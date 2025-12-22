"""
Action to stop the HandyMouse application.
"""


def action(connector):
    """
    Stop the HandyMouse application gracefully.
    
    Args:
        connector: The BackendConnector instance.
    """
    if connector.app_instance is not None:
        connector.app_instance.context.flags.EXIT_REQUESTED = True
    else:
        print("Warning: No app instance to stop.")

