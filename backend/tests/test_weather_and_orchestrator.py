"""
Comprehensive unit and integration tests for Weather Service, Weather Agent,
Multi-Agent Orchestrator, and API endpoints.

Covers:
- Geocoding success, location not found, and network timeout handling
- Forecast parsing, WMO code translation, and units
- Upstream network errors, timeouts, and zero fake-data guarantee
- Agronomic application-window rules (runoff, wind drift, heat, clear window)
- Weather Agent execution with real location resolution
- Partial failure handling in the Orchestrator
- Weather & Analysis API endpoints
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import httpx
from fastapi.testclient import TestClient

from app.main import app
from app.services.weather_service import (
    geocode_location_info,
    geocode_location,
    get_forecast,
    get_wmo_condition,
    WeatherServiceError,
    WeatherTimeoutError,
    WeatherConnectionError,
    WeatherLocationNotFoundError,
    WeatherResponseValidationError,
)
from app.engine.application_window import assess_application_window
from app.agents.weather_agent import run_weather_agent
from app.agents.orchestrator import orchestrate
from app.models.soil import SoilReport, SoilValue

client = TestClient(app)

MOCK_GEOCODING_RESPONSE = {
    "results": [
        {
            "name": "Pune",
            "latitude": 18.5204,
            "longitude": 73.8567,
            "country": "India",
            "admin1": "Maharashtra",
            "timezone": "Asia/Kolkata",
        }
    ]
}

MOCK_FORECAST_PAYLOAD = {
    "latitude": 18.5204,
    "longitude": 73.8567,
    "elevation": 560.0,
    "timezone": "Asia/Kolkata",
    "daily": {
        "time": ["2026-10-20", "2026-10-21", "2026-10-22"],
        "temperature_2m_max": [31.5, 32.0, 30.0],
        "temperature_2m_min": [19.2, 18.5, 19.0],
        "precipitation_sum": [0.0, 15.2, 0.0],
        "precipitation_probability_max": [10, 85, 20],
        "windspeed_10m_max": [12.4, 18.1, 14.0],
        "relative_humidity_2m_max": [55.0, 80.0, 60.0],
        "weathercode": [0, 63, 1],
    },
}


# ============================================================================
# 1. Weather Service: Geocoding Tests
# ============================================================================

@pytest.mark.asyncio
async def test_geocoding_success():
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = MOCK_GEOCODING_RESPONSE

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_resp):
        loc = await geocode_location_info("Pune")
        assert loc is not None
        assert loc["name"] == "Pune"
        assert abs(loc["latitude"] - 18.5204) < 0.01
        assert abs(loc["longitude"] - 73.8567) < 0.01
        assert loc["admin1"] == "Maharashtra"
        assert "Pune" in loc["formatted_name"]


@pytest.mark.asyncio
async def test_geocoding_tuple_helper():
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = MOCK_GEOCODING_RESPONSE

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_resp):
        coords = await geocode_location("Pune")
        assert coords is not None
        lat, lon = coords
        assert abs(lat - 18.5204) < 0.01
        assert abs(lon - 73.8567) < 0.01


@pytest.mark.asyncio
async def test_geocoding_unknown_location_returns_none():
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {"results": []}

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_resp):
        loc = await geocode_location_info("UnknownNonExistentCityXYZ999")
        assert loc is None


@pytest.mark.asyncio
async def test_geocoding_timeout_raises_weather_timeout():
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock, side_effect=httpx.TimeoutException("Timeout")):
        with pytest.raises(WeatherTimeoutError):
            await geocode_location_info("RemoteUncachedTown")



# ============================================================================
# 2. Weather Service: Forecast & Zero Fake-Data Tests
# ============================================================================

@pytest.mark.asyncio
async def test_forecast_fetch_success():
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = MOCK_FORECAST_PAYLOAD

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_resp):
        result = await get_forecast(18.5204, 73.8567, days=3)
        assert "days" in result
        days = result["days"]
        assert len(days) == 3

        day1 = days[0]
        assert day1["date"] == "2026-10-20"
        assert day1["temp_max_c"] == 31.5
        assert day1["temp_min_c"] == 19.2
        assert day1["precipitation_mm"] == 0.0
        assert day1["precipitation_probability_pct"] == 10
        assert day1["wind_max_kmh"] == 12.4
        assert day1["condition"] == "Clear sky"

        day2 = days[1]
        assert day2["precipitation_mm"] == 15.2
        assert day2["precipitation_probability_pct"] == 85
        assert "rain" in day2["condition"].lower()

        assert "Open-Meteo" in result["attribution"]
        assert result["generated_at"] is not None


@pytest.mark.asyncio
async def test_forecast_http_error_does_not_invent_data():
    mock_resp = MagicMock()
    mock_resp.status_code = 503
    mock_resp.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Service Unavailable", request=MagicMock(), response=mock_resp
    )

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_resp):
        with pytest.raises(WeatherServiceError):
            await get_forecast(18.5204, 73.8567)


@pytest.mark.asyncio
async def test_forecast_timeout_does_not_invent_data():
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock, side_effect=httpx.TimeoutException("Connection timed out")):
        with pytest.raises(WeatherTimeoutError):
            await get_forecast(18.5204, 73.8567)


@pytest.mark.asyncio
async def test_forecast_malformed_response_raises_validation_error():
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {"daily": {"time": []}}  # Empty dates list

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_resp):
        with pytest.raises(WeatherResponseValidationError):
            await get_forecast(18.5204, 73.8567)


def test_wmo_weather_code_translations():
    assert get_wmo_condition(0) == "Clear sky"
    assert "rain" in get_wmo_condition(63).lower()
    assert "thunderstorm" in get_wmo_condition(95).lower()
    assert get_wmo_condition(999) == "Code 999"


# ============================================================================
# 3. Application Window Agronomic Rules
# ============================================================================

def test_app_window_no_application_needed():
    res = assess_application_window([], needs_application=False)
    assert res.recommendation == "NO"
    assert res.apply_today == "WAIT"


def test_app_window_heavy_rain_triggers_wait_with_runoff_warning():
    days = [
        {
            "date": "2026-10-20",
            "temp_max_c": 30.0,
            "temp_min_c": 20.0,
            "precipitation_mm": 25.0,
            "precipitation_probability_pct": 80,
            "wind_max_kmh": 10.0,
            "condition": "Moderate rain",
        },
        {
            "date": "2026-10-21",
            "temp_max_c": 30.0,
            "temp_min_c": 20.0,
            "precipitation_mm": 0.0,
            "precipitation_probability_pct": 5,
            "wind_max_kmh": 8.0,
            "condition": "Clear sky",
        },
    ]
    res = assess_application_window(days, needs_application=True, location_name="Pune")
    assert res.apply_today == "WAIT"
    assert "runoff" in res.reason.lower() or "rain" in res.reason.lower()
    assert res.next_window == "2026-10-21"
    assert res.location_name == "Pune"
    assert res.is_available is True


def test_app_window_high_wind_triggers_wait_with_drift_warning():
    days = [
        {
            "date": "2026-10-20",
            "temp_max_c": 28.0,
            "temp_min_c": 18.0,
            "precipitation_mm": 0.0,
            "precipitation_probability_pct": 0,
            "wind_max_kmh": 36.0,
            "condition": "Clear sky",
        }
    ]
    res = assess_application_window(days, needs_application=True)
    assert res.apply_today == "WAIT"
    assert "wind" in res.reason.lower()


def test_app_window_extreme_heat_triggers_wait_with_heat_warning():
    days = [
        {
            "date": "2026-10-20",
            "temp_max_c": 42.0,
            "temp_min_c": 28.0,
            "precipitation_mm": 0.0,
            "precipitation_probability_pct": 0,
            "wind_max_kmh": 12.0,
            "condition": "Clear sky",
        }
    ]
    res = assess_application_window(days, needs_application=True)
    assert res.apply_today == "WAIT"
    assert "heat" in res.reason.lower() or "thermal" in res.reason.lower() or "42" in res.reason


def test_app_window_clear_day_triggers_go():
    days = [
        {
            "date": "2026-10-20",
            "temp_max_c": 31.0,
            "temp_min_c": 20.0,
            "precipitation_mm": 0.0,
            "precipitation_probability_pct": 10,
            "wind_max_kmh": 12.0,
            "condition": "Clear sky",
        }
    ]
    res = assess_application_window(days, needs_application=True)
    assert res.apply_today == "GO"
    assert res.is_available is True
    assert "guarantee" not in res.reason.lower()


def test_app_window_when_weather_unavailable_does_not_fabricate():
    res = assess_application_window([], needs_application=True)
    assert res.apply_today == "WAIT"
    assert res.is_available is False
    assert "cannot confirm" in res.reason.lower() or "unavailable" in res.reason.lower()


# ============================================================================
# 4. Weather Agent Tests
# ============================================================================

@pytest.mark.asyncio
async def test_weather_agent_with_valid_location():
    mock_geo = {
        "name": "Pune",
        "latitude": 18.5204,
        "longitude": 73.8567,
        "country": "India",
        "admin1": "Maharashtra",
        "formatted_name": "Pune, Maharashtra, India",
    }
    mock_forecast_data = {
        "days": [
            {
                "date": "2026-10-20",
                "temp_max_c": 30.0,
                "temp_min_c": 20.0,
                "precipitation_mm": 0.0,
                "precipitation_probability_pct": 5,
                "wind_max_kmh": 10.0,
                "condition": "Clear sky",
            }
        ],
        "attribution": "Weather data by Open-Meteo.com (CC BY 4.0)",
        "latitude": 18.5204,
        "longitude": 73.8567,
    }

    with patch("app.services.weather_service.geocode_location_info", new_callable=AsyncMock, return_value=mock_geo), \
         patch("app.services.weather_service.get_forecast", new_callable=AsyncMock, return_value=mock_forecast_data):

        result = await run_weather_agent(location_name="Pune")
        assert result.is_available is True
        assert result.apply_today == "GO"
        assert "Pune" in result.location_name
        assert len(result.forecast_days) == 1
        assert result.attribution is not None


@pytest.mark.asyncio
async def test_weather_agent_with_unknown_location_reports_clear_failure():
    with patch("app.services.weather_service.geocode_location_info", new_callable=AsyncMock, return_value=None):
        result = await run_weather_agent(location_name="TotallyUnknownCity999")
        assert result.is_available is False
        assert result.apply_today == "WAIT"
        assert "could not resolve" in result.reason.lower() or "not found" in result.reason.lower()
        assert len(result.forecast_days) == 0


@pytest.mark.asyncio
async def test_weather_agent_with_provider_failure_does_not_fabricate():
    mock_geo = {
        "name": "Nagpur",
        "latitude": 21.1458,
        "longitude": 79.0882,
        "country": "India",
        "formatted_name": "Nagpur, Maharashtra, India",
    }

    with patch("app.services.weather_service.geocode_location_info", new_callable=AsyncMock, return_value=mock_geo), \
         patch("app.services.weather_service.get_forecast", new_callable=AsyncMock, side_effect=WeatherTimeoutError("Open-Meteo timeout")):

        result = await run_weather_agent(location_name="Nagpur")
        assert result.is_available is False
        assert result.apply_today == "WAIT"
        assert "unavailable" in result.reason.lower() or "timeout" in result.reason.lower() or "timed out" in result.reason.lower()
        assert len(result.forecast_days) == 0


# ============================================================================
# 5. Multi-Agent Orchestrator Tests
# ============================================================================

def make_sample_soil_report():
    return SoilReport(
        nitrogen=SoilValue(value=180, unit="kg/ha"),
        phosphorus=SoilValue(value=14, unit="kg/ha"),
        potassium=SoilValue(value=160, unit="kg/ha"),
        ph=SoilValue(value=6.8, unit="pH"),
    )


@pytest.mark.asyncio
async def test_orchestrator_full_success():
    soil_report = make_sample_soil_report()

    mock_geo = {"name": "Nagpur", "latitude": 21.1458, "longitude": 79.0882, "formatted_name": "Nagpur, Maharashtra, India"}
    mock_forecast_data = {
        "days": [
            {
                "date": "2026-10-20",
                "temp_max_c": 32.0,
                "temp_min_c": 22.0,
                "precipitation_mm": 0.0,
                "precipitation_probability_pct": 5,
                "wind_max_kmh": 12.0,
                "condition": "Clear sky",
            }
        ],
        "attribution": "Weather data by Open-Meteo.com (CC BY 4.0)",
        "latitude": 21.1458,
        "longitude": 79.0882,
    }

    with patch("app.services.weather_service.geocode_location_info", new_callable=AsyncMock, return_value=mock_geo), \
         patch("app.services.weather_service.get_forecast", new_callable=AsyncMock, return_value=mock_forecast_data), \
         patch("app.services.llm_service.generate_explanation", new_callable=AsyncMock, return_value="Plain terms explanation"):

        resp = await orchestrate(soil=soil_report, location_name="Nagpur")

        assert resp.application_window.is_available is True
        assert resp.application_window.apply_today == "GO"
        assert len(resp.partial_failures) == 0
        assert len(resp.crop_scores) > 0
        assert len(resp.fertilizer_options) > 0


@pytest.mark.asyncio
async def test_orchestrator_handles_weather_partial_failure():
    """
    When the Weather service fails, soil/crop recommendation must still succeed,
    the failure should be cleanly reported in `partial_failures`, and confidence
    adjusted without crashing or returning fake weather.
    """
    soil_report = make_sample_soil_report()

    with patch("app.services.weather_service.geocode_location_info", new_callable=AsyncMock, side_effect=WeatherConnectionError("Network down")), \
         patch("app.services.llm_service.generate_explanation", new_callable=AsyncMock, return_value="Plain terms explanation"):
        resp = await orchestrate(soil=soil_report, location_name="Nashik")

        # Soil and crop analysis still completed!
        assert len(resp.crop_scores) > 0
        assert len(resp.fertilizer_options) > 0

        # Weather window safely indicated unavailable
        assert resp.application_window.is_available is False
        assert resp.application_window.apply_today == "WAIT"

        # Partial failure is clearly reported
        assert len(resp.partial_failures) == 1
        assert "weather" in resp.partial_failures[0].lower()


# ============================================================================
# 6. API Route Tests: /api/weather/forecast & /api/recommendations
# ============================================================================

def test_api_weather_missing_location_returns_400():
    resp = client.get("/api/weather/forecast")
    assert resp.status_code == 400
    assert "lat/lon or a location_name" in resp.json()["detail"]


def test_api_weather_invalid_lat_lon_returns_400():
    resp = client.get("/api/weather/forecast?latitude=95.0&longitude=50.0")
    assert resp.status_code == 400
    assert "out of bounds" in resp.json()["detail"].lower()


def test_api_weather_unknown_location_returns_404():
    with patch("app.services.weather_service.geocode_location_info", new_callable=AsyncMock, return_value=None):
        resp = client.get("/api/weather/forecast?location_name=NonExistentTown999")
        assert resp.status_code == 404
        assert "could not resolve" in resp.json()["detail"].lower()


def test_api_weather_success_with_geocoded_location():
    mock_geo = {
        "name": "Pune",
        "latitude": 18.5204,
        "longitude": 73.8567,
        "country": "India",
        "admin1": "Maharashtra",
        "formatted_name": "Pune, Maharashtra, India",
    }
    mock_forecast_data = {
        "days": [
            {
                "date": "2026-10-20",
                "temp_max_c": 31.0,
                "temp_min_c": 20.0,
                "precipitation_mm": 0.0,
                "precipitation_probability_pct": 5,
                "wind_max_kmh": 10.0,
                "condition": "Clear sky",
            }
        ],
        "attribution": "Weather data by Open-Meteo.com (CC BY 4.0)",
        "latitude": 18.5204,
        "longitude": 73.8567,
    }

    with patch("app.services.weather_service.geocode_location_info", new_callable=AsyncMock, return_value=mock_geo), \
         patch("app.services.weather_service.get_forecast", new_callable=AsyncMock, return_value=mock_forecast_data):

        resp = client.get("/api/weather/forecast?location_name=Pune")
        assert resp.status_code == 200
        data = resp.json()
        assert "days" in data
        assert len(data["days"]) == 1
        assert "Pune" in data["location_name"]


def test_api_analysis_endpoint_orchestrates_weather_and_soil():
    payload = {
        "soil": {
            "nitrogen": {"value": 180, "unit": "kg/ha"},
            "phosphorus": {"value": 14, "unit": "kg/ha"},
            "potassium": {"value": 160, "unit": "kg/ha"},
            "ph": {"value": 6.8, "unit": "pH"},
            "organic_carbon": {"value": 0.5, "unit": "%"},
        },
        "location_name": "Nagpur",
    }

    mock_geo = {"name": "Nagpur", "latitude": 21.1458, "longitude": 79.0882, "formatted_name": "Nagpur, Maharashtra, India"}
    mock_forecast_data = {
        "days": [
            {
                "date": "2026-10-20",
                "temp_max_c": 32.0,
                "temp_min_c": 22.0,
                "precipitation_mm": 0.0,
                "precipitation_probability_pct": 5,
                "wind_max_kmh": 10.0,
                "condition": "Clear sky",
            }
        ],
        "attribution": "Weather data by Open-Meteo.com (CC BY 4.0)",
        "latitude": 21.1458,
        "longitude": 79.0882,
    }

    with patch("app.services.weather_service.geocode_location_info", new_callable=AsyncMock, return_value=mock_geo), \
         patch("app.services.weather_service.get_forecast", new_callable=AsyncMock, return_value=mock_forecast_data), \
         patch("app.services.llm_service.generate_explanation", new_callable=AsyncMock, return_value="Plain terms explanation"):

        resp = client.post("/api/analysis", json=payload)
        assert resp.status_code == 200
        data = resp.json()

        assert "soil" in data
        assert "crop_scores" in data
        assert "fertilizer_options" in data
        assert "application_window" in data
        assert data["application_window"]["apply_today"] == "GO"
        assert "Nagpur" in data["application_window"]["location_name"]
        assert len(data["partial_failures"]) == 0
