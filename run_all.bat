@echo off
chcp 65001 >nul
echo =======================================
echo    BG Remover Pro - Batch Processing
echo    KIMI DESIGN
echo =======================================
echo.
cd /d "%~dp0"

if not exist .venv\Scripts\python.exe (
    echo Virtual environment not found!
    echo Please run: python install.py
    pause
    exit /b 1
)

if not exist sours mkdir sours
if not exist results mkdir results

echo Place images in 'sours' folder
echo Results will be saved to 'results' folder
echo.

.venv\Scripts\python.exe main.py

echo.
echo =======================================
echo Done! Check results folder.
echo =======================================
pause
