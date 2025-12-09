@echo off
setlocal
echo ==========================================
echo BeatDeStack Extended NVIDIA CUDA Build
echo ==========================================
echo.

REM Check for Python 3.10+
py --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found!
    pause
    exit /b 1
)

echo Step 1: Creating Virtual Environment (venv_cuda)...
if not exist venv_cuda (
    py -m venv venv_cuda
)

echo.
echo Step 2: Installing Dependencies...
call venv_cuda\Scripts\activate
python -m pip install --upgrade pip
REM Install PyTorch with CUDA 12.1 (Broad release compatibility)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
pip install PyQt6 soundfile numpy demucs audio-separator pyinstaller onnxruntime-gpu tensorflow pretty_midi basic-pitch mir_eval librosa resampy tf-keras

echo.
echo Step 3: Building EXE (CUDA)...
pyinstaller --clean --noconsole --onefile --name BeatDeStackExtended_CUDA --icon=resources/icon.png --version-file=version_info.txt --add-data "src;src" --add-data "resources;resources" --add-data "models;models" --collect-all demucs --collect-all torchaudio --collect-all soundfile --collect-all numpy --collect-all basic_pitch --collect-all pretty_midi --collect-all tf_keras --hidden-import="sklearn.utils._cython_blas" --hidden-import="sklearn.neighbors.typedefs" --hidden-import="sklearn.neighbors.quad_tree" --hidden-import="sklearn.tree._utils" main.py

if %errorlevel% neq 0 (
    echo ERROR: CUDA Build failed!
    pause
    exit /b 1
)

echo.
echo ==========================================
echo Build Complete!
echo Location: dist/BeatDeStackExtended_CUDA.exe
echo ==========================================
pause
