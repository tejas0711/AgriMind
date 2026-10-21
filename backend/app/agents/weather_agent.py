"""Agent 2 - Weather & Application Timing Agent.

Given a location and whether an active fertilizer or amendment application was
recommended, coordinates with the live Open-Meteo weather service and evaluates
safe application windows.

Adheres strictly to the requirement that weather data is never fabricated:
if the provider is down, times out, or the location cannot be resolved,
a clear partial-failure status is returned without fake meteorological numbers.
"""
from __future__ import annotations

from typing import Optional
from app.models.recommendation import ApplicationWindow
from app.services import weather_service
from app.engine.application_window import assess_application_window


async def run_weather_agent(
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    location_name: Optional[str] = None,
    needs_application: bool = True,
) -> Optional[ApplicationWindow]:
    """Obtains and interprets current forecast data relevant to the farm location."""
    resolved_location_name = location_name

    # 1. Geocode location if coordinates are missing but location_name is provided
    if (latitude is None or longitude is None) and location_name:
        try:
            geo_info = await weather_service.geocode_location_info(location_name)
            if geo_info:
                latitude = geo_info["latitude"]
                longitude = geo_info["longitude"]
                resolved_location_name = geo_info.get("formatted_name", location_name)
            else:
                return ApplicationWindow(
                    recommendation="YES" if needs_application else "NO",
                    apply_today="WAIT",
                    reason=f"Could not resolve location '{location_name}'. Weather-based timing advice could not be evaluated.",
                    location_name=location_name,
                    is_available=False,
                    error=f"Location '{location_name}' was not found by geocoding service.",
                    limitations="Without verified farm coordinates, weather runoff risks cannot be determined.",
                )
        except weather_service.WeatherServiceError as exc:
            return ApplicationWindow(
                recommendation="YES" if needs_application else "NO",
                apply_today="WAIT",
                reason=f"Geocoding service unavailable ({exc}). Weather-based timing advice could not be evaluated.",
                location_name=location_name,
                is_available=False,
                error=str(exc),
                limitations="Geocoding service is temporarily unreachable; application timing could not be verified.",
            )

    # 2. Handle missing coordinates
    if latitude is None or longitude is None:
        if not needs_application:
            return None
        return ApplicationWindow(
            recommendation="YES",
            apply_today="WAIT",
            reason="No farm location provided, so the live weather forecast could not be checked.",
            is_available=False,
            limitations="Please provide a farm location name or GPS coordinates to verify application weather windows.",
        )

    # 3. Fetch live forecast from weather provider
    try:
        forecast = await weather_service.get_forecast(latitude, longitude)
    except weather_service.WeatherServiceError as exc:
        return ApplicationWindow(
            recommendation="YES" if needs_application else "NO",
            apply_today="WAIT",
            reason=f"Live weather forecast unavailable ({exc}). Weather-based timing advice could not be verified.",
            location_name=resolved_location_name,
            latitude=latitude,
            longitude=longitude,
            is_available=False,
            error=str(exc),
            limitations="Weather provider is temporarily unreachable. Do not assume ideal application conditions without local verification.",
        )

    # 4. Assess meteorological application window with deterministic rules
    return assess_application_window(
        forecast_days=forecast.get("days", []),
        needs_application=needs_application,
        location_name=resolved_location_name,
        latitude=latitude,
        longitude=longitude,
        fetched_at=forecast.get("generated_at"),
    )
