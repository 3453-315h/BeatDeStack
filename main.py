import os
# Must be set before importing tensorflow/keras
os.environ["TF_USE_LEGACY_KERAS"] = "1"

import sys

# Fix for 'NoneType' object has no attribute 'write' in noconsole mode
class StreamRedirector:
    def write(self, text):
        pass
    def flush(self):
        pass

if sys.stdout is None:
    sys.stdout = StreamRedirector()
if sys.stderr is None:
    sys.stderr = StreamRedirector()

def _get_log_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def crash_handler(exctype, value, tb_obj):
    import traceback as tb
    import datetime
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    error_msg = "".join(tb.format_exception(exctype, value, tb_obj))
    
    try:
        log_dir = _get_log_dir()
        crash_log = os.path.join(log_dir, "CRASH_LOG.txt")
        with open(crash_log, "a", encoding="utf-8") as f:
            f.write(f"\n[{timestamp}] CRASH REPORT:\n")
            f.write(error_msg)
            f.write("-" * 50 + "\n")
    except Exception:
        pass
        
    sys.__excepthook__(exctype, value, tb_obj)
    sys.exit(1)

sys.excepthook = crash_handler

from PyQt6.QtWidgets import QApplication
from src.ui.main_window import MainWindow
from src.ui.splash import SplashScreen
from src.core import constants
import time

def run_worker(args):
    # args is a list of arguments passed after --worker
    try:
        import json
        config = json.loads(args[0])
        
        from src.core.splitter import separate_audio
        input_file = config['input_file']
        output_dir = config['output_dir']
        stem_count = config['stem_count']
        quality = config['quality']
        export_zip = config['export_zip']
        keep_original = config['keep_original']
        
        # Forward all remaining options dynamically
        extra_options = {
            k: v for k, v in config.items()
            if k not in ('input_file', 'output_dir', 'stem_count', 'quality', 'export_zip', 'keep_original')
        }
        
        separate_audio(
            input_file,
            output_dir,
            stem_count,
            quality,
            export_zip,
            keep_original,
            **extra_options
        )
    except Exception as e:
        print(f"WORKER ERROR: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    if "--worker" in sys.argv:
        # Worker mode
        idx = sys.argv.index("--worker")
        run_worker(sys.argv[idx+1:])
        return

    app = QApplication(sys.argv)
    app.setApplicationName("BeatDeStack")
    
    splash = SplashScreen()
    splash.show()
    splash.show_message("Initializing Core Systems...")
    app.processEvents()
    
    # Configure GPU memory limits for better performance (Performance Optimization #14)
    from src.core.gpu_utils import configure_gpu_memory
    configure_gpu_memory(constants.GPU_MEMORY_FRACTION)  # Use configured fraction of GPU memory
    
    splash.show_message("Loading AI Models...")
    app.processEvents()
    splash.show_message("Starting UI...")
    app.processEvents()
    
    window = MainWindow()
    window.show()
    splash.finish(window)
    
    sys.exit(app.exec())

if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()
    main()
