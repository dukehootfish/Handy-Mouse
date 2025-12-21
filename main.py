"""
HandyMouse Main Entry Point.

This file initializes and runs the HandyMouse application.
"""

from app import HandyMouseApp
import sys
import os
import ctypes


def set_high_priority():
    """ Set the priority of the process to high. """
    try:
        sys.getwindowsversion()
    except AttributeError:
        # Not on Windows
        return

    # HIGH_PRIORITY_CLASS = 0x00000080
    # ABOVE_NORMAL_PRIORITY_CLASS = 0x00008000
    pid = os.getpid()
    handle = ctypes.windll.kernel32.OpenProcess(0x0100, False, pid) # PROCESS_SET_INFORMATION
    if handle:
        ctypes.windll.kernel32.SetPriorityClass(handle, 0x00000080)
        ctypes.windll.kernel32.CloseHandle(handle)
        print("Process priority set to HIGH.")
    else:
        print("Failed to set process priority.")


def main():
    set_high_priority()
    app = HandyMouseApp()
    app.run()


if __name__ == "__main__":
    main()
