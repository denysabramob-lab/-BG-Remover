#!/bin/bash

# BG Remover Pro - Batch Processing (CLI)
# KIMI DESIGN

cd "$(dirname "$0")"

# Ensure sours directory exists
mkdir -p sours results

if command -v poetry &> /dev/null && [ -f "poetry.lock" ]; then
    echo "Using Poetry..."
    poetry run python main.py
else
    echo "Using virtual environment..."
    source .venv/bin/activate
    python main.py
fi

echo ""
echo "Results saved to: ./results/"
