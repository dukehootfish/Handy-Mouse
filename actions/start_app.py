"""
Action to start the HandyMouse application.
"""

from core.app import HandyMouseApp
from helpers.utils import set_high_priority


def action(connector):
    """
    Start the HandyMouse application.
    
    Args:
        connector: The BackendConnector instance.
    """
    set_high_priority()
    app = HandyMouseApp()
    connector.app_instance = app
    app.run()

