"""
HandyMouse Main Entry Point.
"""

import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from helpers.utils import set_high_priority


def main():
    set_high_priority()
    
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # Show splash screen
    from gui.splash_screen import SplashScreen
    splash = SplashScreen()
    splash.show()
    app.processEvents()
    
    # Load main window
    from gui.main_window import MainWindow
    window = MainWindow()
    
    # Transition to main window
    def show_main():
        splash.close()
        window.show()
    
    QTimer.singleShot(300, show_main)
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
