#!/bin/bash
# ==========================================
# StemLab macOS CPU Build
# ==========================================

set -e  # Exit on error

echo "=========================================="
echo "StemLab macOS CPU Build"
echo "=========================================="
echo ""

# Check for Python 3.10
if ! command -v python3.10 &> /dev/null; then
    echo "ERROR: Python 3.10 not found!"
    echo "Install with: brew install python@3.10"
    exit 1
fi

echo "Step 1: Creating Virtual Environment (venv_macos_cpu)..."
if [ -d "venv_macos_cpu" ]; then
    echo "Removing old venv_macos_cpu..."
    rm -rf venv_macos_cpu
fi
python3.10 -m venv venv_macos_cpu

echo ""
echo "Step 2: Installing Dependencies (CPU Version)..."
source venv_macos_cpu/bin/activate
python -m pip install --upgrade pip
pip install PyQt6 soundfile numpy

echo ""
echo "Installing PyTorch (CPU)..."
pip install torch torchvision torchaudio

echo ""
echo "Installing Demucs and other tools..."
pip install demucs audio-separator pyinstaller onnxruntime

echo ""
echo "Step 3: Building App Bundle..."
pyinstaller --clean --noconsole --onefile --name StemLab \
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
echo "You can find StemLab in the dist folder."
echo "=========================================="
