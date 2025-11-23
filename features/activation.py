import time
import numpy as np
from helpers import detectors
import config
from core.condition import condition

@condition(priority=0)
def check_activation(hand_data, img, time_now, context):
    is_pose = detectors.is_activation_pose(hand_data)
    
    # We want to run if the pose is detected OR if we have a pending activation to potentially cancel
    if is_pose or context.flags.ACTIVATION_PENDING:
        return True, {
            'hand_data': hand_data, 
            'time_now': time_now,
            'is_pose': is_pose
        }
    return False, {}

@check_activation.event
def toggle_system_event(context, data):
    """
    Handles the logic for toggling the system active state.
    """
    hand_data = data['hand_data']
    time_now = data['time_now']
    is_pose = data['is_pose']
    
    if is_pose:
        # Check cooldown
        if (time_now - context.flags.LAST_TOGGLE_TIME) > config.TOGGLE_COOLDOWN:
            if not context.flags.SYSTEM_ACTIVE:
                # Activation Sequence
                process_activation_hold(context, time_now, hand_data)
            else:
                # Instant Deactivation
                context.flags.SYSTEM_ACTIVE = False
                context.flags.LAST_TOGGLE_TIME = time_now
                reset_activation_state(context)
                context.mouse.leftRelease()
                context.mouse.rightRelease()
                print(f"System Active: {context.flags.SYSTEM_ACTIVE}")
    else:
        # Reset pending activation if pose broken
        if context.flags.ACTIVATION_PENDING:
            reset_activation_state(context)

def process_activation_hold(context, current_time, hand_data):
    wrist_x, wrist_y = hand_data.wrist
    if not context.flags.ACTIVATION_PENDING:
        context.flags.ACTIVATION_PENDING = True
        context.flags.ACTIVATION_START_TIME = current_time
        context.flags.ACTIVATION_ANCHOR_X = wrist_x
        context.flags.ACTIVATION_ANCHOR_Y = wrist_y
        context.flags.ACTIVATION_DRIFT_FRAMES = 0
        print("Activation pending: hold gesture steady...")
    else:
        # Check stillness
        move_dist = np.hypot(
            wrist_x - context.flags.ACTIVATION_ANCHOR_X, 
            wrist_y - context.flags.ACTIVATION_ANCHOR_Y
        )
        allowed_wiggle = max(
            config.TOGGLE_ON_WIGGLE_MIN_PX,
            config.TOGGLE_ON_WIGGLE_RATIO * hand_data.palm_size,
        )
        
        if move_dist > allowed_wiggle:
            context.flags.ACTIVATION_DRIFT_FRAMES += 1
            if context.flags.ACTIVATION_DRIFT_FRAMES >= config.TOGGLE_ON_DRIFT_FRAMES:
                # Reset anchor
                context.flags.ACTIVATION_START_TIME = current_time
                context.flags.ACTIVATION_ANCHOR_X = wrist_x
                context.flags.ACTIVATION_ANCHOR_Y = wrist_y
                context.flags.ACTIVATION_DRIFT_FRAMES = 0
        else:
            context.flags.ACTIVATION_DRIFT_FRAMES = 0
            
        if (current_time - context.flags.ACTIVATION_START_TIME) >= config.TOGGLE_ON_STILLNESS_SECONDS:
            context.flags.SYSTEM_ACTIVE = True
            context.flags.LAST_TOGGLE_TIME = current_time
            reset_activation_state(context)
            print(f"System Active: {context.flags.SYSTEM_ACTIVE}")

def reset_activation_state(context):
    context.flags.ACTIVATION_PENDING = False
    context.flags.ACTIVATION_START_TIME = None
    context.flags.ACTIVATION_ANCHOR_X = None
    context.flags.ACTIVATION_ANCHOR_Y = None
    context.flags.ACTIVATION_DRIFT_FRAMES = 0
