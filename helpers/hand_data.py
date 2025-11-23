import numpy as np
import config

class HandData:
    """
    Encapsulates hand landmark data and provides helper properties/methods
    for gesture detection.
    """
    def __init__(self, hand_landmarks, img_shape):
        self.landmarks = hand_landmarks
        self.img_h, self.img_w = img_shape
        
        # Cache for computed positions to avoid re-calculation
        self._positions = {}
        
        # Initialize key points
        self.wrist = self._get_pos(config.WRIST_IDX)
        self.thumb_tip = self._get_pos(config.THUMB_TIP_IDX)
        self.index_tip = self._get_pos(config.INDEX_FINGER_TIP_IDX)
        self.middle_tip = self._get_pos(config.MIDDLE_FINGER_TIP_IDX)
        self.ring_tip = self._get_pos(config.RING_FINGER_TIP_IDX)
        self.pinky_tip = self._get_pos(config.PINKY_TIP_IDX)
        
        self.middle_mcp = self._get_pos(config.MIDDLE_FINGER_MCP_IDX)
        self.index_mcp = self._get_pos(config.CURSOR_TRACKING_IDX) # Index MCP
        
        # Calculate Palm Size (Wrist to Middle MCP)
        self.palm_size = np.hypot(self.middle_mcp[0] - self.wrist[0], 
                                  self.middle_mcp[1] - self.wrist[1])
                                  
        # Pre-calculate Distances to Wrist
        self.ring_to_wrist_dist = np.hypot(self.ring_tip[0] - self.wrist[0], 
                                           self.ring_tip[1] - self.wrist[1])
        self.index_to_wrist_dist = np.hypot(self.index_tip[0] - self.wrist[0], 
                                            self.index_tip[1] - self.wrist[1])
        self.middle_to_wrist_dist = np.hypot(self.middle_tip[0] - self.wrist[0], 
                                             self.middle_tip[1] - self.wrist[1])
        self.pinky_to_wrist_dist = np.hypot(self.pinky_tip[0] - self.wrist[0], 
                                            self.pinky_tip[1] - self.wrist[1])

    def _get_pos(self, idx):
        """Extracts (x, y) from landmarks for a given index."""
        if idx in self._positions:
            return self._positions[idx]
        
        lm = self.landmarks.landmark[idx]
        x, y = int(lm.x * self.img_w), int(lm.y * self.img_h)
        self._positions[idx] = (x, y)
        return x, y

