from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.soil import SoilReport, SoilValue
from app.services import i18n, llm_service

client = TestClient(app)


def test_normalize_language_runtime_capability():
    assert i18n.normalize_language("hi") == "hi"
    assert i18n.normalize_language("mr") == "mr"
    assert i18n.normalize_language("en") == "en"
    assert i18n.normalize_language("hi-IN") == "en"  # unsupported exact code normalizes to fallback
    assert i18n.normalize_language("fr") == "en"
    assert i18n.normalize_language(None) == "en"
    assert i18n.normalize_language("") == "en"


def test_language_instruction_safety_and_technical_terms():
    for lang in ("hi", "mr"):
        instr = i18n.llm_language_instruction(lang)
        # Must require Devanagari script
        assert "Devanagari" in instr
        # Must require keeping chemical/fertilizer names in Latin script or recognizable format
        assert "Urea" in instr or "Latin" in instr
        # Must preserve deterministic calculations and forbid invented measurements
        assert "deterministic" in instr.lower() or "unchanged" in instr.lower()
        assert "invented" in instr.lower() or "missing" in instr.lower()


def test_all_languages_have_matching_phrases_for_phase_7():
    en_keys = set(i18n.PHRASES["en"].keys())
    assert "evidence_reference" in en_keys
    assert "chat_question_ack" in en_keys
    for lang in ("hi", "mr"):
        lang_keys = set(i18n.PHRASES[lang].keys())
        assert lang_keys == en_keys, f"{lang} is missing keys: {en_keys - lang_keys}"


def test_template_fallback_in_hindi_with_question_and_evidence():
    from app.models.recommendation import Evidence, Deficiency
    evidence = [
        Evidence(
            text="According to ICAR guidelines, balanced application of NPK improves soil health.",
            source="ICAR Guidelines",
            score=0.88,
            title="ICAR Soil Fertility Guidelines",
            issuing_organization="ICAR-IISS",
        )
    ]
    deficiencies = [
        Deficiency(nutrient="nitrogen", status="LOW", detail="Low nitrogen")
    ]
    res = llm_service._template_fallback(
        deficiencies=deficiencies,
        crop_scores=[],
        fertilizer_options=[],
        application_window=None,
        contradictions=[],
        language="hi",
        user_question="यूरिया कब डालें?",
        evidence=evidence,
    )
    # Check that Hindi Devanagari is present
    assert any("\u0900" <= ch <= "\u097f" for ch in res)
    # Check that nitrogen term with Latin abbreviation is used
    assert "नाइट्रोजन (N)" in res
    assert "यूरिया कब डालें?" in res
    assert "ICAR" in res


def test_template_fallback_in_marathi_with_question_and_evidence():
    from app.models.recommendation import Evidence, Deficiency
    evidence = [
        Evidence(
            text="CGIAR soil framework recommends split nitrogen application.",
            source="CGIAR Framework",
            score=0.85,
            title="CGIAR Soil Framework",
            issuing_organization="CGIAR",
        )
    ]
    deficiencies = [
        Deficiency(nutrient="nitrogen", status="LOW", detail="Low nitrogen")
    ]
    res = llm_service._template_fallback(
        deficiencies=deficiencies,
        crop_scores=[],
        fertilizer_options=[],
        application_window=None,
        contradictions=[],
        language="mr",
        user_question="नत्र खत कधी द्यावे?",
        evidence=evidence,
    )
    # Check that Marathi Devanagari is present
    assert any("\u0900" <= ch <= "\u097f" for ch in res)
    # Check that Marathi nitrogen term is used
    assert "नत्र (N)" in res
    assert "नत्र खत कधी द्यावे?" in res


def test_chat_endpoint_in_hindi():
    payload = {
        "message": "मेरी मिट्टी में नाइट्रोजन की कमी है, क्या करूँ?",
        "language": "hi",
        "soil": {
            "nitrogen": {"value": 150, "unit": "kg/ha"},
            "phosphorus": {"value": 18, "unit": "kg/ha"},
            "potassium": {"value": 220, "unit": "kg/ha"},
            "ph": {"value": 6.8, "unit": "pH"},
        },
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert data["language"] == "hi"
    assert data["is_llm_fallback"] in (True, False)
    assert data["llm_provider"] is not None
    # Response contains Devanagari script
    assert any("\u0900" <= ch <= "\u097f" for ch in data["answer"])


def test_chat_endpoint_in_marathi():
    payload = {
        "message": "मातीमध्ये सेंद्रिय कर्ब कसा वाढवावा?",
        "language": "mr",
        "soil": {
            "nitrogen": {"value": 190, "unit": "kg/ha"},
            "phosphorus": {"value": 14, "unit": "kg/ha"},
            "potassium": {"value": 240, "unit": "kg/ha"},
            "organic_carbon": {"value": 0.42, "unit": "%"},
            "ph": {"value": 7.2, "unit": "pH"},
        },
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert data["language"] == "mr"
    assert any("\u0900" <= ch <= "\u097f" for ch in data["answer"])


def test_chat_endpoint_unsupported_language_normalizes_to_en():
    payload = {
        "message": "What fertilizer should I use for wheat?",
        "language": "es",  # Spanish not supported -> normalizes to English
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["language"] == "en"


def test_chat_contradiction_detection():
    # Nitrogen is already HIGH (620 kg/ha)
    payload = {
        "message": "Should I apply more urea to my field?",
        "language": "en",
        "soil": {
            "nitrogen": {"value": 620, "unit": "kg/ha"},
            "phosphorus": {"value": 20, "unit": "kg/ha"},
            "potassium": {"value": 250, "unit": "kg/ha"},
        },
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["contradiction_flag"] is not None
    assert "nitrogen" in data["contradiction_flag"].lower()


def test_chat_without_soil_report_does_not_crash():
    payload = {
        "message": "How does organic compost help soil biology?",
        "language": "en",
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data["answer"]) > 10
    assert isinstance(data["evidence"], list)
