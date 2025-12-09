from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, 
    QListWidgetItem, QPushButton, QGroupBox, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
from src.ui.style import COLORS
import os


class ModelsView(QWidget):
    """View for browsing and managing installed AI models."""
    
    models_changed = pyqtSignal()  # Emitted when models are added/deleted
    
    def __init__(self, model_manager, parent=None):
        super().__init__(parent)
        self.model_manager = model_manager
        self._setup_ui()
        self.refresh_models()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Header
        header = QLabel("🧠 Installed Models")
        header.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {COLORS['text']};")
        layout.addWidget(header)
        
        desc = QLabel("Manage your Demucs and MDX-Net models")
        desc.setStyleSheet(f"color: {COLORS['text_dim']};")
        layout.addWidget(desc)
        
        # Models List
        self.model_list = QListWidget()
        self.model_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {COLORS['surface']};
                border: 1px solid rgba(255,255,255,0.1);
                border-radius: 8px;
                padding: 5px;
            }}
            QListWidget::item {{
                padding: 10px;
                border-radius: 4px;
                margin: 2px 0;
            }}
            QListWidget::item:selected {{
                background-color: rgba(0, 212, 255, 0.2);
            }}
        """)
        layout.addWidget(self.model_list, 1)
        
        # Info Box
        self.info_group = QGroupBox("Model Info")
        info_layout = QVBoxLayout()
        self.lbl_model_info = QLabel("Select a model to view details")
        self.lbl_model_info.setStyleSheet(f"color: {COLORS['text_dim']};")
        self.lbl_model_info.setWordWrap(True)
        info_layout.addWidget(self.lbl_model_info)
        self.info_group.setLayout(info_layout)
        layout.addWidget(self.info_group)
        
        # Actions
        actions_layout = QHBoxLayout()
        
        self.btn_refresh = QPushButton("🔄 Refresh")
        self.btn_refresh.clicked.connect(self.refresh_models)
        actions_layout.addWidget(self.btn_refresh)
        
        self.btn_download = QPushButton("⬇️ Download Models")
        self.btn_download.setStyleSheet(f"background-color: {COLORS['primary']}; color: #000;")
        self.btn_download.clicked.connect(self._open_download_dialog)
        actions_layout.addWidget(self.btn_download)
        
        self.btn_import = QPushButton("📥 Import Model")
        self.btn_import.clicked.connect(self._import_model)
        actions_layout.addWidget(self.btn_import)
        
        actions_layout.addStretch()
        
        self.btn_delete = QPushButton("🗑️ Delete")
        self.btn_delete.setStyleSheet(f"color: {COLORS['danger']};")
        self.btn_delete.clicked.connect(self._delete_model)
        self.btn_delete.setEnabled(False)
        actions_layout.addWidget(self.btn_delete)
        
        layout.addLayout(actions_layout)
        
        # Connect selection
        self.model_list.itemSelectionChanged.connect(self._on_selection_changed)
    
    def refresh_models(self):
        """Refresh the models list."""
        self.model_list.clear()
        
        # Get models from manager
        models = self.model_manager.get_all_models()
        default_models = self.model_manager.default_models
        
        for model_name in models:
            item = QListWidgetItem(model_name)
            
            # Determine model type from name
            if "htdemucs" in model_name.lower():
                item.setText(f"🎵 {model_name} (Demucs)")
            elif ".onnx" in model_name.lower():
                item.setText(f"🔮 {model_name} (MDX-Net)")
            elif ".pth" in model_name.lower():
                item.setText(f"📦 {model_name} (Custom)")
            else:
                item.setText(f"📁 {model_name}")
            
            # Grey out default models
            if model_name in default_models:
                item.setForeground(QColor(128, 128, 128))
            
            item.setData(Qt.ItemDataRole.UserRole, model_name)
            self.model_list.addItem(item)
        
        self.lbl_model_info.setText(f"Found {len(models)} models")
    
    def _on_selection_changed(self):
        """Handle model selection."""
        items = self.model_list.selectedItems()
        
        if items:
            model_name = items[0].data(Qt.ItemDataRole.UserRole)
            self._show_model_info(model_name)
            
            # Only allow deleting non-default models
            default_models = self.model_manager.default_models
            is_default = model_name in default_models
            self.btn_delete.setEnabled(not is_default)
            
            if is_default:
                self.btn_delete.setToolTip("Default models cannot be deleted")
            else:
                self.btn_delete.setToolTip("Delete this model")
        else:
            self.btn_delete.setEnabled(False)
    
    def _show_model_info(self, model_name):
        """Display detailed info about selected model."""
        # Comprehensive model descriptions
        MODEL_INFO = {
            # Default Demucs models
            "htdemucs": {
                "type": "Demucs v4 Hybrid Transformer",
                "desc": "Default 4-stem separation model. Separates audio into Vocals, Drums, Bass, and Other. Fast and reliable for general use.",
                "best_for": "Quick separation, everyday use",
                "stems": "Vocals, Drums, Bass, Other"
            },
            "htdemucs_ft": {
                "type": "Demucs v4 Fine-Tuned",
                "desc": "Fine-tuned version with improved vocal clarity. Best quality among default Demucs models. Recommended for serious work.",
                "best_for": "High-quality vocal extraction",
                "stems": "Vocals, Drums, Bass, Other"
            },
            "htdemucs_6s": {
                "type": "Demucs v4 Six-Stem",
                "desc": "Extended 6-stem model that also separates Guitar and Piano. Ideal for complex musical analysis and remixing.",
                "best_for": "Detailed instrument separation",
                "stems": "Vocals, Drums, Bass, Guitar, Piano, Other"
            },
            "mdx_extra": {
                "type": "MDX-Net Extra",
                "desc": "MDX architecture optimized for cleaner separation. Good balance of speed and quality.",
                "best_for": "General purpose, faster than Demucs",
                "stems": "Vocals, Instrumental"
            },
            # MDX-Net ONNX models
            "Kim_Vocal_2.onnx": {
                "type": "MDX-Net ONNX (Kim)",
                "desc": "Premium vocal extraction model by Kim. Excellent at isolating clean vocals with minimal artifacts. Community favorite.",
                "best_for": "Clean vocal extraction, acapellas",
                "quality": "High SDR score"
            },
            "Kim_Vocal_1.onnx": {
                "type": "MDX-Net ONNX (Kim)",
                "desc": "Original Kim vocal model. Slightly less refined than V2 but still excellent quality.",
                "best_for": "Vocal extraction",
                "quality": "Good SDR score"
            },
            "Kim_Inst.onnx": {
                "type": "MDX-Net ONNX (Kim)",
                "desc": "Kim's instrumental extraction model. Removes vocals to produce clean backing tracks.",
                "best_for": "Instrumental extraction, backing tracks",
                "quality": "High SDR score"
            },
            "UVR-MDX-NET-Voc_FT.onnx": {
                "type": "MDX-Net Fine-Tuned",
                "desc": "UVR's fine-tuned vocal model. Optimized for vocal clarity and reduced bleed from instruments.",
                "best_for": "Vocal isolation with minimal bleed",
                "quality": "Very High"
            },
            "UVR_MDXNET_KARA_2.onnx": {
                "type": "MDX-Net Karaoke",
                "desc": "Specialized for creating karaoke tracks. Removes vocals while preserving instrumental backing perfectly.",
                "best_for": "Karaoke creation, instrumental extraction",
                "quality": "Optimized for instrumentals"
            },
            "UVR_MDXNET_Main.onnx": {
                "type": "MDX-Net Main",
                "desc": "General-purpose MDX-Net model. Good all-around performance for vocal/instrumental separation.",
                "best_for": "General separation tasks",
                "quality": "Balanced"
            },
            "UVR-MDX-NET-Inst_HQ_1.onnx": {
                "type": "MDX-Net Instrumental HQ",
                "desc": "First version of the high-quality instrumental model. Clean vocal removal for backing tracks.",
                "best_for": "Instrumental extraction",
                "quality": "High"
            },
            "UVR-MDX-NET-Inst_HQ_3.onnx": {
                "type": "MDX-Net Instrumental HQ",
                "desc": "Third iteration with improved vocal removal. Produces cleaner instrumental tracks.",
                "best_for": "Clean instrumentals, backing tracks",
                "quality": "Very High"
            },
            "Reverb_HQ_By_FoxJoy.onnx": {
                "type": "MDX-Net Reverb Removal",
                "desc": "Removes room reverb and ambiance from audio. Makes recordings sound dry and close-mic'd.",
                "best_for": "Reverb removal, room noise reduction",
                "quality": "Specialized"
            },
            # VR Models (PTH)
            "UVR-DeEcho-DeReverb.pth": {
                "type": "VR Architecture v5 (FoxJoy)",
                "desc": "Combined echo and reverb removal. Cleans up recordings with unwanted room reflections and echo effects.",
                "best_for": "Cleaning recordings, podcast cleanup",
                "quality": "213 MB - comprehensive"
            },
            "UVR-DeNoise.pth": {
                "type": "VR Architecture v5 (FoxJoy)",
                "desc": "Advanced noise reduction. Removes background hiss, hum, and ambient noise while preserving audio quality.",
                "best_for": "Noise removal, audio cleanup",
                "quality": "121 MB - best denoiser"
            },
            "UVR-DeNoise-Lite.pth": {
                "type": "VR Architecture v5 (FoxJoy)",
                "desc": "Lighter version of DeNoise. Faster processing with good noise reduction for less demanding tasks.",
                "best_for": "Quick noise removal, lower resource usage",
                "quality": "17 MB - lightweight"
            },
            "UVR-De-Echo-Normal.pth": {
                "type": "VR Architecture v5 (FoxJoy)",
                "desc": "Normal-strength echo removal. Removes slapback and room echo without being too aggressive.",
                "best_for": "Echo removal, room treatment",
                "quality": "121 MB - balanced"
            },
            # MDX23C models
            "MDX23C-8KFFT-InstVoc_HQ.ckpt": {
                "type": "MDX23C (2023 Challenge)",
                "desc": "Winning model from Sound Demixing Challenge 2023. Uses 8K FFT for high-resolution separation with minimal artifacts.",
                "best_for": "Highest quality separation",
                "quality": "427 MB - state-of-the-art"
            },
            "MDX23C-8KFFT-InstVoc_HQ_2.ckpt": {
                "type": "MDX23C Version 2",
                "desc": "Improved second version of the MDX23C model. Even better separation quality and fewer artifacts.",
                "best_for": "Premium vocal/instrumental separation",
                "quality": "427 MB - enhanced"
            },
            "MDX23C-DrumSep-aufr33-jarredou.ckpt": {
                "type": "MDX23C Drum Separator",
                "desc": "Specialized drum separation model. Isolates drum tracks from full mixes with high precision.",
                "best_for": "Drum extraction, rhythm isolation",
                "quality": "417 MB - drum specialist"
            },
            # Roformer models
            "model_bs_roformer_ep_317_sdr_12.9755.ckpt": {
                "type": "BS-Roformer (Band-Split)",
                "desc": "State-of-the-art vocal isolation using Band-Split Roformer architecture. SDR 12.97 - best available quality for vocals.",
                "best_for": "Premium vocal extraction",
                "quality": "SDR 12.97 (Excellent)"
            },
            "vocals_mel_band_roformer.ckpt": {
                "type": "MelBand Roformer (Kimberley Jensen)",
                "desc": "High-quality MelBand Roformer for vocal extraction. Original weights by Kimberley Jensen.",
                "best_for": "Vocal extraction, high fidelity",
                "quality": "870 MB - premium"
            },
            "model_mel_band_roformer_ep_3005_sdr_11.4360.ckpt": {
                "type": "Mel-Roformer Viperx",
                "desc": "MelBand Roformer trained by Viperx. SDR 11.43 - excellent balance of quality and processing speed.",
                "best_for": "High-quality vocals, balanced processing",
                "quality": "SDR 11.43 (Very Good)"
            },
            "denoise_mel_band_roformer_aufr33_sdr_27.9959.ckpt": {
                "type": "Mel-Roformer Denoise (aufr33)",
                "desc": "Advanced AI-based denoising using MelBand Roformer. SDR 27.99 - exceptional noise reduction quality.",
                "best_for": "Premium noise removal, audio restoration",
                "quality": "SDR 27.99 (Outstanding)"
            },
            "deverb_bs_roformer_8_384dim_10depth.ckpt": {
                "type": "BS-Roformer De-Reverb",
                "desc": "Band-Split Roformer specifically trained for reverb removal. Removes room ambiance while preserving clarity.",
                "best_for": "Reverb removal, dry audio extraction",
                "quality": "345 MB - specialized"
            },
            "mel_band_roformer_karaoke_aufr33_viperx_sdr_10.1956.ckpt": {
                "type": "Mel-Roformer Karaoke",
                "desc": "MelBand Roformer optimized for karaoke creation. Removes vocals while preserving instrumentals perfectly.",
                "best_for": "Karaoke creation, instrumental extraction",
                "quality": "SDR 10.19 (Great for karaoke)"
            },
        }
        
        info_lines = [f"<b style='font-size: 14px;'>{model_name}</b>", ""]
        
        # Check for specific model info
        model_data = MODEL_INFO.get(model_name, None)
        
        if model_data:
            info_lines.append(f"<span style='color: #00D4FF;'>Type:</span> {model_data['type']}")
            info_lines.append("")
            info_lines.append(f"<span style='color: #FFD700;'>Description:</span><br>{model_data['desc']}")
            info_lines.append("")
            info_lines.append(f"<span style='color: #4ADE80;'>Best for:</span> {model_data['best_for']}")
            if 'stems' in model_data:
                info_lines.append(f"<span style='color: #FF6B6B;'>Stems:</span> {model_data['stems']}")
            if 'quality' in model_data:
                info_lines.append(f"<span style='color: #A78BFA;'>Quality:</span> {model_data['quality']}")
        else:
            # Fallback for unknown models
            if "htdemucs" in model_name.lower():
                info_lines.append("Type: <span style='color: #00D4FF'>Demucs v4</span>")
                info_lines.append("Multi-stem audio separation using Hybrid Transformer Demucs")
            elif ".onnx" in model_name.lower():
                info_lines.append("Type: <span style='color: #FF6B6B'>MDX-Net ONNX</span>")
                info_lines.append("Optimized neural network for fast inference")
            elif ".pth" in model_name.lower():
                info_lines.append("Type: <span style='color: #FFD700'>VR Architecture</span>")
                info_lines.append("PyTorch model for audio enhancement")
            elif ".ckpt" in model_name.lower():
                info_lines.append("Type: <span style='color: #4ADE80'>MDX23C/Roformer</span>")
                info_lines.append("Advanced checkpoint model for high-quality separation")
        
        # Try to get file size
        model_paths = self.model_manager.get_model_paths()
        for path in model_paths:
            full_path = os.path.join(path, model_name)
            if os.path.exists(full_path):
                size_mb = os.path.getsize(full_path) / (1024 * 1024)
                info_lines.append("")
                info_lines.append(f"<span style='color: #888;'>Size: {size_mb:.1f} MB</span>")
                break
        
        self.lbl_model_info.setText("<br>".join(info_lines))
    
    def _import_model(self):
        """Import a custom model."""
        from PyQt6.QtWidgets import QFileDialog
        files, _ = QFileDialog.getOpenFileNames(
            self, "Import Model", "", "Model Files (*.pth *.onnx *.yaml)"
        )
        if files:
            for f in files:
                self.model_manager.import_model(f)
            self.refresh_models()
            self.models_changed.emit()
    
    def _delete_model(self):
        """Delete selected model."""
        items = self.model_list.selectedItems()
        if not items:
            return
        
        model_name = items[0].data(Qt.ItemDataRole.UserRole)
        
        # Confirm
        reply = QMessageBox.question(
            self, "Delete Model",
            f"Are you sure you want to delete '{model_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if hasattr(self.model_manager, 'delete_model'):
                self.model_manager.delete_model(model_name)
            self.refresh_models()
            self.models_changed.emit()
    
    def _open_download_dialog(self):
        """Open the model download dialog."""
        from src.ui.model_download_dialog import ModelDownloadDialog
        dialog = ModelDownloadDialog(self)
        dialog.exec()
        self.refresh_models()
        self.models_changed.emit()
