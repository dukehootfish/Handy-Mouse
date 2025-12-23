"""
Worker threads for HandyMouse application.
"""

from PySide6.QtCore import QThread, Signal
import numpy as np
from core.config_manager import config
from gui.loading_messages import get_step, get_step_count


class VideoWorker(QThread):
    """Worker thread for video capture and processing."""
    
    change_pixmap_signal = Signal(np.ndarray)
    finished_signal = Signal()
    loading_signal = Signal(str, int)  # (message, progress 0-100)

    def __init__(self):
        super().__init__()
        self._run_flag = True
        self.app = None
        self._show_dev = config.get("SHOW_DEVELOPER_LOADING_MESSAGES")

    def _emit_step(self, index: int):
        """Emit a loading step by index."""
        step = get_step(index)
        self.loading_signal.emit(step.get_message(self._show_dev), step.progress)

    def run(self):
        """Main worker thread execution."""
        try:
            self._emit_step(0)  # Connecting to camera
            
            from core.app import HandyMouseApp
            
            self._emit_step(1)  # Loading model
            self._emit_step(2)  # Initializing tracker
            
            self.app = HandyMouseApp()
            
            # Check if we should stop before continuing
            if not self._run_flag:
                return
            
            self._emit_step(3)  # Setting up detection
            self._emit_step(4)  # Finalizing
            self._emit_step(5)  # Ready
            
            # Main processing loop
            while self._run_flag:
                success, img = self.app.process_frame()
                
                if not self._run_flag:
                    break
                
                if success and img is not None:
                    try:
                        self.change_pixmap_signal.emit(img)
                    except RuntimeError:
                        # Signal receiver was destroyed, stop processing
                        break
                
                if self.app.context.flags.EXIT_REQUESTED:
                    self._run_flag = False

        except Exception as e:
            print(f"VideoWorker error: {e}")
        
        finally:
            # Clean up resources
            try:
                if self.app:
                    self.app._cleanup()
                    if hasattr(self.app, 'video_cap') and self.app.video_cap:
                        self.app.video_cap.release()
            except Exception as e:
                print(f"Error during worker cleanup: {e}")
            
            # Emit finished signal (may fail if receiver is destroyed, but that's ok)
            try:
                self.finished_signal.emit()
            except RuntimeError:
                pass  # Receiver was destroyed, ignore

    def stop(self):
        """Signal the worker to stop processing."""
        self._run_flag = False
