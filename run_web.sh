#!/bin/bash

# BG Remover Pro - Web UI Launcher
# KIMI DESIGN
# Repository: https://github.com/denysabramob-lab/-BG-Remover.git

cd "$(dirname "$0")"

echo "========================================"
echo "   BG Remover Pro - Starting..."
echo "   KIMI DESIGN"
echo "========================================"
echo ""

# Check if venv exists
if [ ! -d ".venv" ]; then
    echo "Virtual environment not found!"
    echo "Please run: python3 install.py"
    exit 1
fi

# Check for Poetry
if command -v poetry &> /dev/null && [ -f "poetry.lock" ]; then
    echo "Using Poetry..."
    poetry run python web_ui.py
else
    echo "Using virtual environment..."
    echo "Open http://localhost:7860 in your browser"
    echo ""
    source .venv/bin/activate
    python web_ui.py
fi
