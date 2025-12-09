import os
import soundfile as sf
import math
from src.utils.logger import logger

def create_preview_slice(input_path, output_path, duration=30.0):
    """
    Extracts a slice of audio from the middle of the track.
    
    Args:
        input_path (str): Path to source audio.
        output_path (str): Path to save the slice.
        duration (float): Duration in seconds.
        
    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        # Get info
        info = sf.info(input_path)
        sr = info.samplerate
        total_frames = info.frames
        total_duration = total_frames / sr
        
        # Determine start point (Middle)
        # If song is shorter than duration, use whole song
        if total_duration <= duration:
            start_frame = 0
            frames_to_read = total_frames
        else:
            mid_point = total_duration / 2
            start_time = max(0, mid_point - (duration / 2))
            start_frame = int(start_time * sr)
            frames_to_read = int(duration * sr)
            
        # Read and Write
        # sf.read handles seeking efficiently
        data, samplerate = sf.read(input_path, start=start_frame, stop=start_frame + frames_to_read)
        
        # Save
        sf.write(output_path, data, samplerate)
        logger.info(f"Created preview slice: {output_path} ({duration}s from {start_frame/sr:.2f}s)")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create preview slice: {e}")
        return False
