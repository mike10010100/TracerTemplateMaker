"""
Application State Module for TracerTemplateMaker

Manages the current runtime state of the application, decoupling data from UI.
"""

from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass
class AppState:
    """Holds the current state of the application's processing parameters."""

    # Image Paths
    current_image_path: Optional[str] = None

    # Processing Parameters
    contrast: float = 1.0
    brightness: float = 1.0
    sharpness: float = 1.0
    blur_kernel: int = 0

    # Layer Parameters
    profile_threshold: int = 200
    profile_tolerance: int = 30
    profile_smoothing: int = 5

    text_threshold: int = 127
    text_tolerance: int = 30
    text_detail: int = 2

    # Colors (BGR)
    bg_color: Tuple[int, int, int] = (255, 255, 255)
    tracer_color: Tuple[int, int, int] = (0, 255, 255)
    text_color: Tuple[int, int, int] = (0, 0, 0)

    # Dimensions
    width_mm: float = 100.0
    height_mm: float = 50.0

    # STL Options
    thickness: float = 2.0
    separate_text: bool = False

    def to_dict(self):
        """Convert state to dictionary for serialization."""
        return {
            "contrast": self.contrast,
            "brightness": self.brightness,
            "sharpness": self.sharpness,
            "blur_kernel": self.blur_kernel,
            "profile_threshold": self.profile_threshold,
            "profile_tolerance": self.profile_tolerance,
            "profile_smoothing": self.profile_smoothing,
            "text_threshold": self.text_threshold,
            "text_tolerance": self.text_tolerance,
            "text_detail": self.text_detail,
            "bg_color": list(self.bg_color),
            "tracer_color": list(self.tracer_color),
            "text_color": list(self.text_color),
            "thickness": self.thickness,
            "separate_text": self.separate_text,
            "last_width": self.width_mm,
            "last_height": self.height_mm,
        }

    def load_from_dict(self, data: dict):
        """Update state from a dictionary."""
        self.contrast = data.get("contrast", 1.0)
        self.brightness = data.get("brightness", 1.0)
        self.sharpness = data.get("sharpness", 1.0)
        self.blur_kernel = data.get("blur_kernel", 0)
        self.profile_threshold = data.get("profile_threshold", 200)
        self.profile_tolerance = data.get("profile_tolerance", 30)
        self.profile_smoothing = data.get("profile_smoothing", 5)
        self.text_threshold = data.get("text_threshold", 127)
        self.text_tolerance = data.get("text_tolerance", 30)
        self.text_detail = data.get("text_detail", 2)

        # Colors need to be converted to tuples
        if "bg_color" in data:
            self.bg_color = tuple(data["bg_color"])
        if "tracer_color" in data:
            self.tracer_color = tuple(data["tracer_color"])
        if "text_color" in data:
            self.text_color = tuple(data["text_color"])

        self.thickness = data.get("thickness", 2.0)
        self.separate_text = data.get("separate_text", False)
        self.width_mm = data.get("last_width", 100.0)
        self.height_mm = data.get("last_height", 50.0)
