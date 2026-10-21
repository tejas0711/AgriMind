"""Persistent ChromaDB collection for the AgriMind knowledge base."""
from __future__ import annotations

import os
from functools import lru_cache

CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", os.path.join(os.path.dirname(__file__), "..", "..", "vector_db"))
COLLECTION_NAME = "agrimind_knowledge"


@lru_cache(maxsize=1)
def _get_client():
    import chromadb
    from chromadb.config import Settings

    os.makedirs(CHROMA_PERSIST_DIR, exist_ok=True)
    return chromadb.PersistentClient(
        path=CHROMA_PERSIST_DIR,
        settings=Settings(anonymized_telemetry=False),
    )


def get_collection():
    client = _get_client()
    return client.get_or_create_collection(name=COLLECTION_NAME, metadata={"hnsw:space": "cosine"})


def reset_collection():
    client = _get_client()
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    return get_collection()


def upsert_chunks(ids: list[str], embeddings: list[list[float]], documents: list[str], metadatas: list[dict]):
    collection = get_collection()
    collection.upsert(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)


def query(embedding: list[float], top_k: int = 5, where: dict | None = None):
    collection = get_collection()
    return collection.query(query_embeddings=[embedding], n_results=top_k, where=where)


def count() -> int:
    return get_collection().count()
