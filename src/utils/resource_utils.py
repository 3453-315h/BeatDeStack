import os
import sys
import shutil

def get_resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # In dev, use the current working directory or referencing from this file
        # relative_path is expected to be like "resources/icons/home.svg"
        # We assume the app is run from project root, so "resources" is at root.
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


def get_ffmpeg_path():
    """
    Get path to FFmpeg executable.
    
    Priority:
    1. Bundled in PyInstaller EXE (sys._MEIPASS/bin/ffmpeg.exe)
    2. Bundled in dev mode (project_root/bin/ffmpeg.exe)
    3. System PATH (shutil.which)
    4. Fallback to "ffmpeg" (hope it's in PATH)
    """
    # Check for bundled ffmpeg
    try:
        # Frozen EXE mode: look in sys._MEIPASS/bin/
        bundled = os.path.join(sys._MEIPASS, "bin", "ffmpeg.exe")
        if os.path.exists(bundled):
            return bundled
    except AttributeError:
        # Dev mode: look relative to working directory
        bundled = os.path.join(os.path.abspath("."), "bin", "ffmpeg.exe")
        if os.path.exists(bundled):
            return bundled
    
    # Fallback to system PATH
    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return system_ffmpeg
    
    # Last resort - hope it's accessible
    return "ffmpeg"
