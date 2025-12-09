#!/bin/bash
# ==========================================
# StemLab Linux AMD ROCm Build
# ==========================================

set -e  # Exit on error

echo "=========================================="
echo "StemLab Linux ROCm Build (AMD GPU)"
echo "=========================================="
echo ""

# Check for Python 3.10
if ! command -v python3.10 &> /dev/null; then
    echo "ERROR: Python 3.10 not found!"
    echo "Install with your package manager, e.g.:"
    echo "  Ubuntu/Debian: sudo apt install python3.10 python3.10-venv"
    echo "  Fedora: sudo dnf install python3.10"
    exit 1
fi

# Check for ROCm
if ! command -v rocminfo &> /dev/null; then
    echo "WARNING: ROCm utilities not found in PATH."
    echo "Make sure ROCm is properly installed."
    echo "See: https://rocm.docs.amd.com/en/latest/deploy/linux/quick_start.html"
    echo ""
fi

echo "Step 1: Creating Virtual Environment (venv_rocm)..."
if [ -d "venv_rocm" ]; then
    echo "Removing old venv_rocm..."
    rm -rf venv_rocm
fi
python3.10 -m venv venv_rocm

echo ""
echo "Step 2: Installing Dependencies (ROCm Version)..."
source venv_rocm/bin/activate
python -m pip install --upgrade pip
pip install PyQt6 soundfile numpy

echo ""
echo "Installing PyTorch with ROCm 6.0 support..."
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/rocm6.0

echo ""
echo "Installing Demucs and other tools..."
pip install demucs audio-separator pyinstaller onnxruntime

echo ""
echo "Step 3: Building Executable..."
pyinstaller --clean --noconsole --onefile --name StemLab_ROCm \
    --add-data "src:src" --add-data "resources:resources" --add-data "models:models" \
    --collect-all demucs --collect-all torchaudio --collect-all soundfile \
    --collect-all numpy \
    --hidden-import="sklearn.utils._cython_blas" \
    --hidden-import="sklearn.neighbors.typedefs" \
    --hidden-import="sklearn.neighbors.quad_tree" \
    --hidden-import="sklearn.tree._utils" \
    main.py

echo ""
echo "=========================================="
echo "Build Complete!"
echo "You can find StemLab_ROCm in the dist folder."
echo ""
echo "This build will use AMD GPU (ROCm/HIP)"
echo "for accelerated audio separation."
echo "=========================================="
