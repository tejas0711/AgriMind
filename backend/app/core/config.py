from __future__ import annotations

import os
from functools import lru_cache
from typing import List, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized application settings loaded from environment variables and .env file."""

    app_name: str = "AgriMind API"
    app_version: str = "0.1.0"
    app_description: str = "Multi-Agent AI Soil, Crop & Fertilizer Optimization System"
    debug: bool = False

    # CORS & Network
    frontend_origin: str = "http://localhost:5173"
    cors_origins: Union[str, List[str]] = Field(
        default="http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://localhost:4173,http://localhost:5174"
    )

    # LLM Providers (all optional; system uses deterministic fallback if absent)
    default_llm_provider: str = Field(default="openai", description="Preferred provider: openai, gemini, or openrouter")
    llm_timeout_seconds: float = 20.0
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"

    gemini_api_key: str | None = None
    gemini_model: str = "gemini-3.8-flash"

    openrouter_api_key: str | None = None
    openrouter_model: str = "openai/gpt-4o-mini"

    llm_base_url: str | None = None

    # Weather Service
    open_meteo_base_url: str = "https://api.open-meteo.com/v1/forecast"

    # Storage paths
    chroma_persist_dir: str = "./vector_db"
    upload_dir: str = "./uploads"

    # Database & Persistence (PostgreSQL primary with seamless SQLite fallback)
    database_url: str = Field(
        default="sqlite:///./agrimind.db",
        description="PostgreSQL connection string (e.g. postgresql://user:pass@localhost:5432/agrimind_db) or sqlite for local dev",
    )

    # JWT Authentication & Security
    jwt_secret_key: str = Field(
        default="agrimind-dev-jwt-secret-key-replace-in-production-09a8b7c6d5e4f3a2",
        description="HMAC secret key used to sign JWT access tokens",
    )
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440  # 24 hours

    # File upload validation limits
    max_upload_size_bytes: int = 10 * 1024 * 1024  # 10 MB default limit
    allowed_upload_extensions: Union[str, List[str]] = Field(default=".pdf")

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def get_cors_origins(self) -> list[str]:
        """Returns a sanitized list of allowed CORS origins."""
        origins = []
        if isinstance(self.cors_origins, str):
            origins = [o.strip() for o in self.cors_origins.split(",") if o.strip()]
        elif isinstance(self.cors_origins, list):
            origins = [str(o).strip() for o in self.cors_origins if str(o).strip()]

        if self.frontend_origin and self.frontend_origin not in origins:
            origins.append(self.frontend_origin.strip())

        # Ensure common local dev hosts are included
        defaults = [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:3000",
            "http://localhost:4173",
            "http://localhost:5174",
        ]
        for d in defaults:
            if d not in origins:
                origins.append(d)

        return origins


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
