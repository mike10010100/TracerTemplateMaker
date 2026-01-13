#!/usr/bin/env python3
"""
Test STL generation edge cases to ensure robustness.
"""

import cv2
import numpy as np

from modules.stl_generator import STLGenerator


def test_empty_mask():
    """Test with empty mask (all black)."""
    print("\n" + "=" * 60)
    print("TEST 1: Empty Mask (all black)")
    print("=" * 60)

    empty_mask = np.zeros((100, 100), dtype=np.uint8)
    generator = STLGenerator(width_mm=50.0, height_mm=50.0)

    try:
        mesh = generator.extrude_mask_to_mesh(empty_mask, 2.0)
        stats = generator.get_mesh_stats(mesh)
        print("✅ Handled empty mask gracefully")
        print(f"   Vertices: {stats['vertices']}")
        print(f"   Is watertight: {stats['is_watertight']}")
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False

    return True


def test_no_holes():
    """Test with solid rectangle (no holes)."""
    print("\n" + "=" * 60)
    print("TEST 2: Solid Rectangle (no holes)")
    print("=" * 60)

    solid_mask = np.ones((100, 100), dtype=np.uint8) * 255
    cv2.rectangle(solid_mask, (10, 10), (90, 90), 255, -1)

    generator = STLGenerator(width_mm=50.0, height_mm=50.0)

    try:
        mesh = generator.extrude_mask_to_mesh(solid_mask, 2.0)
        stats = generator.get_mesh_stats(mesh)
        print("✅ Generated solid mesh")
        print(f"   Vertices: {stats['vertices']}")
        print(f"   Is watertight: {stats['is_watertight']}")

        if not stats["is_watertight"]:
            print("❌ FAILED: Mesh should be watertight")
            return False

    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False

    return True


def test_multiple_holes():
    """Test with multiple disconnected holes."""
    print("\n" + "=" * 60)
    print("TEST 3: Multiple Holes")
    print("=" * 60)

    mask = np.ones((200, 400), dtype=np.uint8) * 255
    cv2.rectangle(mask, (20, 20), (380, 180), 255, -1)

    # Add 5 holes
    cv2.circle(mask, (80, 100), 20, 0, -1)
    cv2.circle(mask, (160, 100), 20, 0, -1)
    cv2.circle(mask, (240, 100), 20, 0, -1)
    cv2.circle(mask, (320, 100), 20, 0, -1)
    cv2.rectangle(mask, (150, 40), (250, 70), 0, -1)  # Rectangle hole

    generator = STLGenerator(width_mm=100.0, height_mm=50.0)

    try:
        mesh = generator.extrude_mask_to_mesh(mask, 2.0)
        stats = generator.get_mesh_stats(mesh)
        print("✅ Generated mesh with multiple holes")
        print(f"   Vertices: {stats['vertices']}")
        print(f"   Faces: {stats['faces']}")
        print(f"   Is watertight: {stats['is_watertight']}")

        if not stats["is_watertight"]:
            print("❌ FAILED: Mesh should be watertight")
            return False

    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False

    return True


def test_nested_contours():
    """Test with nested contours (hole within hole)."""
    print("\n" + "=" * 60)
    print("TEST 4: Nested Contours")
    print("=" * 60)

    mask = np.ones((200, 200), dtype=np.uint8) * 255
    cv2.rectangle(mask, (20, 20), (180, 180), 255, -1)  # Outer

    # Create hole
    cv2.circle(mask, (100, 100), 50, 0, -1)
    # Create island within hole (should be separate solid piece)
    cv2.circle(mask, (100, 100), 20, 255, -1)

    generator = STLGenerator(width_mm=50.0, height_mm=50.0)

    try:
        mesh = generator.extrude_mask_to_mesh(mask, 2.0)
        stats = generator.get_mesh_stats(mesh)
        print("✅ Generated mesh with nested contours")
        print(f"   Vertices: {stats['vertices']}")
        print(f"   Faces: {stats['faces']}")
        print(f"   Is watertight: {stats['is_watertight']}")

        if not stats["is_watertight"]:
            print("❌ FAILED: Mesh should be watertight")
            return False

    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False

    return True


def test_dual_layer_stl():
    """Test dual-layer STL creation."""
    print("\n" + "=" * 60)
    print("TEST 5: Dual Layer STL")
    print("=" * 60)

    # Profile mask
    profile = np.ones((100, 200), dtype=np.uint8) * 255
    cv2.rectangle(profile, (10, 10), (190, 90), 255, -1)
    cv2.circle(profile, (50, 50), 15, 0, -1)  # Hole

    # Text mask
    text = np.zeros((100, 200), dtype=np.uint8)
    cv2.putText(text, "TEST", (60, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, 255, 2)

    generator = STLGenerator(width_mm=100.0, height_mm=50.0)

    try:
        output_path = "/tmp/test_dual_layer.stl"
        stl_path = generator.create_dual_layer_stl(profile, text, 2.0, 0.5, output_path)
        print(f"✅ Generated dual-layer STL: {stl_path}")

    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False

    return True


def test_none_text_mask():
    """Test create_template_stl with None text mask."""
    print("\n" + "=" * 60)
    print("TEST 6: None Text Mask")
    print("=" * 60)

    profile = np.ones((100, 200), dtype=np.uint8) * 255
    cv2.rectangle(profile, (10, 10), (190, 90), 255, -1)

    generator = STLGenerator(width_mm=100.0, height_mm=50.0)

    try:
        output_path = "/tmp/test_no_text.stl"
        stl_path = generator.create_template_stl(
            profile, None, 2.0, output_path, separate_text=False
        )
        print(f"✅ Generated STL with None text mask: {stl_path}")

    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False

    return True


def main():
    """Run all edge case tests."""
    print("╔" + "=" * 58 + "╗")
    print("║  STL GENERATOR EDGE CASE TESTS                           ║")
    print("╚" + "=" * 58 + "╝")

    tests = [
        ("Empty Mask", test_empty_mask),
        ("No Holes", test_no_holes),
        ("Multiple Holes", test_multiple_holes),
        ("Nested Contours", test_nested_contours),
        ("Dual Layer", test_dual_layer_stl),
        ("None Text Mask", test_none_text_mask),
    ]

    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"❌ {name} crashed: {e}")
            results.append((name, False))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {name}")

    print("=" * 60)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 60)

    return passed == total


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
