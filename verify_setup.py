"""Standalone sanity check, run automatically by setup_windows.ps1 (and safe
to re-run manually any time): parses sample_data/Soil_Test_Report_Demo_Farm.pdf
through the REAL pdf_service + soil_parser pipeline and checks the values
against what we know is actually in that PDF.

This exists specifically to catch a regression of the "Organic Carbon shows
UNKNOWN" bug without needing the full FastAPI server running.

Run from the project root with the backend venv activated:
    python verify_setup.py
"""
from __future__ import annotations

import os
import sys

BACKEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend")
sys.path.insert(0, BACKEND_DIR)

SAMPLE_PDF = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "sample_data", "Soil_Test_Report_Demo_Farm.pdf"
)

EXPECTED = {
    "nitrogen": 180,
    "phosphorus": 15,
    "potassium": 260,
    "ph": 6.4,
    "organic_carbon": 0.45,
    "electrical_conductivity": 0.32,
}

# Cross-checked against the real demo lab report's own printed ratings.
EXPECTED_STATUS = {
    "nitrogen": "LOW",
    "phosphorus": "MEDIUM",
    "potassium": "MEDIUM",
    "organic_carbon": "LOW",
}
EXPECTED_MICRO_STATUS = {  # LOW = deficient, HIGH = sufficient/adequate
    "zinc": "LOW",
    "iron": "HIGH",
    "sulphur": "HIGH",
}


def main() -> int:
    if not os.path.exists(SAMPLE_PDF):
        print(f"FAIL: sample PDF not found at {SAMPLE_PDF}")
        return 1

    try:
        from app.services.pdf_service import extract_text
        from app.services.soil_parser import parse_soil_text
        from app.engine.fertilizer_optimizer import detect_deficiencies
    except ImportError as exc:
        print(f"FAIL: could not import backend modules ({exc}).")
        print("Make sure you're running this with the backend venv activated:")
        print(r"    backend\.venv\Scripts\Activate.ps1")
        print("    python verify_setup.py")
        return 1

    print(f"Reading: {SAMPLE_PDF}")
    text = extract_text(SAMPLE_PDF)
    if not text.strip():
        print("FAIL: no text extracted from the sample PDF (PyMuPDF issue?).")
        return 1

    report = parse_soil_text(text)

    all_ok = True
    print("\nParsed values vs. expected:")
    for field, expected_value in EXPECTED.items():
        field_obj = getattr(report, field, None)
        actual = field_obj.value if field_obj else None
        status = "OK" if actual == expected_value else "MISMATCH"
        if actual != expected_value:
            all_ok = False
        print(f"  {field:26} expected={expected_value:<8} actual={actual}   [{status}]")

    print(f"\nCompleteness: {report.completeness() * 100:.0f}%")
    print(f"Extraction warnings: {report.extraction_warnings or 'none'}")

    print("\nDeficiency classification vs. the real report's own printed ratings:")
    deficiencies = {d.nutrient: d.status for d in detect_deficiencies(report)}
    for field, expected_status in EXPECTED_STATUS.items():
        actual_status = deficiencies.get(field, "MISSING")
        status = "OK" if actual_status == expected_status else "MISMATCH"
        if actual_status != expected_status:
            all_ok = False
        print(f"  {field:26} expected={expected_status:<8} actual={actual_status:<8} [{status}]")

    print("\nMicronutrient classification (LOW=deficient, HIGH=sufficient):")
    for field, expected_status in EXPECTED_MICRO_STATUS.items():
        actual_status = deficiencies.get(field, "MISSING")
        status = "OK" if actual_status == expected_status else "MISMATCH"
        if actual_status != expected_status:
            all_ok = False
        print(f"  {field:26} expected={expected_status:<8} actual={actual_status:<8} [{status}]")

    if all_ok and report.completeness() == 1.0:
        print("\nPASS: soil parser AND deficiency classification match the real")
        print("demo report's own printed ratings, including Organic Carbon,")
        print("Nitrogen, and Zinc deficiency.")
        return 0
    else:
        print("\nFAIL: one or more fields did not parse or classify as expected.")
        print("Raw extracted text (first 500 chars) for debugging:")
        print(text[:500])
        return 1


if __name__ == "__main__":
    sys.exit(main())
