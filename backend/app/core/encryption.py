from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os
from app.core.config import settings


def get_encryption_key() -> bytes:
    """Derive encryption key from JWT secret"""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b'crypto_trading_salt',  # In production, use a proper salt
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(settings.SECRET_KEY.encode()))
    return key


def encrypt_data(data: str) -> str:
    """Encrypt sensitive data (API keys, secrets)"""
    key = get_encryption_key()
    fernet = Fernet(key)
    encrypted = fernet.encrypt(data.encode())
    return base64.urlsafe_b64encode(encrypted).decode()


def decrypt_data(encrypted_data: str) -> str:
    """Decrypt sensitive data"""
    key = get_encryption_key()
    fernet = Fernet(key)
    encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
    decrypted = fernet.decrypt(encrypted_bytes)
    return decrypted.decode()
