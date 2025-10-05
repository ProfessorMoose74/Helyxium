#!/usr/bin/env python3
"""
Helyxium Universal Installer
Automatically detects platform and installs Helyxium with all dependencies.
"""

import os
import sys
import platform
import subprocess
import shutil
import json
import urllib.request
import urllib.error
import zipfile
import tarfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import tempfile
import venv

# Installer configuration
INSTALLER_VERSION = "1.0.0"
HELYXIUM_VERSION = "0.1.0"  # Note: Keep in sync with src/__init__.py
REPO_URL = "https://github.com/helyxium/helyxium"
PYTHON_MIN_VERSION = (3, 9)
PYTHON_MAX_VERSION = (3, 13)

class Colors:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'
    
    @classmethod
    def disable(cls):
        """Disable colors for systems that don't support them."""
        cls.HEADER = cls.BLUE = cls.CYAN = cls.GREEN = ''
        cls.YELLOW = cls.RED = cls.BOLD = cls.UNDERLINE = cls.END = ''

class HelyxiumInstaller:
    """Universal Helyxium installer."""
    
    def __init__(self):
        self.system = platform.system().lower()
        self.architecture = platform.machine().lower()
        self.python_version = sys.version_info
        self.install_dir = self._get_install_directory()
        self.venv_dir = self.install_dir / "venv"
        self.app_dir = self.install_dir / "app"
        self.temp_dir = None
        
        # Disable colors on Windows by default (can be overridden)
        if self.system == 'windows' and not os.environ.get('FORCE_COLOR'):
            Colors.disable()
    
    def _get_install_directory(self) -> Path:
        """Get the appropriate installation directory for the platform."""
        if self.system == 'windows':
            base = Path(os.environ.get('LOCALAPPDATA', '~')).expanduser()
            return base / "Helyxium"
        elif self.system == 'darwin':  # macOS
            return Path("~/Applications/Helyxium").expanduser()
        else:  # Linux and others
            return Path("~/.local/share/Helyxium").expanduser()
    
    def print_header(self):
        """Print installer header."""
        print(f"\n{Colors.CYAN}{'='*60}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.HEADER}    Helyxium Universal VR Bridge Platform{Colors.END}")
        print(f"{Colors.BOLD}{Colors.BLUE}           Installation Wizard v{INSTALLER_VERSION}{Colors.END}")
        print(f"{Colors.CYAN}{'='*60}{Colors.END}\n")
        
        print(f"{Colors.BLUE}Target Platform:{Colors.END} {self.system.title()} ({self.architecture})")
        print(f"{Colors.BLUE}Python Version:{Colors.END} {'.'.join(map(str, self.python_version[:3]))}")
        print(f"{Colors.BLUE}Install Directory:{Colors.END} {self.install_dir}")
        print()
    
    def check_python_version(self) -> bool:
        """Check if Python version is compatible."""
        print(f"{Colors.BLUE}🐍 Checking Python version...{Colors.END}")
        
        if self.python_version < PYTHON_MIN_VERSION:
            print(f"{Colors.RED}❌ Python {'.'.join(map(str, PYTHON_MIN_VERSION))} or higher required.{Colors.END}")
            print(f"   Current version: {'.'.join(map(str, self.python_version[:3]))}")
            return False
        elif self.python_version >= PYTHON_MAX_VERSION:
            print(f"{Colors.YELLOW}⚠️  Python {'.'.join(map(str, self.python_version[:3]))} is newer than tested versions.{Colors.END}")
            print(f"   Helyxium supports up to Python {'.'.join(map(str, PYTHON_MAX_VERSION))}")
            response = input("   Continue anyway? (y/N): ").lower()
            if response != 'y':
                return False
        
        print(f"{Colors.GREEN}✅ Python version compatible{Colors.END}")
        return True
    
    def check_system_requirements(self) -> bool:
        """Check system-specific requirements."""
        print(f"{Colors.BLUE}🖥️  Checking system requirements...{Colors.END}")
        
        # Check available disk space (at least 500MB)
        try:
            if self.system == 'windows':
                import ctypes
                free_bytes = ctypes.c_ulonglong(0)
                ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                    ctypes.c_wchar_p(str(self.install_dir.parent)),
                    ctypes.pointer(free_bytes), None, None
                )
                free_space = free_bytes.value
            else:
                stat = shutil.disk_usage(self.install_dir.parent if self.install_dir.parent.exists() else Path.home())
                free_space = stat.free
            
            required_space = 500 * 1024 * 1024  # 500MB
            if free_space < required_space:
                print(f"{Colors.RED}❌ Insufficient disk space. Required: 500MB, Available: {free_space // (1024*1024)}MB{Colors.END}")
                return False
                
        except Exception:
            print(f"{Colors.YELLOW}⚠️  Could not check disk space, continuing...{Colors.END}")
        
        # Check for required system libraries
        missing_libs = []
        
        if self.system == 'linux':
            # Check for essential libraries
            required_libs = ['libGL.so.1', 'libX11.so.6', 'libxcb.so.1']
            for lib in required_libs:
                try:
                    subprocess.run(['ldconfig', '-p'], capture_output=True, check=True)
                    result = subprocess.run(['ldconfig', '-p'], capture_output=True, text=True)
                    if lib not in result.stdout:
                        missing_libs.append(lib)
                except:
                    pass
        
        if missing_libs:
            print(f"{Colors.YELLOW}⚠️  Missing system libraries: {', '.join(missing_libs)}{Colors.END}")
            if self.system == 'linux':
                print("   Try installing: sudo apt-get install libgl1-mesa-glx libx11-6 libxcb1")
                print("   Or: sudo yum install mesa-libGL libX11 libxcb")
        
        print(f"{Colors.GREEN}✅ System requirements check completed{Colors.END}")
        return True
    
    def create_directories(self) -> bool:
        """Create necessary directories."""
        print(f"{Colors.BLUE}📁 Creating installation directories...{Colors.END}")
        
        try:
            self.install_dir.mkdir(parents=True, exist_ok=True)
            self.app_dir.mkdir(parents=True, exist_ok=True)
            
            # Create temp directory
            self.temp_dir = Path(tempfile.mkdtemp(prefix='helyxium_install_'))
            
            print(f"{Colors.GREEN}✅ Directories created{Colors.END}")
            return True
            
        except PermissionError:
            print(f"{Colors.RED}❌ Permission denied. Try running as administrator/sudo.{Colors.END}")
            return False
        except Exception as e:
            print(f"{Colors.RED}❌ Failed to create directories: {e}{Colors.END}")
            return False
    
    def download_helyxium(self) -> bool:
        """Download Helyxium source code."""
        print(f"{Colors.BLUE}⬇️  Downloading Helyxium...{Colors.END}")
        
        # If running from local directory, copy instead of download
        current_dir = Path(__file__).parent.parent
        if (current_dir / "main.py").exists() and (current_dir / "src").exists():
            print(f"{Colors.BLUE}   Using local Helyxium installation{Colors.END}")
            try:
                # Copy all necessary files
                for item in current_dir.iterdir():
                    if item.name in ['.git', '__pycache__', '.pytest_cache', 'installer']:
                        continue
                    if item.is_dir():
                        shutil.copytree(item, self.app_dir / item.name, dirs_exist_ok=True)
                    else:
                        shutil.copy2(item, self.app_dir / item.name)
                
                print(f"{Colors.GREEN}✅ Local files copied{Colors.END}")
                return True
            except Exception as e:
                print(f"{Colors.RED}❌ Failed to copy local files: {e}{Colors.END}")
                return False
        
        # Download from GitHub
        download_url = f"{REPO_URL}/archive/refs/heads/main.zip"
        zip_path = self.temp_dir / "helyxium.zip"
        
        try:
            print(f"   Downloading from: {download_url}")
            urllib.request.urlretrieve(download_url, zip_path)
            
            # Extract
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(self.temp_dir)
            
            # Find extracted directory and move contents
            extracted_dirs = [d for d in self.temp_dir.iterdir() if d.is_dir() and d.name.startswith('helyxium')]
            if not extracted_dirs:
                raise Exception("Could not find extracted Helyxium directory")
            
            src_dir = extracted_dirs[0]
            for item in src_dir.iterdir():
                if item.is_dir():
                    shutil.copytree(item, self.app_dir / item.name, dirs_exist_ok=True)
                else:
                    shutil.copy2(item, self.app_dir / item.name)
            
            print(f"{Colors.GREEN}✅ Helyxium downloaded and extracted{Colors.END}")
            return True
            
        except urllib.error.URLError as e:
            print(f"{Colors.RED}❌ Download failed: {e}{Colors.END}")
            print("   Please check your internet connection or download manually.")
            return False
        except Exception as e:
            print(f"{Colors.RED}❌ Extraction failed: {e}{Colors.END}")
            return False
    
    def create_virtual_environment(self) -> bool:
        """Create Python virtual environment."""
        print(f"{Colors.BLUE}🐍 Creating virtual environment...{Colors.END}")
        
        try:
            venv.create(self.venv_dir, with_pip=True, clear=True)
            print(f"{Colors.GREEN}✅ Virtual environment created{Colors.END}")
            return True
        except Exception as e:
            print(f"{Colors.RED}❌ Failed to create virtual environment: {e}{Colors.END}")
            return False
    
    def get_venv_python(self) -> str:
        """Get path to Python executable in virtual environment."""
        if self.system == 'windows':
            return str(self.venv_dir / "Scripts" / "python.exe")
        else:
            return str(self.venv_dir / "bin" / "python")
    
    def get_venv_pip(self) -> str:
        """Get path to pip executable in virtual environment."""
        if self.system == 'windows':
            return str(self.venv_dir / "Scripts" / "pip.exe")
        else:
            return str(self.venv_dir / "bin" / "pip")
    
    def install_dependencies(self) -> bool:
        """Install Python dependencies."""
        print(f"{Colors.BLUE}📦 Installing dependencies...{Colors.END}")
        
        pip_path = self.get_venv_pip()
        requirements_file = self.app_dir / "requirements.txt"
        
        if not requirements_file.exists():
            print(f"{Colors.RED}❌ requirements.txt not found{Colors.END}")
            return False
        
        try:
            # Upgrade pip first
            subprocess.run([pip_path, "install", "--upgrade", "pip"], 
                         check=True, capture_output=True)
            
            # Install requirements
            print("   Installing Python packages (this may take a few minutes)...")
            result = subprocess.run([pip_path, "install", "-r", str(requirements_file)], 
                                  check=True, capture_output=True, text=True)
            
            print(f"{Colors.GREEN}✅ Dependencies installed successfully{Colors.END}")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"{Colors.RED}❌ Failed to install dependencies{Colors.END}")
            print(f"   Error: {e.stderr if e.stderr else e.stdout}")
            return False
    
    def create_launcher_scripts(self) -> bool:
        """Create platform-specific launcher scripts."""
        print(f"{Colors.BLUE}🚀 Creating launcher scripts...{Colors.END}")
        
        python_path = self.get_venv_python()
        main_script = self.app_dir / "main.py"
        
        try:
            if self.system == 'windows':
                # Create .bat launcher
                bat_content = f"""@echo off
cd /d "{self.app_dir}"
"{python_path}" main.py %*
"""
                launcher_path = self.install_dir / "Helyxium.bat"
                with open(launcher_path, 'w') as f:
                    f.write(bat_content)
                
                # Create .cmd launcher (alternative)
                cmd_launcher = self.install_dir / "Helyxium.cmd"
                shutil.copy2(launcher_path, cmd_launcher)
                
            else:  # Linux/macOS
                # Create shell script launcher
                sh_content = f"""#!/bin/bash
cd "{self.app_dir}"
"{python_path}" main.py "$@"
"""
                launcher_path = self.install_dir / "helyxium"
                with open(launcher_path, 'w') as f:
                    f.write(sh_content)
                os.chmod(launcher_path, 0o755)
            
            print(f"{Colors.GREEN}✅ Launcher scripts created{Colors.END}")
            return True
            
        except Exception as e:
            print(f"{Colors.RED}❌ Failed to create launcher scripts: {e}{Colors.END}")
            return False
    
    def create_desktop_shortcuts(self) -> bool:
        """Create desktop shortcuts and system integration."""
        print(f"{Colors.BLUE}🖥️  Creating desktop integration...{Colors.END}")
        
        try:
            if self.system == 'windows':
                self._create_windows_shortcuts()
            elif self.system == 'darwin':  # macOS
                self._create_macos_app()
            else:  # Linux
                self._create_linux_desktop_entry()
            
            print(f"{Colors.GREEN}✅ Desktop integration created{Colors.END}")
            return True
            
        except Exception as e:
            print(f"{Colors.YELLOW}⚠️  Desktop integration failed (optional): {e}{Colors.END}")
            return True  # Non-critical failure
    
    def _create_windows_shortcuts(self):
        """Create Windows shortcuts."""
        try:
            import winshell
            from win32com.client import Dispatch
            
            # Desktop shortcut
            desktop = winshell.desktop()
            shortcut_path = os.path.join(desktop, "Helyxium.lnk")
            
            shell = Dispatch('WScript.Shell')
            shortcut = shell.CreateShortCut(shortcut_path)
            shortcut.Targetpath = str(self.install_dir / "Helyxium.bat")
            shortcut.WorkingDirectory = str(self.app_dir)
            shortcut.IconLocation = str(self.app_dir / "assets" / "icons" / "helyxium.ico")
            shortcut.Description = "Helyxium Universal VR Bridge Platform"
            shortcut.save()
            
            # Start menu shortcut
            start_menu = winshell.start_menu()
            start_shortcut = os.path.join(start_menu, "Programs", "Helyxium.lnk")
            os.makedirs(os.path.dirname(start_shortcut), exist_ok=True)
            shutil.copy2(shortcut_path, start_shortcut)
            
        except ImportError:
            # Fallback: create without winshell
            print("   Note: Install pywin32 for better Windows integration")
    
    def _create_macos_app(self):
        """Create macOS application bundle."""
        app_bundle = self.install_dir.parent / "Helyxium.app"
        contents_dir = app_bundle / "Contents"
        macos_dir = contents_dir / "MacOS"
        resources_dir = contents_dir / "Resources"
        
        # Create directory structure
        macos_dir.mkdir(parents=True, exist_ok=True)
        resources_dir.mkdir(parents=True, exist_ok=True)
        
        # Create Info.plist
        plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleDisplayName</key>
    <string>Helyxium</string>
    <key>CFBundleExecutable</key>
    <string>Helyxium</string>
    <key>CFBundleIdentifier</key>
    <string>com.helyxium.app</string>
    <key>CFBundleName</key>
    <string>Helyxium</string>
    <key>CFBundleVersion</key>
    <string>{HELYXIUM_VERSION}</string>
    <key>CFBundleShortVersionString</key>
    <string>{HELYXIUM_VERSION}</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
</dict>
</plist>"""
        
        with open(contents_dir / "Info.plist", 'w') as f:
            f.write(plist_content)
        
        # Create launcher executable
        launcher_script = f"""#!/bin/bash
cd "{self.app_dir}"
"{self.get_venv_python()}" main.py "$@"
"""
        
        launcher_path = macos_dir / "Helyxium"
        with open(launcher_path, 'w') as f:
            f.write(launcher_script)
        os.chmod(launcher_path, 0o755)
        
        # Copy icon if available
        icon_path = self.app_dir / "assets" / "icons" / "helyxium_logo.png"
        if icon_path.exists():
            shutil.copy2(icon_path, resources_dir / "icon.png")
    
    def _create_linux_desktop_entry(self):
        """Create Linux desktop entry."""
        desktop_dir = Path.home() / ".local" / "share" / "applications"
        desktop_dir.mkdir(parents=True, exist_ok=True)
        
        desktop_entry = f"""[Desktop Entry]
Version=1.0
Type=Application
Name=Helyxium
Comment=Universal VR Bridge Platform
Exec={self.install_dir / "helyxium"}
Icon={self.app_dir / "assets" / "icons" / "helyxium_logo.png"}
Terminal=false
Categories=Game;Utility;
StartupNotify=true
"""
        
        desktop_file = desktop_dir / "helyxium.desktop"
        with open(desktop_file, 'w') as f:
            f.write(desktop_entry)
        os.chmod(desktop_file, 0o755)
        
        # Update desktop database
        try:
            subprocess.run(["update-desktop-database", str(desktop_dir)], 
                          capture_output=True, check=True)
        except:
            pass  # Non-critical
    
    def create_uninstaller(self) -> bool:
        """Create uninstaller script."""
        print(f"{Colors.BLUE}🗑️  Creating uninstaller...{Colors.END}")
        
        try:
            if self.system == 'windows':
                uninstall_content = f"""@echo off
echo Uninstalling Helyxium...
rmdir /s /q "{self.install_dir}"
del /q "%USERPROFILE%\\Desktop\\Helyxium.lnk"
del /q "%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\Helyxium.lnk"
echo Helyxium has been uninstalled.
pause
del "%~f0"
"""
                uninstaller_path = self.install_dir / "Uninstall.bat"
            else:
                uninstall_content = f"""#!/bin/bash
echo "Uninstalling Helyxium..."
rm -rf "{self.install_dir}"
rm -f "$HOME/Desktop/Helyxium.desktop"
rm -f "$HOME/.local/share/applications/helyxium.desktop"
if [ "$XDG_CURRENT_DESKTOP" = "GNOME" ] || [ "$XDG_CURRENT_DESKTOP" = "Unity" ]; then
    update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true
fi
echo "Helyxium has been uninstalled."
rm -- "$0"
"""
                uninstaller_path = self.install_dir / "uninstall.sh"
                
            with open(uninstaller_path, 'w') as f:
                f.write(uninstall_content)
            
            if self.system != 'windows':
                os.chmod(uninstaller_path, 0o755)
            
            print(f"{Colors.GREEN}✅ Uninstaller created{Colors.END}")
            return True
            
        except Exception as e:
            print(f"{Colors.YELLOW}⚠️  Failed to create uninstaller: {e}{Colors.END}")
            return True  # Non-critical
    
    def cleanup_temp(self):
        """Clean up temporary files."""
        if self.temp_dir and self.temp_dir.exists():
            try:
                shutil.rmtree(self.temp_dir)
            except:
                pass  # Best effort cleanup
    
    def run_post_install_test(self) -> bool:
        """Run a quick test to verify installation."""
        print(f"{Colors.BLUE}🧪 Running post-installation test...{Colors.END}")
        
        try:
            python_path = self.get_venv_python()
            test_script = f"""
import sys
sys.path.insert(0, r'{self.app_dir / "src"}')
try:
    from src.core.application import HelyxiumApp
    print('✅ Core modules load successfully')
    sys.exit(0)
except Exception as e:
    print(f'❌ Module load failed: {{e}}')
    sys.exit(1)
"""
            
            result = subprocess.run([python_path, "-c", test_script], 
                                  capture_output=True, text=True, 
                                  cwd=str(self.app_dir))
            
            if result.returncode == 0:
                print(f"{Colors.GREEN}✅ Installation test passed{Colors.END}")
                return True
            else:
                print(f"{Colors.YELLOW}⚠️  Installation test warnings: {result.stdout}{Colors.END}")
                return True  # Non-critical
                
        except Exception as e:
            print(f"{Colors.YELLOW}⚠️  Could not run installation test: {e}{Colors.END}")
            return True  # Non-critical
    
    def install(self) -> bool:
        """Run the complete installation process."""
        self.print_header()
        
        steps = [
            ("Python Version Check", self.check_python_version),
            ("System Requirements", self.check_system_requirements),
            ("Directory Creation", self.create_directories),
            ("Download Helyxium", self.download_helyxium),
            ("Virtual Environment", self.create_virtual_environment),
            ("Install Dependencies", self.install_dependencies),
            ("Create Launchers", self.create_launcher_scripts),
            ("Desktop Integration", self.create_desktop_shortcuts),
            ("Create Uninstaller", self.create_uninstaller),
            ("Post-Install Test", self.run_post_install_test),
        ]
        
        for step_name, step_func in steps:
            print(f"\n{Colors.BOLD}--- {step_name} ---{Colors.END}")
            try:
                if not step_func():
                    print(f"\n{Colors.RED}💥 Installation failed at: {step_name}{Colors.END}")
                    self.cleanup_temp()
                    return False
            except KeyboardInterrupt:
                print(f"\n{Colors.YELLOW}⚠️  Installation cancelled by user{Colors.END}")
                self.cleanup_temp()
                return False
            except Exception as e:
                print(f"\n{Colors.RED}💥 Unexpected error in {step_name}: {e}{Colors.END}")
                self.cleanup_temp()
                return False
        
        self.cleanup_temp()
        
        # Success message
        print(f"\n{Colors.GREEN}{'='*60}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.GREEN}    🎉 Helyxium Installation Complete! 🎉{Colors.END}")
        print(f"{Colors.GREEN}{'='*60}{Colors.END}")
        print(f"\n{Colors.BLUE}Installation Directory:{Colors.END} {self.install_dir}")
        print(f"{Colors.BLUE}Launch Command:{Colors.END}", end=" ")
        
        if self.system == 'windows':
            print(f"Double-click Helyxium.bat or run from Start Menu")
        else:
            print(f"{self.install_dir / 'helyxium'}")
        
        print(f"\n{Colors.CYAN}To uninstall:{Colors.END}", end=" ")
        if self.system == 'windows':
            print(f"Run {self.install_dir / 'Uninstall.bat'}")
        else:
            print(f"Run {self.install_dir / 'uninstall.sh'}")
        
        print(f"\n{Colors.YELLOW}Happy VR bridging with Helyxium! 🥽✨{Colors.END}\n")
        return True

def main():
    """Main installer entry point."""
    try:
        installer = HelyxiumInstaller()
        success = installer.install()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Installation cancelled.{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}Unexpected error: {e}{Colors.END}")
        sys.exit(1)

if __name__ == "__main__":
    main()