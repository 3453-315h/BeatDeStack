@echo off
setlocal
echo ==========================================
echo BeatDeStack Extended Distribution Builder
echo ==========================================
echo.

REM Check for venv_amd
if not exist venv_amd (
    echo ERROR: venv_amd not found!
    echo Please run build_amd_rocmsdk.bat first to set up the environment.
    pause
    exit /b 1
)

echo Activating environment...
call venv_amd\Scripts\activate

echo.
echo ==========================================
echo BUILD 1/2: BeatDeStackExtended_ROCm.exe (Full)
echo Includes rocm_runtime folder (~1.4GB+)
echo ==========================================
pyinstaller --clean --noconsole --onefile --name BeatDeStackExtended_ROCm --icon=resources/icon.png --version-file=version_info.txt --add-data "src;src" --add-data "resources;resources" --add-data "models;models" --add-data "rocm_runtime;rocm_runtime" --collect-all demucs --collect-all torchaudio --collect-all soundfile --collect-all numpy --hidden-import="sklearn.utils._cython_blas" --hidden-import="sklearn.neighbors.typedefs" --hidden-import="sklearn.neighbors.quad_tree" --hidden-import="sklearn.tree._utils" main.py

if %errorlevel% neq 0 (
    echo ERROR: Build 1 failed!
    pause
    exit /b 1
)

echo.
echo ==========================================
echo BUILD 2/2: BeatDeStackExtended.exe (Lite)
echo NO rocm_runtime (~400MB)
echo ==========================================
pyinstaller --clean --noconsole --onefile --name BeatDeStackExtended --icon=resources/icon.png --version-file=version_info.txt --add-data "src;src" --add-data "resources;resources" --add-data "models;models" --collect-all demucs --collect-all torchaudio --collect-all soundfile --collect-all numpy --hidden-import="sklearn.utils._cython_blas" --hidden-import="sklearn.neighbors.typedefs" --hidden-import="sklearn.neighbors.quad_tree" --hidden-import="sklearn.tree._utils" main.py

if %errorlevel% neq 0 (
    echo ERROR: Build 2 failed!
    pause
    exit /b 1
)

echo.
echo ==========================================
echo BUILD 3/3: BeatDeStackExtended_DirectML.exe
echo Experimental DirectML Build
echo ==========================================
echo Launching separate DirectML build script...
cmd /c build_directml.bat

echo.
echo ==========================================
echo BUILD 4/4: BeatDeStackExtended_CUDA.exe
echo NVIDIA CUDA Build
echo ==========================================
echo Launching separate CUDA build script...
cmd /c build_cuda.bat

echo.
echo ==========================================
echo All Builds Complete!
echo Location: dist/
echo ==========================================
pause
