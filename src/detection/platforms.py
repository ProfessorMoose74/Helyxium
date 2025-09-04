"""
VR Platform Software Detection System

Detects installed VR software and available APIs:
- Steam VR and installed games
- Meta Quest software ecosystem
- PlayStation VR games library
- VRChat, Rec Room, Horizon Worlds
- Available APIs and SDK versions
"""

import os
import platform
import subprocess
import json
import winreg
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from enum import Enum
from dataclasses import dataclass

try:
    import winreg
except ImportError:
    winreg = None

try:
    import shutil
except ImportError:
    shutil = None


class VRPlatform(Enum):
    """VR platform types."""
    STEAM_VR = "steamvr"
    META_QUEST = "meta_quest"
    OCULUS_PC = "oculus_pc"
    PLAYSTATION_VR = "playstation_vr"
    VRCHAT = "vrchat"
    REC_ROOM = "rec_room"
    HORIZON_WORLDS = "horizon_worlds"
    VIVEPORT = "viveport"
    WINDOWS_MR = "windows_mr"
    VARJO_BASE = "varjo_base"
    PICO_CONNECT = "pico_connect"


@dataclass
class VRPlatformInfo:
    """Information about a detected VR platform."""
    platform: VRPlatform
    name: str
    version: Optional[str]
    install_path: Optional[str]
    is_running: bool
    is_installed: bool
    api_available: bool
    sdk_version: Optional[str]
    supported_games: List[str]
    capabilities: Set[str]
    additional_info: Dict[str, Any]


class VRPlatformDetector:
    """Detects installed VR platforms and software."""
    
    def __init__(self) -> None:
        """Initialize the VR platform detector."""
        self._detected_platforms: List[VRPlatformInfo] = []
        self._system = platform.system().lower()
    
    def detect_vr_platforms(self) -> Dict[str, Any]:
        """
        Detect installed VR software and available APIs.
        
        Returns:
            Dictionary with detected platforms and their information
        """
        self._detected_platforms = []
        
        detection_methods = [
            self._detect_steam_vr,
            self._detect_meta_oculus,
            self._detect_playstation_vr,
            self._detect_vrchat,
            self._detect_rec_room,
            self._detect_horizon_worlds,
            self._detect_viveport,
            self._detect_windows_mr,
            self._detect_varjo,
            self._detect_pico_connect,
        ]
        
        for method in detection_methods:
            try:
                method()
            except Exception as e:
                print(f"Platform detection method {method.__name__} failed: {e}")
        
        return self._compile_platform_results()
    
    def _detect_steam_vr(self) -> None:
        """Detect Steam VR installation and games."""
        try:
            # Common Steam installation paths
            steam_paths = []
            
            if self._system == "windows":
                # Windows Steam paths
                steam_paths.extend([
                    r"C:\Program Files (x86)\Steam",
                    r"C:\Program Files\Steam",
                    os.path.expandvars(r"%PROGRAMFILES%\Steam"),
                    os.path.expandvars(r"%PROGRAMFILES(X86)%\Steam"),
                ])
                
                # Check registry for Steam path (multiple possible keys)
                if winreg:
                    registry_paths = [
                        (winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam"),
                        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Valve\Steam"),
                        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam")
                    ]
                    
                    for hkey, subkey in registry_paths:
                        try:
                            with winreg.OpenKey(hkey, subkey) as key:
                                steam_path = winreg.QueryValueEx(key, "SteamPath")[0]
                                if steam_path and steam_path not in steam_paths:
                                    steam_paths.append(steam_path)
                        except (WindowsError, FileNotFoundError, OSError):
                            continue
            
            elif self._system == "darwin":  # macOS
                steam_paths.extend([
                    os.path.expanduser("~/Library/Application Support/Steam"),
                    "/Applications/Steam.app/Contents/MacOS"
                ])
            
            elif self._system == "linux":
                # Modern Linux distributions have various Steam installation paths
                steam_paths.extend([
                    os.path.expanduser("~/.steam"),
                    os.path.expanduser("~/.local/share/Steam"),
                    os.path.expanduser("~/.var/app/com.valvesoftware.Steam/home/.local/share/Steam"),  # Flatpak
                    os.path.expanduser("/var/lib/snapd/snap/steam/common/.local/share/Steam"),  # Snap
                    "/usr/local/games/steam",
                    "/opt/steam",
                    "/usr/share/steam",
                    "/var/lib/steam"
                ])
                
                # Check for Steam via package manager
                if shutil and shutil.which("steam"):
                    steam_paths.append("/usr/bin/steam")
            
            steam_info = None
            for steam_path in steam_paths:
                if os.path.exists(steam_path):
                    steam_info = self._analyze_steam_installation(steam_path)
                    break
            
            if steam_info:
                self._detected_platforms.append(steam_info)
                
        except Exception as e:
            print(f"Steam VR detection failed: {e}")
    
    def _analyze_steam_installation(self, steam_path: str) -> Optional[VRPlatformInfo]:
        """Analyze Steam installation for VR capabilities."""
        try:
            # Check for SteamVR
            steamvr_path = None
            vr_games = []
            
            # Look for SteamVR installation
            possible_steamvr_paths = [
                os.path.join(steam_path, "steamapps", "common", "SteamVR"),
                os.path.join(steam_path, "steamapps", "common", "SteamVRDriver"),
            ]
            
            for path in possible_steamvr_paths:
                if os.path.exists(path):
                    steamvr_path = path
                    break
            
            # Check if SteamVR is running
            is_running = self._is_process_running("vrmonitor") or self._is_process_running("vrserver")
            
            # Scan for VR games
            steamapps_path = os.path.join(steam_path, "steamapps", "common")
            if os.path.exists(steamapps_path):
                vr_games = self._scan_steam_vr_games(steamapps_path)
            
            # Get Steam version
            version = self._get_steam_version(steam_path)
            
            # Check API availability
            api_available = steamvr_path is not None
            
            return VRPlatformInfo(
                platform=VRPlatform.STEAM_VR,
                name="Steam VR",
                version=version,
                install_path=steamvr_path or steam_path,
                is_running=is_running,
                is_installed=steamvr_path is not None,
                api_available=api_available,
                sdk_version=self._get_steamvr_sdk_version(steamvr_path) if steamvr_path else None,
                supported_games=vr_games,
                capabilities={"lighthouse_tracking", "room_scale", "steam_overlay"},
                additional_info={
                    "steam_path": steam_path,
                    "steamvr_path": steamvr_path,
                    "game_count": len(vr_games)
                }
            )
            
        except Exception as e:
            print(f"Steam analysis failed: {e}")
            return None
    
    def _scan_steam_vr_games(self, steamapps_path: str) -> List[str]:
        """Scan for VR games in Steam installation."""
        vr_games = []
        
        # Known VR game folder patterns
        vr_game_patterns = [
            "Half-Life Alyx",
            "Beat Saber",
            "VRChat",
            "Pavlov VR",
            "Superhot VR",
            "The Lab",
            "Rec Room",
            "Blade and Sorcery",
            "Skyrim VR",
            "Fallout 4 VR",
            "Elite Dangerous",
            "No Man's Sky",
            "Boneworks",
            "Pistol Whip",
            "Job Simulator",
            "Vacation Simulator",
            "Arizona Sunshine",
            "Gorn",
            "Space Pirate Trainer",
            "Tilt Brush",
            "Google Earth VR"
        ]
        
        try:
            for item in os.listdir(steamapps_path):
                item_path = os.path.join(steamapps_path, item)
                if os.path.isdir(item_path):
                    # Check if folder name matches VR game patterns
                    for pattern in vr_game_patterns:
                        if pattern.lower() in item.lower():
                            vr_games.append(item)
                            break
        except Exception:
            pass
        
        return vr_games
    
    def _detect_meta_oculus(self) -> None:
        """Detect Meta/Oculus software."""
        try:
            oculus_paths = []
            
            if self._system == "windows":
                # Windows Oculus paths
                oculus_paths.extend([
                    r"C:\Program Files\Oculus",
                    r"C:\Program Files (x86)\Oculus",
                    os.path.expandvars(r"%PROGRAMFILES%\Oculus"),
                    os.path.expandvars(r"%PROGRAMFILES(X86)%\Oculus"),
                ])
                
                # Check registry (multiple possible keys for different Windows versions)
                if winreg:
                    registry_paths = [
                        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Oculus VR, LLC\Oculus", "Base"),
                        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Oculus VR, LLC\Oculus", "Base"),
                        (winreg.HKEY_CURRENT_USER, r"Software\Oculus VR, LLC\Oculus", "Base"),
                        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Meta\Oculus", "InstallPath"),
                        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Meta\Oculus", "InstallPath")
                    ]
                    
                    for hkey, subkey, value_name in registry_paths:
                        try:
                            with winreg.OpenKey(hkey, subkey) as key:
                                oculus_path = winreg.QueryValueEx(key, value_name)[0]
                                if oculus_path and oculus_path not in oculus_paths:
                                    oculus_paths.append(oculus_path)
                        except (WindowsError, FileNotFoundError, OSError):
                            continue
            
            # Meta Quest (standalone) - check for Quest Link/Air Link
            meta_info = None
            for oculus_path in oculus_paths:
                if os.path.exists(oculus_path):
                    meta_info = self._analyze_oculus_installation(oculus_path)
                    break
            
            if meta_info:
                self._detected_platforms.append(meta_info)
                
        except Exception as e:
            print(f"Meta/Oculus detection failed: {e}")
    
    def _analyze_oculus_installation(self, oculus_path: str) -> Optional[VRPlatformInfo]:
        """Analyze Oculus/Meta installation."""
        try:
            # Check if Oculus software is running
            is_running = (self._is_process_running("oculusclient") or 
                         self._is_process_running("oculusruntime") or
                         self._is_process_running("ovrservice"))
            
            # Get version
            version = self._get_oculus_version(oculus_path)
            
            # Check for Oculus games
            games = self._scan_oculus_games(oculus_path)
            
            # Check API availability
            api_available = os.path.exists(os.path.join(oculus_path, "Support", "oculus-runtime"))
            
            return VRPlatformInfo(
                platform=VRPlatform.OCULUS_PC,
                name="Oculus PC",
                version=version,
                install_path=oculus_path,
                is_running=is_running,
                is_installed=True,
                api_available=api_available,
                sdk_version=self._get_oculus_sdk_version(oculus_path),
                supported_games=games,
                capabilities={"quest_link", "air_link", "oculus_store", "hand_tracking"},
                additional_info={
                    "supports_quest_link": True,
                    "supports_air_link": True,
                    "game_count": len(games)
                }
            )
            
        except Exception as e:
            print(f"Oculus analysis failed: {e}")
            return None
    
    def _detect_playstation_vr(self) -> None:
        """Detect PlayStation VR software (PC adapter)."""
        try:
            # PlayStation VR doesn't have official PC support,
            # but check for third-party drivers like TrueOpenVR
            
            # Check for PSVR processes or drivers
            psvr_running = self._is_process_running("psvr") or self._is_process_running("psvr_driver")
            
            if psvr_running:
                psvr_info = VRPlatformInfo(
                    platform=VRPlatform.PLAYSTATION_VR,
                    name="PlayStation VR",
                    version="Unknown",
                    install_path=None,
                    is_running=psvr_running,
                    is_installed=psvr_running,  # Assume installed if running
                    api_available=False,
                    sdk_version=None,
                    supported_games=[],
                    capabilities={"6dof_tracking", "3d_audio"},
                    additional_info={
                        "note": "Third-party PC support detected"
                    }
                )
                self._detected_platforms.append(psvr_info)
                
        except Exception as e:
            print(f"PlayStation VR detection failed: {e}")
    
    def _detect_vrchat(self) -> None:
        """Detect VRChat installation."""
        try:
            vrchat_info = self._detect_application(
                "VRChat",
                ["vrchat", "vrchat.exe"],
                [
                    r"C:\Program Files\VRChat",
                    r"C:\Program Files (x86)\VRChat",
                    os.path.expanduser("~/Applications/VRChat.app") if self._system == "darwin" else "",
                ],
                VRPlatform.VRCHAT,
                {"social_vr", "user_generated_content", "avatars", "worlds"}
            )
            
            if vrchat_info:
                self._detected_platforms.append(vrchat_info)
                
        except Exception as e:
            print(f"VRChat detection failed: {e}")
    
    def _detect_rec_room(self) -> None:
        """Detect Rec Room installation."""
        try:
            rec_room_info = self._detect_application(
                "Rec Room",
                ["recroom", "recroom.exe"],
                [
                    r"C:\Program Files\Rec Room",
                    r"C:\Program Files (x86)\Rec Room",
                ],
                VRPlatform.REC_ROOM,
                {"social_vr", "games", "cross_platform"}
            )
            
            if rec_room_info:
                self._detected_platforms.append(rec_room_info)
                
        except Exception as e:
            print(f"Rec Room detection failed: {e}")
    
    def _detect_horizon_worlds(self) -> None:
        """Detect Horizon Worlds (Meta)."""
        try:
            # Horizon Worlds is primarily Quest-native,
            # but might be accessible through Oculus PC app
            
            if any(p.platform == VRPlatform.OCULUS_PC for p in self._detected_platforms):
                horizon_info = VRPlatformInfo(
                    platform=VRPlatform.HORIZON_WORLDS,
                    name="Horizon Worlds",
                    version="Unknown",
                    install_path=None,
                    is_running=False,
                    is_installed=True,  # Available through Meta ecosystem
                    api_available=False,
                    sdk_version=None,
                    supported_games=[],
                    capabilities={"social_vr", "world_building", "meta_ecosystem"},
                    additional_info={
                        "access_method": "Meta Quest platform",
                        "note": "Primarily Quest-native with potential PC access"
                    }
                )
                self._detected_platforms.append(horizon_info)
                
        except Exception as e:
            print(f"Horizon Worlds detection failed: {e}")
    
    def _detect_viveport(self) -> None:
        """Detect Viveport installation."""
        try:
            viveport_paths = [
                r"C:\Program Files\VIVE\Viveport",
                r"C:\Program Files (x86)\VIVE\Viveport",
                r"C:\Viveport",
            ]
            
            for viveport_path in viveport_paths:
                if os.path.exists(viveport_path):
                    viveport_info = VRPlatformInfo(
                        platform=VRPlatform.VIVEPORT,
                        name="Viveport",
                        version=self._get_viveport_version(viveport_path),
                        install_path=viveport_path,
                        is_running=self._is_process_running("viveport"),
                        is_installed=True,
                        api_available=True,
                        sdk_version=None,
                        supported_games=self._scan_viveport_games(viveport_path),
                        capabilities={"vive_ecosystem", "subscription_service"},
                        additional_info={"viveport_path": viveport_path}
                    )
                    self._detected_platforms.append(viveport_info)
                    break
                    
        except Exception as e:
            print(f"Viveport detection failed: {e}")
    
    def _detect_windows_mr(self) -> None:
        """Detect Windows Mixed Reality."""
        try:
            if self._system != "windows":
                return
            
            # Check for Windows MR portal
            wmr_running = self._is_process_running("mixedrealityportal")
            
            # Check registry for WMR installation (multiple possible locations)
            wmr_installed = False
            if winreg:
                wmr_registry_paths = [
                    r"SOFTWARE\Microsoft\Windows\CurrentVersion\Holographic",
                    r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Holographic",
                    r"SOFTWARE\Microsoft\MixedReality",
                    r"SOFTWARE\Microsoft\Windows Mixed Reality"
                ]
                
                for reg_path in wmr_registry_paths:
                    try:
                        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path) as key:
                            wmr_installed = True
                            break
                    except (WindowsError, FileNotFoundError, OSError):
                        continue
            
            if wmr_installed or wmr_running:
                wmr_info = VRPlatformInfo(
                    platform=VRPlatform.WINDOWS_MR,
                    name="Windows Mixed Reality",
                    version=self._get_windows_version(),
                    install_path=r"C:\Windows\System32\MixedRealityPortal",
                    is_running=wmr_running,
                    is_installed=wmr_installed,
                    api_available=wmr_installed,
                    sdk_version=None,
                    supported_games=["Mixed Reality Portal", "Cliff House"],
                    capabilities={"inside_out_tracking", "motion_controllers", "holographic"},
                    additional_info={"integrated_with_windows": True}
                )
                self._detected_platforms.append(wmr_info)
                
        except Exception as e:
            print(f"Windows MR detection failed: {e}")
    
    def _detect_varjo(self) -> None:
        """Detect Varjo software."""
        try:
            varjo_paths = [
                r"C:\Program Files\Varjo",
                r"C:\Program Files (x86)\Varjo",
            ]
            
            for varjo_path in varjo_paths:
                if os.path.exists(varjo_path):
                    varjo_info = VRPlatformInfo(
                        platform=VRPlatform.VARJO_BASE,
                        name="Varjo Base",
                        version=self._get_varjo_version(varjo_path),
                        install_path=varjo_path,
                        is_running=self._is_process_running("varjo"),
                        is_installed=True,
                        api_available=True,
                        sdk_version=None,
                        supported_games=[],
                        capabilities={"high_resolution", "enterprise_vr", "mixed_reality"},
                        additional_info={"varjo_path": varjo_path}
                    )
                    self._detected_platforms.append(varjo_info)
                    break
                    
        except Exception as e:
            print(f"Varjo detection failed: {e}")
    
    def _detect_pico_connect(self) -> None:
        """Detect Pico Connect software."""
        try:
            pico_paths = [
                r"C:\Program Files\Pico Interactive",
                r"C:\Program Files (x86)\Pico Interactive",
                r"C:\Program Files\PicoConnect",
            ]
            
            for pico_path in pico_paths:
                if os.path.exists(pico_path):
                    pico_info = VRPlatformInfo(
                        platform=VRPlatform.PICO_CONNECT,
                        name="Pico Connect",
                        version=None,
                        install_path=pico_path,
                        is_running=self._is_process_running("pico"),
                        is_installed=True,
                        api_available=True,
                        sdk_version=None,
                        supported_games=[],
                        capabilities={"pico_ecosystem", "wireless_streaming"},
                        additional_info={"pico_path": pico_path}
                    )
                    self._detected_platforms.append(pico_info)
                    break
                    
        except Exception as e:
            print(f"Pico Connect detection failed: {e}")
    
    def _detect_application(self, app_name: str, process_names: List[str], 
                          install_paths: List[str], platform: VRPlatform, 
                          capabilities: Set[str]) -> Optional[VRPlatformInfo]:
        """Generic application detection helper."""
        is_running = any(self._is_process_running(proc) for proc in process_names)
        install_path = None
        
        for path in install_paths:
            if path and os.path.exists(path):
                install_path = path
                break
        
        # Also check Steam for the application
        steam_installed = False
        if not install_path:
            # This would require Steam API integration or registry checking
            # For now, just check if it's running
            steam_installed = is_running
        
        if install_path or is_running or steam_installed:
            return VRPlatformInfo(
                platform=platform,
                name=app_name,
                version=None,
                install_path=install_path,
                is_running=is_running,
                is_installed=install_path is not None or steam_installed,
                api_available=False,
                sdk_version=None,
                supported_games=[],
                capabilities=capabilities,
                additional_info={
                    "steam_available": steam_installed,
                    "standalone_install": install_path is not None
                }
            )
        
        return None
    
    def _is_process_running(self, process_name: str) -> bool:
        """Check if a process is currently running."""
        try:
            if self._system == "windows":
                # Try multiple Windows process detection methods
                methods = [
                    (["tasklist", "/FI", f"IMAGENAME eq {process_name}*"], lambda out: process_name.lower() in out.lower()),
                    (["wmic", "process", "where", f"name='{process_name}*'", "get", "name"], lambda out: process_name.lower() in out.lower()),
                    (["powershell", "-Command", f"Get-Process -Name {process_name.replace('.exe', '')} -ErrorAction SilentlyContinue"], lambda out: len(out.strip()) > 0)
                ]
                
                for cmd, check_func in methods:
                    try:
                        result = subprocess.run(
                            cmd,
                            capture_output=True,
                            text=True,
                            timeout=10,
                            creationflags=subprocess.CREATE_NO_WINDOW if self._system == "windows" else 0
                        )
                        if result.returncode == 0 and check_func(result.stdout):
                            return True
                    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
                        continue
            else:
                # Linux/macOS process detection
                methods = [
                    ["pgrep", "-f", process_name],
                    ["pidof", process_name],
                    ["ps", "aux"]  # Fallback: search in full process list
                ]
                
                for i, cmd in enumerate(methods):
                    try:
                        result = subprocess.run(
                            cmd,
                            capture_output=True,
                            text=True,
                            timeout=10
                        )
                        if i < 2:  # pgrep, pidof
                            return result.returncode == 0
                        else:  # ps aux
                            return process_name.lower() in result.stdout.lower()
                    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
                        continue
        except Exception:
            pass
        return False
    
    def _get_steam_version(self, steam_path: str) -> Optional[str]:
        """Get Steam version."""
        try:
            version_file = os.path.join(steam_path, "package", "steam_client_win32")
            if os.path.exists(version_file):
                with open(version_file, "r") as f:
                    return f.read().strip()
        except Exception:
            pass
        return None
    
    def _get_steamvr_sdk_version(self, steamvr_path: str) -> Optional[str]:
        """Get SteamVR SDK version."""
        try:
            # Check for version info in SteamVR directory
            version_files = [
                os.path.join(steamvr_path, "drivers", "lighthouse", "bin", "win64", "driver_lighthouse.dll"),
                os.path.join(steamvr_path, "bin", "win64", "vrclient_x64.dll")
            ]
            
            for version_file in version_files:
                if os.path.exists(version_file):
                    # This would require proper version extraction from DLL
                    # For now, return a placeholder
                    return "Latest"
        except Exception:
            pass
        return None
    
    def _get_oculus_version(self, oculus_path: str) -> Optional[str]:
        """Get Oculus software version."""
        try:
            # Check for version in Oculus directory
            manifest_file = os.path.join(oculus_path, "CoreData", "Manifests", "oculus-client.json")
            if os.path.exists(manifest_file):
                with open(manifest_file, "r") as f:
                    manifest = json.load(f)
                    return manifest.get("version")
        except Exception:
            pass
        return None
    
    def _get_oculus_sdk_version(self, oculus_path: str) -> Optional[str]:
        """Get Oculus SDK version."""
        try:
            sdk_path = os.path.join(oculus_path, "Support", "oculus-runtime")
            if os.path.exists(sdk_path):
                return "Latest"
        except Exception:
            pass
        return None
    
    def _scan_oculus_games(self, oculus_path: str) -> List[str]:
        """Scan for Oculus games."""
        games = []
        try:
            software_path = os.path.join(oculus_path, "Software")
            if os.path.exists(software_path):
                for item in os.listdir(software_path):
                    if os.path.isdir(os.path.join(software_path, item)):
                        games.append(item)
        except Exception:
            pass
        return games
    
    def _scan_viveport_games(self, viveport_path: str) -> List[str]:
        """Scan for Viveport games."""
        games = []
        try:
            # Viveport games are typically in a games subdirectory
            games_path = os.path.join(viveport_path, "Games")
            if os.path.exists(games_path):
                for item in os.listdir(games_path):
                    if os.path.isdir(os.path.join(games_path, item)):
                        games.append(item)
        except Exception:
            pass
        return games
    
    def _get_viveport_version(self, viveport_path: str) -> Optional[str]:
        """Get Viveport version."""
        try:
            # Check for version info
            version_file = os.path.join(viveport_path, "version.txt")
            if os.path.exists(version_file):
                with open(version_file, "r") as f:
                    return f.read().strip()
        except Exception:
            pass
        return None
    
    def _get_varjo_version(self, varjo_path: str) -> Optional[str]:
        """Get Varjo software version."""
        try:
            # Check for version info in Varjo directory
            version_file = os.path.join(varjo_path, "version.txt")
            if os.path.exists(version_file):
                with open(version_file, "r") as f:
                    return f.read().strip()
        except Exception:
            pass
        return None
    
    def _get_windows_version(self) -> str:
        """Get Windows version."""
        try:
            return platform.platform()
        except Exception:
            return "Unknown"
    
    def _compile_platform_results(self) -> Dict[str, Any]:
        """Compile platform detection results."""
        result = {
            "platforms_detected": len(self._detected_platforms),
            "platforms": [],
            "running_platforms": [],
            "available_apis": [],
            "total_games": 0,
            "capabilities_summary": set(),
        }
        
        for platform_info in self._detected_platforms:
            platform_data = {
                "platform": platform_info.platform.value,
                "name": platform_info.name,
                "version": platform_info.version,
                "install_path": platform_info.install_path,
                "is_running": platform_info.is_running,
                "is_installed": platform_info.is_installed,
                "api_available": platform_info.api_available,
                "sdk_version": platform_info.sdk_version,
                "supported_games": platform_info.supported_games,
                "game_count": len(platform_info.supported_games),
                "capabilities": list(platform_info.capabilities),
                "additional_info": platform_info.additional_info
            }
            
            result["platforms"].append(platform_data)
            
            if platform_info.is_running:
                result["running_platforms"].append(platform_info.platform.value)
            
            if platform_info.api_available:
                result["available_apis"].append(platform_info.platform.value)
            
            result["total_games"] += len(platform_info.supported_games)
            result["capabilities_summary"].update(platform_info.capabilities)
        
        # Convert set to list for JSON serialization
        result["capabilities_summary"] = list(result["capabilities_summary"])
        
        return result
    
    def get_detected_platforms(self) -> List[VRPlatformInfo]:
        """Get list of detected VR platforms."""
        return self._detected_platforms.copy()
    
    def is_platform_available(self, platform: VRPlatform) -> bool:
        """Check if a specific platform is available."""
        return any(p.platform == platform and p.is_installed for p in self._detected_platforms)
    
    def is_platform_running(self, platform: VRPlatform) -> bool:
        """Check if a specific platform is currently running."""
        return any(p.platform == platform and p.is_running for p in self._detected_platforms)
    
    def get_platform_info(self, platform: VRPlatform) -> Optional[VRPlatformInfo]:
        """Get information about a specific platform."""
        for p in self._detected_platforms:
            if p.platform == platform:
                return p
        return None


class PlatformDetector(VRPlatformDetector):
    """Alias for VRPlatformDetector to match main application expectations."""
    
    def __init__(self):
        super().__init__()
        self._previous_platforms = None
    
    def has_platforms_changed(self) -> bool:
        """Check if platform configuration has changed since last detection."""
        current_platforms = [
            (p.platform, p.is_installed, p.is_running) 
            for p in self._detected_platforms
        ]
        
        if self._previous_platforms is None:
            self._previous_platforms = current_platforms
            return True
        
        changed = self._previous_platforms != current_platforms
        self._previous_platforms = current_platforms
        return changed


# Global instances for easy access
vr_platform_detector = VRPlatformDetector()
platform_detector = PlatformDetector()