"""
STL Generator Module for TracerTemplateMaker

This module handles conversion of SVG/masks to 3D STL models:
- Extrusion of 2D profiles into 3D models
- Dimensional accuracy maintenance
- Multi-layer extrusion for dual-color printing
- STL file export
"""

from typing import Optional

import cv2
import numpy as np
import trimesh

from modules.logger import setup_logger

logger = setup_logger("STLGenerator")


class STLGenerator:
    """
    Generates 3D STL models from 2D masks with accurate dimensions.
    """

    def __init__(self, width_mm: float, height_mm: float):
        """
        Initialize STL generator with target dimensions.

        Args:
            width_mm: Width in millimeters
            height_mm: Height in millimeters
        """
        self.width_mm = width_mm
        self.height_mm = height_mm
        self.scale_factor = 1.0

    def set_scale_factor(self, pixel_width: int, pixel_height: int):
        """
        Calculate scale factor from pixels to millimeters.

        Args:
            pixel_width: Width of source image in pixels
            pixel_height: Height of source image in pixels
        """
        self.scale_factor = self.width_mm / pixel_width

    def extrude_mask_to_mesh(
        self, binary_mask: np.ndarray, thickness_mm: float, base_height_mm: float = 0.0
    ) -> trimesh.Trimesh:
        """
        Extrude a 2D binary mask into a 3D mesh with proper hole handling.

        Args:
            binary_mask: Binary image mask (white = solid, black = hole)
            thickness_mm: Thickness of extrusion in millimeters
            base_height_mm: Height of the base (0 = starts at Z=0)

        Returns:
            trimesh.Trimesh: Watertight 3D mesh object with holes as voids
        """
        # Set scale factor
        height, width = binary_mask.shape
        self.set_scale_factor(width, height)

        # Find contours with hierarchy information
        contours, hierarchy = cv2.findContours(
            binary_mask,
            cv2.RETR_CCOMP,  # Get both outer and inner contours
            cv2.CHAIN_APPROX_SIMPLE,
        )

        if len(contours) == 0:
            # Return empty mesh if no contours found
            return trimesh.Trimesh()

        # Safety check: Filter out tiny contours (noise) and limit total count
        MIN_CONTOUR_AREA = 0.01  # mm² (very small, just noise filtering)
        MAX_CONTOURS = 1000

        # Calculate contour areas and filter
        contour_data = []
        for i, c in enumerate(contours):
            area_pixels = cv2.contourArea(c)
            area_mm = area_pixels * (self.scale_factor**2)
            if area_mm >= MIN_CONTOUR_AREA or len(c) >= 3:
                contour_data.append((i, c, area_mm))

        # If too many contours, keep only the largest ones
        if len(contour_data) > MAX_CONTOURS:
            logger.warning(f"Too many contours ({len(contour_data)}), limiting to {MAX_CONTOURS}")
            # Sort by area and keep largest
            contour_data.sort(key=lambda x: x[2], reverse=True)
            contour_data = contour_data[:MAX_CONTOURS]

            # Rebuild contours and hierarchy
            filtered_contours = [c for _, c, _ in contour_data]
            temp_mask = np.zeros_like(binary_mask)
            cv2.drawContours(temp_mask, filtered_contours, -1, 255, -1)
            contours, hierarchy = cv2.findContours(
                temp_mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE
            )
            logger.info(f"Reduced to {len(contours)} contours after filtering")
        elif len(contour_data) < len(contours):
            logger.info(f"Filtered out {len(contours) - len(contour_data)} tiny contours (noise)")
            filtered_contours = [c for _, c, _ in contour_data]
            temp_mask = np.zeros_like(binary_mask)
            cv2.drawContours(temp_mask, filtered_contours, -1, 255, -1)
            contours, hierarchy = cv2.findContours(
                temp_mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE
            )

        # Hierarchy format: [Next, Previous, First_Child, Parent]
        # hierarchy[0][i][3] == -1 means outer contour (no parent)
        # hierarchy[0][i][3] != -1 means inner contour (has parent, it's a hole)

        all_meshes = []

        # Process each outer contour and its holes
        for idx, contour in enumerate(contours):
            if len(contour) < 3:
                continue

            # Check if this is an outer contour
            if hierarchy[0][idx][3] != -1:
                continue  # Skip inner contours, we'll process them with their parent

            # This is an outer contour - scale it to millimeters
            outer_polygon = self._scale_contour_to_mm(contour)

            # Find all holes for this outer contour
            holes = []
            for hole_idx, hole_contour in enumerate(contours):
                if len(hole_contour) < 3:
                    continue
                # Check if this contour is a child of current outer contour
                if hierarchy[0][hole_idx][3] == idx:
                    hole_polygon = self._scale_contour_to_mm(hole_contour)
                    holes.append(hole_polygon)

            # Create polygon with holes using trimesh
            try:
                # Create 2D polygon with holes
                from shapely.geometry import Polygon

                # Safety check: Skip polygons with too many vertices (potential hang)
                MAX_VERTICES = 5000
                if len(outer_polygon) > MAX_VERTICES:
                    logger.warning(
                        f"Contour {idx} has too many vertices ({len(outer_polygon)}), "
                        "simplifying..."
                    )
                    # Simplify the polygon
                    epsilon = 0.01 * cv2.arcLength(contour, True)
                    simplified = cv2.approxPolyDP(contour, epsilon, True)
                    outer_polygon = self._scale_contour_to_mm(simplified)

                if len(holes) > 0:
                    # Limit number of holes to prevent complexity explosion
                    MAX_HOLES = 100
                    if len(holes) > MAX_HOLES:
                        logger.warning(
                            f"Contour {idx} has too many holes ({len(holes)}), "
                            f"limiting to {MAX_HOLES}"
                        )
                        # Sort holes by area and keep largest
                        hole_areas = [Polygon(h).area if len(h) >= 3 else 0 for h in holes]
                        sorted_holes = sorted(zip(hole_areas, holes), reverse=True)
                        holes = [h for _, h in sorted_holes[:MAX_HOLES]]

                    polygon = Polygon(outer_polygon, holes)
                else:
                    polygon = Polygon(outer_polygon)

                # Check if polygon is valid before extruding
                if not polygon.is_valid:
                    logger.warning(f"Invalid polygon for contour {idx}, attempting to fix...")
                    polygon = polygon.buffer(0)  # Fix self-intersections
                    if not polygon.is_valid:
                        raise ValueError("Polygon cannot be fixed")

                # Extrude polygon to 3D mesh
                mesh = trimesh.creation.extrude_polygon(polygon, height=thickness_mm)

                # Translate mesh to correct base height
                if base_height_mm != 0.0:
                    mesh.apply_translation([0, 0, base_height_mm])

                all_meshes.append(mesh)

            except Exception as e:
                # If polygon creation fails, fall back to simple extrusion
                logger.warning(f"Polygon extrusion failed for contour {idx}: {e}")
                # Create simple mesh without holes as fallback
                fallback_mesh = self._create_simple_extrusion(
                    outer_polygon, thickness_mm, base_height_mm
                )
                if fallback_mesh is not None:
                    all_meshes.append(fallback_mesh)

        # Combine all meshes
        if len(all_meshes) == 0:
            return trimesh.Trimesh()
        elif len(all_meshes) == 1:
            return all_meshes[0]
        else:
            return trimesh.util.concatenate(all_meshes)

    def _scale_contour_to_mm(self, contour: np.ndarray) -> np.ndarray:
        """
        Scale a contour from pixels to millimeters.

        Args:
            contour: OpenCV contour array

        Returns:
            np.ndarray: Scaled 2D points in mm
        """
        points_2d = []
        for point in contour:
            x = point[0][0] * self.scale_factor
            y = point[0][1] * self.scale_factor
            points_2d.append([x, y])
        return np.array(points_2d)

    def _create_simple_extrusion(
        self, polygon: np.ndarray, thickness_mm: float, base_height_mm: float
    ) -> Optional[trimesh.Trimesh]:
        """
        Create simple extrusion without holes (fallback method).

        Args:
            polygon: 2D points in mm
            thickness_mm: Extrusion thickness
            base_height_mm: Base height

        Returns:
            Optional[trimesh.Trimesh]: Simple extruded mesh or None
        """
        try:
            from shapely.geometry import Polygon as ShapelyPolygon

            poly = ShapelyPolygon(polygon)
            mesh = trimesh.creation.extrude_polygon(poly, height=thickness_mm)
            if base_height_mm != 0.0:
                mesh.apply_translation([0, 0, base_height_mm])
            return mesh
        except Exception:
            return None

    def close_mesh_caps(
        self, mesh: trimesh.Trimesh, binary_mask: np.ndarray, base_height: float, thickness: float
    ) -> trimesh.Trimesh:
        """
        Verify mesh is watertight (should already be from extrude_polygon).

        Args:
            mesh: Input mesh
            binary_mask: Binary mask (not used, kept for compatibility)
            base_height: Z-height of bottom (not used, kept for compatibility)
            thickness: Extrusion thickness (not used, kept for compatibility)

        Returns:
            trimesh.Trimesh: Mesh (already watertight from extrude_polygon)
        """
        # The new extrude_polygon method creates watertight meshes automatically
        # This method is kept for compatibility but no longer needs to do anything
        return mesh

    def create_dual_layer_stl(
        self,
        profile_mask: np.ndarray,
        text_mask: np.ndarray,
        base_thickness_mm: float,
        text_height_mm: float,
        output_path: str,
    ) -> str:
        """
        Create STL with two layers for dual-color 3D printing:
        - Base layer: Main profile with holes (Z=0 to Z=base_thickness_mm)
        - Text layer: Raised text on TOP of base
          (Z=base_thickness_mm to Z=base_thickness_mm+text_height_mm)

        Args:
            profile_mask: Binary mask for base profile
            text_mask: Binary mask for text
            base_thickness_mm: Thickness of base layer
            text_height_mm: Additional height for text layer (raised on top)
            output_path: Path to save STL file

        Returns:
            str: Path to saved STL file
        """
        # Create base mesh (starts at Z=0, goes up to base_thickness_mm)
        base_mesh = self.extrude_mask_to_mesh(profile_mask, base_thickness_mm, 0.0)

        # Create text mesh ON TOP of base (starts at Z=base_thickness_mm, goes up by text_height_mm)
        # This creates raised text on the TOP surface of the card
        text_mesh = self.extrude_mask_to_mesh(text_mask, text_height_mm, base_thickness_mm)

        # Combine meshes
        if len(text_mesh.vertices) > 0:
            combined_mesh = trimesh.util.concatenate([base_mesh, text_mesh])
        else:
            combined_mesh = base_mesh

        # Mirror flip the mesh on Y-axis so text side is on TOP when placed on build plate
        # This flips the model vertically (top becomes bottom)
        import numpy as np

        # Create Y-axis mirror transformation matrix
        # This reflects across the Y-axis (flips in XZ plane)
        mirror_matrix = np.array(
            [
                [1, 0, 0, 0],  # Keep X
                [0, 1, 0, 0],  # Keep Y
                [0, 0, -1, 0],  # Flip Z (mirror on Y-axis)
                [0, 0, 0, 1],
            ]
        )
        combined_mesh.apply_transform(mirror_matrix)

        # After flipping, translate back to Z=0 (move to build plate)
        # Find the minimum Z value
        min_z = combined_mesh.bounds[0][2]
        if min_z < 0:
            combined_mesh.apply_translation([0, 0, -min_z])

        # Ensure proper mesh orientation (fix any inverted normals)
        # Safety check: Skip fix_normals() on very complex meshes (can hang)
        MAX_FACES_FOR_FIX_NORMALS = 100000
        if len(combined_mesh.faces) <= MAX_FACES_FOR_FIX_NORMALS:
            try:
                combined_mesh.fix_normals()
            except Exception as e:
                logger.warning(f"Could not fix normals: {e}")
                # Continue anyway - mesh might still be usable
        else:
            logger.warning(
                f"Mesh too complex ({len(combined_mesh.faces)} faces), skipping fix_normals()"
            )

        # Export to STL
        combined_mesh.export(output_path)
        return output_path

    def create_simple_stl(
        self, binary_mask: np.ndarray, thickness_mm: float, output_path: str
    ) -> str:
        """
        Create simple single-layer STL from binary mask.

        Args:
            binary_mask: Binary image mask
            thickness_mm: Extrusion thickness in mm
            output_path: Path to save STL file

        Returns:
            str: Path to saved STL file
        """
        # Create mesh
        tri_mesh = self.extrude_mask_to_mesh(binary_mask, thickness_mm, 0.0)

        # Export to STL
        tri_mesh.export(output_path)
        return output_path

    def create_template_stl(
        self,
        profile_mask: np.ndarray,
        text_mask: Optional[np.ndarray],
        thickness_mm: float,
        output_path: str,
        separate_text: bool = False,
    ) -> str:
        """
        Create STL model of tracing template.

        Args:
            profile_mask: Binary mask for outer profile and holes
            text_mask: Binary mask for text (optional)
            thickness_mm: Thickness of the template card
            output_path: Path to save STL file
            separate_text: If True and text_mask provided, create raised text

        Returns:
            str: Path to saved STL file
        """
        if text_mask is not None and separate_text:
            # Create dual-layer model with raised text
            # Text is always 0.2mm high on top of the base
            text_height = 0.2  # Fixed 0.2mm height for text layer
            return self.create_dual_layer_stl(
                profile_mask,
                text_mask,
                thickness_mm,  # Base is full thickness
                text_height,  # Text is fixed 0.2mm raised on top
                output_path,
            )
        else:
            # Create simple flat template
            # If text_mask exists, combine it with profile
            if text_mask is not None:
                combined_mask = cv2.bitwise_or(profile_mask, text_mask)
            else:
                combined_mask = profile_mask

            return self.create_simple_stl(combined_mask, thickness_mm, output_path)

    def get_mesh_stats(self, mesh: trimesh.Trimesh) -> dict:
        """
        Get statistics about the mesh for verification.

        Args:
            mesh: Trimesh object

        Returns:
            dict: Statistics including volume, area, bounds, etc.
        """
        bounds = mesh.bounds

        # Handle empty mesh case
        if bounds is None or len(mesh.vertices) == 0:
            return {
                "vertices": 0,
                "faces": 0,
                "volume_mm3": 0.0,
                "area_mm2": 0.0,
                "is_watertight": False,
                "bounds_min": [0, 0, 0],
                "bounds_max": [0, 0, 0],
                "dimensions_mm": [0, 0, 0],
            }

        return {
            "vertices": len(mesh.vertices),
            "faces": len(mesh.faces),
            "volume_mm3": mesh.volume,
            "area_mm2": mesh.area,
            "is_watertight": mesh.is_watertight,
            "bounds_min": bounds[0].tolist(),
            "bounds_max": bounds[1].tolist(),
            "dimensions_mm": (bounds[1] - bounds[0]).tolist(),
        }

    def validate_dimensions(self, mesh: trimesh.Trimesh, tolerance_mm: float = 0.1) -> bool:
        """
        Validate that mesh dimensions match expected dimensions.
        CRITICAL for dimensional accuracy.

        Args:
            mesh: Trimesh object to validate
            tolerance_mm: Acceptable tolerance in millimeters

        Returns:
            bool: True if dimensions are within tolerance
        """
        bounds = mesh.bounds

        # Handle empty mesh case
        if bounds is None or len(mesh.vertices) == 0:
            return False

        actual_width = bounds[1][0] - bounds[0][0]
        actual_height = bounds[1][1] - bounds[0][1]

        width_ok = abs(actual_width - self.width_mm) <= tolerance_mm
        height_ok = abs(actual_height - self.height_mm) <= tolerance_mm

        return width_ok and height_ok

    def preview_mesh(self, mesh: trimesh.Trimesh) -> trimesh.Scene:
        """
        Create a preview scene of the mesh.

        Args:
            mesh: Trimesh object

        Returns:
            trimesh.Scene: Scene object for rendering
        """
        scene = trimesh.Scene(mesh)
        return scene
