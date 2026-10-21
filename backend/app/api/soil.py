"""Soil report upload and parsing API endpoints."""
from __future__ import annotations

import logging
from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.core.config import get_settings
from app.models.soil import SoilParseResponse, SoilReport
from app.services.pdf_service import (
    InvalidPdfError,
    extract_pdf_from_bytes,
)
from app.services.soil_parser import parse_soil_document

logger = logging.getLogger("agrimind.api.soil")
router = APIRouter(prefix="/api/soil", tags=["soil"])


async def _process_pdf_upload(file: UploadFile) -> SoilParseResponse:
    """Validates and extracts structured soil data from an uploaded PDF."""
    settings = get_settings()

    filename = file.filename or "unknown.pdf"
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type for '{filename}'. Only PDF documents (.pdf) are supported.",
        )

    try:
        contents = await file.read()
    except Exception as exc:
        logger.error(f"Failed reading upload stream for {filename}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed reading uploaded file: {exc}",
        ) from exc

    file_size = len(contents)
    if file_size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file is empty (0 bytes). Please upload a valid soil report PDF.",
        )

    if file_size > settings.max_upload_size_bytes:
        max_mb = settings.max_upload_size_bytes / (1024 * 1024)
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File '{filename}' ({file_size / 1024:.1f} KB) exceeds the maximum upload limit of {max_mb:.0f} MB.",
        )

    try:
        extract_result = extract_pdf_from_bytes(contents, filename)
    except InvalidPdfError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.error(f"Unexpected error extracting PDF {filename}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to extract content from PDF: {exc}",
        ) from exc

    # Check for scanned / image-only documents
    if extract_result.is_scanned_image:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=extract_result.ocr_notice or (
                "No extractable digital text found in this PDF (it appears to be a scanned image). "
                "OCR is not available in the current phase. Please upload a digital text-based Soil Health Card."
            ),
        )

    return parse_soil_document(
        text=extract_result.text,
        file_name=filename,
        file_size_bytes=file_size,
        page_count=extract_result.page_count,
        is_scanned_image=False,
        ocr_notice=None,
    )


@router.post(
    "/parse",
    response_model=SoilParseResponse,
    summary="Parse soil report PDF into structured measurements",
    description="Upload a digital soil report PDF to extract core nutrients, micronutrients, units, and source evidence.",
)
async def parse_soil_report(file: UploadFile = File(...)) -> SoilParseResponse:
    """Primary endpoint for PDF parsing with detailed measurements and audit evidence."""
    return await _process_pdf_upload(file)


@router.post(
    "/upload",
    response_model=SoilParseResponse,
    summary="Upload soil report PDF (backward-compatible alias)",
    description="Maintains backward compatibility with earlier frontend integrations while returning rich parsed measurements.",
)
async def upload_soil_report(file: UploadFile = File(...)) -> SoilParseResponse:
    """Backward-compatible upload endpoint returning SoilParseResponse."""
    return await _process_pdf_upload(file)
