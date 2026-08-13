"""
apps/auth/services/normal_services.py
Everything that isn't Google-specific: registration, email/password login,
access/refresh token issuing, the get_current_user dependency used to protect
routes everywhere in the app, and forgot/reset password.
"""

import logging
from datetime import timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config.base import settings
from core.database import get_db
from apps.auth.models import User
from apps.auth.helpers import hash_password, verify_password, create_token, decode_token

logger = logging.getLogger(__name__)

# Gives Swagger's "Authorize" dialog a single "paste your token" box instead of
# OAuth2PasswordBearer's username/password/client_id/client_secret form (which
# doesn't match our JSON-body /login endpoint and always fails via Swagger's UI).
bearer_scheme = HTTPBearer(auto_error=True)
bearer_scheme_optional = HTTPBearer(auto_error=False)


# ---------------- Token issuing ----------------

def create_access_token(user_id: int) -> str:
    return create_token(str(user_id), timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES), "access")


def create_refresh_token(user_id: int) -> str:
    return create_token(str(user_id), timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS), "refresh")


def _decode_and_check_type(token: str, expected_type: str) -> int:
    payload = decode_token(token)
    if not payload or payload.get("type") != expected_type or payload.get("sub") is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return int(payload["sub"])


def decode_access_or_refresh(token: str, expected_type: str) -> int:
    """Public wrapper so routers can decode a refresh token without importing
    the private helper above directly."""
    return _decode_and_check_type(token, expected_type)


# ---------------- User lookups ----------------

async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


# ---------------- Register / login ----------------

async def register_user(db: AsyncSession, email: str, password: str, full_name: str) -> User:
    existing = await get_user_by_email(db, email)
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(email=email, hashed_password=hash_password(password), full_name=full_name)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def authenticate_user(db: AsyncSession, email: str, password: str) -> Optional[User]:
    user = await get_user_by_email(db, email)
    if not user or not user.hashed_password:
        # No such user, or a Google-only account with no local password set.
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


# ---------------- Dependencies for protected routes ----------------

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    user_id = _decode_and_check_type(credentials.credentials, expected_type="access")
    user = await get_user_by_id(db, user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
    return user


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme_optional),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """Doesn't raise if there's no/invalid token — for endpoints that are public
    but show extra data when logged in (e.g. 'has_liked' on a feed item)."""
    if not credentials:
        return None
    try:
        user_id = _decode_and_check_type(credentials.credentials, expected_type="access")
    except HTTPException:
        return None
    return await get_user_by_id(db, user_id)


# ---------------- Forgot / reset password ----------------

async def request_password_reset(db: AsyncSession, email: str) -> None:
    """Always returns silently, whether or not the email exists — never reveal
    account existence via this endpoint. If the user exists, logs (in place of
    actually emailing) a reset link containing a short-lived 'reset' token."""
    user = await get_user_by_email(db, email)
    if not user:
        return

    reset_token = create_token(
        str(user.id), timedelta(minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES), "reset"
    )

    # TODO: replace with a real email send (e.g. SES/SendGrid/Resend).
    # The frontend route should be something like /reset-password?token=<reset_token>.
    logger.info("Password reset requested for %s — token=%s", user.email, reset_token)


async def reset_password(db: AsyncSession, token: str, new_password: str) -> None:
    user_id = _decode_and_check_type(token, expected_type="reset")
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token")

    # Also covers Google-only accounts setting a password for the first time,
    # which lets them log in with email/password from then on too.
    user.hashed_password = hash_password(new_password)
    db.add(user)
    await db.commit()