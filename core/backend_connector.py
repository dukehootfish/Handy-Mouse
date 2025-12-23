"""
Backend Connector for HandyMouse.

This class dynamically loads actions from the actions/ folder and exposes them
as methods, providing a unified interface for the frontend to interact with the backend.
"""

import os
import importlib.util
import inspect


class BackendConnector:
    """
    A connector class that dynamically loads actions from the actions/ folder
    and exposes them as methods.
    """

    def __init__(self):
        """Initialize the connector and load all actions."""
        self.app_instance = None
        self.load_actions()

    def load_actions(self):
        """
        Dynamically load all action modules from the actions/ folder
        and attach their 'action' functions as methods to this instance.
        """
        actions_dir = os.path.join(os.path.dirname(__file__), "actions")
        
        if not os.path.exists(actions_dir):
            print(f"Warning: Actions directory '{actions_dir}' not found.")
            return

        # Get all Python files in the actions directory
        for filename in os.listdir(actions_dir):
            if filename.endswith(".py") and filename != "__init__.py":
                module_name = filename[:-3]  # Remove .py extension
                
                try:
                    # Import the module
                    spec = importlib.util.spec_from_file_location(
                        f"actions.{module_name}",
                        os.path.join(actions_dir, filename)
                    )
                    if spec is None or spec.loader is None:
                        print(f"Warning: Could not load spec for {filename}")
                        continue
                    
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    # Check if the module has an 'action' function
                    if hasattr(module, "action") and callable(module.action):
                        # Get the function signature to determine how many parameters it takes
                        sig = inspect.signature(module.action)
                        params = list(sig.parameters.keys())
                        
                        # Create a wrapper method that passes 'self' (connector) as first arg
                        def make_action_wrapper(action_func, connector_instance):
                            def action_wrapper(*args, **kwargs):
                                # Always pass connector instance as first argument
                                return action_func(connector_instance, *args, **kwargs)
                            return action_wrapper
                        
                        # Attach the action as a method with the module name
                        setattr(self, module_name, make_action_wrapper(module.action, self))
                        print(f"Loaded action: {module_name}")
                    else:
                        print(f"Warning: Module '{module_name}' does not have an 'action' function.")
                        
                except Exception as e:
                    print(f"Error loading action '{module_name}': {e}")

