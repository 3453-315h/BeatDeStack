# CUDA Build Guide for BeatDeStack Extended

This guide is for **NVIDIA GPU users** who want to build BeatDeStack Extended from source with CUDA support.

## Why Build from Source?

The pre-built CUDA EXE is ~3.1 GB because PyTorch bundles the entire CUDA runtime. Building from source lets you:

- Use your system's existing CUDA installation
- Create a smaller executable
- Customize for your specific GPU

---

## Prerequisites

### Required Software

| Software | Version | Download |
|----------|---------|----------|
| Python | 3.10 - 3.12 | [python.org](https://www.python.org/downloads/) |
| CUDA Toolkit | 11.8 or 12.1 | [NVIDIA](https://developer.nvidia.com/cuda-toolkit) |
| cuDNN | 8.x (matching CUDA) | [NVIDIA cuDNN](https://developer.nvidia.com/cudnn) |
| Git | Any | [git-scm.com](https://git-scm.com/) |

### Verify CUDA Installation

```powershell
nvcc --version
# Should output: Cuda compilation tools, release 11.8, V11.8.89
```

---

## Build Steps

### 1. Clone the Repository

```powershell
git clone https://github.com/3453-315h/BeatDeStackExtended.git
cd BeatDeStackExtended
```

### 2. Create Virtual Environment

```powershell
py -3.12 -m venv venv_cuda
.\venv_cuda\Scripts\activate
```

### 3. Install PyTorch with CUDA

**CUDA 11.8:**

```powershell
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

**CUDA 12.1:**

```powershell
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

### 4. Install Dependencies

```powershell
pip install demucs audio-separator pyinstaller soundfile numpy scipy PyQt6 noisereduce librosa onnxruntime-gpu
```

### 5. Build

```powershell
.\build_scripts\build_slim_cuda.bat
```

Output: `dist\BeatDeStackExtended_Slim_CUDA.exe`

---

## Troubleshooting

- **CUDA not available**: Verify `nvcc --version` works, reinstall PyTorch
- **GPU not detected**: Update NVIDIA drivers, check CUDA Toolkit version

## Alternative

Use the **DirectML build** (438 MB) - works on NVIDIA, AMD, and Intel GPUs without CUDA setup.
