# BG Remover Pro - Docker Image
# KIMI DESIGN
# Repository: https://github.com/denysabramob-lab/-BG-Remover.git

FROM python:3.11-slim-bookworm

LABEL maintainer="KIMI DESIGN"
LABEL description="BG Remover Pro - AI Background Removal Tool"
LABEL version="1.0.0"

# Prevent interactive prompts during build
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    wget \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY pyproject.toml poetry.lock* ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
    torch \
    torchvision \
    --index-url https://download.pytorch.org/whl/cpu

# Install other dependencies
RUN pip install --no-cache-dir \
    transformers==4.38.2 \
    opencv-python \
    numpy \
    Pillow \
    scipy \
    rembg \
    onnxruntime \
    fastapi \
    uvicorn \
    python-multipart

# Install segment-anything from git
RUN pip install --no-cache-dir \
    git+https://github.com/facebookresearch/segment-anything.git

# Create directories for uploads, results, and previews
RUN mkdir -p /app/uploads /app/results /app/previews /app/sours

# Copy application code
COPY web_ui.py main.py ./
COPY run_web.sh run_all.sh ./

# Make scripts executable
RUN chmod +x /app/run_web.sh /app/run_all.sh

# Expose port for web UI
EXPOSE 7860

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:7860/ || exit 1

# Set entrypoint
ENTRYPOINT ["python", "web_ui.py"]
