"""
Mouse control module.

This module handles the interaction with the system mouse, including movement
and clicking, based on coordinates provided by the tracking system.
"""

import wx
import numpy as np
from pynput.mouse import Button, Controller
from config import SCREEN_MAPPING_WIDTH_DIVISOR, SCREEN_MAPPING_HEIGHT_DIVISOR

class MouseController:
    """
    Manages mouse cursor movement and clicks.
    """

    def __init__(self):
        """
        Initialize the MouseController.
        
        Sets up the pynput mouse controller and retrieves the screen size
        using wxPython.
        """
        self.mouse = Controller()
        self.app = wx.App(False)
        self.screen_width, self.screen_height = wx.GetDisplaySize()
        self.left_pressed = False
        self.right_pressed = False

    def move_to(self, location: np.ndarray):
        """
        Moves the mouse cursor to a mapped position on the screen.

        The logic maps the camera coordinates to screen coordinates.
        Note: The original logic inverted the X axis and scaled Y.
        
        Args:
            location (np.ndarray): The (x, y) coordinates from the tracker.
        """
        # Mapping logic from original script:
        # sx - (mouse_location[0] * sx / 1200)
        # mouse_location[1] * sy / 675
        
        target_x = self.screen_width - (location[0] * self.screen_width / SCREEN_MAPPING_WIDTH_DIVISOR)
        target_y = location[1] * self.screen_height / SCREEN_MAPPING_HEIGHT_DIVISOR
        
        self.mouse.position = (target_x, target_y)

    def leftClick(self):
        """
        Performs a left mouse click (press down) if not already pressed.
        """
        if not self.left_pressed:
            self.mouse.press(Button.left)
            self.left_pressed = True
            print("Left Click")

    def rightClick(self):
        """
        Performs a right mouse click (press down) if not already pressed.
        """
        if not self.right_pressed:
            self.mouse.press(Button.right)
            self.right_pressed = True
            print("Right Click")
    def rightRelease(self):
        """
        Releases the right mouse button if it is currently pressed.
        """
        if self.right_pressed:
            self.mouse.release(Button.right)
            self.right_pressed = False
            # print("Right Unclick")
    def leftRelease(self):
        """
        Releases the left mouse button if it is currently pressed.
        """
        if self.left_pressed:
            self.mouse.release(Button.left)
            self.left_pressed = False
            # print("Unclick")

