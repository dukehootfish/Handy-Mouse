import numpy as np
import config
from core.condition import condition
from helpers.hand_data import HandData
from pynput.keyboard import Key, Controller

keyboard = Controller()


def _get_label(handedness_info):
    if handedness_info and getattr(handedness_info, "classification", None):
        if handedness_info.classification:
            return handedness_info.classification[0].label
    return None


def _infer_secondary_label(frame_labels, main_label, explicit_secondary):
    if explicit_secondary:
        return explicit_secondary
    if not frame_labels:
        return None
    if main_label:
        for label in frame_labels:
            if label and label != main_label:
                return label
    # Fallback: just grab the first available labeled hand
    for label in frame_labels:
        if label:
            return label
    return None

def is_pinch(hand_data):
    """
    Checks if the hand is in a pinch pose (Thumb and Index tips close).
    Uses the configured pinch ratio from config.
    """
    dist = np.hypot(
        hand_data.index_tip[0] - hand_data.thumb_tip[0],
        hand_data.index_tip[1] - hand_data.thumb_tip[1]
    )
    return dist < hand_data.palm_size * config.ZOOM_PINCH_DISTANCE_RATIO

@condition(priority=0, skip_following=True)
def check_zoom(hand_data, img, time_now, context):
    frame_landmarks = getattr(context, "frame_landmarks", []) or []
    frame_handedness = getattr(context, "frame_handedness", []) or []
    frame_labels = [_get_label(h) for h in frame_handedness]
    img_shape = img.shape[:2]

    # 1. Check for Two-Hand Pinch (Zoom Interaction)
    if len(frame_landmarks) >= 2:
        label_0 = frame_labels[0] if len(frame_labels) > 0 else None
        label_1 = frame_labels[1] if len(frame_labels) > 1 else None
        h1 = HandData(
            frame_landmarks[0],
            img_shape,
            label=label_0,
            is_main=(label_0 == context.flags.MAIN_HAND),
        )
        h2 = HandData(
            frame_landmarks[1],
            img_shape,
            label=label_1,
            is_main=(label_1 == context.flags.MAIN_HAND),
        )

        if is_pinch(h1) and is_pinch(h2):
            return True, {
                "mode": "zoom_interaction",
                "h1": h1,
                "h2": h2,
                "time": time_now,
            }

    # 2. Check for Secondary Hand Panning (Only if Zoom is Active)
    if context.flags.ZOOM_ACTIVE and frame_landmarks:
        secondary_label = _infer_secondary_label(
            frame_labels,
            context.flags.MAIN_HAND,
            context.flags.SECONDARY_HAND,
        )
        if secondary_label:
            sec_hand_idx = -1
            for i, label in enumerate(frame_labels):
                if label == secondary_label:
                    sec_hand_idx = i
                    break

            if sec_hand_idx != -1 and sec_hand_idx < len(frame_landmarks):
                h_sec = HandData(
                    frame_landmarks[sec_hand_idx],
                    img_shape,
                    label=secondary_label,
                    is_main=(secondary_label == context.flags.MAIN_HAND),
                )

                if is_pinch(h_sec):
                    if getattr(hand_data, "label", None) == secondary_label:
                        return True, {
                            "mode": "zoom_pan",
                            "hand": hand_data,
                            "time": time_now,
                        }
                    return True, {"mode": "halt", "time": time_now}

    return False, {}

@check_zoom.event
def zoom_handler(context, data):
    mode = data.get("mode")

    if mode == "zoom_interaction":
        context.flags.ZOOM_PAN_POINT = None
        interaction_time = data["time"]
        if (
            interaction_time - context.flags.LAST_ZOOM_TIME
            > config.ZOOM_INTERACTION_RESET_SECONDS
        ):
            context.flags.ZOOM_LAST_DIST = None
            context.flags.ZOOM_DELTA_ACCUM = 0.0
        context.flags.LAST_ZOOM_TIME = interaction_time

        h1 = data["h1"]
        h2 = data["h2"]

        # Calculate distance between wrists
        dist = np.hypot(h1.wrist[0] - h2.wrist[0], h1.wrist[1] - h2.wrist[1])
        # Normalize by image width
        img_w = h1.img_w
        if not img_w:
            return
        norm_dist = dist / img_w

        if context.flags.ZOOM_LAST_DIST is None:
            # First frame of interaction
            context.flags.ZOOM_LAST_DIST = norm_dist
            context.flags.ZOOM_DELTA_ACCUM = 0.0
            # If not active, activate
            if not context.flags.ZOOM_ACTIVE:
                context.flags.ZOOM_ACTIVE = True
                print("Zoom Mode Activated")
            return

        if (
            norm_dist > config.ZOOM_EXIT_THRESHOLD
            or norm_dist < config.ZOOM_MIN_EXIT_THRESHOLD
        ):
            _exit_zoom(context)
            return

        # Interaction continues
        delta = norm_dist - context.flags.ZOOM_LAST_DIST
        context.flags.ZOOM_LAST_DIST = norm_dist
        context.flags.ZOOM_DELTA_ACCUM += delta

        time_since_op = interaction_time - context.flags.LAST_ZOOM_OP_TIME
        accumulated = context.flags.ZOOM_DELTA_ACCUM

        if (
            abs(accumulated) < config.ZOOM_STEP_THRESHOLD
            or time_since_op < config.ZOOM_KEY_COOLDOWN
        ):
            return

        steps = min(
            int(abs(accumulated) / config.ZOOM_STEP_THRESHOLD),
            config.ZOOM_MAX_STEPS_PER_FRAME,
        )

        if steps <= 0:
            return

        direction = 1 if accumulated > 0 else -1
        key_char = "=" if direction > 0 else "-"

        for _ in range(steps):
            _send_zoom_key(key_char)

        context.flags.ZOOM_DELTA_ACCUM -= (
            direction * config.ZOOM_STEP_THRESHOLD * steps
        )
        context.flags.LAST_ZOOM_OP_TIME = interaction_time

    elif mode == "zoom_pan":
        hand = data["hand"]
        target_pos = np.array(getattr(hand, "index_mcp", hand.wrist), dtype=float)
        if context.flags.ZOOM_PAN_POINT is None:
            context.flags.ZOOM_PAN_POINT = target_pos
        else:
            smoothing = config.ZOOM_PAN_SMOOTHING
            context.flags.ZOOM_PAN_POINT = (
                context.flags.ZOOM_PAN_POINT * smoothing
                + target_pos * (1 - smoothing)
            )
        context.mouse.move_to(context.flags.ZOOM_PAN_POINT)

    elif mode == "halt":
        # Intentionally blank – ensures lower-priority conditions don't move the cursor.
        return


def _send_zoom_key(key_char):
    keyboard.press(Key.cmd)
    keyboard.press(key_char)
    keyboard.release(key_char)
    keyboard.release(Key.cmd)


def _exit_zoom(context):
    if not context.flags.ZOOM_ACTIVE:
        return
    context.flags.ZOOM_ACTIVE = False
    context.flags.ZOOM_LAST_DIST = None
    context.flags.ZOOM_DELTA_ACCUM = 0.0
    context.flags.ZOOM_PAN_POINT = None
    context.flags.LAST_ZOOM_OP_TIME = 0.0
    context.flags.LAST_ZOOM_TIME = 0.0
    keyboard.press(Key.cmd)
    keyboard.press(Key.esc)
    keyboard.release(Key.esc)
    keyboard.release(Key.cmd)
    print("Zoom Mode Exited")

