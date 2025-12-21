"""
Configuration constants for the HandyMouse application.This module contains settings for video capture, hand tracking landmarks,
and interaction thresholds.
"""

# Camera Settings
CAM_WIDTH = 1280
CAM_HEIGHT = 720

# Hand Landmark Indices (MediaPipe Hands)
# See: https://google.github.io/mediapipe/solutions/hands.html
#hand-landmark-model
THUMB_TIP_IDX = 4
INDEX_FINGER_TIP_IDX = 8
MIDDLE_FINGER_MCP_IDX = 9
MIDDLE_FINGER_TIP_IDX = 12
RING_FINGER_TIP_IDX = 16
PINKY_TIP_IDX = 20
WRIST_IDX = 0
CURSOR_TRACKING_IDX = 5  

# Index finger MCP (metacarpophalangeal joint)
# Interaction Thresholds
RIGHT_CLICK_DISTANCE_RATIO = 0.22
# Fraction of palm size (Wrist to Middle MCP) for a click
LEFT_CLICK_DISTANCE_RATIO = 0.27  
# Fraction of palm size for a click
# Long Click Settings
LONG_CLICK_DURATION = 0.3 
# Seconds to hold a click to trigger long click mode
LONG_CLICK_RELEASE_GRACE_PERIOD = 0.1 
# Seconds of lost detection allowed before releasing long click
MOVEMENT_STABILITY_RATIO = 0.05  
# Fraction of palm size for movement stability
SMOOTHING_FACTOR = 0.25  
# Smoothing factor (0.0 to 1.0). Lower = smoother but more lag.
TOGGLE_COOLDOWN = 2.0  
# Seconds to wait between toggles
TOGGLE_ON_STILLNESS_SECONDS = 1.0  
# Seconds to hold toggle-on gesture steadily before enabling
TOGGLE_ON_WIGGLE_RATIO = 0.12  
# Allowed movement during activation as fraction of palm size
TOGGLE_ON_WIGGLE_MIN_PX = 18.0  
# Minimum pixel wiggle allowed regardless of hand size
TOGGLE_ON_DRIFT_FRAMES = 3  
# Number of consecutive frames outside wiggle before resetting timer
# Screen Mapping
SCREEN_MAPPING_WIDTH_DIVISOR = 1200
SCREEN_MAPPING_HEIGHT_DIVISOR = 675
# Scroll Settings
INVERT_SCROLL_DIRECTION_VERTICAL = True  
# Set to True to invert vertical scroll direction
INVERT_SCROLL_DIRECTION_HORIZONTAL = False  
# Set to True to invert horizontal scroll direction
SCROLL_SPEED_FACTOR = 0.05  
# Multiplier for scroll speed (drag-to-scroll sensitivity)
FIST_DETECTION_LEEWAY = 0.1  
# Seconds to wait before ending scroll mode if fist is lost

# Volume Gesture Settings
VOLUME_PINCH_RATIO = 0.25  
# Max distance between thumb and index tip as fraction of palm size
VOLUME_PINCH_MIN_RATIO = 0.05
# Min distance between thumb and index tip (to avoid pinch)
VOLUME_CURL_RATIO = 1.2   
# Max distance for curled fingers (middle, ring, pinky) as fraction of palm size

# Mic Mute Gesture Settings
MIC_TOGGLE_DISTANCE_RATIO = 0.25  
# Fraction of palm size for pinch detection
MIC_TOGGLE_COOLDOWN = 2.0  
# Seconds to wait between toggles

# Exit Gesture Settings (Two-Handed Mode)
DOUBLE_FIST_EXIT_DURATION = 1.0  
# Seconds to hold both fists closed to exit HandyMouse