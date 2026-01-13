"""
Configuration Management Module for TracerTemplateMaker

Handles default settings, constants, and persistence of user preferences.
"""

import json
import os
from typing import Any, Dict

from modules.logger import setup_logger

logger = setup_logger("Config")

# Application Constants
APP_NAME = "TracerTemplateMaker"
VERSION = "1.6.1"
DEFAULT_WINDOW_SIZE = (1400, 800)

# Default Processing Parameters
DEFAULTS = {
    "contrast": 1.0,
    "brightness": 1.0,
    "sharpness": 1.0,
    "blur_kernel": 0,
    "profile_threshold": 200,
    "profile_tolerance": 30,
    "profile_smoothing": 5,
    "text_threshold": 127,
    "text_tolerance": 30,
    "text_detail": 2,
    "bg_color": [255, 255, 255],  # BGR
    "tracer_color": [0, 255, 255],  # BGR
    "text_color": [0, 0, 0],  # BGR
    "thickness": 2.0,
    "separate_text": False,
    "last_width": 100.0,
    "last_height": 50.0,
}


class ConfigManager:
    """Handles loading and saving of user configuration."""

    def __init__(self):
        self.config_dir = os.path.join(os.path.expanduser("~"), ".tracertemplatemaker")
        self.config_path = os.path.join(self.config_dir, "settings.json")
        self.settings = DEFAULTS.copy()
        self.load_settings()

    def load_settings(self):
        """Load settings from JSON file."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r") as f:
                    user_settings = json.load(f)
                    # Update defaults with user settings (prevents issues with new keys)
                    self.settings.update(user_settings)
            except Exception as e:
                logger.error(f"Error loading settings: {e}")

    def save_settings(self, current_settings: Dict[str, Any]):
        """Save current settings to JSON file."""
        self.settings.update(current_settings)

        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)

        try:
            with open(self.config_path, "w") as f:
                json.dump(self.settings, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving settings: {e}")

    def get(self, key: str) -> Any:
        """Get a setting value."""
        return self.settings.get(key, DEFAULTS.get(key))
