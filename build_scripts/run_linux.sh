#!/bin/bash
# ==========================================
# StemLab Linux Run Script
# ==========================================

# Try virtual environments
if [ -d ".venv" ]; then
    echo "Using .venv virtual environment..."
    source .venv/bin/activate
elif [ -d "venv_cuda" ]; then
    echo "Using CUDA virtual environment..."
    source venv_cuda/bin/activate
elif [ -d "venv_rocm" ]; then
    echo "Using ROCm virtual environment..."
    source venv_rocm/bin/activate
elif [ -d "venv_cpu" ]; then
    echo "Using CPU virtual environment..."
    source venv_cpu/bin/activate
else
    echo "ERROR: No virtual environment found!"
    exit 1
fi

python main.py
