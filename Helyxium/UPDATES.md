# Helyxium OS Compatibility Updates

## Summary
Updated Helyxium for compatibility with modern operating systems and distributions. All changes maintain backward compatibility while adding support for newer systems.

## Python Version Support
- **Updated**: Python version requirement from `^3.11` to `>=3.9,<3.14`
- **Benefit**: Supports stable Python 3.9+ through Python 3.13
- **MyPy**: Updated target version to use Python 3.9 as baseline

## Dependency Updates
Updated key dependencies to current stable versions while maintaining compatibility:
- FastAPI: `^0.104.0` → `^0.115.0`
- WebSockets: `^12.0` → `^13.0` 
- Requests: `^2.31.0` → `^2.32.0`
- Pydantic: `^2.5.0` → `^2.9.0`
- Cryptography: `^41.0.0` → `^43.0.0`
- NumPy: `^1.25.0` → `^1.26.0`
- PyQt6: `^6.6.0` → `^6.7.0`
- Babel: `^2.13.0` → `^2.16.0`
- msgpack: `>=1.0.7` → `>=1.0.8`

## Windows Compatibility Improvements

### Registry Access
- **Enhanced Steam Detection**: Added support for multiple registry keys including WOW6432Node for 32-bit apps on 64-bit Windows
- **Oculus/Meta Detection**: Updated to detect both legacy Oculus and newer Meta installations
- **Windows MR**: Added detection for Windows Mixed Reality across different registry locations
- **Language Detection**: Improved Windows language detection with fallbacks for Windows 10/11

### Process Detection
- **Multi-method Approach**: Added fallback methods using tasklist, wmic, and PowerShell
- **Error Handling**: Improved handling of Windows-specific errors and permissions
- **Timeout Management**: Added proper timeout handling for subprocess calls

## Linux Distribution Support

### Steam Detection
- **Flatpak Support**: Added detection for Steam installed via Flatpak
- **Snap Support**: Added detection for Steam installed via Snap
- **Package Manager**: Added detection when Steam is installed via system package manager
- **Modern Paths**: Updated search paths for contemporary Linux distributions

### VR Hardware Detection
- **Multiple Methods**: Added udev and sysfs detection methods alongside traditional lsusb
- **Modern Linux**: Better support for systemd-based distributions
- **Container Support**: Improved detection in containerized environments

## Error Handling Improvements
- **Exception Specificity**: Replaced generic `Exception` catches with specific error types
- **Registry Errors**: Added handling for `WindowsError`, `FileNotFoundError`, and `OSError`
- **Subprocess Timeouts**: Added `TimeoutExpired` handling for system calls
- **Graceful Degradation**: System continues to function even if some detection methods fail

## Cross-Platform Enhancements
- **Path Handling**: Improved cross-platform path resolution
- **Environment Variables**: Better handling of Windows environment variable expansion
- **Shell Integration**: Added support for different shell environments on Linux/macOS

## Testing & Validation
- **Syntax Validation**: All modules pass Python syntax compilation
- **Import Testing**: Core modules load successfully
- **Version Compatibility**: Confirmed compatibility with Python 3.13.5

## Backward Compatibility
- **Maintained APIs**: All existing APIs remain unchanged
- **Legacy Support**: Older detection methods still work as fallbacks
- **Configuration**: Existing configuration files remain valid

## Logo Integration
- **Application Branding**: Integrated the beautiful 3D Helyxium logo throughout the application
- **Multi-format Support**: Created ICO, PNG variants in multiple sizes (32x32 to 256x256)
- **System Integration**: Logo appears in window title bar, system tray, and executable icon
- **Smart Fallbacks**: Graceful handling of missing logo files with appropriate defaults
- **Build Integration**: Logo automatically included in PyInstaller builds

## Files Modified
- `pyproject.toml` - Updated Python version requirements and dependencies
- `requirements.txt` - Updated dependency versions
- `src/detection/platforms.py` - Enhanced Windows registry access and Linux support
- `src/localization/detector.py` - Improved Windows language detection
- `src/core/application.py` - Added logo integration for window and system tray icons
- `helyxium.spec` - Updated PyInstaller spec to include logo assets
- Various detection modules - Added better error handling and modern OS support

## Files Added
- `assets/icons/helyxium_logo.png` - Original high-resolution logo
- `assets/icons/helyxium.ico` - Windows executable icon format
- `assets/icons/helyxium_*.png` - Multiple PNG sizes for different uses
- `scripts/convert_logo.py` - Automated logo conversion utility
- `LOGO_SETUP.md` - Logo setup and usage instructions

## Installation
After these updates, run:
```bash
# Update dependencies
pip install -r requirements.txt
# Or with poetry
poetry install
```

## Future Considerations
- Dependencies will need periodic updates as new versions are released
- Monitor Python 3.14 release for compatibility testing
- Consider adding automated testing for different OS environments