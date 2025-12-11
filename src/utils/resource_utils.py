import os
import sys

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
