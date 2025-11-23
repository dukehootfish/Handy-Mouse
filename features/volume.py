import time
import cv2
import numpy as np
from helpers import detectors
import config
from helpers.utils import wrap_angle_delta, clamp
from core.condition import condition

@condition(priority=2)
def check_volume(hand_data, img, time_now, context):
    if not context.flags.SYSTEM_ACTIVE:
        return False, {}
    
    if context.flags.SCROLL_ACTIVE:
        return False, {}

    is_pose = detectors.is_volume_pose(hand_data)
    
    if is_pose or context.flags.VOLUME_ACTIVE:
        return True, {
            'hand_data': hand_data,
            'img': img,
            'time_now': time_now,
            'is_pose': is_pose
        }
    return False, {}

@check_volume.event
def manage_volume_event(context, data):
    hand_data = data['hand_data']
    img = data['img']
    time_now = data['time_now']
    is_pose = data['is_pose']
    
    # State Transition
    if is_pose:
        context.flags.VOLUME_CONFIRM_COUNT += 1
        context.flags.VOLUME_POSE_LAST_SEEN_TIME = time_now
    else:
        context.flags.VOLUME_CONFIRM_COUNT = 0
        if context.flags.VOLUME_ACTIVE:
            if context.flags.VOLUME_POSE_LAST_SEEN_TIME is None:
                context.flags.VOLUME_POSE_LAST_SEEN_TIME = time_now
            elif (time_now - context.flags.VOLUME_POSE_LAST_SEEN_TIME) > config.VOLUME_EXIT_LEEWAY:
                context.flags.VOLUME_ACTIVE = False
                context.flags.VOLUME_POSE_LAST_SEEN_TIME = None
                
    if (not context.flags.VOLUME_ACTIVE and 
        context.flags.VOLUME_CONFIRM_COUNT >= config.VOLUME_ENTER_CONFIRM_FRAMES):
        
        context.flags.VOLUME_ACTIVE = True
        context.flags.VOLUME_POSE_LAST_SEEN_TIME = time_now
        
        # Initialize volume state
        thumb_x, thumb_y = hand_data.thumb_tip
        idx_x, idx_y = hand_data.index_mcp
        context.flags.VOLUME_THETA_PREV = np.arctan2(thumb_y - idx_y, thumb_x - idx_x)
        context.flags.VOLUME_PERCENT_CURRENT = context.audio.get_master_volume()
        context.flags.VOLUME_PERCENT_APPLIED = context.flags.VOLUME_PERCENT_CURRENT
        
        # Reset inputs
        context.mouse.leftRelease()
        context.mouse.rightRelease()
        
    if context.flags.VOLUME_ACTIVE:
        process_volume_control(context, img, hand_data)

def process_volume_control(context, img, hand_data):
    thumb_x, thumb_y = hand_data.thumb_tip
    idx_x, idx_y = hand_data.index_mcp
    theta = np.arctan2(thumb_y - idx_y, thumb_x - idx_x)
    
    delta = wrap_angle_delta(theta - context.flags.VOLUME_THETA_PREV)
    delta_deg = float(np.degrees(delta))
    
    if abs(delta_deg) < config.VOLUME_ANGLE_DEADZONE_DEG:
        delta_deg = 0.0

    if config.VOLUME_DIRECTION_REVERSED:
        delta_deg = -delta_deg

    context.flags.VOLUME_PERCENT_CURRENT += delta_deg / config.VOLUME_DEG_PER_PERCENT
    context.flags.VOLUME_PERCENT_CURRENT = clamp(context.flags.VOLUME_PERCENT_CURRENT, 0.0, 100.0)

    # Smoothing
    alpha = config.VOLUME_SMOOTHING_ALPHA
    if context.flags.VOLUME_PERCENT_APPLIED is None:
        context.flags.VOLUME_PERCENT_APPLIED = context.flags.VOLUME_PERCENT_CURRENT
    else:
        context.flags.VOLUME_PERCENT_APPLIED = (
            1.0 - alpha
        ) * context.flags.VOLUME_PERCENT_APPLIED + alpha * context.flags.VOLUME_PERCENT_CURRENT

    context.audio.set_master_volume(context.flags.VOLUME_PERCENT_APPLIED)
    context.flags.VOLUME_THETA_PREV = theta

    # UI Overlay
    vol_text = f"Volume: {int(round(context.flags.VOLUME_PERCENT_APPLIED))}%"
    cv2.putText(img, vol_text, (40, 590), cv2.FONT_HERSHEY_PLAIN, 2, (0, 255, 0), 2)
    
    bar_x, bar_y = 40, 610
    bar_w, bar_h = 300, 16
    
    cv2.rectangle(img, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), (0, 255, 0), 2)
    filled_w = int(bar_w * (context.flags.VOLUME_PERCENT_APPLIED / 100.0))
    cv2.rectangle(img, (bar_x, bar_y), (bar_x + filled_w, bar_y + bar_h), (0, 255, 0), cv2.FILLED)
