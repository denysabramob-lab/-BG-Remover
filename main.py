import os
import numpy as np
import torch
import glob
import cv2
from PIL import Image
from rembg import remove as rmbg_remove, new_session
from transformers import SamModel, SamProcessor
from pathlib import Path

# --- НАСТРОЙКИ ---
DEVICE = "cpu"
SAM_MODEL_NAME = "facebook/sam-vit-base"

print(f"Загрузка моделей на {DEVICE}...")

# RMBG сессия
session = new_session("u2net")

# SAM
sam_model = SamModel.from_pretrained(SAM_MODEL_NAME).to(DEVICE)
sam_processor = SamProcessor.from_pretrained(SAM_MODEL_NAME)

def dilate_mask(mask, iterations=2):
    kernel = np.ones((3, 3), np.uint8)
    return cv2.dilate(mask.astype(np.uint8), kernel, iterations=iterations).astype(bool)

def erode_mask(mask, iterations=1):
    kernel = np.ones((3, 3), np.uint8)
    return cv2.erode(mask.astype(np.uint8), kernel, iterations=iterations).astype(bool)

def feather_edges(mask, radius=2):
    mask_uint8 = (mask.astype(np.uint8)) * 255
    return cv2.GaussianBlur(mask_uint8, (radius*2+1, radius*2+1), 0)

def process_image(image_path, output_path):
    print(f"Обработка {image_path}...")
    
    img_pil = Image.open(image_path).convert("RGB")
    w, h = img_pil.size
    
    # --- ШАГ 1: RMBG ---
    img_no_bg = rmbg_remove(img_pil, session=session)
    alpha = np.array(img_no_bg)[:, :, 3]
    rmbg_mask = alpha > 128
    
    print(f"  RMBG coverage: {rmbg_mask.sum()/(h*w):.1%}")
    
    # --- ШАГ 2: Подготовка для SAM ---
    y_indices, x_indices = np.where(rmbg_mask > 0)
    if len(x_indices) == 0:
        print(f"[{image_path}] Объект не найден.")
        return
    
    # BBOX с отступом 20%
    obj_w = np.max(x_indices) - np.min(x_indices)
    obj_h = np.max(y_indices) - np.min(y_indices)
    margin_x = int(obj_w * 0.20)
    margin_y = int(obj_h * 0.20)
    
    x_min = max(0, np.min(x_indices) - margin_x)
    y_min = max(0, np.min(y_indices) - margin_y)
    x_max = min(w, np.max(x_indices) + margin_x)
    y_max = min(h, np.max(y_indices) + margin_y)
    
    input_box = [x_min, y_min, x_max, y_max]
    
    # --- ШАГ 3: SAM ---
    final_mask = rmbg_mask.copy()
    
    try:
        inputs = sam_processor(
            img_pil, 
            input_boxes=[[[input_box]]],
            return_tensors="pt"
        ).to(DEVICE)
        
        with torch.no_grad():
            outputs = sam_model(**inputs)
        
        # Пост-обработка масок
        masks = sam_processor.image_processor.post_process_masks(
            outputs.pred_masks.cpu(), 
            inputs["original_sizes"].cpu(), 
            inputs["reshaped_input_sizes"].cpu()
        )
        
        # ИСПРАВЛЕНИЕ: masks[0] имеет форму [1, 3, H, W] (батч, num_masks, H, W)
        # Берем masks[0][0] чтобы получить [3, H, W]
        sam_masks = masks[0][0]  # shape: [3, H, W] - 3 маски
        
        print(f"  SAM masks shape: {sam_masks.shape}")
        
        best_iou = 0
        best_mask = rmbg_mask
        
        # Перебираем 3 маски от SAM
        for i in range(sam_masks.shape[0]):
            current_mask = sam_masks[i].numpy()  # Теперь это [H, W]
            
            # Ресайз к оригинальному размеру если нужно
            if current_mask.shape != (h, w):
                current_mask = cv2.resize(current_mask.astype(np.uint8), (w, h), 
                                        interpolation=cv2.INTER_NEAREST).astype(bool)
            
            # Считаем IoU с RMBG
            intersection = np.logical_and(current_mask, rmbg_mask).sum()
            union = np.logical_or(current_mask, rmbg_mask).sum()
            iou = intersection / (union + 1e-6)
            
            # Инвертированная версия
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
        print(f"  SAM IoU: {best_iou:.2f}")
        
        if best_iou < 0.3:
            print(f"  SAM низкое качество, используем RMBG")
            final_mask = rmbg_mask
            
    except Exception as e:
        print(f"  Ошибка SAM: {e}. Используем RMBG.")
        import traceback
        traceback.print_exc()
        final_mask = rmbg_mask
    
    # --- ШАГ 4: ПОСТ-ОБРАБОТКА ---
    final_mask = dilate_mask(final_mask, iterations=2)
    final_mask = erode_mask(final_mask, iterations=1)
    
    coverage = final_mask.sum() / (h * w)
    if coverage > 0.90:
        print(f"  Инвертируем (coverage: {coverage:.1%})")
        final_mask = ~final_mask
        coverage = final_mask.sum() / (h * w)
    
    print(f"  Итог: {coverage:.1%}")
    
    # --- СОХРАНЕНИЕ ---
    mask_feathered = feather_edges(final_mask, radius=2)
    mask_img = Image.fromarray(mask_feathered, mode='L')
    empty = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    img_rgba = img_pil.convert("RGBA")
    
    result = Image.composite(img_rgba, empty, mask_img)
    result.save(output_path)
    print(f"  Сохранено: {output_path}")

# Запуск
os.makedirs("results", exist_ok=True)
images = glob.glob("sours/*.*")

for img_path in images:
    if img_path.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.bmp')):
        out_path = os.path.join("results", Path(img_path).stem + ".png")
        try:
            process_image(img_path, out_path)
        except Exception as e:
            print(f"Ошибка обработки {img_path}: {e}")
            import traceback
            traceback.print_exc()

print("Готово!")