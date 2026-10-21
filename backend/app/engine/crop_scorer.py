"""Deterministic crop suitability scoring and limiting factor diagnosis.

Evaluates crop suitability on a 0-100 scale using soil parameters (pH, N, P, K, EC, OC)
and crop requirement benchmarks from data/knowledge/crops/crop_requirements.json.

Strictly deterministic: plain arithmetic without LLMs or external AI APIs.
Returns categorized suitability, positive contributing factors, limiting constraints,
and missing-parameter uncertainty notices.
"""
from __future__ import annotations

from typing import List, Optional
from app.models.soil import SoilReport
from app.models.crop import CropRequirement, CropScore
from app.services.crop_service import load_crop_requirements

# Factor weight distribution summing to 100
_WEIGHTS = {
    "ph": 30.0,
    "nitrogen": 20.0,
    "phosphorus": 15.0,
    "potassium": 15.0,
    "season": 20.0,
}

# Legume crops with symbiotic nitrogen fixation capability
LEGUME_CROPS = {"soybean", "chickpea (gram)", "chickpea", "groundnut", "lentil", "black gram", "green gram"}


def _determine_category(score: float) -> str:
    if score >= 80.0:
        return "Highly Suitable"
    if score >= 60.0:
        return "Moderately Suitable"
    if score >= 40.0:
        return "Marginally Suitable"
    return "Unsuitable"


def score_crop(
    soil: SoilReport,
    crop: CropRequirement,
    current_season: Optional[str] = None,
) -> CropScore:
    """Calculates deterministic suitability score (0-100) and factors for a crop."""
    reasons: List[str] = []
    positive_factors: List[str] = []
    limiting_factors: List[str] = []
    missing_factors: List[str] = []
    factor_breakdown: dict[str, float] = {}

    total_score = 0.0
    crop_name_lower = crop.name.strip().lower()
    is_legume = crop_name_lower in LEGUME_CROPS

    # -------------------------------------------------------------
    # 1. Soil Reaction (pH) Evaluation (Weight: 30)
    # -------------------------------------------------------------
    ph_val = soil.ph.value if soil.ph else None
    if ph_val is not None:
        if crop.ph_min <= ph_val <= crop.ph_max:
            ph_fit = True
            pts = _WEIGHTS["ph"]
            total_score += pts
            factor_breakdown["ph"] = pts
            msg = f"Soil pH {ph_val} is within {crop.name}'s preferred range ({crop.ph_min}-{crop.ph_max})."
            reasons.append(msg)
            positive_factors.append(f"Optimal pH ({ph_val}) supports maximum nutrient bioavailability (+{pts:.0f} pts).")
        else:
            ph_fit = False
            # Minor deviation vs severe deviation
            dist = min(abs(ph_val - crop.ph_min), abs(ph_val - crop.ph_max))
            if dist <= 0.5:
                pts = _WEIGHTS["ph"] * 0.4  # partial tolerance
                total_score += pts
                factor_breakdown["ph"] = pts
                msg = f"Soil pH {ph_val} is slightly outside {crop.name}'s ideal band ({crop.ph_min}-{crop.ph_max})."
                reasons.append(msg)
                limiting_factors.append(f"Slight pH deviation ({ph_val} vs {crop.ph_min}-{crop.ph_max}) may mildly reduce uptake.")
            else:
                factor_breakdown["ph"] = 0.0
                msg = f"Soil pH {ph_val} is outside {crop.name}'s preferred range ({crop.ph_min}-{crop.ph_max})."
                reasons.append(msg)
                limiting_factors.append(f"Suboptimal soil pH ({ph_val}); risk of nutrient fixation or elemental toxicity.")
    else:
        ph_fit = False
        # Neutral uncertainty baseline (50% weight) when unmeasured
        pts = _WEIGHTS["ph"] * 0.5
        total_score += pts
        factor_breakdown["ph"] = pts
        reasons.append("Soil pH was not available, so pH fit could not be fully scored.")
        missing_factors.append("Soil pH was not measured; suitability calculated with moderate uncertainty.")

    # -------------------------------------------------------------
    # 2. Available Nitrogen Evaluation (Weight: 20)
    # -------------------------------------------------------------
    n_val = soil.nitrogen.value if soil.nitrogen else None
    if n_val is not None:
        if crop.n_min <= n_val <= crop.n_max:
            n_fit = True
            pts = _WEIGHTS["nitrogen"]
            total_score += pts
            factor_breakdown["nitrogen"] = pts
            msg = f"Available nitrogen ({n_val} kg/ha) meets {crop.name}'s requirement."
            reasons.append(msg)
            positive_factors.append(f"Adequate available nitrogen ({n_val} kg/ha) matches crop demand (+{pts:.0f} pts).")
        elif is_legume and n_val < crop.n_min:
            # Legumes biologically fix nitrogen via Rhizobia; low N is not heavily penalizing
            n_fit = True
            pts = _WEIGHTS["nitrogen"] * 0.85
            total_score += pts
            factor_breakdown["nitrogen"] = pts
            reasons.append(f"{crop.name} is a legume that fixes nitrogen; low soil N ({n_val} kg/ha) is mitigated.")
            positive_factors.append(f"Legume nitrogen fixation mitigates low soil N level ({n_val} kg/ha).")
        else:
            n_fit = False
            factor_breakdown["nitrogen"] = 0.0
            gap = "below" if n_val < crop.n_min else "above"
            msg = f"Available nitrogen ({n_val} kg/ha) is {gap} {crop.name}'s ideal range ({crop.n_min}-{crop.n_max} kg/ha)."
            reasons.append(msg)
            limiting_factors.append(f"Nitrogen level ({n_val} kg/ha) is {gap} target ({crop.n_min}-{crop.n_max} kg/ha).")
    else:
        n_fit = False
        pts = _WEIGHTS["nitrogen"] * 0.5
        total_score += pts
        factor_breakdown["nitrogen"] = pts
        reasons.append("Available nitrogen was not tested.")
        missing_factors.append("Available nitrogen test missing; baseline suitability assumed.")

    # -------------------------------------------------------------
    # 3. Available Phosphorus Evaluation (Weight: 15)
    # -------------------------------------------------------------
    p_val = soil.phosphorus.value if soil.phosphorus else None
    if p_val is not None:
        if crop.p_min <= p_val <= crop.p_max:
            p_fit = True
            pts = _WEIGHTS["phosphorus"]
            total_score += pts
            factor_breakdown["phosphorus"] = pts
            msg = f"Available phosphorus ({p_val} kg/ha) meets {crop.name}'s requirement."
            reasons.append(msg)
            positive_factors.append(f"Available phosphorus ({p_val} kg/ha) supports strong root establishment (+{pts:.0f} pts).")
        else:
            p_fit = False
            factor_breakdown["phosphorus"] = 0.0
            gap = "below" if p_val < crop.p_min else "above"
            msg = f"Available phosphorus ({p_val} kg/ha) is {gap} {crop.name}'s ideal range ({crop.p_min}-{crop.p_max} kg/ha)."
            reasons.append(msg)
            limiting_factors.append(f"Phosphorus level ({p_val} kg/ha) is {gap} target range ({crop.p_min}-{crop.p_max} kg/ha).")
    else:
        p_fit = False
        pts = _WEIGHTS["phosphorus"] * 0.5
        total_score += pts
        factor_breakdown["phosphorus"] = pts
        missing_factors.append("Available phosphorus not reported.")

    # -------------------------------------------------------------
    # 4. Available Potassium Evaluation (Weight: 15)
    # -------------------------------------------------------------
    k_val = soil.potassium.value if soil.potassium else None
    if k_val is not None:
        if crop.k_min <= k_val <= crop.k_max:
            k_fit = True
            pts = _WEIGHTS["potassium"]
            total_score += pts
            factor_breakdown["potassium"] = pts
            msg = f"Available potassium ({k_val} kg/ha) meets {crop.name}'s requirement."
            reasons.append(msg)
            positive_factors.append(f"Available potassium ({k_val} kg/ha) is within optimal range (+{pts:.0f} pts).")
        else:
            k_fit = False
            factor_breakdown["potassium"] = 0.0
            gap = "below" if k_val < crop.k_min else "above"
            msg = f"Available potassium ({k_val} kg/ha) is {gap} {crop.name}'s ideal range ({crop.k_min}-{crop.k_max} kg/ha)."
            reasons.append(msg)
            limiting_factors.append(f"Potassium level ({k_val} kg/ha) is {gap} target range ({crop.k_min}-{crop.k_max} kg/ha).")
    else:
        k_fit = False
        pts = _WEIGHTS["potassium"] * 0.5
        total_score += pts
        factor_breakdown["potassium"] = pts
        missing_factors.append("Available potassium not reported.")

    # -------------------------------------------------------------
    # 5. Season Fit Evaluation (Weight: 20)
    # -------------------------------------------------------------
    season_fit = current_season is None or current_season.lower() in [s.lower() for s in crop.season]
    if season_fit:
        pts = _WEIGHTS["season"]
        total_score += pts
        factor_breakdown["season"] = pts
        if current_season:
            reasons.append(f"{crop.name} is suitable for the {current_season} season.")
            positive_factors.append(f"Current season ({current_season.capitalize()}) matches growing cycle (+{pts:.0f} pts).")
        else:
            positive_factors.append("No specific season constraint specified; full season suitability credited.")
    else:
        factor_breakdown["season"] = 0.0
        reasons.append(f"{crop.name} is typically grown in {', '.join(crop.season)}, not {current_season}.")
        limiting_factors.append(f"Unfavorable season ({current_season}); crop typically planted in {', '.join(crop.season)}.")

    # -------------------------------------------------------------
    # 6. Salinity (EC) Sensitivity Modifiers
    # -------------------------------------------------------------
    ec_val = soil.electrical_conductivity.value if soil.electrical_conductivity else None
    if ec_val is not None and ec_val > 1.5:
        # Sensitive vegetable / pulse crops
        if crop_name_lower in ["tomato", "onion", "chickpea (gram)", "soybean"]:
            penalty = 15.0
            total_score = max(0.0, total_score - penalty)
            limiting_factors.append(f"High electrical conductivity ({ec_val} dS/m) imposes osmotic salinity stress (-{penalty:.0f} pts).")

    final_score = round(min(100.0, max(0.0, total_score)), 1)
    category = _determine_category(final_score)

    return CropScore(
        name=crop.name,
        score=final_score,
        ph_fit=ph_fit,
        n_fit=n_fit,
        p_fit=p_fit,
        k_fit=k_fit,
        season_fit=season_fit,
        reasons=reasons,
        category=category,
        positive_factors=positive_factors,
        limiting_factors=limiting_factors,
        missing_factors=missing_factors,
        factor_breakdown=factor_breakdown,
    )


def rank_crops(
    soil: SoilReport,
    current_season: Optional[str] = None,
    top_n: int = 5,
) -> List[CropScore]:
    """Ranks all documented crops by calculated suitability score in descending order."""
    scores = [score_crop(soil, crop, current_season) for crop in load_crop_requirements()]
    scores.sort(key=lambda s: s.score, reverse=True)
    return scores[:top_n]
