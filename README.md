# Helyxium
**Universal VR Bridge Platform - Where the World Comes Together**

Helyxium is a comprehensive VR platform detection and bridge system that enables seamless interaction across multiple virtual reality ecosystems including Meta Quest, SteamVR, PlayStation VR, and more.

## Features

- **Universal VR Hardware Detection** - Automatically detects and identifies VR headsets from all major manufacturers
- **Multi-Platform Support** - Works with SteamVR, Meta/Oculus, PlayStation VR, Windows MR, VRChat, and other VR platforms
- **Cross-Platform Compatibility** - Runs on Windows, macOS, and Linux with modern distribution support
- **Real-time Monitoring** - Continuous detection of VR hardware and software changes
- **Multi-language Support** - Interface available in multiple languages with automatic system language detection
- **Modern Architecture** - Built with FastAPI, PyQt6, and modern Python practices

## System Requirements

- **Python**: 3.9 - 3.13
- **Operating Systems**: 
  - Windows 10/11 (with Windows Mixed Reality support)
  - macOS 10.15+ (with Apple Vision Pro support)
  - Linux (Ubuntu 20.04+, Fedora 35+, Arch Linux, and other modern distributions)

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/helyxium/helyxium.git
cd helyxium

# Install dependencies
pip install -r requirements.txt

# Or using Poetry (recommended)
poetry install
```

### Running Helyxium

```bash
# Direct execution
python main.py

# Or using Poetry
poetry run python main.py
```

### Logo Setup

Before building, set up the application logo:

1. Save the provided logo image as `assets/icons/helyxium_logo.png`
2. Run the conversion script: `python scripts/convert_logo.py` (requires Pillow)

See [LOGO_SETUP.md](LOGO_SETUP.md) for detailed instructions.

### Building Standalone Executable

```bash
# Build for your platform
python build.py

# Or using Poetry
poetry run python build.py
```

## Distribution

### Creating Installer Bundle

For distribution to end users, create a universal installer bundle:

```bash
# Simple bundle creation (recommended)
python create_installer_bundle.py

# Advanced packaging (requires additional tools)
python installer/package_installer.py
```

This creates a ZIP file containing:
- Complete Helyxium source code
- Universal installer script  
- All necessary assets and documentation
- Installation instructions

Users simply extract and run `python installer/install.py` to automatically install Helyxium with all dependencies.

## Supported VR Hardware

### Headsets
- **Meta Quest Series**: Quest 1, Quest 2, Quest 3, Quest Pro, Quest 3S
- **HTC Vive Series**: Vive, Vive Pro, Vive Pro 2, Vive Cosmos
- **Valve Index**: Full support with lighthouse tracking
- **PlayStation VR**: PSVR, PSVR2 (with PC adapter)
- **Windows Mixed Reality**: All WMR headsets
- **Apple Vision Pro**: Detection and basic support
- **Pico**: Pico 4 and other Pico Interactive headsets
- **Varjo**: Enterprise VR headsets

### Tracking Technologies
- Inside-out tracking (Quest, WMR, Pico)
- Lighthouse tracking (Vive, Index)
- Outside-in tracking (PSVR)
- Hand tracking and eye tracking detection
- Passthrough and mixed reality capabilities

## Supported VR Platforms

- **SteamVR** - Full integration with Steam's VR ecosystem
- **Meta/Oculus PC** - Quest Link, Air Link, and Oculus Store
- **Windows Mixed Reality** - Native Windows holographic platform
- **VRChat** - Popular social VR platform
- **Rec Room** - Cross-platform VR social gaming
- **Horizon Worlds** - Meta's social VR platform
- **Viveport** - HTC's VR content platform

## Architecture

Helyxium is built with a modular architecture:

- **Core Application** (`src/core/`) - Main application logic and orchestration
- **Hardware Detection** (`src/detection/hardware.py`) - VR headset and controller detection
- **Platform Detection** (`src/detection/platforms.py`) - VR software and game detection  
- **Localization** (`src/localization/`) - Multi-language support with automatic detection
- **UI Components** (`src/ui/`) - PyQt6-based user interface with theme support
- **Security** (`src/security/`) - Authentication and data protection
- **Networking** (`src/networking/`) - Cross-platform VR communication

## Recent Updates

See [UPDATES.md](UPDATES.md) for detailed information about recent compatibility improvements and new features.

### Highlights
- Python 3.9-3.13 support with flexible version requirements
- Enhanced Windows 10/11 compatibility with improved registry access
- Modern Linux distribution support (Flatpak, Snap, systemd)
- Updated dependencies for better performance and security
- Improved error handling and graceful degradation

## Development

### Requirements
- Python 3.9+
- Poetry (recommended) or pip
- PyQt6 for GUI development
- pytest for testing

### Development Setup

```bash
# Install development dependencies
poetry install --with dev

# Run tests
poetry run pytest

# Format code
poetry run black .

# Type checking
poetry run mypy src/

# Linting
poetry run flake8 src/
```

## Contributing

We welcome contributions! Please see our contributing guidelines and feel free to submit issues or pull requests.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, feature requests, or bug reports, please open an issue on our GitHub repository.
