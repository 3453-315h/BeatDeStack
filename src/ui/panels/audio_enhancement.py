from PyQt6.QtWidgets import QGroupBox, QVBoxLayout, QHBoxLayout, QSlider, QLabel, QCheckBox, QComboBox
from PyQt6.QtCore import Qt


class AudioEnhancementPanel(QGroupBox):
    """Panel for audio enhancement controls (de-reverb, de-echo, etc.)."""
    
    def __init__(self, parent=None):
        super().__init__("AUDIO ENHANCEMENT ▼", parent)
        self.setCheckable(True)
        self.setChecked(False)
        self.toggled.connect(self._on_toggle)
        self._setup_ui()
        # Start collapsed
        self.setMaximumHeight(30)
    
    def _setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(5)
        
        # --- Presets ---
        preset_layout = QHBoxLayout()
        preset_layout.addWidget(QLabel("Preset:"))
        self.combo_presets = QComboBox()
        self.combo_presets.addItems([
            "Custom", "Default (Reset)", "Vocal - Shine (Bright)", "Vocal - Warm (Tube)",
            "Drums - Punch", "Bass - Definition", "Master - Polish"
        ])
        self.combo_presets.setToolTip("Apply pre-configured settings")
        self.combo_presets.currentTextChanged.connect(self._apply_preset)
        preset_layout.addWidget(self.combo_presets)
        layout.addLayout(preset_layout)
        
        # Low Cut Filter
        self.chk_low_cut = QCheckBox("Low Cut Filter (80Hz)")
        self.chk_low_cut.setToolTip("Remove low frequency rumble/noise below 80Hz.")
        layout.addWidget(self.chk_low_cut)

        # De-Reverb
        self.slider_dereverb, self.label_dereverb = self._create_slider(
            layout, "De-Reverb:", 0, 100, 0, 
            tooltip="Reduce room reverberation (echo/hall effect).")
        
        # De-Echo
        self.slider_deecho, self.label_deecho = self._create_slider(
            layout, "De-Echo:", 0, 100, 0,
            tooltip="Remove distinctive slapback delay/echo.")
        
        # De-Noise
        self.slider_denoise, self.label_denoise = self._create_slider(
            layout, "De-Noise:", 0, 100, 0,
            tooltip="Reduce constant background noise (hiss, hum).")
        
        # Vocal Clarity
        self.slider_clarity, self.label_clarity = self._create_slider(
            layout, "Clarity:", 0, 100, 0,
            tooltip="Enhance vocal presence and detail.")
        
        # Ensemble
        self.slider_ensemble, self.label_ensemble = self._create_slider(
            layout, "Ensemble:", 0, 100, 0,
            tooltip="Blend standard separation with MDX vocals for cleaner results.")
        
        # Bass Boost
        self.slider_bass, self.label_bass = self._create_slider(
            layout, "Bass:", 0, 100, 0,
            tooltip="Boost low frequencies (DSP based).")

        # Compressor (Punch)
        self.slider_compressor, self.label_compressor = self._create_slider(
            layout, "Punch:", 0, 100, 0,
            tooltip="Dynamic compression (Consistent volume/Impact).")

        # Exciter (Warmth)
        self.slider_exciter, self.label_exciter = self._create_slider(
            layout, "Warmth:", 0, 100, 0,
            tooltip="Harmonic saturation (Analog feel).")
        
        # Stereo Width (100 = normal)
        self.slider_stereo, self.label_stereo = self._create_slider(
            layout, "Width:", 0, 200, 100, width=40,
            tooltip="Adjust stereo field: 0=Mono, 100=Normal, 200=Extra Wide.")
            
        layout.addWidget(QLabel("3-Band Equalizer"))
        
        # EQ - Low
        self.slider_eq_low, self.label_eq_low = self._create_eq_slider(
            layout, "Low:", -12, 12, 0, tooltip="Adjust low frequencies (Bass).")

        # EQ - Mid
        self.slider_eq_mid, self.label_eq_mid = self._create_eq_slider(
            layout, "Mid:", -12, 12, 0, tooltip="Adjust mid frequencies (Vocals/Body).")

        # EQ - High
        self.slider_eq_high, self.label_eq_high = self._create_eq_slider(
            layout, "High:", -12, 12, 0, tooltip="Adjust high frequencies (Air/Detail).")
        
        self.setLayout(layout)
        
    def _create_eq_slider(self, parent_layout, label_text, min_val, max_val, default, width=35, tooltip=None):
        """Helper to create EQ slider (-12dB to +12dB)."""
        row = QHBoxLayout()
        lbl = QLabel(label_text)
        if tooltip: lbl.setToolTip(tooltip)
        row.addWidget(lbl)
        
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(min_val, max_val)
        slider.setValue(default)
        if tooltip: slider.setToolTip(tooltip)
        
        label = QLabel(f"{default}dB")
        label.setFixedWidth(width)
        
        slider.valueChanged.connect(lambda v: label.setText(f"{v:+}dB" if v != 0 else "0dB"))
        
        row.addWidget(slider)
        row.addWidget(label)
        parent_layout.addLayout(row)
        
        return slider, label
    
    def _create_slider(self, parent_layout, label_text, min_val, max_val, default, width=35, tooltip=None):
        """Helper to create a labeled slider row."""
        row = QHBoxLayout()
        lbl = QLabel(label_text)
        if tooltip: lbl.setToolTip(tooltip)
        row.addWidget(lbl)
        
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(min_val, max_val)
        slider.setValue(default)
        if tooltip: slider.setToolTip(tooltip)
        
        label = QLabel(f"{default}%")
        label.setFixedWidth(width)
        
        slider.valueChanged.connect(lambda v: label.setText(f"{v}%"))
        
        row.addWidget(slider)
        row.addWidget(label)
        parent_layout.addLayout(row)
        
        return slider, label
    
    def _on_toggle(self, checked):
        """Handle expand/collapse."""
        if checked:
            self.setTitle("AUDIO ENHANCEMENT ▲")
            self.setMaximumHeight(16777215)
        else:
            self.setTitle("AUDIO ENHANCEMENT ▼")
            self.setMaximumHeight(30)
    
    def get_values(self):
        """Returns dict of all enhancement values."""
        return {
            "dereverb": self.slider_dereverb.value(),
            "deecho": self.slider_deecho.value(),
            "denoise": self.slider_denoise.value(),
            "clarity": self.slider_clarity.value(),
            "ensemble": self.slider_ensemble.value(),
            "bass_boost": self.slider_bass.value(),
            "compressor": self.slider_compressor.value(),
            "exciter": self.slider_exciter.value(),
            "stereo_width": self.slider_stereo.value(),
            "low_cut": self.chk_low_cut.isChecked(),
            "eq_low": self.slider_eq_low.value(),
            "eq_mid": self.slider_eq_mid.value(),
            "eq_high": self.slider_eq_high.value()
        }

    def _apply_preset(self, text):
        """Apply selected preset settings."""
        if text == "Custom":
            return
            
        settings = {
            "Default (Reset)":       {"dereverb": 0, "deecho": 0, "denoise": 0, "clarity": 0, "ensemble": 0, "bass": 0, "punch": 0, "warmth": 0, "width": 100, "low_cut": False, "eq": [0,0,0]},
            "Vocal - Shine (Bright)": {"dereverb": 20, "deecho": 0, "denoise": 10, "clarity": 40, "ensemble": 0, "bass": 0, "punch": 20, "warmth": 10, "width": 100, "low_cut": True, "eq": [-2, 1, 3]},
            "Vocal - Warm (Tube)":    {"dereverb": 10, "deecho": 0, "denoise": 0, "clarity": 20, "ensemble": 0, "bass": 0, "punch": 30, "warmth": 40, "width": 100, "low_cut": True, "eq": [1, 2, -1]},
            "Drums - Punch":          {"dereverb": 0, "deecho": 0, "denoise": 0, "clarity": 0, "ensemble": 0, "bass": 10, "punch": 60, "warmth": 20, "width": 100, "low_cut": False, "eq": [3, -2, 2]},
            "Bass - Definition":      {"dereverb": 0, "deecho": 0, "denoise": 0, "clarity": 0, "ensemble": 0, "bass": 20, "punch": 50, "warmth": 30, "width": 0, "low_cut": False, "eq": [4, 2, 0]},
            "Master - Polish":        {"dereverb": 0, "deecho": 0, "denoise": 0, "clarity": 10, "ensemble": 0, "bass": 5, "punch": 15, "warmth": 15, "width": 110, "low_cut": True, "eq": [1, 0, 1]},
        }
        
        s = settings.get(text)
        if not s: return
        
        # Block signals to prevent infinite recursion if we had two-way binding (which we don't, but good practice)
        # Also prevents setting "Custom" immediately
        self.combo_presets.blockSignals(True)
        
        self.slider_dereverb.setValue(s["dereverb"])
        self.slider_deecho.setValue(s["deecho"])
        self.slider_denoise.setValue(s["denoise"])
        self.slider_clarity.setValue(s["clarity"])
        self.slider_ensemble.setValue(s["ensemble"])
        self.slider_bass.setValue(s["bass"])
        self.slider_compressor.setValue(s["punch"])
        self.slider_exciter.setValue(s["warmth"])
        self.slider_stereo.setValue(s["width"])
        self.chk_low_cut.setChecked(s["low_cut"])
        self.slider_eq_low.setValue(s["eq"][0])
        self.slider_eq_mid.setValue(s["eq"][1])
        self.slider_eq_high.setValue(s["eq"][2])
        
        self.combo_presets.blockSignals(False)
        # Restore selection name (it might not change, but ensures checking logic correct)
        # If user touches a slider, we should probably set to "Custom"? 
        # For now, let's just leave it.

    # TODO: Connect all sliders to set combo to "Custom" if changed manually?
    # That requires connecting all valueChanged signals.
    # Let's do that for a polished feel.
