"""
apps/auth/models.py
SQLAlchemy model for the users table.
Onboarding data (role/interests/state) lives in apps.onboarding.models.OnboardingProfile,
linked back to this table by user_id — kept separate so auth stays identity-only.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    # Nullable because Google-only accounts have no local password
    # (also nullable after a forgot-password reset request until they set a new one).
    hashed_password = Column(String, nullable=True)
    full_name = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)

    # Set when the account was created/linked via "Sign in with Google".
    # Unique + nullable: normal email/password users leave this NULL.
    google_id = Column(String, unique=True, index=True, nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # One-to-one to apps.onboarding.models.OnboardingProfile
    onboarding_profile = relationship(
        "OnboardingProfile", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<User id={self.id} email={self.email}>"
