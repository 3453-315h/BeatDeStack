import os
import numpy as np
# import soundfile as sf # Replaced by torchaudio
import torch
import torchaudio
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QRectF
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen

from src.ui.style import COLORS

class WaveformLoader(QThread):
    """Background thread to load audio data for visualization."""
    loaded = pyqtSignal(np.ndarray, float) # peaks, duration_sec

    def __init__(self, file_path, width_pixels=1000):
        super().__init__()
        self.file_path = file_path
        self.width_pixels = width_pixels

    def run(self):
        try:
            # Bulletproof loading using ffmpeg CLI directly
            import subprocess
            from src.utils.resource_utils import get_ffmpeg_path
            
            # Get bundled or system ffmpeg path
            ffmpeg_path = get_ffmpeg_path()

            # Command: Decode to float32 linear PCM, mono, 44100Hz, stdout
            # -v error : quiet
            # -i file : input
            # -f f32le : format float 32 little endian
            # -ac 1 : audio channels 1 (mix to mono)
            # -ar 44100 : sample rate
            # - : output to pipe
            cmd = [
                ffmpeg_path, 
                "-v", "error", 
                "-i", self.file_path,
                "-f", "f32le",
                "-ac", "1",
                "-ar", "44100",
                "-"
            ]
            
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            # Run
            try:
                process = subprocess.Popen(
                    cmd, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE,
                    bufsize=10**7, # Large buffer
                    startupinfo=startupinfo
                )
            except FileNotFoundError:
                 raise Exception(f"FFmpeg binary not found at: {ffmpeg_path}")
            
            stdout_data, stderr_data = process.communicate()
            
            if process.returncode != 0:
                raise Exception(f"FFmpeg failed (code {process.returncode}): {stderr_data.decode('utf-8', errors='ignore')}")
            
            # Convert bytes to numpy array
            frames_np = np.frombuffer(stdout_data, dtype=np.float32)
            
            # Calc duration
            sample_rate = 44100
            total_frames = len(frames_np)
            duration = total_frames / sample_rate
            
            # Downsample to ~2000 points max for responsiveness
            target_points = 2000
            
            if total_frames > 0:
                step = max(1, total_frames // target_points)
                
                # Reshape/Strided access
                # Handle remainder
                remainder = total_frames % step
                if remainder > 0:
                    frames_np = frames_np[:-remainder]
                    
                chunks = frames_np.reshape(-1, step)
                # Take max abs value in each chunk (peak detection)
                peaks = np.abs(chunks).max(axis=1)
                
                # Normalize to 0-1
                m = peaks.max()
                if m > 0:
                    peaks = peaks / m
            else:
                peaks = np.array([])

            self.loaded.emit(peaks, duration)
            
        except Exception as e:
            print(f"Waveform Load Error ({self.file_path}): {e}")
            self.loaded.emit(np.array([]), 0)

class WaveformSelectorWidget(QWidget):
    """
    Renders waveform and allows 60s selection.
    """
    selection_changed = pyqtSignal(float, float) # start_time, end_time

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(60)
        self.setMouseTracking(True)
        
        self.file_path = None
        self.peaks = np.array([])
        self.duration = 0
        
        # Selection state
        self.selection_start = 0.0 # Seconds
        self.selection_duration = 30.0 # Seconds (Fixed or default)
        self.is_dragging = False
        
        self.loader = None
        
        self.loading_label = QLabel("Loading Waveform...", self)
        self.loading_label.setStyleSheet(f"color: {COLORS['text_dim']}; background: transparent;")
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loading_label.hide()
        
        # Colors
        self.col_wave = QColor(COLORS['primary'])
        self.col_wave.setAlpha(150)
        
        self.col_select = QColor(COLORS['accent'])
        self.col_select.setAlpha(100) # Highlight overlay
        
        self.col_border = QColor(COLORS['accent'])
        
    def resizeEvent(self, event):
        self.loading_label.resize(self.size())
        super().resizeEvent(event)

    def clear(self):
        """Reset waveform to empty state."""
        self.file_path = None
        self.peaks = np.array([])
        self.duration = 0
        self.loading_label.hide()
        self.update()

    def load_file(self, file_path):
        if self.file_path == file_path:
            return
            
        self.file_path = file_path
        self.peaks = np.array([])
        self.duration = 0
        self.loading_label.show()
        self.update()
        
        # Start thread
        if self.loader and self.loader.isRunning():
            self.loader.wait()
            
        self.loader = WaveformLoader(file_path, width_pixels=self.width())
        self.loader.loaded.connect(self._on_loaded)
        self.loader.start()
        
    def _on_loaded(self, peaks, duration):
        self.peaks = peaks
        self.duration = duration
        self.loading_label.hide()
        
        # Default selection: Middle 30s or start 30s?
        # Let's verify duration.
        if self.duration < 30:
            self.selection_duration = self.duration
            self.selection_start = 0
            
        else:
            self.selection_duration = 30.0 # Default
            self.selection_start = (self.duration - 30) / 2 # Center it
            
        self.selection_changed.emit(self.selection_start, self.selection_start + self.selection_duration)
        self.update()
        
    def get_selection(self):
        """Return start, end in seconds."""
        end = min(self.duration, self.selection_start + self.selection_duration)
        return self.selection_start, end

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Background
        painter.fillRect(self.rect(), QColor(20, 20, 25))
        
        if len(self.peaks) == 0:
            return
            
        w = self.width()
        h = self.height()
        mid_y = h / 2
        
        # Draw Waveform
        count = len(self.peaks)
        if count > 0:
            
            # Bar width
            bar_w = w / count
            
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(self.col_wave))
            
            for i, val in enumerate(self.peaks):
                x = i * bar_w
                # Mirror amplitude
                bar_h = val * h * 0.9
                y = (h - bar_h) / 2
                painter.drawRect(QRectF(x, y, max(1, bar_w), bar_h))
                
        # Draw Selection Overlay
        if self.duration > 0:
            scale = w / self.duration
            sel_x = self.selection_start * scale
            sel_w = self.selection_duration * scale
            
            # Bounds check for drawing
            if sel_x < 0: sel_x = 0
            if sel_x + sel_w > w: sel_w = w - sel_x
            
            rect = QRectF(sel_x, 0, sel_w, h)
            
            # Fill dim everywhere ELSE? Or highlight selection?
            # Highlight selection is standard.
            painter.setBrush(QBrush(self.col_select))
            painter.setPen(QPen(self.col_border, 2))
            painter.drawRect(rect)
            
            # Draw time labels
            start_txt = self._fmt_time(self.selection_start)
            end_txt = self._fmt_time(self.selection_start + self.selection_duration)
            
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(int(sel_x) + 5, 15, start_txt)
            # painter.drawText(int(sel_x + sel_w) - 35, h - 5, end_txt)

    def _fmt_time(self, s):
        m = int(s // 60)
        sec = int(s % 60)
        return f"{m:02}:{sec:02}"

    def mousePressEvent(self, event):
        if self.duration == 0: return
        self.is_dragging = True
        self._update_selection_from_mouse(event.pos().x())
        
    def mouseMoveEvent(self, event):
        if self.is_dragging:
            self._update_selection_from_mouse(event.pos().x())
            
    def mouseReleaseEvent(self, event):
        self.is_dragging = False
        
    def _update_selection_from_mouse(self, x):
        if self.duration == 0: return
        
        w = self.width()
        pct = max(0, min(1, x / w))
        time_point = pct * self.duration
        
        # Center selection on mouse? Or start selection at mouse?
        # User said "select a 60 second segment".
        # Let's center the 60s window on the click for ease use
        
        new_start = time_point - (self.selection_duration / 2)
        
        # Clamp
        if new_start < 0: new_start = 0
        if new_start + self.selection_duration > self.duration:
            new_start = self.duration - self.selection_duration
            
        self.selection_start = new_start
        self.selection_changed.emit(self.selection_start, self.selection_start + self.selection_duration)
        self.update()
