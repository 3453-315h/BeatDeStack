@echo off
setlocal
echo ==========================================
echo BeatDeStack Extended DirectML Build (Generic)
echo ==========================================
echo.

REM Check for Python 3.10+
py --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found!
    pause
    exit /b 1
)

echo Step 1: Creating Virtual Environment (venv_directml)...
if not exist venv_directml (
    py -m venv venv_directml
)

echo.
echo Step 2: Installing Dependencies...
call venv_directml\Scripts\activate
python -m pip install --upgrade pip

REM Install PyTorch (CPU) - DirectML will be handled by onnxruntime-directml
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

REM Install onnxruntime-directml and other deps
pip install PyQt6 soundfile numpy demucs audio-separator pyinstaller onnxruntime-directml tensorflow pretty_midi basic-pitch mir_eval librosa resampy tf-keras

echo.
echo Step 3: Building EXE (DirectML)...
REM Using BeatDeStackExtended_DirectML.spec if it exists, otherwise command line
if exist BeatDeStackExtended_DirectML.spec (
    pyinstaller BeatDeStackExtended_DirectML.spec
) else (
    pyinstaller --clean --noconsole --onefile --name BeatDeStackExtended_DirectML --icon=resources/icon.png --version-file=version_info.txt --add-data "src;src" --add-data "resources;resources" --add-data "models;models" --collect-all demucs --collect-all torchaudio --collect-all soundfile --collect-all numpy --collect-all basic_pitch --collect-all pretty_midi --collect-all tf_keras --hidden-import="sklearn.utils._cython_blas" --hidden-import="sklearn.neighbors.typedefs" --hidden-import="sklearn.neighbors.quad_tree" --hidden-import="sklearn.tree._utils" main.py
)

if %errorlevel% neq 0 (
    echo ERROR: DirectML Build failed!
    pause
    exit /b 1
)

echo.
echo ==========================================
echo Build Complete!
echo Location: dist/BeatDeStackExtended_DirectML.exe
echo ==========================================
pause
