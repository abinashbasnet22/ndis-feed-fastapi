"""
apps/auth/services/__init__.py
Re-exports everything from normal_services and google_services so routers.py
(and anything else) can just do `from apps.auth.services import X`,
matching the apps/newsfeed/services/__init__.py convention.
"""

from apps.auth.services.normal_services import (
    create_access_token,
    create_refresh_token,
    decode_access_or_refresh,
    get_user_by_email,
    get_user_by_id,
    register_user,
    authenticate_user,
    get_current_user,
    get_current_user_optional,
    request_password_reset,
    reset_password,
)
from apps.auth.services.google_services import get_or_create_google_user

__all__ = [
    "create_access_token",
    "create_refresh_token",
    "decode_access_or_refresh",
    "get_user_by_email",
    "get_user_by_id",
    "register_user",
    "authenticate_user",
    "get_current_user",
    "get_current_user_optional",
    "request_password_reset",
    "reset_password",
    "get_or_create_google_user",
]
