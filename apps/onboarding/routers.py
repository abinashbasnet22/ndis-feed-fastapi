"""
apps/onboarding/routers.py
Register in main.py:

    from apps.onboarding.routers import router as onboarding_router
    app.include_router(onboarding_router, prefix="/caremate/onboarding", tags=["onboarding"])
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from apps.auth.services import get_current_user
from apps.auth.models import User
from apps.onboarding.schemas import OnboardingRequest, OnboardingOut
from apps.onboarding.services import upsert_onboarding_profile, get_onboarding_profile

router = APIRouter()


@router.put("/", response_model=OnboardingOut)
async def submit_onboarding(
    payload: OnboardingRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Called once right after /caremate/auth/register (or /google for
    first-time Google sign-ups). PUT because re-submitting fully replaces
    the previous answers rather than patching individual fields."""
    profile = await upsert_onboarding_profile(
        db, current_user.id, payload.role.value, payload.interests, payload.state.value
    )
    return profile


@router.get("/me", response_model=OnboardingOut)
async def my_onboarding(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Frontend calls this after login to decide: show onboarding flow (404 = not
    done yet) or skip straight to the feed."""
    profile = await get_onboarding_profile(db, current_user.id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Onboarding not completed")
    return profile
