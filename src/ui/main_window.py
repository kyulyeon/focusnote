from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel, QGroupBox, QCheckBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
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
        
        # Start monitoring button
        start_button_group = QGroupBox()
        start_button_layout = QVBoxLayout()

        self.start_btn = QPushButton("Start Monitoring")
        self.start_btn.setStyleSheet("background-color: #4CAF50; color: white; font-size: 14px;")
        self.start_btn.clicked.connect(self.on_start_clicked)
        start_button_layout.addWidget(self.start_btn)

        start_button_group.setLayout(start_button_layout)
        start_button_group.setStyleSheet("QGroupBox { border: none; }")
        main_layout.addWidget(start_button_group)
        
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
        
    def on_start_clicked(self):
        """Handle start button click"""
        pass
    
    def on_auto_start_changed(self, state):
        """Handle auto-start checkbox change"""
        pass