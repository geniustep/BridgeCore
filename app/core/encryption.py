"""
Encryption Service for Sensitive Data

Encrypt/decrypt connection configs and credentials
"""
from cryptography.fernet import Fernet
from typing import Dict, Any
import json
import base64
from app.core.config import settings


class EncryptionService:
    """
    Service for encrypting sensitive data

    Features:
    - Encrypt connection configs
    - Decrypt for use
    - Key management
    """

    def __init__(self, encryption_key: str = None):
        """
        Initialize encryption service

        Args:
            encryption_key: Base64-encoded Fernet key
        """
        if encryption_key:
            self.key = encryption_key.encode()
        else:
            # Use secret key from settings or generate one
            # In production, use environment variable
            self.key = base64.urlsafe_b64encode(
                settings.SECRET_KEY.encode()[:32].ljust(32, b'0')
            )

        self.cipher = Fernet(self.key)

    def encrypt_config(self, config: Dict[str, Any]) -> str:
        """
        Encrypt configuration dictionary

        Args:
            config: Configuration dictionary

        Returns:
            Encrypted string

        Example:
            encrypted = service.encrypt_config({
                "url": "https://odoo.example.com",
                "username": "admin",
                "password": "secret123"
            })
        """
        json_str = json.dumps(config)
        encrypted_bytes = self.cipher.encrypt(json_str.encode())
        return encrypted_bytes.decode()

    def decrypt_config(self, encrypted_data: str) -> Dict[str, Any]:
        """
        Decrypt configuration

        Args:
            encrypted_data: Encrypted string

        Returns:
            Decrypted configuration dictionary
        """
        decrypted_bytes = self.cipher.decrypt(encrypted_data.encode())
        json_str = decrypted_bytes.decode()
        return json.loads(json_str)

    def encrypt_value(self, value: str) -> str:
        """
        Encrypt single value

        Args:
            value: Value to encrypt

        Returns:
            Encrypted string
        """
        encrypted_bytes = self.cipher.encrypt(value.encode())
        return encrypted_bytes.decode()

    def decrypt_value(self, encrypted_value: str) -> str:
        """
        Decrypt single value

        Args:
            encrypted_value: Encrypted string

        Returns:
            Decrypted value
        """
        decrypted_bytes = self.cipher.decrypt(encrypted_value.encode())
        return decrypted_bytes.decode()

    @staticmethod
    def generate_key() -> str:
        """
        Generate new Fernet key

        Returns:
            Base64-encoded key string
        """
        key = Fernet.generate_key()
        return key.decode()


# Global encryption service instance
encryption_service = EncryptionService()


# Helper functions for backward compatibility
def encrypt_data(data: Dict[str, Any]) -> str:
    """
    Encrypt configuration data (helper function)
    
    Args:
        data: Configuration dictionary
        
    Returns:
        Encrypted string
    """
    return encryption_service.encrypt_config(data)


def decrypt_data(encrypted_data: str) -> Dict[str, Any]:
    """
    Decrypt configuration data (helper function)
    
    Args:
        encrypted_data: Encrypted string
        
    Returns:
        Decrypted configuration dictionary
    """
    return encryption_service.decrypt_config(encrypted_data)
