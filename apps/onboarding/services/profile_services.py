"""
apps/onboarding/services.py
"""

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.onboarding.models import OnboardingProfile


async def get_onboarding_profile(db: AsyncSession, user_id: int) -> Optional[OnboardingProfile]:
    result = await db.execute(select(OnboardingProfile).where(OnboardingProfile.user_id == user_id))
    return result.scalar_one_or_none()


async def upsert_onboarding_profile(
    db: AsyncSession, user_id: int, role: str, interests: List[str], state: str
) -> OnboardingProfile:
    """Creates the profile on first submit; overwrites it if the user re-does
    onboarding later (e.g. changes their region or interests from settings)."""
    profile = await get_onboarding_profile(db, user_id)

    if profile:
        profile.role = role
        profile.interests = interests
        profile.state = state
    else:
        profile = OnboardingProfile(user_id=user_id, role=role, interests=interests, state=state)
        db.add(profile)

    await db.commit()
    await db.refresh(profile)
    return profile
