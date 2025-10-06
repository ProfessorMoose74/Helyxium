#!/usr/bin/env python3
"""
Build script for Helyxium standalone executable
Cross-platform build support
"""

import platform
import shutil
import subprocess
import sys
from pathlib import Path


class HelyxiumBuilder:
    def __init__(self):
        self.root_dir = Path(__file__).parent
        self.dist_dir = self.root_dir / "dist"
        self.build_dir = self.root_dir / "build"
        self.system = platform.system()

    def clean(self):
        """Clean previous build artifacts"""
        print("Cleaning previous builds...")
        for path in [self.dist_dir, self.build_dir]:
            if path.exists():
                shutil.rmtree(path)

        for pycache in self.root_dir.rglob("__pycache__"):
            shutil.rmtree(pycache)

    def install_dependencies(self):
        """Install required dependencies"""
        print("Installing dependencies...")
        try:
            subprocess.run(
                ["poetry", "install", "--only", "main"], check=True, cwd=self.root_dir
            )
        except subprocess.CalledProcessError:
            print("Failed to install dependencies with poetry")
            print("Trying pip install...")
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
                check=True,
                cwd=self.root_dir,
            )

    def build(self):
        """Build the standalone executable"""
        print(f"Building Helyxium for {self.system}...")

        try:
            subprocess.run(
                ["poetry", "run", "pyinstaller", "helyxium.spec", "--clean"],
                check=True,
                cwd=self.root_dir,
            )
        except subprocess.CalledProcessError:
            print("Failed to build with poetry")
            print("Trying direct pyinstaller...")
            subprocess.run(
                [sys.executable, "-m", "PyInstaller", "helyxium.spec", "--clean"],
                check=True,
                cwd=self.root_dir,
            )

    def verify_build(self):
        """Verify the build was successful"""
        exe_name = "Helyxium.exe" if self.system == "Windows" else "Helyxium"
        exe_path = self.dist_dir / exe_name

        if exe_path.exists():
            print("\n" + "=" * 50)
            print("  Build successful!")
            print(f"  Executable: {exe_path}")
            print("=" * 50)
            return True
        else:
            print("\n" + "=" * 50)
            print("  Build failed!")
            print("  Check the error messages above")
            print("=" * 50)
            return False

    def run(self):
        """Run the complete build process"""
        print("=" * 50)
        print(f"  Building Helyxium for {self.system}")
        print("=" * 50 + "\n")

        self.clean()
        self.install_dependencies()
        self.build()

        if self.verify_build():
            return 0
        return 1


if __name__ == "__main__":
    builder = HelyxiumBuilder()
    sys.exit(builder.run())
