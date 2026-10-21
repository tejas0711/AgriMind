"""AgriMind Deterministic Agricultural Recommendation Engine.

Provides pure Python soil classification, crop suitability scoring, fertilizer selection,
application timing assessment, and contradiction checking.
"""
from app.engine.soil_classifier import (
    classify_all_parameters,
    classify_macronutrient,
    classify_micronutrient,
    classify_soil_reaction,
    classify_salinity,
    DEFAULT_MACRO_THRESHOLDS,
    DEFAULT_MICRONUTRIENT_CRITICAL,
    RULE_SOURCES,
)
from app.engine.crop_scorer import score_crop, rank_crops
from app.engine.fertilizer_optimizer import (
    detect_deficiencies,
    recommend_fertilizers,
    check_contradiction,
    detect_all_contradictions,
)
from app.engine.application_window import assess_application_window
from app.engine.recommendation_engine import evaluate_recommendations

__all__ = [
    "classify_all_parameters",
    "classify_macronutrient",
    "classify_micronutrient",
    "classify_soil_reaction",
    "classify_salinity",
    "DEFAULT_MACRO_THRESHOLDS",
    "DEFAULT_MICRONUTRIENT_CRITICAL",
    "RULE_SOURCES",
    "score_crop",
    "rank_crops",
    "detect_deficiencies",
    "recommend_fertilizers",
    "check_contradiction",
    "detect_all_contradictions",
    "assess_application_window",
    "evaluate_recommendations",
]
