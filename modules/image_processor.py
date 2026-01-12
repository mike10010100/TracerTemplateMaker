"""
Image Processing Module for TracerTemplateMaker

This module handles all image processing operations including:
- Loading and preprocessing images
- Edge detection and contour extraction
- Color separation for background, holes, and text
- Image enhancement (contrast, brightness, sharpness)
"""

import cv2
import numpy as np
from PIL import Image, ImageEnhance
from typing import Tuple, List, Optional


class ImageProcessor:
    """
    Handles image processing operations for tracing template conversion.
    Maintains dimensional accuracy by tracking pixel-to-real-world scaling.
    """

    def __init__(self):
        """Initialize the image processor with default parameters."""
        self.original_image = None
        self.processed_image = None
        self.scale_factor = 1.0  # Pixels per millimeter
        self.actual_width_mm = None
        self.actual_height_mm = None

    def load_image(self, file_path: str) -> np.ndarray:
        """
        Load an image from file path.

        Args:
            file_path: Path to the image file (JPG, PNG, etc.)

        Returns:
            numpy.ndarray: Loaded image in BGR format
        """
        self.original_image = cv2.imread(file_path)
        if self.original_image is None:
            raise ValueError(f"Could not load image from {file_path}")

        self.processed_image = self.original_image.copy()
        return self.original_image

    def set_dimensions(self, width_mm: float, height_mm: float):
        """
        Set the actual physical dimensions of the template for scaling.
        This is CRITICAL for dimensional accuracy.

        Args:
            width_mm: Actual width in millimeters
            height_mm: Actual height in millimeters
        """
        self.actual_width_mm = width_mm
        self.actual_height_mm = height_mm

        if self.original_image is not None:
            img_height, img_width = self.original_image.shape[:2]
            # Calculate scale factor (pixels per mm)
            self.scale_factor = img_width / width_mm

    def adjust_contrast(self, image: np.ndarray, contrast: float) -> np.ndarray:
        """
        Adjust image contrast.

        Args:
            image: Input image (BGR)
            contrast: Contrast factor (0.5 = half, 1.0 = original, 2.0 = double)

        Returns:
            numpy.ndarray: Contrast-adjusted image
        """
        # Convert to PIL for easier enhancement
        pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        enhancer = ImageEnhance.Contrast(pil_image)
        enhanced = enhancer.enhance(contrast)
        # Convert back to OpenCV format
        return cv2.cvtColor(np.array(enhanced), cv2.COLOR_RGB2BGR)

    def adjust_brightness(self, image: np.ndarray, brightness: float) -> np.ndarray:
        """
        Adjust image brightness.

        Args:
            image: Input image (BGR)
            brightness: Brightness factor (0.5 = darker, 1.0 = original, 2.0 = brighter)

        Returns:
            numpy.ndarray: Brightness-adjusted image
        """
        pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        enhancer = ImageEnhance.Brightness(pil_image)
        enhanced = enhancer.enhance(brightness)
        return cv2.cvtColor(np.array(enhanced), cv2.COLOR_RGB2BGR)

    def adjust_sharpness(self, image: np.ndarray, sharpness: float) -> np.ndarray:
        """
        Adjust image sharpness.

        Args:
            image: Input image (BGR)
            sharpness: Sharpness factor (0.0 = blurred, 1.0 = original, 2.0 = sharpened)

        Returns:
            numpy.ndarray: Sharpness-adjusted image
        """
        pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        enhancer = ImageEnhance.Sharpness(pil_image)
        enhanced = enhancer.enhance(sharpness)
        return cv2.cvtColor(np.array(enhanced), cv2.COLOR_RGB2BGR)

    def apply_gaussian_blur(self, image: np.ndarray, kernel_size: int) -> np.ndarray:
        """
        Apply Gaussian blur to reduce noise.

        Args:
            image: Input image (BGR)
            kernel_size: Size of Gaussian kernel (must be odd, e.g., 3, 5, 7)

        Returns:
            numpy.ndarray: Blurred image
        """
        if kernel_size % 2 == 0:
            kernel_size += 1  # Ensure kernel size is odd
        if kernel_size < 1:
            return image
        return cv2.GaussianBlur(image, (kernel_size, kernel_size), 0)

    def extract_color_mask(self, image: np.ndarray, target_color: Tuple[int, int, int],
                          tolerance: int = 30) -> np.ndarray:
        """
        Extract a mask for pixels matching a specific color.
        Useful for separating background, text, or specific features.

        Args:
            image: Input image (BGR)
            target_color: Target color in BGR format (B, G, R)
            tolerance: Color matching tolerance (0-255)

        Returns:
            numpy.ndarray: Binary mask (255 = match, 0 = no match)
        """
        # Convert BGR to HSV for better color matching
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        target_hsv = cv2.cvtColor(np.uint8([[target_color]]), cv2.COLOR_BGR2HSV)[0][0]

        # Define color range based on tolerance
        # Use int() to prevent overflow warnings
        lower = np.array([max(0, int(target_hsv[0]) - tolerance), 50, 50], dtype=np.uint8)
        upper = np.array([min(179, int(target_hsv[0]) + tolerance), 255, 255], dtype=np.uint8)

        # Create mask
        mask = cv2.inRange(hsv, lower, upper)
        return mask

    def detect_edges_canny(self, image: np.ndarray, threshold1: int = 50,
                          threshold2: int = 150) -> np.ndarray:
        """
        Detect edges using Canny edge detection.

        Args:
            image: Input image (BGR or grayscale)
            threshold1: Lower threshold for edge detection
            threshold2: Upper threshold for edge detection

        Returns:
            numpy.ndarray: Binary edge map
        """
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        # Apply Canny edge detection
        edges = cv2.Canny(gray, threshold1, threshold2)
        return edges

    def find_contours(self, binary_image: np.ndarray) -> List[np.ndarray]:
        """
        Find contours in a binary image.

        Args:
            binary_image: Binary image (0 or 255)

        Returns:
            List of contours as numpy arrays
        """
        contours, hierarchy = cv2.findContours(
            binary_image,
            cv2.RETR_TREE,  # Retrieve all contours with hierarchy
            cv2.CHAIN_APPROX_SIMPLE  # Compress contours to save memory
        )
        return contours

    def threshold_image(self, image: np.ndarray, threshold_value: int = 127,
                       inverse: bool = False) -> np.ndarray:
        """
        Apply binary threshold to image.

        Args:
            image: Input image (grayscale or BGR)
            threshold_value: Threshold value (0-255)
            inverse: If True, invert the threshold

        Returns:
            numpy.ndarray: Binary thresholded image
        """
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        threshold_type = cv2.THRESH_BINARY_INV if inverse else cv2.THRESH_BINARY
        _, binary = cv2.threshold(gray, threshold_value, 255, threshold_type)
        return binary

    def separate_layers(self, image: np.ndarray,
                       background_color: Tuple[int, int, int],
                       tracer_color: Tuple[int, int, int],
                       text_color: Tuple[int, int, int],
                       profile_tolerance: int = 30,
                       profile_threshold: int = 200,
                       profile_smoothing: int = 5,
                       text_tolerance: int = 30,
                       text_threshold: int = 127,
                       text_detail: int = 2) -> Tuple[np.ndarray, np.ndarray]:
        """
        Separate image into two layers with independent controls:
        1. Profile layer: Holes (background color showing through tracer)
        2. Text layer: Text and guide lines

        Args:
            image: Input image (BGR)
            background_color: Background/void color (what shows through holes - usually white) (BGR)
            tracer_color: Tracer card color (the card itself - e.g., yellow) (BGR)
            text_color: Text/line color (markings on card - e.g., black) (BGR)
            profile_tolerance: Color matching tolerance for profile (0-100)
            profile_threshold: Threshold for profile/hole detection (0-255, higher=more selective)
            profile_smoothing: Smoothing amount for profile edges (0-10)
            text_tolerance: Color matching tolerance for text (0-100)
            text_threshold: Threshold for text detection (0-255)
            text_detail: Detail preservation level for text (0-10, lower=more detail)

        Returns:
            Tuple of (profile_mask, text_mask) as binary images
        """
        # LAYER 1: Profile/Holes - Extract ONLY the background color (holes/voids)
        # This is where the background shows THROUGH the tracer
        background_mask = self.extract_color_mask(image, background_color, profile_tolerance)

        # Add threshold-based detection for profile (bright areas)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        _, profile_threshold_mask = cv2.threshold(gray, profile_threshold, 255, cv2.THRESH_BINARY)

        # Combine color and threshold for profile
        background_mask = cv2.bitwise_or(background_mask, profile_threshold_mask)

        # LAYER 2: Text - Extract text/line markings
        text_mask_color = self.extract_color_mask(image, text_color, text_tolerance)

        # Also use threshold-based detection for fine details (tick marks, text, etc.)
        _, text_threshold_mask = cv2.threshold(gray, text_threshold, 255, cv2.THRESH_BINARY_INV)

        # Combine color-based and threshold-based text detection
        text_mask = cv2.bitwise_or(text_mask_color, text_threshold_mask)

        # Extract tracer card color to help clean up (use average of tolerances)
        avg_tolerance = (profile_tolerance + text_tolerance) // 2
        tracer_mask = self.extract_color_mask(image, tracer_color, avg_tolerance)

        # Remove text from background mask (text shouldn't be in profile layer)
        background_mask = cv2.bitwise_and(background_mask, cv2.bitwise_not(text_mask))

        # Remove background from text mask (background shouldn't be in text layer)
        text_mask = cv2.bitwise_and(text_mask, cv2.bitwise_not(background_mask))

        # Remove tracer from text mask (only want text, not card color)
        text_mask = cv2.bitwise_and(text_mask, cv2.bitwise_not(tracer_mask))

        # Profile mask is ONLY the background/void areas (holes)
        profile_mask = background_mask

        # Apply smoothing to profile based on smoothing parameter
        if profile_smoothing > 0:
            # Smoothing intensity based on slider value
            kernel_size = min(profile_smoothing * 2 + 1, 11)  # Max 11x11
            if kernel_size >= 3:
                profile_mask = cv2.GaussianBlur(profile_mask, (kernel_size, kernel_size), 0)
                _, profile_mask = cv2.threshold(profile_mask, 127, 255, cv2.THRESH_BINARY)

                # Morphological closing to fill small gaps
                morph_size = max(2, profile_smoothing // 2)
                kernel = np.ones((morph_size, morph_size), np.uint8)
                profile_mask = cv2.morphologyEx(profile_mask, cv2.MORPH_CLOSE, kernel)

        # Apply detail preservation to text based on detail parameter
        # Lower text_detail value = more detail preserved (smaller kernel)
        if text_detail > 0:
            kernel_size = max(2, text_detail)
            text_kernel = np.ones((kernel_size, kernel_size), np.uint8)
            text_mask = cv2.morphologyEx(text_mask, cv2.MORPH_OPEN, text_kernel)

        return profile_mask, text_mask

    def get_pixel_to_mm_scale(self) -> float:
        """
        Get the current pixel-to-millimeter scale factor.
        Essential for maintaining dimensional accuracy.

        Returns:
            float: Pixels per millimeter
        """
        return self.scale_factor

    def process_image(self, contrast: float = 1.0, brightness: float = 1.0,
                     sharpness: float = 1.0, blur_kernel: int = 0) -> np.ndarray:
        """
        Apply all processing steps to the original image.

        Args:
            contrast: Contrast adjustment factor
            brightness: Brightness adjustment factor
            sharpness: Sharpness adjustment factor
            blur_kernel: Gaussian blur kernel size

        Returns:
            numpy.ndarray: Processed image
        """
        if self.original_image is None:
            raise ValueError("No image loaded")

        # Start with original
        result = self.original_image.copy()

        # Apply adjustments in sequence
        if blur_kernel > 0:
            result = self.apply_gaussian_blur(result, blur_kernel)

        result = self.adjust_contrast(result, contrast)
        result = self.adjust_brightness(result, brightness)
        result = self.adjust_sharpness(result, sharpness)

        self.processed_image = result
        return result
