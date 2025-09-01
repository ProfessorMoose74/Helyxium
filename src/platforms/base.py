"""
Base Platform Connector Class
Provides the foundation for all VR platform integrations.
"""

import logging
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from dataclasses import dataclass
from PyQt6.QtCore import QObject, pyqtSignal

from ..utils.logging import get_logger


class ConnectionStatus(Enum):
    """Platform connection status."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    AUTHENTICATING = "authenticating"
    AUTHENTICATED = "authenticated"
    ERROR = "error"
    RECONNECTING = "reconnecting"


class PlatformCapability(Enum):
    """Platform capabilities."""
    SOCIAL_FEATURES = "social_features"
    WORLD_DISCOVERY = "world_discovery"
    AVATAR_SYSTEM = "avatar_system"
    MESSAGING = "messaging"
    VOICE_CHAT = "voice_chat"
    CROSS_PLATFORM_FRIENDS = "cross_platform_friends"
    WORLD_UPLOAD = "world_upload"
    CONTENT_SHARING = "content_sharing"
    LIVE_STREAMING = "live_streaming"
    MARKETPLACE = "marketplace"


@dataclass
class PlatformUser:
    """Represents a user on a VR platform."""
    user_id: str
    username: str
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    is_online: bool = False
    status_message: Optional[str] = None
    platform: str = ""
    additional_info: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.additional_info is None:
            self.additional_info = {}


@dataclass
class PlatformWorld:
    """Represents a VR world on a platform."""
    world_id: str
    name: str
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None
    creator: Optional[PlatformUser] = None
    platform: str = ""
    is_public: bool = True
    max_users: int = 0
    current_users: int = 0
    tags: List[str] = None
    rating: Optional[float] = None
    additional_info: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.additional_info is None:
            self.additional_info = {}


@dataclass
class PlatformMessage:
    """Represents a message on a VR platform."""
    message_id: str
    sender: PlatformUser
    content: str
    timestamp: float
    message_type: str = "text"  # text, image, voice, system
    channel_id: Optional[str] = None
    is_private: bool = False
    additional_info: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.additional_info is None:
            self.additional_info = {}


class BasePlatformConnector(QObject, ABC):
    """
    Abstract base class for all VR platform connectors.
    
    Provides common functionality and interface for platform integrations.
    """
    
    # Signals
    connection_status_changed = pyqtSignal(str, str)  # platform_name, status
    user_status_changed = pyqtSignal(str, dict)  # platform_name, user_info
    message_received = pyqtSignal(str, dict)  # platform_name, message_info
    world_discovered = pyqtSignal(str, dict)  # platform_name, world_info
    friends_updated = pyqtSignal(str, list)  # platform_name, friends_list
    error_occurred = pyqtSignal(str, str, str)  # platform_name, error_type, error_message
    
    def __init__(self, platform_name: str):
        super().__init__()
        
        self.platform_name = platform_name
        self.logger = get_logger(f"platform.{platform_name}")
        
        # Connection state
        self._status = ConnectionStatus.DISCONNECTED
        self._last_error: Optional[str] = None
        self._connection_config: Dict[str, Any] = {}
        
        # Platform data
        self._current_user: Optional[PlatformUser] = None
        self._friends_list: List[PlatformUser] = []
        self._discovered_worlds: List[PlatformWorld] = []
        self._recent_messages: List[PlatformMessage] = []
        
        # Event callbacks
        self._event_callbacks: Dict[str, List[Callable]] = {}
        
        # Rate limiting
        self._rate_limit_config = {
            "max_requests_per_minute": 60,
            "max_messages_per_minute": 30,
            "request_interval": 1.0  # seconds
        }
        
        self.logger.info(f"Initialized {platform_name} platform connector")
    
    # Abstract methods that must be implemented by subclasses
    
    @abstractmethod
    async def connect(self, config: Dict[str, Any]) -> bool:
        """
        Connect to the VR platform.
        
        Args:
            config: Platform-specific connection configuration
            
        Returns:
            True if connection was successful
        """
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """
        Disconnect from the VR platform.
        
        Returns:
            True if disconnection was successful
        """
        pass
    
    @abstractmethod
    async def authenticate(self, credentials: Dict[str, Any]) -> bool:
        """
        Authenticate with the VR platform.
        
        Args:
            credentials: Platform-specific authentication credentials
            
        Returns:
            True if authentication was successful
        """
        pass
    
    @abstractmethod
    def get_supported_capabilities(self) -> List[PlatformCapability]:
        """
        Get list of capabilities supported by this platform.
        
        Returns:
            List of supported capabilities
        """
        pass
    
    @abstractmethod
    async def get_friends_list(self) -> List[PlatformUser]:
        """
        Get the user's friends list from the platform.
        
        Returns:
            List of friends
        """
        pass
    
    @abstractmethod
    async def send_message(self, recipient_id: str, content: str, message_type: str = "text") -> bool:
        """
        Send a message to another user.
        
        Args:
            recipient_id: ID of the message recipient
            content: Message content
            message_type: Type of message (text, image, etc.)
            
        Returns:
            True if message was sent successfully
        """
        pass
    
    @abstractmethod
    async def discover_worlds(self, search_query: Optional[str] = None, limit: int = 20) -> List[PlatformWorld]:
        """
        Discover VR worlds on the platform.
        
        Args:
            search_query: Optional search query to filter worlds
            limit: Maximum number of worlds to return
            
        Returns:
            List of discovered worlds
        """
        pass
    
    @abstractmethod
    async def join_world(self, world_id: str) -> bool:
        """
        Join a VR world.
        
        Args:
            world_id: ID of the world to join
            
        Returns:
            True if successfully joined the world
        """
        pass
    
    # Common implementation methods
    
    @property
    def status(self) -> ConnectionStatus:
        """Get current connection status."""
        return self._status
    
    @property
    def is_connected(self) -> bool:
        """Check if platform is connected."""
        return self._status in [ConnectionStatus.CONNECTED, ConnectionStatus.AUTHENTICATED]
    
    @property
    def is_authenticated(self) -> bool:
        """Check if platform is authenticated."""
        return self._status == ConnectionStatus.AUTHENTICATED
    
    @property
    def current_user(self) -> Optional[PlatformUser]:
        """Get current authenticated user."""
        return self._current_user
    
    @property
    def last_error(self) -> Optional[str]:
        """Get last error message."""
        return self._last_error
    
    def _set_status(self, status: ConnectionStatus, error_message: Optional[str] = None):
        """Set connection status and emit signal."""
        old_status = self._status
        self._status = status
        self._last_error = error_message
        
        if old_status != status:
            self.logger.info(f"Status changed: {old_status.value} -> {status.value}")
            self.connection_status_changed.emit(self.platform_name, status.value)
            
            if error_message:
                self.logger.error(f"Platform error: {error_message}")
                self.error_occurred.emit(self.platform_name, "connection", error_message)
    
    def _set_current_user(self, user: PlatformUser):
        """Set current authenticated user."""
        self._current_user = user
        self.user_status_changed.emit(self.platform_name, {
            "user_id": user.user_id,
            "username": user.username,
            "display_name": user.display_name,
            "is_online": user.is_online,
            "status_message": user.status_message
        })
    
    def _update_friends_list(self, friends: List[PlatformUser]):
        """Update friends list and emit signal."""
        self._friends_list = friends
        friends_data = [
            {
                "user_id": friend.user_id,
                "username": friend.username,
                "display_name": friend.display_name,
                "is_online": friend.is_online,
                "status_message": friend.status_message
            }
            for friend in friends
        ]
        self.friends_updated.emit(self.platform_name, friends_data)
    
    def _add_discovered_world(self, world: PlatformWorld):
        """Add a discovered world."""
        # Avoid duplicates
        if not any(w.world_id == world.world_id for w in self._discovered_worlds):
            self._discovered_worlds.append(world)
            
            world_data = {
                "world_id": world.world_id,
                "name": world.name,
                "description": world.description,
                "thumbnail_url": world.thumbnail_url,
                "creator": world.creator.username if world.creator else None,
                "is_public": world.is_public,
                "max_users": world.max_users,
                "current_users": world.current_users,
                "tags": world.tags,
                "rating": world.rating
            }
            self.world_discovered.emit(self.platform_name, world_data)
    
    def _add_message(self, message: PlatformMessage):
        """Add a received message."""
        self._recent_messages.append(message)
        
        # Keep only recent messages (last 100)
        if len(self._recent_messages) > 100:
            self._recent_messages = self._recent_messages[-100:]
        
        message_data = {
            "message_id": message.message_id,
            "sender": {
                "user_id": message.sender.user_id,
                "username": message.sender.username,
                "display_name": message.sender.display_name
            },
            "content": message.content,
            "timestamp": message.timestamp,
            "message_type": message.message_type,
            "channel_id": message.channel_id,
            "is_private": message.is_private
        }
        self.message_received.emit(self.platform_name, message_data)
    
    def register_event_callback(self, event_type: str, callback: Callable):
        """Register a callback for platform events."""
        if event_type not in self._event_callbacks:
            self._event_callbacks[event_type] = []
        self._event_callbacks[event_type].append(callback)
    
    def unregister_event_callback(self, event_type: str, callback: Callable):
        """Unregister a callback for platform events."""
        if event_type in self._event_callbacks:
            try:
                self._event_callbacks[event_type].remove(callback)
            except ValueError:
                pass
    
    def _emit_event(self, event_type: str, data: Any):
        """Emit an event to registered callbacks."""
        if event_type in self._event_callbacks:
            for callback in self._event_callbacks[event_type]:
                try:
                    callback(self.platform_name, event_type, data)
                except Exception as e:
                    self.logger.error(f"Error in event callback: {e}")
    
    def get_platform_info(self) -> Dict[str, Any]:
        """Get platform information and status."""
        return {
            "platform_name": self.platform_name,
            "status": self._status.value,
            "is_connected": self.is_connected,
            "is_authenticated": self.is_authenticated,
            "supported_capabilities": [cap.value for cap in self.get_supported_capabilities()],
            "current_user": {
                "user_id": self._current_user.user_id,
                "username": self._current_user.username,
                "display_name": self._current_user.display_name
            } if self._current_user else None,
            "friends_count": len(self._friends_list),
            "discovered_worlds_count": len(self._discovered_worlds),
            "recent_messages_count": len(self._recent_messages),
            "last_error": self._last_error
        }
    
    def get_connection_config(self) -> Dict[str, Any]:
        """Get connection configuration (without sensitive data)."""
        safe_config = self._connection_config.copy()
        
        # Remove sensitive fields
        sensitive_fields = ["password", "token", "secret", "key", "auth", "credential"]
        for field in list(safe_config.keys()):
            if any(sensitive in field.lower() for sensitive in sensitive_fields):
                safe_config[field] = "***HIDDEN***"
        
        return safe_config
    
    async def health_check(self) -> bool:
        """Perform a health check on the platform connection."""
        try:
            if not self.is_connected:
                return False
            
            # Basic connectivity test - implement in subclasses
            return True
            
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False
    
    async def reconnect(self) -> bool:
        """Attempt to reconnect to the platform."""
        if self._status == ConnectionStatus.RECONNECTING:
            return False
        
        self._set_status(ConnectionStatus.RECONNECTING)
        
        try:
            await self.disconnect()
            await asyncio.sleep(2)  # Brief delay before reconnecting
            return await self.connect(self._connection_config)
            
        except Exception as e:
            self._set_status(ConnectionStatus.ERROR, f"Reconnection failed: {e}")
            return False
    
    def cleanup(self):
        """Cleanup resources when connector is destroyed."""
        self.logger.info(f"Cleaning up {self.platform_name} platform connector")
        self._event_callbacks.clear()
        self._friends_list.clear()
        self._discovered_worlds.clear()
        self._recent_messages.clear()