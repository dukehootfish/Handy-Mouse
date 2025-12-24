"""
HandyMouse Main Entry Point.
"""

import sys
import time
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
    
    start_time = time.time()

    # Load main window
    from gui.main_window import MainWindow
    window = MainWindow()
    
    # Transition to main window
    def show_main():
        splash.close()
        window.show()
    
    # Calculate remaining time to ensure splash is shown for at least 1.5 seconds
    elapsed = time.time() - start_time
    min_splash_ms = 1500
    remaining_ms = max(0, int(min_splash_ms - (elapsed * 1000)))
    
    QTimer.singleShot(remaining_ms, show_main)
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
