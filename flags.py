class HandyFlags:
    def __init__(self):
        # Main System Flags
        self.SYSTEM_ACTIVE = False
        self.SCROLL_ACTIVE = False
        self.LONG_CLICK_ACTIVE = False
        
        # Activation State
        self.ACTIVATION_PENDING = False
        self.ACTIVATION_START_TIME = None
        self.ACTIVATION_ANCHOR_X = None
        self.ACTIVATION_ANCHOR_Y = None
        self.ACTIVATION_DRIFT_FRAMES = 0
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
