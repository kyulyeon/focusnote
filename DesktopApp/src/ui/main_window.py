from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel, QGroupBox, QCheckBox, QComboBox
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from detection.detect_record import AudioCapture
from audio.audio_thread import AudioCaptureThread


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.audio_capture = AudioCapture()
        self.capture_thread = AudioCaptureThread(self.audio_capture)
        
        self.init_ui()
        
        # Set up status update timer
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(1000)  # Update every second
        
        # Start the capture thread
        self.capture_thread.start()
        
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Focusnote")
        self.setGeometry(100, 100, 300, 400)
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Title
        title = QLabel("Focusnote")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)
        
        # Status section
        status_group = QGroupBox("Status")
        status_layout = QVBoxLayout()
        
        self.status_label = QLabel("Status: Idle")
        status_layout.addWidget(self.status_label)
        
        self.discord_status_label = QLabel("Discord: Not detected")
        status_layout.addWidget(self.discord_status_label)

        self.zoom_status_label = QLabel("Zoom: Not detected")
        status_layout.addWidget(self.zoom_status_label)
        
        status_group.setLayout(status_layout)
        main_layout.addWidget(status_group)
        
        # Settings section
        settings_group = QGroupBox("Settings")
        settings_layout = QVBoxLayout()
        
        self.auto_start_checkbox = QCheckBox("Auto-start monitoring")
        self.auto_start_checkbox.stateChanged.connect(self.on_auto_start_changed)
        settings_layout.addWidget(self.auto_start_checkbox)
        
        settings_group.setLayout(settings_layout)
        main_layout.addWidget(settings_group)
        
        # Push everything to the top
        main_layout.addStretch()
    
    def update_status(self):
        """Periodically check and update all status labels"""
        # Check Discord status
        discord_active, discord_name, discord_cpu = self.audio_capture.detect_discord_call()
        if discord_active:
            self.discord_status_label.setText(f"Discord: Detected ✓ ({discord_cpu:.1f}% CPU)")
            self.discord_status_label.setStyleSheet("color: green;")
        else:
            self.discord_status_label.setText("Discord: Not detected")
            self.discord_status_label.setStyleSheet("color: gray;")
        
        # Check Zoom status
        zoom_active, zoom_name, zoom_cpu = self.audio_capture.detect_zoom_call()
        if zoom_active:
            self.zoom_status_label.setText(f"Zoom: Detected ✓ ({zoom_cpu:.1f}% CPU)")
            self.zoom_status_label.setStyleSheet("color: green;")
        else:
            self.zoom_status_label.setText("Zoom: Not detected")
            self.zoom_status_label.setStyleSheet("color: gray;")
        
        # Check recording status
        is_recording = self.audio_capture.is_recording
        platform = self.audio_capture.active_platform
        
        if is_recording and platform:
            self.status_label.setText(f"Status: Recording {platform.upper()}")
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
        elif self.audio_capture.running:
            self.status_label.setText("Status: Monitoring")
            self.status_label.setStyleSheet("color: blue;")
        else:
            self.status_label.setText("Status: Idle")
            self.status_label.setStyleSheet("color: gray;")
    
    def on_auto_start_changed(self, state):
        """Handle auto-start checkbox change"""
        pass

    def closeEvent(self, event):
        self.status_timer.stop()
        self.capture_thread.stop()
        event.accept()