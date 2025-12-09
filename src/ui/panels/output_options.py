from PyQt6.QtWidgets import (
    QGroupBox, QVBoxLayout, QHBoxLayout, QLabel, 
    QComboBox, QCheckBox, QWidget
)


class OutputPanel(QGroupBox):
    """Panel for output format options."""
    
    def __init__(self, parent=None):
        super().__init__("OUTPUT", parent)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(8)
        
        # Format row
        fmt_layout = QHBoxLayout()
        fmt_layout.addWidget(QLabel("Format:"))
        self.combo_format = QComboBox()
        self.combo_format.setMinimumWidth(100)
        self.combo_format.addItems(["WAV", "FLAC", "MP3", "OGG", "AIFF"])
        self.combo_format.setCurrentText("MP3")
        self.combo_format.currentTextChanged.connect(self._toggle_format_options)
        fmt_layout.addWidget(self.combo_format)
        fmt_layout.addStretch()
        layout.addLayout(fmt_layout)
        
        # Sample Rate row
        rate_layout = QHBoxLayout()
        rate_layout.addWidget(QLabel("Sample Rate:"))
        self.combo_rate = QComboBox()
        self.combo_rate.setMinimumWidth(100)
        self.combo_rate.addItems(["44100", "48000", "88200", "96000"])
        self.combo_rate.setCurrentText("44100")
        rate_layout.addWidget(self.combo_rate)
        rate_layout.addStretch()
        layout.addLayout(rate_layout)
        
        # Bit Depth row (hidden for MP3/OGG)
        self.depth_container = QWidget()
        depth_layout = QHBoxLayout(self.depth_container)
        depth_layout.setContentsMargins(0, 0, 0, 0)
        depth_layout.addWidget(QLabel("Bit Depth:"))
        self.combo_depth = QComboBox()
        self.combo_depth.setMinimumWidth(100)
        self.combo_depth.addItems(["16-bit", "24-bit", "32-bit Float"])
        depth_layout.addWidget(self.combo_depth)
        depth_layout.addStretch()
        layout.addWidget(self.depth_container)
        
        # Output checkboxes
        self.chk_zip = QCheckBox("Export as ZIP")
        self.chk_keep = QCheckBox("Keep Original")
        self.chk_keep.setChecked(True)
        self.chk_auto_open = QCheckBox("Auto-open Folder")
        self.chk_auto_open.setChecked(True)
        
        layout.addWidget(self.chk_zip)
        self.chk_midi = QCheckBox("Export as MIDI")
        layout.addWidget(self.chk_midi)
        layout.addWidget(self.chk_keep)
        layout.addWidget(self.chk_auto_open)
        
        self.setLayout(layout)
        
        # Initial format state
        self._toggle_format_options("MP3")
    
    def _toggle_format_options(self, format_text):
        """Show/hide bit depth based on format."""
        if format_text in ["MP3", "OGG"]:
            self.depth_container.setEnabled(False)
            self.depth_container.setVisible(False)
        else:
            self.depth_container.setEnabled(True)
            self.depth_container.setVisible(True)
    
    def get_values(self):
        """Returns dict of output settings."""
        return {
            "format": self.combo_format.currentText(),
            "sample_rate": int(self.combo_rate.currentText()),
            "bit_depth": self.combo_depth.currentText(),
            "export_zip": self.chk_zip.isChecked(),
            "export_midi": self.chk_midi.isChecked(),
            "keep_original": self.chk_keep.isChecked()
        }
    
    def is_auto_open_enabled(self):
        """Returns whether auto-open folder is enabled."""
        return self.chk_auto_open.isChecked()
