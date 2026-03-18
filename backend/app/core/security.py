from cryptography.fernet import Fernet
import base64
import os
from app.config import settings


def _get_cipher() -> Fernet:
    key = settings.ENCRYPTION_KEY
    if not key:
        key = base64.urlsafe_b64encode(os.urandom(32)).decode()
    elif len(key) != 44:
        key = base64.urlsafe_b64encode(key.encode()[:32].ljust(32, b"0"))
    return Fernet(key.encode() if isinstance(key, str) else key)


def encrypt(data: str) -> str:
    cipher = _get_cipher()
    return cipher.encrypt(data.encode()).decode()


def decrypt(token: str) -> str:
    cipher = _get_cipher()
    return cipher.decrypt(token.encode()).decode()
