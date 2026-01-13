import unittest

import cv2
import numpy as np

from modules.image_processor import ImageProcessor


class TestImageProcessor(unittest.TestCase):
    """Unit tests for ImageProcessor class."""

    def setUp(self):
        self.processor = ImageProcessor()
        # Create a synthetic image (100x100 RGB)
        # Background: Gray (200, 200, 200) - Allows brightness/contrast checks
        # Card: Blue (255, 0, 0) - BGR - Dark in grayscale (avoid threshold trigger)
        # Text: Black (0, 0, 0)
        self.image = np.ones((100, 100, 3), dtype=np.uint8) * 200

        # Draw "Card" (Blue rect)
        cv2.rectangle(self.image, (20, 20), (80, 80), (255, 0, 0), -1)

        # Draw "Text" (Black circle) inside card
        cv2.circle(self.image, (50, 50), 10, (0, 0, 0), -1)

        # Hole (Gray circle) inside card (matches background)
        cv2.circle(self.image, (30, 30), 5, (200, 200, 200), -1)

        self.processor.original_image = self.image
        self.processor.processed_image = self.image

    def test_initialization(self):
        """Test initial state."""
        self.assertIsNotNone(self.processor.original_image)
        self.assertEqual(self.processor.scale_factor, 1.0)

    def test_set_dimensions(self):
        """Test dimension setting and scale calculation."""
        # Image is 100px wide. Set real width to 50mm.
        # Scale should be 100 / 50 = 2.0 pixels/mm
        self.processor.set_dimensions(50.0, 50.0)
        self.assertEqual(self.processor.scale_factor, 2.0)
        self.assertEqual(self.processor.actual_width_mm, 50.0)

    def test_adjustments(self):
        """Test image adjustments don't crash and return image."""
        # Brightness
        bright = self.processor.adjust_brightness(self.image, 1.5)
        self.assertEqual(bright.shape, self.image.shape)
        self.assertFalse(np.array_equal(bright, self.image))

        # Contrast
        contrast = self.processor.adjust_contrast(self.image, 1.5)
        self.assertEqual(contrast.shape, self.image.shape)

    def test_extract_color_mask(self):
        """Test extracting a specific color."""
        # Extract Blue (Card)
        target_color = (255, 0, 0)
        mask = self.processor.extract_color_mask(self.image, target_color, tolerance=10)

        # Check center pixel (should be white/255 in mask)
        self.assertEqual(mask[50, 50], 0)  # Oops, 50,50 is black circle (text)
        self.assertEqual(mask[25, 25], 255)  # 25,25 is blue card
        self.assertEqual(mask[0, 0], 0)  # 0,0 is gray background

    def test_separate_layers(self):
        """Test full layer separation logic."""
        bg_color = (200, 200, 200)  # Gray
        tracer_color = (255, 0, 0)  # Blue
        text_color = (0, 0, 0)  # Black

        profile_mask, text_mask = self.processor.separate_layers(
            self.image,
            bg_color,
            tracer_color,
            text_color,
            profile_tolerance=10,
            profile_threshold=190,
            text_tolerance=10,
            profile_smoothing=0,
            text_detail=0,
        )

        # Profile Mask: Should capture holes (gray background inside/outside)
        # 0,0 is background -> Should be white in profile mask
        self.assertEqual(profile_mask[0, 0], 255)

        # 30,30 is hole (gray) -> Should be white in profile mask
        self.assertEqual(profile_mask[30, 30], 255)

        # 25,25 is card (blue) -> Should be black in profile mask
        self.assertEqual(profile_mask[25, 25], 0)

        # Text Mask: Should capture text (black)
        # 50,50 is black circle -> Should be white in text mask
        self.assertEqual(text_mask[50, 50], 255)

        # 25,25 is card -> Should be black in text mask
        self.assertEqual(text_mask[25, 25], 0)


if __name__ == "__main__":
    unittest.main()
