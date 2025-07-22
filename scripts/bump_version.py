import sys
from pathlib import Path

def bump_version(version_type="patch"):
    """Bump version in VERSION file"""
    
    # Read current version from VERSION file
    version_file = Path("VERSION")
    current_version = version_file.read_text().strip()
    
    major, minor, patch = map(int, current_version.split('.'))
    
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
    
    # Update VERSION file
    version_file.write_text(new_version)
    
    print(f"Version bumped to {new_version}")
    return new_version

if __name__ == "__main__":
    version_type = sys.argv[1] if len(sys.argv) > 1 else "patch"
    bump_version(version_type)