import numpy as np
from config_manager import config
from .utils import (
    are_distances_similar,
    angle_between_vectors_deg,
    is_colinear_and_between,
)


def is_activation_pose(hand_data):
    """
    Checks for the activation/deactivation gesture:
    Ring finger curled, others extended.
    """
    ring_curled = hand_data.ring_to_wrist_dist < hand_data.palm_size
    others_extended = (
        hand_data.index_to_wrist_dist > hand_data.palm_size * 1.5
        and hand_data.middle_to_wrist_dist > hand_data.palm_size * 1.5
        and hand_data.pinky_to_wrist_dist
        > hand_data.palm_size * 1.2  # Pinky is naturally shorter
    )
    return ring_curled and others_extended


def is_volume_pose(hand_data):
    """
    Checks for the volume control gesture:
    - All fingers but index and thumb curled.
    - Distance between index and thumb tips small.
    """
    # Check curled fingers (Middle, Ring, Pinky)
    curl_thresh = hand_data.palm_size * config.VOLUME_CURL_RATIO
    others_curled = (
        hand_data.middle_to_wrist_dist < curl_thresh
        and hand_data.ring_to_wrist_dist < curl_thresh
        and hand_data.pinky_to_wrist_dist < curl_thresh
    )

    if not others_curled:
        return False

    # Check pinch distance
    pinch_dist = np.hypot(
        hand_data.index_tip[0] - hand_data.thumb_tip[0],
        hand_data.index_tip[1] - hand_data.thumb_tip[1]
    )
    
    min_dist = hand_data.palm_size * config.VOLUME_PINCH_MIN_RATIO
    max_dist = hand_data.palm_size * config.VOLUME_PINCH_RATIO
    
    is_pinch = min_dist < pinch_dist < max_dist

    # Index should not be fully curled (to distinguish from fist)
    # In a pinch, index is bent but tip is usually further than curled fingers
    index_not_curled = hand_data.index_to_wrist_dist > (curl_thresh * 0.8)

    return is_pinch and index_not_curled


def is_fist(hand_data):
    """
    Checks for a fist gesture (all fingertips close to wrist).
    """
    curl_threshold = hand_data.palm_size * 1.1
    return (
        hand_data.index_to_wrist_dist < curl_threshold
        and hand_data.middle_to_wrist_dist < curl_threshold
        and hand_data.ring_to_wrist_dist < curl_threshold
        and hand_data.pinky_to_wrist_dist < curl_threshold
    )


def get_pinch_distance(hand_data, finger_tip):
    """Returns distance between thumb and specified finger tip."""
    return np.hypot(
        finger_tip[0] - hand_data.thumb_tip[0], finger_tip[1] - hand_data.thumb_tip[1]
    )


def is_left_click(hand_data):
    dist = get_pinch_distance(hand_data, hand_data.index_tip)
    return dist < config.LEFT_CLICK_DISTANCE_RATIO * hand_data.palm_size


def is_right_click(hand_data):
    dist = get_pinch_distance(hand_data, hand_data.middle_tip)
    undist = get_pinch_distance(hand_data, hand_data.ring_tip)
    return dist < config.RIGHT_CLICK_DISTANCE_RATIO * hand_data.palm_size and undist > config.MIC_TOGGLE_DISTANCE_RATIO * hand_data.palm_size


def is_mic_mute(hand_data):
    """
    Checks for mic mute gesture (Ring + Middle + Thumb pinch).
    """
    ring_dist = get_pinch_distance(hand_data, hand_data.ring_tip)
    middle_dist = get_pinch_distance(hand_data, hand_data.middle_tip)

    threshold = config.MIC_TOGGLE_DISTANCE_RATIO * hand_data.palm_size
    return ring_dist < threshold and middle_dist < threshold
