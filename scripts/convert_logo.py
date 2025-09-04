#!/usr/bin/env python3
"""
Script to convert the Helyxium logo to different formats needed for the application.
Converts PNG to ICO for Windows builds and creates different sizes.
"""

from pathlib import Path
from PIL import Image, ImageFilter
import sys

def convert_logo():
    """Convert the main logo to various formats and sizes."""
    
    assets_dir = Path(__file__).parent.parent / "assets" / "icons"
    logo_path = assets_dir / "helyxium_logo.png"
    
    if not logo_path.exists():
        print(f"Error: Logo file not found at {logo_path}")
        print("Please save the provided logo image as 'helyxium_logo.png' in the assets/icons directory")
        return False
    
    try:
        # Open the original logo
        with Image.open(logo_path) as img:
            # Convert to RGBA if not already
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            
            # Create ICO file with multiple sizes for Windows
            ico_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
            ico_images = []
            
            for size in ico_sizes:
                resized = img.resize(size, Image.Resampling.LANCZOS)
                ico_images.append(resized)
            
            # Save as ICO
            ico_path = assets_dir / "helyxium.ico"
            ico_images[0].save(ico_path, format='ICO', sizes=ico_sizes)
            print(f"Created ICO file: {ico_path}")
            
            # Create different PNG sizes
            sizes = {
                'small': (32, 32),
                'medium': (64, 64),
                'large': (128, 128),
                'xlarge': (256, 256)
            }
            
            for name, size in sizes.items():
                resized = img.resize(size, Image.Resampling.LANCZOS)
                size_path = assets_dir / f"helyxium_{name}.png"
                resized.save(size_path, 'PNG')
                print(f"Created {name} PNG: {size_path}")
            
            # Create a simplified icon for system tray (smaller, cleaner)
            tray_icon = img.resize((32, 32), Image.Resampling.LANCZOS)
            
            # Apply slight sharpening for small size
            tray_icon = tray_icon.filter(ImageFilter.UnsharpMask(radius=1, percent=50, threshold=3))
            
            tray_path = assets_dir / "helyxium_tray.png"
            tray_icon.save(tray_path, 'PNG')
            print(f"Created system tray icon: {tray_path}")
            
            print(f"✅ Successfully converted logo to all required formats!")
            return True
            
    except Exception as e:
        print(f"Error processing logo: {e}")
        return False

if __name__ == "__main__":
    try:
        import PIL
    except ImportError:
        print("Error: Pillow (PIL) is required for image processing.")
        print("Install with: pip install Pillow")
        sys.exit(1)
    
    success = convert_logo()
    sys.exit(0 if success else 1)