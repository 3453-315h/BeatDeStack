@echo off
setlocal
echo ==========================================
echo StemLab Windows AMD Build (Bundled ROCm SDK)
echo Uses bundled ROCm runtime from rocm_runtime folder
echo ==========================================
echo.

REM Check for Python 3.12 (required for PyTorch ROCm compatibility)
py -3.12 --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python 3.12 not found!
    echo PyTorch ROCm requires Python 3.12 or lower.
    echo Please install Python 3.12 from python.org
    pause
    exit /b 1
)

REM Check for rocm_runtime folder
if not exist rocm_runtime\bin\amdhip64_7.dll (
    echo ERROR: rocm_runtime folder not found or incomplete!
    echo Make sure you have the AMD ROCm DLLs in rocm_runtime\bin\ and rocm_runtime\lib\
    pause
    exit /b 1
)

echo Step 1: Creating Virtual Environment (venv_amd)...
if exist venv_amd (
    echo Removing old venv_amd...
    rmdir /s /q venv_amd
)
py -3.12 -m venv venv_amd

echo.
echo Step 2: Setting up ROCm environment...
set PATH=%~dp0rocm_runtime\bin;%~dp0rocm_runtime\lib;%PATH%

echo.
echo Step 3: Installing Dependencies (AMD ROCm SDK Version)...
call venv_amd\Scripts\activate
python -m pip install --upgrade pip
pip install PyQt6 soundfile numpy

echo.
echo Installing PyTorch with ROCm 6.0 support...
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/rocm6.0

echo.
echo Installing Demucs and other tools...
echo.
echo Installing Demucs and other tools...
echo.
echo Installing Demucs and other tools...
echo.
echo Installing Demucs and other tools...
pip install demucs audio-separator pyinstaller onnxruntime tensorflow pretty_midi basic-pitch mir_eval librosa resampy tf-keras

echo.
echo Step 4: Building EXE...
pyinstaller --clean --noconsole --onefile --name StemLab_AMD --add-data "src;src" --add-data "resources;resources" --add-data "rocm_runtime;rocm_runtime" --collect-all demucs --collect-all torchaudio --collect-all soundfile --collect-all numpy --collect-all basic_pitch --collect-all pretty_midi --collect-all tf_keras --hidden-import="sklearn.utils._cython_blas" --hidden-import="sklearn.neighbors.typedefs" --hidden-import="sklearn.neighbors.quad_tree" --hidden-import="sklearn.tree._utils" main.py

echo.
echo ==========================================
echo Build Complete!
echo.
echo To run from source: run_amd_rocmsdk.bat
echo Compiled EXE: dist\StemLab_AMD.exe
echo.
echo IMPORTANT: Make sure you have AMD's PyTorch driver:
echo https://www.amd.com/en/resources/support-articles/release-notes/RN-AMDGPU-WINDOWS-PYTORCH-7-1-1.html
echo ==========================================
pause
