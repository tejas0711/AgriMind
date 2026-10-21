from __future__ import annotations

import json
import os
from functools import lru_cache

FERTILIZER_DATA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "knowledge", "fertilizer", "fertilizer_options.json"
)


@lru_cache(maxsize=1)
def load_fertilizer_options() -> dict:
    with open(os.path.abspath(FERTILIZER_DATA_PATH), "r", encoding="utf-8") as f:
        return json.load(f)


def get_options_for_nutrient(nutrient: str) -> dict:
    data = load_fertilizer_options()
    return data.get(nutrient, {"chemical": [], "organic": []})
