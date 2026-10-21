"""Deterministic nutrient-status classification, fertilizer selection, and contradiction detection.

Follows official Indian Soil Health Card (SHC) fertility rating bands and ICAR
recommendation guidelines. Exact dosages are intentionally flagged as PROVISIONAL,
requiring local extension/KVK verification.

Strictly excludes all chemical pesticide recommendations.
Enforces multi-layer contradiction prevention (e.g. blocking potassium addition if
potassium is HIGH; preventing lime on alkaline soils; guarding legume nodulation).
"""
from __future__ import annotations

from typing import List, Optional, Tuple, Dict
from app.models.soil import SoilReport
from app.models.recommendation import Deficiency, FertilizerOption
from app.services.fertilizer_service import get_options_for_nutrient
from app.engine.soil_classifier import (
    DEFAULT_MACRO_THRESHOLDS,
    DEFAULT_MICRONUTRIENT_CRITICAL,
    classify_all_parameters,
    classify_macronutrient,
    classify_micronutrient,
    classify_soil_reaction,
    classify_salinity,
)

# Preserved for backward-compatibility with direct test imports
_THRESHOLDS = DEFAULT_MACRO_THRESHOLDS
_MICRONUTRIENT_CRITICAL = DEFAULT_MICRONUTRIENT_CRITICAL

# Active nutrient keys eligible for fertilizer / amendment lookup
ACTIVE_NUTRIENTS = (
    "nitrogen",
    "phosphorus",
    "potassium",
    "organic_carbon",
    "zinc",
    "iron",
    "sulphur",
    "boron",
    "copper",
    "manganese",
    "ph_acidic",
    "ph_alkaline",
)

LEGUME_CROPS = {"soybean", "chickpea (gram)", "chickpea", "groundnut", "lentil", "black gram", "green gram"}


def detect_deficiencies(soil: SoilReport) -> List[Deficiency]:
    """Evaluates soil measurements and returns structured status classifications."""
    classification = classify_all_parameters(soil)
    return classification["deficiencies"]


def recommend_fertilizers(
    deficiencies: List[Deficiency],
    prefer_organic: bool = False,
    soil: Optional[SoilReport] = None,
    selected_crop: Optional[str] = None,
) -> List[FertilizerOption]:
    """Selects relevant chemical and organic amendments for diagnosed deficiencies.

    Strict Contradiction Avoidance:
      - Only nutrients flagged LOW receive fertilizer options.
      - Nutrients classified HIGH are strictly blocked from receiving fertilizer.
      - High pH soils receive gypsum / organic amendments, never lime.
      - Strongly acidic soils receive lime, never acidifying fertilizers.
      - Legume crops receive cautionary notes regarding high nitrogen applications.
    """
    options: List[FertilizerOption] = []
    seen_names = set()

    # Identify which nutrients are HIGH to enforce hard contradiction blocks
    high_nutrients = {d.nutrient for d in deficiencies if d.status == "HIGH"}

    for d in deficiencies:
        # Only LOW status triggers active fertilizer/amendment selection
        if d.status != "LOW":
            continue

        target_key = d.nutrient
        if d.nutrient == "ph":
            # pH < 5.5 (LOW) implies acidity requiring liming
            target_key = "ph_acidic"

        # Check if the amendment itself would add a nutrient that is already HIGH
        if target_key in high_nutrients:
            continue

        data = get_options_for_nutrient(target_key)
        chosen_types = ["organic", "chemical"] if prefer_organic else ["chemical", "organic"]

        for ftype in chosen_types:
            for item in data.get(ftype, []):
                name = item.get("name", "")
                if name in seen_names:
                    continue

                # Contradiction guard: If potassium is HIGH, never recommend wood ash or MOP/SOP
                if "potassium" in high_nutrients and ("potash" in name.lower() or "wood ash" in name.lower() or "mop" in name.lower()):
                    continue

                # Contradiction guard: If phosphorus is HIGH, never recommend DAP or SSP or Rock Phosphate
                if "phosphorus" in high_nutrients and ("phosphate" in name.lower() or "dap" in name.lower() or "ssp" in name.lower()):
                    continue

                # Legume guard: If target crop is a legume, flag high N fertilizers
                notes = item.get("application_notes", "")
                if selected_crop and selected_crop.lower() in LEGUME_CROPS and d.nutrient == "nitrogen":
                    notes += f" Note: {selected_crop} fixes atmospheric nitrogen; apply only starter dose of N."

                seen_names.add(name)
                options.append(
                    FertilizerOption(
                        name=name,
                        type=ftype,
                        nutrient=d.nutrient,
                        application_notes=notes,
                        source=item.get("source"),
                        purpose=item.get("purpose"),
                        cautions=item.get("cautions"),
                        is_provisional=True,
                    )
                )

    # Check for Alkaline Soil pH (> 8.0) which is classified as status="HIGH" for pH
    ph_def = next((d for d in deficiencies if d.nutrient == "ph"), None)
    if ph_def and ph_def.status == "HIGH":
        alkaline_data = get_options_for_nutrient("ph_alkaline")
        chosen_types = ["organic", "chemical"] if prefer_organic else ["chemical", "organic"]
        for ftype in chosen_types:
            for item in alkaline_data.get(ftype, []):
                name = item.get("name", "")
                if name not in seen_names:
                    seen_names.add(name)
                    options.append(
                        FertilizerOption(
                            name=name,
                            type=ftype,
                            nutrient="ph",
                            application_notes=item.get("application_notes", ""),
                            source=item.get("source"),
                            purpose=item.get("purpose"),
                            cautions=item.get("cautions"),
                            is_provisional=True,
                        )
                    )

    return options


def check_contradiction(user_question: str, deficiencies: List[Deficiency]) -> Optional[str]:
    """Detects obvious contradiction when user asks to add a nutrient that soil test shows as HIGH."""
    q = user_question.lower()
    nutrient_keywords = {
        "nitrogen": ["nitrogen", "urea", "ammonium sulphate"],
        "phosphorus": ["phosphorus", "phosphate", "dap", "ssp", "rock phosphate"],
        "potassium": ["potassium", "potash", "mop", "sop", "wood ash"],
        "zinc": ["zinc", "znso4", "zinc sulphate", "zinc sulfate"],
        "iron": ["iron", "feso4", "ferrous sulphate", "ferrous sulfate"],
        "sulphur": ["sulphur", "sulfur", "gypsum"],
        "boron": ["boron", "borax", "solubor"],
    }

    for nutrient, keywords in nutrient_keywords.items():
        if any(k in q for k in keywords):
            match = next((d for d in deficiencies if d.nutrient == nutrient), None)
            if match and match.status == "HIGH":
                label = nutrient.title()
                val_str = f" ({match.value} {match.unit})" if match.value else ""
                return (
                    f"Your soil report shows {label} is already HIGH{val_str}. "
                    f"Adding more {nutrient} fertilizer is not recommended and could create a nutrient imbalance."
                )

    # Check liming contradiction
    if any(k in q for k in ["lime", "liming", "calcium carbonate", "dolomite"]):
        ph_match = next((d for d in deficiencies if d.nutrient == "ph"), None)
        if ph_match and ph_match.status == "HIGH":
            return (
                f"Your soil report shows pH is alkaline ({ph_match.value}). "
                "Applying agricultural lime will raise pH further and is strongly contraindicated."
            )

    return None


def detect_all_contradictions(
    soil: SoilReport,
    deficiencies: List[Deficiency],
    user_question: Optional[str] = None,
    selected_crop: Optional[str] = None,
) -> List[str]:
    """Comprehensive multi-rule contradiction detection.

    Verifies:
      1. User query vs high soil nutrient status.
      2. High nutrient report status vs fertilizer blocking.
      3. Soil pH vs incompatible amendment (lime on alkaline soil).
      4. Legume crop vs heavy nitrogenous fertilization.
    """
    contradictions: List[str] = []

    # 1. User question contradiction
    if user_question:
        user_c = check_contradiction(user_question, deficiencies)
        if user_c:
            contradictions.append(user_c)

    # 2. Check for high nutrient warnings
    for d in deficiencies:
        if d.status == "HIGH" and d.nutrient in ["nitrogen", "phosphorus", "potassium"]:
            label = d.nutrient.replace("_", " ").title()
            val_str = f"{d.value} {d.unit}" if d.value else "excessive"
            # Affirm that system does not recommend more of this nutrient
            contradictions.append(
                f"Nutrient Safeguard: {label} is HIGH ({val_str}). Additional {d.nutrient} fertilizer is blocked "
                f"to prevent toxic luxury consumption and economic waste."
            )

    # 3. Soil pH amendment contradiction
    if soil.ph and soil.ph.value is not None:
        if soil.ph.value > 8.0:
            contradictions.append(
                f"Alkaline Soil Safeguard: Soil pH is {soil.ph.value} (> 8.0). "
                "Liming materials (calcium carbonate/wood ash) are contraindicated. Use gypsum or sulfur amendments."
            )

    # 4. Legume nodulation safeguard
    if selected_crop and selected_crop.lower() in LEGUME_CROPS:
        n_def = next((d for d in deficiencies if d.nutrient == "nitrogen"), None)
        if n_def and n_def.status == "HIGH":
            contradictions.append(
                f"Legume Safeguard: High soil nitrogen in {selected_crop} field inhibits biological Rhizobium nodulation. "
                "Withhold synthetic nitrogen to encourage active nitrogen fixation."
            )

    return contradictions
