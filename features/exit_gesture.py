"""
Exit Gesture Feature

Detects when both fists are closed in two-handed mode for a configurable duration,
and requests application exit (equivalent to pressing ESC).
"""
import cv2
from helpers import detectors
from helpers.hand_data import HandData
from core.config_manager import config
from core.condition import condition


def _get_label(handedness_info):
    """Extract label from handedness info."""
    if handedness_info and getattr(handedness_info, "classification", None):
        if handedness_info.classification:
            return handedness_info.classification[0].label
    return None


@condition(priority=1)
def check_double_fist_exit(hand_data, img, time_now, context):
    """
    Check if both hands are making fists in two-handed mode.
    Only triggers in two-handed mode when both fists are closed.
    """
    # Only check in two-handed mode
    if not context.flags.TWO_HANDED_MODE:
        # Reset the timer if we're not in two-handed mode
        if context.flags.DOUBLE_FIST_START_TIME is not None:
            context.flags.DOUBLE_FIST_START_TIME = None
        return False, {}
    
    # Get all hands in the current frame
    frame_landmarks = getattr(context, "frame_landmarks", []) or []
    frame_handedness = getattr(context, "frame_handedness", []) or []
    
    # Need exactly 2 hands for this gesture
    if len(frame_landmarks) < 2:
        # Reset timer if we don't have both hands
        if context.flags.DOUBLE_FIST_START_TIME is not None:
            context.flags.DOUBLE_FIST_START_TIME = None
        return False, {}
    
    # Create HandData for both hands
    img_shape = img.shape[:2]
    frame_labels = [_get_label(h) for h in frame_handedness]
    
    hands = []
    for idx in range(min(2, len(frame_landmarks))):
        label = frame_labels[idx] if idx < len(frame_labels) else None
        h = HandData(
            frame_landmarks[idx],
            img_shape,
            label=label,
            is_main=(label == context.flags.MAIN_HAND),
        )
        hands.append(h)
    
    # Check if both hands are making fists
    both_fists = all(detectors.is_fist(h) for h in hands)
    
    if both_fists:
        return True, {
            'time_now': time_now,
            'img': img,
            'hands': hands,
            'both_fists': True
        }
    else:
        # Reset timer if gesture is not held
        if context.flags.DOUBLE_FIST_START_TIME is not None:
            context.flags.DOUBLE_FIST_START_TIME = None
        return True, {
            'time_now': time_now,
            'img': img,
            'both_fists': False
        }


@check_double_fist_exit.event
def handle_double_fist_exit(context, data):
    """
    Handle the double fist exit gesture timing and trigger exit if held long enough.
    """
    time_now = data['time_now']
    img = data['img']
    both_fists = data['both_fists']
    
    if both_fists:
        # Consume the frame to prevent other interactions
        context.frame_consumed = True
        
        # Start timer on first detection
        if context.flags.DOUBLE_FIST_START_TIME is None:
            context.flags.DOUBLE_FIST_START_TIME = time_now
        
        # Calculate duration
        duration = time_now - context.flags.DOUBLE_FIST_START_TIME
        remaining = max(0.0, config.DOUBLE_FIST_EXIT_DURATION - duration)
        
        # Display countdown on screen
        if remaining > 0:
            cv2.putText(
                img,
                f"Exiting in: {remaining:.1f}s",
                (img.shape[1] // 2 - 150, img.shape[0] // 2),
                cv2.FONT_HERSHEY_PLAIN,
                3,
                (0, 0, 255),
                3,
            )
        else:
            # Trigger exit
            context.flags.EXIT_REQUESTED = True
            cv2.putText(
                img,
                "Exiting HandyMouse...",
                (img.shape[1] // 2 - 200, img.shape[0] // 2),
                cv2.FONT_HERSHEY_PLAIN,
                3,
                (0, 0, 255),
                3,
            )
        
        # Release any held mouse buttons
        context.mouse.leftRelease()
        context.mouse.rightRelease()
    else:
        # Reset if fists are not both closed
        context.flags.DOUBLE_FIST_START_TIME = None

