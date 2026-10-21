from app.services.soil_parser import parse_soil_text


SAMPLE_REPORT_TEXT = """
Soil Health Card
Available Nitrogen (N): 180 kg/ha
Available Phosphorus (P): 15 kg/ha
Available Potassium (K): 260 kg/ha
pH: 6.4
Organic Carbon (OC): 0.45 %
Electrical Conductivity (EC): 0.8 dS/m
"""


def test_parses_all_core_fields():
    report = parse_soil_text(SAMPLE_REPORT_TEXT)
    assert report.nitrogen.value == 180
    assert report.phosphorus.value == 15
    assert report.potassium.value == 260
    assert report.ph.value == 6.4
    assert report.organic_carbon.value == 0.45
    assert report.electrical_conductivity.value == 0.8
    assert report.completeness() == 1.0
    assert report.extraction_warnings == []


def test_missing_fields_are_flagged():
    partial_text = "pH: 7.1\nAvailable Nitrogen (N): 100 kg/ha"
    report = parse_soil_text(partial_text)
    assert report.ph.value == 7.1
    assert report.nitrogen.value == 100
    assert report.phosphorus is None
    assert report.completeness() < 1.0
    assert any("phosphorus" in w for w in report.extraction_warnings)


def test_organic_carbon_without_abbreviation_is_still_parsed():
    """Regression test for the bug where 'Organic Carbon: 0.45%' (no '(OC)'
    abbreviation next to it) was silently parsed as UNKNOWN because the
    old regex required the literal letters 'oc' to be present in the text,
    not just optionally allowed.
    """
    text = "Organic Carbon: 0.45 %\nElectrical Conductivity: 0.32 dS/m"
    report = parse_soil_text(text)
    assert report.organic_carbon is not None
    assert report.organic_carbon.value == 0.45
    assert report.electrical_conductivity is not None
    assert report.electrical_conductivity.value == 0.32


def test_micronutrient_without_abbreviation_does_not_warn():
    """Missing/unparsed micronutrients (zinc, iron, boron, sulphur) should
    not add noisy warnings since they aren't part of the core deterministic
    engine inputs.
    """
    text = "Available Nitrogen (N): 180 kg/ha\nAvailable Phosphorus (P): 15 kg/ha\n" \
           "Available Potassium (K): 260 kg/ha\npH: 6.4\nOrganic Carbon: 0.45 %\n" \
           "Electrical Conductivity: 0.32 dS/m"
    report = parse_soil_text(text)
    assert report.extraction_warnings == []
    assert report.completeness() == 1.0


def test_parses_manganese_and_copper_with_measurements():
    """Verify that manganese and copper are extracted and stored in measurements."""
    text = (
        "Soil Health Card\n"
        "Manganese (Mn): 3.2 ppm\n"
        "Copper (Cu): 0.85 ppm\n"
        "Zinc: 0.42 ppm\n"
    )
    report = parse_soil_text(text)
    assert report.manganese is not None
    assert report.manganese.value == 3.2
    assert report.copper is not None
    assert report.copper.value == 0.85
    assert report.zinc is not None
    assert report.zinc.value == 0.42

    # Verify measurement metadata
    assert report.measurements is not None
    assert report.measurements["manganese"].status == "extracted"
    assert report.measurements["manganese"].rating == "SUFFICIENT"
    assert "3.2" in report.measurements["manganese"].source_text


def test_implausible_value_sets_needs_review_status():
    """Implausible values (e.g. pH > 11) must be marked needs_review."""
    text = "pH: 13.5\nAvailable Nitrogen: 180 kg/ha\n"
    report = parse_soil_text(text)
    assert report.ph.value == 13.5
    assert report.measurements["ph"].status == "needs_review"
    assert "outside typical soil range" in report.measurements["ph"].warning

