class HandActivationState:
    def __init__(self, label):
        self.label = label
        self.pending = False
        self.start_time = None
        self.anchor_x = None
        self.anchor_y = None
        self.drift_frames = 0
        self.is_active = False

    def reset_pending(self):
        self.pending = False
        self.start_time = None
        self.anchor_x = None
        self.anchor_y = None
        self.drift_frames = 0


class HandyFlags:
    def __init__(self):
        # Main System Flags
        self.SYSTEM_ACTIVE = False
        self.SCROLL_ACTIVE = False
        self.LONG_CLICK_ACTIVE = False

        # Hand Role State
        self.MAIN_HAND = None
        self.SECONDARY_HAND = None
        self.TWO_HANDED_MODE = False
        self.HAND_STATES = {
            "Left": HandActivationState("Left"),
            "Right": HandActivationState("Right"),
        }
        self.LAST_TOGGLE_TIME = 0

        # Scroll State
        self.SCROLL_ORIGIN_X = None
        self.SCROLL_ORIGIN_Y = None
        self.LAST_FIST_TIME = None

        # Mic State
        self.MIC_MUTE_HANDLED = False
        self.LAST_MIC_TOGGLE_TIME = 0

        # Click State
        self.LONG_CLICK_START_TIME = None
        self.LAST_CLICK_DETECTED_TIME = 0

        # Mouse Smoothing State
        self.MOUSE_LOCATION = None
        self.IS_FIRST_DETECTION = True

        # Exit Gesture State (Both Fists Closed)
        self.DOUBLE_FIST_START_TIME = None
        self.EXIT_REQUESTED = False

    def get_hand_state(self, label):
        if label not in self.HAND_STATES:
            self.HAND_STATES[label] = HandActivationState(label)
        return self.HAND_STATES[label]
