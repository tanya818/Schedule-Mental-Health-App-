import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    String,
    Text,
    SmallInteger,
    CheckConstraint,
    Date,
    Integer,
    TIMESTAMP,
    ForeignKey,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("uuid_generate_v4()"),
    )
    name = Column(Text, nullable=False)
    email = Column(Text, unique=True, nullable=False)
    age = Column(SmallInteger, nullable=True)
    gender = Column(Text, nullable=True)
    created_at = Column(
        TIMESTAMP(timezone=True), nullable=False, server_default=text("now()")
    )

    # Google sign-in
    google_sub = Column(Text, unique=True, nullable=True)  # Google's permanent user ID ("sub")
    avatar_url = Column(Text, nullable=True)               # Google profile picture
    last_login_at = Column(TIMESTAMP(timezone=True), nullable=True)
    updated_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("now()"),
        onupdate=func.now(),
    )
    # Bump to invalidate every access token for this user ("log out of all devices")
    token_version = Column(
        Integer, nullable=False, default=0, server_default=text("0")
    )

    events = relationship(
        "Event", back_populates="user", cascade="all, delete-orphan"
    )


class Event(Base):
    __tablename__ = "events"
    __table_args__ = (
        CheckConstraint(
            "recurrence_frequency IN ('daily', 'weekly', 'monthly', 'yearly')",
            name="ck_events_recurrence_frequency",
        ),
        # One-time event: all recurrence fields empty. Repeating: frequency + interval >= 1.
        CheckConstraint(
            "(recurrence_frequency IS NULL AND recurrence_interval IS NULL"
            " AND recurrence_days IS NULL AND recurrence_until IS NULL)"
            " OR (recurrence_frequency IS NOT NULL AND recurrence_interval >= 1)",
            name="ck_events_recurrence_complete",
        ),
        CheckConstraint(
            "recurrence_days IS NULL OR recurrence_frequency = 'weekly'",
            name="ck_events_recurrence_days_weekly_only",
        ),
    )

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("uuid_generate_v4()"),
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    name = Column(Text, nullable=False)
    start_time = Column(TIMESTAMP(timezone=True), nullable=False)
    end_time = Column(TIMESTAMP(timezone=True), nullable=False)
    stress_level = Column(SmallInteger, nullable=True)
    category = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(
        TIMESTAMP(timezone=True), nullable=False, server_default=text("now()")
    )

    # Recurrence rule. All NULL = one-time event.
    recurrence_frequency = Column(Text, nullable=True)            # daily | weekly | monthly | yearly
    recurrence_interval = Column(SmallInteger, nullable=True)     # every N periods (1 = every)
    recurrence_days = Column(ARRAY(Text), nullable=True)          # weekly only: ["mon", "wed"]
    recurrence_until = Column(Date, nullable=True)                # last date (inclusive); NULL = forever

    user = relationship("User", back_populates="events")
