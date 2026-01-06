"""
Processing Presets - Save and load separation configurations
"""
import os
import json
from typing import List, Dict, Optional, Any, Union
from src.utils.logger import logger

# Default preset storage location
def _get_presets_dir() -> str:
    """Get the directory for storing presets."""
    import sys
    try:
        # Frozen EXE
        base = os.path.dirname(sys.executable)
    except:
        base = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    
    presets_dir = os.path.join(base, "presets")
    os.makedirs(presets_dir, exist_ok=True)
    return presets_dir


# Built-in preset definitions
DEFAULT_PRESETS: Dict[str, Dict[str, Any]] = {
    "Karaoke Master": {
        "description": "Optimized for backing tracks with minimal vocal bleed",
        "stem_count": 2,
        "mode": "Instrumental",
        "quality": 2,  # Best
        "dereverb": True,
        "denoise": False,
        "format": "MP3",
        "sample_rate": 44100,
    },
    "Vocal Extract": {
        "description": "Ultra-clean acapella extraction",
        "stem_count": 2,
        "mode": "Vocals Only",
        "quality": 2,  # Best
        "dereverb": True,
        "denoise": True,
        "format": "WAV",
        "sample_rate": 44100,
    },
    "Full Stems (DJ)": {
        "description": "4-stem split for DJing and remixing",
        "stem_count": 4,
        "mode": "Standard",
        "quality": 1,  # Balanced
        "dereverb": False,
        "denoise": False,
        "format": "WAV",
        "sample_rate": 44100,
    },
    "Producer Pack": {
        "description": "Full 6-stem separation at highest quality",
        "stem_count": 6,
        "mode": "Standard",
        "quality": 2,  # Best
        "dereverb": False,
        "denoise": False,
        "format": "WAV",
        "sample_rate": 48000,
        "bit_depth": "24-bit",
    },
    "Quick Preview": {
        "description": "Fast separation for previewing",
        "stem_count": 2,
        "mode": "Standard",
        "quality": 0,  # Fast
        "dereverb": False,
        "denoise": False,
        "format": "MP3",
        "sample_rate": 44100,
    },
}


def get_preset_names() -> List[str]:
    """Get list of all available preset names (built-in + user)."""
    names = list(DEFAULT_PRESETS.keys())
    
    # Add user presets
    presets_dir = _get_presets_dir()
    for filename in os.listdir(presets_dir):
        if filename.endswith('.json'):
            name = filename[:-5]  # Remove .json
            if name not in names:
                names.append(name)
    
    return names


def load_preset(name: str) -> Optional[Dict[str, Any]]:
    """
    Load a preset by name.
    Returns dict of settings or None if not found.
    """
    # Check built-in first
    if name in DEFAULT_PRESETS:
        return DEFAULT_PRESETS[name].copy()
    
    # Check user presets
    preset_file = os.path.join(_get_presets_dir(), f"{name}.json")
    if os.path.exists(preset_file):
        try:
            with open(preset_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load preset {name}: {e}")
            return None
    
    return None


def save_preset(name: str, settings: Dict[str, Any]) -> bool:
    """
    Save a user preset.
    Returns True on success.
    """
    preset_file = os.path.join(_get_presets_dir(), f"{name}.json")
    try:
        with open(preset_file, 'w') as f:
            json.dump(settings, f, indent=2)
        logger.info(f"Saved preset: {name}")
        return True
    except Exception as e:
        logger.error(f"Failed to save preset {name}: {e}")
        return False


def delete_preset(name: str) -> bool:
    """
    Delete a user preset.
    Built-in presets cannot be deleted.
    """
    if name in DEFAULT_PRESETS:
        logger.warning(f"Cannot delete built-in preset: {name}")
        return False
    
    preset_file = os.path.join(_get_presets_dir(), f"{name}.json")
    if os.path.exists(preset_file):
        try:
            os.remove(preset_file)
            logger.info(f"Deleted preset: {name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete preset {name}: {e}")
            return False
    
    return False


def is_builtin(name: str) -> bool:
    """Check if a preset is built-in (not deletable)."""
    return name in DEFAULT_PRESETS
