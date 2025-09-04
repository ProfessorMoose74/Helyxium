# Helyxium Logo Setup

## Installing the Logo

1. **Save the Logo Image**: Save the provided Helyxium logo image as `helyxium_logo.png` in the `assets/icons/` directory.

2. **Convert to Multiple Formats** (Optional but Recommended):
   ```bash
   # Install Pillow for image processing if not already installed
   pip install Pillow
   
   # Run the logo conversion script
   python scripts/convert_logo.py
   ```

   This script will create:
   - `helyxium.ico` - Windows icon format for executables
   - `helyxium_small.png` (32x32) - Small version
   - `helyxium_medium.png` (64x64) - Medium version  
   - `helyxium_large.png` (128x128) - Large version
   - `helyxium_xlarge.png` (256x256) - Extra large version
   - `helyxium_tray.png` (32x32) - Optimized for system tray

## Directory Structure
After setup, your assets directory should look like:
```
assets/
└── icons/
    ├── helyxium_logo.png      # Original logo (provided by you)
    ├── helyxium.ico           # Windows executable icon
    ├── helyxium_small.png     # 32x32 version
    ├── helyxium_medium.png    # 64x64 version
    ├── helyxium_large.png     # 128x128 version
    ├── helyxium_xlarge.png    # 256x256 version
    └── helyxium_tray.png      # System tray optimized
```

## Usage in Application

The logo is automatically integrated into:

- **Application Window Icon**: Main window uses the logo as its icon
- **System Tray Icon**: Uses optimized tray version (32x32) for better visibility
- **Executable Icon**: Windows builds use the ICO format for the executable icon
- **Task Bar**: Application appears with the logo in the taskbar

## Manual Setup (Alternative)

If you prefer manual setup or the script doesn't work:

1. Save the logo as `assets/icons/helyxium_logo.png`
2. Optionally create smaller versions manually:
   - System tray works best with 32x32 or 64x64 pixel versions
   - For Windows executables, convert to ICO format using online tools or image editors

## Building with Logo

When building the executable with PyInstaller:
```bash
python build.py
```

The build script will automatically include the logo assets and use the appropriate icon format for the executable.

## Troubleshooting

- **Logo not showing**: Check that `assets/icons/helyxium_logo.png` exists
- **System tray icon missing**: The application will fall back to a default icon if custom ones aren't found
- **Build errors with ICO**: If ICO conversion fails, the build will use PNG format as fallback
- **Blurry icons**: Use the convert script to generate properly sized versions for different use cases

## Logo Attribution

The beautiful 3D Helyxium logo represents the universal bridge concept with interconnected geometric patterns, symbolizing the connection between different VR worlds and platforms.