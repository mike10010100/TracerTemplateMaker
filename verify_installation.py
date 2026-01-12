#!/usr/bin/env python3
"""
Complete installation and functionality verification script.
Tests all critical imports and core functionality.
"""

import sys

def test_imports():
    """Test all required imports."""
    print("Testing imports...")

    try:
        import numpy
        print("✅ numpy")
    except ImportError as e:
        print(f"❌ numpy: {e}")
        return False

    try:
        import cv2
        print("✅ opencv-python")
    except ImportError as e:
        print(f"❌ opencv-python: {e}")
        return False

    try:
        from PIL import Image
        print("✅ Pillow")
    except ImportError as e:
        print(f"❌ Pillow: {e}")
        return False

    try:
        import svgwrite
        print("✅ svgwrite")
    except ImportError as e:
        print(f"❌ svgwrite: {e}")
        return False

    try:
        from stl import mesh
        print("✅ numpy-stl")
    except ImportError as e:
        print(f"❌ numpy-stl: {e}")
        return False

    try:
        import trimesh
        print("✅ trimesh")
    except ImportError as e:
        print(f"❌ trimesh: {e}")
        return False

    try:
        from shapely.geometry import Polygon
        print("✅ shapely")
    except ImportError as e:
        print(f"❌ shapely: {e}")
        return False

    try:
        import mapbox_earcut
        print("✅ mapbox-earcut")
    except ImportError as e:
        print(f"❌ mapbox-earcut: {e}")
        return False

    try:
        from PyQt6.QtWidgets import QApplication
        print("✅ PyQt6")
    except ImportError as e:
        print(f"❌ PyQt6: {e}")
        return False

    try:
        import skimage
        print("✅ scikit-image")
    except ImportError as e:
        print(f"❌ scikit-image: {e}")
        return False

    return True

def test_modules():
    """Test custom modules."""
    print("\nTesting custom modules...")

    try:
        from modules.image_processor import ImageProcessor
        print("✅ ImageProcessor")
    except ImportError as e:
        print(f"❌ ImageProcessor: {e}")
        return False

    try:
        from modules.svg_generator import SVGGenerator
        print("✅ SVGGenerator")
    except ImportError as e:
        print(f"❌ SVGGenerator: {e}")
        return False

    try:
        from modules.stl_generator import STLGenerator
        print("✅ STLGenerator")
    except ImportError as e:
        print(f"❌ STLGenerator: {e}")
        return False

    try:
        from modules.ui_components import ImagePreviewWidget, ControlPanel
        print("✅ UI Components")
    except ImportError as e:
        print(f"❌ UI Components: {e}")
        return False

    return True

def test_stl_watertight():
    """Quick STL watertight test."""
    print("\nTesting STL generation...")

    try:
        import numpy as np
        import cv2
        from modules.stl_generator import STLGenerator

        # Create simple test mask
        mask = np.ones((100, 100), dtype=np.uint8) * 255
        cv2.rectangle(mask, (20, 20), (80, 80), 255, -1)
        cv2.circle(mask, (50, 50), 10, 0, -1)  # Hole

        # Generate mesh
        generator = STLGenerator(width_mm=50.0, height_mm=50.0)
        mesh = generator.extrude_mask_to_mesh(mask, 2.0)

        # Check watertight
        if mesh.is_watertight:
            print("✅ STL generation creates watertight meshes")
            return True
        else:
            print("❌ STL mesh is not watertight")
            return False

    except Exception as e:
        print(f"❌ STL generation failed: {e}")
        return False

def main():
    """Run all verification tests."""
    print("╔" + "="*58 + "╗")
    print("║  TracerTemplateMaker Installation Verification          ║")
    print("╚" + "="*58 + "╝\n")

    results = []

    # Test imports
    results.append(("Dependencies", test_imports()))

    # Test modules
    results.append(("Custom Modules", test_modules()))

    # Test STL generation
    results.append(("STL Watertight", test_stl_watertight()))

    # Summary
    print("\n" + "="*60)
    print("VERIFICATION SUMMARY")
    print("="*60)

    all_passed = all(success for _, success in results)

    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {name}")

    print("="*60)

    if all_passed:
        print("✅ All tests passed! Installation is complete and working.")
        print("\nYou can now run the application with:")
        print("  python main.py")
        return 0
    else:
        print("❌ Some tests failed. Please check the errors above.")
        print("\nTry reinstalling dependencies:")
        print("  pip install -r requirements.txt")
        return 1

if __name__ == "__main__":
    sys.exit(main())
