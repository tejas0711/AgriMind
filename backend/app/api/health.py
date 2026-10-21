from __future__ import annotations

from datetime import datetime, timezone
from fastapi import APIRouter
from app.core.config import get_settings
from app.models.system import HealthResponse, SystemInfoResponse, SystemCapabilities
from app.services.crop_service import load_crop_requirements
from app.services.i18n import SUPPORTED_LANGUAGES

router = APIRouter(prefix="/api", tags=["system"])


@router.get("/health", response_model=HealthResponse)
async def get_health() -> HealthResponse:
    """Returns the current health status and semantic version of AgriMind API."""
    settings = get_settings()
    return HealthResponse(
        status="healthy",
        service=settings.app_name,
        version=settings.app_version,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@router.get("/info", response_model=SystemInfoResponse)
async def get_info() -> SystemInfoResponse:
    """Returns application capabilities, supported crops, nutrients, and languages."""
    settings = get_settings()

    # Safely check RAG vector index count
    rag_ready = False
    try:
        from app.rag import vector_store
        rag_ready = vector_store.count() > 0
    except Exception:
        rag_ready = False

    crops = [c.name for c in load_crop_requirements()]

    capabilities = SystemCapabilities(
        rag_indexed=rag_ready,
        weather_integration=True,
        deterministic_engine=True,
        llm_openai_configured=bool(settings.openai_api_key),
        llm_gemini_configured=bool(settings.gemini_api_key),
        llm_openrouter_configured=bool(settings.openrouter_api_key),
        local_llm_configured=bool(settings.llm_base_url),
    )

    return SystemInfoResponse(
        service=settings.app_name,
        version=settings.app_version,
        description=settings.app_description,
        supported_languages=list(SUPPORTED_LANGUAGES),
        supported_crops=crops,
        core_nutrients=["nitrogen", "phosphorus", "potassium", "ph", "organic_carbon", "electrical_conductivity"],
        micronutrients=["zinc", "iron", "sulphur", "boron"],
        capabilities=capabilities,
    )
