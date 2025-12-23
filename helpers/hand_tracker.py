"""
Hand tracking module using MediaPipe.

This module provides the HandTracker class to abstract the complexity of
initializing and using MediaPipe's Hand tracking solution.
"""

import mediapipe as mp
import cv2
import numpy as np
from typing import Tuple, List, NamedTuple

class HandTracker:
    """
    A wrapper class for MediaPipe Hands to perform hand tracking and landmark extraction.
    """

    def __init__(self, static_image_mode: bool = False, max_num_hands: int = 1, 
                 min_detection_confidence: float = 0.5, min_tracking_confidence: float = 0.5):
        """
        Initialize the HandTracker.

        Args:
            static_image_mode (bool): Whether to treat the input images as a batch of static
                                      and possibly unrelated images.
            max_num_hands (int): Maximum number of hands to detect.
            min_detection_confidence (float): Minimum confidence value ([0.0, 1.0]) for hand
                                              detection to be considered successful.
            min_tracking_confidence (float): Minimum confidence value ([0.0, 1.0]) for the
                                             hand landmarks to be considered tracked successfully.
        """
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=static_image_mode,
            max_num_hands=max_num_hands,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence
        )

    def process_frame(
        self, img: np.ndarray
    ) -> Tuple[np.ndarray, List[NamedTuple], List[NamedTuple], List[NamedTuple]]:
        """
        Process a single video frame to detect hands.

        Args:
            img (np.ndarray): The input image (BGR format from OpenCV).

        Returns:
            Tuple[np.ndarray, List[NamedTuple], List[NamedTuple], List[NamedTuple]]:
                - The processed image (BGR).
                - Detected hand landmarks objects (possibly empty).
                - The handedness classification entries for the detected hands.
                - The world landmarks (3D coordinates in meters).
        """
        # Convert the BGR image to RGB before processing.
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results = self.hands.process(img_rgb)

        hand_landmarks = results.multi_hand_landmarks or []
        handedness = results.multi_handedness or []
        world_landmarks = results.multi_hand_world_landmarks or []

        return img, list(hand_landmarks), list(handedness), list(world_landmarks)

    def draw_landmarks(self, img: np.ndarray, hand_landmarks, color: Tuple[int, int, int]):
        drawing_spec = self.mp_drawing.DrawingSpec(color=color, thickness=2, circle_radius=2)
        self.mp_drawing.draw_landmarks(
            img,
            hand_landmarks,
            self.mp_hands.HAND_CONNECTIONS,
            drawing_spec,
            drawing_spec,
        )

    def get_landmark_pos(self, hand_landmarks, landmark_idx: int, img_shape: Tuple[int, int]) -> Tuple[int, int]:
        """
        Calculate the pixel coordinates of a specific landmark.

        Args:
            hand_landmarks: The detected hand landmarks object from MediaPipe.
            landmark_idx (int): The index of the landmark to retrieve.
            img_shape (Tuple[int, int]): The shape of the image (height, width).

        Returns:
            Tuple[int, int]: The (x, y) pixel coordinates of the landmark.
        """
        h, w = img_shape
        lm = hand_landmarks.landmark[landmark_idx]
        x, y = int(lm.x * w), int(lm.y * h)
        return x, y

