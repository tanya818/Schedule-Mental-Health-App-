import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, EmailStr, ConfigDict, Field


# ---------- Users ----------

class UserCreate(BaseModel):
    """Body for POST /users. id and createdAt are server-generated."""
    name: str
    email: EmailStr
    age: Optional[int] = Field(default=None, ge=0, le=150)
    gender: Optional[str] = None


class UserUpdate(BaseModel):
    """Body for PUT /users/{userId} (full replace)."""
    name: str
    email: EmailStr
    age: Optional[int] = Field(default=None, ge=0, le=150)
    gender: Optional[str] = None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    email: str
    age: Optional[int] = None
    gender: Optional[str] = None
    created_at: datetime


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


class EventCreate(BaseModel):
    """Body for POST /users/{userId}/events."""
    name: str
    start_time: datetime
    end_time: datetime
    stress_level: Optional[int] = Field(default=None, ge=0, le=10)
    recurring: bool = False
    category: EventCategory
    description: Optional[str] = None


class EventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    start_time: datetime
    end_time: datetime
    stress_level: Optional[int] = None
    recurring: bool
    category: str
    description: Optional[str] = None
    created_at: datetime
