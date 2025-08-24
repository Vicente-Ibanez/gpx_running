"""
This module contains utility functions for data processing.
"""

import os

def check_path_exists(path: str) -> bool:
    """Check if a given path exists."""
    return os.path.exists(path)