"""Structured representations of a soil report and parsed measurements."""
from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class ExtractionStatus(str, Enum):
    EXTRACTED = "extracted"
    MISSING = "missing"
    NEEDS_REVIEW = "needs_review"
    USER_EDITED = "user_edited"


class SoilValue(BaseModel):
    """Simple numeric value and unit container."""
    value: float
    unit: Optional[str] = None


class SoilMeasurement(BaseModel):
    """Detailed metadata for a single soil test parameter.

    Retains numeric value, unit, verbatim source text from the PDF,
    extraction status, and validation flags.
    """
    name: str = Field(description="Display name, e.g. 'Available Nitrogen (N)'")
    field_key: str = Field(description="Standardized key, e.g. 'nitrogen'")
    value: Optional[float] = Field(default=None, description="Numeric measurement value")
    unit: Optional[str] = Field(default=None, description="Measurement unit, e.g. 'kg/ha'")
    source_text: Optional[str] = Field(default=None, description="Verbatim text line or snippet from PDF")
    status: str = Field(default="extracted", description="Extraction status: extracted, missing, needs_review, user_edited")
    is_edited: bool = Field(default=False, description="Flag indicating if farmer/user modified this value")
    warning: Optional[str] = Field(default=None, description="Validation warning or plausibility flag")
    rating: Optional[str] = Field(default=None, description="Soil Health Card band: LOW, MEDIUM, HIGH, etc.")
    typical_range: Optional[str] = Field(default=None, description="Reference benchmark range or threshold")


class SoilReport(BaseModel):
    """Structured soil data extracted from a Soil Health Card / lab report.

    All fields are optional because real-world reports are frequently incomplete.
    Missing fields lower completeness downstream rather than being defaulted.
    """

    nitrogen: Optional[SoilValue] = None          # kg/ha
    phosphorus: Optional[SoilValue] = None         # kg/ha
    potassium: Optional[SoilValue] = None          # kg/ha
    ph: Optional[SoilValue] = None
    organic_carbon: Optional[SoilValue] = None     # %
    electrical_conductivity: Optional[SoilValue] = None  # dS/m
    zinc: Optional[SoilValue] = None               # ppm
    iron: Optional[SoilValue] = None               # ppm
    boron: Optional[SoilValue] = None              # ppm
    sulphur: Optional[SoilValue] = None            # ppm
    manganese: Optional[SoilValue] = None          # ppm
    copper: Optional[SoilValue] = None             # ppm

    measurements: Optional[Dict[str, SoilMeasurement]] = None
    raw_text_excerpt: Optional[str] = None
    extraction_warnings: List[str] = Field(default_factory=list)

    def completeness(self) -> float:
        """Fraction of the 6 core fields (N,P,K,pH,OC,EC) that were found."""
        core = [
            self.nitrogen,
            self.phosphorus,
            self.potassium,
            self.ph,
            self.organic_carbon,
            self.electrical_conductivity,
        ]
        found = sum(1 for f in core if f is not None and f.value is not None)
        return round(found / len(core), 2)


class SoilParseResponse(SoilReport):
    """Rich API response returned by the PDF parsing pipeline."""

    file_name: str = Field(description="Name of the uploaded PDF file")
    file_size_bytes: int = Field(description="File size in bytes")
    page_count: int = Field(description="Number of pages in the PDF document")
    is_scanned_image: bool = Field(default=False, description="Whether PDF contains raster images with no digital text")
    ocr_notice: Optional[str] = Field(default=None, description="User advice if document lacks extractable text")
    measurements: Dict[str, SoilMeasurement] = Field(default_factory=dict, description="Detailed dictionary of all parameters")
    core_completeness: float = Field(default=0.0, description="Completeness fraction (0.0 to 1.0) of core parameters")
    warnings: List[str] = Field(default_factory=list, description="General or field-specific extraction warnings")
    needs_review: List[str] = Field(default_factory=list, description="List of field keys needing farmer review")
