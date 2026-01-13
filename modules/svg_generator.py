"""
SVG Generator Module for TracerTemplateMaker

This module handles conversion of processed images to SVG vector format with:
- Dimensionally accurate scaling
- Multi-layer support (profile layer and text layer)
- Contour-to-path conversion
- Bezier curve optimization
"""

from typing import List, Sequence, Tuple

import cv2
import numpy as np
import svgwrite


class SVGGenerator:
    """
    Generates SVG files from processed images with accurate dimensions and layers.
    """

    def __init__(self, width_mm: float, height_mm: float):
        """
        Initialize SVG generator with target dimensions.

        Args:
            width_mm: Output width in millimeters
            height_mm: Height in millimeters
        """
        self.width_mm = width_mm
        self.height_mm = height_mm
        self.scale_factor = 1.0  # Will be set when processing image

    def set_scale_factor(self, pixel_width: int, pixel_height: int):
        """
        Calculate scale factor from pixel dimensions to mm.

        Args:
            pixel_width: Width of source image in pixels
            pixel_height: Height of source image in pixels
        """
        # Scale factor to convert from pixels to mm
        self.scale_factor = self.width_mm / pixel_width

    def contour_to_path_data(self, contour: np.ndarray, simplify: bool = True) -> str:
        """
        Convert OpenCV contour to SVG path data string.

        Args:
            contour: OpenCV contour array
            simplify: If True, apply Douglas-Peucker simplification

        Returns:
            str: SVG path data (e.g., "M10,10 L20,20 Z")
        """
        if simplify:
            # Simplify contour to reduce points while maintaining shape
            epsilon = 0.001 * cv2.arcLength(contour, True)
            contour = cv2.approxPolyDP(contour, epsilon, True)

        if len(contour) < 3:
            return ""  # Need at least 3 points for a valid path

        # Start path with Move command
        x_start = contour[0][0][0] * self.scale_factor
        y_start = contour[0][0][1] * self.scale_factor
        path_data = f"M {x_start:.3f},{y_start:.3f}"

        # Add Line commands for each subsequent point
        for point in contour[1:]:
            x = point[0][0] * self.scale_factor
            y = point[0][1] * self.scale_factor
            path_data += f" L {x:.3f},{y:.3f}"

        # Close path
        path_data += " Z"
        return path_data

    def create_svg_from_masks(
        self, profile_mask: np.ndarray, text_mask: np.ndarray, output_path: str
    ) -> str:
        """
        Create SVG file with two layers from binary masks.

        Args:
            profile_mask: Binary mask for outer profile and holes
            text_mask: Binary mask for text and guide lines
            output_path: Path to save SVG file

        Returns:
            str: Path to saved SVG file
        """
        # Set scale factor based on mask dimensions
        height, width = profile_mask.shape
        self.set_scale_factor(width, height)

        # Create SVG drawing with exact dimensions
        dwg = svgwrite.Drawing(
            output_path,
            size=(f"{self.width_mm}mm", f"{self.height_mm}mm"),
            viewBox=f"0 0 {self.width_mm} {self.height_mm}",
        )

        # Add layer groups
        profile_layer = dwg.g(id="profile_layer", fill="none", stroke="black", stroke_width="0.1mm")
        text_layer = dwg.g(id="text_layer", fill="black", stroke="none")

        # Process profile mask - find contours
        profile_contours = self.find_contours_from_mask(profile_mask)

        # Add profile contours to profile layer
        for i, contour in enumerate(profile_contours):
            path_data = self.contour_to_path_data(contour)
            if path_data:
                profile_layer.add(dwg.path(d=path_data, id=f"profile_{i}"))

        # Process text mask - find contours
        text_contours = self.find_contours_from_mask(text_mask)

        # Add text contours to text layer
        for i, contour in enumerate(text_contours):
            path_data = self.contour_to_path_data(contour)
            if path_data:
                text_layer.add(dwg.path(d=path_data, id=f"text_{i}", fill="black"))

        # Add layers to drawing
        dwg.add(profile_layer)
        dwg.add(text_layer)

        # Save SVG file
        dwg.save()
        return output_path

    def find_contours_from_mask(self, mask: np.ndarray) -> Sequence[np.ndarray]:
        """
        Find contours from binary mask.

        Args:
            mask: Binary mask image

        Returns:
            List of contours
        """
        contours, hierarchy = cv2.findContours(
            mask,
            cv2.RETR_CCOMP,  # Retrieve both external and hole contours
            cv2.CHAIN_APPROX_SIMPLE,
        )
        return contours

    def create_simple_svg(
        self,
        binary_mask: np.ndarray,
        output_path: str,
        fill_color: str = "black",
        stroke_color: str = "none",
    ) -> str:
        """
        Create simple single-layer SVG from binary mask.

        Args:
            binary_mask: Binary image mask
            output_path: Path to save SVG
            fill_color: Fill color for shapes
            stroke_color: Stroke color for shapes

        Returns:
            str: Path to saved SVG file
        """
        # Set scale factor
        height, width = binary_mask.shape
        self.set_scale_factor(width, height)

        # Create SVG drawing
        dwg = svgwrite.Drawing(
            output_path,
            size=(f"{self.width_mm}mm", f"{self.height_mm}mm"),
            viewBox=f"0 0 {self.width_mm} {self.height_mm}",
        )

        # Find and add contours
        contours = self.find_contours_from_mask(binary_mask)

        for i, contour in enumerate(contours):
            path_data = self.contour_to_path_data(contour)
            if path_data:
                dwg.add(
                    dwg.path(d=path_data, id=f"shape_{i}", fill=fill_color, stroke=stroke_color)
                )

        dwg.save()
        return output_path

    def optimize_paths(
        self, contours: List[np.ndarray], tolerance: float = 1.0
    ) -> Sequence[np.ndarray]:
        """
        Optimize contour paths by reducing number of points.

        Args:
            contours: List of contours
            tolerance: Simplification tolerance (higher = more aggressive)

        Returns:
            List of optimized contours
        """
        optimized = []
        for contour in contours:
            # Apply Douglas-Peucker algorithm
            epsilon = tolerance * 0.001 * cv2.arcLength(contour, True)
            simplified = cv2.approxPolyDP(contour, epsilon, True)
            optimized.append(simplified)
        return optimized

    def get_svg_bounds(self) -> Tuple[float, float]:
        """
        Get the bounds of the SVG in millimeters.

        Returns:
            Tuple of (width_mm, height_mm)
        """
        return self.width_mm, self.height_mm

    def add_metadata(
        self, dwg: svgwrite.Drawing, description: str = "", creator: str = "TracerTemplateMaker"
    ):
        """
        Add metadata to SVG file.

        Args:
            dwg: SVG Drawing object
            description: Description of the drawing
            creator: Creator/software name
        """
        # Add description element for metadata
        desc_text = f"{description} - Created by {creator}"
        dwg.set_desc(title="Tracing Template", desc=desc_text)

    def create_layered_svg(
        self,
        profile_mask: np.ndarray,
        text_mask: np.ndarray,
        output_path: str,
        include_metadata: bool = True,
    ) -> str:
        """
        Create a complete SVG with properly organized layers.
        This is the main method for generating production SVG files.

        Args:
            profile_mask: Binary mask for outer profile and cutouts
            text_mask: Binary mask for text and markings
            output_path: Path to save SVG file
            include_metadata: Whether to include metadata

        Returns:
            str: Path to saved SVG file
        """
        # Set scale factor
        height, width = profile_mask.shape
        self.set_scale_factor(width, height)

        # Create SVG with proper dimensions
        # Set profile='tiny' to disable strict validation for custom attributes
        dwg = svgwrite.Drawing(
            output_path,
            size=(f"{self.width_mm}mm", f"{self.height_mm}mm"),
            viewBox=f"0 0 {self.width_mm} {self.height_mm}",
            profile="tiny",  # Use 'tiny' profile to allow custom attributes
        )

        # Add metadata if requested
        if include_metadata:
            self.add_metadata(dwg, "Vectorized tracing template with profile and text layers")

        # Layer 1: Profile and holes (for cutting/outline)
        # Using clear IDs instead of Inkscape-specific attributes for compatibility
        profile_layer = dwg.g(
            id="layer_1_profile_and_holes",
            fill="none",  # No fill - just outlines
            stroke="black",
            stroke_width="0.1mm",
            class_="profile-layer",
        )

        # Layer 2: Text and markings (for engraving/secondary color)
        text_layer = dwg.g(
            id="layer_2_text_and_markings",
            fill="none",  # No fill - just outlines for laser cutting/engraving
            stroke="red",  # Different color to distinguish from profile layer
            stroke_width="0.1mm",
            class_="text-layer",
        )

        # Process and add profile contours
        profile_contours = self.find_contours_from_mask(profile_mask)
        for i, contour in enumerate(profile_contours):
            path_data = self.contour_to_path_data(contour, simplify=True)
            if path_data:
                profile_layer.add(dwg.path(d=path_data, id=f"profile_path_{i}"))

        # Process and add text contours
        text_contours = self.find_contours_from_mask(text_mask)
        for i, contour in enumerate(text_contours):
            path_data = self.contour_to_path_data(contour, simplify=True)
            if path_data:
                text_layer.add(dwg.path(d=path_data, id=f"text_path_{i}"))

        # Add layers to drawing in correct order
        dwg.add(profile_layer)
        dwg.add(text_layer)

        # Save the file
        dwg.save()
        return output_path
