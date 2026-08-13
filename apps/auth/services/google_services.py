"""
apps/auth/services/google_services.py
Business logic for "Sign in with Google": token verification is delegated to
apps.auth.backends.google_backend (the only thing that talks to Google);
this module owns what happens in OUR database once we trust the token.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.auth.backends.google_backend import verify_google_id_token
from apps.auth.models import User
from apps.auth.services.normal_services import get_user_by_email


async def get_or_create_google_user(db: AsyncSession, id_token: str) -> User:
    payload = verify_google_id_token(id_token)
    google_id = payload["sub"]
    email = payload["email"]

    # 1. Already linked by google_id -> just log them in.
    result = await db.execute(select(User).where(User.google_id == google_id))
    user = result.scalar_one_or_none()
    if user:
        return user

    # 2. Existing email/password account with the same email -> link Google to it.
    user = await get_user_by_email(db, email)
    if user:
        user.google_id = google_id
        user.is_verified = True
        if not user.avatar_url:
            user.avatar_url = payload.get("picture")
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    # 3. Brand new user, created via Google only (no password).
    user = User(
        email=email,
        hashed_password=None,
        full_name=payload.get("name"),
        avatar_url=payload.get("picture"),
        google_id=google_id,
        is_verified=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
