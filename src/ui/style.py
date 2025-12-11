
COLORS = {
    "background": "#0E0E0E",
    "surface": "#1A1A1A",
    "primary": "#00D4FF",  # Bright Cyan
    "secondary": "#FF6B6B", # Soft Coral
    "text": "#FFFFFF",
    "text_dim": "#B0B0B0",
    "danger": "#FF4444",
    "success": "#00D4FF",
    "accent": "#FF6B6B",
    "primary_dim": "rgba(0, 212, 255, 0.2)"
}

STYLESHEET = f"""
QMainWindow {{
    background-color: {COLORS['background']};
}}

QWidget {{
    color: {COLORS['text']};
    font-family: 'Segoe UI', 'Roboto', 'Helvetica Neue', sans-serif;
    font-size: 14px;
}}

/* Glassy Panels */
QFrame {{
    border: none;
}}

/* Buttons */
QPushButton {{
    background-color: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    padding: 8px 16px;
    color: {COLORS['primary']};
    font-weight: 600;
}}

QPushButton:hover {{
    background-color: rgba(0, 212, 255, 0.1);
    border: 1px solid {COLORS['primary']};
    color: {COLORS['text']};
}}

QPushButton:pressed {{
    background-color: {COLORS['primary']};
    color: #000000;
}}

QPushButton:disabled {{
    border-color: #333;
    color: #555;
    background-color: transparent;
}}

/* Group Box (Glass) */
QGroupBox {{
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    margin-top: 24px;
    background-color: rgba(255, 255, 255, 0.02);
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 10px;
    padding: 0 5px;
    color: {COLORS['primary']};
    font-weight: bold;
    background-color: transparent;
}}

QGroupBox::indicator {{
    width: 16px; 
    height: 16px;
}}

/* Sliders */
QSlider::groove:horizontal {{
    height: 6px;
    background: #222222;
    margin: 2px 0;
    border-radius: 3px;
}}

QSlider::handle:horizontal {{
    background: {COLORS['primary']};
    border: 1px solid {COLORS['primary']};
    width: 16px;
    height: 16px;
    margin: -5px 0;
    border-radius: 8px;
}}

/* Progress Bar */
QProgressBar {{
    border: none;
    background-color: #1a1a1a;
    border-radius: 6px;
    text-align: center;
    color: white;
}}

QProgressBar::chunk {{
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {COLORS['primary']}, stop:1 {COLORS['secondary']});
    border-radius: 6px;
}}

/* List Widget */
QListWidget {{
    background-color: rgba(26, 26, 26, 0.5);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 10px;
    padding: 5px;
    outline: none;
}}

QListWidget::item {{
    padding: 0px;
    border-radius: 6px;
    margin-bottom: 4px;
    background-color: rgba(255, 255, 255, 0.02);
}}

QListWidget::item:selected {{
    background-color: rgba(0, 212, 255, 0.15);
    border: 1px solid {COLORS['primary']};
}}

QScrollArea {{
    background: transparent;
    border: none;
}}

QComboBox {{
    background-color: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 5px;
    padding: 5px;
    color: {COLORS['text']};
}}

QComboBox::drop-down {{
    border: none;
}}

QComboBox QAbstractItemView {{
    background-color: #1A1A1A;
    border: 1px solid rgba(255, 255, 255, 0.1);
    selection-background-color: rgba(0, 212, 255, 0.15);
    color: white;
}}

QMenu {{
    background-color: #1A1A1A;
    border: 1px solid rgba(255, 255, 255, 0.1);
    color: white;
    padding: 5px;
}}

QMenu::item {{
    padding: 5px 20px;
    border-radius: 4px;
}}

QMenu::item:selected {{
    background-color: rgba(0, 212, 255, 0.15);
}}

QSpinBox, QDoubleSpinBox {{
    background-color: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 5px;
    padding: 5px;
    color: {COLORS['text']};
}}
"""

def apply_theme(app_or_window):
    app_or_window.setStyleSheet(STYLESHEET)
