import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db

router = APIRouter(tags=["Events"])


@router.post(
    "/users/{userId}/events",
    response_model=schemas.EventOut,
    status_code=status.HTTP_201_CREATED,
)
def create_event(
    userId: uuid.UUID, payload: schemas.EventCreate, db: Session = Depends(get_db)
):
    """Create a new event on the given user's schedule."""
    user = db.query(models.User).filter(models.User.id == userId).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {userId} not found",
        )

    if payload.end_time <= payload.start_time:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="end_time must be after start_time",
        )

    event = models.Event(
        user_id=userId,
        name=payload.name,
        start_time=payload.start_time,
        end_time=payload.end_time,
        stress_level=payload.stress_level,
        recurring=payload.recurring,
        category=payload.category.value,
        description=payload.description,
    )

    db.add(event)
    db.commit()
    db.refresh(event)

    return event
