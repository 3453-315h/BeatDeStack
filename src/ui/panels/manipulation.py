from PyQt6.QtWidgets import (
    QGroupBox, QVBoxLayout, QHBoxLayout, QLabel, 
    QSpinBox, QDoubleSpinBox, QCheckBox
)


class ManipulationPanel(QGroupBox):
    """Panel for audio manipulation controls (pitch, time stretch, bands)."""
    
    def __init__(self, parent=None):
        super().__init__("AUDIO MANIPULATION ▼", parent)
        self.setCheckable(True)
        self.setChecked(False)
        self.toggled.connect(self._on_toggle)
        self._setup_ui()
        # Start collapsed
        self.setMaximumHeight(30)
    
    def _setup_ui(self):
        layout = QVBoxLayout()
        
        # Pitch Shift
        pitch_layout = QHBoxLayout()
        pitch_layout = QHBoxLayout()
        pitch_layout.addWidget(QLabel("Pitch Shift (Semitones):"))
        pitch_layout.addStretch()
        self.spin_pitch = QSpinBox()
        self.spin_pitch.setRange(-12, 12)
        self.spin_pitch.setValue(0)
        self.spin_pitch.setFixedWidth(80)
        pitch_layout.addWidget(self.spin_pitch)
        layout.addLayout(pitch_layout)
        
        # Time Stretch
        time_layout = QHBoxLayout()
        time_layout = QHBoxLayout()
        time_layout.addWidget(QLabel("Time Stretch (Speed):"))
        time_layout.addStretch()
        self.spin_time = QDoubleSpinBox()
        self.spin_time.setRange(0.5, 2.0)
        self.spin_time.setSingleStep(0.1)
        self.spin_time.setValue(1.0)
        self.spin_time.setFixedWidth(80)
        time_layout.addWidget(self.spin_time)
        layout.addLayout(time_layout)
        
        # Spectral Tools
        self.chk_split_bands = QCheckBox("Split Bands (Low/Mid/High)")
        self.chk_split_bands.setToolTip("Generate separate Low, Mid, and High freq files for each stem")
        layout.addWidget(self.chk_split_bands)
        
        self.setLayout(layout)
    
    def _on_toggle(self, checked):
        """Handle expand/collapse."""
        if checked:
            self.setTitle("AUDIO MANIPULATION ▲")
            self.setMaximumHeight(16777215)
        else:
            self.setTitle("AUDIO MANIPULATION ▼")
            self.setMaximumHeight(30)
    
    def get_values(self):
        """Returns dict of manipulation settings."""
        return {
            "pitch_shift": self.spin_pitch.value(),
            "time_stretch": self.spin_time.value(),
            "split_bands": self.chk_split_bands.isChecked()
        }
