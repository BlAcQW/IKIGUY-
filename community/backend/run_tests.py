#!/usr/bin/env python
"""
Test runner script that properly configures imports and runs the test suite.
"""

import sys
import os

# Add backend directory to Python path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

# Now run pytest
if __name__ == "__main__":
    import pytest

    # Run tests with proper configuration
    exit_code = pytest.main([
        "tests/",
        "-v",
        "--tb=short",
        "-p", "no:warnings",
        "-x",  # Stop on first failure for debugging
    ])

    sys.exit(exit_code)
