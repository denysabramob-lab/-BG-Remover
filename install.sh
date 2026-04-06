#!/bin/bash

# BG Remover Pro - Installation Script
# KIMI DESIGN

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   BG Remover Pro - Installation${NC}"
echo -e "${BLUE}        KIMI DESIGN${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | grep -oP '\d+\.\d+' | head -1)
REQUIRED_VERSION="3.11"

echo -e "${YELLOW}Checking Python version...${NC}"
if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)" 2>/dev/null; then
    echo -e "${RED}Error: Python 3.11 or higher is required${NC}"
    echo "Current version: $(python3 --version 2>&1)"
    exit 1
fi
echo -e "${GREEN}✓ Python version OK: $(python3 --version)${NC}"

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo -e "${RED}Error: pyproject.toml not found${NC}"
    echo "Please run this script from the project root directory"
    exit 1
fi

echo ""
echo -e "${YELLOW}Installing dependencies...${NC}"

# Check for poetry
if command -v poetry &> /dev/null; then
    echo -e "${BLUE}Using Poetry for installation...${NC}"
    
    # Configure poetry
    poetry config virtualenvs.in-project true
    
    # Install dependencies
    echo -e "${YELLOW}Installing packages (this may take a few minutes)...${NC}"
    poetry install --no-interaction
    
    echo ""
    echo -e "${GREEN}✓ Installation completed successfully!${NC}"
    echo ""
    echo -e "${BLUE}To run the application:${NC}"
    echo "  poetry run python web_ui.py"
    echo "  or"
    echo "  ./run_web.sh"
    
else
    echo -e "${BLUE}Poetry not found, using pip...${NC}"
    
    # Create virtual environment
    if [ ! -d ".venv" ]; then
        echo -e "${YELLOW}Creating virtual environment...${NC}"
        python3 -m venv .venv
    fi
    
    # Activate virtual environment
    echo -e "${YELLOW}Activating virtual environment...${NC}"
    source .venv/bin/activate
    
    # Upgrade pip
    echo -e "${YELLOW}Upgrading pip...${NC}"
    pip install --upgrade pip
    
    # Install dependencies
    echo -e "${YELLOW}Installing packages (this may take a few minutes)...${NC}"
    pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
    pip install transformers==4.38.2
    pip install opencv-python numpy pillow scipy rembg onnxruntime fastapi uvicorn python-multipart
    pip install git+https://github.com/facebookresearch/segment-anything.git
    
    echo ""
    echo -e "${GREEN}✓ Installation completed successfully!${NC}"
    echo ""
    echo -e "${BLUE}To run the application:${NC}"
    echo "  source .venv/bin/activate"
    echo "  python web_ui.py"
    echo "  or"
    echo "  ./run_web.sh"
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}   Installation Complete!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "The application will be available at: http://localhost:7860"
echo ""
echo "For more information, see FAQ.md"
