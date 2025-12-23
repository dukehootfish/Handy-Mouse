"""
Action to update configuration values.
"""

from core.config_manager import config


def action(connector, key, value):
    """
    Update a configuration value.
    
    Args:
        connector: The BackendConnector instance.
        key: The configuration key to update.
        value: The new value to set.
    """
    config.set(key, value)

