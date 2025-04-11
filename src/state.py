import json
import os
import threading
import copy # Added copy for deepcopy

# Default settings structure for crosshair profiles
DEFAULT_SETTINGS = {
    "type": "parametric", # 'parametric', 'static', 'animated'
    "parametric": {
        "center_dot_enabled": True,
        "center_dot_color": "#FF0000", # Red
        "center_dot_size": 3,
        "center_dot_opacity": 200,
        "inner_lines_enabled": True,
        "inner_lines_color": "#FFFFFF", # White
        "inner_lines_thickness": 1,
        "inner_lines_length": 5,
        "inner_lines_gap": 3,
        "inner_lines_opacity": 255,
        "outer_lines_enabled": False,
        "outer_lines_color": "#00FF00", # Green
        "outer_lines_thickness": 1,
        "outer_lines_length": 2,
        "outer_lines_gap": 8,
        "outer_lines_opacity": 180,
        "outline_enabled": True,
        "outline_color": "#000000", # Black
        "outline_thickness": 1,
        "outline_opacity": 150,
        "t_shape": False
    },
    "static": {
        "image_path": None, # Path relative to user_uploads/
        "opacity": 255,
        "scale": 1.0
    },
    "animated": {
        "gif_path": None, # Path relative to user_uploads/
        "opacity": 255,
        "scale": 1.0,
        "speed": 100 # Percentage
    }
}

# Default application configuration
DEFAULT_APP_CONFIG = {
    "overlay_x": None, 
    "overlay_y": None
}

class StateManager:
    """Manages shared state: crosshair settings and app configuration."""
    def __init__(self, user_data_dir):
        self._lock = threading.Lock()
        self._settings = copy.deepcopy(DEFAULT_SETTINGS)
        self._app_config = copy.deepcopy(DEFAULT_APP_CONFIG)
        
        # Ensure user data directory exists
        self._user_data_dir = user_data_dir
        os.makedirs(self._user_data_dir, exist_ok=True)
        
        self._config_file_path = os.path.join(self._user_data_dir, 'config.json')
        self._load_app_config()

    # --- Crosshair Settings Methods ---
    def get_settings(self):
        """Returns a deep copy of the current crosshair settings (thread-safe)."""
        with self._lock:
            return copy.deepcopy(self._settings)

    def update_settings(self, new_settings):
        """Updates the internal crosshair settings dictionary (thread-safe).
        Assumes validation has happened externally.
        """
        settings_copy = copy.deepcopy(new_settings)
        with self._lock:
            self._settings = settings_copy
            print(f"State Manager: Crosshair settings updated.")

    # --- Application Configuration Methods ---
    def _load_app_config(self):
        """Loads application configuration from config.json."""
        with self._lock:
            try:
                if os.path.exists(self._config_file_path):
                    with open(self._config_file_path, 'r') as f:
                        loaded_config = json.load(f)
                        print(f"State Manager [Load]: Read from file: {loaded_config}") # Log read data
                        # Merge loaded config with defaults to handle missing keys
                        self._app_config.update(loaded_config)
                        print(f"State Manager [Load]: Merged config: {self._app_config}") # Log merged data
                else:
                    print(f"State Manager: No config file found at {self._config_file_path}, using defaults.")
                    # Save defaults if file doesn't exist
                    self._save_app_config_nolock()
            except (json.JSONDecodeError, IOError) as e:
                print(f"State Manager: Error loading config file {self._config_file_path}: {e}. Using defaults.")
                self._app_config = copy.deepcopy(DEFAULT_APP_CONFIG)

    def _save_app_config_nolock(self):
        """Saves the current application configuration to config.json (no lock)."""
        try:
            config_to_save = copy.deepcopy(self._app_config) # Copy before saving
            print(f"State Manager [Save]: Attempting to write: {config_to_save} to {self._config_file_path}")
            with open(self._config_file_path, 'w') as f:
                json.dump(config_to_save, f, indent=4)
            print(f"State Manager [Save]: Successfully wrote config.")
        except IOError as e:
            print(f"State Manager [Save]: Error writing config file {self._config_file_path}: {e}")

    def get_app_config(self):
        """Returns a copy of the current application configuration (thread-safe)."""
        with self._lock:
            return copy.deepcopy(self._app_config)

    def update_app_config(self, key, value):
        """Updates a specific key in the app config and saves it (thread-safe)."""
        with self._lock:
            if key in self._app_config:
                self._app_config[key] = value
                print(f"State Manager [Update]: Updated '{key}' to '{value}'. Current config: {self._app_config}") # Log before save
                self._save_app_config_nolock()
            else:
                print(f"State Manager: Warning - Attempted to update unknown config key '{key}'.")

    # --- Profile Management Methods (Basic stubs) ---

    # def save_profile(self, name):
    #     # ... logic to save self._settings to profiles/<name>.json ...
    #     pass

    # def load_profile(self, name):
    #     # ... logic to load from profiles/<name>.json, validate, update self._settings ...
    #     pass

    # def list_profiles(self):
    #     # ... logic to scan profiles/ directory ...
    #     pass

    # def delete_profile(self, name):
    #     # ... logic to delete profiles/<name>.json ...
    #     pass 