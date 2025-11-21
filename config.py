"""
Configuration constants for the HandyMouse application.

This module contains settings for video capture, hand tracking landmarks,
and interaction thresholds.
"""

# Camera Settings
CAM_WIDTH = 1280
CAM_HEIGHT = 720

# Hand Landmark Indices (MediaPipe Hands)
# See: https://google.github.io/mediapipe/solutions/hands.html#hand-landmark-model
THUMB_TIP_IDX = 4
INDEX_FINGER_TIP_IDX = 8
MIDDLE_FINGER_MCP_IDX = 9
MIDDLE_FINGER_TIP_IDX = 12
RING_FINGER_TIP_IDX = 16
PINKY_TIP_IDX = 20
WRIST_IDX = 0
CURSOR_TRACKING_IDX = 5  # Index finger MCP (metacarpophalangeal joint)

# Interaction Thresholds
RIGHT_CLICK_DISTANCE_RATIO = 0.22  # Fraction of palm size (Wrist to Middle MCP) for a click
LEFT_CLICK_DISTANCE_RATIO = 0.27   # Fraction of palm size for a click
MOVEMENT_STABILITY_RATIO = 0.05  # Fraction of palm size for movement stability
SMOOTHING_FACTOR = 0.2  # Smoothing factor (0.0 to 1.0). Lower = smoother but more lag.
TOGGLE_COOLDOWN = 2.0  # Seconds to wait between toggles

# Screen Mapping
SCREEN_MAPPING_WIDTH_DIVISOR = 1200
SCREEN_MAPPING_HEIGHT_DIVISOR = 675

# Scroll Settings
INVERT_SCROLL_DIRECTION = False # Set to True to invert scroll direction
SCROLL_SPEED_FACTOR = 0.003 # Multiplier for scroll speed
SCROLL_DEADZONE = 120 # Pixels of movement required to start scrolling
FIST_DETECTION_LEEWAY = 0.1 # Seconds to wait before ending scroll mode if fist is lost