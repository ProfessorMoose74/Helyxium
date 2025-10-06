"""
End-to-End Encryption System
Provides secure encryption for cross-platform communications and data storage.
"""

import base64
import json
import os
import secrets
from typing import Optional, Tuple

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from ..utils.logging import get_logger


class EncryptionManager:
    """Manages encryption keys and provides encryption/decryption services."""

    def __init__(self):
        self.logger = get_logger(__name__)

        # Symmetric encryption for local data
        self._local_key: Optional[bytes] = None
        self._local_cipher: Optional[Fernet] = None

        # Asymmetric encryption for cross-platform communication
        self._private_key: Optional[rsa.RSAPrivateKey] = None
        self._public_key: Optional[rsa.RSAPublicKey] = None

        # Initialize encryption
        self._initialize_encryption()

    def _initialize_encryption(self):
        """Initialize encryption keys."""
        try:
            # Load or generate local encryption key
            self._local_key = self._get_or_create_local_key()
            self._local_cipher = Fernet(self._local_key)

            # Load or generate RSA key pair
            self._private_key, self._public_key = self._get_or_create_rsa_keys()

            self.logger.info("Encryption manager initialized")

        except Exception as e:
            self.logger.error(f"Failed to initialize encryption: {e}")
            raise

    def _get_or_create_local_key(self) -> bytes:
        """Get or create local encryption key."""
        key_file = self._get_key_file_path("local.key")

        if key_file.exists():
            try:
                with open(key_file, "rb") as f:
                    return f.read()
            except Exception as e:
                self.logger.warning(f"Failed to load local key: {e}")

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
            self.logger.error(f"Failed to save local key: {e}")

        return key

    def _get_or_create_rsa_keys(self) -> Tuple[rsa.RSAPrivateKey, rsa.RSAPublicKey]:
        """Get or create RSA key pair."""
        private_key_file = self._get_key_file_path("private.pem")
        public_key_file = self._get_key_file_path("public.pem")

        # Try to load existing keys
        if private_key_file.exists() and public_key_file.exists():
            try:
                with open(private_key_file, "rb") as f:
                    private_key = serialization.load_pem_private_key(
                        f.read(), password=None
                    )

                with open(public_key_file, "rb") as f:
                    public_key = serialization.load_pem_public_key(f.read())

                return private_key, public_key

            except Exception as e:
                self.logger.warning(f"Failed to load RSA keys: {e}")

        # Generate new key pair
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        public_key = private_key.public_key()

        # Save keys
        try:
            private_key_file.parent.mkdir(parents=True, exist_ok=True)

            # Save private key
            private_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            )

            with open(private_key_file, "wb") as f:
                f.write(private_pem)

            # Save public key
            public_pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )

            with open(public_key_file, "wb") as f:
                f.write(public_pem)

            # Set restrictive permissions
            if hasattr(os, "chmod"):
                os.chmod(private_key_file, 0o600)
                os.chmod(public_key_file, 0o644)

        except Exception as e:
            self.logger.error(f"Failed to save RSA keys: {e}")

        return private_key, public_key

    def _get_key_file_path(self, filename: str):
        """Get path for key files."""
        from pathlib import Path

        # Use a secure location for keys
        if os.name == "nt":  # Windows
            key_dir = Path.home() / "AppData" / "Roaming" / "Helyxium" / "keys"
        else:  # Unix-like
            key_dir = Path.home() / ".helyxium" / "keys"

        key_dir.mkdir(parents=True, exist_ok=True)
        return key_dir / filename

    def encrypt_local_data(self, data: str) -> str:
        """
        Encrypt data for local storage.

        Args:
            data: Plain text data to encrypt

        Returns:
            Base64 encoded encrypted data
        """
        try:
            if not self._local_cipher:
                raise ValueError("Local encryption not initialized")

            encrypted_data = self._local_cipher.encrypt(data.encode("utf-8"))
            return base64.urlsafe_b64encode(encrypted_data).decode("ascii")

        except Exception as e:
            self.logger.error(f"Local encryption failed: {e}")
            raise

    def decrypt_local_data(self, encrypted_data: str) -> str:
        """
        Decrypt locally stored data.

        Args:
            encrypted_data: Base64 encoded encrypted data

        Returns:
            Decrypted plain text
        """
        try:
            if not self._local_cipher:
                raise ValueError("Local encryption not initialized")

            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode("ascii"))
            decrypted_data = self._local_cipher.decrypt(encrypted_bytes)
            return decrypted_data.decode("utf-8")

        except Exception as e:
            self.logger.error(f"Local decryption failed: {e}")
            raise

    def encrypt_for_transmission(self, data: str, recipient_public_key: bytes) -> str:
        """
        Encrypt data for secure transmission using recipient's public key.

        Args:
            data: Plain text data to encrypt
            recipient_public_key: Recipient's public key in PEM format

        Returns:
            Base64 encoded encrypted data
        """
        try:
            # Load recipient's public key
            public_key = serialization.load_pem_public_key(recipient_public_key)

            # For large data, use hybrid encryption (RSA + AES)
            # Generate a random AES key
            aes_key = Fernet.generate_key()
            aes_cipher = Fernet(aes_key)

            # Encrypt data with AES
            encrypted_data = aes_cipher.encrypt(data.encode("utf-8"))

            # Encrypt AES key with RSA
            encrypted_aes_key = public_key.encrypt(
                aes_key,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None,
                ),
            )

            # Combine encrypted key and data
            combined = {
                "key": base64.urlsafe_b64encode(encrypted_aes_key).decode("ascii"),
                "data": base64.urlsafe_b64encode(encrypted_data).decode("ascii"),
            }

            combined_json = json.dumps(combined)
            return base64.urlsafe_b64encode(combined_json.encode("utf-8")).decode(
                "ascii"
            )

        except Exception as e:
            self.logger.error(f"Transmission encryption failed: {e}")
            raise

    def decrypt_from_transmission(self, encrypted_data: str) -> str:
        """
        Decrypt data received from secure transmission.

        Args:
            encrypted_data: Base64 encoded encrypted data

        Returns:
            Decrypted plain text
        """
        try:
            if not self._private_key:
                raise ValueError("Private key not available")

            # Decode combined data
            combined_json = base64.urlsafe_b64decode(
                encrypted_data.encode("ascii")
            ).decode("utf-8")
            combined = json.loads(combined_json)

            # Decrypt AES key with RSA
            encrypted_aes_key = base64.urlsafe_b64decode(
                combined["key"].encode("ascii")
            )
            aes_key = self._private_key.decrypt(
                encrypted_aes_key,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None,
                ),
            )

            # Decrypt data with AES
            aes_cipher = Fernet(aes_key)
            encrypted_content = base64.urlsafe_b64decode(
                combined["data"].encode("ascii")
            )
            decrypted_data = aes_cipher.decrypt(encrypted_content)

            return decrypted_data.decode("utf-8")

        except Exception as e:
            self.logger.error(f"Transmission decryption failed: {e}")
            raise

    def get_public_key_pem(self) -> bytes:
        """
        Get the public key in PEM format for sharing.

        Returns:
            Public key in PEM format
        """
        if not self._public_key:
            raise ValueError("Public key not available")

        return self._public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

    def generate_session_key(self) -> str:
        """
        Generate a random session key for temporary encryption.

        Returns:
            Base64 encoded session key
        """
        session_key = secrets.token_bytes(32)
        return base64.urlsafe_b64encode(session_key).decode("ascii")

    def encrypt_with_session_key(self, data: str, session_key: str) -> str:
        """
        Encrypt data with a session key.

        Args:
            data: Plain text data to encrypt
            session_key: Base64 encoded session key

        Returns:
            Base64 encoded encrypted data
        """
        try:
            key_bytes = base64.urlsafe_b64decode(session_key.encode("ascii"))
            cipher = Fernet(base64.urlsafe_b64encode(key_bytes))

            encrypted_data = cipher.encrypt(data.encode("utf-8"))
            return base64.urlsafe_b64encode(encrypted_data).decode("ascii")

        except Exception as e:
            self.logger.error(f"Session encryption failed: {e}")
            raise

    def decrypt_with_session_key(self, encrypted_data: str, session_key: str) -> str:
        """
        Decrypt data with a session key.

        Args:
            encrypted_data: Base64 encoded encrypted data
            session_key: Base64 encoded session key

        Returns:
            Decrypted plain text
        """
        try:
            key_bytes = base64.urlsafe_b64decode(session_key.encode("ascii"))
            cipher = Fernet(base64.urlsafe_b64encode(key_bytes))

            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode("ascii"))
            decrypted_data = cipher.decrypt(encrypted_bytes)
            return decrypted_data.decode("utf-8")

        except Exception as e:
            self.logger.error(f"Session decryption failed: {e}")
            raise

    def secure_delete_key_files(self):
        """Securely delete key files (for security reset)."""
        try:
            key_files = [
                self._get_key_file_path("local.key"),
                self._get_key_file_path("private.pem"),
                self._get_key_file_path("public.pem"),
            ]

            for key_file in key_files:
                if key_file.exists():
                    # Overwrite with random data before deletion
                    file_size = key_file.stat().st_size
                    with open(key_file, "wb") as f:
                        f.write(secrets.token_bytes(file_size))

                    key_file.unlink()

            self.logger.info("Key files securely deleted")

        except Exception as e:
            self.logger.error(f"Failed to delete key files: {e}")
            raise


# Global instance
encryption_manager = EncryptionManager()
