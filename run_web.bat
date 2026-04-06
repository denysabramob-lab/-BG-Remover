@echo off
chcp 65001 >nul
echo =======================================
echo    BG Remover Pro - Starting
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

echo Starting Web UI...
echo Open http://localhost:7860 in your browser
echo.

.venv\Scripts\python.exe web_ui.py

pause
