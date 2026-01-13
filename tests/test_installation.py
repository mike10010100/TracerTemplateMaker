#!/usr/bin/env python3
"""
Installation Test Script for TracerTemplateMaker

This script verifies that all dependencies are correctly installed
and the application is ready to run.
"""

import importlib
import sys


def test_python_version():
    """Test that Python version is 3.8 or higher."""
    print("Testing Python version...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"✓ Python {version.major}.{version.minor}.{version.micro} - OK")
        return True
    else:
        print(f"✗ Python {version.major}.{version.minor}.{version.micro} - FAILED")
        print("  Python 3.8 or higher required")
        return False


def test_import(module_name, package_name=None):
    """Test if a module can be imported."""
    display_name = package_name or module_name
    try:
        importlib.import_module(module_name)
        print(f"✓ {display_name} - OK")
        return True
    except ImportError as e:
        print(f"✗ {display_name} - FAILED")
        print(f"  Error: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("TracerTemplateMaker - Installation Test")
    print("=" * 60)
    print()

    results = []

    # Test Python version
    results.append(test_python_version())
    print()

    # Test required modules
    print("Testing required packages...")

    modules_to_test = [
        ("cv2", "opencv-python"),
        ("numpy", "numpy"),
        ("PIL", "Pillow"),
        ("svgwrite", "svgwrite"),
        ("trimesh", "trimesh"),
        ("PyQt6.QtWidgets", "PyQt6"),
        ("PyQt6.QtCore", "PyQt6-Core"),
        ("PyQt6.QtGui", "PyQt6-GUI"),
    ]

    for module, package in modules_to_test:
        results.append(test_import(module, package))

    print()
    print("=" * 60)

    # Summary
    passed = sum(results)
    total = len(results)

    if passed == total:
        print(f"SUCCESS: All {total} tests passed!")
        print()
        print("You're ready to run TracerTemplateMaker!")
        print("Start the application with: python main.py")
        return 0
    else:
        failed = total - passed
        print(f"FAILED: {failed} of {total} tests failed")
        print()
        print("Please install missing packages:")
        print("  pip install .")
        return 1


if __name__ == "__main__":
    sys.exit(main())
