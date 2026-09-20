import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    String,
    Text,
    SmallInteger,
    Boolean,
    TIMESTAMP,
    ForeignKey,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
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

    events = relationship(
        "Event", back_populates="user", cascade="all, delete-orphan"
    )


class Event(Base):
    __tablename__ = "events"

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
    recurring = Column(Boolean, nullable=False, default=False, server_default=text("false"))
    category = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(
        TIMESTAMP(timezone=True), nullable=False, server_default=text("now()")
    )

    user = relationship("User", back_populates="events")
