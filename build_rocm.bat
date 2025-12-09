@echo off
setlocal
echo ==========================================
echo StemLab Windows AMD ROCm Build
echo ==========================================
echo.

REM Check for Python 3.10
py -3.10 --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python 3.10 not found!
    echo Please install Python 3.10 from python.org
    pause
    exit /b 1
)

echo Step 1: Creating Virtual Environment (venv_rocm)...
if exist venv_rocm (
    echo Removing old venv_rocm...
    rmdir /s /q venv_rocm
)
py -3.10 -m venv venv_rocm

echo.
echo Step 2: Installing Dependencies (ROCm Version)...
call venv_rocm\Scripts\activate
python -m pip install --upgrade pip
pip install PyQt6 soundfile numpy

echo.
echo Installing PyTorch with ROCm 6.0 support...
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/rocm6.0

echo.
echo Installing Demucs and other tools...
pip install demucs audio-separator pyinstaller onnxruntime

echo.
echo Step 3: Building EXE...
pyinstaller --clean --noconsole --onefile --name StemLab_ROCm --add-data "src;src" --add-data "resources;resources" --collect-all demucs --collect-all torchaudio --collect-all soundfile --collect-all numpy --hidden-import="sklearn.utils._cython_blas" --hidden-import="sklearn.neighbors.typedefs" --hidden-import="sklearn.neighbors.quad_tree" --hidden-import="sklearn.tree._utils" main.py

echo.
echo ==========================================
echo Build Complete!
echo You can find StemLab_ROCm.exe in the dist folder.
echo.
echo This build will use AMD GPU (ROCm/HIP)
echo for accelerated audio separation.
echo ==========================================
pause
