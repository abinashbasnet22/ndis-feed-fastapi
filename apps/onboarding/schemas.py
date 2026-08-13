"""
apps/onboarding/schemas.py
Enums and request/response shapes for the onboarding flow
(Step 1: role, Step 2: interests, Step 3: state — submitted together as one call).
"""

from enum import Enum
from typing import List

from pydantic import BaseModel, Field, field_validator


class UserRole(str, Enum):
    NDIS_PROVIDER = "ndis_provider"
    ALLIED_HEALTH = "allied_health"
    NDIS_PARTICIPANT = "ndis_participant"
    SUPPORT_WORKER = "support_worker"
    SUPPORT_COORDINATOR = "support_coordinator"
    PLAN_MANAGER = "plan_manager"
    FAMILY_CARER = "family_carer"
    JOB_SEEKER = "job_seeker"


class AustralianState(str, Enum):
    NSW = "NSW"
    VIC = "VIC"
    QLD = "QLD"
    WA = "WA"
    SA = "SA"
    TAS = "TAS"
    ACT = "ACT"
    NT = "NT"


# Tags shown on the "What topics interest you?" screen.
INTEREST_TAGS = {
    "policy_and_law",
    "funding",
    "sil_sda",
    "workforce",
    "early_funding",
    "allied_health",
}


class OnboardingRequest(BaseModel):
    role: UserRole
    interests: List[str] = Field(min_length=3)
    state: AustralianState

    @field_validator("interests")
    @classmethod
    def check_interests(cls, value: List[str]) -> List[str]:
        unknown = set(value) - INTEREST_TAGS
        if unknown:
            raise ValueError(f"Unknown interest tag(s): {sorted(unknown)}")
        return value


class OnboardingOut(BaseModel):
    role: UserRole
    interests: List[str]
    state: AustralianState

    class Config:
        from_attributes = True
