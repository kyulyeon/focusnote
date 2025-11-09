from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QGroupBox, QCheckBox, QFrame, QScrollArea
)
from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtGui import QFont, QPalette, QColor
from detection.detect_record import AudioCapture
from audio.audio_thread import AudioCaptureThread
from transcription.websocket_client import TranscriptionWebSocketClient


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.audio_capture = AudioCapture()
        self.capture_thread = AudioCaptureThread(self.audio_capture)

        # # Setup WebSocket transcription client
        # self.transcription_client = TranscriptionWebSocketClient(
        #     self.audio_capture,
        #     server_url="ws://localhost:17483"
        # )
        # self.transcription_client.start()
        
        self.init_ui()
        self.apply_styles()
        
        # Set up status update timer
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(1000)
        
        # Start the capture thread
        self.capture_thread.start()
        
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("FocusNote")
        self.setGeometry(100, 100, 420, 600)
        self.setMinimumSize(400, 550)
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Header Section
        header_layout = QVBoxLayout()
        header_layout.setSpacing(5)
        
        title = QLabel("FocusNote")
        title_font = QFont()
        title_font.setPointSize(28)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(title)
        
        subtitle = QLabel("Focus on the conversation. We'll handle the notes.")
        subtitle_font = QFont()
        subtitle_font.setPointSize(10)
        subtitle.setFont(subtitle_font)
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #666666;")
        header_layout.addWidget(subtitle)
        
        main_layout.addLayout(header_layout)
        
        # Main Status Card
        status_card = QFrame()
        status_card.setObjectName("statusCard")
        status_card_layout = QVBoxLayout(status_card)
        status_card_layout.setContentsMargins(20, 20, 20, 20)
        status_card_layout.setSpacing(15)
        
        # Status indicator
        status_header = QHBoxLayout()
        self.status_icon = QLabel("●")
        self.status_icon.setStyleSheet("color: #999999; font-size: 24px;")
        status_header.addWidget(self.status_icon)
        
        self.status_label = QLabel("Status: Idle")
        status_font = QFont()
        status_font.setPointSize(14)
        status_font.setBold(True)
        self.status_label.setFont(status_font)
        status_header.addWidget(self.status_label)
        status_header.addStretch()
        
        status_card_layout.addLayout(status_header)
        
        # Separator line
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("background-color: #e0e0e0;")
        status_card_layout.addWidget(line)
        
        # Platform detection section
        platforms_label = QLabel("Active Platforms")
        platforms_label.setStyleSheet("color: #666666; font-weight: bold; font-size: 11px;")
        status_card_layout.addWidget(platforms_label)
        
        # Discord status
        discord_layout = QHBoxLayout()
        self.discord_icon = QLabel("◉")
        self.discord_icon.setStyleSheet("color: #999999; font-size: 18px;")
        discord_layout.addWidget(self.discord_icon)
        
        self.discord_status_label = QLabel("Discord")
        discord_status_font = QFont()
        discord_status_font.setPointSize(12)
        self.discord_status_label.setFont(discord_status_font)
        discord_layout.addWidget(self.discord_status_label)
        discord_layout.addStretch()
        
        self.discord_cpu_label = QLabel("")
        self.discord_cpu_label.setStyleSheet("color: #999999; font-size: 11px;")
        discord_layout.addWidget(self.discord_cpu_label)
        
        status_card_layout.addLayout(discord_layout)
        
        # Zoom status
        zoom_layout = QHBoxLayout()
        self.zoom_icon = QLabel("◉")
        self.zoom_icon.setStyleSheet("color: #999999; font-size: 18px;")
        zoom_layout.addWidget(self.zoom_icon)
        
        self.zoom_status_label = QLabel("Zoom")
        zoom_status_font = QFont()
        zoom_status_font.setPointSize(12)
        self.zoom_status_label.setFont(zoom_status_font)
        zoom_layout.addWidget(self.zoom_status_label)
        zoom_layout.addStretch()
        
        self.zoom_cpu_label = QLabel("")
        self.zoom_cpu_label.setStyleSheet("color: #999999; font-size: 11px;")
        zoom_layout.addWidget(self.zoom_cpu_label)
        
        status_card_layout.addLayout(zoom_layout)
        
        main_layout.addWidget(status_card)
        
        # Settings Section
        settings_group = QGroupBox("Settings")
        settings_group.setObjectName("settingsGroup")
        settings_layout = QVBoxLayout()
        settings_layout.setContentsMargins(15, 20, 15, 15)
        settings_layout.setSpacing(12)
        
        self.auto_start_checkbox = QCheckBox("Auto-start monitoring on launch")
        self.auto_start_checkbox.setStyleSheet("font-size: 12px;")
        self.auto_start_checkbox.stateChanged.connect(self.on_auto_start_changed)
        settings_layout.addWidget(self.auto_start_checkbox)
        
        self.auto_dnd_checkbox = QCheckBox("Enable Do Not Disturb during calls")
        self.auto_dnd_checkbox.setStyleSheet("font-size: 12px;")
        self.auto_dnd_checkbox.setChecked(False)
        settings_layout.addWidget(self.auto_dnd_checkbox)
        
        self.save_transcripts_checkbox = QCheckBox("Save transcripts automatically")
        self.save_transcripts_checkbox.setStyleSheet("font-size: 12px;")
        self.save_transcripts_checkbox.setChecked(False)
        settings_layout.addWidget(self.save_transcripts_checkbox)
        
        settings_group.setLayout(settings_layout)
        main_layout.addWidget(settings_group)
        
        # Action Buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        
        self.view_notes_btn = QPushButton("View Notes Hub")
        self.view_notes_btn.setObjectName("secondaryButton")
        self.view_notes_btn.setMinimumHeight(40)
        buttons_layout.addWidget(self.view_notes_btn)
        
        self.settings_btn = QPushButton("Advanced Settings")
        self.settings_btn.setObjectName("secondaryButton")
        self.settings_btn.setMinimumHeight(40)
        buttons_layout.addWidget(self.settings_btn)
        
        main_layout.addLayout(buttons_layout)
        
        # Push everything to the top
        main_layout.addStretch()
        
        # Footer
        footer = QLabel("Desktop Meeting Assistant")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setStyleSheet("color: #999999; font-size: 10px; padding: 10px;")
        main_layout.addWidget(footer)
    
    def apply_styles(self):
        """Apply modern stylesheet to the application"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            
            QFrame#statusCard {
                background-color: white;
                border-radius: 12px;
                border: 1px solid #e0e0e0;
            }
            
            QGroupBox {
                background-color: white;
                border-radius: 12px;
                border: 1px solid #e0e0e0;
                font-weight: bold;
                font-size: 12px;
                padding-top: 10px;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 5px 10px;
                color: #333333;
            }
            
            QCheckBox {
                spacing: 8px;
                color: #333333;
            }
            
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 2px solid #cccccc;
                background-color: white;
            }
            
            QCheckBox::indicator:checked {
                background-color: #4CAF50;
                border-color: #4CAF50;
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cGF0aCBkPSJNMTAgM0w0LjUgOC41TDIgNiIgc3Ryb2tlPSJ3aGl0ZSIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiLz48L3N2Zz4=);
            }
            
            QCheckBox::indicator:hover {
                border-color: #4CAF50;
            }
            
            QPushButton#secondaryButton {
                background-color: white;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 12px;
                font-weight: bold;
                color: #333333;
            }
            
            QPushButton#secondaryButton:hover {
                background-color: #f8f8f8;
                border-color: #4CAF50;
            }
            
            QPushButton#secondaryButton:pressed {
                background-color: #eeeeee;
            }
        """)
    
    def update_status(self):
        """Periodically check and update all status labels"""
        # Check Discord status
        discord_active, discord_name, discord_cpu = self.audio_capture.detect_discord_call()
        if discord_active:
            self.discord_status_label.setText("Discord")
            self.discord_status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
            self.discord_icon.setStyleSheet("color: #4CAF50; font-size: 18px;")
            self.discord_cpu_label.setText(f"{discord_cpu:.1f}% CPU")
        else:
            self.discord_status_label.setText("Discord")
            self.discord_status_label.setStyleSheet("color: #999999;")
            self.discord_icon.setStyleSheet("color: #999999; font-size: 18px;")
            self.discord_cpu_label.setText("Not detected")
        
        # Check Zoom status
        zoom_active, zoom_name, zoom_cpu = self.audio_capture.detect_zoom_call()
        if zoom_active:
            self.zoom_status_label.setText("Zoom")
            self.zoom_status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
            self.zoom_icon.setStyleSheet("color: #4CAF50; font-size: 18px;")
            self.zoom_cpu_label.setText(f"{zoom_cpu:.1f}% CPU")
        else:
            self.zoom_status_label.setText("Zoom")
            self.zoom_status_label.setStyleSheet("color: #999999;")
            self.zoom_icon.setStyleSheet("color: #999999; font-size: 18px;")
            self.zoom_cpu_label.setText("Not detected")
        
        # Check recording status
        is_recording = self.audio_capture.is_recording
        platform = self.audio_capture.active_platform
        
        if is_recording and platform:
            self.status_label.setText(f"Recording {platform.upper()}")
            self.status_label.setStyleSheet("color: #f44336; font-weight: bold;")
            self.status_icon.setStyleSheet("color: #f44336; font-size: 24px;")
        elif self.audio_capture.running:
            self.status_label.setText("Monitoring")
            self.status_label.setStyleSheet("color: #2196F3; font-weight: bold;")
            self.status_icon.setStyleSheet("color: #2196F3; font-size: 24px;")
        else:
            self.status_label.setText("Idle")
            self.status_label.setStyleSheet("color: #999999; font-weight: bold;")
            self.status_icon.setStyleSheet("color: #999999; font-size: 24px;")
    
    def on_auto_start_changed(self, state):
        """Handle auto-start checkbox change"""
        # Implement auto-start logic here
        pass

    def closeEvent(self, event):
        """Clean up when window is closed"""
        self.status_timer.stop()
        # self.transcription_client.stop()
        self.capture_thread.stop()
        event.accept()