from __future__ import annotations

import io
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_api_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "AgriMind API"
    assert data["version"] == "0.1.0"
    assert "timestamp" in data


def test_root_health_alias():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "0.1.0"


def test_root_index():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["docs"] == "/docs"
    assert data["health"] == "/api/health"


def test_api_info_capabilities():
    response = client.get("/api/info")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "AgriMind API"
    assert "en" in data["supported_languages"]
    assert "hi" in data["supported_languages"]
    assert "mr" in data["supported_languages"]
    assert len(data["supported_crops"]) > 0
    assert "Tomato" in data["supported_crops"]
    assert data["capabilities"]["deterministic_engine"] is True


def test_validation_error_handling_on_invalid_payload():
    # Sending invalid JSON payload (soil field missing required structure)
    response = client.post("/api/recommendation", json={"soil": "invalid_string_not_dict"})
    assert response.status_code == 422
    data = response.json()
    assert data["status_code"] == 422
    assert data["error_type"] == "ValidationError"
    assert "detail" in data


def test_upload_non_pdf_error_handling():
    # Sending a non-PDF file
    fake_txt = io.BytesIO(b"Hello world soil report")
    response = client.post(
        "/api/soil/upload",
        files={"file": ("soil_report.txt", fake_txt, "text/plain")},
    )
    assert response.status_code == 400
    data = response.json()
    assert "PDF" in data["detail"]


def test_weather_missing_location_error_handling():
    # Missing lat/lon and location_name
    response = client.get("/api/weather/forecast")
    assert response.status_code == 400
    data = response.json()
    assert "lat/lon or a location_name" in data["detail"]
