"""Converts raw soil-report text into validated structured soil measurements.

Follows the project's engineering principle:
Numeric soil extraction is deterministic (pure regex and rule validation, no LLM guessing).
Each measurement captures value, unit, verbatim source text, plausibility status,
and Soil Health Card benchmark rating.
"""
from __future__ import annotations

import re
from typing import Any, Callable, Dict, List, Optional, Tuple

from app.models.soil import (
    SoilMeasurement,
    SoilParseResponse,
    SoilReport,
    SoilValue,
)

# Common unit patterns
_KG_HA = r"kg\s*/\s*ha|kg/ha|kg\s*/\s*acre|kg/acre|lbs\s*/\s*acre|lbs/acre|ppm|mg\s*/\s*kg|mg/kg"
_PPM = r"ppm|mg\s*/\s*kg|mg/kg|ug\s*/\s*g"
_PCT = r"%|percent"
_DS_M = r"ds\s*/\s*m|dS\s*/\s*m|dS/m|ds/m|mmhos\s*/\s*cm|mmhos/cm|mS\s*/\s*cm|mS/cm"


def _full_name_pattern(full_name: str, abbrev: str, units: str) -> str:
    """Build a tolerant pattern for '<Full Name> [(ABBR)] [:/-] <value> [unit]'.

    IMPORTANT: the abbreviation group is wrapped as `(?:\\(?abbr\\)?)?` so the
    ENTIRE "(ABBR)" chunk is optional -- not just the parentheses around a
    mandatory abbreviation.
    """
    return (
        rf"{full_name}\s*(?:\(?{abbrev}\)?)?\s*[:\-\|\=]?\s*"
        rf"(?P<value>\d+\.?\d*)\s*(?P<unit>{units})?"
    )


def _abbrev_pattern(abbrev: str, units: str) -> str:
    """Fallback pattern matching just the standalone abbreviation, e.g. 'N: 180'."""
    return rf"\b{abbrev}\b\s*[:\-\|\=]?\s*(?P<value>\d+\.?\d*)\s*(?P<unit>{units})?"


# Parameter definitions, units, benchmarks, and plausibility ranges
PARAMETER_DEFINITIONS: dict[str, dict[str, Any]] = {
    "nitrogen": {
        "name": "Available Nitrogen (N)",
        "is_core": True,
        "default_unit": "kg/ha",
        "patterns": [
            r"(?:available\s+)?" + _full_name_pattern("nitrogen", "n", _KG_HA),
            _abbrev_pattern("N", _KG_HA),
            r"\bN\b\s*[:\-\|\s]+\s*(?P<value>\d+\.?\d*)\s*(?P<unit>kg/ha|ppm)?",
        ],
        "typical_range": "Low: <280, Med: 280-560, High: >560 kg/ha",
        "min_plausible": 5.0,
        "max_plausible": 2000.0,
        "rating_fn": lambda v: "LOW" if v < 280 else ("MEDIUM" if v <= 560 else "HIGH"),
    },
    "phosphorus": {
        "name": "Available Phosphorus (P)",
        "is_core": True,
        "default_unit": "kg/ha",
        "patterns": [
            r"(?:available\s+)?" + _full_name_pattern("phosphorus", "p", _KG_HA),
            _abbrev_pattern("P", _KG_HA),
            r"(?:available\s+)?p2o5\s*[:\-\|\=]?\s*(?P<value>\d+\.?\d*)\s*(?P<unit>kg/ha|ppm)?",
        ],
        "typical_range": "Low: <10, Med: 10-25, High: >25 kg/ha",
        "min_plausible": 1.0,
        "max_plausible": 350.0,
        "rating_fn": lambda v: "LOW" if v < 10 else ("MEDIUM" if v <= 25 else "HIGH"),
    },
    "potassium": {
        "name": "Available Potassium (K)",
        "is_core": True,
        "default_unit": "kg/ha",
        "patterns": [
            r"(?:available\s+)?" + _full_name_pattern("potassium", "k", _KG_HA),
            _abbrev_pattern("K", _KG_HA),
            r"(?:available\s+)?k2o\s*[:\-\|\=]?\s*(?P<value>\d+\.?\d*)\s*(?P<unit>kg/ha|ppm)?",
        ],
        "typical_range": "Low: <108, Med: 108-280, High: >280 kg/ha",
        "min_plausible": 5.0,
        "max_plausible": 2500.0,
        "rating_fn": lambda v: "LOW" if v < 108 else ("MEDIUM" if v <= 280 else "HIGH"),
    },
    "ph": {
        "name": "Soil Reaction (pH)",
        "is_core": True,
        "default_unit": None,
        "patterns": [
            r"(?:soil\s+)?(?:reaction\s+)?\bpH\b(?:\s*\([0-9\:\.]+\))?\s*[:\-\|\=]?\s*(?P<value>\d+\.?\d*)",
        ],
        "typical_range": "Acidic: <6.5, Neutral: 6.5-7.5, Alkaline: >7.5",
        "min_plausible": 3.0,
        "max_plausible": 11.0,
        "rating_fn": lambda v: "ACIDIC" if v < 6.5 else ("NEUTRAL" if v <= 7.5 else "ALKALINE"),
    },
    "organic_carbon": {
        "name": "Organic Carbon (OC)",
        "is_core": True,
        "default_unit": "%",
        "patterns": [
            _full_name_pattern(r"organic\s+carbon", "oc", _PCT),
            _abbrev_pattern("OC", _PCT),
            r"\bSOC\b\s*[:\-\|\=]?\s*(?P<value>\d+\.?\d*)\s*(?P<unit>%)?",
        ],
        "typical_range": "Low: <0.50%, Med: 0.50-0.75%, High: >0.75%",
        "min_plausible": 0.02,
        "max_plausible": 15.0,
        "rating_fn": lambda v: "LOW" if v < 0.5 else ("MEDIUM" if v <= 0.75 else "HIGH"),
    },
    "electrical_conductivity": {
        "name": "Electrical Conductivity (EC)",
        "is_core": True,
        "default_unit": "dS/m",
        "patterns": [
            _full_name_pattern(r"electrical\s+conductivity", "ec", _DS_M),
            _abbrev_pattern("EC", _DS_M),
        ],
        "typical_range": "Normal: <=1.0 dS/m, Critical: 1.0-2.0 dS/m, Saline: >2.0 dS/m",
        "min_plausible": 0.01,
        "max_plausible": 25.0,
        "rating_fn": lambda v: "NORMAL" if v <= 1.0 else ("CRITICAL" if v <= 2.0 else "HIGH"),
    },
    "zinc": {
        "name": "Available Zinc (Zn)",
        "is_core": False,
        "default_unit": "ppm",
        "patterns": [
            _full_name_pattern(r"(?:dtpa\s+)?zinc", "zn", _PPM),
            _abbrev_pattern("Zn", _PPM),
            r"\bDTPA[- ]Zn\b\s*[:\-\|\=]?\s*(?P<value>\d+\.?\d*)\s*(?P<unit>ppm)?",
        ],
        "typical_range": "Critical level: 0.60 ppm (DTPA-Zn)",
        "min_plausible": 0.01,
        "max_plausible": 150.0,
        "rating_fn": lambda v: "DEFICIENT" if v < 0.6 else "SUFFICIENT",
    },
    "iron": {
        "name": "Available Iron (Fe)",
        "is_core": False,
        "default_unit": "ppm",
        "patterns": [
            _full_name_pattern(r"(?:dtpa\s+)?iron", "fe", _PPM),
            _abbrev_pattern("Fe", _PPM),
            r"\bDTPA[- ]Fe\b\s*[:\-\|\=]?\s*(?P<value>\d+\.?\d*)\s*(?P<unit>ppm)?",
        ],
        "typical_range": "Critical level: 4.50 ppm (DTPA-Fe)",
        "min_plausible": 0.05,
        "max_plausible": 250.0,
        "rating_fn": lambda v: "DEFICIENT" if v < 4.5 else "SUFFICIENT",
    },
    "manganese": {
        "name": "Available Manganese (Mn)",
        "is_core": False,
        "default_unit": "ppm",
        "patterns": [
            _full_name_pattern(r"(?:dtpa\s+)?manganese", "mn", _PPM),
            _abbrev_pattern("Mn", _PPM),
            r"\bDTPA[- ]Mn\b\s*[:\-\|\=]?\s*(?P<value>\d+\.?\d*)\s*(?P<unit>ppm)?",
        ],
        "typical_range": "Critical level: 2.00 ppm (DTPA-Mn)",
        "min_plausible": 0.05,
        "max_plausible": 250.0,
        "rating_fn": lambda v: "DEFICIENT" if v < 2.0 else "SUFFICIENT",
    },
    "copper": {
        "name": "Available Copper (Cu)",
        "is_core": False,
        "default_unit": "ppm",
        "patterns": [
            _full_name_pattern(r"(?:dtpa\s+)?copper", "cu", _PPM),
            _abbrev_pattern("Cu", _PPM),
            r"\bDTPA[- ]Cu\b\s*[:\-\|\=]?\s*(?P<value>\d+\.?\d*)\s*(?P<unit>ppm)?",
        ],
        "typical_range": "Critical level: 0.20 ppm (DTPA-Cu)",
        "min_plausible": 0.01,
        "max_plausible": 100.0,
        "rating_fn": lambda v: "DEFICIENT" if v < 0.2 else "SUFFICIENT",
    },
    "sulphur": {
        "name": "Available Sulphur (S)",
        "is_core": False,
        "default_unit": "ppm",
        "patterns": [
            _full_name_pattern(r"(?:available\s+)?sulph?ur", "s", _PPM),
            _abbrev_pattern("S", _PPM),
            r"\bSO4[- ]S\b\s*[:\-\|\=]?\s*(?P<value>\d+\.?\d*)\s*(?P<unit>ppm)?",
        ],
        "typical_range": "Critical level: 10.0 ppm (Available S)",
        "min_plausible": 0.1,
        "max_plausible": 300.0,
        "rating_fn": lambda v: "DEFICIENT" if v < 10.0 else "SUFFICIENT",
    },
    "boron": {
        "name": "Available Boron (B)",
        "is_core": False,
        "default_unit": "ppm",
        "patterns": [
            _full_name_pattern(r"(?:hot\s+water\s+)?boron", "b", _PPM),
            _abbrev_pattern("B", _PPM),
        ],
        "typical_range": "Critical level: 0.50 ppm (Hot water soluble B)",
        "min_plausible": 0.01,
        "max_plausible": 50.0,
        "rating_fn": lambda v: "DEFICIENT" if v < 0.5 else "SUFFICIENT",
    },
}

_CORE_FIELDS = {k for k, v in PARAMETER_DEFINITIONS.items() if v["is_core"]}


def _clean_unit(raw_unit: str | None, default_unit: str | None) -> str | None:
    if not raw_unit:
        return default_unit
    unit_str = re.sub(r"\s+", "", raw_unit).lower()
    if "kg/ha" in unit_str or "kg/acre" in unit_str or "lbs/acre" in unit_str:
        return raw_unit.strip()
    if "ds/m" in unit_str or "mmhos/cm" in unit_str:
        return "dS/m"
    if "ppm" in unit_str or "mg/kg" in unit_str:
        return "ppm"
    if "%" in unit_str:
        return "%"
    return raw_unit.strip()


def parse_soil_text(text: str) -> SoilReport:
    """Converts raw text into a backward-compatible SoilReport with measurements."""
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    warnings: list[str] = []
    fields: dict[str, SoilValue] = {}
    measurements: dict[str, SoilMeasurement] = {}

    for field_key, defs in PARAMETER_DEFINITIONS.items():
        name = defs["name"]
        is_core = defs["is_core"]
        default_unit = defs["default_unit"]
        min_p = defs["min_plausible"]
        max_p = defs["max_plausible"]
        rating_fn = defs["rating_fn"]

        extracted_val: float | None = None
        extracted_unit: str | None = None
        source_line: str | None = None

        # Strategy 1: Match against entire text using compiled regex patterns
        for pattern in defs["patterns"]:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                try:
                    val = float(match.group("value"))
                    unit = match.group("unit") if "unit" in match.groupdict() else None
                    extracted_val = val
                    extracted_unit = _clean_unit(unit, default_unit)
                    # Extract surrounding line for source text evidence
                    start = max(0, match.start() - 30)
                    end = min(len(text), match.end() + 30)
                    matched_snippet = match.group(0).strip()
                    source_line = matched_snippet
                    # Try to locate exact full line if possible
                    for line in lines:
                        if matched_snippet in line or (str(val) in line and (field_key[:3].lower() in line.lower())):
                            source_line = line
                            break
                    break
                except (ValueError, IndexError):
                    continue

        if extracted_val is not None:
            # Range & Plausibility Validation
            status = "extracted"
            warning_msg = None

            if extracted_val < min_p or extracted_val > max_p:
                status = "needs_review"
                warning_msg = (
                    f"Measurement {extracted_val} {extracted_unit or ''} for {name} is "
                    f"outside typical soil range ({min_p} - {max_p}). Please verify."
                )
                warnings.append(warning_msg)

            rating = rating_fn(extracted_val)
            fields[field_key] = SoilValue(value=extracted_val, unit=extracted_unit)
            measurements[field_key] = SoilMeasurement(
                name=name,
                field_key=field_key,
                value=extracted_val,
                unit=extracted_unit,
                source_text=source_line,
                status=status,
                is_edited=False,
                warning=warning_msg,
                rating=rating,
                typical_range=defs["typical_range"],
            )
        else:
            # Missing parameter
            status = "missing"
            if is_core:
                warnings.append(f"Could not find a value for '{field_key}' in the uploaded report.")

            measurements[field_key] = SoilMeasurement(
                name=name,
                field_key=field_key,
                value=None,
                unit=default_unit,
                source_text=None,
                status=status,
                is_edited=False,
                warning="Not detected in report" if is_core else None,
                rating="UNKNOWN",
                typical_range=defs["typical_range"],
            )

    report = SoilReport(
        **fields,
        measurements=measurements,
        raw_text_excerpt=text[:800],
        extraction_warnings=warnings,
    )
    return report


def parse_soil_document(
    text: str,
    file_name: str,
    file_size_bytes: int,
    page_count: int = 1,
    is_scanned_image: bool = False,
    ocr_notice: str | None = None,
) -> SoilParseResponse:
    """Parses extracted PDF document text into a rich SoilParseResponse.

    Populates measurements, flags parameters needing review, and calculates completeness.
    """
    soil_report = parse_soil_text(text)
    needs_review = [
        k for k, m in (soil_report.measurements or {}).items()
        if m.status in ("needs_review", "missing") and PARAMETER_DEFINITIONS[k]["is_core"]
    ]

    soil_values = {
        k: getattr(soil_report, k) for k in PARAMETER_DEFINITIONS.keys()
        if getattr(soil_report, k, None) is not None
    }

    return SoilParseResponse(
        file_name=file_name,
        file_size_bytes=file_size_bytes,
        page_count=page_count,
        is_scanned_image=is_scanned_image,
        ocr_notice=ocr_notice,
        measurements=soil_report.measurements or {},
        core_completeness=soil_report.completeness(),
        warnings=soil_report.extraction_warnings,
        needs_review=needs_review,
        raw_text_excerpt=soil_report.raw_text_excerpt,
        **soil_values,
    )
