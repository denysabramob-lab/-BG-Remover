#!/bin/bash

# BG Remover Pro - Installation Script
# KIMI DESIGN
# Repository: https://github.com/denysabramob-lab/-BG-Remover.git
#
# NOTE: This is a wrapper script that calls install.py
# For cross-platform installation, use: python3 install.py

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   BG Remover Pro - Installation${NC}"
echo -e "${BLUE}        KIMI DESIGN${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if we're in the right directory
if [ ! -f "install.py" ]; then
    echo -e "${RED}Error: install.py not found${NC}"
    echo "Please run this script from the project root directory"
    exit 1
fi

# Run the Python installer (works on all platforms)
python3 install.py
