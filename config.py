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
TOGGLE_ON_STILLNESS_SECONDS = 2.0  # Seconds to hold toggle-on gesture steadily before enabling
TOGGLE_ON_WIGGLE_RATIO = 0.12  # Allowed movement during activation as fraction of palm size
TOGGLE_ON_WIGGLE_MIN_PX = 18.0  # Minimum pixel wiggle allowed regardless of hand size
TOGGLE_ON_DRIFT_FRAMES = 3  # Number of consecutive frames outside wiggle before resetting timer

# Screen Mapping
SCREEN_MAPPING_WIDTH_DIVISOR = 1200
SCREEN_MAPPING_HEIGHT_DIVISOR = 675

# Scroll Settings
INVERT_SCROLL_DIRECTION = False # Set to True to invert scroll direction
SCROLL_SPEED_FACTOR = 0.003 # Multiplier for scroll speed
SCROLL_DEADZONE = 120 # Pixels of movement required to start scrolling
FIST_DETECTION_LEEWAY = 0.1 # Seconds to wait before ending scroll mode if fist is lost

# Volume Gesture Settings
# Distances between thumb tip and other fingertips should be near and similar
VOLUME_NEAR_MIN_RATIO = 0.15  # * palm_size
VOLUME_NEAR_MAX_RATIO = 0.35  # * palm_size
VOLUME_EQUALITY_TOL = 0.15    # max deviation from mean / mean
VOLUME_LINE_TOL = 0.10        # absolute tolerance as ratio of palm_size for colinearity check

# Thumb relation to index MCP
VOLUME_MIN_VERTICAL_DIFF = 0.06   # * palm_size (thumb below index MCP by at least this)
VOLUME_HORIZONTAL_TOL = 0.25      # * palm_size (thumb horizontally close to index MCP)

# Pose entry/exit timing
VOLUME_ENTER_CONFIRM_FRAMES = 5   # consecutive frames to enter
VOLUME_EXIT_LEEWAY = 0.15         # seconds to tolerate pose loss before exit

# Rotation to volume mapping
VOLUME_ANGLE_DEADZONE_DEG = 2.0   # ignore tiny jitter
VOLUME_DEG_PER_PERCENT = 3.0      # degrees of rotation per 1% volume change
VOLUME_SMOOTHING_ALPHA = 0.4      # EMA smoothing for applied volume (0..1)
VOLUME_DIRECTION_REVERSED = False # swap direction if needed