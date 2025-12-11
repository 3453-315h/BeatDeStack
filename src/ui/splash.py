from PyQt6.QtWidgets import QSplashScreen, QProgressBar, QVBoxLayout, QLabel, QWidget
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap, QPainter, QColor, QFont, QPen
from .style import COLORS

class SplashScreen(QSplashScreen):
    def __init__(self, splash_path=None):
        # Determine resource path
        import sys
        import os
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.abspath(".")
            
        splash_dir = os.path.join(base_path, "resources", "splashes")
        pixmap = None

        if os.path.exists(splash_dir):
            import random
            # Get list of png files in the directory
            splash_files = [f for f in os.listdir(splash_dir) if f.lower().endswith('.png')]
            if splash_files:
                selected_splash = random.choice(splash_files)
                splash_path = os.path.join(splash_dir, selected_splash)
                pixmap = QPixmap(splash_path)

        if pixmap is None:
            # Fallback if image missing or folder empty
            pixmap = QPixmap(600, 400)
            pixmap.fill(QColor(COLORS['background']))
            painter = QPainter(pixmap)
            painter.setPen(QColor(COLORS['text']))
            painter.drawText(0, 0, 600, 400, Qt.AlignmentFlag.AlignCenter, "BeatDeStack eXtended")
            painter.end()

        # Initialize with the pixmap
        super().__init__(pixmap)
        
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)

    def show_message(self, message):
        self.showMessage(message, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter, QColor(COLORS['secondary']))
