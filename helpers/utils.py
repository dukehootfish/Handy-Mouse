"""
Utility functions for the HandyMouse application.
"""

import numpy as np
import sys
import os
import ctypes


def smooth_position(target_pos: np.ndarray, current_pos: np.ndarray, alpha: float = 0.5) -> np.ndarray:
    """
    Smooths the position movement using Linear Interpolation (Lerp).

    Args:
        target_pos (np.ndarray): The new target position (raw input).
        current_pos (np.ndarray): The current smoothed position.
        alpha (float): The smoothing factor (0 < alpha <= 1).
                       Higher alpha means more responsiveness, lower alpha means more smoothing.

    Returns:
        np.ndarray: The new smoothed position.
    """
    return current_pos + alpha * (target_pos - current_pos)

def is_palm_facing_camera(hand_landmarks, handedness_info):
    """
    Determines if the palm is facing the camera.
    
    Uses the relative position of the Index MCP and Pinky MCP joints combined with 
    handedness information to determine orientation.
    
    Args:
        hand_landmarks: The detected hand landmarks.
        handedness_info: The MediaPipe handedness classification object.
        
    Returns:
        bool: True if the palm is likely facing the camera, False otherwise.
    """
    if not handedness_info:
        return True # Default to True if uncertain to avoid locking out
        
    
    label = handedness_info.classification[0].label # "Left" or "Right"
    
    # Landmark indices
    INDEX_MCP = 5
    PINKY_MCP = 17
    
    index_mcp_x = hand_landmarks.landmark[INDEX_MCP].x
    pinky_mcp_x = hand_landmarks.landmark[PINKY_MCP].x
    
    is_palm = False
    
    if label == "Right":
        # Expect Index < Pinky for Palm
        if index_mcp_x < pinky_mcp_x:
            is_palm = True
    else: # Label == "Left"
        # Expect Pinky < Index for Palm
        if pinky_mcp_x < index_mcp_x:
            is_palm = True

    # When the hand is upside down, MediaPipe's handedness logic appears flipped.
    # In that case, invert the palm assumption so gestures remain intuitive.
    if hand_landmarks and not is_palm_rightside_up(hand_landmarks):
        is_palm = not is_palm
            
    return is_palm

def is_palm_rightside_up(hand_landmarks):
    """
    Determines if the palm is upside down based on wrist and finger MCP positions.
    
    Args:
        hand_landmarks: The detected hand landmarks.
        
    Returns:
        bool: True if the palm is likely right side up, False otherwise.
    """
    # Landmark indices
    WRIST = 0
    MIDDLE_MCP = 9
    
    wrist_y = hand_landmarks.landmark[WRIST].y
    middle_mcp_y = hand_landmarks.landmark[MIDDLE_MCP].y
    
    # If wrist is below both MCPs, palm is right side up
    if wrist_y > middle_mcp_y:
        return True
    return False
    
def are_distances_similar(distances: np.ndarray, tolerance_ratio: float) -> bool:
    """
    Checks whether a set of distances are roughly equal within a relative tolerance.

    Args:
        distances (np.ndarray): Array of positive distances.
        tolerance_ratio (float): Maximum allowed (max deviation / mean).

    Returns:
        bool: True if the distances are similar, False otherwise.
    """
    if distances.size == 0:
        return False
    mean_val = float(np.mean(distances))
    if mean_val <= 0.0:
        return False
    max_dev = float(np.max(np.abs(distances - mean_val)))
    return (max_dev / mean_val) <= tolerance_ratio

def angle_between_vectors_deg(v1: np.ndarray, v2: np.ndarray) -> float:
    """
    Computes the signed smallest angle between two 2D vectors in degrees.

    Args:
        v1 (np.ndarray): Vector 1 as [x, y].
        v2 (np.ndarray): Vector 2 as [x, y].

    Returns:
        float: Angle in degrees in [0, 180].
    """
    v1 = np.asarray(v1, dtype=float)
    v2 = np.asarray(v2, dtype=float)
    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)
    if norm1 == 0.0 or norm2 == 0.0:
        return 0.0
    # Use arctan2 of cross and dot for numerical stability
    cross = v1[0] * v2[1] - v1[1] * v2[0]
    dot = v1[0] * v2[0] + v1[1] * v2[1]
    angle_rad = np.abs(np.arctan2(cross, dot))
    return float(np.degrees(angle_rad))

def wrap_angle_delta(delta_rad: float) -> float:
    """
    Wraps an angle delta in radians to the range [-pi, pi].
    """
    two_pi = 2.0 * np.pi
    wrapped = (delta_rad + np.pi) % two_pi - np.pi
    return float(wrapped)

def is_colinear_and_between(a: np.ndarray, b: np.ndarray, c: np.ndarray, tolerance: float) -> bool:
    """
    Checks if point b lies on the line segment a-c within an absolute tolerance.

    Args:
        a, b, c (np.ndarray): Points as [x, y].
        tolerance (float): Absolute tolerance on (ab + bc - ac).

    Returns:
        bool: True if b is between a and c (approximately colinear).
    """
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    c = np.asarray(c, dtype=float)
    ab = np.linalg.norm(a - b)
    bc = np.linalg.norm(b - c)
    ac = np.linalg.norm(a - c)
    return abs((ab + bc) - ac) <= tolerance

def clamp(value: float, min_value: float, max_value: float) -> float:
    """
    Clamps a numeric value to a given range.
    """
    return float(max(min_value, min(max_value, value)))

def set_high_priority():
    """ Set the priority of the process to high. """
    try:
        sys.getwindowsversion()
    except AttributeError:
        # Not on Windows
        return

    # HIGH_PRIORITY_CLASS = 0x00000080
    # ABOVE_NORMAL_PRIORITY_CLASS = 0x00008000
    pid = os.getpid()
    handle = ctypes.windll.kernel32.OpenProcess(0x0100, False, pid) # PROCESS_SET_INFORMATION
    if handle:
        ctypes.windll.kernel32.SetPriorityClass(handle, 0x00000080)
        ctypes.windll.kernel32.CloseHandle(handle)
        print("Process priority set to HIGH.")
    else:
        print("Failed to set process priority.")

