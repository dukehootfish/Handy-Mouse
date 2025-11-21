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
from utils import smooth_position
import config

def main():
    """
    Main application loop.
    """
    # Initialize Hand Tracker
    tracker = HandTracker(max_num_hands=1)

    # Initialize Mouse Controller
    mouse_ctrl = MouseController()

    # Initialize Video Capture
    video_cap = cv2.VideoCapture(0)
    video_cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.CAM_WIDTH)
    video_cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.CAM_HEIGHT)

    # State variables for mouse smoothing
    mouse_location = np.array([0, 0])
    
    # Flag to initialize mouse_location on first detection
    is_first_detection = True

    # Toggle state
    system_active = True
    last_toggle_time = 0

    print("HandyMouse started. Press 'Esc' to exit.")

    try:
        while True:
            success, img = video_cap.read()
            if not success:
                print("Failed to grab frame.")
                break

            # Process frame for hand tracking
            img, hand_landmarks = tracker.process_frame(img)
            img_h, img_w = img.shape[:2]

            if hand_landmarks:
                # Toggle Logic: Ring finger tip touches palm (Wrist/Base)
                # AND other fingers (Index, Middle, Pinky) are extended (not touching palm)
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

                # Distances to wrist
                ring_to_wrist_dist = np.hypot(ring_tip_x - wrist_x, ring_tip_y - wrist_y)
                index_to_wrist_dist = np.hypot(index_tip_x - wrist_x, index_tip_y - wrist_y)
                middle_to_wrist_dist = np.hypot(middle_tip_x - wrist_x, middle_tip_y - wrist_y)
                pinky_to_wrist_dist = np.hypot(pinky_tip_x - wrist_x, pinky_tip_y - wrist_y)
                
                palm_size = np.hypot(palm_base_x - wrist_x, palm_base_y - wrist_y)

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
                    if current_time - last_toggle_time > config.TOGGLE_COOLDOWN:
                        system_active = not system_active
                        last_toggle_time = current_time
                        if not system_active:
                            mouse_ctrl.release() # Ensure mouse is released when disabling
                        print(f"System Active: {system_active}")

                # Existing Mouse Logic (only if active)
                if system_active:
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
                    pinch_distance = np.hypot(index_x - thumb_x, index_y - thumb_y)

                    # Visual feedback for pinch gesture
                    cv2.line(img, (thumb_x, thumb_y), (index_x, index_y), (255, 0, 255), 2)
                    cv2.putText(img, f'Distance: {int(pinch_distance)}', (40, 450), 
                                cv2.FONT_HERSHEY_PLAIN, 2, (255, 0, 0), 2)

                    # Handle Click
                    if pinch_distance < config.CLICK_DISTANCE_THRESHOLD:
                        mouse_ctrl.click()
                    else:
                        mouse_ctrl.release()
            
            # Status Display
            status_text = "Active" if system_active else "Paused"
            status_color = (0, 255, 0) if system_active else (0, 0, 255)
            cv2.putText(img, f'System: {status_text}', (40, 50), 
                        cv2.FONT_HERSHEY_PLAIN, 2, status_color, 2)

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
