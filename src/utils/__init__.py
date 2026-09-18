"""
Utility modules for logging and system resources.
"""
from src.utils.logger import logger
from src.utils.resource_utils import get_ffmpeg_path, get_resource_path

__all__ = ["logger", "get_ffmpeg_path", "get_resource_path"]
