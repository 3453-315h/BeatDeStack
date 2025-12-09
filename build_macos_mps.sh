#!/bin/bash
# ==========================================
# StemLab macOS MPS (Apple Silicon) Build
# ==========================================

set -e  # Exit on error

echo "=========================================="
echo "StemLab macOS MPS Build (Apple Silicon)"
echo "=========================================="
echo ""

# Check for Python 3.10
if ! command -v python3.10 &> /dev/null; then
    echo "ERROR: Python 3.10 not found!"
    echo "Install with: brew install python@3.10"
    exit 1
fi

# Check for Apple Silicon
ARCH=$(uname -m)
if [ "$ARCH" != "arm64" ]; then
    echo "WARNING: This script is optimized for Apple Silicon (arm64)."
    echo "Detected architecture: $ARCH"
    echo "MPS acceleration may not be available."
    echo ""
fi

echo "Step 1: Creating Virtual Environment (venv_macos_mps)..."
if [ -d "venv_macos_mps" ]; then
    echo "Removing old venv_macos_mps..."
    rm -rf venv_macos_mps
fi
python3.10 -m venv venv_macos_mps

echo ""
echo "Step 2: Installing Dependencies (MPS Version)..."
source venv_macos_mps/bin/activate
python -m pip install --upgrade pip
pip install PyQt6 soundfile numpy

echo ""
echo "Installing PyTorch with MPS support..."
# On macOS with Apple Silicon, MPS is included by default
pip install torch torchvision torchaudio

echo ""
echo "Installing Demucs and other tools..."
pip install demucs audio-separator pyinstaller onnxruntime

echo ""
echo "Step 3: Building App Bundle..."
pyinstaller --clean --noconsole --onefile --name StemLab_MPS \
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
echo "You can find StemLab_MPS in the dist folder."
echo ""
echo "This build will use Apple Silicon GPU (MPS)"
echo "for accelerated audio separation."
echo "=========================================="
