"""
Authentication helpers:
  - verify_google_id_token: checks a Google ID token sent by the mobile app
  - create_access_token:    issues OUR access token (JWT signed with JWT_SECRET)
  - get_current_user:       FastAPI dependency that reads "Authorization: Bearer <token>"
"""
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from google.auth.exceptions import TransportError
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from sqlalchemy.orm import Session

from app import config, models
from app.database import get_db

ALGORITHM = "HS256"

_google_request = google_requests.Request()
_bearer = HTTPBearer(auto_error=False)


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


# ---------- Google ----------

def verify_google_id_token(token: str) -> dict:
    """
    Verify a Google ID token and return its claims (sub, email, name, picture, ...).
    Checks: Google's signature, issuer, expiry, audience == our Web client ID, verified email.
    """
    if not config.GOOGLE_WEB_CLIENT_ID:
        # Without a client ID the audience check would be skipped, so refuse instead.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google sign-in is not configured (GOOGLE_WEB_CLIENT_ID is missing)",
        )
    try:
        claims = google_id_token.verify_oauth2_token(
            token,
            _google_request,
            audience=config.GOOGLE_WEB_CLIENT_ID,
            clock_skew_in_seconds=10,
        )
    except TransportError:
        # Couldn't download Google's public keys (network problem), not the user's fault
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not reach Google to verify the sign-in. Try again.",
        )
    except ValueError:
        raise _unauthorized("Invalid or expired Google ID token")

    if not claims.get("email"):
        raise _unauthorized("Google ID token has no email. Request the 'openid email profile' scopes.")
    if not claims.get("email_verified"):
        raise _unauthorized("Google account email is not verified")
    return claims


# ---------- Our access tokens ----------

def create_access_token(user: models.User) -> Tuple[str, int]:
    """Return (token, expires_in_seconds)."""
    now = datetime.now(timezone.utc)
    expires_in = config.ACCESS_TOKEN_MINUTES * 60
    payload = {
        "sub": str(user.id),
        "ver": user.token_version,
        "iat": now,
        "exp": now + timedelta(seconds=expires_in),
    }
    return jwt.encode(payload, config.JWT_SECRET, algorithm=ALGORITHM), expires_in


def get_current_user(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
    db: Session = Depends(get_db),
) -> models.User:
    """Resolve the logged-in user from 'Authorization: Bearer <access_token>'."""
    if creds is None:
        raise _unauthorized("Not authenticated")

    try:
        payload = jwt.decode(
            creds.credentials,
            config.JWT_SECRET,
            algorithms=[ALGORITHM],
            options={"require": ["sub", "exp"]},
        )
        user_id = uuid.UUID(payload["sub"])
    except (jwt.PyJWTError, ValueError):
        raise _unauthorized("Invalid or expired access token")

    user = db.get(models.User, user_id)
    # token_version mismatch means the user used "log out of all devices"
    if user is None or payload.get("ver") != user.token_version:
        raise _unauthorized("Invalid or expired access token")
    return user
