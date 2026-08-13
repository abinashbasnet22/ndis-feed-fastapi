"""
apps/auth/backends/google_backend.py
Talks to Google only. No DB, no business logic — just "is this id_token legit,
and if so what did Google tell us about the person". Kept isolated so it's easy
to mock in tests and easy to swap if you ever add another OAuth provider
(e.g. apps/auth/backends/apple_backend.py) alongside it.
"""

from fastapi import HTTPException, status
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token

from config.base import settings


def verify_google_id_token(token: str) -> dict:
    """Verifies the id_token's signature against Google's public keys and checks
    the audience matches our OAuth client ID. Raises HTTPException(401) on any
    failure. Returns Google's decoded payload on success:
    sub, email, email_verified, name, picture, iss, aud, exp, ...
    """
    try:
        payload = google_id_token.verify_oauth2_token(
            token, google_requests.Request(), settings.GOOGLE_CLIENT_ID
        )
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Google token")

    if payload.get("iss") not in ("accounts.google.com", "https://accounts.google.com"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token issuer")
    if not payload.get("email_verified", False):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Google email not verified")

    return payload
