#!/usr/bin/env python3
"""
Helyxium Installer Packager
Creates distributable installation bundles for all platforms.
"""

import json
import os
import platform
import shutil
import subprocess
import sys
import tarfile
import tempfile
import zipfile
from pathlib import Path
from typing import Dict, List, Optional


class InstallerPackager:
    """Creates distributable installation bundles."""

    def __init__(self):
        self.root_dir = Path(__file__).parent.parent
        self.dist_dir = self.root_dir / "dist" / "installers"
        self.installer_dir = self.root_dir / "installer"
        self.version = self._get_version()

    def _get_version(self) -> str:
        """Get version from pyproject.toml or default."""
        try:
            pyproject_path = self.root_dir / "pyproject.toml"
            if pyproject_path.exists():
                with open(pyproject_path, "r") as f:
                    content = f.read()
                    for line in content.split("\n"):
                        if line.strip().startswith("version = "):
                            return line.split('"')[1]
        except:
            pass
        return "0.1.0"

    def clean_dist(self):
        """Clean previous distribution files."""
        print("Cleaning previous distributions...")
        if self.dist_dir.exists():
            try:
                shutil.rmtree(self.dist_dir)
            except PermissionError as e:
                print(f"   Warning: Could not fully clean {self.dist_dir}: {e}")
                # Try to clean individual files
                import time

                for root, dirs, files in os.walk(self.dist_dir):
                    for file in files:
                        try:
                            file_path = Path(root) / file
                            file_path.chmod(0o777)  # Make writable
                            file_path.unlink()
                        except:
                            continue
        self.dist_dir.mkdir(parents=True, exist_ok=True)

    def create_source_bundle(self) -> Path:
        """Create source code bundle with installer."""
        print("Creating source bundle...")

        import time

        timestamp = int(time.time())
        bundle_name = f"helyxium-{self.version}-universal-installer-{timestamp}"
        bundle_dir = self.dist_dir / bundle_name
        bundle_dir.mkdir(parents=True)

        # Copy essential files
        essential_files = [
            "main.py",
            "requirements.txt",
            "pyproject.toml",
            "README.md",
            "UPDATES.md",
            "LOGO_SETUP.md",
            "version.txt",
            "helyxium.spec",
        ]

        # Copy essential directories
        essential_dirs = ["src", "assets", "scripts", "installer"]

        # Copy files
        for file_name in essential_files:
            src_file = self.root_dir / file_name
            if src_file.exists():
                shutil.copy2(src_file, bundle_dir / file_name)

        # Copy directories
        for dir_name in essential_dirs:
            src_dir = self.root_dir / dir_name
            if src_dir.exists():
                try:
                    shutil.copytree(src_dir, bundle_dir / dir_name, dirs_exist_ok=True)
                except PermissionError as e:
                    print(f"   Warning: Could not copy {dir_name}: {e}")
                    continue

        # Create installation instructions
        self._create_install_instructions(bundle_dir)

        return bundle_dir

    def _create_install_instructions(self, bundle_dir: Path):
        """Create installation instructions."""
        install_md = f"""# Helyxium Universal Installer

## Quick Install

### Windows
1. Open Command Prompt or PowerShell
2. Navigate to this directory
3. Run: `python installer/install.py`

### macOS/Linux
1. Open Terminal
2. Navigate to this directory  
3. Run: `python3 installer/install.py`

## What the Installer Does

-  **Platform Detection**: Automatically detects your OS and architecture
-  **Python Compatibility Check**: Ensures Python 3.9-3.13 compatibility
-  **Virtual Environment**: Creates isolated Python environment
-  **Dependency Installation**: Installs all required packages automatically
-  **Desktop Integration**: Creates shortcuts and system integration
-  **Launcher Scripts**: Creates easy-to-use launcher commands
-  **Uninstaller**: Includes clean uninstall capability

## Installation Locations

- **Windows**: `%LOCALAPPDATA%\\Helyxium`
- **macOS**: `~/Applications/Helyxium`  
- **Linux**: `~/.local/share/Helyxium`

## Requirements

- Python 3.9 or higher (up to 3.13)
- Internet connection (for dependency download)
- ~500MB free disk space
- Administrative privileges (Windows/macOS) or sudo access (Linux)

## System-Specific Notes

### Windows
- Requires Windows 10 or later
- May need to install Microsoft Visual C++ Redistributable
- Windows Defender might scan the installer (normal behavior)

### macOS  
- Requires macOS 10.15 (Catalina) or later
- May need to allow app in Security & Privacy settings
- Apple Silicon and Intel Macs both supported

### Linux
- Supports Ubuntu 20.04+, Fedora 35+, Arch Linux, and other modern distros
- May need to install system packages: `libgl1-mesa-glx libx11-6 libxcb1`
- Wayland and X11 display servers supported

## Troubleshooting

### Permission Errors
- **Windows**: Run Command Prompt as Administrator
- **macOS/Linux**: Use `sudo python3 installer/install.py`

### Python Not Found
- Install Python from [python.org](https://python.org)
- Ensure Python is added to PATH
- Use `python3` instead of `python` on macOS/Linux

### Network Issues
- Check firewall/antivirus settings
- Try running installer with VPN disabled
- Manual installation available in README.md

### Dependencies Fail to Install
- Update pip: `python -m pip install --upgrade pip`
- Clear pip cache: `pip cache purge` 
- Install missing system libraries (Linux)

## Manual Installation

If the installer fails, you can install manually:

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\\Scripts\\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run Helyxium
python main.py
```

## Support

- **Issues**: Report at GitHub repository
- **Documentation**: See README.md
- **Updates**: Check UPDATES.md for recent changes

---

**Helyxium v{self.version} - Universal VR Bridge Platform**
*Where the World Comes Together*
"""

        with open(bundle_dir / "INSTALL.md", "w") as f:
            f.write(install_md)

    def create_zip_bundle(self, source_dir: Path) -> Path:
        """Create ZIP bundle for Windows/cross-platform."""
        print("Creating ZIP bundle...")

        zip_name = f"{source_dir.name}.zip"
        zip_path = self.dist_dir / zip_name

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(source_dir):
                # Skip unnecessary directories
                dirs[:] = [
                    d for d in dirs if d not in [".git", "__pycache__", ".pytest_cache"]
                ]

                for file in files:
                    if file.endswith((".pyc", ".pyo", ".DS_Store")):
                        continue

                    file_path = Path(root) / file
                    arc_path = file_path.relative_to(source_dir)
                    zipf.write(file_path, arc_path)

        return zip_path

    def create_tar_bundle(self, source_dir: Path) -> Path:
        """Create TAR.GZ bundle for Unix systems."""
        print(" Creating TAR.GZ bundle...")

        tar_name = f"{source_dir.name}.tar.gz"
        tar_path = self.dist_dir / tar_name

        with tarfile.open(tar_path, "w:gz") as tarf:
            for root, dirs, files in os.walk(source_dir):
                # Skip unnecessary directories
                dirs[:] = [
                    d for d in dirs if d not in [".git", "__pycache__", ".pytest_cache"]
                ]

                for file in files:
                    if file.endswith((".pyc", ".pyo", ".DS_Store")):
                        continue

                    file_path = Path(root) / file
                    arc_path = file_path.relative_to(source_dir)
                    tarf.add(file_path, arc_path)

        return tar_path

    def create_windows_installer(self, source_dir: Path) -> Optional[Path]:
        """Create Windows-specific installer using NSIS or similar."""
        print(" Creating Windows installer...")

        # Check if NSIS is available
        try:
            subprocess.run(["makensis", "/VERSION"], capture_output=True, check=True)
            return self._create_nsis_installer(source_dir)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("   NSIS not found, skipping Windows installer")
            return None

    def _create_nsis_installer(self, source_dir: Path) -> Path:
        """Create NSIS installer script and build."""
        nsis_script = f"""
!define APPNAME "Helyxium"
!define APPVERSION "{self.version}"
!define COMPANYNAME "Helyxium Team"
!define DESCRIPTION "Universal VR Bridge Platform"

!define INSTDIR_REG_ROOT "HKLM"
!define INSTDIR_REG_KEY "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APPNAME}}"

RequestExecutionLevel admin
InstallDir "$LOCALAPPDATA\\${{APPNAME}}"

Name "${{APPNAME}}"
OutFile "{self.dist_dir}\\helyxium-{self.version}-windows-installer.exe"

Page directory
Page instfiles

Section "Install"
    SetOutPath $INSTDIR
    
    # Copy all files
    File /r "{source_dir}\\*"
    
    # Run installer
    ExecWait '"$INSTDIR\\installer\\install.py"'
    
    # Create uninstaller
    WriteUninstaller "$INSTDIR\\Uninstall.exe"
    
    # Registry info for Add/Remove Programs
    WriteRegStr ${{INSTDIR_REG_ROOT}} "${{INSTDIR_REG_KEY}}" "DisplayName" "${{APPNAME}}"
    WriteRegStr ${{INSTDIR_REG_ROOT}} "${{INSTDIR_REG_KEY}}" "UninstallString" "$INSTDIR\\Uninstall.exe"
    WriteRegStr ${{INSTDIR_REG_ROOT}} "${{INSTDIR_REG_KEY}}" "DisplayVersion" "${{APPVERSION}}"
    WriteRegStr ${{INSTDIR_REG_ROOT}} "${{INSTDIR_REG_KEY}}" "Publisher" "${{COMPANYNAME}}"
    WriteRegStr ${{INSTDIR_REG_ROOT}} "${{INSTDIR_REG_KEY}}" "DisplayIcon" "$INSTDIR\\assets\\icons\\helyxium.ico"
    
SectionEnd

Section "Uninstall"
    RMDir /r "$INSTDIR"
    DeleteRegKey ${{INSTDIR_REG_ROOT}} "${{INSTDIR_REG_KEY}}"
SectionEnd
"""

        nsis_file = self.dist_dir / "helyxium_installer.nsi"
        with open(nsis_file, "w") as f:
            f.write(nsis_script)

        # Build installer
        subprocess.run(["makensis", str(nsis_file)], check=True)

        # Clean up NSIS script
        nsis_file.unlink()

        return self.dist_dir / f"helyxium-{self.version}-windows-installer.exe"

    def create_deb_package(self, source_dir: Path) -> Optional[Path]:
        """Create Debian package for Ubuntu/Debian."""
        print(" Creating DEB package...")

        try:
            # Check if dpkg-deb is available
            subprocess.run(["dpkg-deb", "--version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("   dpkg-deb not found, skipping DEB package")
            return None

        # Create package structure
        pkg_name = f"helyxium_{self.version}_all"
        pkg_dir = self.dist_dir / pkg_name

        # Create directories
        (pkg_dir / "DEBIAN").mkdir(parents=True)
        (pkg_dir / "opt" / "helyxium").mkdir(parents=True)
        (pkg_dir / "usr" / "share" / "applications").mkdir(parents=True)
        (pkg_dir / "usr" / "bin").mkdir(parents=True)

        # Copy application files
        shutil.copytree(source_dir, pkg_dir / "opt" / "helyxium", dirs_exist_ok=True)

        # Create control file
        control_content = f"""Package: helyxium
Version: {self.version}
Section: games
Priority: optional
Architecture: all
Depends: python3 (>= 3.9), python3-venv, python3-pip
Maintainer: Helyxium Team <team@helyxium.com>
Description: Universal VR Bridge Platform
 Helyxium connects all virtual reality worlds and platforms,
 providing seamless interaction across VR ecosystems.
"""

        with open(pkg_dir / "DEBIAN" / "control", "w") as f:
            f.write(control_content)

        # Create postinst script
        postinst_content = """#!/bin/bash
cd /opt/helyxium
python3 installer/install.py --system-install
"""

        postinst_path = pkg_dir / "DEBIAN" / "postinst"
        with open(postinst_path, "w") as f:
            f.write(postinst_content)
        os.chmod(postinst_path, 0o755)

        # Build package
        deb_path = pkg_dir.with_suffix(".deb")
        subprocess.run(["dpkg-deb", "--build", str(pkg_dir), str(deb_path)], check=True)

        # Clean up build directory
        shutil.rmtree(pkg_dir)

        return deb_path

    def create_checksums(self, files: List[Path]):
        """Create checksum files for verification."""
        print(" Creating checksums...")

        import hashlib

        checksums = {}

        for file_path in files:
            if file_path.exists():
                # Calculate SHA256
                hasher = hashlib.sha256()
                with open(file_path, "rb") as f:
                    for chunk in iter(lambda: f.read(4096), b""):
                        hasher.update(chunk)

                checksums[file_path.name] = {
                    "sha256": hasher.hexdigest(),
                    "size": file_path.stat().st_size,
                }

        # Write checksums file
        checksums_file = self.dist_dir / "checksums.json"
        with open(checksums_file, "w") as f:
            json.dump(checksums, f, indent=2)

        # Write SHA256SUMS file (standard format)
        sha256sums_file = self.dist_dir / "SHA256SUMS"
        with open(sha256sums_file, "w") as f:
            for filename, data in checksums.items():
                f.write(f"{data['sha256']}  {filename}\\n")

    def create_release_notes(self):
        """Create release notes from UPDATES.md."""
        print(" Creating release notes...")

        release_notes = f"""# Helyxium v{self.version} Release

## Installation Options

### Universal Installer (Recommended)
- **Windows**: `helyxium-{self.version}-universal-installer.zip`
- **macOS/Linux**: `helyxium-{self.version}-universal-installer.tar.gz`

### Platform-Specific
- **Windows Installer**: `helyxium-{self.version}-windows-installer.exe` (if available)
- **Debian/Ubuntu**: `helyxium-{self.version}_all.deb` (if available)

## Quick Start

1. Download the appropriate package for your platform
2. Extract (if ZIP/TAR.GZ) 
3. Run the installer:
   - **Windows**: `python installer\\install.py`
   - **macOS/Linux**: `python3 installer/install.py`

## Verification

All packages include SHA256 checksums in `checksums.json` and `SHA256SUMS`.

## What's New

See `UPDATES.md` in the package for detailed changes.

## System Requirements

- Python 3.9 - 3.13
- 500MB free disk space
- Internet connection (for dependencies)

## Support

- Report issues on GitHub
- Documentation in README.md
- Installation help in INSTALL.md

---

*Helyxium - Where the World Comes Together*
"""

        with open(self.dist_dir / "RELEASE_NOTES.md", "w") as f:
            f.write(release_notes)

    def package(self):
        """Create all distribution packages."""
        print(f" Packaging Helyxium v{self.version} installer bundles...")
        print("=" * 60)

        # Clean previous builds
        self.clean_dist()

        # Create source bundle
        source_bundle = self.create_source_bundle()

        # Create distribution packages
        created_files = []

        # Cross-platform packages
        zip_bundle = self.create_zip_bundle(source_bundle)
        created_files.append(zip_bundle)

        tar_bundle = self.create_tar_bundle(source_bundle)
        created_files.append(tar_bundle)

        # Platform-specific installers
        if platform.system().lower() == "windows":
            windows_installer = self.create_windows_installer(source_bundle)
            if windows_installer:
                created_files.append(windows_installer)

        if platform.system().lower() == "linux":
            deb_package = self.create_deb_package(source_bundle)
            if deb_package:
                created_files.append(deb_package)

        # Create checksums
        self.create_checksums([f for f in created_files if f])

        # Create release notes
        self.create_release_notes()

        # Clean up temporary source bundle
        shutil.rmtree(source_bundle)

        # Summary
        print("\\n" + "=" * 60)
        print(" Packaging Complete!")
        print("=" * 60)
        print(f"\\nDistribution packages created in: {self.dist_dir}")
        print("\\nCreated files:")

        for file_path in self.dist_dir.iterdir():
            if file_path.is_file():
                size_mb = file_path.stat().st_size / (1024 * 1024)
                print(f"   {file_path.name} ({size_mb:.1f} MB)")

        print(f"\\n Ready for distribution! ")


def main():
    """Main packager entry point."""
    try:
        packager = InstallerPackager()
        packager.package()
    except KeyboardInterrupt:
        print("\\n Packaging cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\\n Packaging failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
