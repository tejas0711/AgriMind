from __future__ import annotations

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response schema."""
    status: str = Field(default="healthy", description="Application health status")
    service: str = Field(default="AgriMind API", description="Service identifier")
    version: str = Field(default="0.1.0", description="API semantic version")
    timestamp: str = Field(description="ISO-8601 server timestamp")


class SystemCapabilities(BaseModel):
    """System features and capabilities description."""
    rag_indexed: bool
    weather_integration: bool
    deterministic_engine: bool
    llm_openai_configured: bool
    llm_gemini_configured: bool
    llm_openrouter_configured: bool
    local_llm_configured: bool


class SystemInfoResponse(BaseModel):
    """System information and metadata."""
    service: str
    version: str
    description: str
    supported_languages: List[str]
    supported_crops: List[str]
    core_nutrients: List[str]
    micronutrients: List[str]
    capabilities: SystemCapabilities


class ErrorResponse(BaseModel):
    """Standardized API error response format."""
    detail: str = Field(description="Human-readable error description")
    status_code: int = Field(description="HTTP status code")
    error_type: Optional[str] = Field(default=None, description="Category of error")
