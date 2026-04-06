#!/usr/bin/env python3
"""
BG Remover Pro - Cross-platform Installation Script
KIMI DESIGN

Supported platforms:
- Linux (Ubuntu, Debian, CentOS, etc.)
- macOS (Intel & Apple Silicon)
- Windows 10/11 (native Python or WSL2)

Repository: https://github.com/denysabramob-lab/-BG-Remover.git
"""

import os
import sys
import subprocess
import platform
import shutil
from pathlib import Path

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_colored(text, color=Colors.BLUE):
    """Print colored text (works on Linux/Mac, ignored on Windows)"""
    if platform.system() != "Windows":
        print(f"{color}{text}{Colors.ENDC}")
    else:
        print(text)

def print_header():
    print_colored("=" * 50, Colors.HEADER)
    print_colored("   BG Remover Pro - Installation", Colors.CYAN)
    print_colored("        KIMI DESIGN", Colors.CYAN)
    print_colored("=" * 50, Colors.HEADER)
    print()

def run_command(cmd, description="", check=True):
    """Run shell command with error handling"""
    if description:
        print_colored(f"➜ {description}...", Colors.YELLOW)
    
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            check=check
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except subprocess.CalledProcessError as e:
        if check:
            print_colored(f"✗ Error: {e}", Colors.RED)
            if e.stderr:
                print(e.stderr)
        return None

def check_python_version():
    """Check if Python version is 3.11 or higher"""
    print_colored("Checking Python version...", Colors.YELLOW)
    
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 11):
        print_colored(f"✗ Python 3.11+ required, found {version.major}.{version.minor}", Colors.RED)
        print("Please install Python 3.11 or higher:")
        print("  Ubuntu/Debian: sudo apt install python3.11 python3.11-venv")
        print("  macOS: brew install python@3.11")
        print("  Windows: Download from python.org")
        return False
    
    print_colored(f"✓ Python {version.major}.{version.minor}.{version.micro} OK", Colors.GREEN)
    return True

def check_git():
    """Check if git is installed"""
    git_path = shutil.which("git")
    if not git_path:
        print_colored("✗ Git not found. Please install Git:", Colors.RED)
        print("  Ubuntu/Debian: sudo apt install git")
        print("  macOS: brew install git")
        print("  Windows: https://git-scm.com/download/win")
        return False
    return True

def create_virtual_env():
    """Create Python virtual environment"""
    print_colored("Creating virtual environment...", Colors.YELLOW)
    
    venv_path = Path(".venv")
    if venv_path.exists():
        print_colored("  Virtual environment already exists, skipping...", Colors.YELLOW)
        return True
    
    try:
        subprocess.run([sys.executable, "-m", "venv", ".venv"], check=True)
        print_colored("✓ Virtual environment created", Colors.GREEN)
        return True
    except Exception as e:
        print_colored(f"✗ Failed to create virtual environment: {e}", Colors.RED)
        return False

def get_venv_python():
    """Get path to Python in virtual environment"""
    if platform.system() == "Windows":
        return ".venv\\Scripts\\python.exe"
    return ".venv/bin/python"

def get_venv_pip():
    """Get path to pip in virtual environment"""
    if platform.system() == "Windows":
        return ".venv\\Scripts\\pip.exe"
    return ".venv/bin/pip"

def install_dependencies():
    """Install all required packages"""
    print_colored("Installing dependencies (this may take a few minutes)...", Colors.YELLOW)
    
    pip_cmd = get_venv_pip()
    python_cmd = get_venv_python()
    
    # Upgrade pip first
    print_colored("  Upgrading pip...", Colors.YELLOW)
    run_command(f"{pip_cmd} install --upgrade pip", check=False)
    
    # Core ML packages
    packages = [
        "torch",
        "torchvision",
        "transformers==4.38.2",
        "opencv-python",
        "numpy",
        "Pillow",
        "scipy",
        "rembg",
        "onnxruntime",
        "fastapi",
        "uvicorn",
        "python-multipart",
    ]
    
    for package in packages:
        print_colored(f"  Installing {package}...", Colors.YELLOW)
        if package == "torch":
            # Install CPU-only version for smaller size
            result = run_command(
                f'{pip_cmd} install torch torchvision --index-url https://download.pytorch.org/whl/cpu',
                check=False
            )
        else:
            result = run_command(f"{pip_cmd} install {package}", check=False)
        
        if result is None:
            print_colored(f"  ⚠ Warning: Failed to install {package}", Colors.YELLOW)
    
    # Install segment-anything from git
    print_colored("  Installing segment-anything...", Colors.YELLOW)
    run_command(
        f'{pip_cmd} install git+https://github.com/facebookresearch/segment-anything.git',
        check=False
    )
    
    print_colored("✓ Dependencies installed", Colors.GREEN)
    return True

def check_poetry():
    """Check if Poetry is available"""
    return shutil.which("poetry") is not None

def install_with_poetry():
    """Install using Poetry"""
    print_colored("Using Poetry for installation...", Colors.BLUE)
    
    # Configure poetry to create venv in project
    run_command("poetry config virtualenvs.in-project true", check=False)
    
    # Install dependencies
    print_colored("Installing packages with Poetry...", Colors.YELLOW)
    result = run_command("poetry install --no-interaction", check=False)
    
    if result is not None:
        print_colored("✓ Installation completed with Poetry!", Colors.GREEN)
        return True
    return False

def create_run_scripts():
    """Create platform-specific run scripts"""
    print_colored("Creating run scripts...", Colors.YELLOW)
    
    # Windows batch files
    if platform.system() == "Windows":
        # run_web.bat
        with open("run_web.bat", "w") as f:
            f.write('''@echo off
echo =======================================
echo    BG Remover Pro - Starting...
echo =======================================
cd /d "%~dp0"
.venv\\Scripts\\python.exe web_ui.py
pause
''')
        
        # run_all.bat
        with open("run_all.bat", "w") as f:
            f.write('''@echo off
cd /d "%~dp0"
if not exist sours mkdir sours
if not exist results mkdir results
.venv\\Scripts\\python.exe main.py
echo.
echo Results saved to: .\\results\\
pause
''')
        
        print_colored("✓ Created run_web.bat and run_all.bat", Colors.GREEN)
    
    else:
        # Unix shell scripts (already exist, just ensure they're executable)
        for script in ["run_web.sh", "run_all.sh", "install.sh"]:
            if os.path.exists(script):
                os.chmod(script, 0o755)
        print_colored("✓ Shell scripts are ready", Colors.GREEN)

def print_final_instructions(use_poetry=False):
    """Print final instructions"""
    print()
    print_colored("=" * 50, Colors.HEADER)
    print_colored("   Installation Complete!", Colors.GREEN)
    print_colored("=" * 50, Colors.HEADER)
    print()
    
    print_colored("To run the application:", Colors.CYAN)
    
    if platform.system() == "Windows":
        if use_poetry:
            print("  poetry run python web_ui.py")
        else:
            print("  Double-click: run_web.bat")
            print("  Or in terminal: .venv\\Scripts\\python.exe web_ui.py")
    else:
        if use_poetry:
            print("  poetry run python web_ui.py")
        else:
            print("  ./run_web.sh")
            print("  Or: source .venv/bin/activate && python web_ui.py")
    
    print()
    print_colored("Then open in browser:", Colors.CYAN)
    print("  http://localhost:7860")
    print()
    print_colored("Repository:", Colors.CYAN)
    print("  https://github.com/denysabramob-lab/-BG-Remover.git")
    print()

def main():
    """Main installation flow"""
    print_header()
    
    # Platform info
    print(f"Platform: {platform.system()} {platform.release()}")
    print(f"Python: {sys.executable}")
    print()
    
    # Pre-flight checks
    if not check_python_version():
        sys.exit(1)
    
    if not check_git():
        print_colored("⚠ Git not found. Some features may not work.", Colors.YELLOW)
    
    # Check if we're in the right directory
    if not os.path.exists("pyproject.toml") and not os.path.exists("web_ui.py"):
        print_colored("✗ Error: Not in project root directory", Colors.RED)
        print("Please run this script from the project folder.")
        sys.exit(1)
    
    # Try Poetry first if available
    if check_poetry() and os.path.exists("poetry.lock"):
        print_colored("Poetry detected!", Colors.GREEN)
        if install_with_poetry():
            create_run_scripts()
            print_final_instructions(use_poetry=True)
            return
        else:
            print_colored("Poetry installation failed, falling back to pip...", Colors.YELLOW)
    
    # Standard pip installation
    print_colored("Using pip for installation...", Colors.BLUE)
    
    if not create_virtual_env():
        sys.exit(1)
    
    if not install_dependencies():
        print_colored("⚠ Some packages failed to install", Colors.YELLOW)
    
    create_run_scripts()
    print_final_instructions(use_poetry=False)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        print_colored("\nInstallation cancelled by user.", Colors.YELLOW)
        sys.exit(1)
    except Exception as e:
        print_colored(f"\n✗ Installation failed: {e}", Colors.RED)
        sys.exit(1)
