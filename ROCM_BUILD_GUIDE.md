# ROCm Build Guide for BeatDeStack Extended

This guide is for **AMD GPU users** who want to build BeatDeStack Extended with ROCm support.

> **Note:** ROCm is available on both **Linux** and **Windows**. PyTorch's official ROCm wheels are Linux-only. For Windows AMD users, use the **DirectML build** instead.

---

## Supported Hardware

| AMD GPU Series | ROCm Support |
|----------------|--------------|
| RX 7000 (RDNA 3) | ✅ Full |
| RX 6000 (RDNA 2) | ✅ Full |
| RX 5000 (RDNA 1) | ✅ Full |
| RX Vega | ✅ Full |

## Prerequisites (Linux)

- Ubuntu 22.04 LTS
- ROCm 5.6+
- Python 3.10 - 3.12

---

## Build Steps

### 1. Install ROCm (Ubuntu)

```bash
wget https://repo.radeon.com/rocm/rocm.gpg.key -O - | gpg --dearmor | sudo tee /etc/apt/keyrings/rocm.gpg > /dev/null
echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/rocm.gpg] https://repo.radeon.com/rocm/apt/5.6 jammy main" | sudo tee /etc/apt/sources.list.d/rocm.list
sudo apt update && sudo apt install rocm-hip-sdk rocm-libs
sudo usermod -aG video,render $USER
# Reboot after this
```

### 2. Clone & Setup

```bash
git clone https://github.com/3453-315h/BeatDeStackExtended.git
cd BeatDeStackExtended
python3.12 -m venv venv_rocm
source venv_rocm/bin/activate
```

### 3. Install PyTorch ROCm

```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/rocm5.6
```

### 4. Install Dependencies

```bash
pip install demucs audio-separator pyinstaller soundfile numpy scipy PyQt6 noisereduce librosa onnxruntime
```

### 5. Build

```bash
chmod +x build_scripts/build_slim_rocm.sh
./build_scripts/build_slim_rocm.sh
```

Output: `dist/BeatDeStackExtended_Slim_ROCm`

---

## Alternative: DirectML (Windows)

For AMD GPUs on Windows, use the **DirectML build** (438 MB) - no ROCm setup required.
