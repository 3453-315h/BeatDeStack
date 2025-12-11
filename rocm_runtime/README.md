# AMD ROCm Runtime for Windows

This folder contains AMD's ROCm SDK libraries required for GPU acceleration on AMD graphics cards.

## Contents

### bin/ - Core HIP Runtime
- `amdhip64_7.dll` - HIP runtime library
- `amd_comgr0701.dll` - AMD compiler
- `hiprtc0701.dll` - HIP runtime compilation
- `hiprtc-builtins0701.dll` - HIP built-in functions
- `rocm-openblas.dll` - OpenBLAS for ROCm

### lib/ - ROCm Libraries
- `MIOpen.dll` - AMD Deep Learning Library
- `rocblas.dll` - BLAS operations
- `rocfft.dll` - FFT operations
- `rocrand.dll` - Random number generation
- `rocsolver.dll` - Linear algebra solver
- `rocsparse.dll` - Sparse matrix operations
- `hipfft.dll`, `hipfftw.dll` - HIP FFT
- `libhipblas.dll`, `libhipblaslt.dll` - HIP BLAS
- `hiprand.dll`, `hipsolver.dll`, `hipsparse.dll` - HIP wrappers

## Requirements

You need AMD's PyTorch driver installed:
https://www.amd.com/en/resources/support-articles/release-notes/RN-AMDGPU-WINDOWS-PYTORCH-7-1-1.html

## Usage

Run StemLab with AMD GPU (bundled SDK):
```batch
run_amd_rocmsdk.bat
```

The run script automatically adds these DLLs to the system PATH.
