"""
Web UI для обработки изображений с удалением фона.
Dark theme video-editor style.
"""

import os
import io
import zipfile
import asyncio
import base64
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass
from datetime import datetime
import tempfile
import shutil

import numpy as np
import torch
import cv2
from PIL import Image
from rembg import remove as rmbg_remove, new_session
from transformers import SamModel, SamProcessor
from fastapi import FastAPI, File, UploadFile, Form, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse, StreamingResponse, JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from starlette.requests import Request

# --- НАСТРОЙКИ ---
DEVICE = "cpu"
SAM_MODEL_NAME = "facebook/sam-vit-base"
UPLOAD_DIR = Path("uploads")
RESULTS_DIR = Path("results")
PREVIEWS_DIR = Path("previews")

UPLOAD_DIR.mkdir(exist_ok=True)
RESULTS_DIR.mkdir(exist_ok=True)
PREVIEWS_DIR.mkdir(exist_ok=True)

app = FastAPI(title="Background Removal Tool")

# --- ГЛОБАЛЬНЫЕ МОДЕЛИ ---
print(f"Загрузка моделей на {DEVICE}...")
session = new_session("u2net")
sam_model = SamModel.from_pretrained(SAM_MODEL_NAME).to(DEVICE)
sam_processor = SamProcessor.from_pretrained(SAM_MODEL_NAME)
print("Модели загружены!")

# Для отслеживания прогресса
processing_status = {}
preview_cache = {}  # Кэш для превью


@dataclass
class ProcessingParams:
    """Параметры обработки изображений"""
    margin_percent: float = 20.0
    dilate_iterations: int = 2
    erode_iterations: int = 1
    feather_radius: int = 2
    iou_threshold: float = 0.3
    use_sam: bool = True
    output_format: str = "png"


def dilate_mask(mask, iterations=2):
    kernel = np.ones((3, 3), np.uint8)
    return cv2.dilate(mask.astype(np.uint8), kernel, iterations=iterations).astype(bool)


def erode_mask(mask, iterations=1):
    kernel = np.ones((3, 3), np.uint8)
    return cv2.erode(mask.astype(np.uint8), kernel, iterations=iterations).astype(bool)


def feather_edges(mask, radius=2):
    mask_uint8 = (mask.astype(np.uint8)) * 255
    return cv2.GaussianBlur(mask_uint8, (radius*2+1, radius*2+1), 0)


def process_single_image(image_path: Path, output_path: Path, params: ProcessingParams, task_id: str = None):
    """Обработка одного изображения с заданными параметрами"""
    
    img_pil = Image.open(image_path).convert("RGB")
    w, h = img_pil.size
    
    # --- ШАГ 1: RMBG ---
    img_no_bg = rmbg_remove(img_pil, session=session)
    alpha = np.array(img_no_bg)[:, :, 3]
    rmbg_mask = alpha > 128
    
    # --- ШАГ 2: Подготовка для SAM ---
    y_indices, x_indices = np.where(rmbg_mask > 0)
    if len(x_indices) == 0:
        raise ValueError("Объект не найден на изображении")
    
    # BBOX с отступом
    obj_w = np.max(x_indices) - np.min(x_indices)
    obj_h = np.max(y_indices) - np.min(y_indices)
    margin_x = int(obj_w * params.margin_percent / 100)
    margin_y = int(obj_h * params.margin_percent / 100)
    
    x_min = max(0, np.min(x_indices) - margin_x)
    y_min = max(0, np.min(y_indices) - margin_y)
    x_max = min(w, np.max(x_indices) + margin_x)
    y_max = min(h, np.max(y_indices) + margin_y)
    
    input_box = [x_min, y_min, x_max, y_max]
    
    # --- ШАГ 3: SAM (опционально) ---
    final_mask = rmbg_mask.copy()
    
    if params.use_sam:
        try:
            inputs = sam_processor(
                img_pil, 
                input_boxes=[[[input_box]]],
                return_tensors="pt"
            ).to(DEVICE)
            
            with torch.no_grad():
                outputs = sam_model(**inputs)
            
            masks = sam_processor.image_processor.post_process_masks(
                outputs.pred_masks.cpu(), 
                inputs["original_sizes"].cpu(), 
                inputs["reshaped_input_sizes"].cpu()
            )
            
            sam_masks = masks[0][0]
            
            best_iou = 0
            best_mask = rmbg_mask
            
            for i in range(sam_masks.shape[0]):
                current_mask = sam_masks[i].numpy()
                
                if current_mask.shape != (h, w):
                    current_mask = cv2.resize(
                        current_mask.astype(np.uint8), 
                        (w, h), 
                        interpolation=cv2.INTER_NEAREST
                    ).astype(bool)
                
                intersection = np.logical_and(current_mask, rmbg_mask).sum()
                union = np.logical_or(current_mask, rmbg_mask).sum()
                iou = intersection / (union + 1e-6)
                
                current_mask_inv = ~current_mask
                intersection_inv = np.logical_and(current_mask_inv, rmbg_mask).sum()
                union_inv = np.logical_or(current_mask_inv, rmbg_mask).sum()
                iou_inv = intersection_inv / (union_inv + 1e-6)
                
                if iou > best_iou:
                    best_iou = iou
                    best_mask = current_mask
                if iou_inv > best_iou:
                    best_iou = iou_inv
                    best_mask = current_mask_inv
            
            final_mask = best_mask
            
            if best_iou < params.iou_threshold:
                final_mask = rmbg_mask
                
        except Exception as e:
            print(f"Ошибка SAM: {e}. Используем RMBG.")
            final_mask = rmbg_mask
    
    # --- ШАГ 4: ПОСТ-ОБРАБОТКА ---
    if params.dilate_iterations > 0:
        final_mask = dilate_mask(final_mask, iterations=params.dilate_iterations)
    if params.erode_iterations > 0:
        final_mask = erode_mask(final_mask, iterations=params.erode_iterations)
    
    coverage = final_mask.sum() / (h * w)
    if coverage > 0.90:
        final_mask = ~final_mask
        coverage = final_mask.sum() / (h * w)
    
    # --- СОХРАНЕНИЕ ---
    mask_feathered = feather_edges(final_mask, radius=params.feather_radius)
    mask_img = Image.fromarray(mask_feathered, mode='L')
    empty = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    img_rgba = img_pil.convert("RGBA")
    
    result = Image.composite(img_rgba, empty, mask_img)
    
    if params.output_format == "webp":
        result.save(output_path, "WEBP", quality=95)
    else:
        result.save(output_path, "PNG")
    
    return {
        "coverage": float(coverage),
        "width": w,
        "height": h
    }


def generate_preview(image_path: Path, params: ProcessingParams) -> str:
    """Генерация превью для предпросмотра, возвращает base64"""
    
    # Создаем временный файл для превью
    preview_path = PREVIEWS_DIR / f"preview_{image_path.stem}.png"
    
    # Обрабатываем с уменьшенным качеством для скорости
    try:
        img_pil = Image.open(image_path).convert("RGB")
        # Уменьшаем для скорости превью
        img_pil.thumbnail((800, 800), Image.Resampling.LANCZOS)
        
        w, h = img_pil.size
        
        # RMBG - rembg может возвращать перевернутое изображение
        img_no_bg = rmbg_remove(img_pil, session=session)
        
        # Конвертируем в numpy и берем альфа-канал
        img_no_bg_array = np.array(img_no_bg)
        alpha = img_no_bg_array[:, :, 3]
        rmbg_mask = alpha > 128
        
        # Проверяем ориентацию маски
        # Инвертируем маску по вертикали если нужно
        if len(img_no_bg_array.shape) == 3 and img_no_bg_array.shape[0] != h:
            rmbg_mask = rmbg_mask.T
        
        # Быстрая пост-обработка без SAM для превью
        final_mask = rmbg_mask.copy()
        
        if params.dilate_iterations > 0:
            final_mask = dilate_mask(final_mask, iterations=params.dilate_iterations)
        if params.erode_iterations > 0:
            final_mask = erode_mask(final_mask, iterations=params.erode_iterations)
        
        coverage = final_mask.sum() / (h * w)
        if coverage > 0.90:
            final_mask = ~final_mask
        
        mask_feathered = feather_edges(final_mask, radius=params.feather_radius)
        
        # Убеждаемся что размеры совпадают
        if mask_feathered.shape != (h, w):
            mask_feathered = cv2.resize(mask_feathered, (w, h), interpolation=cv2.INTER_NEAREST)
        
        mask_img = Image.fromarray(mask_feathered, mode='L')
        empty = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        img_rgba = img_pil.convert("RGBA")
        
        result = Image.composite(img_rgba, empty, mask_img)
        
        # Конвертируем в base64
        buffer = io.BytesIO()
        result.save(buffer, format='PNG')
        buffer.seek(0)
        img_base64 = base64.b64encode(buffer.read()).decode()
        
        return img_base64
        
    except Exception as e:
        print(f"Preview error: {e}")
        import traceback
        traceback.print_exc()
        return ""


# --- HTML ФРОНТЕНД ---

HTML_CONTENT = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BG Remover</title>
    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }
        
        :root {
            --bg-primary: #0d0d0f;
            --bg-secondary: #1a1a1e;
            --bg-tertiary: #252529;
            --bg-hover: #2a2a2f;
            --accent-primary: #8b5cf6;
            --accent-secondary: #a78bfa;
            --accent-gradient: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%);
            --text-primary: #ffffff;
            --text-secondary: #9ca3af;
            --text-muted: #6b7280;
            --border-color: #2d2d33;
            --success: #22c55e;
            --error: #ef4444;
            --warning: #f59e0b;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
            overflow: hidden;
        }
        
        /* HEADER */
        .header {
            height: 60px;
            background: var(--bg-secondary);
            border-bottom: 1px solid var(--border-color);
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 24px;
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            z-index: 100;
        }
        
        .logo {
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 1.3em;
            font-weight: 700;
            background: var(--accent-gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .logo-icon {
            width: 36px;
            height: 36px;
            background: var(--accent-gradient);
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.2em;
            -webkit-text-fill-color: white;
        }
        
        .header-actions {
            display: flex;
            gap: 12px;
        }
        
        .btn {
            padding: 10px 20px;
            border: none;
            border-radius: 8px;
            font-size: 0.9em;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .btn-primary {
            background: var(--accent-gradient);
            color: white;
        }
        
        .btn-primary:hover:not(:disabled) {
            transform: translateY(-1px);
            box-shadow: 0 4px 20px rgba(139, 92, 246, 0.4);
        }
        
        .btn-primary:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        
        .btn-secondary {
            background: var(--bg-tertiary);
            color: var(--text-primary);
            border: 1px solid var(--border-color);
        }
        
        .btn-secondary:hover {
            background: var(--bg-hover);
        }
        
        /* MAIN LAYOUT */
        .main-container {
            display: grid;
            grid-template-columns: 280px 1fr 320px;
            height: calc(100vh - 60px);
            margin-top: 60px;
        }
        
        /* LEFT PANEL - FILES */
        .left-panel {
            background: var(--bg-secondary);
            border-right: 1px solid var(--border-color);
            display: flex;
            flex-direction: column;
        }
        
        .panel-header {
            padding: 16px 20px;
            border-bottom: 1px solid var(--border-color);
            font-weight: 600;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .panel-header span {
            color: var(--text-secondary);
            font-size: 0.85em;
            font-weight: 400;
        }
        
        .upload-btn {
            margin: 16px 20px;
            padding: 40px 20px;
            border: 2px dashed var(--border-color);
            border-radius: 12px;
            text-align: center;
            cursor: pointer;
            transition: all 0.2s;
            color: var(--text-secondary);
        }
        
        .upload-btn:hover, .upload-btn.dragover {
            border-color: var(--accent-primary);
            background: rgba(139, 92, 246, 0.05);
            color: var(--text-primary);
        }
        
        .upload-btn input {
            display: none;
        }
        
        .upload-icon {
            font-size: 32px;
            margin-bottom: 8px;
        }
        
        .file-list {
            flex: 1;
            overflow-y: auto;
            padding: 0 16px 16px;
        }
        
        .file-item {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 10px;
            border-radius: 10px;
            cursor: pointer;
            transition: all 0.2s;
            margin-bottom: 6px;
            position: relative;
        }
        
        .file-item:hover {
            background: var(--bg-hover);
        }
        
        .file-item.active {
            background: rgba(139, 92, 246, 0.15);
            border: 1px solid var(--accent-primary);
        }
        
        .file-thumb {
            width: 48px;
            height: 48px;
            border-radius: 8px;
            object-fit: cover;
            background: var(--bg-tertiary);
        }
        
        .file-info {
            flex: 1;
            min-width: 0;
        }
        
        .file-name {
            font-size: 0.85em;
            font-weight: 500;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        
        .file-status {
            font-size: 0.75em;
            color: var(--text-muted);
            margin-top: 2px;
        }
        
        .file-status.done {
            color: var(--success);
        }
        
        .file-status.error {
            color: var(--error);
        }
        
        .file-status.processing {
            color: var(--accent-secondary);
        }
        
        .file-remove {
            width: 24px;
            height: 24px;
            border-radius: 6px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--text-muted);
            opacity: 0;
            transition: all 0.2s;
            cursor: pointer;
        }
        
        .file-item:hover .file-remove {
            opacity: 1;
        }
        
        .file-remove:hover {
            background: var(--error);
            color: white;
        }
        
        /* CENTER - PREVIEW */
        .center-panel {
            background: var(--bg-primary);
            display: flex;
            flex-direction: column;
            position: relative;
        }
        
        .preview-container {
            flex: 1;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 40px;
            position: relative;
            overflow: hidden;
        }
        
        .preview-wrapper {
            position: relative;
            max-width: 100%;
            max-height: 100%;
            box-shadow: 0 20px 60px rgba(0,0,0,0.5);
            border-radius: 12px;
            overflow: hidden;
        }
        
        .preview-wrapper img {
            max-width: 100%;
            max-height: calc(100vh - 240px);
            display: block;
        }
        
        .compare-slider {
            position: absolute;
            top: 0;
            bottom: 0;
            width: 4px;
            background: var(--accent-primary);
            cursor: ew-resize;
            z-index: 10;
            left: 50%;
        }
        
        .compare-slider::after {
            content: '◀ ▶';
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 32px;
            height: 32px;
            background: var(--accent-primary);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 10px;
            color: white;
            letter-spacing: -1px;
        }
        
        .preview-overlay {
            position: absolute;
            top: 20px;
            left: 20px;
            background: rgba(0,0,0,0.7);
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 0.8em;
            color: var(--text-secondary);
            backdrop-filter: blur(10px);
        }
        
        .empty-state {
            text-align: center;
            color: var(--text-muted);
        }
        
        .empty-state-icon {
            font-size: 64px;
            margin-bottom: 16px;
            opacity: 0.5;
        }
        
        .toolbar {
            height: 60px;
            background: var(--bg-secondary);
            border-top: 1px solid var(--border-color);
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 16px;
            padding: 0 24px;
        }
        
        .toolbar-btn {
            height: 40px;
            padding: 0 20px;
            border-radius: 10px;
            border: none;
            background: var(--bg-tertiary);
            color: var(--text-secondary);
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            font-size: 0.9em;
            font-weight: 500;
        }
        
        .toolbar-btn:hover {
            background: var(--bg-hover);
            color: var(--text-primary);
        }
        
        .toolbar-btn.active {
            background: var(--accent-primary);
            color: white;
        }
        
        /* RIGHT PANEL - SETTINGS */
        .right-panel {
            background: var(--bg-secondary);
            border-left: 1px solid var(--border-color);
            display: flex;
            flex-direction: column;
            overflow-y: auto;
        }
        
        .settings-section {
            padding: 20px;
            border-bottom: 1px solid var(--border-color);
        }
        
        .settings-section h3 {
            font-size: 0.75em;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: var(--text-muted);
            margin-bottom: 16px;
        }
        
        .param-row {
            margin-bottom: 20px;
        }
        
        .param-row:last-child {
            margin-bottom: 0;
        }
        
        .param-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }
        
        .param-label {
            font-size: 0.9em;
            color: var(--text-primary);
        }
        
        .param-value {
            font-size: 0.85em;
            color: var(--accent-secondary);
            font-weight: 600;
            min-width: 40px;
            text-align: right;
        }
        
        input[type="range"] {
            width: 100%;
            height: 6px;
            border-radius: 3px;
            background: var(--bg-tertiary);
            outline: none;
            -webkit-appearance: none;
        }
        
        input[type="range"]::-webkit-slider-thumb {
            -webkit-appearance: none;
            width: 18px;
            height: 18px;
            border-radius: 50%;
            background: var(--accent-gradient);
            cursor: pointer;
            border: 2px solid var(--bg-secondary);
            box-shadow: 0 2px 8px rgba(139, 92, 246, 0.4);
        }
        
        .toggle-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .toggle {
            width: 48px;
            height: 26px;
            background: var(--bg-tertiary);
            border-radius: 13px;
            position: relative;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .toggle.active {
            background: var(--accent-primary);
        }
        
        .toggle::after {
            content: '';
            position: absolute;
            width: 22px;
            height: 22px;
            background: white;
            border-radius: 50%;
            top: 2px;
            left: 2px;
            transition: all 0.2s;
        }
        
        .toggle.active::after {
            left: 24px;
        }
        
        .format-select {
            width: 100%;
            padding: 10px 14px;
            border-radius: 8px;
            border: 1px solid var(--border-color);
            background: var(--bg-tertiary);
            color: var(--text-primary);
            font-size: 0.9em;
            outline: none;
            cursor: pointer;
        }
        
        .format-select:focus {
            border-color: var(--accent-primary);
        }
        
        .progress-section {
            padding: 20px;
            background: var(--bg-tertiary);
        }
        
        .progress-bar {
            height: 6px;
            background: var(--bg-primary);
            border-radius: 3px;
            overflow: hidden;
            margin-bottom: 12px;
        }
        
        .progress-fill {
            height: 100%;
            background: var(--accent-gradient);
            border-radius: 3px;
            transition: width 0.3s;
        }
        
        .progress-text {
            font-size: 0.85em;
            color: var(--text-secondary);
            text-align: center;
        }
        
        /* SCROLLBAR */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: transparent;
        }
        
        ::-webkit-scrollbar-thumb {
            background: var(--bg-tertiary);
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: var(--border-color);
        }
        
        /* LOADING */
        .loading {
            display: inline-block;
            width: 16px;
            height: 16px;
            border: 2px solid var(--bg-tertiary);
            border-top-color: var(--accent-primary);
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        /* RESPONSIVE */
        @media (max-width: 1100px) {
            .main-container {
                grid-template-columns: 240px 1fr 280px;
            }
        }
        
        .hidden {
            display: none !important;
        }
    </style>
</head>
<body>
    <header class="header">
        <div class="logo">
            <div class="logo-icon">✂️</div>
            <div>
                <div style="font-size: 0.7em; opacity: 0.7; font-weight: 400; letter-spacing: 2px; margin-bottom: -4px;">KIMI DESIGN</div>
                <div>BG Remover Pro</div>
            </div>
        </div>
        <div class="header-actions">
            <button class="btn btn-secondary" id="clearBtn">
                🗑️ Очистить
            </button>
            <button class="btn btn-primary" id="processBtn" disabled>
                <span id="processBtnText">▶ Обработать все</span>
            </button>
            <button class="btn btn-primary hidden" id="downloadBtn">
                📦 Скачать ZIP
            </button>
        </div>
    </header>
    
    <div class="main-container">
        <!-- LEFT PANEL -->
        <aside class="left-panel">
            <div class="panel-header">
                Изображения
                <span id="fileCount">0</span>
            </div>
            
            <div class="upload-btn" id="dropZone">
                <div class="upload-icon">📁</div>
                <div>Добавить файлы</div>
                <input type="file" id="fileInput" multiple accept="image/*">
            </div>
            
            <div class="file-list" id="fileList"></div>
        </aside>
        
        <!-- CENTER - PREVIEW -->
        <main class="center-panel">
            <div class="preview-container" id="previewContainer">
                <div class="empty-state" id="emptyState">
                    <div class="empty-state-icon">🖼️</div>
                    <p>Загрузите изображения для начала работы</p>
                </div>
                
                <div class="preview-wrapper hidden" id="previewWrapper">
                    <img id="resultPreview" src="" alt="Result">
                    <div class="preview-overlay" id="previewOverlay">Генерация превью...</div>
                </div>
            </div>
            
            <div class="toolbar">
                <button class="toolbar-btn active" id="viewResult" title="Результат обработки">✨ Результат</button>
                <button class="toolbar-btn" id="refreshPreview" title="Обновить превью">🔄 Обновить превью</button>
            </div>
        </main>
        
        <!-- RIGHT PANEL -->
        <aside class="right-panel">
            <div class="settings-section">
                <h3>Параметры обрезки</h3>
                
                <div class="param-row">
                    <div class="param-header">
                        <span class="param-label">Отступ от объекта</span>
                        <span class="param-value" id="marginValue">20%</span>
                    </div>
                    <input type="range" id="margin" min="0" max="100" value="20">
                </div>
                
                <div class="param-row">
                    <div class="param-header">
                        <span class="param-label">Расширение маски</span>
                        <span class="param-value" id="dilateValue">2</span>
                    </div>
                    <input type="range" id="dilate" min="0" max="10" value="2">
                </div>
                
                <div class="param-row">
                    <div class="param-header">
                        <span class="param-label">Сжатие маски</span>
                        <span class="param-value" id="erodeValue">1</span>
                    </div>
                    <input type="range" id="erode" min="0" max="10" value="1">
                </div>
                
                <div class="param-row">
                    <div class="param-header">
                        <span class="param-label">Размытие краёв</span>
                        <span class="param-value" id="featherValue">2</span>
                    </div>
                    <input type="range" id="feather" min="0" max="10" value="2">
                </div>
            </div>
            
            <div class="settings-section">
                <h3>Настройки</h3>
                
                <div class="param-row toggle-row">
                    <span class="param-label">Использовать SAM</span>
                    <div class="toggle active" id="useSamToggle"></div>
                </div>
                
                <div class="param-row">
                    <span class="param-label" style="display: block; margin-bottom: 10px;">Формат выхода</span>
                    <select class="format-select" id="outputFormat">
                        <option value="png">PNG (без потерь)</option>
                        <option value="webp">WebP (сжатие)</option>
                    </select>
                </div>
            </div>
            
            <div class="progress-section hidden" id="progressSection">
                <div class="progress-bar">
                    <div class="progress-fill" id="progressFill" style="width: 0%"></div>
                </div>
                <div class="progress-text" id="progressText">0 / 0 обработано</div>
            </div>
        </aside>
    </div>
    
    <script>
        // STATE
        let files = [];
        let currentFileIndex = -1;
        let taskId = null;
        let previewDebounceTimer = null;
        
        // DOM
        const dropZone = document.getElementById('dropZone');
        const fileInput = document.getElementById('fileInput');
        const fileList = document.getElementById('fileList');
        const fileCount = document.getElementById('fileCount');
        const processBtn = document.getElementById('processBtn');
        const processBtnText = document.getElementById('processBtnText');
        const downloadBtn = document.getElementById('downloadBtn');
        const clearBtn = document.getElementById('clearBtn');
        const emptyState = document.getElementById('emptyState');
        const previewWrapper = document.getElementById('previewWrapper');
        const resultPreview = document.getElementById('resultPreview');
        const previewOverlay = document.getElementById('previewOverlay');
        const progressSection = document.getElementById('progressSection');
        const progressFill = document.getElementById('progressFill');
        const progressText = document.getElementById('progressText');
        
        // PARAMETERS
        const params = {
            margin: 20,
            dilate: 2,
            erode: 1,
            feather: 2,
            useSam: true,
            outputFormat: 'png'
        };
        
        // Event listeners for params
        ['margin', 'dilate', 'erode', 'feather'].forEach(id => {
            const input = document.getElementById(id);
            const display = document.getElementById(id + 'Value');
            input.addEventListener('input', () => {
                const val = parseInt(input.value);
                params[id] = val;
                display.textContent = val + (id === 'margin' ? '%' : '');
                debouncePreviewUpdate();
            });
        });
        
        document.getElementById('useSamToggle').addEventListener('click', function() {
            this.classList.toggle('active');
            params.useSam = this.classList.contains('active');
            debouncePreviewUpdate();
        });
        
        document.getElementById('outputFormat').addEventListener('change', function() {
            params.outputFormat = this.value;
        });
        
        function debouncePreviewUpdate() {
            clearTimeout(previewDebounceTimer);
            if (currentFileIndex >= 0 && files[currentFileIndex]) {
                previewDebounceTimer = setTimeout(() => updatePreview(), 500);
            }
        }
        
        // FILE UPLOAD
        dropZone.addEventListener('click', () => fileInput.click());
        
        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('dragover');
        });
        
        dropZone.addEventListener('dragleave', () => {
            dropZone.classList.remove('dragover');
        });
        
        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('dragover');
            handleFiles(e.dataTransfer.files);
        });
        
        fileInput.addEventListener('change', () => {
            handleFiles(fileInput.files);
        });
        
        function handleFiles(fileList) {
            const newFiles = Array.from(fileList).filter(f => f.type.startsWith('image/'));
            files = [...files, ...newFiles];
            updateFileList();
            processBtn.disabled = files.length === 0;
            
            if (currentFileIndex === -1 && files.length > 0) {
                selectFile(0);
            }
        }
        
        function updateFileList() {
            fileCount.textContent = files.length;
            fileList.innerHTML = files.map((file, i) => `
                <div class="file-item ${i === currentFileIndex ? 'active' : ''}" data-index="${i}">
                    <img class="file-thumb" src="${URL.createObjectURL(file)}" alt="">
                    <div class="file-info">
                        <div class="file-name">${file.name}</div>
                        <div class="file-status" id="status-${i}">${(file.size / 1024).toFixed(0)} KB</div>
                    </div>
                    <div class="file-remove" onclick="removeFile(event, ${i})">✕</div>
                </div>
            `).join('');
            
            // Add click handlers
            fileList.querySelectorAll('.file-item').forEach(item => {
                item.addEventListener('click', (e) => {
                    if (!e.target.classList.contains('file-remove')) {
                        selectFile(parseInt(item.dataset.index));
                    }
                });
            });
        }
        
        function removeFile(e, index) {
            e.stopPropagation();
            files.splice(index, 1);
            if (currentFileIndex === index) {
                currentFileIndex = files.length > 0 ? 0 : -1;
                if (currentFileIndex >= 0) {
                    selectFile(0);
                } else {
                    showEmptyState();
                }
            } else if (currentFileIndex > index) {
                currentFileIndex--;
            }
            updateFileList();
            processBtn.disabled = files.length === 0;
        }
        
        clearBtn.addEventListener('click', () => {
            files = [];
            currentFileIndex = -1;
            updateFileList();
            showEmptyState();
            processBtn.disabled = true;
            downloadBtn.classList.add('hidden');
        });
        
        function showEmptyState() {
            emptyState.classList.remove('hidden');
            previewWrapper.classList.add('hidden');
        }
        
        function selectFile(index) {
            currentFileIndex = index;
            updateFileList();
            
            emptyState.classList.add('hidden');
            previewWrapper.classList.remove('hidden');
            
            // Auto generate preview
            updatePreview();
        }
        
        // PREVIEW
        async function updatePreview() {
            if (currentFileIndex < 0 || !files[currentFileIndex]) return;
            
            const file = files[currentFileIndex];
            
            // Show loading
            previewOverlay.textContent = 'Генерация превью...';
            previewOverlay.classList.remove('hidden');
            resultPreview.style.opacity = '0.5';
            
            const formData = new FormData();
            formData.append('file', file);
            formData.append('margin_percent', params.margin);
            formData.append('dilate_iterations', params.dilate);
            formData.append('erode_iterations', params.erode);
            formData.append('feather_radius', params.feather);
            formData.append('use_sam', params.useSam);
            
            try {
                const response = await fetch('/api/preview', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                if (data.preview) {
                    resultPreview.src = 'data:image/png;base64,' + data.preview;
                    resultPreview.onload = () => {
                        previewOverlay.classList.add('hidden');
                        resultPreview.style.opacity = '1';
                    };
                }
            } catch (err) {
                console.error('Preview error:', err);
                previewOverlay.textContent = 'Ошибка генерации';
            }
        }
        
        // REFRESH PREVIEW
        document.getElementById('refreshPreview').addEventListener('click', updatePreview);
        
        // PROCESS ALL
        processBtn.addEventListener('click', async () => {
            if (files.length === 0) return;
            
            processBtn.disabled = true;
            processBtnText.innerHTML = '<span class="loading"></span> Обработка...';
            progressSection.classList.remove('hidden');
            downloadBtn.classList.add('hidden');
            
            const formData = new FormData();
            files.forEach(f => formData.append('files', f));
            formData.append('margin_percent', params.margin);
            formData.append('dilate_iterations', params.dilate);
            formData.append('erode_iterations', params.erode);
            formData.append('feather_radius', params.feather);
            formData.append('use_sam', params.useSam);
            formData.append('output_format', params.outputFormat);
            
            try {
                const response = await fetch('/api/process', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                
                if (data.task_id) {
                    taskId = data.task_id;
                    pollStatus();
                }
            } catch (err) {
                console.error('Process error:', err);
                processBtn.disabled = false;
                processBtnText.textContent = '▶ Обработать все';
            }
        });
        
        async function pollStatus() {
            try {
                const res = await fetch(`/api/status/${taskId}`);
                const data = await res.json();
                
                const progress = ((data.completed + data.errors) / data.total * 100) || 0;
                progressFill.style.width = progress + '%';
                progressText.textContent = `${data.completed} / ${data.total} обработано`;
                
                // Update file statuses
                data.files.forEach((file, i) => {
                    const statusEl = document.getElementById(`status-${i}`);
                    if (statusEl) {
                        if (file.status === 'completed') {
                            statusEl.textContent = '✓ Готово';
                            statusEl.className = 'file-status done';
                        } else if (file.status === 'error') {
                            statusEl.textContent = '✗ Ошибка';
                            statusEl.className = 'file-status error';
                        } else if (file.status === 'processing') {
                            statusEl.textContent = '⟳ Обработка...';
                            statusEl.className = 'file-status processing';
                        }
                    }
                });
                
                if (data.status === 'completed') {
                    processBtnText.textContent = '✓ Готово';
                    downloadBtn.classList.remove('hidden');
                    setTimeout(() => {
                        processBtn.disabled = false;
                        processBtnText.textContent = '▶ Обработать все';
                    }, 2000);
                } else {
                    setTimeout(pollStatus, 500);
                }
            } catch (err) {
                setTimeout(pollStatus, 1000);
            }
        }
        
        // DOWNLOAD
        downloadBtn.addEventListener('click', () => {
            if (taskId) {
                window.location.href = `/api/download/${taskId}`;
            }
        });
    </script>
</body>
</html>
'''


# --- API ENDPOINTS ---

@app.get("/")
async def root():
    """Главная страница"""
    return HTMLResponse(content=HTML_CONTENT)


@app.post("/api/preview")
async def generate_preview_endpoint(
    file: UploadFile = File(...),
    margin_percent: float = Form(20.0),
    dilate_iterations: int = Form(2),
    erode_iterations: int = Form(1),
    feather_radius: int = Form(2),
    use_sam: bool = Form(True)
):
    """Генерация превью для предпросмотра"""
    
    params = ProcessingParams(
        margin_percent=margin_percent,
        dilate_iterations=dilate_iterations,
        erode_iterations=erode_iterations,
        feather_radius=feather_radius,
        use_sam=use_sam
    )
    
    # Сохраняем временный файл
    temp_path = PREVIEWS_DIR / f"temp_{file.filename}"
    with open(temp_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    try:
        # Генерируем превью
        preview_base64 = await asyncio.to_thread(generate_preview, temp_path, params)
        return {"preview": preview_base64}
    finally:
        # Удаляем временный файл
        if temp_path.exists():
            temp_path.unlink()


@app.post("/api/process")
async def start_processing(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    margin_percent: float = Form(20.0),
    dilate_iterations: int = Form(2),
    erode_iterations: int = Form(1),
    feather_radius: int = Form(2),
    use_sam: bool = Form(True),
    output_format: str = Form("png")
):
    """Запуск обработки изображений"""
    
    task_id = datetime.now().strftime("%Y%m%d_%H%M%S_") + str(id(files))[-6:]
    task_dir = UPLOAD_DIR / task_id
    task_dir.mkdir(exist_ok=True)
    
    params = ProcessingParams(
        margin_percent=margin_percent,
        dilate_iterations=dilate_iterations,
        erode_iterations=erode_iterations,
        feather_radius=feather_radius,
        use_sam=use_sam,
        output_format=output_format
    )
    
    # Сохраняем загруженные файлы
    saved_files = []
    for file in files:
        if file.filename.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.bmp')):
            file_path = task_dir / file.filename
            with open(file_path, "wb") as f:
                content = await file.read()
                f.write(content)
            saved_files.append(file_path)
    
    # Инициализируем статус
    processing_status[task_id] = {
        "status": "processing",
        "total": len(saved_files),
        "completed": 0,
        "errors": 0,
        "files": [{"name": f.name, "status": "pending"} for f in saved_files],
        "output_dir": None
    }
    
    # Запускаем обработку в фоне
    background_tasks.add_task(process_batch, task_id, saved_files, params)
    
    return {"task_id": task_id, "total_files": len(saved_files)}


async def process_batch(task_id: str, files: List[Path], params: ProcessingParams):
    """Фоновая обработка пакета"""
    
    output_dir = RESULTS_DIR / task_id
    output_dir.mkdir(exist_ok=True)
    
    processing_status[task_id]["output_dir"] = str(output_dir)
    
    for i, file_path in enumerate(files):
        try:
            processing_status[task_id]["files"][i]["status"] = "processing"
            
            output_path = output_dir / f"{file_path.stem}.{params.output_format}"
            
            # Синхронная обработка в треде
            result = await asyncio.to_thread(
                process_single_image,
                file_path,
                output_path,
                params,
                task_id
            )
            
            processing_status[task_id]["files"][i]["status"] = "completed"
            processing_status[task_id]["files"][i]["result"] = result
            processing_status[task_id]["completed"] += 1
            
        except Exception as e:
            processing_status[task_id]["files"][i]["status"] = "error"
            processing_status[task_id]["files"][i]["error"] = str(e)
            processing_status[task_id]["errors"] += 1
    
    processing_status[task_id]["status"] = "completed"


@app.get("/api/status/{task_id}")
async def get_status(task_id: str):
    """Получить статус обработки"""
    if task_id not in processing_status:
        return JSONResponse({"error": "Task not found"}, status_code=404)
    
    return processing_status[task_id]


@app.get("/api/download/{task_id}")
async def download_results(task_id: str):
    """Скачать результаты в ZIP"""
    
    if task_id not in processing_status:
        return JSONResponse({"error": "Task not found"}, status_code=404)
    
    output_dir = Path(processing_status[task_id]["output_dir"])
    
    if not output_dir.exists():
        return JSONResponse({"error": "Results not found"}, status_code=404)
    
    # Создаем ZIP в памяти
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        for file_path in output_dir.iterdir():
            if file_path.is_file():
                zf.write(file_path, file_path.name)
    
    zip_buffer.seek(0)
    
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=results_{task_id}.zip"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)
