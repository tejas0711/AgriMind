from __future__ import annotations

import logging
import os
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import get_settings
from app.db.base import Base

logger = logging.getLogger(__name__)

settings = get_settings()

db_url = os.getenv("DATABASE_URL") or settings.database_url
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

# Configure engine with pre-ping and appropriate connect_args
connect_args = {}
if db_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

try:
    engine = create_engine(
        db_url,
        pool_pre_ping=True,
        connect_args=connect_args,
    )
    # Probe connection
    with engine.connect() as conn:
        pass
except Exception as exc:
    logger.warning("Could not connect to configured DATABASE_URL (%s): %s. Falling back to local SQLite.", db_url, exc)
    db_url = "sqlite:///./agrimind.db"
    engine = create_engine(
        db_url,
        pool_pre_ping=True,
        connect_args={"check_same_thread": False},
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Initialize database tables according to defined models."""
    import app.db.models  # noqa: F401
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables verified/created on %s", db_url.split("@")[-1])


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a database session with guaranteed closure."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
