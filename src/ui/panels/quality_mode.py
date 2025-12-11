from PyQt6.QtWidgets import QGroupBox, QVBoxLayout, QSlider, QLabel
from PyQt6.QtCore import Qt
from src.ui.style import COLORS


class QualityModePanel(QGroupBox):
    """Panel for quality/speed mode selection."""
    
    def __init__(self, parent=None):
        super().__init__("QUALITY MODE", parent)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout()
        
        self.label_quality = QLabel("Balanced (GPU Auto)")
        self.label_quality.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_quality.setStyleSheet(f"color: {COLORS['secondary']}; font-weight: bold;")
        
        self.slider_quality = QSlider(Qt.Orientation.Horizontal)
        self.slider_quality.setRange(0, 2)
        self.slider_quality.setValue(1)  # Default to Balanced
        self.slider_quality.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.slider_quality.setTickInterval(1)
        self.slider_quality.valueChanged.connect(self._update_label)
        
        layout.addWidget(self.label_quality)
        layout.addWidget(self.slider_quality)
        self.setLayout(layout)
    
    def _update_label(self, value):
        labels = ["Fast (CPU)", "Balanced (GPU Auto)", "Best (Ensemble)"]
        self.label_quality.setText(labels[value])
    
    def get_quality(self):
        """Returns quality value (0=Fast, 1=Balanced, 2=Best)."""
        return self.slider_quality.value()
