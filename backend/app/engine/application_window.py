"""Decides WHEN a recommended fertilizer/amendment application should
happen, given a forecast. Pure deterministic rules, no LLM.

Agronomic Rules (deliberately conservative defaults tuned against ICAR and extension practices):
  - Heavy rain expected (>=20mm or >=70% probability or >=8mm) -> WAIT (nutrient runoff & leaching risk)
  - High wind (>=30 km/h) -> WAIT (spray drift & accelerated surface drying/volatilization)
  - Extreme temperature (>=40°C) -> WAIT (ammonia volatilization & crop burn hazard)
  - Otherwise -> GO today if within safe limits, or identify the next clear window within the forecast horizon.
"""
from __future__ import annotations

from typing import List, Optional, Dict, Any
from app.models.recommendation import ApplicationWindow

RAIN_MM_THRESHOLD = 20.0
RAIN_PROB_THRESHOLD = 70.0
WIND_KMH_THRESHOLD = 30.0
EXTREME_HEAT_THRESHOLD = 40.0


def assess_application_window(
    forecast_days: Optional[List[Dict[str, Any]]],
    needs_application: bool,
    location_name: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    fetched_at: Optional[str] = None,
) -> ApplicationWindow:
    """Evaluates meteorological suitability for applying recommended fertilizers or amendments."""
    if not needs_application:
        return ApplicationWindow(
            recommendation="NO",
            apply_today="WAIT",
            reason="No active fertilizer/amendment application was recommended for the current soil status.",
            location_name=location_name,
            latitude=latitude,
            longitude=longitude,
            fetched_at=fetched_at,
            is_available=True,
        )

    if not forecast_days:
        return ApplicationWindow(
            recommendation="YES",
            apply_today="WAIT",
            reason="Weather forecast unavailable; cannot confirm a safe application window.",
            location_name=location_name,
            latitude=latitude,
            longitude=longitude,
            fetched_at=fetched_at,
            is_available=False,
            limitations="Weather-based timing advice could not be evaluated because forecast data is unavailable.",
        )

    today = forecast_days[0]
    rain = today.get("precipitation_mm") or 0.0
    rain_prob = today.get("precipitation_probability_pct") or 0
    wind = today.get("wind_max_kmh") or 0.0
    temp_max = today.get("temp_max_c")

    # 1. Check Rain & Runoff Hazards
    if rain >= RAIN_MM_THRESHOLD or rain_prob >= RAIN_PROB_THRESHOLD or (rain >= 8.0 and rain_prob >= 50):
        next_window = _find_next_clear_day(forecast_days[1:])
        if rain >= RAIN_MM_THRESHOLD:
            reason = f"Heavy rain expected today ({rain}mm) - risk of severe nutrient runoff and leaching."
        elif rain >= 8.0:
            reason = f"Significant rain expected today ({rain}mm, {rain_prob}% probability) - risk of nutrient runoff."
        else:
            reason = f"High chance of rain today ({rain_prob}% probability, {rain}mm expected) - risk of nutrient runoff."

        return ApplicationWindow(
            recommendation="YES",
            apply_today="WAIT",
            reason=reason,
            next_window=next_window,
            forecast_summary=today,
            forecast_days=forecast_days,
            location_name=location_name,
            latitude=latitude,
            longitude=longitude,
            fetched_at=fetched_at,
            current_temperature_c=today.get("current_temperature_c"),
            current_condition=today.get("current_condition") or today.get("condition"),
            is_available=True,
        )

    # 2. Check Wind Hazards (Spray drift / volatilization)
    if wind >= WIND_KMH_THRESHOLD:
        next_window = _find_next_clear_day(forecast_days[1:])
        return ApplicationWindow(
            recommendation="YES",
            apply_today="WAIT",
            reason=f"High wind expected today ({wind} km/h) - unsuitable for spray/foliar application or surface topdressing due to drift and volatilization.",
            next_window=next_window,
            forecast_summary=today,
            forecast_days=forecast_days,
            location_name=location_name,
            latitude=latitude,
            longitude=longitude,
            fetched_at=fetched_at,
            current_temperature_c=today.get("current_temperature_c"),
            current_condition=today.get("current_condition") or today.get("condition"),
            is_available=True,
        )

    # 3. Check Extreme Heat Hazard
    if temp_max is not None and temp_max >= EXTREME_HEAT_THRESHOLD:
        next_window = _find_next_clear_day(forecast_days[1:])
        return ApplicationWindow(
            recommendation="YES",
            apply_today="WAIT",
            reason=f"Extreme heat forecast today ({temp_max}°C) - high risk of rapid ammonia volatilization and foliar scorch. Postpone to cooler hours or upcoming clear window.",
            next_window=next_window,
            forecast_summary=today,
            forecast_days=forecast_days,
            location_name=location_name,
            latitude=latitude,
            longitude=longitude,
            fetched_at=fetched_at,
            current_temperature_c=today.get("current_temperature_c"),
            current_condition=today.get("current_condition") or today.get("condition"),
            is_available=True,
        )

    # 4. Favorable Window
    return ApplicationWindow(
        recommendation="YES",
        apply_today="GO",
        reason="Forecast conditions today are within safe limits for application.",
        forecast_summary=today,
        forecast_days=forecast_days,
        location_name=location_name,
        latitude=latitude,
        longitude=longitude,
        fetched_at=fetched_at,
        current_temperature_c=today.get("current_temperature_c"),
        current_condition=today.get("current_condition") or today.get("condition"),
        is_available=True,
    )


def _find_next_clear_day(remaining_days: List[Dict[str, Any]]) -> Optional[str]:
    """Scans subsequent days to identify the earliest window meeting all safety criteria."""
    for day in remaining_days:
        rain = day.get("precipitation_mm") or 0.0
        rain_prob = day.get("precipitation_probability_pct") or 0
        wind = day.get("wind_max_kmh") or 0.0
        temp_max = day.get("temp_max_c")

        if (
            rain < RAIN_MM_THRESHOLD
            and rain_prob < RAIN_PROB_THRESHOLD
            and rain < 8.0
            and wind < WIND_KMH_THRESHOLD
            and (temp_max is None or temp_max < EXTREME_HEAT_THRESHOLD)
        ):
            return day.get("date")
    return None
