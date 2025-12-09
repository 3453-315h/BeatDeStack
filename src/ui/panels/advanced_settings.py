from PyQt6.QtWidgets import (
    QGroupBox, QVBoxLayout, QHBoxLayout, QLabel, 
    QComboBox, QCheckBox, QPushButton, QSpinBox, QDoubleSpinBox
)
from PyQt6.QtCore import pyqtSignal


class AdvancedSettingsPanel(QGroupBox):
    """Panel for advanced separation settings."""
    
    ensemble_config_requested = pyqtSignal()
    
    def __init__(self, model_manager, parent=None):
        super().__init__("ADVANCED SETTINGS ▼", parent)
        self.model_manager = model_manager
        self.ensemble_models = []
        self.ensemble_algo = "Average (Mean)"
        
        self.setCheckable(True)
        self.setChecked(False)
        self.toggled.connect(self._on_toggle)
        self._setup_ui()
        # Start collapsed
        self.setMaximumHeight(30)
    
    def _setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(5)
        
        # Model Selection
        # Model Selection Row 1
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("Model:"))
        self.combo_model = QComboBox()
        self.combo_model.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContentsOnFirstShow)
        self.refresh_model_list()
        model_layout.addWidget(self.combo_model)
        
        self.btn_refresh_models = QPushButton("🔄")
        self.btn_refresh_models.setFixedWidth(30)
        self.btn_refresh_models.setToolTip("Refresh model list")
        self.btn_refresh_models.clicked.connect(self.refresh_model_list)
        model_layout.addWidget(self.btn_refresh_models)
        layout.addLayout(model_layout)
        
        # Model Selection Row 2 (Import)
        import_layout = QHBoxLayout()
        import_layout.addStretch()
        self.btn_import_model = QPushButton("Import Custom Model") # Expanded text since we have room
        self.btn_import_model.setToolTip("Import custom .pth/.onnx model")
        import_layout.addWidget(self.btn_import_model)
        layout.addLayout(import_layout)
        
        # Ensemble Mode
        ensemble_layout = QHBoxLayout()
        self.chk_ensemble = QCheckBox("Ensemble Mode")
        self.chk_ensemble.toggled.connect(self._toggle_ensemble)
        
        self.btn_ensemble_config = QPushButton("Configure")
        self.btn_ensemble_config.setEnabled(False)
        self.btn_ensemble_config.clicked.connect(lambda: self.ensemble_config_requested.emit())
        
        ensemble_layout.addWidget(self.chk_ensemble)
        ensemble_layout.addWidget(self.btn_ensemble_config)
        layout.addLayout(ensemble_layout)
        
        # Overlap
        overlap_layout = QHBoxLayout()
        overlap_layout.addWidget(QLabel("Overlap:"))
        self.spin_overlap = QDoubleSpinBox()
        self.spin_overlap.setRange(0.0, 0.99)
        self.spin_overlap.setSingleStep(0.05)
        self.spin_overlap.setValue(0.25)
        overlap_layout.addWidget(self.spin_overlap)
        layout.addLayout(overlap_layout)
        
        # Shifts
        shifts_layout = QHBoxLayout()
        shifts_layout.addWidget(QLabel("Shifts:"))
        self.spin_shifts = QSpinBox()
        self.spin_shifts.setRange(0, 10)
        self.spin_shifts.setValue(1)
        shifts_layout.addWidget(self.spin_shifts)
        layout.addLayout(shifts_layout)
        
        # Segment
        segment_layout = QHBoxLayout()
        segment_layout.addWidget(QLabel("Segment:"))
        self.spin_segment = QSpinBox()
        self.spin_segment.setRange(0, 600)
        self.spin_segment.setValue(0)
        segment_layout.addWidget(self.spin_segment)
        layout.addLayout(segment_layout)
        
        # Jobs
        jobs_layout = QHBoxLayout()
        jobs_layout.addWidget(QLabel("Jobs:"))
        self.spin_jobs = QSpinBox()
        self.spin_jobs.setRange(0, 16)
        self.spin_jobs.setValue(0)
        jobs_layout.addWidget(self.spin_jobs)
        layout.addLayout(jobs_layout)

        # Batch Size
        batch_layout = QHBoxLayout()
        batch_layout.addWidget(QLabel("Batch Size:"))
        self.spin_batch_size = QSpinBox()
        self.spin_batch_size.setRange(1, 64)
        self.spin_batch_size.setValue(1)
        self.spin_batch_size.setToolTip("Inference batch size. Higher = faster but more VRAM.")
        batch_layout.addWidget(self.spin_batch_size)
        layout.addLayout(batch_layout)

        # Normalization
        norm_layout = QHBoxLayout()
        norm_layout.addWidget(QLabel("Normalization:"))
        self.spin_norm = QDoubleSpinBox()
        self.spin_norm.setRange(0.1, 1.0)
        self.spin_norm.setSingleStep(0.1)
        self.spin_norm.setValue(0.9)
        self.spin_norm.setToolTip("Max peak normalization threshold.")
        norm_layout.addWidget(self.spin_norm)
        layout.addLayout(norm_layout)
        
        # Clip Mode
        clip_layout = QHBoxLayout()
        clip_layout.addWidget(QLabel("Clip Mode:"))
        self.combo_clip = QComboBox()
        self.combo_clip.addItems(["rescale", "clamp"])
        clip_layout.addWidget(self.combo_clip)
        layout.addLayout(clip_layout)
        
        self.setLayout(layout)
    
    def _on_toggle(self, checked):
        """Handle expand/collapse."""
        if checked:
            self.setTitle("ADVANCED SETTINGS ▲")
            self.setMaximumHeight(16777215)
        else:
            self.setTitle("ADVANCED SETTINGS ▼")
            self.setMaximumHeight(30)
    
    def _toggle_ensemble(self, checked):
        """Enable/disable ensemble controls."""
        self.combo_model.setEnabled(not checked)
        self.btn_ensemble_config.setEnabled(checked)
        if checked and not self.ensemble_models:
            self.ensemble_config_requested.emit()
    
    def refresh_model_list(self):
        """Refresh the model dropdown from model manager."""
        self.combo_model.clear()
        models = self.model_manager.get_all_models()
        self.combo_model.addItems(models)
    
    def set_ensemble_config(self, models, algo):
        """Set ensemble configuration from dialog."""
        self.ensemble_models = models
        self.ensemble_algo = algo
        self.chk_ensemble.setText(f"Ensemble ({len(models)} models)")
    
    def get_values(self):
        """Returns dict of advanced settings."""
        return {
            "model": self.combo_model.currentText(),
            "shifts": self.spin_shifts.value(),
            "overlap": self.spin_overlap.value(),
            "segment": self.spin_segment.value(),
            "jobs": self.spin_jobs.value(),
            "batch_size": self.spin_batch_size.value(),
            "normalization": self.spin_norm.value(),
            "clip_mode": self.combo_clip.currentText(),
            "ensemble_enabled": self.chk_ensemble.isChecked(),
            "ensemble_models": self.ensemble_models,
            "ensemble_algo": self.ensemble_algo
        }
