#!/bin/bash
# ==========================================
# StemLab Linux Run Script
# ==========================================

# Try ROCm venv first, then CPU
if [ -d "venv_rocm" ]; then
    echo "Using ROCm virtual environment..."
    source venv_rocm/bin/activate
elif [ -d "venv_cpu" ]; then
    echo "Using CPU virtual environment..."
    source venv_cpu/bin/activate
else
    echo "ERROR: No virtual environment found!"
    echo "Run build_rocm.sh first."
    exit 1
fi

python main.py
