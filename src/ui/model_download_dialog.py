from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QListWidget,
    QListWidgetItem, QPushButton, QProgressBar, QGroupBox, QComboBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from src.ui.style import COLORS
import os


# Available models organized by category
# Source: audio-separator - verified filenames from list_supported_model_files()
# NOTE: Default models (htdemucs, htdemucs_ft, htdemucs_6s, mdx_extra) are not listed
AVAILABLE_MODELS = {
    "MDX-Net Vocals": [
        ("Kim Vocal 2", "Best vocals extraction (67 MB)", "Kim_Vocal_2.onnx"),
        ("Kim Vocal 1", "Original Kim model (67 MB)", "Kim_Vocal_1.onnx"),
        ("UVR-MDX-NET Voc FT", "Vocal fine-tuned (67 MB)", "UVR-MDX-NET-Voc_FT.onnx"),
        ("UVR-MDX-NET Karaoke 2", "Best for karaoke (53 MB)", "UVR_MDXNET_KARA_2.onnx"),
        ("UVR-MDX-NET Main", "General purpose (67 MB)", "UVR_MDXNET_Main.onnx"),
    ],
    "MDX-Net Instrumental": [
        ("UVR-MDX-NET Inst HQ 3", "High quality instrumental (67 MB)", "UVR-MDX-NET-Inst_HQ_3.onnx"),
        ("UVR-MDX-NET Inst HQ 1", "Instrumental HQ variant (60 MB)", "UVR-MDX-NET-Inst_HQ_1.onnx"),
        ("Kim Inst", "Kim instrumental model (67 MB)", "Kim_Inst.onnx"),
        ("Reverb HQ By FoxJoy", "MDX reverb removal (67 MB)", "Reverb_HQ_By_FoxJoy.onnx"),
    ],
    "MDX23C (Higher Quality)": [
        ("MDX23C-InstVoc HQ", "Vocals/Inst separation (448 MB)", "MDX23C-8KFFT-InstVoc_HQ.ckpt"),
        ("MDX23C-InstVoc HQ 2", "Improved HQ model (448 MB)", "MDX23C-8KFFT-InstVoc_HQ_2.ckpt"),
        ("MDX23C DrumSep", "Drum separation (448 MB)", "MDX23C-DrumSep-aufr33-jarredou.ckpt"),
    ],
    "Enhancement (VR Models)": [
        ("UVR-DeEcho-DeReverb", "Remove echo/reverb (121 MB)", "UVR-DeEcho-DeReverb.pth"),
        ("UVR-DeNoise", "Remove background noise (121 MB)", "UVR-DeNoise.pth"),
        ("UVR-DeNoise-Lite", "Lighter denoise (224 MB)", "UVR-DeNoise-Lite.pth"),
        ("UVR-De-Echo-Normal", "Normal echo removal (127 MB)", "UVR-De-Echo-Normal.pth"),
    ],
    "Roformer Vocals (Best 2024)": [
        ("BS-Roformer-Viperx-1297", "Best vocals SDR 12.97 (639 MB)", "model_bs_roformer_ep_317_sdr_12.9755.ckpt"),
        ("MelBand Roformer Vocals", "Kimberley Jensen vocals (~900 MB)", "vocals_mel_band_roformer.ckpt"),
        ("Mel-Roformer-Viperx", "Mel-band high quality (~900 MB)", "model_mel_band_roformer_ep_3005_sdr_11.4360.ckpt"),
    ],
    "Roformer Enhancement": [
        ("Mel-Roformer Denoise", "Advanced denoising (~900 MB)", "denoise_mel_band_roformer_aufr33_sdr_27.9959.ckpt"),
        ("BS-Roformer De-Reverb", "Roformer reverb removal (~900 MB)", "deverb_bs_roformer_8_384dim_10depth.ckpt"),
        ("Mel-Roformer Karaoke", "Best karaoke (913 MB)", "mel_band_roformer_karaoke_aufr33_viperx_sdr_10.1956.ckpt"),
    ],
    "Demucs v4 (Legacy)": [
        ("htdemucs_ft", "Fine-tuned 4-stem (Quality variant)", "htdemucs_ft.yaml"),
        ("mdx_extra", "Demucs MDX (Legacy hybrid)", "mdx_extra.yaml"),
    ],
}


class DownloadThread(QThread):
    """Thread for downloading models."""
    progress = pyqtSignal(str, int)  # model_name, progress % (-1 = indeterminate)
    status = pyqtSignal(str)  # status message
    finished = pyqtSignal(str, bool, str)  # model_name, success, message
    
    def __init__(self, model_filename):
        super().__init__()
        self.model_filename = model_filename
    
    def run(self):
        try:
            from audio_separator.separator import Separator
            import shutil
            
            self.status.emit("Initializing...")
            self.progress.emit(self.model_filename, 5)
            
            # Determine model directory - use absolute path
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
            models_dir = os.path.join(project_root, "models")
            os.makedirs(models_dir, exist_ok=True)
            
            self.status.emit("Setting up separator...")
            self.progress.emit(self.model_filename, 10)
            
            # Create separator with project models dir
            separator = Separator(
                model_file_dir=models_dir,
                output_dir=models_dir,
            )
            
            # Show indeterminate progress during download
            self.status.emit(f"Downloading {self.model_filename}... (this may take a while)")
            self.progress.emit(self.model_filename, -1)  # -1 = indeterminate
            
            # Load model - this triggers download
            separator.load_model(model_filename=self.model_filename)
            
            self.status.emit("Finalizing...")
            self.progress.emit(self.model_filename, 90)
            
            # audio-separator may download to /tmp - copy to our models folder if needed
            temp_locations = [
                "/tmp/audio-separator-models",
                "C:/tmp/audio-separator-models",
                os.path.expanduser("~/.cache/audio-separator"),
            ]
            
            for temp_dir in temp_locations:
                if os.path.exists(temp_dir):
                    src = os.path.join(temp_dir, self.model_filename)
                    if os.path.exists(src):
                        dest = os.path.join(models_dir, self.model_filename)
                        if not os.path.exists(dest):
                            shutil.copy2(src, dest)
                        break
            
            self.progress.emit(self.model_filename, 100)
            self.finished.emit(self.model_filename, True, "✅ Downloaded successfully!")
            
        except Exception as e:
            error_msg = str(e)
            # Provide more helpful error messages
            if "not found in supported model files" in error_msg:
                error_msg = f"Model '{self.model_filename}' not found in audio-separator's model list"
            self.finished.emit(self.model_filename, False, error_msg)


class ModelDownloadDialog(QDialog):
    """Dialog for downloading AI models."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Download Models")
        self.setMinimumSize(600, 500)
        self.setStyleSheet(f"background-color: {COLORS['background']}; color: {COLORS['text']};")
        self.download_thread = None
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("📥 Download Models")
        header.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {COLORS['primary']};")
        layout.addWidget(header)
        
        desc = QLabel("Select models to download. They will be saved to your models folder.")
        desc.setStyleSheet(f"color: {COLORS['text_dim']};")
        layout.addWidget(desc)
        
        # Category selector
        cat_layout = QHBoxLayout()
        cat_layout.addWidget(QLabel("Category:"))
        self.combo_category = QComboBox()
        self.combo_category.addItems(list(AVAILABLE_MODELS.keys()))
        self.combo_category.currentTextChanged.connect(self._on_category_changed)
        cat_layout.addWidget(self.combo_category, 1)
        layout.addLayout(cat_layout)
        
        # Models list
        self.model_list = QListWidget()
        self.model_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {COLORS['surface']};
                border: 1px solid rgba(255,255,255,0.1);
                border-radius: 8px;
            }}
            QListWidget::item {{
                padding: 10px;
                border-radius: 4px;
                margin: 2px;
            }}
            QListWidget::item:selected {{
                background-color: rgba(0, 212, 255, 0.2);
            }}
        """)
        layout.addWidget(self.model_list, 1)
        
        # Progress
        self.progress_group = QGroupBox("Download Progress")
        progress_layout = QVBoxLayout()
        self.lbl_status = QLabel("Select a model and click Download")
        self.lbl_status.setStyleSheet(f"color: {COLORS['text_dim']};")
        progress_layout.addWidget(self.lbl_status)
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)
        self.progress_group.setLayout(progress_layout)
        layout.addWidget(self.progress_group)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        self.btn_download = QPushButton("⬇️ Download Selected")
        self.btn_download.setStyleSheet(f"background-color: {COLORS['primary']}; color: #000; padding: 10px;")
        self.btn_download.clicked.connect(self._start_download)
        btn_layout.addWidget(self.btn_download)
        
        btn_layout.addStretch()
        
        self.btn_close = QPushButton("Close")
        self.btn_close.clicked.connect(self.close)
        btn_layout.addWidget(self.btn_close)
        
        layout.addLayout(btn_layout)
        
        # Initial populate
        self._on_category_changed(self.combo_category.currentText())
    
    def _on_category_changed(self, category):
        """Populate model list for selected category."""
        self.model_list.clear()
        
        if category not in AVAILABLE_MODELS:
            return
        
        for display_name, description, filename in AVAILABLE_MODELS[category]:
            item = QListWidgetItem(f"{display_name}\n{description}")
            item.setData(Qt.ItemDataRole.UserRole, filename)
            self.model_list.addItem(item)
    
    def _start_download(self):
        """Start downloading selected model."""
        items = self.model_list.selectedItems()
        if not items:
            self.lbl_status.setText("Please select a model first")
            return
        
        if self.download_thread and self.download_thread.isRunning():
            self.lbl_status.setText("Download already in progress...")
            return
        
        model_filename = items[0].data(Qt.ItemDataRole.UserRole)
        self.lbl_status.setText(f"Starting download: {model_filename}")
        self.lbl_status.setStyleSheet(f"color: {COLORS['text_dim']};")
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.btn_download.setEnabled(False)
        
        self.download_thread = DownloadThread(model_filename)
        self.download_thread.progress.connect(self._on_progress)
        self.download_thread.status.connect(self._on_status)
        self.download_thread.finished.connect(self._on_download_finished)
        self.download_thread.start()
    
    def _on_status(self, message):
        """Update status label."""
        self.lbl_status.setText(message)
    
    def _on_progress(self, model_name, progress):
        """Update progress bar."""
        if progress < 0:
            # Indeterminate progress (busy indicator)
            self.progress_bar.setRange(0, 0)
        else:
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(progress)
    
    def _on_download_finished(self, model_name, success, message):
        """Handle download completion."""
        self.btn_download.setEnabled(True)
        
        if success:
            self.progress_bar.setValue(100)
            self.lbl_status.setText(f"✅ {model_name}: {message}")
            self.lbl_status.setStyleSheet(f"color: {COLORS['success']};")
        else:
            self.progress_bar.setValue(0)
            self.lbl_status.setText(f"❌ Failed: {message}")
            self.lbl_status.setStyleSheet(f"color: {COLORS['danger']};")
