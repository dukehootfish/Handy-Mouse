import json
import os
import shutil

CONFIG_FILE = "config.json"
DEFAULT_CONFIG_FILE = "default_config.json"
FORCE_UPDATE_FILE = "config_updates_to_force.json"

class ConfigManager:
    def __init__(self):
        # Initialize internal storage avoiding __setattr__ recursion
        object.__setattr__(self, "_config", {})
        object.__setattr__(self, "_default_config", {})
        self.load_config()

    def load_config(self):
        # 1. Load default config
        try:
            with open(DEFAULT_CONFIG_FILE, 'r') as f:
                self._default_config = json.load(f)
        except FileNotFoundError:
            self._default_config = {}

        # 2. Ensure config.json exists
        if not os.path.exists(CONFIG_FILE):
            if os.path.exists(DEFAULT_CONFIG_FILE):
                shutil.copy(DEFAULT_CONFIG_FILE, CONFIG_FILE)
            else:
                self._config = {}
        
        # 3. Load user config
        try:
            with open(CONFIG_FILE, 'r') as f:
                user_config = json.load(f)

            # Migration: Check if values are old format (not dicts with 'value')
            # and migrate them using default config as template
            migrated = False
            for key, val in user_config.items():
                # If the key exists in default config, we can check format against it
                # or just check if 'val' looks like the new structure.
                if key in self._default_config:
                    default_item = self._default_config[key]
                    if isinstance(default_item, dict) and "value" in default_item:
                        # Default is new format. Check if user config is old format.
                        # Old format: val is directly the value (int, float, bool, etc.)
                        # New format: val is a dict with "value" key
                        if not isinstance(val, dict) or "value" not in val:
                            # Convert to new format
                            new_entry = default_item.copy()
                            new_entry["value"] = val
                            user_config[key] = new_entry
                            migrated = True
                # If key is not in default config (e.g. deprecated key), leave it as is 
                # or maybe wrapped if we want to support it? 
                # For now, only migrate keys we know about.

            self._config = user_config
            if migrated:
                self.save_config()

        except (FileNotFoundError, json.JSONDecodeError):
             self._config = {}

        # 4. Handle forced updates
        force_updates = []
        if os.path.exists(FORCE_UPDATE_FILE):
            try:
                with open(FORCE_UPDATE_FILE, 'r') as f:
                    force_updates = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                force_updates = []
        
        config_modified = False

        if force_updates:
            for key in force_updates:
                if key in self._default_config:
                    self._config[key] = self._default_config[key].copy()
                    config_modified = True
            
            # Clear force updates file
            try:
                with open(FORCE_UPDATE_FILE, 'w') as f:
                    json.dump([], f, indent=4)
            except Exception as e:
                print(f"Error clearing force updates file: {e}")

        # 5. Fallback logic: Ensure all keys in default are in user
        for key, value in self._default_config.items():
            if key not in self._config:
                self._config[key] = value.copy() if isinstance(value, dict) else value
                config_modified = True

        if config_modified:
            self.save_config()

    def save_config(self):
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self._config, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")

    def get(self, key, default=None):
        # Look in _config
        if key in self._config:
            item = self._config[key]
            if isinstance(item, dict) and "value" in item:
                return item["value"]
            return item
        
        # Look in _default_config
        if key in self._default_config:
            self._config[key] = self._default_config[key].copy()
            self.save_config()
            return self._config[key]["value"]
            
        return default

    def set(self, key, value):
        if key in self._config:
            if isinstance(self._config[key], dict) and "value" in self._config[key]:
                self._config[key]["value"] = value
            else:
                self._config[key] = value
            self.save_config()
        else:
            # If creating new key, try to infer structure or just set raw
            # For robustness, just set raw unless we have a template?
            # Or assume everything new is raw.
            self._config[key] = value
            self.save_config()

    def __getattr__(self, name):
        if name in self._config:
            item = self._config[name]
            if isinstance(item, dict) and "value" in item:
                return item["value"]
            return item

        if name in self._default_config:
            self._config[name] = self._default_config[name].copy()
            self.save_config()
            return self._config[name]["value"]

        raise AttributeError(f"'ConfigManager' object has no attribute '{name}'")

    def __setattr__(self, name, value):
        # Bypass for internal attributes
        if name.startswith("_"):
            object.__setattr__(self, name, value)
            return

        # Check if it's a known config key
        if name in self._config:
            item = self._config[name]
            if isinstance(item, dict) and "value" in item:
                item["value"] = value
                self.save_config()
                return
            else:
                # Old format or raw value
                self._config[name] = value
                self.save_config()
                return
        
        if name in self._default_config:
            # Promote from default
            self._config[name] = self._default_config[name].copy()
            self._config[name]["value"] = value
            self.save_config()
            return

        # If not a config key, treat as normal instance attribute
        object.__setattr__(self, name, value)

# Create singleton instance
config = ConfigManager()
