from app.models.soil import SoilReport, SoilValue
from app.engine.crop_scorer import rank_crops
from app.services.crop_service import get_crop


def _good_tomato_soil() -> SoilReport:
    return SoilReport(
        nitrogen=SoilValue(value=150, unit="kg/ha"),
        phosphorus=SoilValue(value=20, unit="kg/ha"),
        potassium=SoilValue(value=200, unit="kg/ha"),
        ph=SoilValue(value=6.5),
        organic_carbon=SoilValue(value=0.6, unit="%"),
    )


def test_tomato_scores_well_on_matching_soil():
    soil = _good_tomato_soil()
    scores = rank_crops(soil, current_season="rabi", top_n=8)
    tomato_score = next(s for s in scores if s.name == "Tomato")
    assert tomato_score.ph_fit is True
    assert tomato_score.score >= 80


def test_rice_scores_lower_on_upland_soil_with_wrong_season():
    soil = _good_tomato_soil()
    scores = rank_crops(soil, current_season="rabi", top_n=8)
    rice_score = next(s for s in scores if s.name == "Rice (Paddy)")
    assert rice_score.season_fit is False


def test_get_crop_lookup_is_case_insensitive():
    assert get_crop("tomato") is not None
    assert get_crop("ToMaTo") is not None
    assert get_crop("nonexistent-crop") is None
