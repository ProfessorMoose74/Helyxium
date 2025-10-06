"""
COPPA Compliance Manager
Implements COPPA-compliant features for users under 13.
"""

import json
import time
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..utils.logging import SecurityLogger, get_logger


class ParentalConsentMethod(Enum):
    """Methods of obtaining parental consent."""

    EMAIL_VERIFICATION = "email_verification"
    CREDIT_CARD_VERIFICATION = "credit_card_verification"
    DIGITAL_SIGNATURE = "digital_signature"
    PHONE_VERIFICATION = "phone_verification"
    POSTAL_MAIL = "postal_mail"


class DataCollectionType(Enum):
    """Types of data that may be collected."""

    NECESSARY_OPERATION = "necessary_operation"  # Required for app function
    ENHANCED_FEATURES = "enhanced_features"  # Optional features
    ANALYTICS = "analytics"  # Usage analytics
    MARKETING = "marketing"  # Marketing data
    SOCIAL_FEATURES = "social_features"  # Social interaction data


@dataclass
class ParentalConsent:
    """Parental consent record."""

    child_user_id: str
    parent_email: str
    parent_name: str
    consent_method: str
    consent_granted: bool
    consent_timestamp: float
    consent_data: Dict[str, Any]
    verification_token: Optional[str] = None
    is_verified: bool = False
    expires_at: Optional[float] = None

    def __post_init__(self):
        if self.consent_data is None:
            self.consent_data = {}


@dataclass
class ChildProfile:
    """Child user profile with COPPA protections."""

    user_id: str
    age: int
    parent_consent: Optional[ParentalConsent] = None
    allowed_data_collection: List[str] = None
    session_time_limits: Dict[str, int] = None  # minutes per day/week
    content_filters: List[str] = None
    social_restrictions: Dict[str, bool] = None
    last_activity: Optional[float] = None
    total_session_time_today: int = 0  # minutes
    break_reminders_enabled: bool = True

    def __post_init__(self):
        if self.allowed_data_collection is None:
            self.allowed_data_collection = [
                DataCollectionType.NECESSARY_OPERATION.value
            ]

        if self.session_time_limits is None:
            self.session_time_limits = {
                "daily_limit": 60,  # 1 hour default
                "session_limit": 30,  # 30 minutes per session
                "break_interval": 15,  # 15 minute break every 30 minutes
            }

        if self.content_filters is None:
            self.content_filters = ["age_appropriate", "no_violence", "educational"]

        if self.social_restrictions is None:
            self.social_restrictions = {
                "can_chat": False,
                "can_voice_chat": False,
                "can_share_personal_info": False,
                "can_add_friends": False,
                "can_join_public_worlds": False,
            }


class COPPAManager:
    """Manages COPPA compliance features."""

    def __init__(self, config_manager=None):
        self.logger = get_logger(__name__)
        self.security_logger = SecurityLogger()
        self.config_manager = config_manager

        # Child profiles storage
        self._child_profiles: Dict[str, ChildProfile] = {}
        self._consent_records: Dict[str, ParentalConsent] = {}

        # Load existing data
        self._load_coppa_data()

        self.logger.info("COPPA manager initialized")

    def _get_coppa_file_path(self, filename: str) -> Path:
        """Get path for COPPA-related files."""
        if self.config_manager:
            base_dir = self.config_manager.config_file_path.parent
        else:
            base_dir = Path.home() / ".helyxium"

        coppa_dir = base_dir / "coppa"
        coppa_dir.mkdir(parents=True, exist_ok=True)
        return coppa_dir / filename

    def _load_coppa_data(self):
        """Load COPPA data from storage."""
        try:
            # Load child profiles
            profiles_file = self._get_coppa_file_path("child_profiles.json")
            if profiles_file.exists():
                with open(profiles_file, "r", encoding="utf-8") as f:
                    profiles_data = json.load(f)

                for user_id, profile_data in profiles_data.items():
                    # Convert consent data if present
                    if profile_data.get("parent_consent"):
                        consent_data = profile_data["parent_consent"]
                        profile_data["parent_consent"] = ParentalConsent(**consent_data)

                    self._child_profiles[user_id] = ChildProfile(**profile_data)

            # Load consent records
            consent_file = self._get_coppa_file_path("consent_records.json")
            if consent_file.exists():
                with open(consent_file, "r", encoding="utf-8") as f:
                    consent_data = json.load(f)

                for record_id, record_data in consent_data.items():
                    self._consent_records[record_id] = ParentalConsent(**record_data)

        except Exception as e:
            self.logger.error(f"Failed to load COPPA data: {e}")

    def _save_coppa_data(self):
        """Save COPPA data to storage."""
        try:
            # Save child profiles
            profiles_data = {}
            for user_id, profile in self._child_profiles.items():
                profile_dict = asdict(profile)
                # Convert ParentalConsent to dict if present
                if profile_dict.get("parent_consent"):
                    profile_dict["parent_consent"] = asdict(profile.parent_consent)
                profiles_data[user_id] = profile_dict

            profiles_file = self._get_coppa_file_path("child_profiles.json")
            with open(profiles_file, "w", encoding="utf-8") as f:
                json.dump(profiles_data, f, indent=2)

            # Save consent records
            consent_data = {
                record_id: asdict(record)
                for record_id, record in self._consent_records.items()
            }

            consent_file = self._get_coppa_file_path("consent_records.json")
            with open(consent_file, "w", encoding="utf-8") as f:
                json.dump(consent_data, f, indent=2)

        except Exception as e:
            self.logger.error(f"Failed to save COPPA data: {e}")

    def create_child_profile(self, user_id: str, age: int) -> bool:
        """
        Create a child profile with COPPA protections.

        Args:
            user_id: User ID
            age: Child's age

        Returns:
            True if profile created successfully
        """
        try:
            if age >= 13:
                self.logger.warning(
                    f"Attempted to create child profile for user >= 13: {age}"
                )
                return False

            child_profile = ChildProfile(user_id=user_id, age=age)

            self._child_profiles[user_id] = child_profile
            self._save_coppa_data()

            self.logger.info(f"Child profile created for user {user_id}, age {age}")
            self.security_logger.coppa_verification(age, False)

            return True

        except Exception as e:
            self.logger.error(f"Failed to create child profile: {e}")
            return False

    def request_parental_consent(
        self,
        user_id: str,
        parent_email: str,
        parent_name: str,
        method: ParentalConsentMethod,
    ) -> Optional[str]:
        """
        Request parental consent for a child user.

        Args:
            user_id: Child user ID
            parent_email: Parent's email address
            parent_name: Parent's name
            method: Consent verification method

        Returns:
            Verification token if request was created successfully
        """
        try:
            child_profile = self._child_profiles.get(user_id)
            if not child_profile:
                self.logger.error(f"Child profile not found: {user_id}")
                return None

            # Generate verification token
            import secrets

            verification_token = secrets.token_urlsafe(32)

            consent = ParentalConsent(
                child_user_id=user_id,
                parent_email=parent_email,
                parent_name=parent_name,
                consent_method=method.value,
                consent_granted=False,
                consent_timestamp=time.time(),
                consent_data={"method": method.value, "requested_at": time.time()},
                verification_token=verification_token,
                expires_at=time.time() + (7 * 24 * 60 * 60),  # 7 days
            )

            self._consent_records[verification_token] = consent
            child_profile.parent_consent = consent

            self._save_coppa_data()

            self.logger.info(f"Parental consent requested for {user_id}")

            # In a real implementation, you would send email/SMS/etc here
            self._send_consent_request(consent)

            return verification_token

        except Exception as e:
            self.logger.error(f"Failed to request parental consent: {e}")
            return None

    def verify_parental_consent(
        self, verification_token: str, consent_data: Dict[str, Any]
    ) -> bool:
        """
        Verify parental consent using the provided token and data.

        Args:
            verification_token: Verification token from consent request
            consent_data: Additional verification data

        Returns:
            True if consent was verified successfully
        """
        try:
            consent = self._consent_records.get(verification_token)
            if not consent:
                self.logger.warning(f"Invalid verification token: {verification_token}")
                return False

            # Check if token is expired
            if consent.expires_at and time.time() > consent.expires_at:
                self.logger.warning(f"Verification token expired: {verification_token}")
                return False

            # Verify consent data based on method
            if not self._verify_consent_method(consent, consent_data):
                return False

            # Mark consent as granted and verified
            consent.consent_granted = True
            consent.is_verified = True
            consent.consent_data.update(consent_data)
            consent.consent_timestamp = time.time()

            # Update child profile
            child_profile = self._child_profiles.get(consent.child_user_id)
            if child_profile:
                child_profile.parent_consent = consent

                # Enable additional features with parental consent
                child_profile.allowed_data_collection.append(
                    DataCollectionType.ENHANCED_FEATURES.value
                )

                # Relax some social restrictions with consent
                child_profile.social_restrictions.update(
                    {"can_chat": True, "can_add_friends": True}
                )

            self._save_coppa_data()

            self.logger.info(f"Parental consent verified for {consent.child_user_id}")
            self.security_logger.coppa_verification(
                child_profile.age if child_profile else 0, True
            )

            return True

        except Exception as e:
            self.logger.error(f"Failed to verify parental consent: {e}")
            return False

    def is_data_collection_allowed(
        self, user_id: str, data_type: DataCollectionType
    ) -> bool:
        """
        Check if data collection is allowed for a child user.

        Args:
            user_id: Child user ID
            data_type: Type of data to collect

        Returns:
            True if data collection is allowed
        """
        child_profile = self._child_profiles.get(user_id)
        if not child_profile:
            return True  # Not a child user

        return data_type.value in child_profile.allowed_data_collection

    def check_session_limits(self, user_id: str) -> Dict[str, Any]:
        """
        Check session time limits for a child user.

        Args:
            user_id: Child user ID

        Returns:
            Dictionary with session limit information
        """
        child_profile = self._child_profiles.get(user_id)
        if not child_profile:
            return {"is_child": False}

        current_time = time.time()

        # Check daily limit
        daily_limit = child_profile.session_time_limits.get("daily_limit", 60)
        session_limit = child_profile.session_time_limits.get("session_limit", 30)

        # Reset daily counter if it's a new day
        if child_profile.last_activity:
            last_day = time.gmtime(child_profile.last_activity).tm_yday
            current_day = time.gmtime(current_time).tm_yday
            if last_day != current_day:
                child_profile.total_session_time_today = 0

        remaining_daily = daily_limit - child_profile.total_session_time_today

        return {
            "is_child": True,
            "daily_limit": daily_limit,
            "session_limit": session_limit,
            "time_used_today": child_profile.total_session_time_today,
            "remaining_daily": max(0, remaining_daily),
            "can_start_session": remaining_daily > 0,
            "break_reminders_enabled": child_profile.break_reminders_enabled,
        }

    def record_session_time(self, user_id: str, minutes: int):
        """
        Record session time for a child user.

        Args:
            user_id: Child user ID
            minutes: Minutes to add to session time
        """
        child_profile = self._child_profiles.get(user_id)
        if not child_profile:
            return

        child_profile.total_session_time_today += minutes
        child_profile.last_activity = time.time()

        self._save_coppa_data()

    def get_content_filters(self, user_id: str) -> List[str]:
        """
        Get content filters for a child user.

        Args:
            user_id: Child user ID

        Returns:
            List of active content filters
        """
        child_profile = self._child_profiles.get(user_id)
        if not child_profile:
            return []

        return child_profile.content_filters.copy()

    def get_social_restrictions(self, user_id: str) -> Dict[str, bool]:
        """
        Get social restrictions for a child user.

        Args:
            user_id: Child user ID

        Returns:
            Dictionary of social restrictions
        """
        child_profile = self._child_profiles.get(user_id)
        if not child_profile:
            return {}

        return child_profile.social_restrictions.copy()

    def update_parental_settings(self, user_id: str, settings: Dict[str, Any]) -> bool:
        """
        Update parental control settings for a child user.

        Args:
            user_id: Child user ID
            settings: New settings to apply

        Returns:
            True if settings were updated successfully
        """
        try:
            child_profile = self._child_profiles.get(user_id)
            if not child_profile:
                return False

            # Update allowed settings
            if "session_time_limits" in settings:
                child_profile.session_time_limits.update(
                    settings["session_time_limits"]
                )

            if "content_filters" in settings:
                child_profile.content_filters = settings["content_filters"]

            if "social_restrictions" in settings:
                child_profile.social_restrictions.update(
                    settings["social_restrictions"]
                )

            if "break_reminders_enabled" in settings:
                child_profile.break_reminders_enabled = settings[
                    "break_reminders_enabled"
                ]

            self._save_coppa_data()

            self.logger.info(f"Parental settings updated for {user_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to update parental settings: {e}")
            return False

    def _verify_consent_method(
        self, consent: ParentalConsent, consent_data: Dict[str, Any]
    ) -> bool:
        """Verify consent based on the chosen method."""
        method = ParentalConsentMethod(consent.consent_method)

        if method == ParentalConsentMethod.EMAIL_VERIFICATION:
            # Verify email confirmation
            return consent_data.get("email_confirmed") is True

        elif method == ParentalConsentMethod.CREDIT_CARD_VERIFICATION:
            # Verify small charge verification
            return consent_data.get("charge_verified") is True

        elif method == ParentalConsentMethod.DIGITAL_SIGNATURE:
            # Verify digital signature
            return consent_data.get("signature_verified") is True

        elif method == ParentalConsentMethod.PHONE_VERIFICATION:
            # Verify phone confirmation
            return consent_data.get("phone_verified") is True

        elif method == ParentalConsentMethod.POSTAL_MAIL:
            # Verify postal confirmation
            return consent_data.get("postal_verified") is True

        return False

    def _send_consent_request(self, consent: ParentalConsent):
        """Send consent request to parent (placeholder implementation)."""
        # In a real implementation, this would send email/SMS/etc
        self.logger.info(
            f"Consent request sent to {consent.parent_email} "
            f"for {consent.child_user_id}"
        )

    def is_child_user(self, user_id: str) -> bool:
        """Check if user is a child (under 13) with COPPA protections."""
        return user_id in self._child_profiles

    def get_child_profile(self, user_id: str) -> Optional[ChildProfile]:
        """Get child profile for a user."""
        return self._child_profiles.get(user_id)

    def cleanup_expired_consents(self):
        """Clean up expired consent requests."""
        current_time = time.time()
        expired_tokens = [
            token
            for token, consent in self._consent_records.items()
            if consent.expires_at
            and current_time > consent.expires_at
            and not consent.is_verified
        ]

        for token in expired_tokens:
            del self._consent_records[token]

        if expired_tokens:
            self._save_coppa_data()
            self.logger.info(
                f"Cleaned up {len(expired_tokens)} expired consent requests"
            )


# Global instance
coppa_manager = COPPAManager()
