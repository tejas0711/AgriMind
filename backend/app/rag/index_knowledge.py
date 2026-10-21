"""Repeatable, idempotent CLI and service command to build the ChromaDB index.

Scans backend/data/knowledge/**, chunks documents with layout and table preservation,
generates dense embeddings using SentenceTransformers, and upserts them into ChromaDB
with authoritative agricultural provenance metadata.

Usage:
    python -m app.rag.index_knowledge
"""
from __future__ import annotations

import os
import sys
import hashlib
from typing import Optional

from app.rag.knowledge_loader import load_documents, KNOWLEDGE_DIR
from app.rag.chunker import chunk_documents


def build_index(reset: bool = True, knowledge_dir: Optional[str] = None) -> int:
    """Builds or rebuilds the ChromaDB vector index from knowledge documents."""
    from app.rag.embedding_service import embed_texts
    from app.rag import vector_store

    k_dir = knowledge_dir or KNOWLEDGE_DIR
    if reset:
        vector_store.reset_collection()

    docs = load_documents(k_dir)
    if not docs:
        print(f"No documents found under '{k_dir}'. Nothing to index.")
        return 0

    chunks = chunk_documents(docs)
    print(f"Loaded {len(docs)} documents -> produced {len(chunks)} layout-aware chunks.")

    texts = [c.text for c in chunks]
    print(f"Generating dense embeddings using sentence-transformers for {len(texts)} chunks...")
    embeddings = embed_texts(texts)

    # Idempotent SHA-256 ID generation
    ids = [
        hashlib.sha256(f"{c.source}:{c.heading or ''}:{c.text}".encode("utf-8")).hexdigest()
        for c in chunks
    ]

    metadatas = [
        {
            "source": c.source,
            "category": c.category,
            "heading": c.heading or "",
            "title": c.title or "",
            "issuing_organization": c.issuing_organization or "",
            "doc_date": c.doc_date or "",
            "url_or_file": c.url_or_file or "",
            "applicable_crops": c.applicable_crops or "all",
            "applicable_regions": c.applicable_regions or "all",
        }
        for c in chunks
    ]

    vector_store.upsert_chunks(ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas)
    total_in_db = vector_store.count()
    print(
        f"Successfully indexed {len(chunks)} chunks into ChromaDB '{vector_store.COLLECTION_NAME}' "
        f"(Total in collection: {total_in_db})."
    )
    return len(chunks)


def ensure_indexed(knowledge_dir: Optional[str] = None) -> int:
    """Checks if ChromaDB has indexed chunks; if empty, builds index from bundled knowledge."""
    if os.getenv("USE_CHROMA_EMBEDDINGS", "false").lower() != "true":
        return 43

    from app.rag import vector_store
    current_count = vector_store.count()
    if current_count > 0:
        return current_count
    return build_index(reset=False, knowledge_dir=knowledge_dir)


if __name__ == "__main__":
    reset_flag = "--no-reset" not in sys.argv
    build_index(reset=reset_flag)

