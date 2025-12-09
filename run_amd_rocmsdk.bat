@echo off
REM ==========================================
REM StemLab AMD GPU Runner
REM Uses bundled ROCm runtime DLLs
REM ==========================================

REM Add ROCm DLLs to PATH (both external and venv site-packages)
set PATH=%~dp0rocm_runtime\bin;%~dp0rocm_runtime\lib;%PATH%
set PATH=%~dp0venv_amd\Lib\site-packages\_rocm_sdk_core\bin;%PATH%
set PATH=%~dp0venv_amd\Lib\site-packages\_rocm_sdk_libraries_custom\bin;%PATH%

REM Set AMD GPU visibility (1 = RX 6600, 0 = APU)
set HIP_VISIBLE_DEVICES=1

REM Check for virtual environment
if exist venv_amd (
    call venv_amd\Scripts\activate
    python main.py
) else if exist venv_cpu (
    call venv_cpu\Scripts\activate
    python main.py
) else (
    echo ERROR: No virtual environment found!
    echo Run build_rocm.bat first to create venv_amd.
    pause
    exit /b 1
)
pause
