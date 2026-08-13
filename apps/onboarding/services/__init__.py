"""
apps/onboarding/services/__init__.py
Re-exports so `from apps.onboarding.services import X` keeps working unchanged
in routers.py, matching the apps/newsfeed/services/__init__.py convention.
"""

from apps.onboarding.services.profile_services import (
    get_onboarding_profile,
    upsert_onboarding_profile,
)

__all__ = [
    "get_onboarding_profile",
    "upsert_onboarding_profile",
]