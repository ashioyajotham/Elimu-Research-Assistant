#!/usr/bin/env python3
import re
import sys
from pathlib import Path

def bump_version(version_type="patch"):
    """Bump version in setup.py and __init__.py"""
    
    # Read current version from setup.py
    setup_py = Path("setup.py")
    content = setup_py.read_text()
    
    version_match = re.search(r'version="(\d+)\.(\d+)\.(\d+)"', content)
    if not version_match:
        print("Could not find version in setup.py")
        return
    
    major, minor, patch = map(int, version_match.groups())
    
    if version_type == "major":
        major += 1
        minor = 0
        patch = 0
    elif version_type == "minor":
        minor += 1
        patch = 0
    else:  # patch
        patch += 1
    
    new_version = f"{major}.{minor}.{patch}"
    
    # Update setup.py
    new_content = re.sub(r'version="[\d\.]+"', f'version="{new_version}"', content)
    setup_py.write_text(new_content)
    
    # Update __init__.py
    init_py = Path("elimu_research_assistant/__init__.py")
    if init_py.exists():
        init_content = init_py.read_text()
        new_init_content = re.sub(r'__version__ = "[\d\.]+"', f'__version__ = "{new_version}"', init_content)
        init_py.write_text(new_init_content)
    
    print(f"Version bumped to {new_version}")
    return new_version

if __name__ == "__main__":
    version_type = sys.argv[1] if len(sys.argv) > 1 else "patch"
    bump_version(version_type)