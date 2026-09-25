import uuid
from datetime import date, datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, EmailStr, ConfigDict, Field, field_validator, model_validator


# ---------- Users ----------

class UserUpdate(BaseModel):
    """Body for PUT /users/me (full replace). Email comes from Google and isn't editable."""
    name: str = Field(min_length=1, max_length=100)
    age: Optional[int] = Field(default=None, ge=0, le=150)
    gender: Optional[str] = None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    email: str
    avatar_url: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    created_at: datetime


# ---------- Auth ----------

class GoogleSignInRequest(BaseModel):
    """Body for POST /auth/google."""
    id_token: str = Field(min_length=1, description="Google ID token from the mobile app")


class DevSignInRequest(BaseModel):
    """Body for POST /auth/dev-login (development only)."""
    email: EmailStr
    name: Optional[str] = None


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
    is_new_user: bool
    user: UserOut


# ---------- Events ----------

class EventCategory(str, Enum):
    """
    Placeholder categories — adjust to whatever set you actually want.
    Kept as a Python enum so FastAPI validates + documents allowed values.
    """
    WORK = "work"
    PERSONAL = "personal"
    HEALTH = "health"
    SOCIAL = "social"
    SLEEP = "sleep"
    OTHER = "other"


class RecurrenceFrequency(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"


class Weekday(str, Enum):
    MON = "mon"
    TUE = "tue"
    WED = "wed"
    THU = "thu"
    FRI = "fri"
    SAT = "sat"
    SUN = "sun"


_WEEKDAY_ORDER = list(Weekday)


class Recurrence(BaseModel):
    """
    How an event repeats. Leave `recurrence` out of the event for a one-time event.

    Examples:
      every day:                 {"frequency": "daily"}
      every other week, Mon+Wed: {"frequency": "weekly", "interval": 2, "days_of_week": ["mon", "wed"]}
      monthly until year end:    {"frequency": "monthly", "until": "2026-12-31"}
    """
    frequency: RecurrenceFrequency
    interval: int = Field(default=1, ge=1, le=365, description="Every N periods (2 + weekly = every other week)")
    days_of_week: Optional[List[Weekday]] = Field(
        default=None,
        description="Weekly only. Defaults to the weekday of start_time.",
    )
    until: Optional[date] = Field(default=None, description="Last date (inclusive). Omit to repeat forever.")

    @field_validator("days_of_week")
    @classmethod
    def dedupe_and_sort_days(cls, v: Optional[List[Weekday]]) -> Optional[List[Weekday]]:
        if v is None:
            return None
        if len(v) == 0:
            raise ValueError("days_of_week cannot be empty; omit it to use the start day")
        return sorted(set(v), key=_WEEKDAY_ORDER.index)

    @model_validator(mode="after")
    def days_only_for_weekly(self):
        if self.days_of_week is not None and self.frequency != RecurrenceFrequency.WEEKLY:
            raise ValueError("days_of_week is only allowed when frequency is 'weekly'")
        return self


class EventCreate(BaseModel):
    """Body for POST /users/me/events."""
    name: str
    start_time: datetime
    end_time: datetime
    stress_level: Optional[int] = Field(default=None, ge=0, le=10)
    category: EventCategory
    description: Optional[str] = None
    recurrence: Optional[Recurrence] = Field(default=None, description="Omit for a one-time event")

    @model_validator(mode="after")
    def until_after_start(self):
        if self.recurrence and self.recurrence.until and self.recurrence.until < self.start_time.date():
            raise ValueError("recurrence.until must be on or after the start date")
        return self


class EventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    start_time: datetime
    end_time: datetime
    stress_level: Optional[int] = None
    category: str
    description: Optional[str] = None
    recurrence: Optional[Recurrence] = None  # null = one-time event
    created_at: datetime

    @classmethod
    def from_model(cls, event) -> "EventOut":
        recurrence = None
        if event.recurrence_frequency is not None:
            recurrence = Recurrence(
                frequency=event.recurrence_frequency,
                interval=event.recurrence_interval,
                days_of_week=event.recurrence_days,
                until=event.recurrence_until,
            )
        return cls(
            id=event.id,
            user_id=event.user_id,
            name=event.name,
            start_time=event.start_time,
            end_time=event.end_time,
            stress_level=event.stress_level,
            category=event.category,
            description=event.description,
            recurrence=recurrence,
            created_at=event.created_at,
        )
