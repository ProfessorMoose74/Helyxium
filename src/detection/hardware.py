"""
VR Hardware Detection System

Detects all connected VR hardware including:
- Meta Quest (1, 2, 3, Pro, 3S)
- PlayStation VR (PSVR, PSVR2)
- Valve Index, HTC Vive series
- Windows Mixed Reality headsets
- Apple Vision Pro
- Pico and other standalone headsets

Returns capabilities matrix for each device.
"""

import logging
import platform
import re
import subprocess  # nosec B404 - subprocess is required for hardware detection with safe, hardcoded commands
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

try:
    import openvr
except ImportError:
    openvr = None

try:
    import usb.core
    import usb.util
except ImportError:
    usb = None


class VRHeadsetType(Enum):
    """VR headset types."""

    META_QUEST_1 = "meta_quest_1"
    META_QUEST_2 = "meta_quest_2"
    META_QUEST_3 = "meta_quest_3"
    META_QUEST_PRO = "meta_quest_pro"
    META_QUEST_3S = "meta_quest_3s"
    PSVR = "psvr"
    PSVR2 = "psvr2"
    VALVE_INDEX = "valve_index"
    HTC_VIVE = "htc_vive"
    HTC_VIVE_PRO = "htc_vive_pro"
    HTC_VIVE_PRO_2 = "htc_vive_pro_2"
    HTC_VIVE_COSMOS = "htc_vive_cosmos"
    WMR_GENERIC = "wmr_generic"
    APPLE_VISION_PRO = "apple_vision_pro"
    PICO_4 = "pico_4"
    VARJO_AERO = "varjo_aero"
    UNKNOWN = "unknown"


@dataclass
class VRCapabilities:
    """VR headset capabilities."""

    has_6dof: bool = True
    has_hand_tracking: bool = False
    has_eye_tracking: bool = False
    has_passthrough: bool = False
    has_wireless: bool = False
    max_refresh_rate: int = 90
    resolution_per_eye: Tuple[int, int] = (1832, 1920)
    fov_horizontal: float = 110.0
    fov_vertical: float = 90.0
    tracking_technology: str = "inside_out"
    supports_room_scale: bool = True


@dataclass
class VRDevice:
    """Detected VR device information."""

    device_type: VRHeadsetType
    name: str
    manufacturer: str
    serial_number: Optional[str] = None
    firmware_version: Optional[str] = None
    connection_type: str = "unknown"
    is_connected: bool = False
    capabilities: VRCapabilities = None
    additional_info: Dict[str, Any] = None

    def __post_init__(self):
        if self.capabilities is None:
            self.capabilities = VRCapabilities()
        if self.additional_info is None:
            self.additional_info = {}


class VRHardwareDetector:
    """Detects VR hardware and their capabilities."""

    # USB Vendor/Product IDs for VR headsets
    USB_DEVICE_IDS = {
        # Meta Quest devices
        (0x2833, 0x0186): VRHeadsetType.META_QUEST_1,
        (0x2833, 0x0183): VRHeadsetType.META_QUEST_2,
        (0x2833, 0x0204): VRHeadsetType.META_QUEST_3,
        (0x2833, 0x0182): VRHeadsetType.META_QUEST_PRO,
        (0x2833, 0x0206): VRHeadsetType.META_QUEST_3S,
        # HTC Vive devices
        (0x0BB4, 0x2C87): VRHeadsetType.HTC_VIVE,
        (0x0BB4, 0x0306): VRHeadsetType.HTC_VIVE_PRO,
        (0x0BB4, 0x0309): VRHeadsetType.HTC_VIVE_PRO_2,
        (0x0BB4, 0x0313): VRHeadsetType.HTC_VIVE_COSMOS,
        # Valve Index
        (0x28DE, 0x2000): VRHeadsetType.VALVE_INDEX,
        # PlayStation VR
        (0x054C, 0x09AF): VRHeadsetType.PSVR,
        (0x054C, 0x0CDE): VRHeadsetType.PSVR2,
        # Pico devices
        (0x2D40, 0x0001): VRHeadsetType.PICO_4,
    }

    # Device capabilities mapping
    DEVICE_CAPABILITIES = {
        VRHeadsetType.META_QUEST_1: VRCapabilities(
            has_6dof=True,
            has_hand_tracking=False,
            has_eye_tracking=False,
            has_passthrough=False,
            has_wireless=True,
            max_refresh_rate=72,
            resolution_per_eye=(1440, 1600),
            fov_horizontal=100.0,
            tracking_technology="inside_out",
        ),
        VRHeadsetType.META_QUEST_2: VRCapabilities(
            has_6dof=True,
            has_hand_tracking=True,
            has_eye_tracking=False,
            has_passthrough=True,
            has_wireless=True,
            max_refresh_rate=120,
            resolution_per_eye=(1832, 1920),
            fov_horizontal=100.0,
            tracking_technology="inside_out",
        ),
        VRHeadsetType.META_QUEST_3: VRCapabilities(
            has_6dof=True,
            has_hand_tracking=True,
            has_eye_tracking=False,
            has_passthrough=True,
            has_wireless=True,
            max_refresh_rate=120,
            resolution_per_eye=(2064, 2208),
            fov_horizontal=110.0,
            tracking_technology="inside_out",
        ),
        VRHeadsetType.META_QUEST_PRO: VRCapabilities(
            has_6dof=True,
            has_hand_tracking=True,
            has_eye_tracking=True,
            has_passthrough=True,
            has_wireless=True,
            max_refresh_rate=90,
            resolution_per_eye=(1800, 1920),
            fov_horizontal=106.0,
            tracking_technology="inside_out",
        ),
        VRHeadsetType.META_QUEST_3S: VRCapabilities(
            has_6dof=True,
            has_hand_tracking=True,
            has_eye_tracking=False,
            has_passthrough=True,
            has_wireless=True,
            max_refresh_rate=120,
            resolution_per_eye=(1832, 1920),
            fov_horizontal=110.0,
            tracking_technology="inside_out",
        ),
        VRHeadsetType.VALVE_INDEX: VRCapabilities(
            has_6dof=True,
            has_hand_tracking=False,
            has_eye_tracking=False,
            has_passthrough=False,
            has_wireless=False,
            max_refresh_rate=144,
            resolution_per_eye=(1440, 1600),
            fov_horizontal=130.0,
            tracking_technology="lighthouse",
        ),
        VRHeadsetType.HTC_VIVE: VRCapabilities(
            has_6dof=True,
            has_hand_tracking=False,
            has_eye_tracking=False,
            has_passthrough=False,
            has_wireless=False,
            max_refresh_rate=90,
            resolution_per_eye=(1080, 1200),
            fov_horizontal=110.0,
            tracking_technology="lighthouse",
        ),
        VRHeadsetType.HTC_VIVE_PRO: VRCapabilities(
            has_6dof=True,
            has_hand_tracking=False,
            has_eye_tracking=False,
            has_passthrough=False,
            has_wireless=False,
            max_refresh_rate=90,
            resolution_per_eye=(1440, 1600),
            fov_horizontal=110.0,
            tracking_technology="lighthouse",
        ),
        VRHeadsetType.HTC_VIVE_PRO_2: VRCapabilities(
            has_6dof=True,
            has_hand_tracking=False,
            has_eye_tracking=False,
            has_passthrough=False,
            has_wireless=False,
            max_refresh_rate=120,
            resolution_per_eye=(2448, 2448),
            fov_horizontal=120.0,
            tracking_technology="lighthouse",
        ),
        VRHeadsetType.PSVR: VRCapabilities(
            has_6dof=True,
            has_hand_tracking=False,
            has_eye_tracking=False,
            has_passthrough=False,
            has_wireless=False,
            max_refresh_rate=120,
            resolution_per_eye=(960, 1080),
            fov_horizontal=100.0,
            tracking_technology="outside_in",
        ),
        VRHeadsetType.PSVR2: VRCapabilities(
            has_6dof=True,
            has_hand_tracking=False,
            has_eye_tracking=True,
            has_passthrough=False,
            has_wireless=False,
            max_refresh_rate=120,
            resolution_per_eye=(2000, 2040),
            fov_horizontal=110.0,
            tracking_technology="inside_out",
        ),
        VRHeadsetType.PICO_4: VRCapabilities(
            has_6dof=True,
            has_hand_tracking=True,
            has_eye_tracking=False,
            has_passthrough=True,
            has_wireless=True,
            max_refresh_rate=90,
            resolution_per_eye=(2160, 2160),
            fov_horizontal=105.0,
            tracking_technology="inside_out",
        ),
    }

    def __init__(self) -> None:
        """Initialize the VR hardware detector."""
        self._detected_devices: List[VRDevice] = []
        self._openvr_available = openvr is not None
        self._usb_available = usb is not None

    def detect_vr_hardware(self) -> Dict[str, Any]:
        """
        Detect all connected VR hardware and return capabilities matrix.

        Returns:
            Dictionary with detected devices and their capabilities
        """
        self._detected_devices = []

        detection_methods = [
            self._detect_via_openvr,
            self._detect_via_usb,
            self._detect_via_platform_specific,
            self._detect_via_process_detection,
        ]

        for method in detection_methods:
            try:
                method()
            except Exception as e:
                print(f"Detection method {method.__name__} failed: {e}")

        return self._compile_detection_results()

    def _detect_via_openvr(self) -> None:
        """Detect VR devices using OpenVR API."""
        if not self._openvr_available:
            return

        try:
            openvr.init(openvr.VRApplication_Background)

            system = openvr.VRSystem()
            if system is None:
                return

            # Get HMD info
            hmd_present = system.isDisplayOnDesktop()
            if not hmd_present:
                return

            # Get device properties
            model = system.getStringTrackedDeviceProperty(
                openvr.k_unTrackedDeviceIndex_Hmd, openvr.Prop_ModelNumber_String
            )

            manufacturer = system.getStringTrackedDeviceProperty(
                openvr.k_unTrackedDeviceIndex_Hmd, openvr.Prop_ManufacturerName_String
            )

            serial = system.getStringTrackedDeviceProperty(
                openvr.k_unTrackedDeviceIndex_Hmd, openvr.Prop_SerialNumber_String
            )

            # Determine device type from model name
            device_type = self._identify_device_type_from_model(model)

            device = VRDevice(
                device_type=device_type,
                name=model or "Unknown VR Headset",
                manufacturer=manufacturer or "Unknown",
                serial_number=serial,
                connection_type="openvr",
                is_connected=True,
                capabilities=self.DEVICE_CAPABILITIES.get(
                    device_type, VRCapabilities()
                ),
                additional_info={"openvr_model": model},
            )

            self._detected_devices.append(device)

        except Exception as e:
            print(f"OpenVR detection failed: {e}")
        finally:
            try:
                openvr.shutdown()
            except Exception as e:
                logger.debug(f"Failed to shutdown OpenVR: {e}")

    def _detect_via_usb(self) -> None:
        """Detect VR devices via USB enumeration."""
        if not self._usb_available:
            return

        try:
            # Find all USB devices
            devices = usb.core.find(find_all=True)

            for device in devices:
                device_id = (device.idVendor, device.idProduct)

                if device_id in self.USB_DEVICE_IDS:
                    device_type = self.USB_DEVICE_IDS[device_id]

                    # Try to get device info
                    try:
                        manufacturer = (
                            usb.util.get_string(device, device.iManufacturer)
                            or "Unknown"
                        )
                        product = (
                            usb.util.get_string(device, device.iProduct)
                            or "Unknown VR Headset"
                        )
                        serial = None
                        try:
                            serial = usb.util.get_string(device, device.iSerialNumber)
                        except Exception as e:
                            logger.debug(f"Failed to get serial number for USB device: {e}")
                    except Exception:
                        manufacturer = "Unknown"
                        product = device_type.value.replace("_", " ").title()
                        serial = None

                    vr_device = VRDevice(
                        device_type=device_type,
                        name=product,
                        manufacturer=manufacturer,
                        serial_number=serial,
                        connection_type="usb",
                        is_connected=True,
                        capabilities=self.DEVICE_CAPABILITIES.get(
                            device_type, VRCapabilities()
                        ),
                        additional_info={
                            "usb_vendor_id": f"0x{device.idVendor:04x}",
                            "usb_product_id": f"0x{device.idProduct:04x}",
                        },
                    )

                    # Avoid duplicates
                    if not any(
                        d.serial_number == serial and d.device_type == device_type
                        for d in self._detected_devices
                    ):
                        self._detected_devices.append(vr_device)

        except Exception as e:
            print(f"USB detection failed: {e}")

    def _detect_via_platform_specific(self) -> None:
        """Use platform-specific detection methods."""
        system = platform.system().lower()

        if system == "windows":
            self._detect_windows_vr()
        elif system == "darwin":  # macOS
            self._detect_macos_vr()
        elif system == "linux":
            self._detect_linux_vr()

    def _detect_windows_vr(self) -> None:
        """Detect VR devices on Windows."""
        try:
            # Check Windows Mixed Reality
            wmr_query = (
                "Get-PnpDevice | Where-Object {$_.FriendlyName -like "
                "'*Mixed Reality*' -or $_.FriendlyName -like '*HoloLens*'}"
            )
            result = subprocess.run(  # nosec B603, B607 - Safe hardcoded command for device detection
                ["powershell", "-Command", wmr_query],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0 and result.stdout.strip():
                # WMR device detected
                device = VRDevice(
                    device_type=VRHeadsetType.WMR_GENERIC,
                    name="Windows Mixed Reality Headset",
                    manufacturer="Microsoft",
                    connection_type="wmr",
                    is_connected=True,
                    capabilities=VRCapabilities(
                        has_6dof=True,
                        has_hand_tracking=True,
                        has_eye_tracking=False,
                        has_passthrough=False,
                        has_wireless=False,
                        max_refresh_rate=90,
                        resolution_per_eye=(1440, 1440),
                        tracking_technology="inside_out",
                    ),
                )
                self._detected_devices.append(device)

        except Exception as e:
            print(f"Windows VR detection failed: {e}")

    def _detect_macos_vr(self) -> None:
        """Detect VR devices on macOS."""
        try:
            # Check for Apple Vision Pro
            result = subprocess.run(  # nosec B603, B607 - Safe hardcoded command for USB device detection
                ["system_profiler", "SPUSBDataType"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                output = result.stdout.lower()
                if "apple" in output and ("vision" in output or "reality" in output):
                    device = VRDevice(
                        device_type=VRHeadsetType.APPLE_VISION_PRO,
                        name="Apple Vision Pro",
                        manufacturer="Apple",
                        connection_type="usb",
                        is_connected=True,
                        capabilities=VRCapabilities(
                            has_6dof=True,
                            has_hand_tracking=True,
                            has_eye_tracking=True,
                            has_passthrough=True,
                            has_wireless=False,
                            max_refresh_rate=90,
                            resolution_per_eye=(3660, 3200),
                            tracking_technology="inside_out",
                        ),
                    )
                    self._detected_devices.append(device)

        except Exception as e:
            print(f"macOS VR detection failed: {e}")

    def _detect_linux_vr(self) -> None:
        """Detect VR devices on Linux."""
        try:
            # Check lsusb output
            result = subprocess.run(  # nosec B603, B607 - Safe hardcoded command for USB device listing
                ["lsusb"], capture_output=True, text=True, timeout=10
            )

            if result.returncode == 0:
                lines = result.stdout.lower()

                # Look for known VR device patterns
                vr_patterns = [
                    (r"htc.*vive", VRHeadsetType.HTC_VIVE),
                    (r"valve.*index", VRHeadsetType.VALVE_INDEX),
                    (r"meta.*quest", VRHeadsetType.META_QUEST_2),  # Generic Quest
                    (r"oculus", VRHeadsetType.META_QUEST_2),
                ]

                for pattern, device_type in vr_patterns:
                    if re.search(pattern, lines):
                        device = VRDevice(
                            device_type=device_type,
                            name=device_type.value.replace("_", " ").title(),
                            manufacturer="Unknown",
                            connection_type="usb",
                            is_connected=True,
                            capabilities=self.DEVICE_CAPABILITIES.get(
                                device_type, VRCapabilities()
                            ),
                        )

                        # Avoid duplicates
                        if not any(
                            d.device_type == device_type for d in self._detected_devices
                        ):
                            self._detected_devices.append(device)

        except Exception as e:
            print(f"Linux VR detection failed: {e}")

    def _detect_via_process_detection(self) -> None:
        """Detect VR devices by checking for running VR processes."""
        try:
            # Check for running VR software processes
            if platform.system().lower() == "windows":
                result = subprocess.run(  # nosec B603, B607 - Safe hardcoded command for process listing
                    ["tasklist", "/FO", "CSV"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
            else:
                result = subprocess.run(  # nosec B603, B607 - Safe hardcoded command for process listing
                    ["ps", "aux"], capture_output=True, text=True, timeout=10
                )

            if result.returncode == 0:
                output = result.stdout.lower()

                # Process patterns that indicate VR headsets
                process_patterns = {
                    "steamvr": VRHeadsetType.VALVE_INDEX,
                    "oculusruntime": VRHeadsetType.META_QUEST_2,
                    "oculus": VRHeadsetType.META_QUEST_2,
                    "vrmonitor": VRHeadsetType.HTC_VIVE,
                    "vrserver": VRHeadsetType.VALVE_INDEX,
                }

                for process, device_type in process_patterns.items():
                    if process in output:
                        # Only add if we haven't detected this type already
                        if not any(
                            d.device_type == device_type for d in self._detected_devices
                        ):
                            device_name = (
                                f"{device_type.value.replace('_', ' ').title()} "
                                "(Process Detection)"
                            )
                            device = VRDevice(
                                device_type=device_type,
                                name=device_name,
                                manufacturer="Unknown",
                                connection_type="process",
                                is_connected=True,
                                capabilities=self.DEVICE_CAPABILITIES.get(
                                    device_type, VRCapabilities()
                                ),
                                additional_info={"detected_via": "process"},
                            )
                            self._detected_devices.append(device)

        except Exception as e:
            print(f"Process detection failed: {e}")

    def _identify_device_type_from_model(self, model: str) -> VRHeadsetType:
        """Identify device type from model string."""
        if not model:
            return VRHeadsetType.UNKNOWN

        model_lower = model.lower()

        # Meta/Oculus devices
        if "quest" in model_lower:
            if "3" in model_lower:
                if "pro" in model_lower:
                    return VRHeadsetType.META_QUEST_PRO
                elif "s" in model_lower:
                    return VRHeadsetType.META_QUEST_3S
                else:
                    return VRHeadsetType.META_QUEST_3
            elif "2" in model_lower:
                return VRHeadsetType.META_QUEST_2
            else:
                return VRHeadsetType.META_QUEST_1

        # HTC devices
        if "vive" in model_lower:
            if "pro" in model_lower:
                if "2" in model_lower:
                    return VRHeadsetType.HTC_VIVE_PRO_2
                else:
                    return VRHeadsetType.HTC_VIVE_PRO
            elif "cosmos" in model_lower:
                return VRHeadsetType.HTC_VIVE_COSMOS
            else:
                return VRHeadsetType.HTC_VIVE

        # Valve devices
        if "index" in model_lower:
            return VRHeadsetType.VALVE_INDEX

        # PlayStation VR
        if "psvr" in model_lower or "playstation vr" in model_lower:
            if "2" in model_lower:
                return VRHeadsetType.PSVR2
            else:
                return VRHeadsetType.PSVR

        # Pico devices
        if "pico" in model_lower:
            return VRHeadsetType.PICO_4

        return VRHeadsetType.UNKNOWN

    def _compile_detection_results(self) -> Dict[str, Any]:
        """Compile detection results into a structured format."""
        result = {
            "devices_detected": len(self._detected_devices),
            "devices": [],
            "capabilities_summary": {},
            "supported_features": set(),
            "detection_methods": [],
        }

        for device in self._detected_devices:
            device_info = {
                "type": device.device_type.value,
                "name": device.name,
                "manufacturer": device.manufacturer,
                "serial_number": device.serial_number,
                "connection_type": device.connection_type,
                "is_connected": device.is_connected,
                "capabilities": {
                    "has_6dof": device.capabilities.has_6dof,
                    "has_hand_tracking": device.capabilities.has_hand_tracking,
                    "has_eye_tracking": device.capabilities.has_eye_tracking,
                    "has_passthrough": device.capabilities.has_passthrough,
                    "has_wireless": device.capabilities.has_wireless,
                    "max_refresh_rate": device.capabilities.max_refresh_rate,
                    "resolution_per_eye": device.capabilities.resolution_per_eye,
                    "fov_horizontal": device.capabilities.fov_horizontal,
                    "fov_vertical": device.capabilities.fov_vertical,
                    "tracking_technology": device.capabilities.tracking_technology,
                    "supports_room_scale": device.capabilities.supports_room_scale,
                },
                "additional_info": device.additional_info,
            }

            result["devices"].append(device_info)

            # Aggregate supported features
            caps = device.capabilities
            if caps.has_6dof:
                result["supported_features"].add("6dof_tracking")
            if caps.has_hand_tracking:
                result["supported_features"].add("hand_tracking")
            if caps.has_eye_tracking:
                result["supported_features"].add("eye_tracking")
            if caps.has_passthrough:
                result["supported_features"].add("passthrough")
            if caps.has_wireless:
                result["supported_features"].add("wireless")
            if caps.supports_room_scale:
                result["supported_features"].add("room_scale")

            # Track detection methods
            if device.connection_type not in result["detection_methods"]:
                result["detection_methods"].append(device.connection_type)

        # Convert set to list for JSON serialization
        result["supported_features"] = list(result["supported_features"])

        # Create capabilities summary
        if self._detected_devices:
            result["capabilities_summary"] = {
                "best_resolution": max(
                    (
                        dev.capabilities.resolution_per_eye[0]
                        * dev.capabilities.resolution_per_eye[1]
                        for dev in self._detected_devices
                    ),
                    default=0,
                ),
                "highest_refresh_rate": max(
                    (
                        dev.capabilities.max_refresh_rate
                        for dev in self._detected_devices
                    ),
                    default=0,
                ),
                "widest_fov": max(
                    (dev.capabilities.fov_horizontal for dev in self._detected_devices),
                    default=0,
                ),
                "has_any_hand_tracking": any(
                    dev.capabilities.has_hand_tracking for dev in self._detected_devices
                ),
                "has_any_eye_tracking": any(
                    dev.capabilities.has_eye_tracking for dev in self._detected_devices
                ),
                "has_any_passthrough": any(
                    dev.capabilities.has_passthrough for dev in self._detected_devices
                ),
                "has_any_wireless": any(
                    dev.capabilities.has_wireless for dev in self._detected_devices
                ),
            }

        return result

    def get_detected_devices(self) -> List[VRDevice]:
        """Get list of detected VR devices."""
        return self._detected_devices.copy()

    def is_vr_ready(self) -> bool:
        """Check if any VR device is ready for use."""
        return any(device.is_connected for device in self._detected_devices)

    def get_primary_device(self) -> Optional[VRDevice]:
        """Get the primary/best VR device available."""
        if not self._detected_devices:
            return None

        # Prioritize by connection quality and capabilities
        connected_devices = [d for d in self._detected_devices if d.is_connected]
        if not connected_devices:
            return None

        # Scoring system for device priority
        def device_score(device: VRDevice) -> int:
            score = 0
            caps = device.capabilities

            # Base score for resolution
            score += caps.resolution_per_eye[0] * caps.resolution_per_eye[1] // 1000

            # Refresh rate bonus
            score += caps.max_refresh_rate

            # Feature bonuses
            if caps.has_hand_tracking:
                score += 50
            if caps.has_eye_tracking:
                score += 100
            if caps.has_passthrough:
                score += 75
            if caps.has_wireless:
                score += 25

            # FOV bonus
            score += int(caps.fov_horizontal)

            return score

        return max(connected_devices, key=device_score)


class HardwareDetector(VRHardwareDetector):
    """
    Extended VR hardware detector with change tracking.

    Extends VRHardwareDetector with additional functionality for monitoring
    hardware configuration changes over time.
    """

    def __init__(self):
        super().__init__()
        self._previous_state = None

    def has_hardware_changed(self) -> bool:
        """Check if hardware configuration has changed since last detection."""
        current_devices = [
            (d.device_type, d.serial_number, d.is_connected)
            for d in self._detected_devices
        ]

        if self._previous_state is None:
            self._previous_state = current_devices
            return True

        changed = self._previous_state != current_devices
        self._previous_state = current_devices
        return changed


# Global instances for easy access
vr_hardware_detector = VRHardwareDetector()
hardware_detector = HardwareDetector()
