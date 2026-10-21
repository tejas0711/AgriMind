"""Deterministic Soil Nutrient and Physical Property Classifier.

Implements official Indian Soil Health Card (SHC) Scheme (2015, Ministry of Agriculture
& Farmers Welfare, Government of India) and ICAR Soil Testing Guidelines.

Evaluates available Macronutrients (N, P, K), Organic Carbon (OC), Soil Reaction (pH),
Salinity (EC), and Micronutrients (Zn, Fe, S, B, Cu, Mn) using configurable thresholds,
supported unit normalization, and granular agronomic implications.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple
from app.models.soil import SoilReport, SoilValue
from app.models.recommendation import Deficiency


# Canonical threshold references based on official Indian Soil Health Card standards
DEFAULT_MACRO_THRESHOLDS: Dict[str, Tuple[float, float]] = {
    # (low_upper_bound, medium_upper_bound) in kg/ha
    # N: Alkaline Permanganate method
    "nitrogen": (280.0, 560.0),
    # P: Olsen's 0.5M NaHCO3 method
    "phosphorus": (10.0, 25.0),
    # K: 1N Neutral Ammonium Acetate method
    "potassium": (108.0, 280.0),
    # OC: Walkley-Black chromic acid wet oxidation method (%)
    "organic_carbon": (0.50, 0.75),
}

DEFAULT_MICRONUTRIENT_CRITICAL: Dict[str, float] = {
    # Critical limit in ppm (mg/kg) below which deficiency is diagnosed
    "zinc": 0.60,       # DTPA-extractable Zn
    "iron": 4.50,       # DTPA-extractable Fe
    "sulphur": 10.0,    # 0.15% CaCl2 extractable S
    "boron": 0.50,      # Hot water soluble B
    "copper": 0.20,     # DTPA-extractable Cu
    "manganese": 2.00,  # DTPA-extractable Mn
}

RULE_SOURCES: Dict[str, str] = {
    "shc_national": "Soil Health Card Scheme (2015), Ministry of Agriculture & Farmers Welfare, GoI",
    "icar_methods": "ICAR Soil Testing in India: A Laboratory Manual (2011)",
    "cssri_saline": "Central Soil Salinity Research Institute (CSSRI) Diagnostic Criteria",
}


def normalize_unit(unit_str: Optional[str]) -> str:
    """Cleans and standardizes measurement unit strings."""
    if not unit_str:
        return ""
    u = unit_str.strip().lower()
    if u in ["kg/ha", "kg / ha", "kgha", "kg ha-1", "kg/hectare"]:
        return "kg/ha"
    if u in ["ppm", "mg/kg", "mg / kg", "mg/l"]:
        return "ppm"
    if u in ["%", "percent", "pct"]:
        return "%"
    if u in ["ds/m", "ds / m", "ms/cm", "mmhos/cm"]:
        return "dS/m"
    if u in ["lbs/acre", "lb/acre", "lbs / acre"]:
        return "lbs/acre"
    return u


def convert_to_standard_unit(nutrient: str, value: float, raw_unit: Optional[str]) -> Tuple[float, str]:
    """Converts supported units to canonical units (kg/ha for NPK, % for OC, ppm for micros).

    Standard agronomic conversion factors:
      - 1 ppm in topsoil (assuming 2 million kg soil per hectare furrow slice) ≈ 2.24 kg/ha.
      - 1 lbs/acre ≈ 1.12 kg/ha.
      - 1 g/kg = 0.1% for organic carbon.
    """
    unit = normalize_unit(raw_unit)

    if nutrient in ["nitrogen", "phosphorus", "potassium"]:
        if unit == "ppm":
            # 1 ppm ≈ 2.24 kg/ha
            return round(value * 2.24, 2), "kg/ha"
        if unit == "lbs/acre":
            # 1 lb/acre ≈ 1.12 kg/ha
            return round(value * 1.12, 2), "kg/ha"
        return value, "kg/ha"

    if nutrient == "organic_carbon":
        if unit == "g/kg":
            return round(value / 10.0, 3), "%"
        return value, "%"

    if nutrient in ["zinc", "iron", "sulphur", "boron", "copper", "manganese"]:
        return value, "ppm"

    if nutrient == "electrical_conductivity":
        return value, "dS/m"

    return value, unit or ""


def classify_macronutrient(
    nutrient: str,
    raw_value: Optional[float],
    raw_unit: Optional[str] = None,
    thresholds: Optional[Tuple[float, float]] = None,
) -> Deficiency:
    """Classifies N, P, K, or OC into LOW, MEDIUM, or HIGH with documented implications."""
    rule_source = RULE_SOURCES["shc_national"]
    label = nutrient.replace("_", " ").title()

    if raw_value is None:
        return Deficiency(
            nutrient=nutrient,
            status="UNKNOWN",
            detail=f"{label} was not measured or extracted from the report.",
            rule_source=rule_source,
            agronomic_implication="Cannot evaluate nutrient availability without laboratory measurement.",
        )

    val_std, std_unit = convert_to_standard_unit(nutrient, raw_value, raw_unit)
    bands = thresholds or DEFAULT_MACRO_THRESHOLDS[nutrient]
    low_band, med_band = bands
    thresh_desc = f"< {low_band} Low, {low_band}-{med_band} Medium, > {med_band} High {std_unit}"

    if val_std < low_band:
        status = "LOW"
        implications = {
            "nitrogen": "Low available nitrogen limits vegetative growth, tillering, and photosynthetic chlorophyll synthesis.",
            "phosphorus": "Low phosphorus restricts early root development, delayed flowering, and energy transfer.",
            "potassium": "Low potassium impairs stomatal regulation, lodging resistance, and disease resilience.",
            "organic_carbon": "Low organic carbon (<0.5%) indicates degraded biological health, poor moisture retention, and low CEC.",
        }
        detail = f"{label} is LOW ({val_std} {std_unit}; benchmark <{low_band}). Corrective fertilizer/amendment recommended."
        implication = implications.get(nutrient, "Deficiency restricts normal crop physiological performance.")
    elif val_std < med_band:
        status = "MEDIUM"
        detail = f"{label} is at an adequate MEDIUM level ({val_std} {std_unit}; benchmark {low_band}-{med_band})."
        implication = "Current fertility level is adequate to support standard maintenance yields."
    else:
        status = "HIGH"
        implications = {
            "nitrogen": "Excessive nitrogen causes vegetative luxuriance, delayed crop maturity, lodging risk, and pest vulnerability.",
            "phosphorus": "High phosphorus risks surface water runoff and antagonizes zinc/iron absorption by roots.",
            "potassium": "Excessive potassium causes luxury consumption and competes antagonistically with calcium and magnesium uptake.",
            "organic_carbon": "High organic carbon (>0.75%) reflects excellent humus content, water retention, and microbial activity.",
        }
        detail = f"{label} is HIGH ({val_std} {std_unit}; benchmark >{med_band}). Additional application is generally unnecessary."
        implication = implications.get(nutrient, "Excess levels observed; additional inputs should be withheld to avoid nutrient imbalance.")

    return Deficiency(
        nutrient=nutrient,
        status=status,
        detail=detail,
        value=val_std,
        unit=std_unit,
        threshold_used=thresh_desc,
        rule_source=rule_source,
        agronomic_implication=implication,
    )


def classify_micronutrient(
    nutrient: str,
    raw_value: Optional[float],
    raw_unit: Optional[str] = None,
    critical_limit: Optional[float] = None,
) -> Deficiency:
    """Classifies micronutrients (Zn, Fe, S, B, Cu, Mn) against critical agronomic limits."""
    rule_source = RULE_SOURCES["shc_national"]
    label = nutrient.title()

    if raw_value is None:
        return Deficiency(
            nutrient=nutrient,
            status="UNKNOWN",
            detail=f"{label} was not analyzed in the submitted soil test report.",
            rule_source=rule_source,
            agronomic_implication="Trace element status unknown. Watch for visual chlorosis symptoms during active growth.",
        )

    val_std, std_unit = convert_to_standard_unit(nutrient, raw_value, raw_unit)
    crit = critical_limit or DEFAULT_MICRONUTRIENT_CRITICAL.get(nutrient, 1.0)
    thresh_desc = f"Critical level: {crit} {std_unit} (Deficient < {crit}, Sufficient >= {crit})"

    if val_std < crit:
        status = "LOW"  # LOW = Deficient
        implications = {
            "zinc": "Zinc deficiency causes 'Khaira' disease in rice, interveinal chlorosis, and stunted leaf rosetting.",
            "iron": "Iron deficiency induces lime-induced interveinal chlorosis on young emergent leaves.",
            "sulphur": "Sulphur deficiency impairs essential amino acids (methionine, cysteine) and oil synthesis in pulses/oilseeds.",
            "boron": "Boron deficiency leads to pollen sterility, poor fruit set, and cracked hollow-heart disorders.",
            "copper": "Copper deficiency causes dieback of terminal shoots and exanthema in fruit crops.",
            "manganese": "Manganese deficiency results in 'Pahala blight' in sugarcane and grey speck in small grains.",
        }
        detail = f"{label} is DEFICIENT ({val_std} {std_unit}, critical limit {crit} {std_unit}). Correction recommended."
        implication = implications.get(nutrient, "Micro-element deficiency restricts metabolic enzymes.")
    else:
        status = "HIGH"  # HIGH = Sufficient / Adequate
        detail = f"{label} is SUFFICIENT ({val_std} {std_unit}, critical limit {crit} {std_unit}). No corrective action required."
        implication = "Adequate available concentration detected in soil test."

    return Deficiency(
        nutrient=nutrient,
        status=status,
        detail=detail,
        value=val_std,
        unit=std_unit,
        threshold_used=thresh_desc,
        rule_source=rule_source,
        agronomic_implication=implication,
    )


def classify_soil_reaction(ph_value: Optional[float]) -> Optional[Deficiency]:
    """Classifies soil pH into agro-ecological acidity/alkalinity classes."""
    if ph_value is None:
        return None

    rule_source = RULE_SOURCES["icar_methods"]
    if ph_value < 5.5:
        return Deficiency(
            nutrient="ph",
            status="LOW",
            detail=f"Soil is strongly acidic (pH {ph_value}; benchmark < 5.5). Risk of aluminium toxicity and P fixation.",
            value=ph_value,
            unit="pH",
            threshold_used="Optimal neutral range: 6.5 - 7.5; Strongly acidic < 5.5",
            rule_source=rule_source,
            agronomic_implication="Acidic soil restricts root development and locks up phosphorus; agricultural liming recommended.",
        )
    if ph_value > 8.0:
        return Deficiency(
            nutrient="ph",
            status="HIGH",
            detail=f"Soil is alkaline/sodic (pH {ph_value}; benchmark > 8.0). Calcium and micronutrient availability is reduced.",
            value=ph_value,
            unit="pH",
            threshold_used="Optimal neutral range: 6.5 - 7.5; Alkaline > 8.0",
            rule_source=rule_source,
            agronomic_implication="Alkaline/calcareous condition induces zinc/iron chlorosis; organic matter or gypsum application recommended.",
        )
    return Deficiency(
        nutrient="ph",
        status="MEDIUM",
        detail=f"Soil pH is in the favorable/neutral zone ({ph_value}).",
        value=ph_value,
        unit="pH",
        threshold_used="Optimal range: 6.0 - 7.5",
        rule_source=rule_source,
        agronomic_implication="Balanced soil reaction supporting wide crop suitability.",
    )


def classify_salinity(ec_value: Optional[float]) -> Optional[Deficiency]:
    """Classifies electrical conductivity (EC) to identify potential salinity hazard."""
    if ec_value is None:
        return None

    rule_source = RULE_SOURCES["cssri_saline"]
    if ec_value > 2.0:
        return Deficiency(
            nutrient="electrical_conductivity",
            status="HIGH",
            detail=f"Electrical Conductivity is high ({ec_value} dS/m; critical > 2.0). Soluble salt injury risk.",
            value=ec_value,
            unit="dS/m",
            threshold_used="Normal < 1.0 dS/m, Critical 1.0 - 2.0 dS/m, Saline > 2.0 dS/m",
            rule_source=rule_source,
            agronomic_implication="High salinity exerts osmotic pull, hindering root water absorption. Salt-tolerant crops advised.",
        )
    if ec_value > 1.0:
        return Deficiency(
            nutrient="electrical_conductivity",
            status="MEDIUM",
            detail=f"EC is slightly elevated ({ec_value} dS/m). Sensitive crops (pulses/vegetables) may experience slight stress.",
            value=ec_value,
            unit="dS/m",
            threshold_used="Normal < 1.0 dS/m, Critical 1.0 - 2.0 dS/m",
            rule_source=rule_source,
            agronomic_implication="Moderate salinity; ensure adequate drainage and furrow irrigation to prevent salt accumulation.",
        )
    return Deficiency(
        nutrient="electrical_conductivity",
        status="LOW",
        detail=f"EC is safe and non-saline ({ec_value} dS/m; < 1.0 dS/m).",
        value=ec_value,
        unit="dS/m",
        threshold_used="Non-saline < 1.0 dS/m",
        rule_source=rule_source,
        agronomic_implication="Normal salt levels with no osmotic inhibition to seedling germination.",
    )


def classify_all_parameters(soil: SoilReport) -> Dict[str, any]:
    """Comprehensive deterministic classification of all 12 supported soil parameters.

    Returns:
      - `deficiencies`: list of Deficiency objects (including LOW, HIGH, MEDIUM, UNKNOWN)
      - `missing_warnings`: explicit list of parameters not tested in this report
      - `data_completeness`: ratio of core measured parameters (0.0 to 1.0)
    """
    deficiencies: List[Deficiency] = []
    missing_warnings: List[str] = []

    # 1. Primary Macronutrients & Organic Carbon
    macro_fields = [
        ("nitrogen", soil.nitrogen),
        ("phosphorus", soil.phosphorus),
        ("potassium", soil.potassium),
        ("organic_carbon", soil.organic_carbon),
    ]
    for key, fld in macro_fields:
        val = fld.value if fld else None
        u = fld.unit if fld else None
        d = classify_macronutrient(key, val, u)
        deficiencies.append(d)
        if d.status == "UNKNOWN":
            missing_warnings.append(
                f"{key.replace('_', ' ').title()} was not measured. Nitrogen/Phosphorus/Potassium/Carbon recommendations are incomplete."
            )

    # 2. Micronutrients
    micro_fields = [
        ("zinc", soil.zinc),
        ("iron", soil.iron),
        ("sulphur", soil.sulphur),
        ("boron", soil.boron),
        ("copper", soil.copper),
        ("manganese", soil.manganese),
    ]
    for key, fld in micro_fields:
        val = fld.value if fld else None
        u = fld.unit if fld else None
        d = classify_micronutrient(key, val, u)
        deficiencies.append(d)
        if d.status == "UNKNOWN":
            missing_warnings.append(f"{key.title()} was not tested; micronutrient status cannot be evaluated.")

    # 3. Soil Reaction (pH)
    ph_val = soil.ph.value if soil.ph else None
    if ph_val is not None:
        ph_d = classify_soil_reaction(ph_val)
        if ph_d:
            deficiencies.append(ph_d)
    else:
        missing_warnings.append("Soil pH was not measured; cannot evaluate acidity or nutrient availability buffers.")
        deficiencies.append(
            Deficiency(
                nutrient="ph",
                status="UNKNOWN",
                detail="Soil pH was not found in the uploaded report.",
                rule_source=RULE_SOURCES["icar_methods"],
                agronomic_implication="Soil acidity/alkalinity unknown.",
            )
        )

    # 4. Salinity (EC)
    ec_val = soil.electrical_conductivity.value if soil.electrical_conductivity else None
    if ec_val is not None:
        ec_d = classify_salinity(ec_val)
        if ec_d:
            deficiencies.append(ec_d)
    else:
        missing_warnings.append("Electrical Conductivity (EC) was not provided; salinity hazard cannot be confirmed.")
        deficiencies.append(
            Deficiency(
                nutrient="electrical_conductivity",
                status="UNKNOWN",
                detail="EC was not found in the uploaded report.",
                rule_source=RULE_SOURCES["cssri_saline"],
                agronomic_implication="Soil salinity unknown.",
            )
        )

    core_completeness = soil.completeness() if hasattr(soil, "completeness") else 0.5

    return {
        "deficiencies": deficiencies,
        "missing_warnings": missing_warnings,
        "data_completeness": core_completeness,
    }
