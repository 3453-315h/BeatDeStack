#!/bin/bash
# ==========================================
# StemLab macOS Run Script
# ==========================================

# Try MPS venv first, then CPU venv
if [ -d "venv_macos_mps" ]; then
    echo "Using MPS virtual environment..."
    source venv_macos_mps/bin/activate
elif [ -d "venv_macos_cpu" ]; then
    echo "Using CPU virtual environment..."
    source venv_macos_cpu/bin/activate
else
    echo "ERROR: No virtual environment found!"
    echo "Run build_macos_mps.sh or build_macos_cpu.sh first."
    exit 1
fi

python main.py
