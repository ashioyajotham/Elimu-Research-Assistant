"""
Elimu Research Assistant - An intelligent research tool for Kenyan educators.
"""
from pathlib import Path

def _get_version():
    """Get version from VERSION file"""
    try:
        version_file = Path(__file__).parent / "VERSION"
        return version_file.read_text().strip()
    except:
        return "development"

__version__ = _get_version()
__author__ = "Ashioya Jotham"
__email__ = "victorashioya960@gmail.com"

from .cli import main

__all__ = ["main"]