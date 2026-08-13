"""
apps/auth/helpers.py
Framework-agnostic building blocks used by the service layer:
password hashing and raw JWT encode/decode. No FastAPI or DB imports here on
purpose — keeps these easy to unit test in isolation.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from config.base import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ---------------- Password hashing ----------------

def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# ---------------- Raw JWT encode/decode ----------------

def create_token(subject: str, expires_delta: timedelta, token_type: str) -> str:
    """subject is normally the user_id as a string. token_type is one of:
    'access' | 'refresh' | 'reset' (password reset)."""
    to_encode = {
        "sub": subject,
        "type": token_type,
        "exp": datetime.now(timezone.utc) + expires_delta,
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    """Returns the decoded payload, or None if the token is invalid/expired.
    Caller is responsible for checking payload['type'] matches what it expects."""
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        return None
