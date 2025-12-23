import time
import numpy as np
from helpers import detectors
from core.config_manager import config
from core.condition import condition

@condition(priority=0)
def check_activation(hand_data, img, time_now, context):
    label = getattr(hand_data, "label", None)
    if not label:
        return False, {}

    state = context.flags.get_hand_state(label)
    is_pose = detectors.is_activation_pose(hand_data)

    if is_pose or state.pending:
        return True, {
            "hand_data": hand_data,
            "time_now": time_now,
            "is_pose": is_pose,
            "state": state,
        }
    return False, {}

@check_activation.event
def toggle_system_event(context, data):
    """
    Handles the logic for toggling the system active state.
    """
    hand_data = data["hand_data"]
    time_now = data["time_now"]
    is_pose = data["is_pose"]
    state = data["state"]

    if is_pose:
        if (time_now - context.flags.LAST_TOGGLE_TIME) > config.TOGGLE_COOLDOWN:
            if state.is_active:
                # Instant Deactivation
                deactivate_hand(context, state.label, time_now)
                reset_activation_state(state)
            else:
                # Activation Sequence
                process_activation_hold(context, state, time_now, hand_data)
    else:
        if state.pending:
            reset_activation_state(state)

def process_activation_hold(context, state, current_time, hand_data):
    wrist_x, wrist_y = hand_data.wrist
    if not state.pending:
        state.pending = True
        state.start_time = current_time
        state.anchor_x = wrist_x
        state.anchor_y = wrist_y
        state.drift_frames = 0
        print(f"{state.label} hand activation pending...")
    else:
        # Check stillness
        move_dist = np.hypot(
            wrist_x - state.anchor_x,
            wrist_y - state.anchor_y
        )
        allowed_wiggle = max(
            config.TOGGLE_ON_WIGGLE_MIN_PX,
            config.TOGGLE_ON_WIGGLE_RATIO * hand_data.palm_size,
        )
        
        if move_dist > allowed_wiggle:
            state.drift_frames += 1
            if state.drift_frames >= config.TOGGLE_ON_DRIFT_FRAMES:
                # Reset anchor
                state.start_time = current_time
                state.anchor_x = wrist_x
                state.anchor_y = wrist_y
                state.drift_frames = 0
        else:
            state.drift_frames = 0
            
        if (current_time - state.start_time) >= config.TOGGLE_ON_STILLNESS_SECONDS:
            activate_hand(context, state.label, current_time)
            reset_activation_state(state)

def reset_activation_state(state):
    state.reset_pending()

def activate_hand(context, label, current_time):
    flags = context.flags
    state = flags.get_hand_state(label)

    if flags.MAIN_HAND is None:
        flags.MAIN_HAND = label
        flags.SYSTEM_ACTIVE = True
        flags.IS_FIRST_DETECTION = True
        flags.MOUSE_LOCATION = None
        state.is_active = True
        print(f"{label} hand set as MAIN.")
    elif flags.MAIN_HAND == label:
        state.is_active = True
    elif flags.SECONDARY_HAND is None and label != flags.MAIN_HAND:
        flags.SECONDARY_HAND = label
        state.is_active = True
        print(f"{label} hand set as SECONDARY.")
    elif flags.SECONDARY_HAND == label:
        state.is_active = True
    else:
        # Ignore additional hands beyond two roles
        return

    flags.LAST_TOGGLE_TIME = current_time
    update_two_handed_flag(flags)

def deactivate_hand(context, label, current_time):
    flags = context.flags
    state = flags.get_hand_state(label)
    state.is_active = False

    if label == flags.MAIN_HAND:
        flags.MAIN_HAND = None
        flags.SYSTEM_ACTIVE = False
        if flags.SECONDARY_HAND:
            secondary_state = flags.get_hand_state(flags.SECONDARY_HAND)
            secondary_state.is_active = False
            flags.SECONDARY_HAND = None
        flags.TWO_HANDED_MODE = False
        flags.SCROLL_ACTIVE = False
        flags.SCROLL_ORIGIN_X = None
        flags.SCROLL_ORIGIN_Y = None
        flags.LAST_FIST_TIME = None
        flags.LONG_CLICK_ACTIVE = False
        flags.LONG_CLICK_START_TIME = None
        flags.MOUSE_LOCATION = None
        flags.IS_FIRST_DETECTION = True
        context.mouse.leftRelease()
        context.mouse.rightRelease()
        print("Main hand toggled off. All hands deactivated.")
    elif label == flags.SECONDARY_HAND:
        flags.SECONDARY_HAND = None
        print("Secondary hand toggled off.")

    flags.LAST_TOGGLE_TIME = current_time
    update_two_handed_flag(flags)

def update_two_handed_flag(flags):
    flags.TWO_HANDED_MODE = flags.SECONDARY_HAND is not None
