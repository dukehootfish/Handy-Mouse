"""
Custom window controls for frameless window.
"""

from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton
from PySide6.QtCore import Qt
from gui.utils import load_stylesheet


class CustomTitleBar(QWidget):
    """
    Window controls (minimize, maximize, close) to be placed in the tab bar.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(32)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.btn_min = self._create_button("─", self._minimize)
        self.btn_max = self._create_button("□", self._toggle_max)
        self.btn_close = self._create_button("✕", self._close)
        self.btn_close.setObjectName("close")
        
        layout.addWidget(self.btn_min)
        layout.addWidget(self.btn_max)
        layout.addWidget(self.btn_close)
        
        self.setStyleSheet(load_stylesheet("title_bar.qss"))

    def _create_button(self, text, callback):
        btn = QPushButton(text)
        btn.setFixedSize(46, 32)
        btn.clicked.connect(callback)
        return btn

    def _minimize(self):
        if self.window():
            self.window().showMinimized()

    def _toggle_max(self):
        if self.window():
            if self.window().isMaximized():
                self.window().showNormal()
                self.btn_max.setText("□")
            else:
                self.window().showMaximized()
                self.btn_max.setText("❐")

    def _close(self):
        if self.window():
            self.window().close()
