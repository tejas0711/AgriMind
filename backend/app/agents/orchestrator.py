"""Agent Orchestrator.

Soil PDF -> Structured Soil Data -> [Soil/Crop Agent, Weather Agent] ->
Recommendation Engine outputs -> LLM explanation -> RecommendationResponse.

Coordinates independent domain agents (Soil/Crop and Weather), records partial failures
transparently without crashing the overall analysis, and ensures no fabricated forecasts.
"""
from __future__ import annotations

from typing import Optional, List
from app.models.soil import SoilReport
from app.models.recommendation import RecommendationResponse, WhyThisRecommendation
from app.agents.soil_agent import run_soil_agent
from app.agents.weather_agent import run_weather_agent
from app.services import llm_service
from app.engine.soil_classifier import RULE_SOURCES


async def orchestrate(
    soil: SoilReport,
    selected_crop: Optional[str] = None,
    season: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    location_name: Optional[str] = None,
    user_question: Optional[str] = None,
    prefer_organic: bool = False,
    language: str = "en",
) -> RecommendationResponse:
    partial_failures: List[str] = []

    # 1. Soil & Crop Analysis Agent
    soil_result = run_soil_agent(soil, selected_crop, season, user_question, prefer_organic)

    # 2. Weather & Application Timing Agent
    needs_application = len(soil_result.fertilizer_options) > 0
    application_window = await run_weather_agent(
        latitude=latitude,
        longitude=longitude,
        location_name=location_name,
        needs_application=needs_application,
    )

    resolved_location = location_name
    if application_window:
        if application_window.location_name:
            resolved_location = application_window.location_name
        if not application_window.is_available:
            partial_failures.append(
                f"Weather Analysis: {application_window.reason}"
            )

    contradictions = soil_result.contradictions
    confidence = soil.completeness() if hasattr(soil, "completeness") else 0.5
    if contradictions:
        confidence = min(confidence, 0.6)
    if application_window and not application_window.is_available:
        # Slight discount on overall confidence when weather cannot be verified
        confidence = max(0.2, confidence * 0.9)

    weather_factor = None
    if application_window:
        weather_factor = f"{application_window.apply_today}: {application_window.reason}"

    rule_sources = list(RULE_SOURCES.values())
    uncertainty_notes = (
        f"{len(soil_result.missing_warnings)} soil properties were not analyzed; results reflect available laboratory data only."
        if soil_result.missing_warnings else None
    )

    why = WhyThisRecommendation(
        reason_soil=_build_soil_reason(soil_result),
        evidence=soil_result.evidence,
        weather_factor=weather_factor,
        confidence=round(confidence, 2),
        contradictions=contradictions,
        missing_warnings=soil_result.missing_warnings,
        uncertainty_notes=uncertainty_notes,
        provisional_notice="Dosages and suitability scores are rule-based guidelines. Consult local KVK before large-scale field application.",
        rule_sources=rule_sources,
    )

    llm_explanation = None
    llm_provider = None
    llm_model = None
    is_llm_fallback = False

    try:
        explanation_res = await llm_service.generate_explanation_result(
            soil=soil,
            deficiencies=soil_result.deficiencies,
            crop_scores=soil_result.crop_scores,
            fertilizer_options=soil_result.fertilizer_options,
            application_window=application_window,
            evidence=soil_result.evidence,
            user_question=user_question,
            contradictions=contradictions,
            language=language,
        )
        llm_explanation = explanation_res.explanation
        llm_provider = explanation_res.provider
        llm_model = explanation_res.model
        is_llm_fallback = explanation_res.is_fallback
    except Exception as exc:
        partial_failures.append(f"AI Explanation: Natural-language synthesis was unavailable ({exc}). Structured rules remain fully valid.")
        llm_explanation = None
        is_llm_fallback = True

    return RecommendationResponse(
        soil=soil,
        deficiencies=soil_result.deficiencies,
        crop_scores=soil_result.crop_scores,
        fertilizer_options=soil_result.fertilizer_options,
        application_window=application_window,
        why=why,
        llm_explanation=llm_explanation,
        llm_provider=llm_provider,
        llm_model=llm_model,
        is_llm_fallback=is_llm_fallback,
        language=language,
        missing_warnings=soil_result.missing_warnings,
        contradictions=contradictions,
        partial_failures=partial_failures,
        location_name=resolved_location,
    )


def _build_soil_reason(soil_result) -> str:
    low = [d.detail for d in soil_result.deficiencies if d.status == "LOW"]
    high = [d.detail for d in soil_result.deficiencies if d.status == "HIGH" and d.nutrient in ["nitrogen", "phosphorus", "potassium", "ph", "electrical_conductivity"]]
    parts = []
    if low:
        parts.append(" ".join(low))
    if high:
        parts.append(" ".join(high))
    if parts:
        return " ".join(parts)
    return "No critical nutrient deficiencies detected from available soil measurements."
