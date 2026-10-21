"""Comprehensive unit tests for AgriMind's Deterministic Agricultural Recommendation Engine.

Tests:
  1. Soil nutrient thresholds (NPK, OC, micronutrients, pH, EC).
  2. Unit conversions (kg/ha, ppm, lbs/acre, %, g/kg).
  3. Missing soil properties and uncertainty flags.
  4. Crop scoring arithmetic, categories, positive & limiting factors.
  5. Contradiction detection (high nutrient blocking, alkaline lime block, legume nodulation).
  6. Organic vs chemical amendment selection, purpose, and cautions.
  7. Strict safety: zero chemical pesticide recommendations.
  8. Determinism: identical inputs & rules produce identical results across runs.
  9. Real API endpoint verification: POST /api/recommendations and POST /api/recommendation.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.soil import SoilReport, SoilValue
from app.engine.soil_classifier import (
    classify_macronutrient,
    classify_micronutrient,
    classify_soil_reaction,
    classify_salinity,
    classify_all_parameters,
    convert_to_standard_unit,
)
from app.engine.crop_scorer import score_crop, rank_crops
from app.services.crop_service import get_crop
from app.engine.fertilizer_optimizer import (
    detect_deficiencies,
    recommend_fertilizers,
    check_contradiction,
    detect_all_contradictions,
)
from app.engine.recommendation_engine import evaluate_recommendations


client = TestClient(app)


# =====================================================================
# 1. Nutrient Thresholds & Status Classification
# =====================================================================

def test_nitrogen_threshold_classification():
    # Low: < 280 kg/ha
    d_low = classify_macronutrient("nitrogen", 180.0, "kg/ha")
    assert d_low.status == "LOW"
    assert "LOW" in d_low.detail
    assert d_low.rule_source is not None

    # Medium: 280 - 560 kg/ha
    d_med = classify_macronutrient("nitrogen", 350.0, "kg/ha")
    assert d_med.status == "MEDIUM"

    # High: > 560 kg/ha
    d_high = classify_macronutrient("nitrogen", 620.0, "kg/ha")
    assert d_high.status == "HIGH"
    assert "HIGH" in d_high.detail
    assert "luxuriance" in d_high.agronomic_implication.lower() or "excess" in d_high.agronomic_implication.lower()


def test_phosphorus_and_potassium_thresholds():
    # Phosphorus: Low < 10, Medium 10-25, High > 25
    assert classify_macronutrient("phosphorus", 8.0, "kg/ha").status == "LOW"
    assert classify_macronutrient("phosphorus", 18.0, "kg/ha").status == "MEDIUM"
    assert classify_macronutrient("phosphorus", 32.0, "kg/ha").status == "HIGH"

    # Potassium: Low < 108, Medium 108-280, High > 280
    assert classify_macronutrient("potassium", 95.0, "kg/ha").status == "LOW"
    assert classify_macronutrient("potassium", 210.0, "kg/ha").status == "MEDIUM"
    assert classify_macronutrient("potassium", 320.0, "kg/ha").status == "HIGH"


def test_micronutrient_critical_limits():
    # Zinc critical: 0.6 ppm
    assert classify_micronutrient("zinc", 0.45, "ppm").status == "LOW"  # Deficient
    assert classify_micronutrient("zinc", 0.85, "ppm").status == "HIGH" # Sufficient

    # Iron critical: 4.5 ppm
    assert classify_micronutrient("iron", 3.2, "ppm").status == "LOW"
    assert classify_micronutrient("iron", 5.5, "ppm").status == "HIGH"

    # Boron critical: 0.5 ppm
    assert classify_micronutrient("boron", 0.3, "ppm").status == "LOW"
    assert classify_micronutrient("boron", 0.7, "ppm").status == "HIGH"


def test_soil_reaction_ph_classification():
    # Strongly acidic: < 5.5
    d_acid = classify_soil_reaction(5.1)
    assert d_acid.status == "LOW"
    assert "acidic" in d_acid.detail.lower()
    assert "liming" in d_acid.agronomic_implication.lower()

    # Optimal neutral: 6.5 - 7.5
    d_neutral = classify_soil_reaction(6.8)
    assert d_neutral.status == "MEDIUM"
    assert "neutral" in d_neutral.detail.lower()

    # Alkaline: > 8.0
    d_alkaline = classify_soil_reaction(8.4)
    assert d_alkaline.status == "HIGH"
    assert "alkaline" in d_alkaline.detail.lower()
    assert "gypsum" in d_alkaline.agronomic_implication.lower()


def test_salinity_ec_classification():
    # Normal: < 1.0 dS/m
    assert classify_salinity(0.6).status == "LOW"

    # Critical: 1.0 - 2.0 dS/m
    assert classify_salinity(1.4).status == "MEDIUM"

    # Saline: > 2.0 dS/m
    d_saline = classify_salinity(2.8)
    assert d_saline.status == "HIGH"
    assert "salin" in d_saline.detail.lower() or "high" in d_saline.detail.lower()


# =====================================================================
# 2. Supported Unit Normalization & Conversions
# =====================================================================

def test_unit_conversions_to_standard_kg_ha():
    # 100 ppm Nitrogen ≈ 224 kg/ha
    val_n, unit_n = convert_to_standard_unit("nitrogen", 100.0, "ppm")
    assert unit_n == "kg/ha"
    assert val_n == 224.0

    # 100 lbs/acre Nitrogen ≈ 112 kg/ha
    val_lb, unit_lb = convert_to_standard_unit("nitrogen", 100.0, "lbs/acre")
    assert unit_lb == "kg/ha"
    assert val_lb == 112.0

    # Organic carbon 6 g/kg = 0.6%
    val_oc, unit_oc = convert_to_standard_unit("organic_carbon", 6.0, "g/kg")
    assert unit_oc == "%"
    assert val_oc == 0.6


# =====================================================================
# 3. Missing Soil Properties & Uncertainty Tracking
# =====================================================================

def test_missing_parameters_tracked_with_uncertainty():
    # Only nitrogen and pH provided
    soil = SoilReport(
        nitrogen=SoilValue(value=190.0, unit="kg/ha"),
        ph=SoilValue(value=6.5),
    )
    classification = classify_all_parameters(soil)
    warnings = classification["missing_warnings"]

    # Verify missing fields produce clear warnings
    assert any("phosphorus" in w.lower() for w in warnings)
    assert any("potassium" in w.lower() for w in warnings)
    assert any("zinc" in w.lower() for w in warnings)
    assert classification["data_completeness"] < 0.5


def test_recommendation_handles_incomplete_soil_report_neutrally():
    soil = SoilReport(nitrogen=SoilValue(value=180.0, unit="kg/ha"))
    res = evaluate_recommendations(soil)

    assert res.soil.nitrogen.value == 180.0
    assert len(res.missing_warnings) > 0
    assert res.why.confidence <= 0.7
    assert res.why.uncertainty_notes is not None


# =====================================================================
# 4. Crop Suitability Scoring & Factors
# =====================================================================

def test_crop_scorer_returns_positive_and_limiting_factors():
    soil = SoilReport(
        nitrogen=SoilValue(value=160.0, unit="kg/ha"),
        phosphorus=SoilValue(value=22.0, unit="kg/ha"),
        potassium=SoilValue(value=210.0, unit="kg/ha"),
        ph=SoilValue(value=6.4),
        organic_carbon=SoilValue(value=0.65, unit="%"),
    )
    tomato = get_crop("Tomato")
    assert tomato is not None

    score_res = score_crop(soil, tomato, current_season="rabi")
    assert score_res.score >= 80.0
    assert score_res.category == "Highly Suitable"
    assert len(score_res.positive_factors) >= 3
    assert "ph" in score_res.factor_breakdown


def test_crop_scorer_penalizes_unfavorable_season_and_salinity():
    soil = SoilReport(
        nitrogen=SoilValue(value=150.0, unit="kg/ha"),
        ph=SoilValue(value=6.5),
        electrical_conductivity=SoilValue(value=2.4, unit="dS/m"),  # High salinity
    )
    tomato = get_crop("Tomato")
    score_res = score_crop(soil, tomato, current_season="kharif")  # Unfavorable season for tomato

    assert score_res.season_fit is False
    assert any("season" in lf.lower() for lf in score_res.limiting_factors)
    assert any("salinity" in lf.lower() or "conductivity" in lf.lower() for lf in score_res.limiting_factors)
    assert score_res.score < 60.0


def test_legume_crop_not_penalized_for_low_soil_nitrogen():
    soil = SoilReport(
        nitrogen=SoilValue(value=50.0, unit="kg/ha"),  # Low for cereals
        ph=SoilValue(value=6.8),
        phosphorus=SoilValue(value=20.0, unit="kg/ha"),
        potassium=SoilValue(value=150.0, unit="kg/ha"),
    )
    soybean = get_crop("Soybean")
    score_res = score_crop(soil, soybean, current_season="kharif")

    # Legume nitrogen fixation credited
    assert score_res.n_fit is True
    assert any("legume" in pf.lower() for pf in score_res.positive_factors)


# =====================================================================
# 5. Contradiction Detection & Safeguards
# =====================================================================

def test_high_potassium_report_blocks_potash_fertilizer():
    soil = SoilReport(
        potassium=SoilValue(value=340.0, unit="kg/ha"),  # HIGH
        nitrogen=SoilValue(value=150.0, unit="kg/ha"),   # LOW
    )
    deficiencies = detect_deficiencies(soil)
    options = recommend_fertilizers(deficiencies, soil=soil)

    # Nitrogen should be recommended, but Potassium must NOT be recommended
    assert any(o.nutrient == "nitrogen" for o in options)
    assert not any(o.nutrient == "potassium" for o in options)
    assert not any("potash" in o.name.lower() or "mop" in o.name.lower() for o in options)


def test_user_query_contradiction_detected_for_high_nutrient():
    soil = SoilReport(potassium=SoilValue(value=350.0, unit="kg/ha"))
    deficiencies = detect_deficiencies(soil)
    contradiction = check_contradiction("Should I apply muriate of potash?", deficiencies)

    assert contradiction is not None
    assert "potassium" in contradiction.lower()
    assert "already high" in contradiction.lower()


def test_liming_blocked_on_alkaline_soil():
    soil = SoilReport(ph=SoilValue(value=8.4))
    deficiencies = detect_deficiencies(soil)
    contradictions = detect_all_contradictions(soil, deficiencies, user_question="Can I add agricultural lime?")

    assert any("lime" in c.lower() or "alkaline" in c.lower() for c in contradictions)

    # Verify recommendations for alkaline pH suggest gypsum or green manure, never lime
    options = recommend_fertilizers(deficiencies, soil=soil)
    assert any("gypsum" in o.name.lower() for o in options)
    assert not any("lime" in o.name.lower() or "calcium carbonate" in o.name.lower() for o in options)


# =====================================================================
# 6. Recommendation Selection, Purposes, Cautions, & Organic Mode
# =====================================================================

def test_fertilizer_options_include_purpose_cautions_and_provisional():
    soil = SoilReport(
        nitrogen=SoilValue(value=140.0, unit="kg/ha"),
        zinc=SoilValue(value=0.38, unit="ppm"),
    )
    deficiencies = detect_deficiencies(soil)
    options = recommend_fertilizers(deficiencies, soil=soil)

    for opt in options:
        assert opt.purpose is not None and len(opt.purpose) > 5
        assert opt.application_notes is not None and len(opt.application_notes) > 5
        assert opt.cautions is not None and len(opt.cautions) > 5
        assert opt.source is not None
        assert opt.is_provisional is True


def test_prefer_organic_prioritizes_organic_amendments():
    soil = SoilReport(nitrogen=SoilValue(value=150.0, unit="kg/ha"))
    deficiencies = detect_deficiencies(soil)

    organic_first = recommend_fertilizers(deficiencies, prefer_organic=True, soil=soil)
    assert organic_first[0].type == "organic"

    chemical_first = recommend_fertilizers(deficiencies, prefer_organic=False, soil=soil)
    assert chemical_first[0].type == "chemical"


def test_strict_safety_no_chemical_pesticides_recommended():
    soil = SoilReport(
        nitrogen=SoilValue(value=100.0, unit="kg/ha"),
        phosphorus=SoilValue(value=5.0, unit="kg/ha"),
        potassium=SoilValue(value=80.0, unit="kg/ha"),
        zinc=SoilValue(value=0.3, unit="ppm"),
        iron=SoilValue(value=2.0, unit="ppm"),
    )
    deficiencies = detect_deficiencies(soil)
    options = recommend_fertilizers(deficiencies, soil=soil)

    banned_terms = ["chlorpyrifos", "monocrotophos", "glyphosate", "imidacloprid", "pesticide", "fungicide", "insecticide"]
    for opt in options:
        opt_text = f"{opt.name} {opt.purpose} {opt.application_notes} {opt.cautions}".lower()
        for banned in banned_terms:
            assert banned not in opt_text, f"Safety violation: found '{banned}' in {opt.name}"


# =====================================================================
# 7. Pure Determinism Test (Identical Inputs = Identical Outputs)
# =====================================================================

def test_recommendation_engine_is_strictly_deterministic():
    soil = SoilReport(
        nitrogen=SoilValue(value=175.0, unit="kg/ha"),
        phosphorus=SoilValue(value=12.0, unit="kg/ha"),
        potassium=SoilValue(value=220.0, unit="kg/ha"),
        ph=SoilValue(value=6.7),
        organic_carbon=SoilValue(value=0.55, unit="%"),
        zinc=SoilValue(value=0.48, unit="ppm"),
    )

    run_1 = evaluate_recommendations(soil, selected_crop="Tomato", season="rabi")
    run_2 = evaluate_recommendations(soil, selected_crop="Tomato", season="rabi")

    # Serialize to JSON and assert exact byte-for-byte equivalence
    assert run_1.model_dump_json() == run_2.model_dump_json()


# =====================================================================
# 8. API Endpoint Verification (POST /api/recommendations)
# =====================================================================

def test_api_recommendations_endpoint():
    payload = {
        "soil": {
            "nitrogen": {"value": 170.0, "unit": "kg/ha"},
            "phosphorus": {"value": 14.0, "unit": "kg/ha"},
            "potassium": {"value": 240.0, "unit": "kg/ha"},
            "ph": {"value": 6.8},
            "organic_carbon": {"value": 0.52, "unit": "%"},
        },
        "selected_crop": "Tomato",
        "season": "rabi",
        "prefer_organic": True,
        "deterministic_only": True,
    }

    # Primary endpoint: POST /api/recommendations
    res = client.post("/api/recommendations", json=payload)
    assert res.status_code == 200
    data = res.json()

    assert "crop_scores" in data
    assert len(data["crop_scores"]) >= 1
    assert data["crop_scores"][0]["name"] == "Tomato"
    assert "fertilizer_options" in data
    assert "why" in data
    assert data["why"]["confidence"] > 0
    assert len(data["why"]["rule_sources"]) > 0

    # Plural/Singular Alias endpoint: POST /api/recommendation
    alias_res = client.post("/api/recommendation", json=payload)
    assert alias_res.status_code == 200
    alias_data = alias_res.json()
    assert alias_data["crop_scores"][0]["name"] == "Tomato"
