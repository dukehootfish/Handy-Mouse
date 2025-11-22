import numpy as np
import config
from utils import (
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
    Checks for the volume control gesture.
    Complex pose: 'L' shape with index and thumb, consistent distances from thumb to other tips.
    """
    # Distances thumb->each fingertip, normalized by palm_size
    thumb_x, thumb_y = hand_data.thumb_tip

    # Helper to get distance from thumb to point
    def dist_to_thumb(pt):
        return np.hypot(pt[0] - thumb_x, pt[1] - thumb_y)

    d_ti = dist_to_thumb(hand_data.index_tip)
    d_tm = dist_to_thumb(hand_data.middle_tip)
    d_tr = dist_to_thumb(hand_data.ring_tip)
    d_tp = dist_to_thumb(hand_data.pinky_tip)

    ratios = np.array([d_ti, d_tm, d_tr, d_tp], dtype=float) / max(
        1.0, hand_data.palm_size
    )

    near_bounds_ok = np.all(
        (ratios >= config.VOLUME_NEAR_MIN_RATIO)
        & (ratios <= config.VOLUME_NEAR_MAX_RATIO)
    )
    equal_ok = are_distances_similar(ratios, config.VOLUME_EQUALITY_TOL)

    # Colinearity and ordering: index_tip - index_mcp - thumb_tip on a line
    # Vectors relative to Index MCP
    index_mcp_x, index_mcp_y = hand_data.index_mcp

    v_index = np.array(
        [hand_data.index_tip[0] - index_mcp_x, hand_data.index_tip[1] - index_mcp_y],
        dtype=float,
    )
    v_thumb = np.array([thumb_x - index_mcp_x, thumb_y - index_mcp_y], dtype=float)

    angle_deg = angle_between_vectors_deg(v_index, v_thumb)
    colinear_angle_ok = angle_deg >= 150.0

    between_ok = is_colinear_and_between(
        np.array(hand_data.index_tip, dtype=float),
        np.array(hand_data.index_mcp, dtype=float),
        np.array(hand_data.thumb_tip, dtype=float),
        tolerance=config.VOLUME_LINE_TOL * hand_data.palm_size,
    )

    # Thumb below and horizontally near index MCP
    vertical_ok = thumb_y > (
        index_mcp_y + config.VOLUME_MIN_VERTICAL_DIFF * hand_data.palm_size
    )
    horizontal_ok = (
        abs(thumb_x - index_mcp_x) <= config.VOLUME_HORIZONTAL_TOL * hand_data.palm_size
    )

    return (
        near_bounds_ok
        and equal_ok
        and colinear_angle_ok
        and between_ok
        and vertical_ok
        and horizontal_ok
    )


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
