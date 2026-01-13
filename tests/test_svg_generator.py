import os
import shutil
import unittest

import numpy as np

from modules.svg_generator import SVGGenerator


class TestSVGGenerator(unittest.TestCase):
    """Unit tests for SVGGenerator class."""

    def setUp(self):
        self.output_dir = "/tmp/tracer_test_svg"
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        self.generator = SVGGenerator(width_mm=100.0, height_mm=50.0)

    def tearDown(self):
        if os.path.exists(self.output_dir):
            shutil.rmtree(self.output_dir)

    def test_initialization(self):
        """Test initial dimensions."""
        self.assertEqual(self.generator.width_mm, 100.0)
        self.assertEqual(self.generator.height_mm, 50.0)

    def test_set_scale_factor(self):
        """Test scale factor calculation."""
        # 100mm width, 200px image width -> 0.5 mm/pixel
        self.generator.set_scale_factor(200, 100)
        self.assertEqual(self.generator.scale_factor, 0.5)

    def test_contour_to_path(self):
        """Test converting contour to SVG path."""
        # Create a simple square contour (4 points)
        # 10,10 to 20,20
        contour = np.array([[[10, 10]], [[20, 10]], [[20, 20]], [[10, 20]]], dtype=np.int32)

        self.generator.scale_factor = 1.0
        path_data = self.generator.contour_to_path_data(contour, simplify=False)

        # Expected: M 10.000,10.000 L 20.000,10.000 L 20.000,20.000 L 10.000,20.000 Z
        self.assertTrue(path_data.startswith("M 10.000,10.000"))
        self.assertTrue(path_data.endswith("Z"))
        self.assertIn("L 20.000,10.000", path_data)

    def test_create_layered_svg(self):
        """Test generating a full SVG file."""
        # Create dummy masks
        profile_mask = np.zeros((100, 200), dtype=np.uint8)
        # Add a square to profile
        profile_mask[10:90, 10:90] = 255

        text_mask = np.zeros((100, 200), dtype=np.uint8)
        # Add a small square to text
        text_mask[40:60, 40:60] = 255

        output_file = os.path.join(self.output_dir, "test.svg")

        self.generator.create_layered_svg(profile_mask, text_mask, output_file)

        self.assertTrue(os.path.exists(output_file))

        # Check content basics
        with open(output_file, "r") as f:
            content = f.read()
            self.assertIn('width="100.0mm"', content)
            self.assertIn('height="50.0mm"', content)
            self.assertIn('id="layer_1_profile_and_holes"', content)
            self.assertIn('id="layer_2_text_and_markings"', content)


if __name__ == "__main__":
    unittest.main()
