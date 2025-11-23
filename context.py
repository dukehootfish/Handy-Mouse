from helpers.mouse_controller import MouseController
from helpers.audio_controller import AudioController
from helpers.hand_tracker import HandTracker
from flags import HandyFlags

class HandyContext:
    def __init__(self):
        self.flags = HandyFlags()
        self.mouse = MouseController()
        self.audio = AudioController()
        self.tracker = HandTracker(max_num_hands=1)

