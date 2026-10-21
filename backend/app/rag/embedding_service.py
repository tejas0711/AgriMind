"""Wraps the embedding model so it's loaded once and easily swappable."""
from __future__ import annotations

import os
from functools import lru_cache

# Prevent huggingface_hub from attempting slow network calls to check model updates on every run
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def _get_model():
    from sentence_transformers import SentenceTransformer

    try:
        return SentenceTransformer(_MODEL_NAME, local_files_only=True)
    except Exception:
        return SentenceTransformer(_MODEL_NAME)


def embed_texts(texts: list[str]) -> list[list[float]]:
    model = _get_model()
    embeddings = model.encode(texts, show_progress_bar=False, normalize_embeddings=True)
    return embeddings.tolist()


@lru_cache(maxsize=256)
def _cached_embed_single(text: str) -> tuple[float, ...]:
    return tuple(embed_texts([text])[0])


def embed_query(text: str) -> list[float]:
    return list(_cached_embed_single(text.strip()))

