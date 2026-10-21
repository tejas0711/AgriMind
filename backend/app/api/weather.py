from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from app.services import weather_service
from app.engine.application_window import assess_application_window

router = APIRouter(prefix="/api/weather", tags=["weather"])


@router.get("/forecast")
async def forecast(
    latitude: Optional[float] = Query(None, description="Farm latitude (-90 to 90)"),
    longitude: Optional[float] = Query(None, description="Farm longitude (-180 to 180)"),
    location_name: Optional[str] = Query(None, description="Farm city/district name, e.g. 'Nashik, Maharashtra'"),
    days: int = Query(5, ge=1, le=14, description="Number of forecast days (1-14)"),
):
    """Fetches real Open-Meteo forecast data and geocodes free-text locations."""
    resolved_name = location_name

    if (latitude is None or longitude is None) and location_name:
        try:
            geo_info = await weather_service.geocode_location_info(location_name)
        except weather_service.WeatherTimeoutError as exc:
            raise HTTPException(status_code=504, detail=str(exc)) from exc
        except weather_service.WeatherConnectionError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except weather_service.WeatherServiceError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

        if not geo_info:
            raise HTTPException(status_code=404, detail=f"Could not resolve location '{location_name}'.")
        latitude, longitude = geo_info["latitude"], geo_info["longitude"]
        resolved_name = geo_info.get("formatted_name", location_name)

    if latitude is None or longitude is None:
        raise HTTPException(
            status_code=400,
            detail="Provide either lat/lon or a location_name.",
        )

    if not (-90.0 <= latitude <= 90.0) or not (-180.0 <= longitude <= 180.0):
        raise HTTPException(
            status_code=400,
            detail=f"Coordinates out of bounds: lat={latitude}, lon={longitude}",
        )

    try:
        data = await weather_service.get_forecast(latitude, longitude, days=days)
        if resolved_name:
            data["location_name"] = resolved_name
        
        # Build deterministic application window so frontend gets full application_window object
        app_win = assess_application_window(
            forecast_days=data.get("days", []),
            needs_application=True,
            location_name=resolved_name,
            latitude=latitude,
            longitude=longitude,
            fetched_at=data.get("generated_at"),
        )
        if "current_temperature_c" in data:
            app_win.current_temperature_c = data["current_temperature_c"]
        if "current_condition" in data:
            app_win.current_condition = data["current_condition"]
        
        data["application_window"] = app_win.model_dump()
        return data
    except weather_service.WeatherTimeoutError as exc:
        raise HTTPException(status_code=504, detail=str(exc)) from exc
    except weather_service.WeatherConnectionError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except weather_service.WeatherServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

