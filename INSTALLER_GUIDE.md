# Helyxium Universal Installer Guide

## Overview

Helyxium includes a sophisticated universal installation system that automatically detects your platform and handles the complete installation process, including:

- ✅ Platform detection (Windows, macOS, Linux)
- ✅ Python version compatibility checking
- ✅ Virtual environment creation
- ✅ Dependency installation
- ✅ Desktop integration
- ✅ Launcher creation
- ✅ Uninstaller generation

## Creating Distribution Packages

### Quick Packaging

**Windows:**
```cmd
package.bat
```

**macOS/Linux:**
```bash
./package.sh
```

### Manual Packaging

```bash
python installer/package_installer.py
```

This creates:
- `helyxium-VERSION-universal-installer.zip` (Windows/Cross-platform)
- `helyxium-VERSION-universal-installer.tar.gz` (macOS/Linux)
- Platform-specific installers (when tools available)

## Installation Process

### 1. User Downloads Package

Users download the appropriate package:
- Windows: `.zip` file
- macOS/Linux: `.tar.gz` file  
- Windows (advanced): `.exe` installer

### 2. Extract and Run

**Windows:**
```cmd
# Extract ZIP file
# Open Command Prompt in extracted folder
python installer\install.py
```

**macOS/Linux:**
```bash
# Extract tar.gz file
tar -xzf helyxium-VERSION-universal-installer.tar.gz
cd helyxium-VERSION-universal-installer
python3 installer/install.py
```

### 3. Automatic Installation

The installer automatically:

1. **Detects Platform** - Windows, macOS, or Linux
2. **Checks Python** - Ensures version 3.9-3.13 compatibility
3. **Verifies System** - Checks disk space and required libraries
4. **Creates Directories** - Sets up installation structure
5. **Downloads/Copies Files** - Installs Helyxium source code
6. **Creates Virtual Environment** - Isolated Python environment
7. **Installs Dependencies** - All required packages
8. **Creates Launchers** - Easy-to-use startup scripts
9. **Desktop Integration** - Shortcuts and system integration
10. **Creates Uninstaller** - Clean removal capability

## Installation Locations

### Default Install Paths

- **Windows**: `%LOCALAPPDATA%\Helyxium`
- **macOS**: `~/Applications/Helyxium`
- **Linux**: `~/.local/share/Helyxium`

### Directory Structure After Install

```
Helyxium/
├── app/                    # Application source code
│   ├── src/               # Helyxium modules
│   ├── assets/            # Icons and resources
│   ├── main.py            # Application entry point
│   └── requirements.txt   # Dependencies list
├── venv/                  # Python virtual environment
│   ├── Scripts/ (Windows) or bin/ (Unix)
│   └── Lib/ or lib/
├── Helyxium.bat          # Windows launcher
├── helyxium              # Unix launcher  
└── Uninstall.bat/sh      # Uninstaller
```

## Desktop Integration

### Windows
- Desktop shortcut: `Helyxium.lnk`
- Start Menu entry: `Programs\Helyxium.lnk`
- Executable: `Helyxium.bat`

### macOS
- Application bundle: `Helyxium.app`
- Launchpad integration
- Dock support

### Linux
- Desktop entry: `~/.local/share/applications/helyxium.desktop`
- Application menu integration
- Executable: `helyxium`

## Uninstallation

### Windows
```cmd
# Run from installation directory
Uninstall.bat
```

### macOS/Linux
```bash
# Run from installation directory
./uninstall.sh
```

The uninstaller removes:
- All installed files and directories
- Desktop shortcuts
- System menu entries
- Virtual environment

## Advanced Installation Options

### Custom Install Directory

Users can modify the installer script to change the installation directory by editing the `_get_install_directory()` method.

### System-Wide Installation

For system administrators, the installer can be modified to install system-wide:

- Windows: `C:\Program Files\Helyxium`
- Linux: `/opt/helyxium` with symlinks in `/usr/local/bin`
- macOS: `/Applications/Helyxium.app`

### Offline Installation

The installer supports offline installation when run from a local source directory. It will copy files instead of downloading from GitHub.

## Troubleshooting

### Common Issues

**Permission Errors:**
- Windows: Run Command Prompt as Administrator
- macOS/Linux: Use `sudo python3 installer/install.py`

**Python Not Found:**
- Install Python from [python.org](https://python.org)
- Ensure Python is in PATH
- Use `python3` instead of `python` on Unix systems

**Network Issues:**
- Check firewall settings
- Verify internet connection
- Try with VPN disabled

**Dependency Installation Fails:**
- Update pip: `python -m pip install --upgrade pip`
- Clear pip cache: `pip cache purge`
- Install system packages (Linux): `sudo apt-get install build-essential`

### Manual Recovery

If automatic installation fails, users can:

1. Navigate to the extracted directory
2. Create virtual environment manually:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Unix
   venv\Scripts\activate     # Windows
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run application:
   ```bash
   python main.py
   ```

## Building Platform-Specific Installers

### Windows Executable Installer

Requires NSIS (Nullsoft Scriptable Install System):

1. Install NSIS from [nsis.sourceforge.io](https://nsis.sourceforge.io/)
2. Run packaging script on Windows
3. Outputs: `helyxium-VERSION-windows-installer.exe`

### Debian Package

On Ubuntu/Debian systems:

1. Install build tools: `sudo apt-get install dpkg-dev`
2. Run packaging script
3. Outputs: `helyxium-VERSION_all.deb`

Install with: `sudo dpkg -i helyxium-VERSION_all.deb`

### macOS App Bundle

The installer automatically creates `.app` bundles on macOS with proper Info.plist and launcher scripts.

## Customization

### Branding

To customize the installer appearance:

1. Edit `Colors` class in `installer/install.py`
2. Modify header text in `print_header()` method
3. Update installer messages throughout the script

### Dependencies

To add or modify dependencies:

1. Update `requirements.txt`
2. Modify dependency check logic if needed
3. Update system requirement checks

### Platform Support

To add support for new platforms:

1. Add platform detection in `__init__()`
2. Implement platform-specific methods
3. Add desktop integration for the platform
4. Test thoroughly on target platform

## Security Considerations

### Code Signing

For production releases:

- **Windows**: Sign executables with code signing certificate
- **macOS**: Sign app bundles and create notarized packages
- **Linux**: Sign packages with GPG keys

### Verification

All distribution packages include:
- `checksums.json` - File hashes and sizes
- `SHA256SUMS` - Standard checksum format

Users can verify downloads:
```bash
sha256sum -c SHA256SUMS
```

### Safe Installation

The installer:
- Creates isolated virtual environments
- Doesn't modify system Python
- Uses user directories by default
- Includes clean uninstall capability

## Distribution

### Release Process

1. Update version in `pyproject.toml`
2. Run `python installer/package_installer.py`
3. Test packages on target platforms
4. Upload to GitHub Releases or distribution platform
5. Update documentation

### Package Hosting

Recommended hosting options:
- GitHub Releases (free, automated)
- Official website download page
- Platform-specific repositories (apt, homebrew, etc.)

---

**Helyxium Universal Installer** - Making VR accessible everywhere! 🥽✨