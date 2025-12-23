"""
Main window for HandyMouse application.
"""

import sys
from PySide6.QtWidgets import QMainWindow, QTabWidget, QVBoxLayout, QWidget
from PySide6.QtGui import QFont, QIcon
from PySide6.QtCore import Qt, QEvent, QPoint
from gui.home_page import HomePage
from gui.settings_page import SettingsPage
from gui.custom_title_bar import CustomTitleBar
from gui.utils import load_stylesheet

# Windows native resize support
if sys.platform == "win32":
    import ctypes
    from ctypes import wintypes
    
    # Windows constants
    HTCLIENT = 1
    HTCAPTION = 2
    HTLEFT = 10
    HTRIGHT = 11
    HTTOP = 12
    HTTOPLEFT = 13
    HTTOPRIGHT = 14
    HTBOTTOM = 15
    HTBOTTOMLEFT = 16
    HTBOTTOMRIGHT = 17
    WM_NCHITTEST = 0x0084


class MainWindow(QMainWindow):
    """Main application window."""
    
    RESIZE_MARGIN = 8  # Pixels from edge for resize
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HandyMouse")
        import os
        icon_path = os.path.join(os.path.dirname(__file__), "assets", "appicon.ico")
        self.setWindowIcon(QIcon(icon_path))
        self.resize(1000, 800)
        self.setMinimumSize(800, 600)
        self.setFont(QFont("Segoe UI", 10))
        
        # Frameless window
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        
        # Main container
        self.container = QWidget()
        self.container.setStyleSheet("background-color: #1e1e1e;")
        
        # Layout
        self.main_layout = QVBoxLayout(self.container)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Tabs
        self.tabs = QTabWidget()
        self.home_page = HomePage()
        self.settings_page = SettingsPage()
        
        self.tabs.addTab(self.home_page, "Home")
        self.tabs.addTab(self.settings_page, "Settings")
        
        # Window Controls in Tab Bar
        self.window_controls = CustomTitleBar(self)
        self.tabs.setCornerWidget(self.window_controls, Qt.Corner.TopRightCorner)
        
        self.main_layout.addWidget(self.tabs)
        
        self.setCentralWidget(self.container)
        self.setStyleSheet(load_stylesheet("main.qss"))
        
        # Install event filter on tab bar for dragging
        self.tabs.tabBar().installEventFilter(self)
        
    def closeEvent(self, event):
        # Stop camera and wait for cleanup before closing
        if self.home_page.worker and self.home_page.worker.isRunning():
            # Stop the camera and wait for cleanup
            self.home_page.stop_camera(is_closing=True)
            # Give a bit more time for cleanup to complete
            if self.home_page.worker and self.home_page.worker.isRunning():
                self.home_page.worker.wait(1000)  # Additional wait if needed
        event.accept()

    def eventFilter(self, obj, event):
        """Handle dragging from the tab bar."""
        if obj == self.tabs.tabBar() and event.type() == QEvent.Type.MouseButtonPress:
            if event.button() == Qt.MouseButton.LeftButton:
                # Only drag if not clicking a tab
                if self.tabs.tabBar().tabAt(event.pos()) == -1:
                    if self.windowHandle():
                        self.windowHandle().startSystemMove()
                    return True
        return super().eventFilter(obj, event)

    if sys.platform == "win32":
        def nativeEvent(self, eventType, message):
            """Handle Windows native events for resize and drag."""
            if eventType == b"windows_generic_MSG":
                msg = ctypes.wintypes.MSG.from_address(int(message))
                if msg.message == WM_NCHITTEST:
                    # Get cursor position (screen coordinates)
                    x = msg.lParam & 0xFFFF
                    y = (msg.lParam >> 16) & 0xFFFF
                    
                    window_rect = self.frameGeometry()
                    
                    # Calculate relative position within window frame
                    rel_x = x - window_rect.x()
                    rel_y = y - window_rect.y()
                    
                    w = window_rect.width()
                    h = window_rect.height()
                    m = self.RESIZE_MARGIN
                    
                    # 1. Check resize edges first (priority)
                    if rel_x < m and rel_y < m:
                        return True, HTTOPLEFT
                    elif rel_x > w - m and rel_y < m:
                        return True, HTTOPRIGHT
                    elif rel_x < m and rel_y > h - m:
                        return True, HTBOTTOMLEFT
                    elif rel_x > w - m and rel_y > h - m:
                        return True, HTBOTTOMRIGHT
                    elif rel_x < m:
                        return True, HTLEFT
                    elif rel_x > w - m:
                        return True, HTRIGHT
                    elif rel_y < m:
                        return True, HTTOP
                    elif rel_y > h - m:
                        return True, HTBOTTOM
                    
                    # 2. Check if in title bar area (top ~40px) for dragging
                    TITLE_BAR_HEIGHT = 40
                    if rel_y < TITLE_BAR_HEIGHT:
                        # Convert to local widget coordinates
                        global_pos = QPoint(x, y)
                        local_pos = self.mapFromGlobal(global_pos)
                        
                        # Check if over tab bar
                        tab_bar = self.tabs.tabBar()
                        tab_bar_global = tab_bar.mapToGlobal(QPoint(0, 0))
                        tab_bar_local = self.mapFromGlobal(tab_bar_global)
                        tab_bar_rect = tab_bar.geometry()
                        tab_bar_rect.moveTopLeft(tab_bar_local)
                        
                        if tab_bar_rect.contains(local_pos):
                            # Check if over an actual tab
                            tab_bar_local_pos = tab_bar.mapFromGlobal(global_pos)
                            if tab_bar.tabAt(tab_bar_local_pos) != -1:
                                # Over a tab, let it handle normally
                                return super().nativeEvent(eventType, message)
                        
                        # Check if over window controls
                        if self.window_controls:
                            controls_global = self.window_controls.mapToGlobal(QPoint(0, 0))
                            controls_local = self.mapFromGlobal(controls_global)
                            controls_rect = self.window_controls.geometry()
                            controls_rect.moveTopLeft(controls_local)
                            
                            if controls_rect.contains(local_pos):
                                # Over controls, let them handle normally
                                return super().nativeEvent(eventType, message)
                        
                        # Empty title bar area -> allow dragging
                        return True, HTCAPTION
            
            return super().nativeEvent(eventType, message)
