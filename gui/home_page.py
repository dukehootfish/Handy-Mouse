"""
Home page for HandyMouse application.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, 
    QHBoxLayout, QFrame, QProgressBar, QStyleOptionProgressBar
)
from PySide6.QtCore import Slot, Qt, QTimer, QElapsedTimer, QRect, QPointF
from PySide6.QtGui import QPixmap, QPainter, QColor, QBrush, QLinearGradient, QPolygon
import numpy as np
from gui.workers import VideoWorker
from gui.utils import convert_cv_qt


class AnimatedProgressBar(QProgressBar):
    """A progress bar with an animated striped pattern on the filled portion."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._offset = 0
        self._animation_timer = QTimer(self)
        self._animation_timer.timeout.connect(self._update_animation)
        self._animation_timer.start(30)  # ~33 FPS for smoother animation
        
        # Stripe configuration
        self._stripe_width = 20
        self._cycle_length = self._stripe_width * 2

    def _update_animation(self):
        self._offset = (self._offset + 1) % self._cycle_length
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            rect = self.rect()
            
            # Draw background
            painter.fillRect(rect, QColor("#1a1a1a"))
            
            # Calculate width of progress
            if self.maximum() > 0:
                progress_ratio = self.value() / self.maximum()
            else:
                progress_ratio = 0
                
            progress_width = int(rect.width() * progress_ratio)
            
            if progress_width > 0:
                progress_rect = QRect(0, 0, progress_width, rect.height())
                
                # Base color with gradient for more visual appeal
                gradient = QLinearGradient(0, 0, progress_width, 0)
                gradient.setColorAt(0, QColor("#3a8fff"))
                gradient.setColorAt(1, QColor("#5ba0ff"))
                painter.fillRect(progress_rect, QBrush(gradient))
                
                # Draw moving stripes overlay
                painter.setClipRect(progress_rect)
                
                # Brighter, more visible stripes
                stripe_color = QColor(255, 255, 255, 80)  # Increased opacity from 30 to 80
                
                # Draw diagonal stripes
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(stripe_color)
                
                # Shift x by offset - start before visible area to ensure smooth animation
                start_x = -self._stripe_width + self._offset
                
                for i in range(start_x, progress_width + rect.height(), self._cycle_length):
                    # Diagonal stripe: /
                    points = [
                        QPointF(i, rect.height()),
                        QPointF(i + self._stripe_width, rect.height()),
                        QPointF(i + self._stripe_width + rect.height(), 0),
                        QPointF(i + rect.height(), 0)
                    ]
                    
                    polygon = QPolygon([p.toPoint() for p in points])
                    painter.drawPolygon(polygon)
        finally:
            painter.end()


class HomePage(QWidget):
    """Home page with camera feed and controls."""
    
    STEP_DISPLAY_DELAY_MS = 500  # Delay before showing a loading step
    PROGRESS_SMOOTH_INTERVAL_MS = 16  # ~60fps animation
    PROGRESS_SMOOTH_STEP = 2  # Progress increment per tick
    
    def __init__(self):
        super().__init__()
        self._setup_ui()
        self.worker = None
        self._is_closing = False  # Flag to track if widget is being destroyed
        
        # Loading state
        self._pending_message = None
        self._pending_progress = 0
        self._current_display_progress = 0
        self._step_timer = QElapsedTimer()
        
        # Timers
        self._delay_timer = QTimer(self)
        self._delay_timer.setSingleShot(True)
        self._delay_timer.timeout.connect(self._show_pending_step)
        
        self._smooth_timer = QTimer(self)
        self._smooth_timer.timeout.connect(self._animate_progress)
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        
        # Video display
        self.video_label = QLabel("Camera stopped")
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setMinimumSize(800, 600)
        self.video_label.setStyleSheet("""
            background-color: #0a0a0a;
            color: #606060;
            border: 1px solid #252525;
            border-radius: 4px;
        """)
        layout.addWidget(self.video_label, 1)
        
        # Loading bar (hidden by default)
        self.loading_container = QFrame()
        self.loading_container.setStyleSheet("background-color: transparent;")
        loading_layout = QVBoxLayout(self.loading_container)
        loading_layout.setContentsMargins(0, 0, 0, 0)
        loading_layout.setSpacing(4)
        
        self.loading_label = QLabel("Initializing...")
        self.loading_label.setStyleSheet("color: #606060;")
        
        self.loading_progress = AnimatedProgressBar()
        self.loading_progress.setRange(0, 100)
        self.loading_progress.setValue(0)
        self.loading_progress.setTextVisible(False)
        self.loading_progress.setFixedHeight(4)
        
        loading_layout.addWidget(self.loading_label)
        loading_layout.addWidget(self.loading_progress)
        self.loading_container.hide()
        layout.addWidget(self.loading_container)
        
        # Controls
        controls = QHBoxLayout()
        controls.setSpacing(12)
        
        self.toggle_btn = QPushButton("Start")
        self.toggle_btn.setObjectName("start")
        self.toggle_btn.setMinimumHeight(40)
        self.toggle_btn.setMinimumWidth(120)
        self.toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_btn.clicked.connect(self.toggle_camera)
        
        controls.addStretch()
        controls.addWidget(self.toggle_btn)
        controls.addStretch()
        
        layout.addLayout(controls)
    
    def _show_pending_step(self):
        """Display the pending loading step after delay."""
        if self._pending_message:
            self.loading_label.setText(self._pending_message)
    
    def _animate_progress(self):
        """Smoothly animate progress bar toward target."""
        if self._current_display_progress < self._pending_progress:
            self._current_display_progress = min(
                self._current_display_progress + self.PROGRESS_SMOOTH_STEP,
                self._pending_progress
            )
            self.loading_progress.setValue(self._current_display_progress)
        elif self._current_display_progress >= 100:
            self._smooth_timer.stop()
    
    def _reset_loading_state(self):
        """Reset all loading-related state."""
        self._pending_message = None
        self._pending_progress = 0
        self._current_display_progress = 0
        self._delay_timer.stop()
        self._smooth_timer.stop()
        self.loading_progress.setValue(0)
    
    def toggle_camera(self):
        if self.worker and self.worker.isRunning():
            self.stop_camera()
        else:
            self.start_camera()

    def start_camera(self):
        if self.worker is not None:
            return
        
        self._reset_loading_state()
        
        self.video_label.setText("Starting...")
        self.toggle_btn.setEnabled(False)
        self.toggle_btn.setText("Starting...")
        
        self.loading_container.show()
        self._step_timer.start()
        
        # Start smooth animation timer
        self._smooth_timer.start(self.PROGRESS_SMOOTH_INTERVAL_MS)
        
        self.worker = VideoWorker()
        self.worker.change_pixmap_signal.connect(self.update_image)
        self.worker.finished_signal.connect(self.on_worker_finished)
        self.worker.loading_signal.connect(self.on_loading_update)
        self.worker.start()

    def stop_camera(self, is_closing=False):
        if not self.worker:
            return
        
        self._is_closing = is_closing
        
        # Only update UI if not closing (widgets might be destroyed)
        if not is_closing:
            try:
                self.video_label.setText("Stopping...")
                self.toggle_btn.setEnabled(False)
                self.toggle_btn.setText("Stopping...")
                # Immediately hide loading container and reset loading state
                self._reset_loading_state()
                self.loading_container.hide()
            except RuntimeError:
                pass  # Widget already destroyed
        
        self._smooth_timer.stop()
        
        # Disconnect signals to prevent crashes during window closure
        if is_closing:
            try:
                self.worker.change_pixmap_signal.disconnect()
                self.worker.finished_signal.disconnect()
                self.worker.loading_signal.disconnect()
            except (RuntimeError, TypeError):
                pass  # Already disconnected or invalid
        
        # Stop the worker
        self.worker.stop()
        
        if is_closing:
            # Wait for thread to finish (with timeout)
            if self.worker.isRunning():
                self.worker.wait(5000)
            
            self.worker = None

    @Slot(np.ndarray)
    def update_image(self, cv_img):
        # Safety check: don't update UI if widget is being destroyed
        if self._is_closing or not self.isVisible():
            return
        
        try:
            if self.loading_container.isVisible():
                self.loading_container.hide()
                self._smooth_timer.stop()
                self.toggle_btn.setEnabled(True)
                self.toggle_btn.setText("Stop")
                self.toggle_btn.setObjectName("stop")
                self.toggle_btn.style().unpolish(self.toggle_btn)
                self.toggle_btn.style().polish(self.toggle_btn)
            
            qt_img = convert_cv_qt(cv_img)
            self.video_label.setPixmap(qt_img)
        except RuntimeError:
            # Widget was destroyed, ignore
            pass

    @Slot()
    def on_worker_finished(self):
        # Safety check: don't update UI if widget is being destroyed
        if self._is_closing:
            self.worker = None
            return
        
        try:
            self._reset_loading_state()
            
            self.toggle_btn.setText("Start")
            self.toggle_btn.setObjectName("start")
            self.toggle_btn.style().unpolish(self.toggle_btn)
            self.toggle_btn.style().polish(self.toggle_btn)
            self.toggle_btn.setEnabled(True)
            
            self.video_label.setText("Camera stopped")
            self.video_label.setPixmap(QPixmap())
            self.loading_container.hide()
            
            self.worker = None
        except RuntimeError:
            # Widget was destroyed, just clean up worker reference
            self.worker = None
    
    @Slot(str, int)
    def on_loading_update(self, message: str, progress: int):
        """Handle loading progress updates with delay and smooth animation."""
        # Safety check: don't update UI if widget is being destroyed
        if self._is_closing or not self.isVisible():
            return
        
        try:
            elapsed = self._step_timer.elapsed()
            
            # Update target progress (animation will catch up smoothly)
            self._pending_progress = progress
            self._pending_message = message
            
            # Only show the message after delay, unless it's the first one
            if elapsed < self.STEP_DISPLAY_DELAY_MS and self._current_display_progress > 0:
                # Start/restart the delay timer
                remaining = self.STEP_DISPLAY_DELAY_MS - elapsed
                self._delay_timer.start(max(1, remaining))
            else:
                # Show immediately
                self.loading_label.setText(message)
            
            # Reset step timer for next step
            self._step_timer.restart()
        except RuntimeError:
            # Widget was destroyed, ignore
            pass
