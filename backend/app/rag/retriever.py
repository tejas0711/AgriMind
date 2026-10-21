"""Semantic retrieval service for the AgriMind knowledge base.

Searches the persistent ChromaDB collection using dense SentenceTransformers
embeddings and returns structured Evidence objects with full metadata provenance
(title, issuing organization, document date, file reference, heading, and relevance score).
"""
from __future__ import annotations

from typing import List, Optional, Set
from app.rag import vector_store
from app.rag.embedding_service import embed_query
from app.models.recommendation import Evidence, Deficiency
from app.models.soil import SoilReport


def retrieve(query_text: str, top_k: int = 4, category: Optional[str] = None) -> List[Evidence]:
    """Performs semantic search over the indexed knowledge base.

    Returns Evidence objects with text, source, relevance score, and provenance metadata.
    """
    if not query_text or not query_text.strip():
        return []

    embedding = embed_query(query_text.strip())
    where = {"category": category} if category else None

    try:
        results = vector_store.query(embedding, top_k=top_k, where=where)
    except Exception:
        return []

    evidence: List[Evidence] = []
    docs = results.get("documents", [[]])[0] if results else []
    metas = results.get("metadatas", [[]])[0] if results else []
    dists = results.get("distances", [[]])[0] if results else []

    for doc, meta, dist in zip(docs, metas, dists):
        similarity = max(0.0, 1.0 - dist)  # cosine distance -> similarity score
        meta = meta or {}
        evidence.append(
            Evidence(
                text=doc,
                source=meta.get("source", "knowledge_base"),
                score=round(similarity, 3),
                title=meta.get("title") or meta.get("heading") or "Agricultural Reference Guide",
                issuing_organization=meta.get("issuing_organization") or "Agricultural Extension Reference",
                doc_date=meta.get("doc_date") or None,
                url_or_file=meta.get("url_or_file") or meta.get("source") or None,
                category=meta.get("category") or category,
                heading=meta.get("heading") or None,
            )
        )
    return evidence


def retrieve_for_recommendation(
    soil: Optional[SoilReport] = None,
    selected_crop: Optional[str] = None,
    deficiencies: Optional[List[Deficiency]] = None,
    user_question: Optional[str] = None,
    top_k: int = 4,
) -> List[Evidence]:
    """Constructs targeted agronomical queries from soil analysis and retrieves top evidence."""
    queries: List[str] = []

    # 1. User specific inquiry takes top priority if given
    if user_question and user_question.strip():
        queries.append(user_question.strip())

    # 2. Add queries for primary nutrient deficiencies
    if deficiencies:
        low_nutrients = [d for d in deficiencies if d.status == "LOW"]
        for d in low_nutrients[:2]:
            queries.append(f"{d.nutrient} deficiency management fertilizer application ICAR")

    # 3. Add queries for soil reaction extremes
    if soil:
        ph_val = soil.ph.value if soil.ph and soil.ph.value is not None else None
        if ph_val is not None:
            if ph_val < 5.8:
                queries.append("acidic soil lime application agricultural limestone")
            elif ph_val > 7.8:
                queries.append("alkaline sodic soil gypsum reclamation high pH")

        oc_val = soil.organic_carbon.value if soil.organic_carbon and soil.organic_carbon.value is not None else None
        if oc_val is not None and oc_val < 0.5:
            queries.append("low soil organic carbon farmyard manure FYM green manuring")

    # 4. Add query for crop nutrient requirements
    if selected_crop:
        queries.append(f"{selected_crop} nutrient requirements fertilizer management 4R stewardship")

    if not queries:
        queries.append("soil testing fertility guidelines 4R nutrient stewardship ICAR")

    seen_sources: Set[str] = set()
    combined_evidence: List[Evidence] = []

    for q in queries[:2]:
        items = retrieve(q, top_k=2)
        for item in items:
            key = f"{item.source}::{item.heading or item.text[:40]}"
            if key not in seen_sources:
                seen_sources.add(key)
                combined_evidence.append(item)

    # Sort descending by relevance score and cap at top_k
    combined_evidence.sort(key=lambda x: x.score, reverse=True)
    return combined_evidence[:top_k]
