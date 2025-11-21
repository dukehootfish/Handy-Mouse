"""
Utility functions for the HandyMouse application.
"""

import numpy as np

def is_stable_movement(true_loc: np.ndarray, virtual_loc: np.ndarray, threshold: float = 10.0) -> bool:
    """
    Determines if the movement is significant enough to be considered stable.
    
    This helps in reducing jitter by ignoring small, unintentional movements.

    Args:
        true_loc (np.ndarray): The current raw location of the tracking point.
        virtual_loc (np.ndarray): The last registered stable location.
        threshold (float): The distance threshold for considering movement valid. 
                           Defaults to 10.0.

    Returns:
        bool: True if the distance between true_loc and virtual_loc exceeds the threshold,
              False otherwise.
    """
    distance = np.linalg.norm(true_loc - virtual_loc)
    return distance > threshold

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
        
    # MediaPipe Handedness:
    # Label is 'Left' or 'Right'. 
    # NOTE: MediaPipe assumes input is mirrored by default for 'Left'/'Right' labels 
    # if using front camera, but let's check the standard behavior.
    # For a standard webcam view (mirrored):
    # - Real Right Hand shows up as "Right" label (usually).
    # 
    # Palm Facing Camera Logic:
    # X coordinates increase from left to right.
    # Right Hand (Palm): Thumb (Left) < Index < Pinky (Right) => Index.x < Pinky.x
    # Left Hand (Palm): Pinky (Left) < Index < Thumb (Right) => Pinky.x < Index.x
    #
    # If Back of Hand is showing:
    # Right Hand (Back): Pinky (Left) < Index < Thumb (Right) => Pinky.x < Index.x
    # Left Hand (Back): Thumb (Left) < Index < Pinky (Right) => Index.x < Pinky.x
    
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
            
    return is_palm