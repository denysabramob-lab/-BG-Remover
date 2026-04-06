# BG Remover Pro - FAQ & Documentation

**KIMI DESIGN** — Инструмент для удаления фона с изображений с использованием AI.

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.11+-blue)
![License](https://img.shields.io/badge/license-MIT-green)

---

## 🚀 Быстрый старт (Quick Start)

```bash
# 1. Клонировать репозиторий
git clone <repository-url>
cd image

# 2. Установить зависимости
chmod +x install.sh
./install.sh

# 3. Запустить Web UI
./run_web.sh

# 4. Открыть в браузере
http://localhost:7860
```

**Готово!** Перетащите изображения в левую панель, настройте параметры справа и нажмите "Обработать все".

---

## 📋 Содержание

- [Системные требования](#системные-требования)
- [Установка Python и зависимостей](#установка-python-и-зависимостей)
- [Установка проекта](#установка-проекта)
- [Запуск](#запуск)
- [Использование](#использование)
- [Параметры обработки](#параметры-обработки)
- [Устранение неполадок](#устранение-неполадок)
- [API](#api)
- [Структура проекта](#структура-проекта)

---

## 💻 Системные требования

### Минимальные
- **Python:** 3.11 или выше
- **RAM:** 4 GB
- **Место на диске:** 2 GB
- **CPU:** с поддержкой AVX

### Рекомендуемые
- **Python:** 3.11-3.12
- **RAM:** 8 GB
- **Место на диске:** 5 GB (для AI-моделей)
- **Диск:** SSD

### Поддерживаемые ОС
- ✅ Linux (Ubuntu 20.04+, Debian 11+, CentOS 8+)
- ✅ macOS (12.0+, Intel/Apple Silicon)
- ✅ Windows 10/11 (через WSL2)

---

## 🔧 Установка Python и зависимостей

### Ubuntu / Debian

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка Python 3.11+ и pip
sudo apt install -y python3.11 python3.11-venv python3-pip

# Установка системных зависимостей
sudo apt install -y git curl wget libgl1-mesa-glx libglib2.0-0

# Установка Poetry (опционально, но рекомендуется)
curl -sSL https://install.python-poetry.org | python3 -
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### macOS

```bash
# Установка Homebrew, если не установлен
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Установка Python
brew install python@3.11 git

# Установка Poetry
brew install poetry
```

### Windows (WSL2)

```powershell
# В PowerShell от имени администратора
wsl --install -d Ubuntu
# Перезагрузка компьютера

# В WSL Ubuntu выполнить команды из раздела Ubuntu выше
```

### Проверка установки

```bash
# Проверка Python
python3 --version  # Должно быть 3.11 или выше

# Проверка Poetry
poetry --version
```

---

## 📦 Установка проекта

### Автоматическая установка (рекомендуется)

```bash
# Перейти в папку проекта
cd image

# Сделать скрипт установки исполняемым
chmod +x install.sh

# Запустить установку
./install.sh
```

Скрипт автоматически:
- Проверит версию Python
- Создаст виртуальное окружение
- Установит все зависимости
- Скачает AI-модели (при первом запуске)

### Ручная установка через Poetry

```bash
# Установка зависимостей
poetry install

# Активация окружения
poetry shell
```

### Ручная установка через pip

```bash
# Создание виртуального окружения
python3 -m venv .venv

# Активация
source .venv/bin/activate  # Linux/Mac
# или: .venv\Scripts\activate  # Windows

# Установка пакетов
pip install --upgrade pip
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip install transformers==4.38.2
pip install opencv-python numpy pillow scipy rembg onnxruntime
pip install fastapi uvicorn python-multipart
pip install git+https://github.com/facebookresearch/segment-anything.git
```

---

## ▶️ Запуск

### Web Interface (рекомендуется)

```bash
# Способ 1: Через скрипт
./run_web.sh

# Способ 2: Через Poetry
poetry run python web_ui.py

# Способ 3: Напрямую
source .venv/bin/activate
python web_ui.py
```

Откройте в браузере: **http://localhost:7860**

### Командная строка (пакетная обработка)

```bash
# Поместите изображения в папку sours/
./run_all.sh

# Или напрямую
poetry run python main.py
```

Результаты сохранятся в папку `results/`

---

## 🖥️ Использование Web Interface

### 1. Загрузка изображений
- Перетащите файлы в левую панель **или**
- Нажмите "+ Добавить" для выбора файлов
- Поддерживаются: JPG, PNG, WebP, BMP

### 2. Настройка параметров (правая панель)

| Параметр | Описание |
|----------|----------|
| **Отступ от объекта** | Увеличивает область вокруг объекта |
| **Расширение маски** | Расширяет границы маски (Dilate) |
| **Сжатие маски** | Сжимает границы маски (Erode) |
| **Размытие краёв** | Смягчает края для естественного вида |
| **SAM** | AI-уточнение границ (медленнее, но точнее) |

### 3. Предпросмотр
- Выберите файл в списке слева
- Регулируйте параметры — превью обновится автоматически
- Нажмите "🔄 Обновить превью" для ручного обновления

### 4. Обработка и скачивание
- Нажмите "▶ Обработать все"
- Дождитесь завершения (прогресс в правой панели)
- Нажмите "📦 Скачать ZIP" для загрузки результатов

---

## ⚙️ Параметры обработки

### Описание параметров

| Параметр | Диапазон | По умолчанию | Когда использовать |
|----------|----------|--------------|-------------------|
| **Отступ от объекта** | 0-100% | 20% | Объект обрезается слишком сильно |
| **Расширение маски** | 0-10 | 2 | Фон просвечивает по краям |
| **Сжатие маски** | 0-10 | 1 | В маску попадает лишний фон |
| **Размытие краёв** | 0-10 | 2 | Нужны мягкие, естественные края |
| **SAM** | On/Off | On | Нужна максимальная точность |

### Пресеты (рекомендуемые настройки)

**Для фото людей:**
- Отступ: 10%
- Dilate: 1
- Erode: 1
- Feather: 3
- SAM: On

**Для предметов/товаров:**
- Отступ: 5%
- Dilate: 2
- Erode: 0
- Feather: 1
- SAM: On

**Для иконок/логотипов:**
- Отступ: 0%
- Dilate: 0
- Erode: 0
- Feather: 0
- SAM: Off (быстрее)

---

## 🔧 Устранение неполадок

### Модели не загружаются

**Ошибка:** `Could not load model` или зависание при загрузке

**Решение:**
```bash
# Очистить кэш Hugging Face
rm -rf ~/.cache/huggingface

# Перезапустить — модели скачаются заново
python web_ui.py
```

### Ошибка порта 7860

**Ошибка:** `Address already in use`

**Решение:**
```bash
# Найти и остановить процесс
lsof -i :7860
kill -9 <PID>

# Или изменить порт в web_ui.py
# uvicorn.run(app, host="0.0.0.0", port=7861)
```

### Медленная обработка

**Причины:**
1. Первый запуск — модели загружаются в память (1-2 мин)
2. Большие изображения (>3000px) — уменьшите перед загрузкой
3. SAM включен — отключите для ускорения в 2-3 раза

### Ошибка CUDA / Memory

**Ошибка:** `CUDA out of memory`

**Решение:** Скрипт автоматически использует CPU. Убедитесь, что в `web_ui.py`:
```python
DEVICE = "cpu"
```

### Проблемы с зависимостями

**Ошибка:** `ModuleNotFoundError` или `ImportError`

**Решение:**
```bash
# Полная переустановка
rm -rf .venv poetry.lock
./install.sh

# Или для pip
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt  # если есть
```

### Ошибка "No module named cv2"

```bash
pip install opencv-python
# или
pip install opencv-python-headless  # для серверов без GUI
```

---

## 🔌 API Documentation

### Запуск обработки

```http
POST /api/process
Content-Type: multipart/form-data

Parameters:
- files: File[]           # Изображения
- margin_percent: float   # Отступ (0-100)
- dilate_iterations: int  # Расширение (0-10)
- erode_iterations: int   # Сжатие (0-10)
- feather_radius: int     # Размытие (0-10)
- use_sam: bool           # Использовать SAM
- output_format: string   # png или webp

Response:
{
  "task_id": "20240406_120000_123456",
  "total_files": 5
}
```

### Генерация превью

```http
POST /api/preview
Content-Type: multipart/form-data

Parameters:
- file: File              # Одно изображение
- [параметры обработки]

Response:
{
  "preview": "base64_encoded_png..."
}
```

### Проверка статуса

```http
GET /api/status/{task_id}

Response:
{
  "status": "processing",
  "total": 5,
  "completed": 3,
  "errors": 0,
  "files": [
    {"name": "img1.jpg", "status": "completed"},
    {"name": "img2.jpg", "status": "processing"}
  ]
}
```

### Скачивание результатов

```http
GET /api/download/{task_id}

Response: ZIP-архив
```

---

## 📁 Структура проекта

```
image/
├── web_ui.py              # Web интерфейс (FastAPI + HTML)
├── main.py                # CLI для пакетной обработки
├── install.sh             # Скрипт установки ⭐
├── run_web.sh             # Запуск Web UI
├── run_all.sh             # CLI пакетная обработка
├── FAQ.md                 # Эта документация
├── pyproject.toml         # Зависимости Poetry
├── poetry.lock            # Лок-файл Poetry
├── sours/                 # Исходные изображения
├── results/               # Результаты обработки
├── uploads/               # Временные загрузки
├── previews/              # Кэш превью
└── .venv/                 # Виртуальное окружение
```

---

## 📚 Полезные команды

```bash
# Переустановка окружения
rm -rf .venv poetry.lock && ./install.sh

# Очистка кэша моделей
rm -rf ~/.cache/huggingface ~/.cache/torch

# Очистка результатов
rm -rf results/* uploads/* previews/*

# Проверка логов
python web_ui.py 2>&1 | tee app.log

# Запуск на другом порту
# Отредактируйте web_ui.py, измените port=7860
```

---

## 🆘 Поддержка

Если у вас возникли проблемы:

1. 📖 Проверьте этот FAQ
2. 🔍 Посмотрите ошибки в терминале
3. 🧹 Попробуйте полную переустановку
4. 📧 Создайте Issue с описанием проблемы

---

## 📄 Лицензия

MIT License — свободное использование для личных и коммерческих проектов.

---

<p align="center">
  <b>KIMI DESIGN</b><br>
  Made with ❤️ and AI
</p>
