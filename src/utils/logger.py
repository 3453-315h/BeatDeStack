import logging
import sys
import os

def setup_logger():
    logger = logging.getLogger("SunoSplitter")
    logger.setLevel(logging.DEBUG)
    
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    
    # File handler - writes to log file next to EXE or in project root
    try:
        if getattr(sys, 'frozen', False):
            # Running as EXE - log next to executable
            log_dir = os.path.dirname(sys.executable)
        else:
            # Running from source - log in project root
            log_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        log_file = os.path.join(log_dir, "beatdestack_debug.log")
        fh = logging.FileHandler(log_file, mode='w', encoding='utf-8')
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        logger.info(f"Debug log file: {log_file}")
    except Exception as e:
        logger.warning(f"Could not create log file: {e}")
    
    return logger

logger = setup_logger()
