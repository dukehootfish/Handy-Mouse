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

                # Process Hand
                img, hand_landmarks, handedness = self.context.tracker.process_frame(img)
                img_h, img_w = img.shape[:2]

                if hand_landmarks:
                    # Orientation Check
                    if not self._check_orientation(img, hand_landmarks, handedness):
                        self._reset_inputs()
                    else:
                        # Create Hand Data
                        hand_data = HandData(hand_landmarks, (img_h, img_w))
                        time_now = time.time()
                        
                        # Run Conditions Loop
                        conditions = ConditionRegistry.get_all()
                        for cond in conditions:
                            # The condition wrapper itself is callable and holds the event func
                            should_run, data = cond(hand_data, img, time_now, self.context)
                            if should_run:
                                if cond.event_func:
                                    cond.event_func(self.context, data)
                                if cond.halt_following:
                                    break

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

    def _check_orientation(self, img, landmarks, handedness):
        palm_facing = is_palm_facing_camera(landmarks, handedness)
        rightside_up = is_palm_rightside_up(landmarks)
        if not (palm_facing and rightside_up):
            if not palm_facing:
                cv2.putText(
                    img,
                    "Palm not facing camera",
                    (40, 100),
                    cv2.FONT_HERSHEY_PLAIN,
                    2,
                    (0, 0, 255),
                    2,
                )

            if not rightside_up:
                cv2.putText(
                    img,
                    "Hand upside down",
                    (40, 140),
                    cv2.FONT_HERSHEY_PLAIN,
                    2,
                    (0, 0, 255),
                    2,
                )

            return False

        return True

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

        if (
            (not self.context.flags.SYSTEM_ACTIVE)
            and self.context.flags.ACTIVATION_PENDING
            and (self.context.flags.ACTIVATION_START_TIME is not None)
        ):
            remaining = max(
                0.0,
                config.TOGGLE_ON_STILLNESS_SECONDS
                - (time.time() - self.context.flags.ACTIVATION_START_TIME),
            )

            cv2.putText(
                img,
                f"Activating in: {remaining:.1f}s",
                (40, 80),
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
