from app.models.soil import SoilReport, SoilValue
from app.engine.fertilizer_optimizer import detect_deficiencies, recommend_fertilizers, check_contradiction


def test_low_nitrogen_flagged_and_recommended():
    soil = SoilReport(nitrogen=SoilValue(value=100, unit="kg/ha"))
    deficiencies = detect_deficiencies(soil)
    n_def = next(d for d in deficiencies if d.nutrient == "nitrogen")
    assert n_def.status == "LOW"

    options = recommend_fertilizers(deficiencies)
    assert any(o.nutrient == "nitrogen" for o in options)


def test_high_potassium_not_recommended_further():
    soil = SoilReport(potassium=SoilValue(value=350, unit="kg/ha"))
    deficiencies = detect_deficiencies(soil)
    k_def = next(d for d in deficiencies if d.nutrient == "potassium")
    assert k_def.status == "HIGH"

    options = recommend_fertilizers(deficiencies)
    assert not any(o.nutrient == "potassium" for o in options)


def test_contradiction_detected_when_user_asks_for_high_nutrient():
    soil = SoilReport(potassium=SoilValue(value=350, unit="kg/ha"))
    deficiencies = detect_deficiencies(soil)
    warning = check_contradiction("Should I add potassium fertilizer?", deficiencies)
    assert warning is not None
    assert "potassium" in warning.lower()


def test_no_contradiction_for_low_nutrient_request():
    soil = SoilReport(nitrogen=SoilValue(value=100, unit="kg/ha"))
    deficiencies = detect_deficiencies(soil)
    warning = check_contradiction("Should I add nitrogen fertilizer?", deficiencies)
    assert warning is None


def test_nitrogen_180_kgha_is_low_per_official_shc_scale():
    """Regression test: a real demo lab report rates 180 kg/ha nitrogen as
    LOW (alkaline permanganate method, official scale 280/560), but an
    earlier version of this engine used (140, 280) and wrongly classified
    it as MEDIUM -- silently skipping a nitrogen recommendation the farmer
    actually needed.
    """
    soil = SoilReport(nitrogen=SoilValue(value=180, unit="kg/ha"))
    deficiencies = detect_deficiencies(soil)
    n_def = next(d for d in deficiencies if d.nutrient == "nitrogen")
    assert n_def.status == "LOW"

    options = recommend_fertilizers(deficiencies)
    assert any(o.nutrient == "nitrogen" for o in options)


def test_matches_real_demo_report_ratings():
    """Cross-checks against the exact values/ratings printed on a real
    soil-test report (N=180 LOW, P=15 MEDIUM, K=260 MEDIUM/MED-HIGH,
    OC=0.45 LOW, Zn=0.42 DEFICIENT, Fe=4.8 ADEQUATE, S=18 SUFFICIENT).
    """
    soil = SoilReport(
        nitrogen=SoilValue(value=180, unit="kg/ha"),
        phosphorus=SoilValue(value=15, unit="kg/ha"),
        potassium=SoilValue(value=260, unit="kg/ha"),
        organic_carbon=SoilValue(value=0.45, unit="%"),
        zinc=SoilValue(value=0.42, unit="ppm"),
        iron=SoilValue(value=4.8, unit="ppm"),
        sulphur=SoilValue(value=18, unit="ppm"),
    )
    deficiencies = {d.nutrient: d for d in detect_deficiencies(soil)}

    assert deficiencies["nitrogen"].status == "LOW"
    assert deficiencies["phosphorus"].status == "MEDIUM"
    assert deficiencies["potassium"].status == "MEDIUM"
    assert deficiencies["organic_carbon"].status == "LOW"
    assert deficiencies["zinc"].status == "LOW"       # DEFICIENT
    assert deficiencies["iron"].status == "HIGH"      # ADEQUATE
    assert deficiencies["sulphur"].status == "HIGH"   # SUFFICIENT


def test_zinc_deficiency_triggers_fertilizer_recommendation():
    soil = SoilReport(zinc=SoilValue(value=0.42, unit="ppm"))
    deficiencies = detect_deficiencies(soil)
    options = recommend_fertilizers(deficiencies)
    assert any(o.nutrient == "zinc" and "znso4" in o.name.lower() or "zinc sulphate" in o.name.lower() for o in options)


def test_adequate_iron_not_recommended():
    soil = SoilReport(iron=SoilValue(value=4.8, unit="ppm"))
    deficiencies = detect_deficiencies(soil)
    options = recommend_fertilizers(deficiencies)
    assert not any(o.nutrient == "iron" for o in options)
