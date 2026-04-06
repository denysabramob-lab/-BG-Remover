# BG Remover Pro - Docker Deployment Guide

**KIMI DESIGN** — Быстрый запуск через Docker

**Repository:** https://github.com/denysabramob-lab/-BG-Remover.git

---

## 🚀 Быстрый старт (Docker)

```bash
# 1. Клонировать репозиторий
git clone https://github.com/denysabramob-lab/-BG-Remover.git
cd -BG-Remover

# 2. Запустить через Docker Compose
docker-compose up -d

# 3. Открыть в браузере
http://localhost:7860
```

**Готово!** Первый запуск займет 2-3 минуты (скачивание образа и моделей).

---

## 📋 Требования

- **Docker** 20.10+ 
- **Docker Compose** 2.0+
- **RAM:** 4GB минимум, 8GB рекомендуется
- **Место на диске:** 5GB (включая образы)

### Проверка установки Docker

```bash
docker --version
docker-compose --version
```

Если Docker не установлен:
- **Ubuntu/Debian:** [Install Docker](https://docs.docker.com/engine/install/ubuntu/)
- **macOS:** [Docker Desktop](https://docs.docker.com/desktop/install/mac-install/)
- **Windows:** [Docker Desktop](https://docs.docker.com/desktop/install/windows-install/)

---

## 🐳 Варианты запуска

### Вариант 1: Docker Compose (рекомендуется)

```bash
# Сборка и запуск
docker-compose up -d

# Просмотр логов
docker-compose logs -f

# Остановка
docker-compose down

# Остановка с удалением данных
docker-compose down -v
```

### Вариант 2: Docker Run

```bash
# Сборка образа
docker build -t bg-remover-pro .

# Запуск контейнера
docker run -d \
  --name bg-remover-pro \
  -p 7860:7860 \
  -v $(pwd)/uploads:/app/uploads \
  -v $(pwd)/results:/app/results \
  -v $(pwd)/previews:/app/previews \
  -v $(pwd)/sours:/app/sours \
  --restart unless-stopped \
  bg-remover-pro

# Windows (PowerShell):
docker run -d `
  --name bg-remover-pro `
  -p 7860:7860 `
  -v ${PWD}/uploads:/app/uploads `
  -v ${PWD}/results:/app/results `
  -v ${PWD}/previews:/app/previews `
  -v ${PWD}/sours:/app/sours `
  --restart unless-stopped `
  bg-remover-pro
```

### Вариант 3: Docker Hub (готовый образ)

```bash
# Загрузка из Docker Hub (если опубликовано)
docker pull denysabramob/bg-remover-pro:latest

# Запуск
docker run -d -p 7860:7860 denysabramob/bg-remover-pro:latest
```

---

## 📁 Проброс папок (Volumes)

| Папка хоста | Папка контейнера | Назначение |
|-------------|------------------|------------|
| `./uploads` | `/app/uploads` | Загруженные файлы |
| `./results` | `/app/results` | Результаты обработки |
| `./previews` | `/app/previews` | Кэш превью |
| `./sours` | `/app/sours` | Исходные изображения для CLI |

**Пример:**
```bash
# Положите изображения в ./sours/
# Результаты появятся в ./results/
```

---

## ⚙️ Настройка

### Изменение порта

Отредактируйте `docker-compose.yml`:
```yaml
ports:
  - "8080:7860"  # Теперь доступно на порту 8080
```

### Лимиты ресурсов

```yaml
deploy:
  resources:
    limits:
      cpus: '2'      # Максимум 2 ядра
      memory: 4G     # Максимум 4GB RAM
```

### Переменные окружения

```yaml
environment:
  - DEVICE=cpu       # Использовать CPU
  - WORKERS=1        # Количество воркеров
```

---

## 🔄 Обновление

```bash
# Остановить
docker-compose down

# Обновить код
git pull origin main

# Пересобрать и запустить
docker-compose up -d --build
```

---

## 📊 Полезные команды

```bash
# Статус контейнера
docker-compose ps

# Логи
docker-compose logs -f

# Перезапуск
docker-compose restart

# Войти в контейнер
docker-compose exec bg-remover bash

# Просмотр использования ресурсов
docker stats bg-remover-pro

# Очистка неиспользуемых образов
docker system prune -a
```

---

## 🔧 Устранение неполадок

### Контейнер не запускается

```bash
# Проверить логи
docker-compose logs

# Проверить статус
docker-compose ps
```

### Порт 7860 занят

```bash
# Найти процесс
sudo lsof -i :7860

# Или изменить порт в docker-compose.yml
ports:
  - "8080:7860"
```

### Медленная работа

Увеличьте лимиты ресурсов в `docker-compose.yml`:
```yaml
deploy:
  resources:
    limits:
      cpus: '4'
      memory: 8G
```

### Ошибка "no space left on device"

```bash
# Очистка Docker
docker system prune -a
docker volume prune

# Проверить место
df -h
```

### Модели не загружаются (ошибка сети)

```bash
# Перезапустить с очисткой
docker-compose down -v
docker-compose up -d
```

---

## 🌐 Доступ извне

### Локальная сеть

```bash
# Используйте IP компьютера
http://192.168.1.100:7860
```

### Публикация в интернет (Ngrok)

```bash
# Установите ngrok
# Запустите туннель
ngrok http 7860

# Получите публичный URL
```

### Nginx Reverse Proxy

```nginx
server {
    listen 80;
    server_name bg-remover.yourdomain.com;
    
    location / {
        proxy_pass http://localhost:7860;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

---

## ☁️ Облачные провайдеры

### VPS (DigitalOcean, Linode, Hetzner)

```bash
# 1. Купите VPS с 4GB+ RAM
# 2. Установите Docker
# 3. Запустите:
docker run -d \
  -p 80:7860 \
  --name bg-remover \
  --restart unless-stopped \
  denysabramob/bg-remover-pro:latest

# 4. Откройте http://your-server-ip
```

### AWS EC2

```bash
# User Data при создании инстанса:
#!/bin/bash
apt-get update
apt-get install -y docker.io docker-compose
git clone https://github.com/denysabramob-lab/-BG-Remover.git
cd -BG-Remover
docker-compose up -d
```

### Google Cloud Run

```bash
# Сборка
gcloud builds submit --tag gcr.io/PROJECT/bg-remover-pro

# Развертывание
gcloud run deploy bg-remover-pro \
  --image gcr.io/PROJECT/bg-remover-pro \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

---

## 📁 Файлы Docker

| Файл | Назначение |
|------|------------|
| `Dockerfile` | Инструкция по сборке образа |
| `docker-compose.yml` | Конфигурация сервисов |
| `.dockerignore` | Исключения из образа |
| `DOCKER.md` | Эта документация |

---

## 🆘 Поддержка

**Repository:** https://github.com/denysabramob-lab/-BG-Remover.git

При проблемах с Docker:
1. Проверьте `docker-compose logs`
2. Убедитесь, что порт не занят
3. Проверьте лимиты ресурсов
4. Создайте Issue с выводом `docker-compose logs`

---

<p align="center">
  <b>KIMI DESIGN</b><br>
  Made with ❤️ and Docker
</p>
