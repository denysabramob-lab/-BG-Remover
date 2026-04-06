#!/bin/bash

# BG Remover Pro - Batch Processing (CLI)
# KIMI DESIGN
# Repository: https://github.com/denysabramob-lab/-BG-Remover.git

cd "$(dirname "$0")"

# Check if venv exists
if [ ! -d ".venv" ]; then
    echo "Virtual environment not found!"
    echo "Please run: python3 install.py"
    exit 1
fi

# Ensure directories exist
mkdir -p sours results

echo "========================================"
echo "   BG Remover Pro - Batch Processing"
echo "   KIMI DESIGN"
echo "========================================"
echo ""
echo "Place images in 'sours' folder"
echo "Results will be saved to 'results' folder"
echo ""

if command -v poetry &> /dev/null && [ -f "poetry.lock" ]; then
    poetry run python main.py
else
    source .venv/bin/activate
    python main.py
fi

echo ""
echo "========================================"
echo "Done! Check results folder."
echo "========================================"
