#!/usr/bin/env python3
"""
Test script to verify STL generation creates watertight meshes with holes as voids.
"""

import numpy as np
import cv2
from modules.stl_generator import STLGenerator
import trimesh

def create_test_mask():
    """
    Create a test mask with:
    - Outer rectangle (card outline)
    - Inner circles (holes that should remain voids)
    """
    # Create 400x200 image (white background)
    mask = np.ones((200, 400), dtype=np.uint8) * 255

    # Draw outer filled rectangle (representing the yellow card area)
    cv2.rectangle(mask, (20, 20), (380, 180), 255, -1)

    # Draw 3 holes (inner circles that should be voids, in black)
    cv2.circle(mask, (100, 100), 30, 0, -1)  # Hole 1
    cv2.circle(mask, (200, 100), 25, 0, -1)  # Hole 2
    cv2.circle(mask, (300, 100), 20, 0, -1)  # Hole 3

    return mask

def test_stl_generation():
    """Test STL generation and verify watertight mesh."""

    print("Creating test mask with outer boundary and inner holes...")
    test_mask = create_test_mask()

    # Save mask for visual verification
    cv2.imwrite('/tmp/test_mask.png', test_mask)
    print("Test mask saved to: /tmp/test_mask.png")

    # Initialize STL generator with test dimensions
    print("\nInitializing STL generator (100mm x 50mm)...")
    generator = STLGenerator(width_mm=100.0, height_mm=50.0)

    # Generate STL mesh
    print("Generating 3D mesh with 2mm thickness...")
    mesh = generator.extrude_mask_to_mesh(
        binary_mask=test_mask,
        thickness_mm=2.0,
        base_height_mm=0.0
    )

    # Get mesh statistics
    print("\n" + "="*60)
    print("MESH STATISTICS")
    print("="*60)
    stats = generator.get_mesh_stats(mesh)
    for key, value in stats.items():
        print(f"{key}: {value}")

    # Verify watertight
    print("\n" + "="*60)
    print("WATERTIGHT VERIFICATION")
    print("="*60)
    if mesh.is_watertight:
        print("✅ SUCCESS: Mesh is WATERTIGHT!")
    else:
        print("❌ FAILURE: Mesh is NOT watertight")
        print(f"   Mesh has {len(mesh.vertices)} vertices and {len(mesh.faces)} faces")

    # Export STL for external verification
    output_path = '/tmp/test_output.stl'
    mesh.export(output_path)
    print(f"\n✅ STL exported to: {output_path}")
    print("   You can open this file in a 3D viewer to verify:")
    print("   - Outer rectangle is solid")
    print("   - Inner circles remain as empty holes (voids)")

    # Validate dimensions
    print("\n" + "="*60)
    print("DIMENSIONAL ACCURACY")
    print("="*60)
    if generator.validate_dimensions(mesh, tolerance_mm=0.5):
        print("✅ SUCCESS: Dimensions are within tolerance!")
    else:
        print("❌ FAILURE: Dimensions are out of tolerance")
        bounds = mesh.bounds
        actual_width = bounds[1][0] - bounds[0][0]
        actual_height = bounds[1][1] - bounds[0][1]
        print(f"   Expected: {generator.width_mm}mm x {generator.height_mm}mm")
        print(f"   Actual:   {actual_width:.2f}mm x {actual_height:.2f}mm")

    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)

    return mesh.is_watertight

if __name__ == "__main__":
    success = test_stl_generation()
    exit(0 if success else 1)
