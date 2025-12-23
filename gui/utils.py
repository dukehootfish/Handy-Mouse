import cv2
import os
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtCore import Qt

def convert_cv_qt(cv_img, max_width=960, max_height=720):
    """Convert from an opencv image to QPixmap, scaling to fit display."""
    rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
    h, w, ch = rgb_image.shape
    bytes_per_line = ch * w
    # PySide6 uses nested Enums
    convert_to_Qt_format = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
    # Scale to fit the display area while maintaining aspect ratio
    p = convert_to_Qt_format.scaled(max_width, max_height, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
    return QPixmap.fromImage(p)

def load_stylesheet(filename):
    """Load a QSS file from the styles directory."""
    # Assuming styles are in gui/styles/
    base_path = os.path.dirname(os.path.abspath(__file__))
    style_path = os.path.join(base_path, "styles", filename)
    
    try:
        with open(style_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"Error loading stylesheet {filename}: {e}")
        return ""
