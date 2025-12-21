import time
import cv2
from helpers import detectors
from config_manager import config
from core.condition import condition

@condition(priority=1)
def check_scroll(hand_data, img, time_now, context):
    if not context.flags.SYSTEM_ACTIVE:
        return False, {}
    if not getattr(hand_data, "is_main", False):
        return False, {}
        
    is_fist = detectors.is_fist(hand_data)
    
    if is_fist or context.flags.SCROLL_ACTIVE:
        return True, {
            'hand_data': hand_data,
            'img': img,
            'time_now': time_now,
            'is_fist': is_fist
        }
    return False, {}

@check_scroll.event
def manage_scroll_event(context, data):
    hand_data = data['hand_data']
    img = data['img']
    time_now = data['time_now']
    is_fist = data['is_fist']
    
    # State transition logic
    if is_fist:
        if not context.flags.SCROLL_ACTIVE:
            context.flags.SCROLL_ACTIVE = True
            context.flags.SCROLL_ORIGIN_X, context.flags.SCROLL_ORIGIN_Y = hand_data.wrist
            context.flags.LAST_FIST_TIME = None
            # Reset inputs
            context.mouse.leftRelease()
            context.mouse.rightRelease()
    else:
        if context.flags.SCROLL_ACTIVE:
            if context.flags.LAST_FIST_TIME is None:
                context.flags.LAST_FIST_TIME = time_now
            elif (time_now - context.flags.LAST_FIST_TIME) > config.FIST_DETECTION_LEEWAY:
                context.flags.SCROLL_ACTIVE = False
                context.flags.SCROLL_ORIGIN_Y = None
                context.flags.LAST_FIST_TIME = None
                
    if context.flags.SCROLL_ACTIVE:
        process_scroll(context, img, hand_data)

def process_scroll(context, img, hand_data):
    wrist_x, wrist_y = hand_data.wrist

    # Calculate movement from the last anchored position (drag logic)
    # Note: context.flags.SCROLL_ORIGIN variables are used
    
    delta_y = wrist_y - context.flags.SCROLL_ORIGIN_Y
    delta_x = wrist_x - context.flags.SCROLL_ORIGIN_X
    
    scroll_amount_y = delta_y * config.SCROLL_SPEED_FACTOR
    scroll_amount_x = delta_x * config.SCROLL_SPEED_FACTOR
    
    steps_y = int(scroll_amount_y)
    steps_x = int(scroll_amount_x)
    
    dy = 0
    dx = 0
    
    if steps_y != 0:
        dy = -steps_y
        if config.INVERT_SCROLL_DIRECTION_VERTICAL:
            dy = -dy
            
        consumed_pixels_y = steps_y / config.SCROLL_SPEED_FACTOR
        context.flags.SCROLL_ORIGIN_Y += consumed_pixels_y

    if steps_x != 0:
        dx = steps_x
        if config.INVERT_SCROLL_DIRECTION_HORIZONTAL:
            dx = -dx
            
        consumed_pixels_x = steps_x / config.SCROLL_SPEED_FACTOR
        context.flags.SCROLL_ORIGIN_X += consumed_pixels_x

    if dx != 0 or dy != 0:
        context.mouse.scroll(dx, dy)

    # Visuals
    if context.flags.SCROLL_ORIGIN_X is not None:
        origin_pt = (int(context.flags.SCROLL_ORIGIN_X), int(context.flags.SCROLL_ORIGIN_Y))
        current_pt = (int(context.flags.SCROLL_ORIGIN_X), int(wrist_y))

        cv2.circle(img, origin_pt, 7, (0, 255, 255), 2)
        cv2.line(img, origin_pt, current_pt, (0, 255, 255), 2)

        cv2.putText(
            img,
            "Scroll: ON",
            (40, 550),
            cv2.FONT_HERSHEY_PLAIN,
            2,
            (0, 255, 255),
            2,
        )
