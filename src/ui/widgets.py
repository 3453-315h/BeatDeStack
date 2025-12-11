from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, 
    QProgressBar, QPushButton, QFrame, QStyle
)
from PyQt6.QtCore import Qt, pyqtSignal, QMimeData, QUrl
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QIcon, QDrag, QAction
from .style import COLORS
import os

class DragDropWidget(QFrame):
    files_dropped = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        self.setStyleSheet(f"""
            QFrame {{
                border: 2px dashed {COLORS['text_dim']};
                border-radius: 15px;
                background-color: rgba(26, 26, 46, 0.3);
            }}
            QFrame:hover {{
                border-color: {COLORS['secondary']};
                background-color: rgba(0, 229, 255, 0.1);
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(20, 30, 20, 30)
        
        self.label = QLabel("Drag & Drop Audio Files Here")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 12px; font-weight: bold; padding: 10px")
        layout.addWidget(self.label)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.accept()
            self.setStyleSheet(f"""
                QFrame {{
                    border: 2px dashed {COLORS['primary']};
                    border-radius: 15px;
                    background-color: rgba(214, 0, 255, 0.1);
                }}
            """)
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self.setStyleSheet(f"""
            QFrame {{
                border: 2px dashed {COLORS['text_dim']};
                border-radius: 15px;
                background-color: rgba(26, 26, 46, 0.3);
            }}
        """)

    def dropEvent(self, event: QDropEvent):
        self.setStyleSheet(f"""
            QFrame {{
                border: 2px dashed {COLORS['text_dim']};
                border-radius: 15px;
                background-color: rgba(26, 26, 46, 0.3);
            }}
        """)
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        valid_files = [f for f in files if f.lower().endswith(('.mp3', '.wav', '.flac', '.m4a'))]
        if valid_files:
            self.files_dropped.emit(valid_files)

class QueueItemWidget(QWidget):
    cancel_requested = pyqtSignal()
    open_folder_requested = pyqtSignal()
    resplit_requested = pyqtSignal()
    midi_export_requested = pyqtSignal(str)

    def __init__(self, filename, parent=None):
        super().__init__(parent)
        self.output_files = [] # Store output paths
        self.setMinimumHeight(40)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 8, 15, 8)
        layout.setSpacing(15)
        
        self.name_label = QLabel(filename)
        self.name_label.setStyleSheet(f"color: {COLORS['text']}; font-weight: bold;")
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.name_label, 2, Qt.AlignmentFlag.AlignVCenter)
        
        self.status_label = QLabel("Pending")
        self.status_label.setStyleSheet(f"color: {COLORS['text_dim']};")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.status_label, 1, Qt.AlignmentFlag.AlignVCenter)
        
        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(12)  # Force height constraint

        self.progress.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid {COLORS['secondary']};
                border-radius: 4px;
                background-color: {COLORS['background']};
                height: 12px;
            }}
            QProgressBar::chunk {{
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {COLORS['primary']}, stop:1 {COLORS['secondary']});
                border-radius: 2px;
            }}
        """)
        layout.addWidget(self.progress, 3, Qt.AlignmentFlag.AlignVCenter)
        
        self.cancel_btn = QPushButton()
        self.cancel_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_TitleBarCloseButton))
        self.cancel_btn.setFixedSize(30, 30)
        self.cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: 1px solid {COLORS['danger']};
                border-radius: 15px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['danger']};
            }}
        """)
        self.cancel_btn.clicked.connect(self.cancel_requested.emit)
        layout.addWidget(self.cancel_btn, 0, Qt.AlignmentFlag.AlignVCenter)
        
        self.open_btn = QPushButton()
        self.open_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DirOpenIcon))
        self.open_btn.setFixedSize(30, 30)
        self.open_btn.setToolTip("Open Output Folder")
        self.open_btn.hide()
        self.open_btn.clicked.connect(self.open_output_folder)
        layout.addWidget(self.open_btn, 0, Qt.AlignmentFlag.AlignVCenter)

    def update_progress(self, filename, value, status=None, output_files=None):
        self.progress.setValue(value)
        if status:
            self.status_label.setText(status)
            if "Error" in status:
                self.status_label.setStyleSheet(f"color: {COLORS['danger']};")
            elif "Done" in status:
                self.status_label.setStyleSheet(f"color: {COLORS['success']};")
                self.open_btn.show()
                # Keep cancel button visible but change purpose to 'Remove'
                self.cancel_btn.show()
                self.cancel_btn.setToolTip("Remove from List")
                if output_files:
                    self.output_files = output_files # Update stored files
            elif "Pending" in status:
                self.open_btn.hide()
                self.drag_btn.hide()
                self.cancel_btn.show()
                
    def contextMenuEvent(self, event):
        from PyQt6.QtWidgets import QMenu
        from PyQt6.QtGui import QAction
        menu = QMenu(self)
        
        open_action = QAction("Open Output Folder", self)
        open_action.triggered.connect(self.open_output_folder)
        menu.addAction(open_action)
        
        # MIDI Export Submenu
        if self.output_files:
            midi_menu = menu.addMenu("Export as MIDI")
            for file_path in self.output_files:
                filename = os.path.basename(file_path)
                action = QAction(filename, self)
                # Use default argument to capture loop variable
                action.triggered.connect(lambda checked, path=file_path: self.midi_export_requested.emit(path))
                midi_menu.addAction(action)
        
        menu.addSeparator()
        
        resplit_action = QAction("Re-split", self)
        resplit_action.triggered.connect(self.resplit_requested.emit)
        menu.addAction(resplit_action)
        
        remove_action = QAction("Remove", self)
        remove_action.triggered.connect(self.cancel_requested.emit)
        menu.addAction(remove_action)
        
        menu.exec(event.globalPos())

    def open_output_folder(self):
        self.open_folder_requested.emit()

from PyQt6.QtGui import QPainter, QColor, QBrush
from PyQt6.QtCore import QTimer
import random

class VisualizerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(80)
        self.bars = 40
        self.values = [0.1] * self.bars
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_values)
        self.timer.start(50)  # 20 FPS
        self.active = False
        self.setStyleSheet(f"background-color: rgba(0, 0, 0, 0.3); border-radius: 8px; border: 1px solid rgba(255,255,255,0.05);")

    def set_active(self, active):
        self.active = active
        if not active:
            self.values = [0.1] * self.bars
            self.update()

    def update_values(self):
        if self.active:
            # Simulate spectrum
            self.values = [max(0.1, min(1.0, random.random() * 0.8 + 0.1)) for _ in range(self.bars)]
        else:
            # Idle gentle wave
            import math
            import time
            t = time.time()
            self.values = [0.1 + 0.05 * math.sin(t * 2 + i * 0.2) for i in range(self.bars)]
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        w = self.width()
        h = self.height()
        bar_w = w / self.bars
        
        for i, val in enumerate(self.values):
            bar_h = h * val * 0.8
            x = i * bar_w
            y = (h - bar_h) / 2
            
            # Gradient color
            c = QColor(COLORS['primary'])
            if self.active:
                c.setAlpha(200)
            else:
                c.setAlpha(100)
                
            painter.setBrush(QBrush(c))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(int(x + 1), int(y), int(bar_w - 2), int(bar_h), 2, 2)

