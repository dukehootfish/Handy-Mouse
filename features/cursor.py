import time
import cv2
import numpy as np
from helpers import detectors
import config
from helpers.utils import smooth_position
from core.condition import condition

@condition(priority=10)
def check_cursor(hand_data, img, time_now, context):
    if not context.flags.SYSTEM_ACTIVE:
        return False, {}
    if context.flags.SCROLL_ACTIVE or context.flags.VOLUME_ACTIVE:
        return False, {}
    if hasattr(context, 'frame_consumed') and context.frame_consumed:
        return False, {}
        
    return True, {
        'hand_data': hand_data,
        'img': img,
        'time_now': time_now
    }

@check_cursor.event
def move_cursor_event(context, data):
    hand_data = data['hand_data']
    img = data['img']
    time_now = data['time_now']
    
    # Cursor Tracking (Index MCP)
    track_x, track_y = hand_data.index_mcp
    
    # Visual Feedback
    cv2.circle(img, (track_x, track_y), 7, (255, 0, 0), cv2.FILLED)
    
    # Smoothing & Movement
    current_raw = np.array([track_x, track_y])
    
    if context.flags.IS_FIRST_DETECTION or context.flags.MOUSE_LOCATION is None:
        context.flags.MOUSE_LOCATION = current_raw
        context.flags.IS_FIRST_DETECTION = False
    
    context.flags.MOUSE_LOCATION = smooth_position(
        current_raw, context.flags.MOUSE_LOCATION, config.SMOOTHING_FACTOR
    )
    
    context.mouse.move_to(context.flags.MOUSE_LOCATION)
    
    # Handle Clicks
    handle_clicks(context, img, hand_data, time_now)

def handle_clicks(context, img, hand_data, time_now):
    # Visual feedback
    cv2.line(img, hand_data.thumb_tip, hand_data.index_tip, (255, 0, 255), 2)

    cv2.putText(
        img,
        f"Left Click: {context.mouse.left_pressed}",
        (40, 450),
        cv2.FONT_HERSHEY_PLAIN,
        2,
        (255, 0, 0),
        2,
    )

    cv2.putText(
        img,
        f"Right Click: {context.mouse.right_pressed}",
        (40, 500),
        cv2.FONT_HERSHEY_PLAIN,
        2,
        (255, 0, 0),
        2,
    )

    is_left = detectors.is_left_click(hand_data)
    is_right = detectors.is_right_click(hand_data)

    # If both left and right click gestures are detected simultaneously, ignore both
    if is_left and is_right:
        context.mouse.leftRelease()
        context.mouse.rightRelease()
        return

    # Right Click
    if is_right:
        context.mouse.rightClick()
    else:
        context.mouse.rightRelease()

    # Left Click
    if is_left:
        context.flags.LAST_CLICK_DETECTED_TIME = time_now
        if context.flags.LONG_CLICK_START_TIME is None:
            context.flags.LONG_CLICK_START_TIME = context.flags.LAST_CLICK_DETECTED_TIME

        # Check if we have entered long click mode
        if (not context.flags.LONG_CLICK_ACTIVE and 
            (context.flags.LAST_CLICK_DETECTED_TIME - context.flags.LONG_CLICK_START_TIME) >= config.LONG_CLICK_DURATION):
            context.flags.LONG_CLICK_ACTIVE = True
            # Visual indicator for long click could be added here

        context.mouse.leftClick()
    else:
        # If we are in long click mode, check grace period
        if context.flags.LONG_CLICK_ACTIVE:
            if (time_now - context.flags.LAST_CLICK_DETECTED_TIME) <= config.LONG_CLICK_RELEASE_GRACE_PERIOD:
                # Within grace period, maintain click
                pass 
            else:
                # Grace period expired, release
                context.mouse.leftRelease()
                context.flags.LONG_CLICK_ACTIVE = False
                context.flags.LONG_CLICK_START_TIME = None
        else:
            # Normal release
            context.mouse.leftRelease()
            context.flags.LONG_CLICK_START_TIME = None
