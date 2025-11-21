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
CURSOR_TRACKING_IDX = 5  # Index finger MCP (metacarpophalangeal joint)

# Interaction Thresholds
CLICK_DISTANCE_THRESHOLD = 40  # Distance between thumb and index for a click
MOVEMENT_STABILITY_THRESHOLD = 10  # Minimum distance to register mouse movement

# Screen Mapping
SCREEN_MAPPING_WIDTH_DIVISOR = 1200
SCREEN_MAPPING_HEIGHT_DIVISOR = 675

