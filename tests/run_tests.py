#!/usr/bin/env python3
"""
Test Runner for TracerTemplateMaker

Discovers and runs all tests in the 'tests' directory.
"""

import os
import sys
import unittest


def run_tests():
    # Add project root to path so we can import modules
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, project_root)

    # Discover tests
    loader = unittest.TestLoader()
    start_dir = os.path.dirname(os.path.abspath(__file__))
    suite = loader.discover(start_dir, pattern="test_*.py")

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(run_tests())
