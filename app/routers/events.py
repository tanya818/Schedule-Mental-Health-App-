from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import get_current_user
from app.database import get_db

router = APIRouter(tags=["Events"])


@router.post(
    "/users/me/events",
    response_model=schemas.EventOut,
    status_code=status.HTTP_201_CREATED,
)
def create_event(
    payload: schemas.EventCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new event on the logged-in user's schedule."""
    if payload.end_time <= payload.start_time:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="end_time must be after start_time",
        )

    rec = payload.recurrence
    event = models.Event(
        user_id=current_user.id,
        name=payload.name,
        start_time=payload.start_time,
        end_time=payload.end_time,
        stress_level=payload.stress_level,
        category=payload.category.value,
        description=payload.description,
        recurrence_frequency=rec.frequency.value if rec else None,
        recurrence_interval=rec.interval if rec else None,
        recurrence_days=[d.value for d in rec.days_of_week] if rec and rec.days_of_week else None,
        recurrence_until=rec.until if rec else None,
    )

    db.add(event)
    db.commit()
    db.refresh(event)

    return schemas.EventOut.from_model(event)
