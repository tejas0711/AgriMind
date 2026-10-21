from __future__ import annotations

import json
import os
from functools import lru_cache

from app.models.crop import CropRequirement

CROP_DATA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "knowledge", "crops", "crop_requirements.json"
)


@lru_cache(maxsize=1)
def load_crop_requirements() -> list[CropRequirement]:
    with open(os.path.abspath(CROP_DATA_PATH), "r", encoding="utf-8") as f:
        raw = json.load(f)
    return [CropRequirement(**item) for item in raw]


def get_crop(name: str) -> CropRequirement | None:
    name_lower = name.strip().lower()
    for crop in load_crop_requirements():
        if crop.name.lower() == name_lower:
            return crop
    return None
