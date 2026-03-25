"""
Utility functions for ffedit.
"""
import os

def file_exists(path):
    return os.path.isfile(path)

def ensure_dir(path):
    os.makedirs(path, exist_ok=True)
