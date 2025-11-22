import cv2

import time

import numpy as np

import config

from hand_tracker import HandTracker

from mouse_controller import MouseController

from audio_controller import AudioController

from hand_data import HandData

import detectors

from utils import (
    is_palm_facing_camera,
    is_palm_rightside_up,
    smooth_position,
    wrap_angle_delta,
    clamp,
)


class HandyMouseApp:

    def __init__(self):

        # Initialize Controllers

        self.tracker = HandTracker(max_num_hands=1)

        self.mouse_ctrl = MouseController()

        self.vol_ctrl = AudioController()

        # Video Capture

        self.video_cap = cv2.VideoCapture(0)

        self.video_cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.CAM_WIDTH)

        self.video_cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.CAM_HEIGHT)

        # State - System

        self.system_active = False

        self.last_toggle_time = 0

        self.activation_pending = False

        self.activation_start_time = None

        self.activation_anchor_x = None

        self.activation_anchor_y = None

        self.activation_drift_frames = 0

        # State - Mouse Smoothing

        self.mouse_location = np.array([0, 0])

        self.is_first_detection = True

        # State - Volume

        self.volume_active = False

        self.volume_confirm_count = 0

        self.volume_pose_last_seen_time = None

        self.volume_theta_prev = 0.0

        self.volume_percent_current = 0.0

        self.volume_percent_applied = None

        # State - Mic Mute

        self.mic_mute_handled = False

        self.last_mic_toggle_time = 0

        # State - Scroll

        self.scroll_active = False

        self.scroll_origin_x = None

        self.scroll_origin_y = None

        self.fist_lost_time = None

        # Gesture Mapping (Priority Order)

        # These return True if they consumed the frame

        self.mode_handlers = [self.handle_volume_mode, self.handle_scroll_mode]

    def run(self):

        print("HandyMouse started. Press 'Esc' to exit.")

        try:

            while True:

                success, img = self.video_cap.read()

                if not success:

                    print("Failed to grab frame.")

                    break

                # Process Hand

                img, hand_landmarks, handedness = self.tracker.prcoess_frame(img)

                img_h, img_w = img.shape[:2]

                if hand_landmarks:

                    # Orientation Check

                    if not self._check_orientation(img, hand_landmarks, handedness):

                        self._reset_inputs()

                    else:

                        # Create Hand Data

                        hand_data = HandData(hand_landmarks, (img_h, img_w))

                        # Check Activation/Deactivation

                        self._handle_system_toggle(hand_data)

                        if self.system_active:

                            # Try specific modes

                            frame_consumed = False

                            for handler in self.mode_handlers:

                                if handler(img, hand_data):

                                    frame_consumed = True

                                    break

                            # Default to Cursor Mode

                            if not frame_consumed:

                                self.handle_cursor_mode(img, hand_data)

                # Status Display

                self._draw_status(img)

                cv2.imshow("HandyMouse - CamOutput", img)

                if cv2.waitKey(1) & 0xFF == 27:

                    break

        except KeyboardInterrupt:

            print("Interrupted by user.")

        finally:

            self.video_cap.release()

            cv2.destroyAllWindows()

    def _reset_inputs(self):

        self.mouse_ctrl.leftRelease()

        self.mouse_ctrl.rightRelease()

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

    def _handle_system_toggle(self, hand_data):

        if detectors.is_activation_pose(hand_data):

            current_time = time.time()

            if (current_time - self.last_toggle_time) > config.TOGGLE_COOLDOWN:

                if not self.system_active:

                    # Activation Sequence

                    self._process_activation_hold(current_time, hand_data)

                else:

                    # Instant Deactivation

                    self.system_active = False

                    self.last_toggle_time = current_time

                    self._reset_activation_state()

                    self._reset_inputs()

                    print(f"System Active: {self.system_active}")

        else:

            # Reset pending activation if pose broken

            if self.activation_pending:

                self._reset_activation_state()

    def _process_activation_hold(self, current_time, hand_data):

        wrist_x, wrist_y = hand_data.wrist

        if not self.activation_pending:

            self.activation_pending = True

            self.activation_start_time = current_time

            self.activation_anchor_x = wrist_x

            self.activation_anchor_y = wrist_y

            self.activation_drift_frames = 0

            print("Activation pending: hold gesture steady...")

        else:

            # Check stillness

            move_dist = np.hypot(
                wrist_x - self.activation_anchor_x, wrist_y - self.activation_anchor_y
            )

            allowed_wiggle = max(
                config.TOGGLE_ON_WIGGLE_MIN_PX,
                config.TOGGLE_ON_WIGGLE_RATIO * hand_data.palm_size,
            )

            if move_dist > allowed_wiggle:

                self.activation_drift_frames += 1

                if self.activation_drift_frames >= config.TOGGLE_ON_DRIFT_FRAMES:

                    # Reset anchor

                    self.activation_start_time = current_time

                    self.activation_anchor_x = wrist_x

                    self.activation_anchor_y = wrist_y

                    self.activation_drift_frames = 0

            else:

                self.activation_drift_frames = 0

            if (
                current_time - self.activation_start_time
            ) >= config.TOGGLE_ON_STILLNESS_SECONDS:

                self.system_active = True

                self.last_toggle_time = current_time

                self._reset_activation_state()

                print(f"System Active: {self.system_active}")

    def _reset_activation_state(self):

        self.activation_pending = False

        self.activation_start_time = None

        self.activation_anchor_x = None

        self.activation_anchor_y = None

        self.activation_drift_frames = 0

    def handle_volume_mode(self, img, hand_data):

        current_time = time.time()

        is_pose = detectors.is_volume_pose(hand_data)

        # State transition logic

        if is_pose:

            self.volume_confirm_count += 1

            self.volume_pose_last_seen_time = current_time

        else:

            self.volume_confirm_count = 0

            if self.volume_active:

                if self.volume_pose_last_seen_time is None:

                    self.volume_pose_last_seen_time = current_time

                elif (
                    current_time - self.volume_pose_last_seen_time
                    > config.VOLUME_EXIT_LEEWAY
                ):

                    self.volume_active = False

                    self.volume_pose_last_seen_time = None

        if (
            not self.volume_active
            and self.volume_confirm_count >= config.VOLUME_ENTER_CONFIRM_FRAMES
        ):

            self.volume_active = True

            self.volume_pose_last_seen_time = current_time

            # Initialize volume state

            thumb_x, thumb_y = hand_data.thumb_tip

            idx_x, idx_y = hand_data.index_mcp

            self.volume_theta_prev = np.arctan2(thumb_y - idx_y, thumb_x - idx_x)

            self.volume_percent_current = self.vol_ctrl.get_master_volume()

            self.volume_percent_applied = self.volume_percent_current

            self._reset_inputs()

        if self.volume_active:

            self._process_volume_control(img, hand_data)

            return True  # Consumed

        return False

    def _process_volume_control(self, img, hand_data):

        thumb_x, thumb_y = hand_data.thumb_tip

        idx_x, idx_y = hand_data.index_mcp

        theta = np.arctan2(thumb_y - idx_y, thumb_x - idx_x)

        delta = wrap_angle_delta(theta - self.volume_theta_prev)

        delta_deg = float(np.degrees(delta))

        if abs(delta_deg) < config.VOLUME_ANGLE_DEADZONE_DEG:

            delta_deg = 0.0

        if config.VOLUME_DIRECTION_REVERSED:

            delta_deg = -delta_deg

        self.volume_percent_current += delta_deg / config.VOLUME_DEG_PER_PERCENT

        self.volume_percent_current = clamp(self.volume_percent_current, 0.0, 100.0)

        # Smoothing

        alpha = config.VOLUME_SMOOTHING_ALPHA

        if self.volume_percent_applied is None:

            self.volume_percent_applied = self.volume_percent_current

        else:

            self.volume_percent_applied = (
                1.0 - alpha
            ) * self.volume_percent_applied + alpha * self.volume_percent_current

        self.vol_ctrl.set_master_volume(self.volume_percent_applied)

        self.volume_theta_prev = theta

        # UI Overlay

        vol_text = f"Volume: {int(round(self.volume_percent_applied))}%"

        cv2.putText(img, vol_text, (40, 590), cv2.FONT_HERSHEY_PLAIN, 2, (0, 255, 0), 2)

        bar_x, bar_y = 40, 610

        bar_w, bar_h = 300, 16

        cv2.rectangle(
            img, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), (0, 255, 0), 2
        )

        filled_w = int(bar_w * (self.volume_percent_applied / 100.0))

        cv2.rectangle(
            img,
            (bar_x, bar_y),
            (bar_x + filled_w, bar_y + bar_h),
            (0, 255, 0),
            cv2.FILLED,
        )

    def handle_scroll_mode(self, img, hand_data):

        current_time = time.time()

        is_fist = detectors.is_fist(hand_data)

        if is_fist:

            if not self.scroll_active:

                self.scroll_active = True

                self.scroll_origin_x, self.scroll_origin_y = hand_data.wrist

                self.fist_lost_time = None

                self._reset_inputs()

        else:

            if self.scroll_active:

                if self.fist_lost_time is None:

                    self.fist_lost_time = current_time

                elif current_time - self.fist_lost_time > config.FIST_DETECTION_LEEWAY:

                    self.scroll_active = False

                    self.scroll_origin_y = None

                    self.fist_lost_time = None

        if self.scroll_active:

            self._process_scroll(img, hand_data)

            return True

        return False

    def _process_scroll(self, img, hand_data):

        wrist_x, wrist_y = hand_data.wrist

        delta_y = wrist_y - self.scroll_origin_y

        distance = abs(delta_y) - config.SCROLL_DEADZONE

        if distance > 0:

            direction = 1 if delta_y < 0 else -1

            dy = int(max(1, min(10, distance * config.SCROLL_SPEED_FACTOR))) * direction

            if config.INVERT_SCROLL_DIRECTION:

                dy = -dy

            self.mouse_ctrl.scroll(dy)

        # Visuals

        if self.scroll_origin_x is not None:

            origin_pt = (int(self.scroll_origin_x), int(self.scroll_origin_y))

            current_pt = (int(self.scroll_origin_x), int(wrist_y))

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

    def handle_cursor_mode(self, img, hand_data):

        # Cursor Tracking (Index MCP)

        track_x, track_y = hand_data.index_mcp

        # Visual Feedback

        cv2.circle(img, (track_x, track_y), 7, (255, 0, 0), cv2.FILLED)

        # Smoothing & Movement

        current_raw = np.array([track_x, track_y])

        if self.is_first_detection:

            self.mouse_location = current_raw

            self.is_first_detection = False

        self.mouse_location = smooth_position(
            current_raw, self.mouse_location, config.SMOOTHING_FACTOR
        )

        self.mouse_ctrl.move_to(self.mouse_location)

        # Handle Mic Mute Toggle and Click Suppression

        is_mute = detectors.is_mic_mute(hand_data)

        current_time = time.time()

        if (
            is_mute
            and current_time - self.last_mic_toggle_time > config.MIC_TOGGLE_COOLDOWN
        ):

            if not self.mic_mute_handled:

                self.vol_ctrl.toggle_mic()

                self.last_mic_toggle_time = current_time

                self.mic_mute_handled = True

            cv2.putText(
                img,
                "Mic Toggled",
                (hand_data.img_w // 2 - 100, hand_data.img_h // 2),
                cv2.FONT_HERSHEY_PLAIN,
                3,
                (0, 0, 255),
                3,
            )

            # Suppress clicks and release buttons

            self.mouse_ctrl.leftRelease()

            self.mouse_ctrl.rightRelease()
            return

        else:

            self.mic_mute_handled = False

        # Clicks

        self._handle_clicks(img, hand_data)

    def _handle_clicks(self, img, hand_data):

        # Visual feedback

        cv2.line(img, hand_data.thumb_tip, hand_data.index_tip, (255, 0, 255), 2)

        cv2.putText(
            img,
            f"Left Click: {self.mouse_ctrl.left_pressed}",
            (40, 450),
            cv2.FONT_HERSHEY_PLAIN,
            2,
            (255, 0, 0),
            2,
        )

        cv2.putText(
            img,
            f"Right Click: {self.mouse_ctrl.right_pressed}",
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

            self.mouse_ctrl.leftRelease()

            self.mouse_ctrl.rightRelease()
            return

        # Right Click

        if is_right:

            self.mouse_ctrl.rightClick()

        else:

            self.mouse_ctrl.rightRelease()

        # Left Click

        if is_left:

            self.mouse_ctrl.leftClick()

        else:

            self.mouse_ctrl.leftRelease()

    def _draw_status(self, img):

        status_text = "Active" if self.system_active else "Paused"

        status_color = (0, 255, 0) if self.system_active else (0, 0, 255)

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
            (not self.system_active)
            and self.activation_pending
            and (self.activation_start_time is not None)
        ):

            remaining = max(
                0.0,
                config.TOGGLE_ON_STILLNESS_SECONDS
                - (time.time() - self.activation_start_time),
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
