from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
import hashlib
import secrets
from app.config import settings

def hash_password(password: str) -> str:
    """Hashes a password using PBKDF2-HMAC-SHA256 with a secure random salt."""
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
    return f"{salt}${key.hex()}"

def verify_password(plain_password: str, hashed_password: str | None) -> bool:
    """Verifies a plain password against the stored salt$hash string."""
    if not hashed_password:
        return True  # Allows existing legacy accounts without password to authenticate and set one
    try:
        if "$" not in hashed_password:
            return secrets.compare_digest(hashed_password, plain_password)
        salt, key_hex = hashed_password.split("$", 1)
        expected_key = hashlib.pbkdf2_hmac('sha256', plain_password.encode('utf-8'), salt.encode('utf-8'), 100000)
        return secrets.compare_digest(expected_key.hex(), key_hex)
    except Exception:
        return False

def create_access_token(user_id: str) -> str:
    """Creates a JWT access token valid for 7 days"""
    expire = datetime.now(timezone.utc) + timedelta(days=7)
    to_encode = {"sub": str(user_id), "exp": expire}
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return encoded_jwt

def decode_access_token(token: str) -> dict:
    """Decodes a JWT access token, raising an exception on failure"""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return payload
    except JWTError:
        raise ValueError("Invalid or expired token")
