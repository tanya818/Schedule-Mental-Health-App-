from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import config, models, schemas
from app.auth import create_access_token, get_current_user, verify_google_id_token
from app.database import get_db

router = APIRouter(prefix="/auth", tags=["Auth"])


def _find_by_email(db: Session, email: str) -> Optional[models.User]:
    return db.query(models.User).filter(func.lower(models.User.email) == email.lower()).first()


def _sign_in(db: Session, user: models.User, is_new_user: bool) -> schemas.AuthResponse:
    user.last_login_at = datetime.now(timezone.utc)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This email is already used by another account",
        )
    db.refresh(user)
    token, expires_in = create_access_token(user)
    return schemas.AuthResponse(
        access_token=token,
        expires_in=expires_in,
        is_new_user=is_new_user,
        user=schemas.UserOut.model_validate(user),
    )


@router.post("/google", response_model=schemas.AuthResponse)
def google_sign_in(payload: schemas.GoogleSignInRequest, db: Session = Depends(get_db)):
    """
    Sign in with a Google ID token from the mobile app.
    Finds the user by Google 'sub', links an existing user by email, or creates a new user.
    """
    claims = verify_google_id_token(payload.id_token)
    google_sub = claims["sub"]
    email = claims["email"].lower()
    is_new_user = False

    # 1. Returning Google user
    user = db.query(models.User).filter(models.User.google_sub == google_sub).first()

    if user is None:
        # 2. Existing user created before Google sign-in: link by email
        user = _find_by_email(db, email)
        if user is not None:
            if user.google_sub is not None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="This email is linked to a different Google account",
                )
            user.google_sub = google_sub
        else:
            # 3. Brand-new user
            user = models.User(
                name=claims.get("name") or email.split("@")[0],
                email=email,
                google_sub=google_sub,
            )
            db.add(user)
            is_new_user = True
    elif user.email != email:
        # Email changed on the Google side: keep ours in sync
        user.email = email

    user.avatar_url = claims.get("picture")
    return _sign_in(db, user, is_new_user)


@router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
def logout_all_devices(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Invalidate every access token issued to this user (all devices)."""
    current_user.token_version += 1
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------- Development only ----------

def dev_sign_in(payload: schemas.DevSignInRequest, db: Session = Depends(get_db)):
    """
    DEVELOPMENT ONLY. Sign in as any email without Google, for Postman testing.
    Only registered when ENV=development.
    """
    email = payload.email.lower()
    user = _find_by_email(db, email)
    is_new_user = user is None
    if is_new_user:
        user = models.User(name=payload.name or email.split("@")[0], email=email)
        db.add(user)
    return _sign_in(db, user, is_new_user)


if config.IS_DEV:
    router.add_api_route(
        "/dev-login",
        dev_sign_in,
        methods=["POST"],
        response_model=schemas.AuthResponse,
        summary="Dev login (development only)",
    )
