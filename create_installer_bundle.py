#!/usr/bin/env python3
"""
Simple Helyxium installer bundle creator
Creates a ZIP file with installer and all necessary files.
"""

import os
import shutil
import sys
import time
import zipfile
from pathlib import Path


def create_installer_bundle():
    """Create a simple installer bundle."""
    print("Creating Helyxium Universal Installer Bundle...")

    root_dir = Path(__file__).parent
    timestamp = int(time.time())
    bundle_name = f"helyxium-universal-installer-{timestamp}.zip"
    bundle_path = root_dir / bundle_name

    # Essential files to include
    essential_files = [
        "main.py",
        "requirements.txt",
        "pyproject.toml",
        "README.md",
        "UPDATES.md",
        "LOGO_SETUP.md",
        "INSTALLER_GUIDE.md",
        "version.txt",
        "helyxium.spec",
    ]

    # Essential directories
    essential_dirs = ["src", "scripts", "installer"]

    # Optional directories (include if they exist)
    optional_dirs = ["assets"]

    print(f"Creating bundle: {bundle_name}")

    try:
        with zipfile.ZipFile(bundle_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            # Add essential files
            for file_name in essential_files:
                file_path = root_dir / file_name
                if file_path.exists():
                    zipf.write(file_path, file_name)
                    print(f"  + {file_name}")

            # Add essential directories
            for dir_name in essential_dirs:
                dir_path = root_dir / dir_name
                if dir_path.exists():
                    for root, dirs, files in os.walk(dir_path):
                        # Skip unnecessary directories
                        dirs[:] = [
                            d
                            for d in dirs
                            if d not in [".git", "__pycache__", ".pytest_cache"]
                        ]

                        for file in files:
                            if file.endswith((".pyc", ".pyo", ".DS_Store")):
                                continue

                            file_path = Path(root) / file
                            arc_path = file_path.relative_to(root_dir)
                            try:
                                zipf.write(file_path, arc_path)
                            except PermissionError:
                                print(f"  ! Skipped {arc_path} (permission denied)")
                                continue
                    print(f"  + {dir_name}/")

            # Add optional directories
            for dir_name in optional_dirs:
                dir_path = root_dir / dir_name
                if dir_path.exists():
                    try:
                        for root, dirs, files in os.walk(dir_path):
                            dirs[:] = [
                                d
                                for d in dirs
                                if d not in [".git", "__pycache__", ".pytest_cache"]
                            ]

                            for file in files:
                                if file.endswith((".pyc", ".pyo", ".DS_Store")):
                                    continue

                                file_path = Path(root) / file
                                arc_path = file_path.relative_to(root_dir)
                                try:
                                    zipf.write(file_path, arc_path)
                                except PermissionError:
                                    print(f"  ! Skipped {arc_path} (permission denied)")
                                    continue
                        print(f"  + {dir_name}/")
                    except Exception as e:
                        print(f"  ! Could not add {dir_name}: {e}")

            # Add installation instructions
            install_readme = """# Helyxium Universal Installer

## Quick Installation

### Windows
1. Extract this ZIP file
2. Open Command Prompt in the extracted folder
3. Run: `python installer\\install.py`

### macOS/Linux  
1. Extract this ZIP file
2. Open Terminal in the extracted folder
3. Run: `python3 installer/install.py`

## What This Does

The installer will automatically:
- Detect your platform (Windows/macOS/Linux)
- Check Python compatibility (3.9-3.13)
- Create a virtual environment
- Install all dependencies
- Set up desktop shortcuts
- Create launcher scripts

## Requirements

- Python 3.9 or higher
- Internet connection (for dependencies)
- ~500MB free disk space

## Need Help?

See INSTALLER_GUIDE.md for detailed instructions and troubleshooting.

---
Helyxium - Universal VR Bridge Platform
"""

            zipf.writestr("INSTALL_README.txt", install_readme)
            print("  + INSTALL_README.txt")

        file_size = bundle_path.stat().st_size / (1024 * 1024)
        print(f"\nBundle created successfully!")
        print(f"  File: {bundle_path}")
        print(f"  Size: {file_size:.1f} MB")
        print(f"\nUsers can download and extract this file, then run:")
        print(f"  python installer/install.py")

        return True

    except Exception as e:
        print(f"\nBundle creation failed: {e}")
        return False


if __name__ == "__main__":
    try:
        success = create_installer_bundle()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nBundle creation cancelled")
        sys.exit(1)
