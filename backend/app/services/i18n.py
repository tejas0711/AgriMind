"""Language support for AgriMind's natural-language layer only.

Deliberately scoped: structured API fields (nutrient keys, status codes like
LOW/MEDIUM/HIGH, deficiency.nutrient, etc.) stay in English always -- that's
the stable contract the frontend and any other client code already relies
on. Only the free-text explanation (LLM output, and the no-API-key template
fallback) is produced in the requested language. This keeps the rest of the
project unchanged while making the actual farmer-facing explanation
multilingual.
"""
from __future__ import annotations

SUPPORTED_LANGUAGES = ("en", "hi", "mr")
DEFAULT_LANGUAGE = "en"

LANGUAGE_NAMES = {
    "en": "English",
    "hi": "Hindi",
    "mr": "Marathi",
}


def normalize_language(language: str | None) -> str:
    if not language:
        return DEFAULT_LANGUAGE
    lang = language.strip().lower()
    return lang if lang in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE


def llm_language_instruction(language: str) -> str:
    """Appended to the LLM system prompt so the model answers in the
    requested language. The model is instructed to keep nutrient
    abbreviations (N, P, K) recognizable even in Devanagari text, since
    farmers and extension workers commonly read those as-is.
    """
    lang = normalize_language(language)
    if lang == "en":
        return "Respond in clear, plain English. Keep original numerical recommendations and soil ratings unchanged."
    name = LANGUAGE_NAMES[lang]
    return (
        f"Respond entirely in {name}, written in Devanagari script, in a natural, "
        f"conversational tone an Indian farmer would actually understand. When you mention a nutrient, "
        f"give the common {name} agricultural term followed by its English abbreviation in "
        f"parentheses the first time it's used (e.g. for nitrogen: 'नाइट्रोजन (N)' in Hindi, 'नत्र (N)' in Marathi). "
        f"Keep technical and commercial fertilizer product names (such as Urea, DAP, MOP, SSP, Zinc Sulphate / ZnSO4) "
        f"in Latin script or standard recognizable Devanagari transliteration with Latin script in parentheses. "
        f"Preserve all original deterministic calculations, crop suitability categories, and fertilizer choices strictly unchanged. "
        f"Do NOT translate missing measurements into invented values or convert uncertainty into false certainty."
    )


# ---------------------------------------------------------------------------
# Template-fallback phrase dictionary, used only when no LLM key is
# configured. Intentionally minimal -- covers the fixed sentence structure
# in llm_service._template_fallback(), not arbitrary free text. Fertilizer
# names/application notes stay in English in all languages, since they come
# from a single-source-of-truth knowledge base that isn't (yet) translated,
# and mistranslating a dosage/product name is worse than leaving it in
# English.
# ---------------------------------------------------------------------------

NUTRIENT_NAMES = {
    "en": {
        "nitrogen": "nitrogen", "phosphorus": "phosphorus", "potassium": "potassium",
        "organic_carbon": "organic carbon", "zinc": "zinc", "iron": "iron", "sulphur": "sulphur",
    },
    "hi": {
        "nitrogen": "नाइट्रोजन (N)", "phosphorus": "फास्फोरस (P)", "potassium": "पोटैशियम (K)",
        "organic_carbon": "जैविक कार्बन (OC)", "zinc": "जिंक (Zn)", "iron": "आयरन (Fe)",
        "sulphur": "सल्फर (S)",
    },
    "mr": {
        "nitrogen": "नत्र (N)", "phosphorus": "स्फुरद (P)", "potassium": "पालाश (K)",
        "organic_carbon": "सेंद्रिय कर्ब (OC)", "zinc": "जस्त (Zn)", "iron": "लोह (Fe)",
        "sulphur": "गंधक (S)",
    },
}

PHRASES = {
    "en": {
        "low_nutrients": "Your soil is currently low in {nutrients}.",
        "no_deficiency": "No major nutrient deficiencies were detected from your report.",
        "crop_score": "{crop} scores {score}/100 for suitability based on your soil data.",
        "consider": "Consider {name} ({type}) - {notes}",
        "apply_today_ok": "Current weather conditions look suitable to apply today.",
        "apply_today_wait": "Hold off on applying: {reason}",
        "next_window": "Next suitable window looks like {date}.",
        "no_key_note": "(A natural-language explanation is unavailable; showing the calculated results.)",
        "type_organic": "organic",
        "type_chemical": "chemical",
        "evidence_reference": "Verified guidance: {text}",
        "chat_question_ack": "Regarding your query '{question}':",
    },
    "hi": {
        "low_nutrients": "आपकी मिट्टी में फिलहाल {nutrients} की कमी है।",
        "no_deficiency": "आपकी रिपोर्ट में कोई बड़ी पोषक तत्व की कमी नहीं पाई गई।",
        "crop_score": "आपकी मिट्टी के आंकड़ों के अनुसार {crop} की उपयुक्तता {score}/100 है।",
        "consider": "{name} ({type}) का उपयोग करें - {notes}",
        "apply_today_ok": "आज का मौसम आवेदन के लिए उपयुक्त लग रहा है।",
        "apply_today_wait": "अभी आवेदन न करें: {reason}",
        "next_window": "अगला उपयुक्त समय लगभग {date} को हो सकता है।",
        "no_key_note": "(स्वाभाविक भाषा में व्याख्या उपलब्ध नहीं है; गणना किए गए परिणाम दिखाए जा रहे हैं।)",
        "type_organic": "जैविक",
        "type_chemical": "रासायनिक",
        "evidence_reference": "सत्यापित कृषि संदर्भ: {text}",
        "chat_question_ack": "आपके प्रश्न '{question}' के संबंध में:",
    },
    "mr": {
        "low_nutrients": "तुमच्या मातीत सध्या {nutrients} ची कमतरता आहे.",
        "no_deficiency": "तुमच्या अहवालात कोणतीही मोठी पोषक तत्वांची कमतरता आढळली नाही.",
        "crop_score": "तुमच्या मातीच्या माहितीनुसार {crop} ची योग्यता {score}/100 आहे.",
        "consider": "{name} ({type}) वापरण्याचा विचार करा - {notes}",
        "apply_today_ok": "आजचे हवामान वापरण्यासाठी योग्य दिसत आहे.",
        "apply_today_wait": "आत्ता वापर टाळा: {reason}",
        "next_window": "पुढील योग्य वेळ अंदाजे {date} असू शकते.",
        "no_key_note": "(नैसर्गिक भाषेतील स्पष्टीकरण उपलब्ध नाही; गणना केलेले परिणाम दाखवले जात आहेत.)",
        "type_organic": "सेंद्रिय",
        "type_chemical": "रासायनिक",
        "evidence_reference": "पडताळलेल्या कृषी संदर्भांनुसार: {text}",
        "chat_question_ack": "तुमच्या प्रश्नाबाबत '{question}':",
    },
}


def phrase(language: str, key: str, **kwargs) -> str:
    lang = normalize_language(language)
    template = PHRASES[lang].get(key, PHRASES["en"][key])
    return template.format(**kwargs)


def nutrient_name(language: str, nutrient_key: str) -> str:
    lang = normalize_language(language)
    return NUTRIENT_NAMES[lang].get(nutrient_key, nutrient_key.replace("_", " "))


def fertilizer_type_label(language: str, ftype: str) -> str:
    lang = normalize_language(language)
    key = "type_organic" if ftype == "organic" else "type_chemical"
    return PHRASES[lang][key]
