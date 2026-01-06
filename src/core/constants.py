"""
Centralized constants for BeatDeStack.
Avoids "magic strings" scattered across the codebase.
"""

# --- Operation Modes ---
MODE_STANDARD = "standard"
MODE_VOCALS = "vocals_only"
MODE_INSTRUMENTAL = "instrumental"
MODE_DRUMS = "drums_only"
MODE_BASS = "bass_only"
MODE_GUITAR = "guitar_only"
MODE_PIANO = "piano_only"

# --- Model Names ---
# Demucs
MODEL_HTDEMUCS = "htdemucs"
MODEL_HTDEMUCS_FT = "htdemucs_ft"
MODEL_HTDEMUCS_6S = "htdemucs_6s"

# Roformer (Vocals)
MODEL_ROFORMER_VOCALS = "vocals_mel_band_roformer.ckpt"

# BS-Roformer (Instrumental/Stems)
MODEL_BS_ROFORMER_INST = "model_bs_roformer_ep_317_sdr_12.9755.ckpt"

# MDX / UVR Models
MODEL_KIM_VOCAL_2 = "Kim_Vocal_2.onnx"
MODEL_MDX_INST_HQ_3 = "UVR-MDX-NET-Inst_HQ_3.onnx"
MODEL_MDX_VOCAL_FT = "UVR-MDX-NET-Voc_FT.onnx"
MODEL_DEECHO_DEREVERB = "UVR-DeEcho-DeReverb.pth"

# Model Checkpoint Filenames (for detection)
CHECKPOINT_EXTENSIONS = [".yaml", ".pth", ".ckpt", ".onnx"]

# --- Cleanup Patterns ---
CLEANUP_PATTERNS = ["_temp_", "(No Reverb)", "(Reverb)", "vocals_ensemble", "vocals_enhanced", "Kim_Vocal", "deverb"]

# --- Preset Names ---
PRESET_DEFAULT = "Default (Balanced)"
