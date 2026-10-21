from __future__ import annotations

import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    Float,
    DateTime,
    Text,
    JSON,
    ForeignKey,
)
from sqlalchemy.orm import relationship

from app.db.base import Base


class User(Base):
    """Registered user model with secure password hash and isolated report relationships."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        onupdate=lambda: datetime.datetime.now(datetime.timezone.utc),
        nullable=False,
    )

    reports = relationship("SavedReport", back_populates="user", cascade="all, delete-orphan")


class SavedReport(Base):
    """Saved farm soil report, analysis results, and recommendation history.
    
    Stores reviewed measurements, evaluated deficiencies, crop scores, fertilizer
    options, weather application windows, and plain-language explanation with
    strict user isolation.
    """

    __tablename__ = "saved_reports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    title = Column(String(255), nullable=False, default="Soil Health Analysis")
    farm_name = Column(String(255), nullable=True)
    location_name = Column(String(255), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    selected_crop = Column(String(100), nullable=True)

    # Structured JSON data
    soil_data = Column(JSON, nullable=False)
    deficiencies = Column(JSON, nullable=True, default=list)
    crop_scores = Column(JSON, nullable=True, default=list)
    fertilizer_options = Column(JSON, nullable=True, default=list)
    application_window = Column(JSON, nullable=True)
    evidence = Column(JSON, nullable=True, default=list)

    # Explanation text and provenance
    explanation = Column(Text, nullable=True)
    llm_provider = Column(String(50), nullable=True)
    llm_model = Column(String(100), nullable=True)
    is_llm_fallback = Column(Boolean, default=True, nullable=False)

    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        onupdate=lambda: datetime.datetime.now(datetime.timezone.utc),
        nullable=False,
    )

    user = relationship("User", back_populates="reports")
