"""
Splash screen for HandyMouse application.
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar, QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPixmap
import os
from gui.utils import load_stylesheet


class SplashScreen(QWidget):
    """A minimal splash screen shown during application startup."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HandyMouse")
        self.setFixedSize(320, 220)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint
        )
        
        self._setup_ui()
        self._center_on_screen()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)
        
        # Icon
        icon_label = QLabel()
        icon_path = os.path.join(os.path.dirname(__file__), "assets", "appicon.png")
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path)
            # Scale to reasonable size (64x64 or maintain aspect ratio)
            scaled_pixmap = pixmap.scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            icon_label.setPixmap(scaled_pixmap)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)
        
        # Title
        self.title_label = QLabel("HandyMouse")
        self.title_label.setFont(QFont("Segoe UI", 20, QFont.Weight.DemiBold))
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title_label)
        
        layout.addStretch()
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(3)
        layout.addWidget(self.progress_bar)
        
        # Status
        self.status_label = QLabel("Loading...")
        self.status_label.setFont(QFont("Segoe UI", 9))
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setObjectName("status")
        layout.addWidget(self.status_label)
        
        self.setStyleSheet(load_stylesheet("splash.qss"))
    
    def _center_on_screen(self):
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.geometry()
            self.move((geo.width() - self.width()) // 2, (geo.height() - self.height()) // 2)
    
    def set_status(self, message: str):
        self.status_label.setText(message)
