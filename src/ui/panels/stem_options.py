from PyQt6.QtWidgets import QGroupBox, QVBoxLayout, QRadioButton, QCheckBox
from PyQt6.QtCore import pyqtSignal


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
        self.radio_vocals = QRadioButton("Vocals Only (Ultra Clean)")
        self.radio_inst = QRadioButton("Instrumental / Karaoke")
        self.radio_drums = QRadioButton("Drums Only")
        self.radio_bass = QRadioButton("Bass Only")
        self.radio_guitar = QRadioButton("Guitar Only (6-Stem)")
        self.radio_piano = QRadioButton("Piano Only (6-Stem)")
        
        # Default selection
        self.radio_2stem.setChecked(True)
        
        # Add to layout
        for radio in [self.radio_2stem, self.radio_4stem, self.radio_6stem,
                      self.radio_vocals, self.radio_inst, self.radio_drums,
                      self.radio_bass, self.radio_guitar, self.radio_piano]:
            layout.addWidget(radio)
            radio.toggled.connect(lambda _: self.selection_changed.emit())
        
        self.chk_invert = QCheckBox("Invert (Spectral Subtraction)")
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
            return 6, "standard"
        elif self.radio_2stem.isChecked():
            return 2, "standard"
        elif self.radio_vocals.isChecked():
            return 2, "vocals_only"
        elif self.radio_inst.isChecked():
            return 2, "instrumental"
        elif self.radio_drums.isChecked():
            return 4, "drums_only"
        elif self.radio_bass.isChecked():
            return 4, "bass_only"
        elif self.radio_guitar.isChecked():
            return 6, "guitar_only"
        elif self.radio_piano.isChecked():
            return 6, "piano_only"
        else:  # 4-stem
            return 4, "standard"
    
    def is_invert_enabled(self):
        """Returns whether invert mode is enabled."""
        return self.chk_invert.isChecked()
