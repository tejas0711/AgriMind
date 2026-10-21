from app.services import i18n


def test_normalize_language_defaults_to_english():
    assert i18n.normalize_language(None) == "en"
    assert i18n.normalize_language("") == "en"
    assert i18n.normalize_language("fr") == "en"  # unsupported language falls back
    assert i18n.normalize_language("HI") == "hi"  # case-insensitive


def test_all_languages_have_matching_phrase_keys():
    en_keys = set(i18n.PHRASES["en"].keys())
    for lang in i18n.SUPPORTED_LANGUAGES:
        assert set(i18n.PHRASES[lang].keys()) == en_keys, f"{lang} phrase keys don't match en"


def test_all_languages_have_matching_nutrient_keys():
    en_keys = set(i18n.NUTRIENT_NAMES["en"].keys())
    for lang in i18n.SUPPORTED_LANGUAGES:
        assert set(i18n.NUTRIENT_NAMES[lang].keys()) == en_keys, f"{lang} nutrient keys don't match en"


def test_phrase_formatting_works_for_every_language():
    for lang in i18n.SUPPORTED_LANGUAGES:
        result = i18n.phrase(lang, "crop_score", crop="Tomato", score=90)
        assert "Tomato" in result
        assert "90" in result


def test_hindi_and_marathi_use_devanagari_script():
    # Rough sanity check: Devanagari Unicode block is U+0900-U+097F
    for lang in ("hi", "mr"):
        text = i18n.phrase(lang, "no_deficiency")
        assert any("\u0900" <= ch <= "\u097f" for ch in text), f"{lang} phrase has no Devanagari characters"


def test_english_explanation_has_no_devanagari():
    text = i18n.phrase("en", "no_deficiency")
    assert not any("\u0900" <= ch <= "\u097f" for ch in text)


def test_llm_language_instruction_mentions_target_language():
    assert "Hindi" in i18n.llm_language_instruction("hi")
    assert "Marathi" in i18n.llm_language_instruction("mr")
    assert "English" in i18n.llm_language_instruction("en")
