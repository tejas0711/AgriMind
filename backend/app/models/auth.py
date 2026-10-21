from __future__ import annotations

import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field


# ---------------------------------------------------------------------------
# User & Authentication Schemas
# ---------------------------------------------------------------------------

class UserRegister(BaseModel):
    """Registration request payload."""
    email: EmailStr
    password: str = Field(min_length=6, description="Password must be at least 6 characters")
    full_name: Optional[str] = Field(default=None, max_length=255)


class UserLogin(BaseModel):
    """Login request payload."""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Public user profile response."""
    id: int
    email: str
    full_name: Optional[str] = None
    is_active: bool = True
    created_at: datetime.datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Authentication success response with bearer token."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ---------------------------------------------------------------------------
# Saved Report Schemas
# ---------------------------------------------------------------------------

class ReportSaveRequest(BaseModel):
    """Payload to save an analyzed soil report and recommendations."""
    title: Optional[str] = "Soil Health Analysis"
    farm_name: Optional[str] = None
    location_name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    selected_crop: Optional[str] = None

    soil_data: Dict[str, Any]
    deficiencies: List[Dict[str, Any]] = Field(default_factory=list)
    crop_scores: List[Dict[str, Any]] = Field(default_factory=list)
    fertilizer_options: List[Dict[str, Any]] = Field(default_factory=list)
    application_window: Optional[Dict[str, Any]] = None
    evidence: List[Dict[str, Any]] = Field(default_factory=list)

    explanation: Optional[str] = None
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    is_llm_fallback: bool = True
    notes: Optional[str] = None


class ReportSummary(BaseModel):
    """Lightweight summary of a saved report for history lists."""
    id: int
    user_id: int
    title: str
    farm_name: Optional[str] = None
    location_name: Optional[str] = None
    selected_crop: Optional[str] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True


class ReportResponse(BaseModel):
    """Complete detail of a saved soil report."""
    id: int
    user_id: int
    title: str
    farm_name: Optional[str] = None
    location_name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    selected_crop: Optional[str] = None

    soil_data: Dict[str, Any]
    deficiencies: List[Dict[str, Any]] = Field(default_factory=list)
    crop_scores: List[Dict[str, Any]] = Field(default_factory=list)
    fertilizer_options: List[Dict[str, Any]] = Field(default_factory=list)
    application_window: Optional[Dict[str, Any]] = None
    evidence: List[Dict[str, Any]] = Field(default_factory=list)

    explanation: Optional[str] = None
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    is_llm_fallback: bool = True
    notes: Optional[str] = None

    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True
