from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.models.soil import SoilReport
from app.models.recommendation import ApplicationWindow
from app.rag.retriever import retrieve
from app.engine.fertilizer_optimizer import detect_deficiencies, check_contradiction
from app.services import llm_service
from app.services.i18n import normalize_language
from app.agents.weather_agent import run_weather_agent

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str
    soil: SoilReport | None = None
    selected_crop: str | None = None
    location: str | None = None
    application_window: ApplicationWindow | None = None
    language: str = "en"  # "en" | "hi" | "mr"


class ChatResponse(BaseModel):
    answer: str
    evidence: list[dict]
    contradiction_flag: str | None = None
    llm_provider: str | None = None
    llm_model: str | None = None
    is_llm_fallback: bool = False
    language: str = "en"


import re
from app.services import weather_service

DEVANAGARI_MAHARASHTRA_MAP = {
    "मुंबई": "Mumbai",
    "पुणे": "Pune",
    "नागपूर": "Nagpur",
    "नाशिक": "Nashik",
    "ठाणे": "Thane",
    "सोलापूर": "Solapur",
    "अमरावती": "Amravati",
    "कोल्हापूर": "Kolhapur",
    "नांदेड": "Nanded",
    "सांगली": "Sangli",
    "जळगाव": "Jalgaon",
    "अकोला": "Akola",
    "लातूर": "Latur",
    "धुळे": "Dhule",
    "अहमदनगर": "Ahmednagar",
    "अहिल्यानगर": "Ahilyanagar",
    "चंद्रपूर": "Chandrapur",
    "परभणी": "Parbhani",
    "जालना": "Jalna",
    "बीड": "Beed",
    "गोंदिया": "Gondia",
    "सातारा": "Satara",
    "यवतमाळ": "Yavatmal",
    "धाराशिव": "Dharashiv",
    "उस्मानाबाद": "Osmanabad",
    "नंदुरबार": "Nandurbar",
    "वर्धा": "Wardha",
    "भंडारा": "Bhandara",
    "बुलढाणा": "Buldhana",
    "वाशीम": "Washim",
    "रत्नागिरी": "Ratnagiri",
    "सिंधुदुर्ग": "Sindhudurg",
    "रायगड": "Raigad",
    "गडचिरोली": "Gadchiroli",
    "पालघर": "Palghar",
    "औरंगाबाद": "Aurangabad",
    "छत्रपती संभाजीनगर": "Chhatrapati Sambhajinagar",
    "संभाजीनगर": "Sambhajinagar",
    "बारामती": "Baramati",
    "कराड": "Karad",
    "पंढरपूर": "Pandharpur",
    "मालेगाव": "Malegaon",
    "शिर्डी": "Shirdi",
    "नवी मुंबई": "Navi Mumbai",
    "कल्याण": "Kalyan",
    "डोंबिवली": "Dombivli",
    "पनवेल": "Panvel",
    "वसई": "Vasai",
    "विरार": "Virar",
    "इचलकरंजी": "Ichalkaranji",
}

MAHARASHTRA_PLACES = [
    "mumbai", "pune", "nagpur", "nashik", "thane", "solapur", "amravati",
    "kolhapur", "nanded", "sangli", "jalgaon", "akola", "latur", "dhule",
    "ahmednagar", "ahilyanagar", "chandrapur", "parbhani", "jalna", "beed",
    "gondia", "satara", "yavatmal", "osmanabad", "dharashiv", "nandurbar",
    "wardha", "bhandara", "buldhana", "washim", "ratnagiri", "sindhudurg",
    "raigad", "gadchiroli", "palghar", "aurangabad", "chhatrapati sambhajinagar",
    "sambhajinagar", "baramati", "karad", "pandharpur", "malegaon", "shirdi",
    "navi mumbai", "kalyan", "dombivli", "panvel", "vasai", "virar", "ichalkaranji"
]


def extract_location_from_message(message: str) -> str | None:
    """Extracts any mentioned city/district/place from user chat query."""
    if not message:
        return None
    msg = message.strip()
    msg_lower = msg.lower()

    # 1. Check Devanagari Maharashtra place names / substrings
    for dev_name, eng_name in DEVANAGARI_MAHARASHTRA_MAP.items():
        if dev_name in msg:
            return eng_name
        stem = dev_name[:-1] if len(dev_name) > 3 else dev_name
        if stem in msg:
            return eng_name

    # 2. Check English Maharashtra place names with word boundaries
    for place in MAHARASHTRA_PLACES:
        if re.search(r'\b' + re.escape(place) + r'\b', msg_lower):
            return place.title()

    # 3. Check prepositions "in <place>", "at <place>", "for <place>", "of <place>", "near <place>"
    m = re.search(
        r'(?:in|at|for|of|near|around)\s+([A-Za-z\u0900-\u097F\s]{2,30}?)(?:\s+(?:now|today|currently|right\s+now|weather|temperature|temp|please|\?|\.|$)|$)',
        msg,
        re.I
    )
    if m:
        cand = m.group(1).strip()
        cand = re.sub(r'[?!.,;]+$', '', cand).strip()
        if cand and len(cand) >= 2:
            return cand

    # 4. Check "<place> weather / temperature / temp / forecast"
    m2 = re.search(
        r'([A-Za-z\u0900-\u097F\s]{2,30}?)\s+(?:weather|temperature|temp|forecast|rain|climate|हवामान|तापमान|पाऊस)',
        msg,
        re.I
    )
    if m2:
        cand = m2.group(1).strip()
        cand = re.sub(r'^(?:what\s+is\s+the|what\s+about|check|how\s+is\s+the)\s+', '', cand, flags=re.I).strip()
        cand = re.sub(r'[?!.,;]+$', '', cand).strip()
        if cand and len(cand) >= 2:
            return cand

    return None


@router.post("", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    lang = normalize_language(req.language)
    evidence = retrieve(req.message, top_k=4)

    contradiction = None
    deficiencies = []
    if req.soil:
        deficiencies = detect_deficiencies(req.soil)
        contradiction = check_contradiction(req.message, deficiencies)

    # Resolve live weather context so the LLM can answer temperature and timing questions
    app_window = req.application_window
    loc = (req.location or "").strip()
    weather_terms = [
        "weather", "temperature", "temp", "rain", "forecast", "wind", "humidity",
        "spray", "apply", "urea", "timing", "today", "tomorrow", "now", "current",
        "मौसम", "तापमान", "बारिश", "हवा", "यूरिया", "आज", "अभी",
        "हवामान", "पाऊस", "वारं", "वार", "उष्णता", "सध्या",
    ]
    msg_lower = req.message.lower()
    asking_weather = any(term in msg_lower for term in weather_terms)

    # Check if a specific location was mentioned in the user's message
    mentioned_loc = extract_location_from_message(req.message)

    # If user mentioned a location or asked about weather, or app_window is missing, fetch fresh real weather
    if mentioned_loc or asking_weather or not app_window or not getattr(app_window, "forecast_summary", None) or getattr(app_window, "current_temperature_c", None) is None:
        target_loc = mentioned_loc or loc or (getattr(app_window, "location_name", None) if app_window else None) or "Pune, Maharashtra"
        try:
            if mentioned_loc:
                # Prefer geocoding with Maharashtra context
                geo_info = await weather_service.geocode_location_info(f"{mentioned_loc}, Maharashtra")
                if not geo_info:
                    geo_info = await weather_service.geocode_location_info(mentioned_loc)
                if geo_info:
                    fresh_window = await run_weather_agent(
                        latitude=geo_info["latitude"],
                        longitude=geo_info["longitude"],
                        location_name=geo_info.get("formatted_name", mentioned_loc),
                        needs_application=True
                    )
                else:
                    fresh_window = await run_weather_agent(location_name=target_loc, needs_application=True)
            else:
                fresh_window = await run_weather_agent(location_name=target_loc, needs_application=True)

            if fresh_window and fresh_window.is_available:
                app_window = fresh_window
        except Exception:
            pass

    res = await llm_service.generate_explanation_result(
        soil=req.soil or SoilReport(),
        deficiencies=deficiencies,
        crop_scores=[],
        fertilizer_options=[],
        application_window=app_window,
        evidence=evidence,
        user_question=req.message,
        contradictions=[contradiction] if contradiction else [],
        language=lang,
    )

    return ChatResponse(
        answer=res.explanation,
        evidence=[e.model_dump() for e in evidence],
        contradiction_flag=contradiction,
        llm_provider=res.provider,
        llm_model=res.model,
        is_llm_fallback=res.is_fallback,
        language=lang,
    )
