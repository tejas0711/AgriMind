from __future__ import annotations

from typing import Optional, List, Dict
from pydantic import BaseModel, Field


class CropRequirement(BaseModel):
    """Reference requirements for a crop, loaded from data/knowledge/crops."""

    name: str
    ph_min: float
    ph_max: float
    n_min: float           # kg/ha, minimum recommended available N
    n_max: float
    p_min: float
    p_max: float
    k_min: float
    k_max: float
    season: list[str]      # e.g. ["kharif", "rabi", "zaid"]
    water_need: str        # "low" | "medium" | "high"
    notes: Optional[str] = None


class CropScore(BaseModel):
    """Evaluated crop suitability score with granular positive and limiting factors."""

    name: str
    score: float            # 0-100
    ph_fit: bool = True
    n_fit: bool = True
    p_fit: bool = True
    k_fit: bool = True
    season_fit: bool = True
    reasons: List[str] = Field(default_factory=list)
    category: str = Field(default="Moderately Suitable", description="Highly Suitable | Moderately Suitable | Marginally Suitable | Unsuitable")
    positive_factors: List[str] = Field(default_factory=list, description="Specific agronomic factors increasing suitability")
    limiting_factors: List[str] = Field(default_factory=list, description="Specific nutrient/pH/season constraints reducing suitability")
    missing_factors: List[str] = Field(default_factory=list, description="Unmeasured soil properties handled neutrally")
    factor_breakdown: Dict[str, float] = Field(default_factory=dict, description="Point contribution per evaluated factor")
