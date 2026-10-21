"""Tests for soil parsing API endpoints and PDF extraction service."""
from __future__ import annotations

import io
import os
import fitz
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

SAMPLE_PDF_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "sample_data", "Soil_Test_Report_Demo_Farm.pdf"
)


def _create_synthetic_text_pdf(text: str) -> bytes:
    """Helper to generate an in-memory PDF with specified text."""
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text(fitz.Point(50, 72), text, fontsize=11)
    b = doc.tobytes()
    doc.close()
    return b


def _create_synthetic_image_pdf() -> bytes:
    """Helper to generate an image-only PDF with zero text characters."""
    doc = fitz.open()
    page = doc.new_page(width=300, height=300)
    pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 100, 100), 1)
    pix.clear_with(255)
    page.insert_image(fitz.Rect(50, 50, 150, 150), pixmap=pix)
    b = doc.tobytes()
    doc.close()
    return b


def test_parse_valid_soil_report_pdf():
    """Verify that uploading the benchmark PDF returns structured measurements and 200 OK."""
    assert os.path.exists(SAMPLE_PDF_PATH), f"Missing {SAMPLE_PDF_PATH}"
    with open(SAMPLE_PDF_PATH, "rb") as f:
        file_bytes = f.read()

    response = client.post(
        "/api/soil/parse",
        files={"file": ("Soil_Test_Report_Demo_Farm.pdf", file_bytes, "application/pdf")},
    )
    assert response.status_code == 200
    data = response.json()

    assert data["file_name"] == "Soil_Test_Report_Demo_Farm.pdf"
    assert data["page_count"] == 1
    assert data["is_scanned_image"] is False
    assert data["core_completeness"] == 1.0

    # Verify extracted parameters
    measurements = data["measurements"]
    assert measurements["nitrogen"]["value"] == 180.0
    assert measurements["nitrogen"]["unit"] == "kg/ha"
    assert measurements["nitrogen"]["rating"] == "LOW"
    assert "180" in measurements["nitrogen"]["source_text"]

    assert measurements["phosphorus"]["value"] == 15.0
    assert measurements["phosphorus"]["rating"] == "MEDIUM"

    assert measurements["potassium"]["value"] == 260.0
    assert measurements["potassium"]["rating"] == "MEDIUM"

    assert measurements["ph"]["value"] == 6.4
    assert measurements["ph"]["rating"] == "ACIDIC"

    assert measurements["organic_carbon"]["value"] == 0.45
    assert measurements["organic_carbon"]["rating"] == "LOW"

    assert measurements["electrical_conductivity"]["value"] == 0.32
    assert measurements["electrical_conductivity"]["rating"] == "NORMAL"

    assert measurements["zinc"]["value"] == 0.42
    assert measurements["zinc"]["rating"] == "DEFICIENT"

    assert measurements["iron"]["value"] == 4.8
    assert measurements["iron"]["rating"] == "SUFFICIENT"

    assert measurements["sulphur"]["value"] == 18.0
    assert measurements["sulphur"]["rating"] == "SUFFICIENT"


def test_upload_alias_compatibility():
    """Verify that /api/soil/upload returns compatible SoilParseResponse."""
    with open(SAMPLE_PDF_PATH, "rb") as f:
        file_bytes = f.read()

    response = client.post(
        "/api/soil/upload",
        files={"file": ("Soil_Test_Report_Demo_Farm.pdf", file_bytes, "application/pdf")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["nitrogen"]["value"] == 180.0
    assert data["core_completeness"] == 1.0


def test_reject_non_pdf_file():
    """Uploading a non-PDF file must return 400 Bad Request."""
    response = client.post(
        "/api/soil/parse",
        files={"file": ("test_data.csv", b"N,P,K\n180,15,260", "text/csv")},
    )
    assert response.status_code == 400
    assert "Only PDF documents (.pdf) are supported" in response.json()["detail"]


def test_reject_empty_file():
    """Uploading an empty file (0 bytes) must return 400 Bad Request."""
    response = client.post(
        "/api/soil/parse",
        files={"file": ("empty.pdf", b"", "application/pdf")},
    )
    assert response.status_code == 400
    assert "empty (0 bytes)" in response.json()["detail"]


def test_reject_corrupted_pdf():
    """Uploading corrupted non-PDF bytes with a .pdf extension must return 422."""
    corrupt_bytes = b"This is not a real PDF document at all. Just random text."
    response = client.post(
        "/api/soil/parse",
        files={"file": ("corrupt.pdf", corrupt_bytes, "application/pdf")},
    )
    assert response.status_code == 422
    assert "valid PDF" in response.json()["detail"]


def test_scanned_image_pdf_detection():
    """Uploading an image-only PDF with zero text must return 422 and OCR advice."""
    image_pdf = _create_synthetic_image_pdf()
    response = client.post(
        "/api/soil/parse",
        files={"file": ("scanned_field_photo.pdf", image_pdf, "application/pdf")},
    )
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert "scanned image" in detail.lower() or "ocr" in detail.lower()


def test_partial_pdf_extraction_flags_missing_fields():
    """Uploading a PDF missing some core values flags them as missing and notes in warnings."""
    partial_text = "Soil Health Card\nAvailable Nitrogen (N): 210 kg/ha\npH: 7.2\n"
    pdf_bytes = _create_synthetic_text_pdf(partial_text)

    response = client.post(
        "/api/soil/parse",
        files={"file": ("partial_soil_report.pdf", pdf_bytes, "application/pdf")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["measurements"]["nitrogen"]["value"] == 210.0
    assert data["measurements"]["nitrogen"]["status"] == "extracted"
    assert data["measurements"]["phosphorus"]["status"] == "missing"
    assert data["core_completeness"] < 1.0
    assert "phosphorus" in data["needs_review"]


def test_implausible_value_flags_needs_review():
    """A value outside typical agricultural range must be flagged with status needs_review."""
    weird_text = "Soil Health Card\npH: 14.5\nAvailable Nitrogen (N): 4500 kg/ha\n"
    pdf_bytes = _create_synthetic_text_pdf(weird_text)

    response = client.post(
        "/api/soil/parse",
        files={"file": ("extreme_soil_report.pdf", pdf_bytes, "application/pdf")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["measurements"]["ph"]["status"] == "needs_review"
    assert "ph" in data["needs_review"]
    assert data["measurements"]["ph"]["warning"] is not None
