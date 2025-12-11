import os
import sys
import platform
import subprocess
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QListWidget, QListWidgetItem, QFileDialog,
    QLabel, QDialog, QTextEdit, QScrollArea, QFrame, QDockWidget
)
from PyQt6.QtCore import Qt, QObject, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtMultimedia import QMediaPlayer
from PyQt6.QtCore import QSize
from .style import COLORS, apply_theme
from .widgets import DragDropWidget, QueueItemWidget, VisualizerWidget
from .panels import (
    StemOptionsPanel, AudioEnhancementPanel, QualityModePanel,
    ManipulationPanel, OutputPanel, AdvancedSettingsPanel
)
from src.core.splitter import SplitterWorker
from src.core.gpu_utils import get_gpu_info
from src.core.model_manager import ModelManager
from src.ui.player import StemPlayerWidget
from src.utils.resource_utils import get_resource_path


# Cross-platform helper functions
def open_folder_cross_platform(path):
    """Open a folder in the system file manager (cross-platform)"""
    if platform.system() == "Windows":
        os.startfile(path)
    elif platform.system() == "Darwin":  # macOS
        subprocess.run(["open", path])
    else:  # Linux and other Unix-like
        subprocess.run(["xdg-open", path])


def play_notification_sound():
    """Play a notification sound (cross-platform, fails silently)"""
    try:
        if platform.system() == "Windows":
            import winsound
            winsound.MessageBeep(winsound.MB_OK)
        elif platform.system() == "Darwin":  # macOS
            subprocess.run(["afplay", "/System/Library/Sounds/Glass.aiff"], 
                          capture_output=True)
        # Linux: No universal notification sound, skip silently
    except Exception:
        pass  # Fail silently on any platform


class LogWindow(QDialog):
    """Log viewer dialog."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Process Logs")
        self.resize(600, 400)
        layout = QVBoxLayout(self)
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setStyleSheet(
            f"background-color: {COLORS['background']}; color: {COLORS['text']}; "
            "font-family: Consolas, monospace;"
        )
        layout.addWidget(self.text_edit)


class LogEmitter(QObject):
    text_written = pyqtSignal(str)


class StreamRedirector:
    def __init__(self, emitter):
        self.emitter = emitter
    def write(self, text):
        self.emitter.text_written.emit(text)
    def flush(self):
        pass


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BeatDeStack eXtended v3.7.0")
        self.resize(1280, 850)
        
        self.model_manager = ModelManager()
        
        # Set window icon
        icon_path = get_resource_path(os.path.join("resources", "icon.png"))
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # Setup Logging
        self.log_emitter = LogEmitter()
        self.log_emitter.text_written.connect(self.append_log)
        # Disable log redirection to prevent startup crashes
        # sys.stdout = StreamRedirector(self.log_emitter)
        # sys.stderr = StreamRedirector(self.log_emitter)
        
        self.log_window = LogWindow(self)
        
        # Central Widget
        central = QWidget()
        self.setCentralWidget(central)
        
        # Wrapper Layout
        wrapper = QVBoxLayout(central)
        wrapper.setSpacing(0)
        wrapper.setContentsMargins(0, 0, 0, 0)
        
        # Main Layout (HBox for Sidebar + Content + Right)
        self.main_layout = QHBoxLayout()
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        wrapper.addLayout(self.main_layout)
        
        apply_theme(self)
        self.setup_ui()
        
        # Player
        self.player_widget = StemPlayerWidget()
        wrapper.addWidget(self.player_widget)
        
        # Player Signals (Sync visualizer if possible, for now just placeholder)
        self.player_widget.btn_play.clicked.connect(
            lambda: self.update_visualizer_state()
        )

    def setup_ui(self):
        # --- Dashboard Layout ---
        # 1. Sidebar (Nav)
        # 2. Center (Queue/Viz)
        # 3. Right (Controls)

        # 1. Left Sidebar
        self._setup_sidebar()
        
        # 2. Center Work Area
        self._setup_center_panel()
        
        # 3. Right Control Panel
        self._setup_right_panel()
        
        # Initial GPU check
        self._update_gpu_status()

    def _setup_sidebar(self):
        """Create navigation sidebar."""
        sidebar = QFrame()
        sidebar.setFixedWidth(45)
        sidebar.setObjectName("sidebar")
        sidebar.setStyleSheet(
            "#sidebar { background-color: rgba(26, 26, 26, 0.6); border-right: 1px solid #000000; }"
        )
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(5, 20, 5, 20)
        sidebar_layout.setSpacing(15)

        # Store button references for highlighting
        self.sidebar_buttons = []
        
        self.btn_home = QPushButton()
        self.btn_home.setToolTip("Home (Ctrl+1)")
        self.btn_home.setFixedSize(35, 35)
        self.btn_home.setIcon(QIcon(get_resource_path(os.path.join("resources", "icons", "home.svg"))))
        self.btn_home.setIconSize(QSize(20, 20))
        self.btn_home.clicked.connect(lambda: self._switch_view(0))
        
        self.btn_models = QPushButton()
        self.btn_models.setToolTip("Models (Ctrl+2)")
        self.btn_models.setFixedSize(35, 35)
        self.btn_models.setIcon(QIcon(get_resource_path(os.path.join("resources", "icons", "models.svg"))))
        self.btn_models.setIconSize(QSize(20, 20))
        self.btn_models.clicked.connect(lambda: self._switch_view(1))
        
        self.btn_batch = QPushButton()
        self.btn_batch.setToolTip("Batch Processing")
        self.btn_batch.setFixedSize(35, 35)
        self.btn_batch.setIcon(QIcon(get_resource_path(os.path.join("resources", "icons", "batch.svg"))))
        self.btn_batch.setIconSize(QSize(20, 20))
        self.btn_batch.clicked.connect(self._show_batch_placeholder)
        
        self.btn_settings = QPushButton()
        self.btn_settings.setToolTip("Settings (Ctrl+,)")
        self.btn_settings.setFixedSize(35, 35)
        self.btn_settings.setIcon(QIcon(get_resource_path(os.path.join("resources", "icons", "settings.svg"))))
        self.btn_settings.setIconSize(QSize(20, 20))
        self.btn_settings.clicked.connect(self._open_settings)
        
        # Style and add buttons
        for btn in [self.btn_home, self.btn_models, self.btn_batch]:
            btn.setStyleSheet("background-color: transparent; border-radius: 8px;")
            self.sidebar_buttons.append(btn)
        self.btn_settings.setStyleSheet("background-color: transparent; border-radius: 8px;")
        
        # Highlight home by default
        self._highlight_sidebar_button(0)
        
        sidebar_layout.addWidget(self.btn_home)
        sidebar_layout.addWidget(self.btn_models)
        sidebar_layout.addWidget(self.btn_batch)
        sidebar_layout.addStretch()
        sidebar_layout.addWidget(self.btn_settings)
        
        self.main_layout.addWidget(sidebar)
        
        # Setup keyboard shortcuts
        self._setup_shortcuts()

    def _setup_center_panel(self):
        """Create center work area with queue and visualizer."""
        center_panel = QWidget()
        center_layout = QVBoxLayout(center_panel)
        center_layout.setContentsMargins(10, 20, 10, 20)
        center_layout.setSpacing(10)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel()
        title = QLabel()
        logo_path = get_resource_path(os.path.join("resources", "logo.png")).replace("\\", "/")
        
        title.setText(
            f'<img src="{logo_path}" width="32" height="32" style="vertical-align: middle;"> '
            'Beat<span style="color: #FF4444;">De</span>Stack e<span style="color: #FF4444;">X</span>tended'
        )
        title.setTextFormat(Qt.TextFormat.RichText)
        title.setStyleSheet(
            f"font-size: 24px; font-weight: 700; color: {COLORS['text']}; margin-left: 0px;"
        )
        header_layout.addWidget(title)
        
        # GPU Status
        self.gpu_label = QLabel("Checking GPU...")
        self.gpu_label.setStyleSheet(
            f"background-color: {COLORS['surface']}; color: {COLORS['text_dim']}; "
            "padding: 4px 12px; border-radius: 12px; font-size: 11px;"
        )
        header_layout.addStretch()
        header_layout.addWidget(self.gpu_label)
        
        center_layout.addLayout(header_layout)
        
        # Visualizer
        self.visualizer = VisualizerWidget()
        center_layout.addWidget(self.visualizer)
        
        # Drag Drop
        self.drag_drop = DragDropWidget()
        self.drag_drop.setFixedHeight(120)
        self.drag_drop.files_dropped.connect(self.add_files_to_queue)
        center_layout.addWidget(self.drag_drop)
        
        # Queue List
        queue_label = QLabel("Processing Queue")
        queue_label.setStyleSheet(
            f"color: {COLORS['text_dim']}; font-weight: bold; margin-top: 10px;"
        )
        center_layout.addWidget(queue_label)
        
        self.queue_list = QListWidget()
        self.queue_list.itemClicked.connect(self._on_queue_item_clicked)
        center_layout.addWidget(self.queue_list)
        
        # Bottom Actions
        actions_layout = QHBoxLayout()
        self.btn_add = QPushButton("+ Add Files")
        self.btn_add.clicked.connect(self.open_file_dialog)
        self.btn_clear = QPushButton("Clear")
        self.btn_clear.clicked.connect(self._on_clear_queue)
        self.logs_btn = QPushButton("View Logs")
        self.logs_btn.setFlat(True)
        self.logs_btn.setStyleSheet(f"color: {COLORS['text_dim']}; text-decoration: underline;")
        self.logs_btn.clicked.connect(self.log_window.show)
        
        actions_layout.addWidget(self.btn_add)
        actions_layout.addWidget(self.btn_clear)
        actions_layout.addStretch()
        actions_layout.addWidget(self.logs_btn)
        center_layout.addLayout(actions_layout)
        
        self.center_panel = center_panel  # Store reference for view switching
        self.main_layout.addWidget(center_panel, 1)

    def _setup_right_panel(self):
        """Create right control panel as a dock widget."""
        # Create Dock Widget
        self.right_dock = QDockWidget("Controls", self)
        self.right_dock.setObjectName("right_dock")
        self.right_dock.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea | Qt.DockWidgetArea.LeftDockWidgetArea)
        self.right_dock.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetFloatable | 
                                  QDockWidget.DockWidgetFeature.DockWidgetMovable)
        
        # Content Widget
        right_panel = QWidget()
        right_panel.setMinimumWidth(280)
        right_panel.setObjectName("right_panel")
        right_panel.setStyleSheet(
            "#right_panel { background-color: rgba(26, 26, 26, 0.6); border-left: 1px solid #000000; }"
        )
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        # Scroll Area - vertical only
        from PyQt6.QtCore import Qt as QtCore
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(QtCore.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("background: transparent;")
        
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        content_layout = QVBoxLayout(scroll_content)
        content_layout.setContentsMargins(10, 20, 10, 20)
        content_layout.setSpacing(15)
        
        # --- Control Panels ---
        
        # Stem Options
        self.stem_panel = StemOptionsPanel()
        self.stem_panel.toggled.connect(self._on_stem_toggled)
        content_layout.addWidget(self.stem_panel)
        
        # Audio Enhancement
        self.enhance_panel = AudioEnhancementPanel()
        self.enhance_panel.toggled.connect(self._on_enhance_toggled)
        content_layout.addWidget(self.enhance_panel)
        
        # Quality Mode
        self.quality_panel = QualityModePanel()
        content_layout.addWidget(self.quality_panel)
        
        # Audio Manipulation
        self.manip_panel = ManipulationPanel()
        content_layout.addWidget(self.manip_panel)
        
        # Output Options
        self.output_panel = OutputPanel()
        content_layout.addWidget(self.output_panel)
        
        # Advanced Settings
        self.advanced_panel = AdvancedSettingsPanel(self.model_manager)
        self.advanced_panel.ensemble_config_requested.connect(self._configure_ensemble)
        self.advanced_panel.btn_import_model.clicked.connect(self._import_custom_model)
        content_layout.addWidget(self.advanced_panel)
        
        content_layout.addStretch()
        
        scroll.setWidget(scroll_content)
        right_layout.addWidget(scroll)
        
        # START BUTTON
        self.btn_process = QPushButton("START PROCESSING")
        self.btn_process.setFixedHeight(60)
        self.btn_process.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_process.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['primary']}; 
                color: #000; 
                border-radius: 8px; 
                font-size: 16px; 
                font-weight: 900;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {COLORS['text']};
            }}
            QPushButton:pressed {{
                background-color: {COLORS['accent']};
            }}
        """)
        self.btn_process.clicked.connect(self.start_processing)
        
        # PREVIEW BUTTON
        self.btn_preview = QPushButton("🔎 Preview (30s)")
        self.btn_preview.setFixedHeight(40) # Smaller than Start
        self.btn_preview.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_preview.setToolTip("Process selected 30s to check settings")
        self.btn_preview.setStyleSheet(f"""
             QPushButton {{
                background-color: {COLORS['surface']}; 
                border: 1px solid {COLORS['primary']};
                color: {COLORS['primary']}; 
                border-radius: 6px; 
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {COLORS['primary_dim']};
                color: white;
            }}
        """)
        self.btn_preview.clicked.connect(self.start_preview)
        
        btn_container = QWidget()
        btn_layout = QVBoxLayout(btn_container)
        btn_layout.setContentsMargins(15, 0, 15, 20)
        
        # Add both buttons
        btn_layout.addWidget(self.btn_process)
        btn_layout.addWidget(self.btn_preview)
        
        right_layout.addWidget(btn_container)
        
        # Set dock widget
        self.right_dock.setWidget(right_panel)
        # Restore title bar and floating state
        self.right_dock.setTitleBarWidget(None) 
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.right_dock)
        self.right_dock.setFloating(False)
        self.resizeDocks([self.right_dock], [650], Qt.Orientation.Horizontal)
        
        self._setup_connections()

    def _setup_connections(self):
        """Connect signals."""
        self.stem_panel.selection_changed.connect(self._update_model_for_mode)
        
    def _update_model_for_mode(self):
        """Auto-select best model based on stem mode."""
        stem_count, mode = self.stem_panel.get_stem_config()
        all_models = self.model_manager.get_all_models()
        
        # Priority Logic: Roformer > User Import > Default Fallback
        
        target_model = "htdemucs" # Ultimate fallback
        
        if mode == "vocals_only" or (stem_count == 2 and mode == "standard"):
            # Prefer MelBand Roformer for Vocals
            if "vocals_mel_band_roformer.ckpt" in all_models:
                target_model = "vocals_mel_band_roformer.ckpt"
            elif "Kim_Vocal_2.onnx" in all_models:
                target_model = "Kim_Vocal_2.onnx"
                
        elif mode == "instrumental":
            # Prefer BS-Roformer for Instrumental
            if "model_bs_roformer_ep_317_sdr_12.9755.ckpt" in all_models:
                target_model = "model_bs_roformer_ep_317_sdr_12.9755.ckpt"
            elif "UVR-MDX-NET-Inst_HQ_3.onnx" in all_models:
                target_model = "UVR-MDX-NET-Inst_HQ_3.onnx"
                
        else:
             # Standard 4-Stem, Drums, Bass, etc.
             # These require a 4-stem model like htdemucs.
             # Roformer (ep_317) is typically 2-stem (Vocals/Inst), so do NOT use it here.
             
             if stem_count == 4:
                 target_model = "htdemucs"
             elif mode in ["drums_only", "bass_only"]:
                 target_model = "htdemucs"
             elif stem_count == 6:
                 # Check for 6-stem model
                 if "htdemucs_6s" in all_models:
                     target_model = "htdemucs_6s"
                 else:
                     target_model = "htdemucs" # Fallback
             else:
                 target_model = "htdemucs"
                 
        # Set the model in Advanced Panel
        # We need to access the combo box directly or add a setter
        index = self.advanced_panel.combo_model.findText(target_model)
        if index >= 0:
            self.advanced_panel.combo_model.setCurrentIndex(index)

    def _on_stem_toggled(self, checked):
        """Collapse enhance panel when stem panel expands."""
        if checked and self.enhance_panel.isChecked():
            self.enhance_panel.setChecked(False)

    def _on_enhance_toggled(self, checked):
        """Collapse stem panel when enhance panel expands."""
        if checked and self.stem_panel.isChecked():
            self.stem_panel.setChecked(False)

    def _on_queue_item_clicked(self, item):
        """Handle click on queue item to show input waveform."""
        widget = self.queue_list.itemWidget(item)
        status = widget.status_label.text()
        file_path = item.data(Qt.ItemDataRole.UserRole)
        
        # If Pending, show input waveform for selection
        if "Pending" in status:
            self.player_widget.load_input_waveform(file_path) # Load into bottom player
            # self.visualizer.load_file(file_path) 
        # If Done, we could show results, but for now user focused on input selection
        # else:
            # Maybe show result stems? existing logic handles dragging/opening
            # For now, do nothing or switch to input waveform anyway if they want to re-preview
            # self.player_widget.load_input_waveform(file_path)
            pass

    def _update_gpu_status(self):
        """Update GPU status display."""
        is_gpu, device_name, _ = get_gpu_info()
        if is_gpu:
            self.gpu_label.setText(f"🚀 {device_name}")
            self.gpu_label.setStyleSheet(
                f"background-color: rgba(0, 212, 255, 0.1); color: {COLORS['success']}; "
                f"padding: 4px 12px; border-radius: 12px; font-size: 11px; "
                f"border: 1px solid {COLORS['success']};"
            )
        else:
            self.gpu_label.setText("🐢 CPU Mode")

    def _configure_ensemble(self):
        """Open ensemble configuration dialog."""
        from src.ui.ensemble_dialog import EnsembleConfigDialog
        models = self.model_manager.get_all_models()
        current = self.advanced_panel.ensemble_models
        dlg = EnsembleConfigDialog(models, current, self)
        if dlg.exec():
            self.advanced_panel.set_ensemble_config(
                dlg.get_selected_models(),
                dlg.get_algorithm()
            )

    def _import_custom_model(self):
        """Import custom model files."""
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Model Files", "", "Model Files (*.pth *.onnx *.yaml)"
        )
        if files:
            for f in files:
                self.model_manager.import_model(f)
            self.advanced_panel.refresh_model_list()
            self.append_log(f"Imported {len(files)} custom models.\n")

    def append_log(self, text):
        self.log_window.text_edit.moveCursor(
            self.log_window.text_edit.textCursor().MoveOperation.End
        )
        self.log_window.text_edit.insertPlainText(text)
        self.log_window.text_edit.moveCursor(
            self.log_window.text_edit.textCursor().MoveOperation.End
        )

    def open_file_dialog(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Audio Files", "", "Audio Files (*.mp3 *.wav *.flac *.m4a)"
        )
        if files:
            self.add_files_to_queue(files)

    def add_files_to_queue(self, files):
        for f in files:
            item = QListWidgetItem(self.queue_list)
            item.setData(Qt.ItemDataRole.UserRole, f)
            widget = QueueItemWidget(os.path.basename(f))
            item.setSizeHint(widget.sizeHint())
            self.queue_list.addItem(item)
            self.queue_list.setItemWidget(item, widget)
            
            widget.cancel_requested.connect(lambda i=item: self.remove_queue_item(i))
            widget.open_folder_requested.connect(lambda i=item: self.open_item_folder(i))
            widget.resplit_requested.connect(lambda i=item: self.resplit_item(i))
            widget.midi_export_requested.connect(self.start_midi_export)

        # Auto-load the first file's waveform if this is a fresh batch
        if files:
            self.player_widget.load_input_waveform(files[0]) # Load into bottom player
            # self.visualizer.load_file(files[0]) 

    def start_midi_export(self, audio_paths, batch_mode=False):
        """Start MIDI export for a specific stem or list of stems."""
        from src.ui.workers import MidiExportWorker
        
        # Handle string vs list
        if isinstance(audio_paths, str):
            paths = [audio_paths]
            log_name = os.path.basename(audio_paths)
        else:
            paths = audio_paths
            log_name = f"{len(paths)} files"
        
        self.append_log(f"Starting MIDI export for: {log_name}...\n")
        
        # Create worker
        self.midi_worker = MidiExportWorker(paths)
        
        if batch_mode:
            self.midi_worker.finished.connect(lambda p: self.append_log(f"MIDI Exported: {os.path.basename(p)}\n"))
            self.midi_worker.all_completed.connect(self._on_midi_batch_finished)
        else:
            self.midi_worker.finished.connect(self._on_midi_export_finished)
            
        self.midi_worker.error.connect(self._on_midi_export_error)
        self.midi_worker.start()

    def _on_midi_batch_finished(self):
        self.append_log("Batch MIDI Export Complete.\n")
        play_notification_sound()
        
    def _on_midi_export_finished(self, output_path):
        self.append_log(f"MIDI Export Complete: {output_path}\n")
        play_notification_sound()
        
        from PyQt6.QtWidgets import QMessageBox
        msg = QMessageBox(self)
        msg.setWindowTitle("Export Complete")
        msg.setText(f"MIDI file created:\n{output_path}")
        msg.setIcon(QMessageBox.Icon.Information)
        msg.addButton("Open Folder", QMessageBox.ButtonRole.AcceptRole)
        msg.addButton("Close", QMessageBox.ButtonRole.RejectRole)
        
        if msg.exec() == QMessageBox.ButtonRole.AcceptRole:
             open_folder_cross_platform(os.path.dirname(output_path))
             
    def _on_midi_export_error(self, error):
        self.append_log(f"MIDI Export Error: {error}\n")
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.critical(self, "Export Failed", f"Failed to export MIDI:\n{error}")

    def resplit_item(self, item):
        widget = self.queue_list.itemWidget(item)
        widget.update_progress(None, 0, "Pending")
        widget.status_label.setStyleSheet(f"color: {COLORS['text_dim']};")
        self.start_processing()

    def remove_queue_item(self, item):
        if hasattr(self, 'worker') and self.worker.isRunning():
            widget = self.queue_list.itemWidget(item)
            status = widget.status_label.text()
            if "Pending" not in status and "Done" not in status and "Error" not in status and "Cancelled" not in status:
                from src.utils.logger import logger
                logger.info("Terminating active process...")
                
                self.worker.terminate()
                self.worker.wait()
                widget.update_progress(None, 0, "Cancelled")
                
                file_path = item.data(Qt.ItemDataRole.UserRole)
                base_name = os.path.splitext(os.path.basename(file_path))[0]
                output_dir = os.path.join(os.path.dirname(file_path), f"{base_name} - Stems")
                
                if os.path.exists(output_dir):
                    import shutil
                    try:
                        shutil.rmtree(output_dir)
                        logger.info(f"Cleaned up output directory: {output_dir}")
                    except Exception as e:
                        logger.error(f"Failed to clean up output directory: {e}")
        
        row = self.queue_list.row(item)
        self.queue_list.takeItem(row)

    def _on_clear_queue(self):
        """Clear queue and player tracks."""
        self.queue_list.clear()
        if hasattr(self, 'player_widget'):
            self.player_widget.load_input_waveform("") # Clears loaded waveform/tracks
            self.player_widget.waveform.setVisible(False) # Ensure waveform is hidden
            
    def open_item_folder(self, item):
        file_path = item.data(Qt.ItemDataRole.UserRole)
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        output_dir = os.path.join(os.path.dirname(file_path), f"{base_name} - Stems")
        
        if os.path.exists(output_dir):
            open_folder_cross_platform(output_dir)
        else:
            open_folder_cross_platform(os.path.dirname(file_path))

    def update_visualizer_state(self):
        is_playing = False
        if hasattr(self, 'player_widget'):
            is_playing = self.player_widget.is_playing
            
        is_processing = hasattr(self, 'worker') and self.worker.isRunning()
        
        if hasattr(self, 'visualizer'):
            self.visualizer.set_active(is_processing or is_playing)

    def start_processing(self):
        if hasattr(self, 'worker') and self.worker.isRunning():
            return

        for i in range(self.queue_list.count()):
            item = self.queue_list.item(i)
            widget = self.queue_list.itemWidget(item)
            
            if widget.status_label.text() == "Pending":
                self.process_item(item)
                return
        
        self.update_visualizer_state()

    def process_item(self, item):
        self.update_visualizer_state()
            
        widget = self.queue_list.itemWidget(item)
        file_path = item.data(Qt.ItemDataRole.UserRole)
        
        # Get values from panels
        stem_count, mode = self.stem_panel.get_stem_config()
        enhance_values = self.enhance_panel.get_values()
        manip_values = self.manip_panel.get_values()
        output_values = self.output_panel.get_values()
        advanced_values = self.advanced_panel.get_values()
        
        # Get Global Settings
        from PyQt6.QtCore import QSettings
        settings = QSettings("BeatDeStack", "BeatDeStackExtended")
        filename_pattern = settings.value("output/filename_pattern", "{stem}")
        
        options = {
            "stem_count": stem_count,
            "mode": mode,
            "output_dir": os.path.dirname(file_path), # Will be overridden by worker logic for folders
            "quality": self.quality_panel.get_quality(),
            "export_zip": mode == "zip",
            "keep_original": False, # Usually false for internal processing unless requested
            "format": output_values["format"],
            "sample_rate": output_values["sample_rate"],
            "bit_depth": output_values["bit_depth"],
            "invert": self.stem_panel.is_invert_enabled(),
            "filename_pattern": filename_pattern,
            **enhance_values,
            **manip_values,
            **output_values,
            **advanced_values
        }
        
        self.worker = SplitterWorker(file_path, options)
        self.worker.progress_updated.connect(widget.update_progress)
        self.worker.log_message.connect(lambda msg: self.append_log(msg + "\n"))
        self.worker.finished.connect(lambda _: self.on_worker_finished(item))
        self.worker.error_occurred.connect(lambda f, e: self.on_worker_error(item, e))
        self.worker.start()

    def start_preview(self):
        """Generate a 30s preview for the selected item."""
        if hasattr(self, 'worker') and self.worker.isRunning():
            self.append_log("Cannot start preview: Process already running.\n")
            return

        selected_items = self.queue_list.selectedItems()
        if not selected_items:
            # Fallback: take first item
            if self.queue_list.count() > 0:
                item = self.queue_list.item(0)
            else:
                self.append_log("No file to preview. Add a file to queue first.\n")
                return
        else:
            item = selected_items[0]
            
        file_path = item.data(Qt.ItemDataRole.UserRole)
        
        # 1. Create Slice
        from src.core.preview import create_preview_slice
        base_dir = os.path.dirname(file_path)
        preview_dir = os.path.join(base_dir, "Previews")
        os.makedirs(preview_dir, exist_ok=True)
        
        temp_slice_path = os.path.join(preview_dir, f"preview_source_{os.path.basename(file_path)}")
        
        # Check if we have a selection from the waveform
        start_time = None
        duration = 30
        
        # If the player is showing the waveform (meaning input matches and is visible)
        if hasattr(self.player_widget, 'waveform') and self.player_widget.waveform.isVisible():
             # Just trust the waveform widget if it's visible
             sel_start, sel_end = self.player_widget.waveform.get_selection()
             start_time = sel_start
             duration = sel_end - sel_start
             # Ensure at least some duration
             if duration < 1: duration = 30
        
        self.append_log(f"Generating preview slice ({duration:.1f}s from {start_time if start_time else 'auto'})...\n")
        if not create_preview_slice(file_path, temp_slice_path, duration=duration, start_time=start_time):
             self.append_log("Failed to create preview slice.\n")
             return

        # 2. Setup Options
        stem_count, mode = self.stem_panel.get_stem_config()
        output_values = self.output_panel.get_values()
        
        from PyQt6.QtCore import QSettings
        settings = QSettings("BeatDeStack", "BeatDeStackExtended")
        filename_pattern = settings.value("output/filename_pattern", "{stem}")
        
        options = {
            "stem_count": stem_count,
            "mode": mode,
            "output_dir": os.path.dirname(file_path), # Placeholder
            "quality": self.quality_panel.get_quality(),
            "export_zip": False,
            "keep_original": False,
            "format": output_values["format"],
            "sample_rate": output_values["sample_rate"],
            "bit_depth": output_values["bit_depth"],
            "invert": self.stem_panel.is_invert_enabled(),
            "filename_pattern": filename_pattern,
            **self.enhance_panel.get_values(),
            **self.manip_panel.get_values(),
            **output_values,
            **self.advanced_panel.get_values()
        }
        
        self.worker = SplitterWorker(temp_slice_path, options)
        self.worker.log_message.connect(lambda msg: self.append_log(msg + "\n"))
        self.worker.finished.connect(lambda: self._on_preview_finished(temp_slice_path))
        self.worker.error_occurred.connect(lambda f, e: self.append_log(f"Preview Error: {e}\n"))
        self.worker.start()
        self.update_visualizer_state()
        
    def _on_preview_finished(self, slice_path):
        self.append_log("Preview Ready! Loading into player...\n")
        play_notification_sound()
        
        # Find results
        base_name = os.path.splitext(os.path.basename(slice_path))[0]
        output_dir = os.path.join(os.path.dirname(slice_path), f"{base_name} - Stems")
        
        # Auto-load into player
        stems = {}
        # Support exts
        EXTS = ('.wav', '.mp3', '.flac')
        try:
            for f in os.listdir(output_dir):
                if f.lower().endswith(EXTS):
                    name = os.path.splitext(f)[0]
                    clean = name.replace(f"{base_name}_", "").replace(f"{base_name} ", "")
                    stems[clean] = os.path.join(output_dir, f)
        except Exception:
            pass
            
        if stems:
            self.player_widget.load_stems(stems)
            self.player_widget.toggle_playback() # Auto-play

    def on_worker_finished(self, item):
        import glob
        
        file_path = item.data(Qt.ItemDataRole.UserRole)
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        output_dir = os.path.join(os.path.dirname(file_path), f"{base_name} - Stems")
        
        output_files = []
        if os.path.exists(output_dir):
            output_files = glob.glob(os.path.join(output_dir, "*.wav"))
            output_files += glob.glob(os.path.join(output_dir, "*.mp3"))

        widget = self.queue_list.itemWidget(item)
        widget.update_progress(None, 100, "Done", output_files=output_files)
        
        play_notification_sound()
            
        if self.output_panel.is_auto_open_enabled():
            self.open_item_folder(item)
            
        # Check for Auto-MIDI Export
        if self.worker.options.get("export_midi") and output_files:
            self.start_midi_export(output_files, batch_mode=True)
            
        self.start_processing()

    def on_worker_error(self, item, error):
        widget = self.queue_list.itemWidget(item)
        widget.status_label.setText(f"Error: {error}")
        widget.status_label.setStyleSheet(f"color: {COLORS['danger']};")
        self.start_processing()

    # --- Sidebar Navigation Methods ---
    
    def _setup_shortcuts(self):
        """Setup keyboard shortcuts."""
        from PyQt6.QtGui import QShortcut, QKeySequence
        
        # Ctrl+O: Open file
        QShortcut(QKeySequence("Ctrl+O"), self, self.open_file_dialog)
        
        # Ctrl+,: Settings
        QShortcut(QKeySequence("Ctrl+,"), self, self._open_settings)
        
        # Ctrl+Enter: Start processing
        QShortcut(QKeySequence("Ctrl+Return"), self, self.start_processing)
        
        # Ctrl+1/2: View switching
        QShortcut(QKeySequence("Ctrl+1"), self, lambda: self._switch_view(0))
        QShortcut(QKeySequence("Ctrl+2"), self, lambda: self._switch_view(1))
    
    def _highlight_sidebar_button(self, index):
        """Highlight active sidebar button."""
        for i, btn in enumerate(self.sidebar_buttons):
            if i == index:
                btn.setStyleSheet(
                    f"background-color: {COLORS['primary_dim']}; border-radius: 8px;"
                )
            else:
                btn.setStyleSheet(
                    "background-color: transparent; border-radius: 8px;"
                )
    
    def _switch_view(self, index):
        """Switch between Home (0), Models (1), and Batch (2) views."""
        self._highlight_sidebar_button(index)
        
        # Hide all overlay views first
        for view_name in ['models_view', 'batch_view']:
            if hasattr(self, view_name):
                view = getattr(self, view_name)
                if view.isVisible():
                    view.hide()
        
        if index == 0:
            # Show main processing view (home)
            self.center_panel.show()
        elif index == 1:
            # Hide home, show models view
            self.center_panel.hide()
            self._show_models_view()
        elif index == 2:
            # Hide home, show batch view
            self.center_panel.hide()
            self._show_batch_view()
    
    def _show_models_view(self):
        """Show the models management view."""
        from src.ui.views import ModelsView
        
        if not hasattr(self, 'models_view'):
            self.models_view = ModelsView(self.model_manager, self)
            self.models_view.setStyleSheet(f"background-color: {COLORS['background']};")
            # Insert at same position as center_panel (index 1, after sidebar)
            self.main_layout.insertWidget(1, self.models_view, 1)
            # Connect to refresh Advanced Settings when models change
            self.models_view.models_changed.connect(self.advanced_panel.refresh_model_list)
        
        self.models_view.show()
    
    def _show_batch_view(self):
        """Show the batch processing view."""
        from src.ui.views import BatchView
        
        if not hasattr(self, 'batch_view'):
            self.batch_view = BatchView(self)
            self.batch_view.setStyleSheet(f"background-color: {COLORS['background']};")
            # Insert at same position as center_panel (index 1, after sidebar)
            self.main_layout.insertWidget(1, self.batch_view, 1)
            # Connect signal
            self.batch_view.files_ready.connect(self._on_batch_files_ready)
        
        self.batch_view.show()

    def _on_batch_files_ready(self, files):
        """Handle files ready from batch view."""
        self.add_files_to_queue(files)
        self._switch_view(0)  # Switch back to home
        self.append_log(f"Added {len(files)} files from batch processing.\n")
    
    def _show_batch_placeholder(self):
        """Switch to batch view."""
        self._switch_view(2)
    
    def _open_settings(self):
        """Open the settings dialog."""
        from src.ui.settings_dialog import SettingsDialog
        dialog = SettingsDialog(self)
        dialog.exec()

    def _on_queue_item_clicked(self, item):
        """Handle click on queue item to auto-load stems into player."""
        widget = self.queue_list.itemWidget(item)
        status = widget.status_label.text()
        
        # Only load if processing is complete
        if "Done" not in status:
            return
            
        file_path = item.data(Qt.ItemDataRole.UserRole)
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        output_dir = os.path.join(os.path.dirname(file_path), f"{base_name} - Stems")
        
        if not os.path.exists(output_dir):
            return
            
        # Collect stems
        stems = {}
        
        # Add Original if exists
        if os.path.exists(file_path):
            stems["Original"] = file_path
            
        # Scan folder for supported audio files
        supported_exts = ('.wav', '.mp3', '.flac', '.ogg', '.m4a')
        
        try:
            for f in os.listdir(output_dir):
                if f.lower().endswith(supported_exts):
                    # Use filename as track name (e.g. "vocals", "drums")
                    name = os.path.splitext(f)[0]
                    # Clean up name if it has prefixes like separate_
                    clean_name = name.replace(f"{base_name}_", "").replace(f"{base_name} ", "")
                    stems[clean_name] = os.path.join(output_dir, f)
        except Exception as e:
            self.append_log(f"Error scanning stems directory: {e}\n")
            return
            
        if stems:
            self.player_widget.load_stems(stems)

