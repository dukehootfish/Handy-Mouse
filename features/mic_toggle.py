import time
import cv2
from helpers import detectors
import config
from core.condition import condition

@condition(priority=3)
def check_mic_mute(hand_data, img, time_now, context):
    if not context.flags.SYSTEM_ACTIVE:
        return False, {}
    if context.flags.SCROLL_ACTIVE or context.flags.VOLUME_ACTIVE:
        return False, {}
        
    is_mute = detectors.is_mic_mute(hand_data)
    
    # Run if mute gesture detected OR if we need to reset the handled flag
    if is_mute or context.flags.MIC_MUTE_HANDLED:
        return True, {
            'hand_data': hand_data,
            'img': img,
            'time_now': time_now,
            'is_mute': is_mute
        }
    return False, {}

@check_mic_mute.event
def toggle_mic_event(context, data):
    hand_data = data['hand_data']
    img = data['img']
    time_now = data['time_now']
    is_mute = data['is_mute']
    
    if is_mute:
        # Consume frame to prevent cursor movement/clicks
        context.frame_consumed = True
        
        if (time_now - context.flags.LAST_MIC_TOGGLE_TIME) > config.MIC_TOGGLE_COOLDOWN:
            if not context.flags.MIC_MUTE_HANDLED:
                context.audio.toggle_mic()
                context.flags.LAST_MIC_TOGGLE_TIME = time_now
                context.flags.MIC_MUTE_HANDLED = True
            
            cv2.putText(
                img,
                "Mic Toggled",
                (hand_data.img_w // 2 - 100, hand_data.img_h // 2),
                cv2.FONT_HERSHEY_PLAIN,
                3,
                (0, 0, 255),
                3,
            )
            
            # Release buttons just in case
            context.mouse.leftRelease()
            context.mouse.rightRelease()
    else:
        # Reset handled state when gesture is released
        context.flags.MIC_MUTE_HANDLED = False
