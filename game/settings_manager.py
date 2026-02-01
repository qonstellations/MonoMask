import json
import os
import sys

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        # Running from source
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

def get_user_data_path(filename):
    """Get path for user data files (settings, saves) - not bundled"""
    # For bundled app, use user's home directory
    if getattr(sys, 'frozen', False):
        # Running as bundled
        user_dir = os.path.expanduser("~/Library/Application Support/MonoMask")
        os.makedirs(user_dir, exist_ok=True)
        return os.path.join(user_dir, filename)
    else:
        # Running from source
        return filename

SETTINGS_FILE = get_user_data_path("user_settings.json")

DEFAULT_SETTINGS = {
    "fullscreen": False,
    "sensitivity": 1.0,
    "master_volume": 0.5
}

def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        return DEFAULT_SETTINGS.copy()
    
    try:
        with open(SETTINGS_FILE, "r") as f:
            data = json.load(f)
            # Merge with defaults to ensure all keys exist
            settings = DEFAULT_SETTINGS.copy()
            settings.update(data)
            return settings
    except Exception as e:
        print(f"Error loading settings: {e}")
        return DEFAULT_SETTINGS.copy()

def save_settings(settings):
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(settings, f, indent=4)
    except Exception as e:
        print(f"Error saving settings: {e}")
