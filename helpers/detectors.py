import numpy as np
from core.config_manager import config
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
