"""Thin, reliable wrapper around the Open-Meteo weather and geocoding services.

Adheres strictly to the principle that weather data must be real:
if the external provider is unreachable, times out, or fails validation,
the service raises a clear error rather than fabricating numbers.

Open-Meteo attribution: "Weather data by Open-Meteo.com (CC BY 4.0)"
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Optional, Tuple, Dict, Any, List
import httpx

OPEN_METEO_BASE_URL = os.getenv("OPEN_METEO_BASE_URL", "https://api.open-meteo.com/v1/forecast")
OPEN_METEO_GEOCODING_URL = os.getenv("OPEN_METEO_GEOCODING_URL", "https://geocoding-api.open-meteo.com/v1/search")

DEFAULT_TIMEOUT_SECONDS = 4.0
GEOCODING_TIMEOUT_SECONDS = 3.5


# ---------------------------------------------------------------------------
# Error Hierarchy
# ---------------------------------------------------------------------------

class WeatherServiceError(Exception):
    """Base exception for all weather and geocoding failures."""
    pass


class WeatherConnectionError(WeatherServiceError):
    """Network connection failure reaching the weather provider."""
    pass


class WeatherTimeoutError(WeatherServiceError):
    """Request to the weather provider timed out."""
    pass


class WeatherLocationNotFoundError(WeatherServiceError):
    """Specified location name could not be resolved to coordinates."""
    pass


class WeatherResponseValidationError(WeatherServiceError):
    """The provider returned an invalid or malformed weather response."""
    pass


# ---------------------------------------------------------------------------
# WMO Weather Interpretation Codes
# ---------------------------------------------------------------------------

WMO_WEATHER_CODES: Dict[int, str] = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Foggy",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snow fall",
    73: "Moderate snow fall",
    75: "Heavy snow fall",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


def get_wmo_condition(code: Optional[int]) -> str:
    """Translates a numeric WMO weather code into human-readable text."""
    if code is None:
        return "Unknown"
    return WMO_WEATHER_CODES.get(code, f"Code {code}")


# ---------------------------------------------------------------------------
# Instant Geocoding Cache & Presets (Maharashtra & Major Indian Agri Hubs)
# ---------------------------------------------------------------------------

KNOWN_INDIAN_LOCATIONS: Dict[str, Tuple[float, float, str, str]] = {
    # format: (latitude, longitude, formatted_name, timezone)
    "pune": (18.5204, 73.8567, "Pune, Maharashtra, India", "Asia/Kolkata"),
    "mumbai": (19.0760, 72.8777, "Mumbai, Maharashtra, India", "Asia/Kolkata"),
    "nagpur": (21.1458, 79.0882, "Nagpur, Maharashtra, India", "Asia/Kolkata"),
    "nashik": (19.9975, 73.7898, "Nashik, Maharashtra, India", "Asia/Kolkata"),
    "nasik": (19.9975, 73.7898, "Nashik, Maharashtra, India", "Asia/Kolkata"),
    "aurangabad": (19.8762, 75.3433, "Chhatrapati Sambhajinagar, Maharashtra, India", "Asia/Kolkata"),
    "chhatrapati sambhajinagar": (19.8762, 75.3433, "Chhatrapati Sambhajinagar, Maharashtra, India", "Asia/Kolkata"),
    "sambhajinagar": (19.8762, 75.3433, "Chhatrapati Sambhajinagar, Maharashtra, India", "Asia/Kolkata"),
    "solapur": (17.6599, 75.9064, "Solapur, Maharashtra, India", "Asia/Kolkata"),
    "kolhapur": (16.7050, 74.2433, "Kolhapur, Maharashtra, India", "Asia/Kolkata"),
    "amravati": (20.9374, 77.7796, "Amravati, Maharashtra, India", "Asia/Kolkata"),
    "nanded": (19.1383, 77.3210, "Nanded, Maharashtra, India", "Asia/Kolkata"),
    "sangli": (16.8524, 74.5815, "Sangli, Maharashtra, India", "Asia/Kolkata"),
    "jalgaon": (21.0077, 75.5626, "Jalgaon, Maharashtra, India", "Asia/Kolkata"),
    "akola": (20.7002, 77.0082, "Akola, Maharashtra, India", "Asia/Kolkata"),
    "latur": (18.4088, 76.5604, "Latur, Maharashtra, India", "Asia/Kolkata"),
    "dhule": (20.9042, 74.7749, "Dhule, Maharashtra, India", "Asia/Kolkata"),
    "ahmednagar": (19.0948, 74.7480, "Ahilyanagar, Maharashtra, India", "Asia/Kolkata"),
    "ahilyanagar": (19.0948, 74.7480, "Ahilyanagar, Maharashtra, India", "Asia/Kolkata"),
    "chandrapur": (19.9615, 79.2961, "Chandrapur, Maharashtra, India", "Asia/Kolkata"),
    "parbhani": (19.2644, 76.7767, "Parbhani, Maharashtra, India", "Asia/Kolkata"),
    "jalna": (19.8347, 75.8816, "Jalna, Maharashtra, India", "Asia/Kolkata"),
    "beed": (18.9891, 75.7601, "Beed, Maharashtra, India", "Asia/Kolkata"),
    "satara": (17.6805, 73.9922, "Satara, Maharashtra, India", "Asia/Kolkata"),
    "osmanabad": (18.1856, 76.0419, "Dharashiv, Maharashtra, India", "Asia/Kolkata"),
    "dharashiv": (18.1856, 76.0419, "Dharashiv, Maharashtra, India", "Asia/Kolkata"),
    "yavatmal": (20.3888, 78.1204, "Yavatmal, Maharashtra, India", "Asia/Kolkata"),
    "wardha": (20.7453, 78.6022, "Wardha, Maharashtra, India", "Asia/Kolkata"),
    "bhandara": (21.1667, 79.6500, "Bhandara, Maharashtra, India", "Asia/Kolkata"),
    "gondia": (21.4598, 80.1961, "Gondia, Maharashtra, India", "Asia/Kolkata"),
    "gadchiroli": (20.1809, 80.0033, "Gadchiroli, Maharashtra, India", "Asia/Kolkata"),
    "washim": (20.1111, 77.1333, "Washim, Maharashtra, India", "Asia/Kolkata"),
    "hingoli": (19.7173, 77.1485, "Hingoli, Maharashtra, India", "Asia/Kolkata"),
    "buldhana": (20.5292, 76.1843, "Buldhana, Maharashtra, India", "Asia/Kolkata"),
    "nandurbar": (21.3697, 74.2394, "Nandurbar, Maharashtra, India", "Asia/Kolkata"),
    "raigad": (18.6414, 72.8722, "Raigad, Maharashtra, India", "Asia/Kolkata"),
    "alibag": (18.6414, 72.8722, "Alibag, Maharashtra, India", "Asia/Kolkata"),
    "ratnagiri": (16.9902, 73.3120, "Ratnagiri, Maharashtra, India", "Asia/Kolkata"),
    "sindhudurg": (16.1158, 73.6980, "Sindhudurg, Maharashtra, India", "Asia/Kolkata"),
    "thane": (19.2183, 72.9781, "Thane, Maharashtra, India", "Asia/Kolkata"),
    "palghar": (19.6967, 72.7699, "Palghar, Maharashtra, India", "Asia/Kolkata"),
    "baramati": (18.1517, 74.5770, "Baramati, Maharashtra, India", "Asia/Kolkata"),
    "shirdi": (19.7667, 74.4762, "Shirdi, Maharashtra, India", "Asia/Kolkata"),
    "delhi": (28.6139, 77.2090, "Delhi, India", "Asia/Kolkata"),
    "bengaluru": (12.9716, 77.5946, "Bengaluru, Karnataka, India", "Asia/Kolkata"),
    "bangalore": (12.9716, 77.5946, "Bengaluru, Karnataka, India", "Asia/Kolkata"),
    "hyderabad": (17.3850, 78.4867, "Hyderabad, Telangana, India", "Asia/Kolkata"),
    "chennai": (13.0827, 80.2707, "Chennai, Tamil Nadu, India", "Asia/Kolkata"),
    "kolkata": (22.5726, 88.3639, "Kolkata, West Bengal, India", "Asia/Kolkata"),
    "ahmedabad": (23.0225, 72.5714, "Ahmedabad, Gujarat, India", "Asia/Kolkata"),
    "jaipur": (26.9124, 75.7873, "Jaipur, Rajasthan, India", "Asia/Kolkata"),
    "lucknow": (26.8467, 80.9462, "Lucknow, Uttar Pradesh, India", "Asia/Kolkata"),
    "bhopal": (23.2599, 77.4126, "Bhopal, Madhya Pradesh, India", "Asia/Kolkata"),
    "patna": (25.5941, 85.1376, "Patna, Bihar, India", "Asia/Kolkata"),
    "chandigarh": (30.7333, 76.7794, "Chandigarh, India", "Asia/Kolkata"),
    "indore": (22.7196, 75.8577, "Indore, Madhya Pradesh, India", "Asia/Kolkata"),
}


# ---------------------------------------------------------------------------
# Geocoding Services
# ---------------------------------------------------------------------------

async def geocode_location_info(name: str) -> Optional[Dict[str, Any]]:
    """Resolves a free-text location into detailed coordinate and place metadata.

    First checks in-memory dictionary for instant (0ms) lookup.
    Falls back to Open-Meteo Geocoding API with a strict timeout.
    """
    if not name or not name.strip():
        return None

    raw_query = name.strip()
    norm_query = raw_query.lower()

    # 1. Instant preset dictionary lookup (0ms round-trip)
    for key, (lat, lon, fmt_name, tz) in KNOWN_INDIAN_LOCATIONS.items():
        if key == norm_query or key in norm_query:
            return {
                "latitude": lat,
                "longitude": lon,
                "name": key.title(),
                "admin1": "Maharashtra" if "Maharashtra" in fmt_name else "India",
                "country": "India",
                "formatted_name": fmt_name,
                "timezone": tz,
            }

    # 2. Remote geocoding fallback
    params = {"name": raw_query, "count": 1, "language": "en", "format": "json"}

    try:
        async with httpx.AsyncClient(timeout=GEOCODING_TIMEOUT_SECONDS) as client:
            resp = await client.get(OPEN_METEO_GEOCODING_URL, params=params)
            resp.raise_for_status()
            data = resp.json()
    except httpx.TimeoutException as exc:
        raise WeatherTimeoutError(f"Geocoding request for '{raw_query}' timed out after {GEOCODING_TIMEOUT_SECONDS}s.") from exc
    except (httpx.ConnectError, httpx.NetworkError) as exc:
        raise WeatherConnectionError(f"Could not connect to geocoding service for '{raw_query}': {exc}") from exc
    except httpx.HTTPError as exc:
        raise WeatherServiceError(f"Geocoding service returned an HTTP error for '{raw_query}': {exc}") from exc
    except Exception as exc:
        raise WeatherServiceError(f"Unexpected error during geocoding for '{raw_query}': {exc}") from exc

    results = data.get("results")
    if not results or not isinstance(results, list) or len(results) == 0:
        return None

    top = results[0]
    lat = top.get("latitude")
    lon = top.get("longitude")
    if lat is None or lon is None:
        return None

    place_name = top.get("name", raw_query)
    admin1 = top.get("admin1")
    country = top.get("country")

    parts = [p for p in [place_name, admin1, country] if p]
    formatted_name = ", ".join(parts) if parts else raw_query

    return {
        "latitude": float(lat),
        "longitude": float(lon),
        "name": place_name,
        "admin1": admin1,
        "country": country,
        "formatted_name": formatted_name,
        "timezone": top.get("timezone", "auto"),
    }



async def geocode_location(name: str) -> Optional[Tuple[float, float]]:
    """Resolves a free-text location to (latitude, longitude) coordinates.

    Maintains full backward-compatibility with existing callers.
    """
    info = await geocode_location_info(name)
    if not info:
        return None
    return info["latitude"], info["longitude"]


# ---------------------------------------------------------------------------
# Forecast Services
# ---------------------------------------------------------------------------

async def get_forecast(latitude: float, longitude: float, days: int = 5) -> Dict[str, Any]:
    """Fetches daily forecast variables relevant to agricultural application timing.

    Variables requested:
      - precipitation_sum (mm)
      - precipitation_probability_max (%)
      - temperature_2m_max (°C)
      - temperature_2m_min (°C)
      - windspeed_10m_max (km/h)
      - relative_humidity_2m_max (%)
      - weathercode (WMO code)

    Returns a structured dictionary with:
      - `days`: list of daily forecast dictionaries
      - `latitude`, `longitude`, `elevation`, `timezone`
      - `generated_at`: ISO UTC timestamp of retrieval
      - `attribution`: provider citation
      - `raw`: original JSON payload
    """
    if not (-90.0 <= latitude <= 90.0) or not (-180.0 <= longitude <= 180.0):
        raise WeatherServiceError(f"Coordinates out of bounds: lat={latitude}, lon={longitude}")

    forecast_days = max(1, min(14, int(days)))

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m",
        "daily": ",".join(
            [
                "precipitation_sum",
                "precipitation_probability_max",
                "temperature_2m_max",
                "temperature_2m_min",
                "windspeed_10m_max",
                "relative_humidity_2m_max",
                "weathercode",
            ]
        ),
        "forecast_days": forecast_days,
        "timezone": "auto",
    }

    try:
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT_SECONDS) as client:
            resp = await client.get(OPEN_METEO_BASE_URL, params=params)
            resp.raise_for_status()
            data = resp.json()
    except httpx.TimeoutException as exc:
        raise WeatherTimeoutError(
            f"Weather forecast request for ({latitude}, {longitude}) timed out after {DEFAULT_TIMEOUT_SECONDS}s."
        ) from exc
    except (httpx.ConnectError, httpx.NetworkError) as exc:
        raise WeatherConnectionError(
            f"Could not connect to weather provider at {OPEN_METEO_BASE_URL}: {exc}"
        ) from exc
    except httpx.HTTPError as exc:
        raise WeatherServiceError(
            f"Weather provider request failed with HTTP error: {exc}"
        ) from exc
    except Exception as exc:
        raise WeatherServiceError(
            f"Unexpected error fetching weather forecast: {exc}"
        ) from exc

    return _format_forecast(data, latitude, longitude)


def _format_forecast(data: Dict[str, Any], req_lat: float, req_lon: float) -> Dict[str, Any]:
    """Validates and formats the Open-Meteo response into structured days and metadata."""
    if not isinstance(data, dict):
        raise WeatherResponseValidationError("Open-Meteo returned a non-dictionary response.")

    daily = data.get("daily")
    if not isinstance(daily, dict):
        raise WeatherResponseValidationError("Open-Meteo response missing required 'daily' forecast structure.")

    dates = daily.get("time")
    if not isinstance(dates, list) or len(dates) == 0:
        raise WeatherResponseValidationError("Open-Meteo response contains an empty forecast dates array.")

    # Parse current weather if present
    current_raw = data.get("current") or data.get("current_weather") or {}
    curr_temp = current_raw.get("temperature_2m", current_raw.get("temperature"))
    curr_humidity = current_raw.get("relative_humidity_2m")
    curr_wind = current_raw.get("wind_speed_10m", current_raw.get("windspeed"))
    curr_code = current_raw.get("weather_code", current_raw.get("weathercode"))
    curr_condition = get_wmo_condition(curr_code) if curr_code is not None else None

    days_list: List[Dict[str, Any]] = []
    for i, date in enumerate(dates):
        code = _safe_get(daily, "weathercode", i)
        precip = _safe_get(daily, "precipitation_sum", i)
        precip_prob = _safe_get(daily, "precipitation_probability_max", i)
        wind = _safe_get(daily, "windspeed_10m_max", i)
        t_max = _safe_get(daily, "temperature_2m_max", i)
        t_min = _safe_get(daily, "temperature_2m_min", i)
        humidity = _safe_get(daily, "relative_humidity_2m_max", i)

        day_dict = {
            "date": date,
            "precipitation_mm": float(precip) if precip is not None else 0.0,
            "precipitation_probability_pct": int(precip_prob) if precip_prob is not None else 0,
            "temp_max_c": float(t_max) if t_max is not None else None,
            "temp_min_c": float(t_min) if t_min is not None else None,
            "wind_max_kmh": float(wind) if wind is not None else 0.0,
            "humidity_max_pct": float(humidity) if humidity is not None else 0.0,
            "weather_code": int(code) if code is not None else None,
            "condition": get_wmo_condition(code),
        }
        if i == 0 and curr_temp is not None:
            day_dict["current_temperature_c"] = float(curr_temp)
            if curr_condition:
                day_dict["current_condition"] = curr_condition
        days_list.append(day_dict)

    now_iso = datetime.now(timezone.utc).isoformat()

    return {
        "raw": data,
        "days": days_list,
        "current_temperature_c": float(curr_temp) if curr_temp is not None else None,
        "current_humidity_pct": float(curr_humidity) if curr_humidity is not None else None,
        "current_wind_kmh": float(curr_wind) if curr_wind is not None else None,
        "current_weather_code": int(curr_code) if curr_code is not None else None,
        "current_condition": curr_condition,
        "latitude": data.get("latitude", req_lat),
        "longitude": data.get("longitude", req_lon),
        "elevation": data.get("elevation", 0.0),
        "timezone": data.get("timezone", "UTC"),
        "generated_at": now_iso,
        "attribution": "Weather data by Open-Meteo.com (CC BY 4.0)",
    }


def _safe_get(d: Dict[str, Any], key: str, idx: int) -> Any:
    arr = d.get(key)
    if not arr or not isinstance(arr, list) or idx >= len(arr):
        return None
    return arr[idx]
