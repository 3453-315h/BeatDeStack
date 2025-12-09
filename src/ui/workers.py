from PyQt6.QtCore import QThread, pyqtSignal
from src.core.midi_converter import MidiConverter
from src.utils.logger import logger

class MidiExportWorker(QThread):
    finished = pyqtSignal(str) # Emits the path of the EACH created file
    all_completed = pyqtSignal()
    error = pyqtSignal(str)
    
    def __init__(self, audio_paths):
        super().__init__()
        if isinstance(audio_paths, str):
            self.audio_paths = [audio_paths]
        else:
            self.audio_paths = audio_paths
        self.converter = MidiConverter()

    def run(self):
        for path in self.audio_paths:
            try:
                output_path = self.converter.convert_to_midi(path)
                if output_path:
                    self.finished.emit(output_path)
                else:
                    self.error.emit(f"Failed to generate MIDI for {os.path.basename(path)}")
            except Exception as e:
                self.error.emit(f"Error {os.path.basename(path)}: {str(e)}")
        
        self.all_completed.emit()
