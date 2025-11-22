"""
HandyMouse Main Application.

This is the entry point for the HandyMouse application. It captures video from the webcam,
tracks hand movements using MediaPipe, and controls the mouse cursor based on hand gestures.
"""

import cv2
import numpy as np
import time
from hand_tracker import HandTracker
from mouse_controller import MouseController
from utils import (
    smooth_position,
    is_palm_facing_camera,
    is_palm_rightside_up,
    are_distances_similar,
    angle_between_vectors_deg,
    wrap_angle_delta,
    is_colinear_and_between,
    clamp,
)
from audio_controller import AudioController
import config

def main():
    """
    Main application loop.
    """
    # Initialize Hand Tracker
    tracker = HandTracker(max_num_hands=1)

    # Initialize Mouse Controller
    mouse_ctrl = MouseController()
    # Initialize Volume Controller
    vol_ctrl = AudioController()

    # Initialize Video Capture
    video_cap = cv2.VideoCapture(0)
    video_cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.CAM_WIDTH)
    video_cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.CAM_HEIGHT)

    # State variables for mouse smoothing
    mouse_location = np.array([0, 0])
    
    # Flag to initialize mouse_location on first detection
    is_first_detection = True

    # Toggle state
    system_active = False
    last_toggle_time = 0
    activation_pending = False
    activation_start_time = None
    activation_anchor_x = None
    activation_anchor_y = None
    activation_drift_frames = 0

    # Scroll state
    scroll_active = False
    scroll_origin_x = None
    scroll_origin_y = None
    fist_lost_time = None
    # Volume state
    volume_active = False
    volume_confirm_count = 0
    volume_theta_prev = 0.0
    volume_percent_current = 0.0
    volume_percent_applied = None
    volume_pose_last_seen_time = None

    print("HandyMouse started. Press 'Esc' to exit.")

    try:
        while True:
            success, img = video_cap.read()
            if not success:
                print("Failed to grab frame.")
                break

            # Process frame for hand tracking
            img, hand_landmarks, handedness = tracker.process_frame(img)
            img_h, img_w = img.shape[:2]

            if hand_landmarks:
                palm_facing_camera = is_palm_facing_camera(hand_landmarks, handedness)
                palm_rightside_up = is_palm_rightside_up(hand_landmarks)
                orientation_valid = palm_facing_camera and palm_rightside_up

                if not orientation_valid:
                    mouse_ctrl.leftRelease()
                    mouse_ctrl.rightRelease()
                    if not palm_facing_camera:
                        cv2.putText(img, "Palm not facing camera", (40, 100), 
                                cv2.FONT_HERSHEY_PLAIN, 2, (0, 0, 255), 2)
                    if not palm_rightside_up:
                        cv2.putText(img, "Hand upside down", (40, 140), 
                                cv2.FONT_HERSHEY_PLAIN, 2, (0, 0, 255), 2)
                else:
                    ring_tip_x, ring_tip_y = tracker.get_landmark_pos(
                            hand_landmarks, config.RING_FINGER_TIP_IDX, (img_h, img_w)
                    )
                    wrist_x, wrist_y = tracker.get_landmark_pos(
                        hand_landmarks, config.WRIST_IDX, (img_h, img_w)
                    )
                    # Using Middle Finger MCP as a reference for palm scale
                    palm_base_x, palm_base_y = tracker.get_landmark_pos(
                        hand_landmarks, config.MIDDLE_FINGER_MCP_IDX, (img_h, img_w)
                    )
                    
                    # Get other finger tips to ensure they are NOT curled
                    index_tip_x, index_tip_y = tracker.get_landmark_pos(
                         hand_landmarks, config.INDEX_FINGER_TIP_IDX, (img_h, img_w)
                    )
                    middle_tip_x, middle_tip_y = tracker.get_landmark_pos(
                         hand_landmarks, config.MIDDLE_FINGER_TIP_IDX, (img_h, img_w)
                    )
                    pinky_tip_x, pinky_tip_y = tracker.get_landmark_pos(
                         hand_landmarks, config.PINKY_TIP_IDX, (img_h, img_w)
                    )
                    thumb_x, thumb_y = tracker.get_landmark_pos(
                         hand_landmarks, config.THUMB_TIP_IDX, (img_h, img_w)
                    )

                    # Distances to wrist
                    ring_to_wrist_dist = np.hypot(ring_tip_x - wrist_x, ring_tip_y - wrist_y)
                    index_to_wrist_dist = np.hypot(index_tip_x - wrist_x, index_tip_y - wrist_y)
                    middle_to_wrist_dist = np.hypot(middle_tip_x - wrist_x, middle_tip_y - wrist_y)
                    pinky_to_wrist_dist = np.hypot(pinky_tip_x - wrist_x, pinky_tip_y - wrist_y)
                    
                    palm_size = np.hypot(palm_base_x - wrist_x, palm_base_y - wrist_y)

                    # Volume gesture detection (pose)
                    # Landmarks for pose checks
                    index_mcp_x, index_mcp_y = tracker.get_landmark_pos(
                        hand_landmarks, config.CURSOR_TRACKING_IDX, (img_h, img_w)
                    )
                    # Distances thumb->each fingertip, normalized by palm_size
                    d_ti = np.hypot(index_tip_x - thumb_x, index_tip_y - thumb_y)
                    d_tm = np.hypot(middle_tip_x - thumb_x, middle_tip_y - thumb_y)
                    d_tr = np.hypot(ring_tip_x - thumb_x, ring_tip_y - thumb_y)
                    d_tp = np.hypot(pinky_tip_x - thumb_x, pinky_tip_y - thumb_y)
                    ratios = np.array([d_ti, d_tm, d_tr, d_tp], dtype=float) / max(1.0, palm_size)
                    near_bounds_ok = np.all(
                        (ratios >= config.VOLUME_NEAR_MIN_RATIO) &
                        (ratios <= config.VOLUME_NEAR_MAX_RATIO)
                    )
                    equal_ok = are_distances_similar(ratios, config.VOLUME_EQUALITY_TOL)
                    # Colinearity and ordering: index_tip - index_mcp - thumb_tip on a line
                    v_index = np.array([index_tip_x - index_mcp_x, index_tip_y - index_mcp_y], dtype=float)
                    v_thumb = np.array([thumb_x - index_mcp_x, thumb_y - index_mcp_y], dtype=float)
                    angle_deg = angle_between_vectors_deg(v_index, v_thumb)
                    colinear_angle_ok = angle_deg >= 150.0
                    between_ok = is_colinear_and_between(
                        np.array([index_tip_x, index_tip_y], dtype=float),
                        np.array([index_mcp_x, index_mcp_y], dtype=float),
                        np.array([thumb_x, thumb_y], dtype=float),
                        tolerance=config.VOLUME_LINE_TOL * palm_size,
                    )
                    # Thumb below and horizontally near index MCP
                    vertical_ok = (thumb_y > (index_mcp_y + config.VOLUME_MIN_VERTICAL_DIFF * palm_size))
                    horizontal_ok = (abs(thumb_x - index_mcp_x) <= config.VOLUME_HORIZONTAL_TOL * palm_size)
                    volume_pose_detected = (
                        near_bounds_ok and equal_ok and colinear_angle_ok and between_ok and
                        vertical_ok and horizontal_ok
                    )

                    # Check conditions:
                    # 1. Ring finger curled (close to wrist)
                    # 2. Index, Middle, Pinky extended (far from wrist)
                    ring_curled = ring_to_wrist_dist < palm_size
                    others_extended = (
                        index_to_wrist_dist > palm_size * 1.5 and
                        middle_to_wrist_dist > palm_size * 1.5 and
                        pinky_to_wrist_dist > palm_size * 1.2 # Pinky is naturally shorter
                    )

                    if ring_curled and others_extended:
                        current_time = time.time()
                        if not system_active:
                            # Toggle ON requires holding the gesture steady for configured duration
                            if (current_time - last_toggle_time) > config.TOGGLE_COOLDOWN:
                                if not activation_pending:
                                    activation_pending = True
                                    activation_start_time = current_time
                                    activation_anchor_x = wrist_x
                                    activation_anchor_y = wrist_y
                                    activation_drift_frames = 0
                                    print("Activation pending: hold gesture steady...")
                                else:
                                    # Check stillness relative to initial anchor and palm-size wiggle allowance
                                    move_dist = np.hypot(wrist_x - activation_anchor_x, wrist_y - activation_anchor_y)
                                    allowed_wiggle = max(config.TOGGLE_ON_WIGGLE_MIN_PX, config.TOGGLE_ON_WIGGLE_RATIO * palm_size)
                                    if move_dist > allowed_wiggle:
                                        # Debounced reset: require drift for N consecutive frames
                                        activation_drift_frames += 1
                                        if activation_drift_frames >= config.TOGGLE_ON_DRIFT_FRAMES:
                                            activation_start_time = current_time
                                            activation_anchor_x = wrist_x
                                            activation_anchor_y = wrist_y
                                            activation_drift_frames = 0
                                    else:
                                        activation_drift_frames = 0
                                    if (current_time - activation_start_time) >= config.TOGGLE_ON_STILLNESS_SECONDS:
                                        system_active = True
                                        last_toggle_time = current_time
                                        activation_pending = False
                                        activation_start_time = None
                                        activation_anchor_x = None
                                        activation_anchor_y = None
                                        activation_drift_frames = 0
                                        print(f"System Active: {system_active}")
                        else:
                            # Toggle OFF occurs immediately with cooldown
                            if (current_time - last_toggle_time) > config.TOGGLE_COOLDOWN:
                                system_active = False
                                last_toggle_time = current_time
                                activation_pending = False
                                activation_start_time = None
                                activation_anchor_x = None
                                activation_anchor_y = None
                                activation_drift_frames = 0
                                mouse_ctrl.leftRelease() # Ensure mouse is released when disabling
                                mouse_ctrl.rightRelease()
                                print(f"System Active: {system_active}")
                    else:
                        # If gesture broken, cancel any pending activation
                        if activation_pending:
                            activation_pending = False
                            activation_start_time = None
                            activation_anchor_x = None
                            activation_anchor_y = None
                            activation_drift_frames = 0

                    # Existing Mouse & Scroll Logic (only if active)
                    if system_active:
                        current_time = time.time()

                        # Volume Mode: entry/exit + rotation handling
                        if volume_pose_detected:
                            volume_confirm_count += 1
                            volume_pose_last_seen_time = current_time
                        else:
                            volume_confirm_count = 0
                            if volume_active:
                                if volume_pose_last_seen_time is None:
                                    volume_pose_last_seen_time = current_time
                                elif current_time - volume_pose_last_seen_time > config.VOLUME_EXIT_LEEWAY:
                                    volume_active = False
                                    volume_pose_last_seen_time = None

                        if not volume_active and volume_confirm_count >= config.VOLUME_ENTER_CONFIRM_FRAMES:
                            # Enter volume mode
                            volume_active = True
                            volume_pose_last_seen_time = current_time
                            volume_theta_prev = np.arctan2(thumb_y - index_mcp_y, thumb_x - index_mcp_x)
                            volume_percent_current = vol_ctrl.get_master_volume()
                            volume_percent_applied = volume_percent_current
                            # Release any buttons during volume control
                            mouse_ctrl.leftRelease()
                            mouse_ctrl.rightRelease()

                        if volume_active:
                            # Compute rotation delta and update volume
                            theta = np.arctan2(thumb_y - index_mcp_y, thumb_x - index_mcp_x)
                            delta = wrap_angle_delta(theta - volume_theta_prev)
                            delta_deg = float(np.degrees(delta))
                            if abs(delta_deg) < config.VOLUME_ANGLE_DEADZONE_DEG:
                                delta_deg = 0.0
                            if config.VOLUME_DIRECTION_REVERSED:
                                delta_deg = -delta_deg
                            volume_percent_current += (delta_deg / config.VOLUME_DEG_PER_PERCENT)
                            volume_percent_current = clamp(volume_percent_current, 0.0, 100.0)
                            # Smooth applied value
                            alpha = config.VOLUME_SMOOTHING_ALPHA
                            if volume_percent_applied is None:
                                volume_percent_applied = volume_percent_current
                            else:
                                volume_percent_applied = (1.0 - alpha) * volume_percent_applied + alpha * volume_percent_current
                            vol_ctrl.set_master_volume(volume_percent_applied)
                            volume_theta_prev = theta

                            # Overlay: Volume bar and percentage
                            vol_text = f"Volume: {int(round(volume_percent_applied))}%"
                            cv2.putText(img, vol_text, (40, 590),
                                        cv2.FONT_HERSHEY_PLAIN, 2, (0, 255, 0), 2)
                            # Simple volume bar
                            bar_x, bar_y = 40, 610
                            bar_w, bar_h = 300, 16
                            cv2.rectangle(img, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), (0, 255, 0), 2)
                            filled_w = int(bar_w * (volume_percent_applied / 100.0))
                            cv2.rectangle(img, (bar_x, bar_y), (bar_x + filled_w, bar_y + bar_h), (0, 255, 0), cv2.FILLED)
                            # Skip cursor/scroll logic during volume mode
                            continue

                        # Detect fist gesture (all fingertips close to wrist)
                        curl_threshold = palm_size * 1.1
                        fist_detected = (
                            index_to_wrist_dist < curl_threshold and
                            middle_to_wrist_dist < curl_threshold and
                            ring_to_wrist_dist < curl_threshold and
                            pinky_to_wrist_dist < curl_threshold
                        )

                        if fist_detected:
                            if not scroll_active:
                                scroll_active = True
                                scroll_origin_x = wrist_x
                                scroll_origin_y = wrist_y
                                fist_lost_time = None
                                # Ensure no buttons are held while scrolling
                                mouse_ctrl.leftRelease()
                                mouse_ctrl.rightRelease()
                        else:
                            if scroll_active:
                                if fist_lost_time is None:
                                    fist_lost_time = current_time
                                elif current_time - fist_lost_time > config.FIST_DETECTION_LEEWAY:
                                    scroll_active = False
                                    scroll_origin_y = None
                                    fist_lost_time = None

                        if scroll_active:
                            # Compute scroll amount based on vertical distance from origin
                            delta_y = wrist_y - scroll_origin_y
                            distance = abs(delta_y) - config.SCROLL_DEADZONE
                            if distance > 0:
                                # Map movement like a mouse: moving up => scroll up, moving down => scroll down
                                direction = 1 if delta_y < 0 else -1
                                dy = int(max(1, min(10, distance * config.SCROLL_SPEED_FACTOR))) * direction
                                if config.INVERT_SCROLL_DIRECTION:
                                    dy = -dy
                                mouse_ctrl.scroll(dy)

                            # Visualize initial fist point and vertical delta
                            if scroll_origin_x is not None and scroll_origin_y is not None:
                                origin_pt = (int(scroll_origin_x), int(scroll_origin_y))
                                current_pt = (int(scroll_origin_x), int(wrist_y))
                                cv2.circle(img, origin_pt, 7, (0, 255, 255), 2)
                                cv2.line(img, origin_pt, current_pt, (0, 255, 255), 2)
                                text_pos = (origin_pt[0] + 10, int((origin_pt[1] + current_pt[1]) / 2))
                                cv2.putText(img, f'dy: {int(delta_y)} px', text_pos,
                                            cv2.FONT_HERSHEY_PLAIN, 2, (0, 255, 255), 2)

                            cv2.putText(img, "Scroll: ON", (40, 550),
                                        cv2.FONT_HERSHEY_PLAIN, 2, (0, 255, 255), 2)
                            # Skip cursor move and click handling while scrolling
                            continue

                        # Get coordinates for cursor tracking (Index Finger MCP)
                        track_x, track_y = tracker.get_landmark_pos(
                            hand_landmarks, config.CURSOR_TRACKING_IDX, (img_h, img_w)
                        )

                        # Visual feedback for tracking point
                        cv2.circle(img, (track_x, track_y), 7, (255, 0, 0), cv2.FILLED)

                        # Calculate current raw mouse location
                        current_raw_location = np.array([track_x, track_y])

                        if is_first_detection:
                            mouse_location = current_raw_location # Initialize with first valid point
                            is_first_detection = False
                        
                        # Smooth movement
                        mouse_location = smooth_position(current_raw_location, mouse_location, config.SMOOTHING_FACTOR)
                        
                        # Move mouse
                        mouse_ctrl.move_to(mouse_location)

                        # Gesture Recognition for Click (Pinch)
                        thumb_x, thumb_y = tracker.get_landmark_pos(
                            hand_landmarks, config.THUMB_TIP_IDX, (img_h, img_w)
                        )
                        index_x, index_y = tracker.get_landmark_pos(
                            hand_landmarks, config.INDEX_FINGER_TIP_IDX, (img_h, img_w)
                        )
                        # Calculate distance between thumb and index finger
                        index_pinch_distance = np.hypot(index_x - thumb_x, index_y - thumb_y)
                        middle_pinch_distance = np.hypot(middle_tip_x - thumb_x, middle_tip_y - thumb_y)
                        # Visual feedback for pinch gesture
                        cv2.line(img, (thumb_x, thumb_y), (index_x, index_y), (255, 0, 255), 2  )
                        cv2.putText(img, f'Left Click: '+ str(mouse_ctrl.left_pressed), (40, 450), 
                                    cv2.FONT_HERSHEY_PLAIN, 2, (255, 0, 0), 2)
                        cv2.putText(img, f'Right Click: '+ str(mouse_ctrl.right_pressed), (40, 500), 
                                    cv2.FONT_HERSHEY_PLAIN, 2, (255, 0, 0), 2)
        
                        # Handle Right Click
                        if middle_pinch_distance < config.RIGHT_CLICK_DISTANCE_RATIO * palm_size:
                            mouse_ctrl.rightClick()
                        else:
                            mouse_ctrl.rightRelease()
                        
                        # Handle Left Click
                        if index_pinch_distance < config.LEFT_CLICK_DISTANCE_RATIO * palm_size:
                            mouse_ctrl.leftClick()
                        else:
                            mouse_ctrl.leftRelease()
            
            # Status Display
            status_text = "Active" if system_active else "Paused"
            status_color = (0, 255, 0) if system_active else (0, 0, 255)
            cv2.putText(img, f'System: {status_text}', (40, 50), 
                        cv2.FONT_HERSHEY_PLAIN, 2, status_color, 2)
            # Activation pending hint
            if (not system_active) and activation_pending and (activation_start_time is not None):
                remaining = max(0.0, config.TOGGLE_ON_STILLNESS_SECONDS - (time.time() - activation_start_time))
                cv2.putText(img, f'Activating in: {remaining:.1f}s', (40, 80),
                            cv2.FONT_HERSHEY_PLAIN, 2, (0, 255, 255), 2)

            # Display the output
            cv2.imshow("HandyMouse - CamOutput", img)
            
            # Exit on 'Esc' key
            if cv2.waitKey(1) & 0xFF == 27:
                break

    except KeyboardInterrupt:
        print("Interrupted by user.")
    finally:
        video_cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
