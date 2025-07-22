import sys
import re
from pathlib import Path
from datetime import datetime

def bump_version(version_type="patch"):
    """Bump version in VERSION file and update CHANGELOG.md"""
    
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
    
    # Update CHANGELOG.md
    update_changelog(new_version)
    
    print(f"Version bumped to {new_version}")
    return new_version

def update_changelog(version):
    """Add new version entry to CHANGELOG.md"""
    changelog_file = Path("CHANGELOG.md")
    
    if not changelog_file.exists():
        print("CHANGELOG.md not found, skipping changelog update")
        return
    
    content = changelog_file.read_text()
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Find the "## [Unreleased]" section and add new version after it
    new_entry = f"""
## [{version}] - {today}

### Added
- 

### Changed
- 

### Fixed
- 

"""
    
    # Insert the new version entry after [Unreleased]
    updated_content = re.sub(
        r'(## \[Unreleased\].*?\n)',
        r'\1' + new_entry,
        content,
        flags=re.DOTALL
    )
    
    changelog_file.write_text(updated_content)
    print(f"Updated CHANGELOG.md with version {version}")

if __name__ == "__main__":
    version_type = sys.argv[1] if len(sys.argv) > 1 else "patch"
    bump_version(version_type)