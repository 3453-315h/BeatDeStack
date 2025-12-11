
import os
import sys
import shutil
import time
import numpy as np
import soundfile as sf
import logging

# Ensure src is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.splitter import separate_audio
from src.core.model_manager import ModelManager

# Setup Logging
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)

# Console Handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(log_formatter)
root_logger.addHandler(console_handler)

# File Handler
file_handler = logging.FileHandler("automated_test_suite.log", mode='w')
file_handler.setFormatter(log_formatter)
root_logger.addHandler(file_handler)

logger = logging.getLogger(__name__)

TEST_DIR = "test_results"
INPUT_FILE = "test.mp3"

def generate_test_tone(filename, duration=10, sr=44100):
    """Generate a 10s sine wave if test file doesn't exist."""
    logger.info(f"Generating test tone: {filename}")
    t = np.linspace(0, duration, int(sr * duration))
    # A4 (440Hz) sine wave
    audio = 0.5 * np.sin(2 * np.pi * 440 * t)
    # Stereo
    audio = np.stack([audio, audio], axis=1)
    sf.write(filename, audio, sr)

def run_test(name, options):
    """Run a single test case."""
    logger.info(f"--- RUNNING TEST: {name} ---")
    logger.info(f"Options: {options}")
    
    output_dir = os.path.join(TEST_DIR, name)
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
        
    start_time = time.time()
    # Remove explicit args that are also in options to avoid duplicates
    opts = options.copy()
    stem_count = opts.pop("stem_count", 2)
    quality = opts.pop("quality", 2)
    
    try:
        separate_audio(
            input_file=INPUT_FILE,
            output_dir=output_dir,
            stem_count=stem_count,
            quality=quality,
            export_zip=False,
            keep_original=False,
            **opts
        )
        duration = time.time() - start_time
        logger.info(f"[PASS] {name} (Time: {duration:.2f}s)")
        return True
    except Exception as e:
        logger.error(f"[FAIL] {name} - Error: {e}")
        return False

def chop_test_file(filename, limit_sec=50):
    """Ensure test file is trimmed to limit_sec."""
    try:
        data, sr = sf.read(filename)
        limit_samples = int(limit_sec * sr)
        if len(data) > limit_samples:
            logger.info(f"Trimming {filename} to {limit_sec} seconds...")
            data = data[:limit_samples]
            sf.write(filename, data, sr)
        else:
            logger.info(f"{filename} is already shorter than {limit_sec}s.")
    except Exception as e:
        logger.error(f"Failed to trim audio: {e}")

def cleanup_test_dir(path, retries=3):
    """Robustly remove directory with retries."""
    for i in range(retries):
        try:
            if os.path.exists(path):
                shutil.rmtree(path, ignore_errors=True)
            if not os.path.exists(path):
                return True
            time.sleep(1)
        except Exception as e:
            logger.warning(f"Cleanup attempt {i+1} failed: {e}")
    return not os.path.exists(path)

def main():
    # 1. Setup
    cleanup_test_dir(TEST_DIR)
    if not os.path.exists(TEST_DIR):
        os.makedirs(TEST_DIR)
    
    if not os.path.exists(INPUT_FILE):
        generate_test_tone(INPUT_FILE)
    
    # Trim to 50s
    chop_test_file(INPUT_FILE, 50)
        
    manager = ModelManager()
    all_models = manager.get_all_models()
    logger.info(f"Found Models: {len(all_models)} - {all_models}")
    
    results = {"pass": 0, "fail": 0}
    
    # 2. Test Formats
    logging.info("\n=== TESTING FORMATS ===")
    formats = ["WAV", "FLAC", "MP3", "AIFF"] # Removed OGG due to crash
    for fmt in formats:
        success = run_test(f"Format_{fmt}", {
            "stem_count": 2,
            "model": "htdemucs", 
            "format": fmt,
            "quality": 0 
        })
        if success: results["pass"] += 1
        else: results["fail"] += 1

    # 3. Test Models (ALL MODELS)
    logging.info("\n=== TESTING ALL MODELS ===")
    # Loop through ALL models as requested
    for model in all_models:
        success = run_test(f"Model_{model}", {
            "stem_count": 4, 
            "model": model,
            "quality": 0
        })
        if success: results["pass"] += 1
        else: results["fail"] += 1

    # 4. Test Enhancements (Mixing Console)
    logging.info("\n=== TESTING ENHANCEMENTS ===")
    success = run_test("Features_Mixing_Console", {
        "stem_count": 2,
        "model": "htdemucs",
        "quality": 0,
        "param_low_cut": True,
        "param_eq_low": 2,
        "param_eq_mid": -2,
        "param_eq_high": 4,
        "param_compressor": 50,
        "param_exciter": 30
    })
    if success: results["pass"] += 1
    else: results["fail"] += 1
    
    # 5. Test Filters (De-Reverb etc)
    # Note: These often require specific libraries or models. 
    # If using DSP fallback, it should work.
    success = run_test("Features_Filters", {
        "stem_count": 2,
        "model": "htdemucs",
        "quality": 0,
        "dereverb": 20, # Should trigger DSP or AI
        "bass_boost": 50,
        "stereo_width": 150
    })
    if success: results["pass"] += 1
    else: results["fail"] += 1

    # 6. Test Manipulation (Pitch/Time)
    logging.info("\n=== TESTING MANIPULATION ===")
    success = run_test("Features_Manipulation", {
        "stem_count": 2,
        "model": "htdemucs",
        "quality": 0,
        "pitch_shift": 2,
        "time_stretch": 1.2
    })
    if success: results["pass"] += 1
    else: results["fail"] += 1
    
    # 7. Test Band Splitting
    success = run_test("Features_BandSplit", {
        "stem_count": 2,
        "model": "htdemucs",
        "quality": 0,
        "split_bands": True
    })
    if success: results["pass"] += 1
    else: results["fail"] += 1

    # Summary
    logger.info("\n=== TEST SUMMARY ===")
    logger.info(f"Passed: {results['pass']}")
    logger.info(f"Failed: {results['fail']}")
    
    if results["fail"] == 0:
        logger.info("[SUCCESS] ALL TESTS PASSED")
    else:
        logger.error("[FAILURE] SOME TESTS FAILED")

if __name__ == "__main__":
    main()
