"""Agent 1 - Soil & Crop Recommendation Agent.

Combines soil data + (optional) selected crop + season with the
deterministic engine and RAG evidence. Does NOT call an LLM directly -
it produces structured facts that the LLM layer later explains.
"""
from __future__ import annotations

from typing import List, Optional
from app.models.soil import SoilReport
from app.models.recommendation import Deficiency, FertilizerOption, Evidence
from app.models.crop import CropScore
from app.engine import crop_scorer, fertilizer_optimizer, soil_classifier
from app.services.crop_service import get_crop
from app.rag.retriever import retrieve, retrieve_for_recommendation


class SoilAgentResult:
    def __init__(
        self,
        deficiencies: List[Deficiency],
        crop_scores: List[CropScore],
        fertilizer_options: List[FertilizerOption],
        evidence: List[Evidence],
        contradiction: Optional[str],
        contradictions: List[str] = None,
        missing_warnings: List[str] = None,
    ):
        self.deficiencies = deficiencies
        self.crop_scores = crop_scores
        self.fertilizer_options = fertilizer_options
        self.evidence = evidence
        self.contradiction = contradiction
        self.contradictions = contradictions or ([contradiction] if contradiction else [])
        self.missing_warnings = missing_warnings or []


def run_soil_agent(
    soil: SoilReport,
    selected_crop: Optional[str],
    season: Optional[str],
    user_question: Optional[str],
    prefer_organic: bool = False,
) -> SoilAgentResult:
    classification = soil_classifier.classify_all_parameters(soil)
    deficiencies = classification["deficiencies"]
    missing_warnings = classification["missing_warnings"]

    if selected_crop:
        crop = get_crop(selected_crop)
        crop_scores = [crop_scorer.score_crop(soil, crop, season)] if crop else []
    else:
        crop_scores = crop_scorer.rank_crops(soil, season)

    fertilizer_options = fertilizer_optimizer.recommend_fertilizers(
        deficiencies, prefer_organic=prefer_organic, soil=soil, selected_crop=selected_crop
    )

    all_contradictions = fertilizer_optimizer.detect_all_contradictions(
        soil=soil, deficiencies=deficiencies, user_question=user_question, selected_crop=selected_crop
    )
    user_contradiction = fertilizer_optimizer.check_contradiction(user_question, deficiencies) if user_question else None

    # Retrieve grounded agricultural evidence from the indexed knowledge base
    evidence = retrieve_for_recommendation(
        soil=soil,
        selected_crop=selected_crop,
        deficiencies=deficiencies,
        user_question=user_question,
        top_k=4,
    )

    return SoilAgentResult(
        deficiencies=deficiencies,
        crop_scores=crop_scores,
        fertilizer_options=fertilizer_options,
        evidence=evidence,
        contradiction=user_contradiction,
        contradictions=all_contradictions,
        missing_warnings=missing_warnings,
    )
