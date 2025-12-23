"""
Loading messages for camera initialization.

Each loading step has both a user-friendly and developer message variant.
"""

from dataclasses import dataclass
from typing import List


@dataclass
class LoadingStep:
    """A single loading step with both display variants."""
    user_message: str
    dev_message: str
    progress: int  # 0-100
    
    def get_message(self, show_dev: bool) -> str:
        """Get the appropriate message based on settings."""
        return self.dev_message if show_dev else self.user_message


# Ordered loading steps for camera initialization
LOADING_STEPS: List[LoadingStep] = [
    LoadingStep("Connecting to camera", "Opening VideoCapture(0)", 5),
    LoadingStep("Loading model", "Creating TensorFlow Lite XNNPACK delegate for CPU", 25),
    LoadingStep("Initializing tracker", "Initializing MediaPipe Hands solution", 50),
    LoadingStep("Setting up detection", "Allocating tensors and buffers", 75),
    LoadingStep("Finalizing", "Running initial inference warmup", 90),
    LoadingStep("Ready", "Initialization complete", 100),
]


def get_step(index: int) -> LoadingStep:
    """Get a loading step by index, clamped to valid range."""
    return LOADING_STEPS[min(index, len(LOADING_STEPS) - 1)]


def get_step_count() -> int:
    """Get the total number of loading steps."""
    return len(LOADING_STEPS)
