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
        # Cache flattened key-value map for quick access
        object.__setattr__(self, "_flattened_config", {})
        self.load_config()

    def _flatten_config(self, config_dict):
        """
        Recursively flattens the config dictionary to map leaf keys to their values/metadata objects.
        Returns a dict where keys are the setting names (e.g., 'CURSOR_SPEED') and values
        are the config objects (e.g., {'value': 1.5, ...}) or raw values.
        """
        flattened = {}
        for key, item in config_dict.items():
            if isinstance(item, dict) and "content" in item:
                # This is a category
                flattened.update(self._flatten_config(item["content"]))
            else:
                # This is a setting
                flattened[key] = item
        return flattened

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

            is_user_flat = not any("content" in v for v in user_config.values() if isinstance(v, dict))
            is_default_nested = any("content" in v for v in self._default_config.values() if isinstance(v, dict))

            if is_user_flat and is_default_nested:
                # Reconstruct user config using default structure but user values
                new_user_config = self._default_config.copy()
                
                # Helper to update nested structure with flat values
                def update_nested(structure, flat_values):
                    for key, item in structure.items():
                        if isinstance(item, dict) and "content" in item:
                            update_nested(item["content"], flat_values)
                        elif key in flat_values:
                            # User has this key
                            user_val = flat_values[key]
                            # If user val is old format (raw), wrap it
                            if isinstance(structure[key], dict) and "value" in structure[key]:
                                if not isinstance(user_val, dict) or "value" not in user_val:
                                     structure[key]["value"] = user_val
                                else:
                                     structure[key] = user_val
                            else:
                                structure[key] = user_val
                
                update_nested(new_user_config, user_config)
                self._config = new_user_config
                self.save_config()
            else:
                self._config = user_config

        except (FileNotFoundError, json.JSONDecodeError):
             self._config = {}

        # 4. Fallback/Fill missing keys from default
        # We walk the default config and ensure every key exists in user config
        def ensure_keys(default_node, user_node):
            modified = False
            for key, default_item in default_node.items():
                if key not in user_node:
                    user_node[key] = default_item.copy()
                    modified = True
                else:
                    if isinstance(default_item, dict) and "content" in default_item:
                         # Recurse into category
                         if "content" not in user_node[key]:
                             # Structure mismatch, reset to default for this category
                             user_node[key] = default_item.copy()
                             modified = True
                         else:
                             if ensure_keys(default_item["content"], user_node[key]["content"]):
                                 modified = True
            return modified

        if ensure_keys(self._default_config, self._config):
            self.save_config()

        # Update cache
        self._flattened_config = self._flatten_config(self._config)

    def save_config(self):
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self._config, f, indent=4)
            # Update cache after save
            self._flattened_config = self._flatten_config(self._config)
        except Exception as e:
            print(f"Error saving config: {e}")

    def _find_key_path(self, key, config_dict, path=None):
        """
        Locates a key within the nested config structure.
        Returns the dictionary containing the key and the key itself.
        """
        if path is None:
            path = []
            
        if key in config_dict:
            return config_dict, key

        for k, v in config_dict.items():
            if isinstance(v, dict) and "content" in v:
                result = self._find_key_path(key, v["content"], path + [k])
                if result:
                    return result
        return None

    def get(self, key, default=None):
        # Check cache first
        if key in self._flattened_config:
            item = self._flattened_config[key]
            if isinstance(item, dict) and "value" in item:
                return item["value"]
            return item
            
        return default

    def set(self, key, value):
        # Find where this key lives in the real _config structure
        location = self._find_key_path(key, self._config)
        if location:
            container, found_key = location
            item = container[found_key]
            if isinstance(item, dict) and "value" in item:
                item["value"] = value
            else:
                container[found_key] = value
            self.save_config()
        else:
            # Fallback to creating it in root.
            self._config[key] = value
            self.save_config()

    def reset_to_defaults(self):
        """
        Resets the configuration to default values.
        """
        self._config = self._default_config.copy()
        # Deep copy to avoid reference issues if we modify _config later
        import copy
        self._config = copy.deepcopy(self._default_config)
        self.save_config()

    def reset_setting(self, key):
        """
        Resets a single setting to its default value.
        """
        # Find default value
        location = self._find_key_path(key, self._default_config)
        if location:
            container, found_key = location
            default_item = container[found_key]
            
            val_to_set = default_item
            if isinstance(default_item, dict) and "value" in default_item:
                val_to_set = default_item["value"]
                
            self.set(key, val_to_set)



    def __getattr__(self, name):
        # This allows config.CURSOR_SPEED access
        val = self.get(name)
        if val is not None:
            return val
        raise AttributeError(f"'ConfigManager' object has no attribute '{name}'")

    def __setattr__(self, name, value):
        if name.startswith("_"):
            object.__setattr__(self, name, value)
            return

        # Try to set as config key
        if name in self._flattened_config:
            self.set(name, value)
            return
            
        # Fallback to instance attribute
        object.__setattr__(self, name, value)

config = ConfigManager()
