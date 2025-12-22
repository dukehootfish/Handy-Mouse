"""
HandyMouse Main Entry Point.

This file initializes and runs the HandyMouse application.
"""

from app import HandyMouseApp
from helpers.utils import set_high_priority


def main():
    set_high_priority()
    app = HandyMouseApp()
    app.run()


if __name__ == "__main__":
    main()
