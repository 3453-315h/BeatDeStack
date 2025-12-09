# BeatDeStack Extended v3.5.0

**The Ultimate Offline AI Stem Separation & Audio Enhancement Tool.**
This release introduces major features including Audio-to-MIDI export, a professional Audio Enhancement Suite, and significant stability improvements.

## 🌟 New Features
*   **🎹 Audio-to-MIDI Export**: Convert any separated stem (Vocals, Bass, etc.) into a MIDI file using Spotify's Basic Pitch technology.
*   **🎛️ Audio Enhancement Suite**:
    *   **De-Reverb**: Remove room ambience (`Reverb_HQ`).
    *   **De-Echo**: Eliminate slapback delay.
    *   **De-Noise**: Clean up background hiss/static (`UVR-DeNoise`).
    *   **Stereo Width**: Expand or narrow the soundstage.
*   **🧠 Advanced Model Management**:
    *   **Persistence**: Models are now saved permanently in the local folder.
    *   **Import**: Support for dragging and dropping custom `.pth` / `.onnx` models.
*   **🐱 Nyan Cat Mode**: Find the secret in the "About" tab!

## 🐛 Bug Fixes & Improvements
*   **Critical Crash Fix**: Resolved app crash when dragging files into the executable logic (Missing Signal).
*   **Startup Fix**: Added `multiprocessing.freeze_support` for stable Windows execution.
*   **UI Polish**: Corrected right-sidebar layout and icon scaling.
*   **Build System**: Unified build scripts for CUDA, ROCm, DirectML, and CPU.

## 📦 Downloads
Select the version matching your hardware:

*   `BeatDeStackExtended_CUDA.exe` - **Best for NVIDIA** (RTX 3060, 4090, etc.)
*   `BeatDeStackExtended_ROCm.exe` - **Best for AMD** (Radeon RX 6000/7000)
*   `BeatDeStackExtended_DirectML.exe` - **Broad Compatibility** (Intel ARC, older GPUs)
*   `BeatDeStackExtended.exe` - **CPU Only** (Universal, slower)

> **Note**: These are portable executables. No installation required. Just download and run.
