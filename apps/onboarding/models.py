"""
apps/onboarding/models.py
Stores the answers from the 3-step onboarding flow (role / interests / state),
one row per user. Kept separate from apps.auth.models.User so auth stays
identity-only and onboarding can evolve independently (e.g. re-onboarding,
versioned onboarding flows, etc.) without touching the users table.
"""

from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from core.database import Base


class OnboardingProfile(Base):
    __tablename__ = "onboarding_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)

    role = Column(String, nullable=False)  # apps.onboarding.schemas.UserRole value
    interests = Column(ARRAY(Text), nullable=False)  # apps.onboarding.schemas.INTEREST_TAGS values
    state = Column(String, nullable=False)  # apps.onboarding.schemas.AustralianState value

    completed_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="onboarding_profile")

    def __repr__(self):
        return f"<OnboardingProfile user_id={self.user_id} role={self.role}>"
