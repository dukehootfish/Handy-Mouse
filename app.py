"""
HandyMouse Main Entry Point.

This file initializes and runs the HandyMouse application using the Conditions/Events architecture.
"""

import cv2
import time
import config
from context import HandyContext
from helpers.hand_data import HandData
from helpers.utils import is_palm_facing_camera, is_palm_rightside_up
from core.condition import ConditionRegistry

# Import features to register conditions
import features.activation
import features.scroll
import features.mic_toggle
import features.cursor

class HandyMouseApp:

    def __init__(self):
        self.context = HandyContext()

        # Video Capture
        self.video_cap = cv2.VideoCapture(0)
        self.video_cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.CAM_WIDTH)
        self.video_cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.CAM_HEIGHT)

    def run(self):
        print("HandyMouse started. Press 'Esc' to exit.")
        try:
            while True:
                success, img = self.video_cap.read()
                if not success:
                    print("Failed to grab frame.")
                    break

                # Reset per-frame state
                self.context.frame_consumed = False

                # Process Hands
                img, hand_landmarks_list, handedness_list = self.context.tracker.process_frame(img)
                img_h, img_w = img.shape[:2]
                processed_hand = False

                if hand_landmarks_list:
                    time_now = time.time()
                    conditions = ConditionRegistry.get_all()
                    for idx, hand_landmarks in enumerate(hand_landmarks_list):
                        if getattr(self.context, "frame_consumed", False):
                            break

                        handedness_info = handedness_list[idx] if idx < len(handedness_list) else None
                        label = self._get_hand_label(handedness_info, idx)
                        palm_ok, upright_ok = self._hand_orientation_status(
                            img, hand_landmarks, handedness_info, label, idx
                        )
                        orientation_ok = palm_ok and upright_ok
                        color = self._get_hand_color(label, orientation_ok)
                        self.context.tracker.draw_landmarks(img, hand_landmarks, color)

                        if not orientation_ok:
                            continue

                        processed_hand = True

                        canonical_label = label if label in ("Left", "Right") else None

                        hand_data = HandData(
                            hand_landmarks,
                            (img_h, img_w),
                            label=canonical_label,
                            is_main=(canonical_label == self.context.flags.MAIN_HAND),
                        )

                        for cond in conditions:
                            should_run, data = cond(hand_data, img, time_now, self.context)
                            if should_run:
                                if cond.event_func:
                                    cond.event_func(self.context, data)
                                if cond.halt_following:
                                    break

                        if getattr(self.context, "frame_consumed", False):
                            break

                if hand_landmarks_list and not processed_hand:
                    self._reset_inputs()

                # Status Display
                self._draw_status(img)
                cv2.imshow("HandyMouse - CamOutput", img)
                if cv2.waitKey(1) & 0xFF == 27:
                    break

        except KeyboardInterrupt:
            print("Interrupted by user.")
        finally:
            self._cleanup()
            self.video_cap.release()
            cv2.destroyAllWindows()

    def _reset_inputs(self):
        self.context.mouse.leftRelease()
        self.context.mouse.rightRelease()

    def _draw_status(self, img):
        status_text = "Active" if self.context.flags.SYSTEM_ACTIVE else "Paused"
        status_color = (0, 255, 0) if self.context.flags.SYSTEM_ACTIVE else (0, 0, 255)

        cv2.putText(
            img,
            f"System: {status_text}",
            (40, 50),
            cv2.FONT_HERSHEY_PLAIN,
            2,
            status_color,
            2,
        )

        cv2.putText(
            img,
            f"Main: {self.context.flags.MAIN_HAND or '--'}",
            (40, 80),
            cv2.FONT_HERSHEY_PLAIN,
            2,
            (0, 255, 255),
            2,
        )

        cv2.putText(
            img,
            f"Secondary: {self.context.flags.SECONDARY_HAND or '--'}",
            (40, 110),
            cv2.FONT_HERSHEY_PLAIN,
            2,
            (255, 255, 0),
            2,
        )

        cv2.putText(
            img,
            f"Two-handed: {'On' if self.context.flags.TWO_HANDED_MODE else 'Off'}",
            (40, 140),
            cv2.FONT_HERSHEY_PLAIN,
            2,
            (0, 200, 255),
            2,
        )

        pending_state = self._get_pending_activation_state()
        if pending_state and pending_state.start_time is not None:
            remaining = max(
                0.0,
                config.TOGGLE_ON_STILLNESS_SECONDS
                - (time.time() - pending_state.start_time),
            )

            cv2.putText(
                img,
                f"{pending_state.label} activating in: {remaining:.1f}s",
                (40, 170),
                cv2.FONT_HERSHEY_PLAIN,
                2,
                (0, 255, 255),
                2,
            )

    def _cleanup(self):
        """
        Ensure any synthetic mouse presses are released before exiting.
        """
        self._reset_inputs()

    def _get_hand_label(self, handedness_info, idx):
        if handedness_info and handedness_info.classification:
            label = handedness_info.classification[0].label
            if label == "Left":
                return "Right"
            elif label == "Right":
                return "Left"
            return label
        return f"Hand {idx + 1}"

    def _hand_orientation_status(self, img, landmarks, handedness_info, label, index):
        palm_facing = is_palm_facing_camera(landmarks, handedness_info)
        rightside_up = is_palm_rightside_up(landmarks)
        label_text = label or f"Hand {index + 1}"
        base_y = 200 + index * 60

        if not palm_facing:
            cv2.putText(
                img,
                f"{label_text}: Palm not facing",
                (40, base_y),
                cv2.FONT_HERSHEY_PLAIN,
                2,
                (0, 0, 255),
                2,
            )

        if not rightside_up:
            cv2.putText(
                img,
                f"{label_text}: Hand upside down",
                (40, base_y + 30),
                cv2.FONT_HERSHEY_PLAIN,
                2,
                (0, 0, 255),
                2,
            )

        return palm_facing, rightside_up

    def _get_hand_color(self, label, orientation_ok):
        # Colors in BGR
        COLOR_RED = (0, 0, 255)
        COLOR_GREEN = (0, 255, 0)
        COLOR_YELLOW = (0, 255, 255)
        COLOR_GRAY = (128, 128, 128)

        if not orientation_ok:
            return COLOR_RED

        if label == self.context.flags.MAIN_HAND:
            return COLOR_YELLOW

        if label == self.context.flags.SECONDARY_HAND and self.context.flags.TWO_HANDED_MODE:
            return COLOR_GREEN

        return COLOR_GRAY

    def _get_pending_activation_state(self):
        for state in self.context.flags.HAND_STATES.values():
            if state.pending and state.start_time is not None:
                return state
        return None
