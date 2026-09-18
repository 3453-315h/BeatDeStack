import logging
import logging.handlers
import sys
import os

def setup_logger():
    logger = logging.getLogger("BeatDeStack")
    logger.setLevel(logging.DEBUG)
    
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    
    # Rotating file handler — keeps up to 5MB × 3 backup files, appends across sessions
    try:
        if getattr(sys, 'frozen', False):
            # Running as EXE - log next to executable
            log_dir = os.path.dirname(sys.executable)
        else:
            # Running from source - log in project root
            log_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        log_file = os.path.join(log_dir, "beatdestack_debug.log")
        fh = logging.handlers.RotatingFileHandler(
            log_file,
            mode='a',
            maxBytes=5 * 1024 * 1024,  # 5MB per file
            backupCount=3,
            encoding='utf-8'
        )
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        logger.info(f"Debug log file: {log_file}")
    except Exception as e:
        logger.warning(f"Could not create log file: {e}")
    
    return logger

logger = setup_logger()
