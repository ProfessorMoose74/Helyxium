"""
Logging Configuration
Centralized logging setup for Helyxium application.
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional
import platform
from datetime import datetime


def get_log_directory() -> Path:
    """Get the appropriate log directory for the current platform."""
    system = platform.system().lower()
    
    if system == "windows":
        log_dir = Path.home() / "AppData" / "Roaming" / "Helyxium" / "logs"
    elif system == "darwin":  # macOS
        log_dir = Path.home() / "Library" / "Logs" / "Helyxium"
    else:  # Linux and others
        log_dir = Path.home() / ".local" / "share" / "helyxium" / "logs"
    
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def setup_logging(
    level: int = logging.INFO,
    console_output: bool = True,
    file_output: bool = True,
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    Setup centralized logging for the Helyxium application.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        console_output: Whether to output logs to console
        file_output: Whether to output logs to file
        log_file: Custom log file path (optional)
    
    Returns:
        Configured root logger
    """
    
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Clear any existing handlers
    root_logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # File handler
    if file_output:
        log_dir = get_log_directory()
        
        if log_file is None:
            timestamp = datetime.now().strftime("%Y%m%d")
            log_file = log_dir / f"helyxium_{timestamp}.log"
        else:
            log_file = Path(log_file)
        
        # Use rotating file handler to manage log file sizes
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Log startup information
    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info("Helyxium Application Starting")
    logger.info(f"Platform: {platform.system()} {platform.release()}")
    logger.info(f"Python: {sys.version}")
    logger.info(f"Log Level: {logging.getLevelName(level)}")
    
    if file_output:
        logger.info(f"Log File: {log_file}")
    
    logger.info("=" * 60)
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a specific module."""
    return logging.getLogger(name)


def set_log_level(level: int):
    """Change the logging level for all handlers."""
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    for handler in root_logger.handlers:
        handler.setLevel(level)
    
    logger = get_logger(__name__)
    logger.info(f"Log level changed to: {logging.getLevelName(level)}")


def log_exception(logger: logging.Logger, message: str = "An exception occurred"):
    """Log an exception with traceback information."""
    logger.exception(message)


def log_vr_event(logger: logging.Logger, event_type: str, details: dict):
    """Log VR-specific events with structured information."""
    logger.info(f"VR Event: {event_type} | {details}")


def log_platform_event(logger: logging.Logger, platform: str, event: str, details: dict):
    """Log platform-specific events."""
    logger.info(f"Platform Event: {platform} | {event} | {details}")


def log_security_event(logger: logging.Logger, event_type: str, user_id: str, details: dict):
    """Log security-related events for audit purposes."""
    logger.warning(f"Security Event: {event_type} | User: {user_id} | {details}")


def log_performance_metric(logger: logging.Logger, metric_name: str, value: float, unit: str = "ms"):
    """Log performance metrics."""
    logger.debug(f"Performance: {metric_name} = {value}{unit}")


class VRLogger:
    """Specialized logger for VR operations."""
    
    def __init__(self, name: str):
        self.logger = get_logger(f"vr.{name}")
    
    def hardware_detected(self, hardware_info: dict):
        """Log VR hardware detection."""
        self.logger.info(f"VR Hardware Detected: {hardware_info}")
    
    def platform_connected(self, platform: str, status: str):
        """Log platform connection status."""
        self.logger.info(f"Platform Connection: {platform} - {status}")
    
    def avatar_translation(self, source_platform: str, target_platform: str, success: bool):
        """Log avatar translation attempts."""
        status = "SUCCESS" if success else "FAILED"
        self.logger.info(f"Avatar Translation: {source_platform} -> {target_platform} - {status}")
    
    def cross_platform_message(self, from_platform: str, to_platform: str, latency_ms: float):
        """Log cross-platform message delivery."""
        self.logger.debug(f"Cross-Platform Message: {from_platform} -> {to_platform} ({latency_ms}ms)")


class SecurityLogger:
    """Specialized logger for security events."""
    
    def __init__(self):
        self.logger = get_logger("security")
    
    def authentication_attempt(self, user_id: str, method: str, success: bool, ip_address: str = "unknown"):
        """Log authentication attempts."""
        status = "SUCCESS" if success else "FAILED"
        self.logger.warning(f"Auth Attempt: {user_id} | {method} | {status} | IP: {ip_address}")
    
    def coppa_verification(self, age: int, parental_consent: bool):
        """Log COPPA-related verification events."""
        self.logger.info(f"COPPA Verification: Age={age}, Consent={parental_consent}")
    
    def data_access_request(self, user_id: str, data_type: str, platform: str):
        """Log data access requests for privacy compliance."""
        self.logger.info(f"Data Access: {user_id} | {data_type} | Platform: {platform}")


# Global logger instances for convenience
vr_logger = VRLogger("main")
security_logger = SecurityLogger()