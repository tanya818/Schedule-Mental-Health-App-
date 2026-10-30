from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import get_current_user
from app.database import get_db

router = APIRouter(tags=["Users"])


@router.get("/users/me", response_model=schemas.UserOut)
def get_me(current_user: models.User = Depends(get_current_user)):
    """Read the logged-in user's info."""
    return current_user


@router.put("/users/me", response_model=schemas.UserOut)
def update_me(
    payload: schemas.UserUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Full replace of the logged-in user's profile (used for onboarding and edits)."""
    current_user.name = payload.name
    current_user.age = payload.age
    current_user.gender = payload.gender
    db.commit()
    db.refresh(current_user)
    return current_user
