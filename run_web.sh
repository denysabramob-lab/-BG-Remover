#!/bin/bash

# BG Remover Pro - Web UI Launcher
# KIMI DESIGN

cd "$(dirname "$0")"

echo "========================================"
echo "   BG Remover Pro - Starting..."
echo "========================================"

# Check for Poetry
if command -v poetry &> /dev/null && [ -f "poetry.lock" ]; then
    echo "Using Poetry..."
    poetry run python web_ui.py
else
    echo "Using virtual environment..."
    source .venv/bin/activate
    python web_ui.py
fi
