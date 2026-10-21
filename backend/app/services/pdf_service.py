"""Extracts raw text and structural metadata from uploaded PDFs using PyMuPDF (fitz).

Supports in-memory stream processing to avoid lingering disk storage.
Detects image-only/scanned PDFs that lack a digital text layer.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List
import fitz  # PyMuPDF


class PdfProcessingError(Exception):
    """Base exception for PDF processing failures."""
    pass


class InvalidPdfError(PdfProcessingError):
    """Raised when the uploaded file is not a valid, readable PDF."""
    pass


class ScannedPdfError(PdfProcessingError):
    """Raised when the PDF has no digital text layer and contains images."""
    pass


@dataclass
class PdfExtractResult:
    """Container for extracted PDF content and structural metadata."""
    text: str
    pages: List[str]
    page_count: int
    total_characters: int
    image_count: int
    is_scanned_image: bool
    ocr_notice: str | None = None


def extract_pdf_from_bytes(file_bytes: bytes, filename: str = "document.pdf") -> PdfExtractResult:
    """Extracts text, pages, and layout metadata from raw PDF bytes.

    Performs stream inspection directly in memory without writing to disk.
    Identifies empty or scanned documents.
    """
    if not file_bytes:
        raise InvalidPdfError("The uploaded file is empty (0 bytes). Please upload a valid PDF document.")

    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
    except Exception as exc:
        raise InvalidPdfError(f"Could not open file as a valid PDF: {exc}") from exc

    try:
        page_count = len(doc)
        if page_count == 0:
            raise InvalidPdfError("The PDF document contains no pages.")

        pages: list[str] = []
        image_count = 0

        for page in doc:
            page_text = page.get_text("text") or ""
            pages.append(page_text)
            try:
                images = page.get_images()
                image_count += len(images)
            except Exception:
                pass

        full_text = "\n".join(pages)
        total_chars = len(full_text.strip())

        # Detection for scanned / image-only PDFs
        # If total non-whitespace text is negligible (< 25 characters) but pages exist
        is_scanned_image = False
        ocr_notice = None

        if total_chars < 25:
            is_scanned_image = True
            ocr_notice = (
                "No extractable digital text was found in this PDF (it appears to be a scanned image or photograph). "
                "OCR (Optical Character Recognition) is not supported in the current phase. "
                "Please upload a digital text-based Soil Health Card or lab report PDF."
            )

        return PdfExtractResult(
            text=full_text,
            pages=pages,
            page_count=page_count,
            total_characters=total_chars,
            image_count=image_count,
            is_scanned_image=is_scanned_image,
            ocr_notice=ocr_notice,
        )
    finally:
        doc.close()


def extract_text(pdf_path: str) -> str:
    """Extract plain text from every page of a PDF file, concatenated.
    Maintained for backward compatibility with existing tests and scripts.
    """
    doc = fitz.open(pdf_path)
    try:
        pages = [page.get_text("text") for page in doc]
    finally:
        doc.close()
    return "\n".join(pages)


def extract_pages(pdf_path: str) -> list[str]:
    """Return a list of per-page text blocks.
    Maintained for backward compatibility with RAG chunking and source citations.
    """
    doc = fitz.open(pdf_path)
    try:
        return [page.get_text("text") for page in doc]
    finally:
        doc.close()
