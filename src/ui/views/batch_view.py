from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget,
    QPushButton, QGroupBox, QProgressBar, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from src.ui.style import COLORS


class BatchView(QWidget):
    """View for batch processing multiple folders/files."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Header
        header = QLabel("📚 Batch Processing")
        header.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {COLORS['text']};")
        layout.addWidget(header)
        
        desc = QLabel("Process entire folders of audio files with consistent settings")
        desc.setStyleSheet(f"color: {COLORS['text_dim']};")
        layout.addWidget(desc)
        
        # Input Folders
        input_group = QGroupBox("Input Folders")
        input_layout = QVBoxLayout()
        
        self.folder_list = QListWidget()
        self.folder_list.setMinimumHeight(150)
        input_layout.addWidget(self.folder_list)
        
        btn_layout = QHBoxLayout()
        self.btn_add_folder = QPushButton("+ Add Folder")
        self.btn_add_folder.clicked.connect(self._add_folder)
        btn_layout.addWidget(self.btn_add_folder)
        
        self.btn_remove_folder = QPushButton("Remove")
        self.btn_remove_folder.clicked.connect(self._remove_folder)
        btn_layout.addWidget(self.btn_remove_folder)
        btn_layout.addStretch()
        input_layout.addLayout(btn_layout)
        
        input_group.setLayout(input_layout)
        layout.addWidget(input_group)
        
        # Status
        status_group = QGroupBox("Status")
        status_layout = QVBoxLayout()
        
        self.lbl_status = QLabel("Ready - Add folders to begin")
        self.lbl_status.setStyleSheet(f"color: {COLORS['text_dim']};")
        status_layout.addWidget(self.lbl_status)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        status_layout.addWidget(self.progress_bar)
        
        self.lbl_current = QLabel("")
        self.lbl_current.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 12px;")
        status_layout.addWidget(self.lbl_current)
        
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        # Actions
        actions_layout = QHBoxLayout()
        actions_layout.addStretch()
        
        self.btn_start = QPushButton("🚀 Start Batch Processing")
        self.btn_start.setStyleSheet(f"background-color: {COLORS['primary']}; color: #000; padding: 12px 24px; font-weight: bold;")
        self.btn_start.clicked.connect(self._start_batch)
        actions_layout.addWidget(self.btn_start)
        
        layout.addLayout(actions_layout)
        layout.addStretch()
    
    def _add_folder(self):
        """Add a folder to the batch list."""
        from PyQt6.QtWidgets import QFileDialog
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self.folder_list.addItem(folder)
            self._update_status()
    
    def _remove_folder(self):
        """Remove selected folder from list."""
        for item in self.folder_list.selectedItems():
            self.folder_list.takeItem(self.folder_list.row(item))
        self._update_status()
    
    def _update_status(self):
        """Update status label."""
        count = self.folder_list.count()
        if count == 0:
            self.lbl_status.setText("Ready - Add folders to begin")
        else:
            self.lbl_status.setText(f"{count} folder(s) queued")
    
    files_ready = pyqtSignal(list)

    def _start_batch(self):
        """Start batch processing."""
        if self.folder_list.count() == 0:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(self, "No Folders", "Add at least one folder to process.")
            return
        
        folders = []
        for i in range(self.folder_list.count()):
            folders.append(self.folder_list.item(i).text())
            
        files = self._scan_folders(folders)
        
        if not files:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(self, "No files found", "No supported audio files found in selected folders.")
            return

        self.files_ready.emit(files)
        
    def _scan_folders(self, folders):
        """Scan folders for audio files."""
        import os
        audio_exts = {'.mp3', '.wav', '.flac', '.m4a', '.ogg', '.aiff', '.wma'}
        found_files = []
        
        for folder in folders:
            for root, _, files in os.walk(folder):
                for file in files:
                    if os.path.splitext(file)[1].lower() in audio_exts:
                        found_files.append(os.path.join(root, file))
                        
        return found_files
