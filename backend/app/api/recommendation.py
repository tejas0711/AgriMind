"""API endpoints for agricultural recommendations and multi-agent analysis.

Exposes:
  - `POST /api/recommendations` (Primary endpoint)
  - `POST /api/recommendation` (Plural/Singular alias compatibility)
  - `POST /api/analysis` (Coordinated multi-agent analysis endpoint)
"""
from __future__ import annotations

from typing import Optional
from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.models.soil import SoilReport
from app.models.recommendation import RecommendationResponse
from app.agents.orchestrator import orchestrate
from app.agents.weather_agent import run_weather_agent
from app.engine.recommendation_engine import evaluate_recommendations
from app.services.weather_service import geocode_location
from app.services.i18n import normalize_language

router = APIRouter(tags=["recommendations"])


class RecommendationRequest(BaseModel):
    soil: SoilReport = Field(description="Validated soil report measurements")
    selected_crop: Optional[str] = Field(default=None, description="Optional target crop name (e.g. 'Tomato', 'Wheat')")
    season: Optional[str] = Field(default=None, description="Optional current growing season ('kharif', 'rabi', 'zaid')")
    location_name: Optional[str] = Field(default=None, description="Optional farm location name (e.g. 'Nashik, Maharashtra')")
    latitude: Optional[float] = Field(default=None, description="Optional farm latitude")
    longitude: Optional[float] = Field(default=None, description="Optional farm longitude")
    user_question: Optional[str] = Field(default=None, description="Optional farmer question or specific inquiry")
    prefer_organic: bool = Field(default=False, description="Whether to prioritize organic soil amendments")
    language: str = Field(default="en", description="Target language code: 'en', 'hi', 'mr'")
    deterministic_only: bool = Field(default=False, description="If true, executes pure rule calculation without LLM synthesis")


async def _handle_recommendation(req: RecommendationRequest) -> RecommendationResponse:
    latitude, longitude = req.latitude, req.longitude

    # 1. Deterministic-only execution mode
    if req.deterministic_only:
        app_window = await run_weather_agent(
            latitude=latitude,
            longitude=longitude,
            location_name=req.location_name,
            needs_application=True,
        )
        forecast_days = app_window.forecast_days if app_window else None
        res = evaluate_recommendations(
            soil=req.soil,
            selected_crop=req.selected_crop,
            season=req.season,
            forecast_days=forecast_days,
            location_name=app_window.location_name if app_window else req.location_name,
            latitude=latitude,
            longitude=longitude,
            fetched_at=app_window.fetched_at if app_window else None,
            user_question=req.user_question,
            prefer_organic=req.prefer_organic,
            language=normalize_language(req.language),
        )
        if app_window and not app_window.is_available:
            res.partial_failures.append(f"Weather Analysis: {app_window.reason}")
        return res

    # 2. Standard multi-agent orchestration
    return await orchestrate(
        soil=req.soil,
        selected_crop=req.selected_crop,
        season=req.season,
        latitude=latitude,
        longitude=longitude,
        location_name=req.location_name,
        user_question=req.user_question,
        prefer_organic=req.prefer_organic,
        language=normalize_language(req.language),
    )


@router.post("/api/recommendations", response_model=RecommendationResponse)
async def get_recommendations(req: RecommendationRequest) -> RecommendationResponse:
    """Primary endpoint: returns rule-derived crop suitability, fertilizer options, weather window, and reasoning."""
    return await _handle_recommendation(req)


@router.post("/api/recommendation", response_model=RecommendationResponse)
async def get_recommendation_alias(req: RecommendationRequest) -> RecommendationResponse:
    """Alias endpoint for singular compatibility."""
    return await _handle_recommendation(req)


@router.post("/api/analysis", response_model=RecommendationResponse)
@router.post("/api/recommendations/analyze", response_model=RecommendationResponse)
async def analyze_full_farm(req: RecommendationRequest) -> RecommendationResponse:
    """Coordinated analysis endpoint: joins SoilAgent, WeatherAgent, and Recommendation Engine."""
    return await _handle_recommendation(req)
