"""
Entry point wrapper for elimu-research-assistant.

This module exists solely so the `elimu` console script has an unambiguous
import path (`elimu_entry:main`) that cannot be shadowed by other packages
placing a `cli.py` flat into site-packages.
"""
import os
import sys

# Ensure the project root is first on sys.path before anything else
_here = os.path.dirname(os.path.abspath(__file__))
if _here not in sys.path:
    sys.path.insert(0, _here)

from cli import main  # noqa: E402

__all__ = ["main"]
