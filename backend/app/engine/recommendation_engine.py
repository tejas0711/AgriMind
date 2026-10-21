"""Core Deterministic Recommendation Engine for AgriMind.

Executes complete agronomic evaluation without calling an LLM or external AI API:
  1. Classifies soil nutrient status using configurable Soil Health Card / ICAR standards.
  2. Evaluates crop suitability scoring and ranks crops with granular factor diagnosis.
  3. Recommends relevant chemical and organic amendments with purposes and cautions.
  4. Detects nutrient, pH, and physiological contradictions.
  5. Computes missing input warnings and uncertainty metrics.
  6. Produces structured, source-attributed recommendation objects.
"""
from __future__ import annotations

from typing import List, Optional, Dict, Any
from app.models.soil import SoilReport
from app.models.crop import CropScore
from app.models.recommendation import (
    Deficiency,
    FertilizerOption,
    ApplicationWindow,
    WhyThisRecommendation,
    RecommendationResponse,
    Evidence,
)
from app.engine.soil_classifier import classify_all_parameters, RULE_SOURCES
from app.engine.crop_scorer import score_crop, rank_crops
from app.engine.fertilizer_optimizer import recommend_fertilizers, detect_all_contradictions
from app.engine.application_window import assess_application_window
from app.services.crop_service import get_crop
from app.rag.retriever import retrieve, retrieve_for_recommendation


def evaluate_recommendations(
    soil: SoilReport,
    selected_crop: Optional[str] = None,
    season: Optional[str] = None,
    forecast_days: Optional[List[Dict[str, Any]]] = None,
    location_name: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    fetched_at: Optional[str] = None,
    user_question: Optional[str] = None,
    prefer_organic: bool = False,
    language: str = "en",
) -> RecommendationResponse:
    """Pure deterministic agricultural recommendation pipeline.

    Callable standalone with zero external network or LLM dependencies.
    Identical inputs and identical rules are guaranteed to produce identical results.
    """
    # 1. Soil Classification & Missing Parameter Detection
    classification = classify_all_parameters(soil)
    deficiencies: List[Deficiency] = classification["deficiencies"]
    missing_warnings: List[str] = classification["missing_warnings"]
    data_completeness: float = classification["data_completeness"]

    # 2. Crop Suitability Evaluation
    if selected_crop:
        target_crop_obj = get_crop(selected_crop)
        if target_crop_obj:
            crop_scores = [score_crop(soil, target_crop_obj, season)]
        else:
            # Fallback to ranked list if crop name unrecognized
            crop_scores = rank_crops(soil, season, top_n=5)
    else:
        crop_scores = rank_crops(soil, season, top_n=5)

    # 3. Fertilizer & Amendment Selection (with Contradiction Guard)
    fertilizer_options: List[FertilizerOption] = recommend_fertilizers(
        deficiencies=deficiencies,
        prefer_organic=prefer_organic,
        soil=soil,
        selected_crop=selected_crop,
    )

    # 4. Multi-Layer Contradiction Detection
    contradictions = detect_all_contradictions(
        soil=soil,
        deficiencies=deficiencies,
        user_question=user_question,
        selected_crop=selected_crop,
    )

    # 5. Weather Application Window Assessment
    needs_application = len(fertilizer_options) > 0
    application_window: Optional[ApplicationWindow] = None
    if forecast_days is not None:
        application_window = assess_application_window(
            forecast_days=forecast_days,
            needs_application=needs_application,
            location_name=location_name,
            latitude=latitude,
            longitude=longitude,
            fetched_at=fetched_at,
        )

    # 6. Evidence Retrieval (RAG grounding with rich metadata)
    evidence: List[Evidence] = []
    try:
        evidence = retrieve_for_recommendation(
            soil=soil,
            selected_crop=selected_crop,
            deficiencies=deficiencies,
            user_question=user_question,
            top_k=4,
        )
    except Exception:
        evidence = []

    # 7. Confidence & Uncertainty Computation
    confidence = data_completeness
    if contradictions:
        confidence = min(confidence, 0.6)
    if not soil.nitrogen or not soil.phosphorus or not soil.potassium:
        confidence = min(confidence, 0.7)
    confidence = round(max(0.2, min(1.0, confidence)), 2)

    # 8. Compile Soil Health Reasoning Summary
    low_details = [d.detail for d in deficiencies if d.status == "LOW"]
    high_details = [d.detail for d in deficiencies if d.status == "HIGH" and d.nutrient in ["nitrogen", "phosphorus", "potassium", "ph", "electrical_conductivity"]]

    reason_parts = []
    if low_details:
        reason_parts.append("Identified deficiencies: " + " ".join(low_details))
    if high_details:
        reason_parts.append("Nutrient safeguards: " + " ".join(high_details))
    if not reason_parts:
        reason_parts.append("Core fertility parameters are within normal maintenance ranges.")
    reason_soil = " ".join(reason_parts)

    weather_factor = None
    if application_window:
        weather_factor = f"{application_window.apply_today}: {application_window.reason}"

    uncertainty_notes = None
    if missing_warnings:
        uncertainty_notes = f"{len(missing_warnings)} soil properties were not analyzed; recommendations reflect available data only."

    rule_sources = list(RULE_SOURCES.values())

    why = WhyThisRecommendation(
        reason_soil=reason_soil,
        evidence=evidence,
        weather_factor=weather_factor,
        confidence=confidence,
        contradictions=contradictions,
        missing_warnings=missing_warnings,
        uncertainty_notes=uncertainty_notes,
        provisional_notice="All dosages require local extension or KVK validation before field application.",
        rule_sources=rule_sources,
    )

    return RecommendationResponse(
        soil=soil,
        deficiencies=deficiencies,
        crop_scores=crop_scores,
        fertilizer_options=fertilizer_options,
        application_window=application_window,
        why=why,
        llm_explanation=None,
        language=language,
        missing_warnings=missing_warnings,
        contradictions=contradictions,
        location_name=location_name,
    )
