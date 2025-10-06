"""
Authentication Manager
Handles multi-factor authentication, biometric authentication,
and secure session management.
"""

import base64
import hashlib
import json
import os
import secrets
import time
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from ..utils.logging import SecurityLogger, get_logger


class AuthenticationMethod(Enum):
    """Available authentication methods."""

    PASSWORD = "password"
    BIOMETRIC_FINGERPRINT = "biometric_fingerprint"
    BIOMETRIC_FACE = "biometric_face"
    HARDWARE_TOKEN = "hardware_token"
    SMS_CODE = "sms_code"
    EMAIL_CODE = "email_code"
    TOTP = "totp"


class AuthenticationResult(Enum):
    """Authentication attempt results."""

    SUCCESS = "success"
    FAILED = "failed"
    REQUIRES_MFA = "requires_mfa"
    ACCOUNT_LOCKED = "account_locked"
    EXPIRED = "expired"
    INVALID_METHOD = "invalid_method"


@dataclass
class UserProfile:
    """User profile information."""

    user_id: str
    username: str
    email: str
    display_name: str
    age: Optional[int] = None
    is_minor: bool = False
    requires_parental_consent: bool = False
    enabled_auth_methods: List[str] = None
    last_login: Optional[float] = None
    failed_attempts: int = 0
    account_locked_until: Optional[float] = None
    preferences: Dict[str, Any] = None
    coppa_verified: bool = False
    created_at: float = None

    def __post_init__(self):
        if self.enabled_auth_methods is None:
            self.enabled_auth_methods = [AuthenticationMethod.PASSWORD.value]
        if self.preferences is None:
            self.preferences = {}
        if self.created_at is None:
            self.created_at = time.time()

        # Auto-determine minor status and COPPA requirements
        if self.age is not None:
            self.is_minor = self.age < 18
            self.requires_parental_consent = self.age < 13


@dataclass
class AuthenticationSession:
    """Active authentication session."""

    session_id: str
    user_id: str
    created_at: float
    expires_at: float
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    auth_methods_used: List[str] = None
    is_active: bool = True
    last_activity: float = None

    def __post_init__(self):
        if self.auth_methods_used is None:
            self.auth_methods_used = []
        if self.last_activity is None:
            self.last_activity = self.created_at

    def is_expired(self) -> bool:
        """Check if session has expired."""
        return time.time() > self.expires_at

    def update_activity(self):
        """Update last activity timestamp."""
        self.last_activity = time.time()


class AuthenticationManager:
    """Manages user authentication, sessions, and security features."""

    def __init__(self, config_manager=None):
        self.logger = get_logger(__name__)
        self.security_logger = SecurityLogger()
        self.config_manager = config_manager

        # Security configuration
        self.max_failed_attempts = 5
        self.lockout_duration = 300  # 5 minutes
        self.session_timeout = 1800  # 30 minutes
        self.require_mfa_for_sensitive = True

        # Storage
        self._users: Dict[str, UserProfile] = {}
        self._sessions: Dict[str, AuthenticationSession] = {}
        self._password_hashes: Dict[str, str] = {}
        self._mfa_secrets: Dict[str, Dict[str, str]] = {}

        # Encryption key for sensitive data
        self._encryption_key = self._get_or_create_encryption_key()
        self._cipher = Fernet(self._encryption_key)

        # Load existing data
        self._load_user_data()

        self.logger.info("Authentication manager initialized")

    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key for sensitive data."""
        key_file = self._get_security_file_path("encryption.key")

        if key_file.exists():
            try:
                with open(key_file, "rb") as f:
                    return f.read()
            except Exception as e:
                self.logger.warning(f"Failed to load encryption key: {e}")

        # Generate new key
        key = Fernet.generate_key()

        try:
            key_file.parent.mkdir(parents=True, exist_ok=True)
            with open(key_file, "wb") as f:
                f.write(key)

            # Set restrictive permissions
            if hasattr(os, "chmod"):
                os.chmod(key_file, 0o600)

        except Exception as e:
            self.logger.error(f"Failed to save encryption key: {e}")

        return key

    def _get_security_file_path(self, filename: str) -> Path:
        """Get path for security-related files."""
        if self.config_manager:
            base_dir = self.config_manager.config_file_path.parent
        else:
            base_dir = Path.home() / ".helyxium"

        security_dir = base_dir / "security"
        security_dir.mkdir(parents=True, exist_ok=True)
        return security_dir / filename

    def _load_user_data(self):
        """Load user data from secure storage."""
        try:
            users_file = self._get_security_file_path("users.json")
            passwords_file = self._get_security_file_path("passwords.dat")

            # Load user profiles
            if users_file.exists():
                with open(users_file, "r", encoding="utf-8") as f:
                    users_data = json.load(f)

                for user_id, user_data in users_data.items():
                    self._users[user_id] = UserProfile(**user_data)

            # Load encrypted password hashes
            if passwords_file.exists():
                with open(passwords_file, "rb") as f:
                    encrypted_data = f.read()

                decrypted_data = self._cipher.decrypt(encrypted_data)
                self._password_hashes = json.loads(decrypted_data.decode("utf-8"))

        except Exception as e:
            self.logger.error(f"Failed to load user data: {e}")

    def _save_user_data(self):
        """Save user data to secure storage."""
        try:
            users_file = self._get_security_file_path("users.json")
            passwords_file = self._get_security_file_path("passwords.dat")

            # Save user profiles (non-sensitive data)
            users_data = {
                user_id: asdict(user) for user_id, user in self._users.items()
            }

            with open(users_file, "w", encoding="utf-8") as f:
                json.dump(users_data, f, indent=2)

            # Save encrypted password hashes
            passwords_json = json.dumps(self._password_hashes)
            encrypted_data = self._cipher.encrypt(passwords_json.encode("utf-8"))

            with open(passwords_file, "wb") as f:
                f.write(encrypted_data)

            # Set restrictive permissions
            if hasattr(os, "chmod"):
                os.chmod(users_file, 0o600)
                os.chmod(passwords_file, 0o600)

        except Exception as e:
            self.logger.error(f"Failed to save user data: {e}")

    def create_user(
        self,
        username: str,
        email: str,
        password: str,
        display_name: str,
        age: Optional[int] = None,
    ) -> tuple[bool, str]:
        """
        Create a new user account.

        Args:
            username: Unique username
            email: User email address
            password: User password
            display_name: Display name
            age: User age (for COPPA compliance)

        Returns:
            (success, message) tuple
        """
        try:
            # Validation
            if not username or not email or not password:
                return False, "All fields are required"

            # Check if user already exists
            user_id = self._generate_user_id(username, email)
            if user_id in self._users:
                return False, "User already exists"

            if any(u.username == username for u in self._users.values()):
                return False, "Username already taken"

            if any(u.email == email for u in self._users.values()):
                return False, "Email already registered"

            # Password strength validation
            if not self._validate_password_strength(password):
                return False, "Password does not meet security requirements"

            # Create user profile
            user_profile = UserProfile(
                user_id=user_id,
                username=username,
                email=email,
                display_name=display_name,
                age=age,
            )

            # COPPA compliance check
            if user_profile.requires_parental_consent:
                self.security_logger.coppa_verification(age or 0, False)
                return False, "Parental consent required for users under 13"

            # Hash password
            password_hash = self._hash_password(password)

            # Store user data
            self._users[user_id] = user_profile
            self._password_hashes[user_id] = password_hash

            # Save to storage
            self._save_user_data()

            self.logger.info(f"User created: {username}")
            self.security_logger.authentication_attempt(user_id, "registration", True)

            return True, "User created successfully"

        except Exception as e:
            self.logger.error(f"Failed to create user: {e}")
            return False, f"Failed to create user: {str(e)}"

    def authenticate(
        self,
        username: str,
        password: str,
        method: AuthenticationMethod = AuthenticationMethod.PASSWORD,
        additional_data: Optional[Dict[str, Any]] = None,
    ) -> tuple[AuthenticationResult, Optional[str]]:
        """
        Authenticate a user.

        Args:
            username: Username or email
            password: Password or authentication data
            method: Authentication method
            additional_data: Additional authentication data

        Returns:
            (result, session_id) tuple
        """
        try:
            # Find user
            user = self._find_user_by_username_or_email(username)
            if not user:
                self.security_logger.authentication_attempt(
                    username, method.value, False
                )
                return AuthenticationResult.FAILED, None

            # Check if account is locked
            if self._is_account_locked(user):
                self.security_logger.authentication_attempt(
                    user.user_id, method.value, False
                )
                return AuthenticationResult.ACCOUNT_LOCKED, None

            # Authenticate based on method
            auth_success = False

            if method == AuthenticationMethod.PASSWORD:
                auth_success = self._verify_password(user.user_id, password)
            elif method == AuthenticationMethod.BIOMETRIC_FINGERPRINT:
                auth_success = self._verify_biometric(
                    user.user_id, "fingerprint", password
                )
            elif method == AuthenticationMethod.BIOMETRIC_FACE:
                auth_success = self._verify_biometric(user.user_id, "face", password)
            # Add other authentication methods as needed

            if not auth_success:
                self._record_failed_attempt(user)
                self.security_logger.authentication_attempt(
                    user.user_id, method.value, False
                )
                return AuthenticationResult.FAILED, None

            # Check if MFA is required
            if self._requires_mfa(user, method):
                self.security_logger.authentication_attempt(
                    user.user_id, method.value, True
                )
                return AuthenticationResult.REQUIRES_MFA, None

            # Create session
            session = self._create_session(user, [method.value])

            # Update user info
            user.last_login = time.time()
            user.failed_attempts = 0
            user.account_locked_until = None

            self._save_user_data()

            self.logger.info(f"User authenticated: {user.username}")
            self.security_logger.authentication_attempt(
                user.user_id, method.value, True
            )

            return AuthenticationResult.SUCCESS, session.session_id

        except Exception as e:
            self.logger.error(f"Authentication failed: {e}")
            return AuthenticationResult.FAILED, None

    def create_session(self, user_id: str, auth_methods: List[str]) -> Optional[str]:
        """Create a new authentication session."""
        try:
            user = self._users.get(user_id)
            if not user:
                return None

            session = self._create_session(user, auth_methods)
            return session.session_id

        except Exception as e:
            self.logger.error(f"Failed to create session: {e}")
            return None

    def validate_session(self, session_id: str) -> Optional[UserProfile]:
        """Validate a session and return user profile if valid."""
        try:
            session = self._sessions.get(session_id)
            if not session:
                return None

            if session.is_expired() or not session.is_active:
                self._invalidate_session(session_id)
                return None

            # Update activity
            session.update_activity()

            return self._users.get(session.user_id)

        except Exception as e:
            self.logger.error(f"Session validation failed: {e}")
            return None

    def logout(self, session_id: str) -> bool:
        """Logout and invalidate session."""
        return self._invalidate_session(session_id)

    def change_password(
        self, user_id: str, old_password: str, new_password: str
    ) -> bool:
        """Change user password."""
        try:
            if not self._verify_password(user_id, old_password):
                return False

            if not self._validate_password_strength(new_password):
                return False

            new_hash = self._hash_password(new_password)
            self._password_hashes[user_id] = new_hash

            self._save_user_data()

            self.logger.info(f"Password changed for user: {user_id}")
            self.security_logger.data_access_request(
                user_id, "password_change", "local"
            )

            return True

        except Exception as e:
            self.logger.error(f"Password change failed: {e}")
            return False

    def enable_mfa(self, user_id: str, method: AuthenticationMethod) -> bool:
        """Enable multi-factor authentication for a user."""
        try:
            user = self._users.get(user_id)
            if not user:
                return False

            if method.value not in user.enabled_auth_methods:
                user.enabled_auth_methods.append(method.value)
                self._save_user_data()

                self.logger.info(f"MFA enabled for user {user_id}: {method.value}")
                return True

            return True  # Already enabled

        except Exception as e:
            self.logger.error(f"Failed to enable MFA: {e}")
            return False

    def is_coppa_compliant(self, user_id: str) -> bool:
        """Check if user account is COPPA compliant."""
        user = self._users.get(user_id)
        if not user:
            return False

        if not user.requires_parental_consent:
            return True

        return user.coppa_verified

    def set_coppa_verification(
        self, user_id: str, verified: bool, parental_consent: bool = False
    ):
        """Set COPPA verification status."""
        user = self._users.get(user_id)
        if user and user.requires_parental_consent:
            user.coppa_verified = verified
            self._save_user_data()

            self.security_logger.coppa_verification(user.age or 0, parental_consent)
            self.logger.info(f"COPPA verification set for user {user_id}: {verified}")

    # Helper methods

    def _generate_user_id(self, username: str, email: str) -> str:
        """Generate a unique user ID."""
        combined = f"{username.lower()}:{email.lower()}:{time.time()}"
        return hashlib.sha256(combined.encode()).hexdigest()[:16]

    def _hash_password(self, password: str) -> str:
        """Hash a password with salt."""
        salt = secrets.token_bytes(32)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return base64.urlsafe_b64encode(salt).decode() + ":" + key.decode()

    def _verify_password(self, user_id: str, password: str) -> bool:
        """Verify a password against stored hash."""
        try:
            stored_hash = self._password_hashes.get(user_id)
            if not stored_hash:
                return False

            salt_b64, key_b64 = stored_hash.split(":")
            salt = base64.urlsafe_b64decode(salt_b64)
            stored_key = base64.urlsafe_b64decode(key_b64)

            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )

            new_key = kdf.derive(password.encode())
            return new_key == stored_key

        except Exception:
            return False

    def _validate_password_strength(self, password: str) -> bool:
        """Validate password strength."""
        if len(password) < 8:
            return False

        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)

        return sum([has_upper, has_lower, has_digit, has_special]) >= 3

    def _find_user_by_username_or_email(self, identifier: str) -> Optional[UserProfile]:
        """Find user by username or email."""
        identifier_lower = identifier.lower()

        for user in self._users.values():
            if (
                user.username.lower() == identifier_lower
                or user.email.lower() == identifier_lower
            ):
                return user

        return None

    def _is_account_locked(self, user: UserProfile) -> bool:
        """Check if account is locked due to failed attempts."""
        if user.account_locked_until is None:
            return False

        if time.time() < user.account_locked_until:
            return True

        # Unlock account
        user.account_locked_until = None
        user.failed_attempts = 0
        return False

    def _record_failed_attempt(self, user: UserProfile):
        """Record a failed authentication attempt."""
        user.failed_attempts += 1

        if user.failed_attempts >= self.max_failed_attempts:
            user.account_locked_until = time.time() + self.lockout_duration
            self.logger.warning(
                f"Account locked due to failed attempts: {user.username}"
            )

    def _requires_mfa(
        self, user: UserProfile, primary_method: AuthenticationMethod
    ) -> bool:
        """Check if multi-factor authentication is required."""
        if not self.require_mfa_for_sensitive:
            return False

        # Require MFA if user has multiple methods enabled
        return len(user.enabled_auth_methods) > 1

    def _verify_biometric(self, user_id: str, biometric_type: str, data: str) -> bool:
        """Verify biometric authentication (placeholder implementation)."""
        # This would integrate with actual biometric systems
        # For now, return False as biometric support is not implemented
        return False

    def _create_session(
        self, user: UserProfile, auth_methods: List[str]
    ) -> AuthenticationSession:
        """Create a new authentication session."""
        session_id = secrets.token_urlsafe(32)
        current_time = time.time()

        session = AuthenticationSession(
            session_id=session_id,
            user_id=user.user_id,
            created_at=current_time,
            expires_at=current_time + self.session_timeout,
            auth_methods_used=auth_methods,
        )

        self._sessions[session_id] = session

        # Clean up expired sessions
        self._cleanup_expired_sessions()

        return session

    def _invalidate_session(self, session_id: str) -> bool:
        """Invalidate a session."""
        session = self._sessions.get(session_id)
        if session:
            session.is_active = False
            del self._sessions[session_id]
            return True
        return False

    def _cleanup_expired_sessions(self):
        """Remove expired sessions."""
        expired_sessions = [
            session_id
            for session_id, session in self._sessions.items()
            if session.is_expired() or not session.is_active
        ]

        for session_id in expired_sessions:
            del self._sessions[session_id]

    def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """Get user profile by ID."""
        return self._users.get(user_id)

    def get_active_sessions_count(self, user_id: str) -> int:
        """Get number of active sessions for a user."""
        return sum(
            1
            for session in self._sessions.values()
            if session.user_id == user_id
            and session.is_active
            and not session.is_expired()
        )
