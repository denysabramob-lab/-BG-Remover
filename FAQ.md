# BG Remover Pro - FAQ & Documentation

**KIMI DESIGN** — Инструмент для удаления фона с изображений с использованием AI.

**Repository:** https://github.com/denysabramob-lab/-BG-Remover.git

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.11+-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20macOS%20%7C%20Windows-blue)

---

## 🚀 Быстрый старт (Quick Start)

### Способ 1: Docker (рекомендуется для серверов)

```bash
# 1. Клонировать
git clone https://github.com/denysabramob-lab/-BG-Remover.git
cd -BG-Remover

# 2. Запустить в Docker
docker-compose up -d

# 3. Открыть в браузере
http://localhost:7860
```

[Подробнее о Docker →](#-docker-развертывание)

### Способ 2: Локальная установка

```bash
# 1. Клонировать репозиторий
git clone https://github.com/denysabramob-lab/-BG-Remover.git
cd -BG-Remover

# 2. Запустить установку (Python скрипт - работает везде)
python3 install.py

# 3. Запустить Web UI
# Linux/Mac:
./run_web.sh
# Windows:
run_web.bat

# 4. Открыть в браузере
http://localhost:7860
```

**Готово!** Перетащите изображения в левую панель, настройте параметры справа и нажмите "Обработать все".

---

## 📋 Содержание

- [Быстрый старт (Docker)](#-быстрый-старт-docker)
- [Поддерживаемые платформы](#поддерживаемые-платформы)
- [Установка Python](#установка-python)
- [Установка проекта](#установка-проекта)
- [Запуск](#запуск)
- [Использование](#использование)
- [Параметры обработки](#параметры-обработки)
- [Устранение неполадок](#устранение-неполадок)
- [API](#api)
- [Docker](#-docker-развертывание)

---

## 💻 Поддерживаемые платформы

| Платформа | Статус | Инструкция |
|-----------|--------|------------|
| **Linux** (Ubuntu, Debian, CentOS) | ✅ Полная поддержка | [См. ниже](#ubuntu--debian) |
| **macOS** (Intel, Apple Silicon) | ✅ Полная поддержка | [См. ниже](#macos) |
| **Windows 10/11** | ✅ Поддержка | [См. ниже](#windows) |
| **Windows (WSL2)** | ✅ Рекомендуется | [См. ниже](#windows-wsl2) |

### Windows

**Вариант 1: Нативный Python (проще)**
1. Скачайте Python 3.11+ с [python.org](https://python.org)
2. Важно: при установке отметьте **"Add Python to PATH"**
3. Откройте PowerShell или CMD
4. Выполните команды из раздела [Быстрый старт](#быстрый-старт)

**Вариант 2: WSL2 (для продвинутых пользователей)**
- Полная совместимость с Linux-версией
- Лучшая производительность для больших файлов
- [Инструкция по установке WSL2](https://docs.microsoft.com/ru-ru/windows/wsl/install)

---

## 🔧 Установка Python

### Ubuntu / Debian

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка Python 3.11+ и необходимых пакетов
sudo apt install -y python3.11 python3.11-venv python3-pip git curl

# Установка системных библиотек для OpenCV
sudo apt install -y libgl1-mesa-glx libglib2.0-0 libsm6 libxext6 libxrender-dev

# Проверка
python3.11 --version
```

### macOS

```bash
# Установка Homebrew (если не установлен)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Установка Python и Git
brew install python@3.11 git

# Проверка
python3 --version
```

### Windows

1. Скачайте установщик: https://python.org/downloads
2. **Важно:** При установке отметьте галочку **"Add Python to PATH"**
3. Установите Git: https://git-scm.com/download/win
4. Откройте PowerShell и проверьте:
```powershell
python --version
# или
py --version
```

---

## 📦 Установка проекта

### Универсальный способ (все платформы)

После установки Python:

```bash
# Клонирование репозитория
git clone https://github.com/denysabramob-lab/-BG-Remover.git
cd -BG-Remover

# Запуск установки (Python скрипт работает везде!)
python3 install.py        # Linux/Mac
python install.py         # Windows (cmd)
py install.py            # Windows (альтернатива)
```

Скрипт `install.py` автоматически:
- ✅ Проверит версию Python
- ✅ Создаст виртуальное окружение
- ✅ Установит все зависимости
- ✅ Скачает AI-модели (при первом запуске)

### Альтернативные способы

**Через Poetry (если установлен):**
```bash
poetry install
poetry run python web_ui.py
```

**Через pip (ручная установка):**
```bash
python3 -m venv .venv

# Linux/Mac:
source .venv/bin/activate

# Windows:
.venv\Scripts\activate

# Установка пакетов
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip install transformers==4.38.2 opencv-python numpy pillow scipy
pip install rembg onnxruntime fastapi uvicorn python-multipart
pip install git+https://github.com/facebookresearch/segment-anything.git
```

---

## ▶️ Запуск

### Web Interface (рекомендуется)

**Linux / macOS:**
```bash
./run_web.sh
# или
python3 web_ui.py
```

**Windows:**
```cmd
run_web.bat
:: или
python web_ui.py
:: или
py web_ui.py
```

Откройте в браузере: **http://localhost:7860**

### Командная строка (пакетная обработка)

**Linux / macOS:**
```bash
# Поместите изображения в папку sours/
./run_all.sh
```

**Windows:**
```cmd
run_all.bat
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

### "python" не найден (Windows)

**Решение:**
```cmd
# Попробуйте:
py --version

# Или используйте полный путь:
C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python311\python.exe install.py
```

### Ошибка "No module named cv2"

**Linux:**
```bash
sudo apt install libgl1-mesa-glx libglib2.0-0
```

**Windows:**
```cmd
pip install opencv-python
```

### Модели не загружаются

```bash
# Очистить кэш и перезапустить
rm -rf ~/.cache/huggingface  # Linux/Mac
# или
rmdir /s /q %USERPROFILE%\.cache\huggingface  # Windows

python3 web_ui.py
```

### Порт 7860 занят

```bash
# Linux/Mac:
lsof -i :7860
kill -9 <PID>

# Windows:
netstat -ano | findstr :7860
taskkill /PID <PID> /F
```

### Медленная обработка

- **Первый запуск** — модели загружаются в память (1-2 мин)
- **SAM** — отключите для ускорения в 2-3 раза (менее точно)
- **Большие изображения** — уменьшите до 2000px перед загрузкой

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
  "files": [...]
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
-BG-Remover/
├── web_ui.py              # Web интерфейс (FastAPI)
├── main.py                # CLI для пакетной обработки
├── install.py             # ✅ Универсальный установщик (Python)
├── install.sh             # Установщик для Linux/Mac (Bash)
├── run_web.sh             # Запуск Web UI (Linux/Mac)
├── run_web.bat            # Запуск Web UI (Windows)
├── run_all.sh             # CLI обработка (Linux/Mac)
├── run_all.bat            # CLI обработка (Windows)
├── FAQ.md                 # Эта документация
├── pyproject.toml         # Зависимости Poetry
├── sours/                 # Исходные изображения
├── results/               # Результаты обработки
├── uploads/               # Временные загрузки
├── previews/              # Кэш превью
└── .venv/                 # Виртуальное окружение
```

---

## 📚 Полезные команды

### Все платформы
```bash
# Переустановка окружения
python3 install.py

# Очистка кэша моделей
# Linux/Mac: rm -rf ~/.cache/huggingface
# Windows: rmdir /s /q %USERPROFILE%\.cache\huggingface

# Очистка результатов
# Linux/Mac: rm -rf results/* uploads/* previews/*
# Windows: del /q results\* uploads\* previews\*
```

---

## 🆘 Поддержка

**Repository:** https://github.com/denysabramob-lab/-BG-Remover.git

При возникновении проблем:
1. 📖 Проверьте этот FAQ
2. 🔍 Посмотрите ошибки в терминале
3. 🧹 Попробуйте `python3 install.py` заново
4. 📧 Создайте Issue на GitHub

---

## 📄 Лицензия

MIT License — свободное использование для личных и коммерческих проектов.

---

<p align="center">
  <b>KIMI DESIGN</b><br>
  Made with ❤️ and AI
</p>
---

## 🐳 Docker развертывание

Быстрый способ развернуть приложение без установки Python и зависимостей.

### Быстрый старт (Docker)

```bash
# Клонировать
git clone https://github.com/denysabramob-lab/-BG-Remover.git
cd -BG-Remover

# Запустить
docker-compose up -d

# Открыть
http://localhost:7860
```

### Требования

- Docker 20.10+
- Docker Compose 2.0+
- 4GB RAM (8GB рекомендуется)
- 5GB свободного места

### Основные команды

```bash
# Запуск
docker-compose up -d

# Просмотр логов
docker-compose logs -f

# Остановка
docker-compose down

# Обновление
docker-compose down
git pull
docker-compose up -d --build
```

### Проброс папок

При запуске через Docker папки автоматически пробрасываются:
- `./uploads` → загруженные файлы
- `./results` → результаты обработки
- `./previews` → кэш превью
- `./sours` → исходные изображения (для CLI)

### Подробная докуменментация

Детальная инструкция по Docker: **[DOCKER.md](./DOCKER.md)**

Там вы найдете:
- Разные варианты запуска (compose, run, hub)
- Настройку портов и ресурсов
- Развертывание на облачных VPS (DigitalOcean, AWS, etc.)
- Reverse proxy через Nginx
- Публикацию через Ngrok
- Устранение неполадок

---

<p align="center">
  <b>KIMI DESIGN</b><br>
  Made with ❤️ and AI
</p>
