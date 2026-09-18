from PyQt6.QtWidgets import QGroupBox, QVBoxLayout, QRadioButton, QCheckBox
from PyQt6.QtCore import pyqtSignal
from src.core import constants


class StemOptionsPanel(QGroupBox):
    """Panel for selecting stem separation mode."""
    
    selection_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__("STEM OPTIONS ▲", parent)
        self.setCheckable(True)
        self.setChecked(True)
        self.toggled.connect(self._on_toggle)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout()
        
        self.radio_2stem = QRadioButton("2-Stem (Vocals / Instrumental)")
        self.radio_4stem = QRadioButton("4-Stem (Classic)")
        self.radio_6stem = QRadioButton("6-Stem (Full Band)")
        self.radio_lead_backing = QRadioButton("Lead && Backing Vocals (Split Voices)")
        self.radio_vocals = QRadioButton("Vocals Only (Ultra Clean)")
        self.radio_inst = QRadioButton("Instrumental / Karaoke")
        self.radio_drums = QRadioButton("Drums Only")
        self.radio_bass = QRadioButton("Bass Only")
        self.radio_guitar = QRadioButton("Guitar Only (Experimental)")
        self.radio_guitar.setStyleSheet("color: #ff4444;")
        self.radio_piano = QRadioButton("Piano Only (Experimental)")
        self.radio_piano.setStyleSheet("color: #ff4444;")
        
        # Default selection
        self.radio_2stem.setChecked(True)
        
        # Add to layout
        for radio in [self.radio_2stem, self.radio_4stem, self.radio_6stem,
                      self.radio_lead_backing, self.radio_vocals, self.radio_inst,
                      self.radio_drums, self.radio_bass, self.radio_guitar, self.radio_piano]:
            layout.addWidget(radio)
            radio.toggled.connect(lambda _: self.selection_changed.emit())
        
        self.chk_invert = QCheckBox("Invert")
        self.chk_invert.setToolTip("Create instrumental by subtracting vocals from mix")
        layout.addWidget(self.chk_invert)
        
        self.setLayout(layout)
    
    def _on_toggle(self, checked):
        """Handle expand/collapse."""
        if checked:
            self.setTitle("STEM OPTIONS ▲")
            self.setMaximumHeight(16777215)
        else:
            self.setTitle("STEM OPTIONS ▼")
            self.setMaximumHeight(30)
    
    def get_stem_config(self):
        """Returns (stem_count, mode) based on current selection."""
        if self.radio_6stem.isChecked():
            return 6, constants.MODE_STANDARD
        elif self.radio_2stem.isChecked():
            return 2, constants.MODE_STANDARD
        elif self.radio_lead_backing.isChecked():
            return 2, constants.MODE_LEAD_BACKING
        elif self.radio_vocals.isChecked():
            return 2, constants.MODE_VOCALS
        elif self.radio_inst.isChecked():
            return 2, constants.MODE_INSTRUMENTAL
        elif self.radio_drums.isChecked():
            return 4, constants.MODE_DRUMS
        elif self.radio_bass.isChecked():
            return 4, constants.MODE_BASS
        elif self.radio_guitar.isChecked():
            return 6, constants.MODE_GUITAR
        elif self.radio_piano.isChecked():
            return 6, constants.MODE_PIANO
        else:  # 4-stem
            return 4, constants.MODE_STANDARD
    
    def set_mode(self, mode, stem_count=None):
        """Sets the active mode radio button programmatically."""
        mode_str = str(mode).lower().replace(" ", "_")
        if "lead" in mode_str or "backing" in mode_str:
            self.radio_lead_backing.setChecked(True)
        elif "vocal" in mode_str and "only" in mode_str:
            self.radio_vocals.setChecked(True)
        elif "inst" in mode_str or "karaoke" in mode_str:
            self.radio_inst.setChecked(True)
        elif "drum" in mode_str:
            self.radio_drums.setChecked(True)
        elif "bass" in mode_str:
            self.radio_bass.setChecked(True)
        elif "guitar" in mode_str:
            self.radio_guitar.setChecked(True)
        elif "piano" in mode_str:
            self.radio_piano.setChecked(True)
        elif stem_count == 6 or "6" in mode_str:
            self.radio_6stem.setChecked(True)
        elif stem_count == 4 or "4" in mode_str:
            self.radio_4stem.setChecked(True)
        elif stem_count == 2 or "2" in mode_str:
            self.radio_2stem.setChecked(True)

    def get_values(self):
        """Returns dict of current values for preset saving."""
        count, mode = self.get_stem_config()
        return {
            "stem_count": count,
            "mode": mode,
            "invert": self.is_invert_enabled()
        }

    def is_invert_enabled(self):
        """Returns whether invert mode is enabled."""
        return self.chk_invert.isChecked()
