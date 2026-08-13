"""
apps/auth/routers.py
Auth endpoints. Register these in main.py:

    from apps.auth.routers import router as auth_router
    app.include_router(auth_router, prefix="/caremate/auth", tags=["auth"])
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from apps.auth.schemas import (
    UserRegister,
    UserLogin,
    UserOut,
    TokenPair,
    AccessToken,
    RefreshRequest,
    GoogleAuthRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    MessageResponse,
)
from apps.auth.services import (
    register_user,
    authenticate_user,
    create_access_token,
    create_refresh_token,
    decode_access_or_refresh,
    get_current_user,
    get_or_create_google_user,
    request_password_reset,
    reset_password,
)
from apps.auth.models import User

router = APIRouter()


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(payload: UserRegister, db: AsyncSession = Depends(get_db)):
    user = await register_user(db, payload.email, payload.password, payload.full_name)
    return user


@router.post("/login", response_model=TokenPair)
async def login(payload: UserLogin, db: AsyncSession = Depends(get_db)):
    user = await authenticate_user(db, payload.email, payload.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")

    return TokenPair(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.post("/refresh", response_model=AccessToken)
async def refresh(payload: RefreshRequest):
    # Verifies the refresh token and issues a new access token.
    # Does NOT rotate the refresh token in this version.
    user_id = decode_access_or_refresh(payload.refresh_token, expected_type="refresh")
    return AccessToken(access_token=create_access_token(user_id))


@router.post("/google", response_model=TokenPair)
async def google_login(payload: GoogleAuthRequest, db: AsyncSession = Depends(get_db)):
    """Client sends the id_token it got from Google Sign-In. We verify it,
    create/link the local user, and return our own access+refresh JWT pair —
    same shape as /login, so the client's token-handling code doesn't need to branch."""
    user = await get_or_create_google_user(db, payload.id_token)

    return TokenPair(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.get("/me", response_model=UserOut)
async def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(payload: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    await request_password_reset(db, payload.email)
    # Always the same response whether or not the email exists — don't leak account existence.
    return MessageResponse(message="If that email is registered, a reset link has been sent.")


@router.post("/reset-password", response_model=MessageResponse)
async def do_reset_password(payload: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    await reset_password(db, payload.token, payload.new_password)
    return MessageResponse(message="Password has been reset. You can now log in.")
