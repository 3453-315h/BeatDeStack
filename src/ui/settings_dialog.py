from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QLabel, QLineEdit, QPushButton, QCheckBox, QSpinBox,
    QComboBox, QFileDialog, QGroupBox, QFormLayout
)
from PyQt6.QtCore import Qt, QSettings, QTimer, pyqtSignal
from src.ui.style import COLORS
from src.utils.resource_utils import get_resource_path
from src.core.gpu_utils import get_gpu_info
import os


class ClickableLabel(QLabel):
    clicked = pyqtSignal()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

class SettingsDialog(QDialog):
    """Application settings dialog with tabbed interface."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumSize(500, 400)
        self.setStyleSheet(f"background-color: {COLORS['background']}; color: {COLORS['text']};")
        
        self.settings = QSettings("BeatDeStack", "eXtended")
        self._setup_ui()
        self._load_settings()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Tab Widget
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {COLORS['surface']};
                background-color: {COLORS['surface']};
                border-radius: 8px;
            }}
            QTabBar::tab {{
                background-color: {COLORS['background']};
                color: {COLORS['text_dim']};
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
            }}
            QTabBar::tab:selected {{
                background-color: {COLORS['surface']};
                color: {COLORS['primary']};
            }}
        """)
        
        # General Tab
        self.tabs.addTab(self._create_general_tab(), "General")
        
        # Performance Tab
        self.tabs.addTab(self._create_performance_tab(), "Performance")
        
        # Models Tab
        # Models Tab
        self.tabs.addTab(self._create_models_tab(), "Models")
        
        # About Tab
        self.tabs.addTab(self._create_about_tab(), "About")
        
        layout.addWidget(self.tabs)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)
        
        self.btn_save = QPushButton("Save")
        self.btn_save.setStyleSheet(f"background-color: {COLORS['primary']}; color: #000;")
        self.btn_save.clicked.connect(self._save_and_close)
        btn_layout.addWidget(self.btn_save)
        
        layout.addLayout(btn_layout)
    
    def _create_general_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Output Settings
        output_group = QGroupBox("Output")
        output_layout = QFormLayout()
        
        # Default output folder
        folder_layout = QHBoxLayout()
        self.txt_output_folder = QLineEdit()
        self.txt_output_folder.setPlaceholderText("Same as input file")
        self.txt_output_folder.setToolTip("Default destination for separated audio files. Leave empty to use input file location.")
        folder_layout.addWidget(self.txt_output_folder)
        
        btn_browse = QPushButton("Browse...")
        btn_browse.setToolTip("Browse for output folder")
        btn_browse.clicked.connect(self._browse_output_folder)
        folder_layout.addWidget(btn_browse)
        
        output_layout.addRow("Default Folder:", folder_layout)
        
        # Default Format
        self.combo_default_format = QComboBox()
        self.combo_default_format.addItems(["MP3", "WAV", "FLAC", "OGG", "AIFF"])
        self.combo_default_format.setToolTip("Default audio format for new operations.")
        output_layout.addRow("Default Format:", self.combo_default_format)
        
        # Filename Pattern
        self.combo_pattern = QComboBox()
        self.combo_pattern.addItems(["{stem}", "{track}_{stem}", "{stem}_{track}", "{track} ({stem})"])
        self.combo_pattern.setToolTip("Naming pattern for output files.\n{stem} = vocals/drums\n{track} = filename")
        output_layout.addRow("Filename Pattern:", self.combo_pattern)
        
        self.chk_auto_open = QCheckBox("Auto-open folder after processing")
        self.chk_auto_open.setChecked(True)
        self.chk_auto_open.setToolTip("Open the folder containing results immediately after processing.")
        output_layout.addRow("", self.chk_auto_open)
        
        self.chk_notification = QCheckBox("Play sound on completion")
        self.chk_notification.setChecked(True)
        self.chk_notification.setToolTip("Play a sound alert when processing finishes.")
        output_layout.addRow("", self.chk_notification)
        
        output_group.setLayout(output_layout)
        layout.addWidget(output_group)
        
        # UI Settings
        ui_group = QGroupBox("Interface")
        ui_layout = QFormLayout()
        
        self.chk_confirm_cancel = QCheckBox("Confirm before canceling active process")
        self.chk_confirm_cancel.setChecked(True)
        self.chk_confirm_cancel.setToolTip("Show confirmation dialog before stopping a running task.")
        ui_layout.addRow("", self.chk_confirm_cancel)
        
        ui_group.setLayout(ui_layout)
        layout.addWidget(ui_group)
        
        layout.addStretch()
        return tab
    
    def _create_performance_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # GPU Settings
        gpu_group = QGroupBox("GPU Acceleration")
        gpu_layout = QFormLayout()
        
        self.combo_device = QComboBox()
        self.combo_device.addItems(["Auto (Recommended)", "CUDA/ROCm", "DirectML", "CPU Only"])
        self.combo_device.setToolTip("Hardware device to use for AI inference. 'Auto' selects the best available GPU.")
        gpu_layout.addRow("Device:", self.combo_device)
        
        gpu_group.setLayout(gpu_layout)
        layout.addWidget(gpu_group)
        
        # Processing Settings
        proc_group = QGroupBox("Processing")
        proc_layout = QFormLayout()
        
        self.spin_threads = QSpinBox()
        self.spin_threads.setRange(0, 32)
        self.spin_threads.setValue(0)
        self.spin_threads.setSpecialValueText("Auto")
        self.spin_threads.setToolTip("Number of CPU threads for processing (0 = Auto).")
        proc_layout.addRow("Worker Threads:", self.spin_threads)
        
        self.spin_memory = QSpinBox()
        self.spin_memory.setRange(0, 64)
        self.spin_memory.setValue(0)
        self.spin_memory.setSuffix(" GB")
        self.spin_memory.setSpecialValueText("Auto")
        self.spin_memory.setSpecialValueText("Auto")
        self.spin_memory.setToolTip("Maximum RAM usage limit (0 = Unlimited). Lower this if you experience crashes.")
        proc_layout.addRow("Memory Limit:", self.spin_memory)
        
        self.spin_batch_size = QSpinBox()
        self.spin_batch_size.setRange(1, 64)
        self.spin_batch_size.setValue(1)
        self.spin_batch_size.setToolTip("Default batch size for new sessions. Higher values use more VRAM but may be faster.")
        proc_layout.addRow("Default Batch Size:", self.spin_batch_size)
        
        proc_group.setLayout(proc_layout)
        layout.addWidget(proc_group)
        
        layout.addStretch()
        return tab
    
    def _create_models_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Model Storage
        storage_group = QGroupBox("Model Storage")
        storage_layout = QFormLayout()
        
        folder_layout = QHBoxLayout()
        self.txt_models_folder = QLineEdit()
        self.txt_models_folder.setPlaceholderText("Default (models/)")
        self.txt_models_folder.setToolTip("Folder where AI models are stored.")
        folder_layout.addWidget(self.txt_models_folder)
        
        btn_browse = QPushButton("Browse...")
        btn_browse.setToolTip("Browse for models folder")
        btn_browse.clicked.connect(self._browse_models_folder)
        folder_layout.addWidget(btn_browse)
        
        storage_layout.addRow("Models Folder:", folder_layout)
        
        storage_group.setLayout(storage_layout)
        layout.addWidget(storage_group)
        
        # Model Options
        options_group = QGroupBox("Options")
        options_layout = QFormLayout()
        
        self.chk_auto_download = QCheckBox("Auto-download missing models")
        self.chk_auto_download.setChecked(True)
        self.chk_auto_download.setToolTip("Automatically download required models if not found locally.")
        options_layout.addRow("", self.chk_auto_download)
        
        self.chk_cache_models = QCheckBox("Keep models in memory between runs")
        self.chk_cache_models.setChecked(False)
        self.chk_cache_models.setToolTip("Keep models loaded in VRAM for faster subsequent runs. Disable if low on memory.")
        options_layout.addRow("", self.chk_cache_models)
        
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        
        layout.addStretch()
        return tab
    
    def _create_about_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setSpacing(20)
        
        # Header
        header_layout = QHBoxLayout()
        header_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Logo
        self.logo_label = ClickableLabel()
        self.logo_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.click_count = 0
        self.logo_label.clicked.connect(self._check_easter_egg)
        
        logo_path = get_resource_path(os.path.join("resources", "logo.png"))
        if os.path.exists(logo_path):
            from PyQt6.QtGui import QPixmap
            pixmap = QPixmap(logo_path).scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.logo_label.setPixmap(pixmap)
        header_layout.addWidget(self.logo_label)
        
        # Title & Version
        self.title_label = QLabel()
        
        # Determine Edition based on active GPU
        _, _, device_type = get_gpu_info()
        edition = "CPU Edition"
        if device_type == "cuda": edition = "NVIDIA CUDA Edition"
        elif device_type == "rocm": edition = "AMD ROCm Edition"
        elif device_type == "directml": edition = "DirectML Edition"
        elif device_type == "mps": edition = "Apple Silicon Edition"
        
        self.title_label.setText(
            f"""<div style='text-align: center;'>
                <h2 style='color: {COLORS['text']}; margin: 0;'>
                    Beat<span style='color: #FF4444;'>De</span>Stack e<span style='color: #FF4444;'>X</span>tended
                </h2>
                <p style='color: {COLORS['text_dim']}; margin: 5px 0 0 0;'>v3.0.0 ({edition})</p>
            </div>"""
        )
        self.title_label.setTextFormat(Qt.TextFormat.RichText)
        header_layout.addWidget(self.title_label)
        
        layout.addLayout(header_layout)
        
        # Description
        desc_label = QLabel(
            "The Ultimate Offline AI Stem Separation & Audio Enhancement Tool.\n"
            "Powered by state-of-the-art models for studio-quality results."
        )
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setStyleSheet(f"color: {COLORS['text']}; font-style: italic;")
        layout.addWidget(desc_label)

        # Homepage Link
        link_label = QLabel(
            '<a href="https://github.com/3453-315h/BeatDeStackExtended" style="color: #00E5FF; text-decoration: none;">'
            'Visit Homepage on GitHub</a>'
        )
        link_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        link_label.setOpenExternalLinks(True)
        link_label.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(link_label)
        
        # Credits
        credits_group = QGroupBox("Credits & Acknowledgements")
        credits_layout = QVBoxLayout()
        credits_label = QLabel(
            """
            <b>StemLab</b> - Project Foundation<br>
            <b>Spotify Basic Pitch</b> - Audio-to-MIDI Conversion<br>
            <b>Anjok07</b> - Ultimate Vocal Remover (UVR)<br>
            <b>Meta Research</b> - Demucs Architecture<br>
            <b>KimberleyJensen</b> - Vocal Models<br>
            <b>FoxJoy</b> - Reverb & Echo Models<br>
            <b>Aufr33 & Jarredou</b> - MDX-Net Training
            """
        )
        credits_label.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 11px; line-height: 1.4;")
        credits_label.setTextFormat(Qt.TextFormat.RichText)
        credits_layout.addWidget(credits_label)
        credits_group.setLayout(credits_layout)
        layout.addWidget(credits_group)
        
        # Legal / Footer
        footer_label = QLabel("© 2025 BeatDeStack Project. Open Source Software.")
        footer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer_label.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 10px; margin-top: 10px;")
        layout.addWidget(footer_label)
        
        layout.addStretch()
        return tab
        
    def _check_easter_egg(self):
        """Hidden feature trigger."""
        self.click_count += 1
        if self.click_count == 5:
            # Activate Nyan Mode
            
            # Setup Flying Cat
            if not hasattr(self, 'nyan_cat'):
                 self.nyan_cat = QLabel(self)
                 path = get_resource_path(os.path.join("resources", "nyan_v2.png"))
                 if os.path.exists(path):
                     from PyQt6.QtGui import QPixmap
                     pix = QPixmap(path) # Native size is 136x96
                     self.nyan_cat.setPixmap(pix)
                     self.nyan_cat.resize(136, 96)
                     self.nyan_cat.show()
            
            self.nyan_x = -100
            self.nyan_cat.move(self.nyan_x, 50) # Start height
            self.nyan_cat.raise_()
            self.nyan_cat.show()
            
            self.timer = QTimer(self)
            self.timer.timeout.connect(self._animate_nyan)
            self.timer.start(20) # 50 FPS
            
            # Update Title
            self.title_label.setText(
                f"""<div style='text-align: center;'>
                    <h2 style='color: #FF69B4; margin: 0; text-shadow: 2px 2px #00FFFF;'>
                        BeatDeStack: NYAN MODE
                    </h2>
                    <p style='color: {COLORS['text_dim']}; margin: 5px 0 0 0;'>Flying through the code...</p>
                </div>"""
            )

    def _animate_nyan(self):
        """Fly the cat."""
        self.nyan_x += 5
        
        # Wavy motion
        import math
        y = 50 + int(math.sin(self.nyan_x * 0.05) * 20)
        
        self.nyan_cat.move(self.nyan_x, y)
        
        if self.nyan_x > self.width():
            self.nyan_x = -100 # Loop


    def _browse_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if folder:
            self.txt_output_folder.setText(folder)
    
    def _browse_models_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Models Folder")
        if folder:
            self.txt_models_folder.setText(folder)
    
    def _load_settings(self):
        """Load settings from QSettings."""
        self.txt_output_folder.setText(self.settings.value("output/folder", ""))
        self.combo_default_format.setCurrentText(self.settings.value("output/default_format", "MP3"))
        self.combo_pattern.setCurrentText(self.settings.value("output/filename_pattern", "{stem}"))
        self.chk_auto_open.setChecked(self.settings.value("output/auto_open", True, type=bool))
        self.chk_notification.setChecked(self.settings.value("output/notification", True, type=bool))
        self.chk_confirm_cancel.setChecked(self.settings.value("ui/confirm_cancel", True, type=bool))
        
        self.combo_device.setCurrentIndex(self.settings.value("performance/device", 0, type=int))
        self.spin_threads.setValue(self.settings.value("performance/threads", 0, type=int))
        self.spin_memory.setValue(self.settings.value("performance/memory", 0, type=int))
        self.spin_batch_size.setValue(self.settings.value("performance/batch_size", 1, type=int))
        
        self.txt_models_folder.setText(self.settings.value("models/folder", ""))
        self.chk_auto_download.setChecked(self.settings.value("models/auto_download", True, type=bool))
        self.chk_cache_models.setChecked(self.settings.value("models/cache", False, type=bool))
    
    def _save_and_close(self):
        """Save settings and close dialog."""
        self.settings.setValue("output/folder", self.txt_output_folder.text())
        self.settings.setValue("output/default_format", self.combo_default_format.currentText())
        self.settings.setValue("output/filename_pattern", self.combo_pattern.currentText())
        self.settings.setValue("output/auto_open", self.chk_auto_open.isChecked())
        self.settings.setValue("output/notification", self.chk_notification.isChecked())
        self.settings.setValue("ui/confirm_cancel", self.chk_confirm_cancel.isChecked())
        
        self.settings.setValue("performance/device", self.combo_device.currentIndex())
        self.settings.setValue("performance/threads", self.spin_threads.value())
        self.settings.setValue("performance/memory", self.spin_memory.value())
        self.settings.setValue("performance/batch_size", self.spin_batch_size.value())
        
        self.settings.setValue("models/folder", self.txt_models_folder.text())
        self.settings.setValue("models/auto_download", self.chk_auto_download.isChecked())
        self.settings.setValue("models/cache", self.chk_cache_models.isChecked())
        
        self.accept()
    
    def get_setting(self, key, default=None, type=str):
        """Get a setting value."""
        return self.settings.value(key, default, type=type)
