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
