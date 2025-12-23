"""
Mouse control module.

This module handles the interaction with the system mouse, including movement
and clicking, based on coordinates provided by the tracking system.
"""

import ctypes
import numpy as np
from pynput.mouse import Button, Controller
from core.config_manager import config

class MouseController:
    """
    Manages mouse cursor movement and clicks.
    """

    def __init__(self):
        """
        Initialize the MouseController.
        
        Sets up the pynput mouse controller and retrieves the screen size
        using ctypes.
        """
        self.mouse = Controller()
        user32 = ctypes.windll.user32
        self.screen_width = user32.GetSystemMetrics(0)
        self.screen_height = user32.GetSystemMetrics(1)
        self.pressed = False
        self.left_pressed = False
        self.right_pressed = False

    def move_to(self, location: np.ndarray, cam_width: int = 1280, cam_height: int = 720):
        """
        Moves the mouse cursor to a mapped position on the screen.

        The logic maps the camera coordinates to screen coordinates.
        CURSOR_SPEED controls how much hand movement maps to cursor movement.
        
        Args:
            location (np.ndarray): The (x, y) coordinates from the tracker.
            cam_width (int): Camera frame width for coordinate mapping.
            cam_height (int): Camera frame height for coordinate mapping.
        """
        speed = config.CURSOR_SPEED
        
        # Map camera coordinates to screen, with speed multiplier
        # Speed > 1: less hand movement covers more screen (faster)
        # Speed < 1: more hand movement needed (slower/more precise)
        target_x = self.screen_width - (location[0] * self.screen_width * speed / cam_width)
        target_y = location[1] * self.screen_height * speed / cam_height
        
        self.mouse.position = (target_x, target_y)

    def click(self):
        """
        Performs a left mouse click (press down) if not already pressed.
        """
        if not self.pressed:
            self.mouse.press(Button.left)
            self.pressed = True
            # print("Click")

    def release(self):
        """
        Releases the left mouse button if it is currently pressed.
        """
        if self.pressed:
            self.mouse.release(Button.left)
            self.pressed = False
            # print("Unclick")

    def leftClick(self):
        """
        Performs a left mouse button press if not already pressed.
        """
        if not self.left_pressed:
            self.mouse.press(Button.left)
            self.left_pressed = True

    def leftRelease(self):
        """
        Releases the left mouse button if it is currently pressed.
        """
        if self.left_pressed:
            self.mouse.release(Button.left)
            self.left_pressed = False

    def rightClick(self):
        """
        Performs a right mouse button press if not already pressed.
        """
        if not self.right_pressed:
            self.mouse.press(Button.right)
            self.right_pressed = True

    def rightRelease(self):
        """
        Releases the right mouse button if it is currently pressed.
        """
        if self.right_pressed:
            self.mouse.release(Button.right)
            self.right_pressed = False

    def scroll(self, dx: int, dy: int):
        """
        Scrolls the mouse wheel vertically and/or horizontally.

        Args:
            dx (int): Positive to scroll right, negative to scroll left.
            dy (int): Positive to scroll up, negative to scroll down.
        """
        self.mouse.scroll(int(dx), int(dy))

