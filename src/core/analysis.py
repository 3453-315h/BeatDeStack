"""
Audio Analysis Module - BPM and Key Detection
Uses librosa for tempo estimation and key detection via chroma features.
"""
import os
import numpy as np
from src.utils.logger import logger

# Try to import librosa, fall back gracefully if not available
try:
    import librosa
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False
    logger.warning("librosa not installed. BPM/Key detection unavailable.")


# Musical key names (using Camelot wheel order for DJ-friendly display)
KEY_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
MODE_NAMES = {0: 'min', 1: 'maj'}  # Minor, Major


def analyze_audio(file_path: str, duration: float = 60.0) -> dict:
    """
    Analyze audio file for BPM and musical key.
    
    Args:
        file_path: Path to audio file
        duration: Max seconds to analyze (for speed, default 60s)
    
    Returns:
        dict with keys: 'bpm', 'key', 'key_confidence', 'success'
    """
    result = {
        'bpm': None,
        'key': None,
        'key_confidence': 0.0,
        'success': False,
        'error': None
    }
    
    if not LIBROSA_AVAILABLE:
        result['error'] = 'librosa not installed'
        return result
    
    if not os.path.exists(file_path):
        result['error'] = 'File not found'
        return result
    
    try:
        # Load audio (mono, limited duration for speed)
        y, sr = librosa.load(file_path, sr=22050, mono=True, duration=duration)
        
        # ---- BPM Detection ----
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        # tempo can be array or scalar depending on librosa version
        bpm = float(tempo[0]) if hasattr(tempo, '__iter__') else float(tempo)
        result['bpm'] = round(bpm, 1)
        
        # ---- Key Detection ----
        # Use chroma features for key detection
        chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
        
        # Average chroma across time
        chroma_avg = np.mean(chroma, axis=1)
        
        # Find the strongest pitch class (0-11)
        root_note = int(np.argmax(chroma_avg))
        
        # Estimate major vs minor using simple heuristic:
        # Compare strength of major 3rd (4 semitones) vs minor 3rd (3 semitones)
        major_third_idx = (root_note + 4) % 12
        minor_third_idx = (root_note + 3) % 12
        
        if chroma_avg[major_third_idx] > chroma_avg[minor_third_idx]:
            mode = 1  # Major
        else:
            mode = 0  # Minor
        
        key_name = KEY_NAMES[root_note]
        mode_name = MODE_NAMES[mode]
        result['key'] = f"{key_name} {mode_name}"
        
        # Confidence is based on how much the root dominates
        result['key_confidence'] = float(chroma_avg[root_note] / np.sum(chroma_avg))
        
        result['success'] = True
        logger.info(f"Analysis complete: {result['bpm']} BPM, {result['key']}")
        
    except Exception as e:
        result['error'] = str(e)
        logger.error(f"Audio analysis failed: {e}")
    
    return result


def format_analysis_string(analysis: dict) -> str:
    """
    Format analysis result for display.
    
    Returns string like "120 BPM • A min" or "Analysis unavailable"
    """
    if not analysis.get('success'):
        return ""
    
    parts = []
    if analysis.get('bpm'):
        parts.append(f"{int(analysis['bpm'])} BPM")
    if analysis.get('key'):
        parts.append(analysis['key'])
    
    return " • ".join(parts) if parts else ""


def get_filename_suffix(analysis: dict) -> str:
    """
    Get analysis info formatted for filename.
    
    Returns string like "_120bpm_Amin" or ""
    """
    if not analysis.get('success'):
        return ""
    
    parts = []
    if analysis.get('bpm'):
        parts.append(f"{int(analysis['bpm'])}bpm")
    if analysis.get('key'):
        # Replace space and # for filename safety
        key_part = analysis['key'].replace(' ', '').replace('#', 's')
        parts.append(key_part)
    
    return "_" + "_".join(parts) if parts else ""
