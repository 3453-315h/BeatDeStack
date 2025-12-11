from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSlider, QLabel, 
    QStyle, QFrame, QScrollArea, QSizePolicy
)
from PyQt6.QtCore import Qt, QUrl, QTimer, pyqtSignal
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from src.ui.style import COLORS
from src.ui.waveform import WaveformSelectorWidget
import os

class ClickableLabel(QLabel):
    clicked = pyqtSignal()
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

class TrackWidget(QFrame):
    """Controls for a single stem track (Vol, Mute, Solo)."""
    
    mute_toggled = pyqtSignal(str, bool)  # name, is_muted
    solo_toggled = pyqtSignal(str, bool)  # name, is_soloed
    volume_changed = pyqtSignal(str, int) # name, value
    track_clicked = pyqtSignal(str)       # name - Request to view waveform
    
    def __init__(self, name, player, audio_output, path, parent=None):
        super().__init__(parent)
        self.name = name
        self.path = path  # Store path for waveform loading
        self.player = player
        self.audio_output = audio_output
        self.is_muted = False
        self.is_soloed = False
        self.base_volume = 1.0
        
        self.setup_ui()
        
    def setup_ui(self):
        self.setStyleSheet(f"background-color: {COLORS['surface']}; border-radius: 6px; margin: 2px;")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        
        # Track Name (Clickable)
        name_lbl = ClickableLabel(self.name.capitalize())
        name_lbl.setStyleSheet(f"color: {COLORS['text']}; font-weight: bold; min-width: 60px;")
        name_lbl.setCursor(Qt.CursorShape.PointingHandCursor)
        name_lbl.setToolTip("Click to view waveform")
        name_lbl.clicked.connect(lambda: self.track_clicked.emit(self.path))
        layout.addWidget(name_lbl)
        
        # Volume Slider
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, 100)
        self.slider.setValue(100)
        self.slider.setFixedWidth(120)
        self.slider.valueChanged.connect(self._on_vol_change)
        layout.addWidget(self.slider)
        
        # Mute Button
        self.btn_mute = QPushButton("M")
        self.btn_mute.setCheckable(True)
        self.btn_mute.setFixedSize(24, 24)
        self.btn_mute.setToolTip("Mute")
        self.btn_mute.clicked.connect(self._on_mute)
        self._style_mute()
        layout.addWidget(self.btn_mute)
        
        # Solo Button
        self.btn_solo = QPushButton("S")
        self.btn_solo.setCheckable(True)
        self.btn_solo.setFixedSize(24, 24)
        self.btn_solo.setToolTip("Solo")
        self.btn_solo.clicked.connect(self._on_solo)
        self._style_solo()
        layout.addWidget(self.btn_solo)
        
    def _style_mute(self):
        bg = COLORS['danger'] if self.is_muted else "transparent"
        border = COLORS['danger']
        color = "white" if self.is_muted else COLORS['text_dim']
        self.btn_mute.setStyleSheet(f"""
            QPushButton {{ 
                background-color: {bg}; border: 1px solid {border}; 
                color: {color}; border-radius: 4px; font-weight: bold;
            }}
        """)
        
    def _style_solo(self):
        bg = COLORS['secondary'] if self.is_soloed else "transparent"
        border = COLORS['secondary']
        color = "white" if self.is_soloed else COLORS['text_dim']
        self.btn_solo.setStyleSheet(f"""
            QPushButton {{ 
                background-color: {bg}; border: 1px solid {border}; 
                color: {color}; border-radius: 4px; font-weight: bold;
            }}
        """)

    def _on_vol_change(self, val):
        self.base_volume = val / 100.0
        if not self.is_muted:
            self.audio_output.setVolume(self.base_volume)
        self.volume_changed.emit(self.name, val)

    def _on_mute(self, checked):
        self.is_muted = checked
        self._update_output_volume()
        self._style_mute()
        self.mute_toggled.emit(self.name, checked)
        
    def _on_solo(self, checked):
        self.is_soloed = checked
        self._style_solo()
        self.solo_toggled.emit(self.name, checked)
        
    def _update_output_volume(self):
        """Internal volume update handling mute state."""
        if self.is_muted:
            self.audio_output.setVolume(0)
        else:
            self.audio_output.setVolume(self.base_volume)
            
    def set_effective_mute(self, should_mute):
        """Used by solo logic to silence non-soloed tracks."""
        # Note: We don't change self.is_muted (visual state), just the actual output
        if should_mute:
            self.audio_output.setVolume(0)
        elif not self.is_muted:
            self.audio_output.setVolume(self.base_volume)


class StemPlayerWidget(QWidget):
    """Multi-track player for auditing stems."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # Lists to hold references
        self.tracks = {} # name -> TrackWidget
        self.players = [] # Keep refs to prevent GC
        self.audio_outputs = []
        
        self.duration = 0
        self.is_playing = False
        
        self.setup_ui()
        
        # Sync Timer (Simulated sync check)
        self.sync_timer = QTimer(self)
        self.sync_timer.setInterval(500)
        self.sync_timer.timeout.connect(self._sync_check)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0) # Tight fit
        layout.setSpacing(0)
        
        # 1. Track Area (Scrollable)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet(f"background-color: {COLORS['background']}; border: none;")
        self.scroll.setFixedHeight(120) # Constrain height
        
        self.track_container = QWidget()
        self.track_layout = QVBoxLayout(self.track_container)
        self.track_layout.setContentsMargins(5, 5, 5, 5)
        self.track_layout.setSpacing(2)
        self.track_layout.addStretch() # Push up
        
        self.scroll.setWidget(self.track_container)
        layout.addWidget(self.scroll)
        
        # 2. Transport Controls (Bottom Bar)
        ctrl_frame = QFrame()
        ctrl_frame.setStyleSheet(f"background-color: {COLORS['surface']};")
        ctrl_layout = QHBoxLayout(ctrl_frame) # Main Layout: Left(Buttons), Right(Waveform)
        ctrl_layout.setContentsMargins(5, 5, 5, 5)
        ctrl_layout.setSpacing(10)
        
        # --- Left Column: Buttons (Stacked) ---
        btn_container = QWidget()
        btn_container.setFixedWidth(40) # Fix width to prevent spacing issues
        btn_layout = QVBoxLayout(btn_container)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(5)
        
        # Play/Pause
        self.btn_play = QPushButton()
        self.btn_play.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
        self.btn_play.clicked.connect(self.toggle_playback)
        self.btn_play.setFixedSize(32, 32) # Adjusted size
        self.btn_play.setStyleSheet(f"background-color: rgba(255, 255, 255, 0.05); border-radius: 8px; border: 1px solid rgba(255, 255, 255, 0.1);")
        btn_layout.addWidget(self.btn_play)
        
        # Stop
        btn_stop = QPushButton()
        btn_stop.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaStop))
        btn_stop.clicked.connect(self.stop_playback)
        btn_stop.setFixedSize(32, 32) # Adjusted size
        btn_stop.setStyleSheet(f"background-color: rgba(255, 255, 255, 0.05); border-radius: 8px; border: 1px solid rgba(255, 255, 255, 0.1);")
        btn_layout.addWidget(btn_stop)
        
        ctrl_layout.addWidget(btn_container)
        
        # --- Right Side: Waveform ---
        # Waveform (Input Selection) - Hidden by default, Expands to fill Right
        self.waveform = WaveformSelectorWidget()
        self.waveform.setFixedHeight(120) # Bigger Waveform
        self.waveform.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed) # Force expansion
        self.waveform.setVisible(False)
        ctrl_layout.addWidget(self.waveform, 1)
        
        # Spacer ensures buttons stay left when waveform is hidden
        # Waveform (stretch=1) will crush this spacer (stretch=0) when visible
        ctrl_layout.addStretch(0)
        
        layout.addWidget(ctrl_frame)
        
        self._seeking = False

    def load_input_waveform(self, file_path):
        """Show waveform for input file selection."""
        self.stop_playback()
        self._clear_tracks() # Clear any result stems
        
        # Show waveform
        self.waveform.setVisible(True)
        # self.seek_slider.setVisible(False) 
        
        if file_path:
             self.waveform.load_file(file_path)
        else:
             self.waveform.clear()
             self.waveform.setVisible(False) 

    def _update_volume(self, name, vol_percent):
        # Already handled by individual track signal
        pass

    def _on_track_clicked(self, path):
        """Load the clicked track into the waveform viewer."""
        if os.path.exists(path):
            self.waveform.load_file(path)
            self.waveform.setVisible(True)
        
    def load_stems(self, stem_dict):
        """
        Load stems into the mixer.
        stem_dict: { 'vocab': path, 'drums': path ... }
        """
        self.stop_playback()
        self.waveform.setVisible(False) # Hide input waveform
        # self.seek_slider.setVisible(True) # Slider removed
        self._clear_tracks()
        
        if not stem_dict:
            return

        # Create a player for each stem
        
        if not stem_dict:
            return

        # Create a player for each stem
        first = True
        for name, path in stem_dict.items():
            if not os.path.exists(path):
                continue
                
            player = QMediaPlayer()
            output = QAudioOutput()
            player.setAudioOutput(output)
            player.setSource(QUrl.fromLocalFile(path))
            
            # Connect signals
            if first:
                # Use the first track as the 'master' for time/duration
                player.positionChanged.connect(self._on_position_changed)
                player.durationChanged.connect(self._on_duration_changed)
                player.playbackStateChanged.connect(self._on_state_changed)
                first = False
            
            # Create UI Widget
            widget = TrackWidget(name, player, output, path)
            
            # Mute 'Original' by default
            if name.lower() == "original":
                widget.btn_mute.setChecked(True)
                widget.set_effective_mute(True) # Apply mute logic
                
            widget.solo_toggled.connect(self._handle_solo)
            widget.track_clicked.connect(self._on_track_clicked)
            
            self.track_layout.insertWidget(self.track_layout.count()-1, widget)
            
            # Store refs
            self.tracks[name] = widget
            self.players.append(player)
            self.audio_outputs.append(output)
            
    def _clear_tracks(self):
        # Stop all
        for p in self.players:
            p.stop()
            p.setSource(QUrl())
            
        # Clear UI
        for i in reversed(range(self.track_layout.count())):
            w = self.track_layout.itemAt(i).widget()
            if w:
                w.setParent(None)
                w.deleteLater()
                
        self.track_layout.addStretch() # Restore spacer
        
        self.tracks.clear()
        self.players.clear()
        self.audio_outputs.clear()
        self.duration = 0
        # self.seek_slider.setRange(0, 0)
        # self.time_lbl.setText("00:00 / 00:00")

    def toggle_playback(self):
        if not self.players: return
        
        if self.is_playing:
            for p in self.players: p.pause()
            self.is_playing = False
            self.sync_timer.stop()
        else:
            for p in self.players: p.play()
            self.is_playing = True
            self.sync_timer.start()

    def stop_playback(self):
        for p in self.players: p.stop()
        self.is_playing = False
        self.sync_timer.stop()
        
    def _handle_solo(self, solo_name, is_soloed):
        # If any track is soloed, mute all non-soloed tracks
        # If multiple are soloed, play all of them
        
        # 1. Determine if ANY track is soloed
        any_solo = any(t.is_soloed for t in self.tracks.values())
        
        # 2. Update effective mute state for all
        for name, widget in self.tracks.items():
            if any_solo:
                # If solo mode is active:
                # Play ONLY if this widget IS soloed
                should_silence = not widget.is_soloed
                widget.set_effective_mute(should_silence)
            else:
                # No solo mode: Respect individual mute buttons
                widget.set_effective_mute(False) # Revert to normal mute state

    # --- Transport & Sync ---
    
    # --- Transport & Sync ---
    
    def _on_position_changed(self, pos):
        if not self._seeking:
            pass
            # self.seek_slider.setValue(pos)
            # self._update_time_lbl(pos)
            
    def _on_duration_changed(self, dur):
        self.duration = dur
        # self.seek_slider.setRange(0, dur)
        
    def _on_state_changed(self, state):
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.btn_play.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPause))
            self.is_playing = True
        else:
            self.btn_play.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
            self.is_playing = False

    def _update_time_lbl(self, ms):
        pass
        # cur_sec = (ms // 1000) % 60
        # cur_min = (ms // 60000)
        # tot_sec = (self.duration // 1000) % 60
        # tot_min = (self.duration // 60000)
        # self.time_lbl.setText(f"{cur_min:02}:{cur_sec:02} / {tot_min:02}:{tot_sec:02}")

    def _on_seek_start(self):
        self._seeking = True
        
    def _on_seek_move(self, pos):
        pass
        # self._update_time_lbl(pos)
        
    def _on_seek_end(self):
        pass
        # pos = self.seek_slider.value()
        # for p in self.players:
        #     p.setPosition(pos)
        # self._seeking = False

    def _sync_check(self):
        """Periodically re-align players if they drift."""
        if not self.players or not self.is_playing: return
        
        # Master is player[0]
        master_pos = self.players[0].position()
        
        for i, p in enumerate(self.players[1:], 1):
            diff = abs(p.position() - master_pos)
            if diff > 50: # >50ms drift
                p.setPosition(master_pos)
