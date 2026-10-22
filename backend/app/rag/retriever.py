"""Semantic retrieval service for the AgriMind knowledge base.

Searches the persistent ChromaDB collection using dense SentenceTransformers
embeddings with an instantaneous in-memory lexical fallback, guaranteeing
sub-second responses without hanging cloud container threads.
"""
from __future__ import annotations

import os
import re
import time
from functools import lru_cache
from typing import List, Optional, Set

from app.models.recommendation import Evidence, Deficiency
from app.models.soil import SoilReport


@lru_cache(maxsize=1)
def _get_knowledge_chunks():
    """Loads and chunks knowledge base markdown files once for instantaneous fallback."""
    try:
        from app.rag.knowledge_loader import load_documents
        from app.rag.chunker import chunk_documents

        return chunk_documents(load_documents())
    except Exception:
        return []


# Common Marathi and Hindi agronomic keywords mapped to English knowledge base terms
MULTILINGUAL_AGRI_MAP = {
    # Crops
    "पीक": ["crop", "crops", "cultivation", "varieties", "yield", "suitability"],
    "पिके": ["crop", "crops", "cultivation", "varieties"],
    "पिका": ["crop", "crops", "cultivation"],
    "फसल": ["crop", "crops", "cultivation", "yield"],
    "फसलें": ["crop", "crops", "cultivation"],
    "कापूस": ["cotton", "black soil", "bollworm"],
    "कपास": ["cotton", "black soil"],
    "ऊस": ["sugarcane", "ratoon", "sugar"],
    "गन्ना": ["sugarcane", "ratoon"],
    "सोयाबीन": ["soybean", "rhizobium", "legume"],
    "गहू": ["wheat", "rust", "rabi"],
    "गेहूं": ["wheat", "rust", "rabi"],
    "हरभरा": ["gram", "chickpea", "pulses"],
    "चना": ["chickpea", "gram", "pulses"],
    "मका": ["maize", "corn"],
    "मक्का": ["maize", "corn"],
    "कांदा": ["onion", "thrips"],
    "प्याज": ["onion", "thrips"],
    "टोमॅटो": ["tomato", "blight"],
    "टमाटर": ["tomato", "blight"],
    "भात": ["rice", "paddy"],
    "धान": ["paddy", "rice"],
    "तूर": ["pigeonpea", "arhar", "pulses"],
    "अरहर": ["pigeonpea", "arhar", "pulses"],
    # Season & Timing
    "आता": ["season", "current", "sowing", "timing", "rabi", "kharif", "crop"],
    "हंगाम": ["season", "kharif", "rabi", "summer"],
    "खरीप": ["kharif", "monsoon", "crop"],
    "रब्बी": ["rabi", "winter", "crop"],
    "लागवड": ["sowing", "planting", "spacing"],
    "पेरणी": ["sowing", "seed", "germination"],
    "कापणी": ["harvest", "yield"],
    # Soil & Nutrients
    "माती": ["soil", "organic carbon", "ph", "texture"],
    "जमीन": ["soil", "land", "drainage"],
    "मृदा": ["soil", "testing"],
    "मिट्टी": ["soil", "organic", "ph"],
    "खत": ["fertilizer", "manure", "npk", "dose"],
    "खते": ["fertilizer", "nutrients"],
    "खाद": ["fertilizer", "manure", "compost"],
    "युरिया": ["urea", "nitrogen", "top dressing"],
    "डीएपी": ["dap", "phosphorus"],
    "फॉस्फरस": ["phosphorus", "root"],
    "पोटॅश": ["potash", "potassium"],
    "सेंद्रिय": ["organic", "compost", "fym"],
    # Water & Weather
    "पाणी": ["water", "irrigation", "drainage"],
    "सिंचन": ["irrigation", "drip"],
    "सिंचाई": ["irrigation", "drip"],
    "हवामान": ["weather", "temperature", "forecast"],
    "मौसम": ["weather", "temperature", "climate"],
    "तापमान": ["temperature", "heat"],
    "पाऊस": ["rainfall", "rain", "precipitation"],
    # Pests & Diseases
    "रोग": ["disease", "fungal", "blight", "wilt"],
    "कीड": ["pest", "insect", "infestation"],
    "किटक": ["pest", "insects"],
}


def _keyword_retrieve(query_text: str, top_k: int = 4, category: Optional[str] = None) -> List[Evidence]:
    """Instantaneous (<2ms) token-overlap retriever over authoritative knowledge chunks with multilingual support."""
    chunks = _get_knowledge_chunks()
    if not chunks or not query_text:
        return []

    q_lower = query_text.lower()
    q_words = [w for w in re.findall(r"\w+", q_lower) if len(w) > 2]

    # Expand Devanagari / multilingual keywords to English domain tokens
    for dev_term, eng_terms in MULTILINGUAL_AGRI_MAP.items():
        if dev_term in query_text:
            q_words.extend(eng_terms)

    if not q_words:
        q_words = ["crop", "soil", "fertilizer", "management"]

    scored = []
    for c in chunks:
        if category and c.category != category:
            continue
        c_text_lower = c.text.lower()
        matches = sum(1 for w in q_words if w in c_text_lower)
        if matches > 0:
            score = round(min(0.95, 0.45 + (matches / len(q_words)) * 0.50), 3)
            scored.append((score, c))

    scored.sort(key=lambda x: x[0], reverse=True)

    # If no specific matches, default to foundational agronomic chunks
    selected_chunks = scored[:top_k]
    if not selected_chunks:
        filtered_chunks = [c for c in chunks if not category or c.category == category]
        selected_chunks = [(0.50, c) for c in (filtered_chunks or chunks)[:top_k]]

    evidence: List[Evidence] = []
    for score, c in selected_chunks:
        evidence.append(
            Evidence(
                text=c.text,
                source=c.source,
                score=score,
                title=c.title or c.heading or "Agricultural Reference Guide",
                issuing_organization=c.issuing_organization or "Agricultural Extension Reference",
                doc_date=c.doc_date or None,
                url_or_file=c.url_or_file or c.source or None,
                category=c.category,
                heading=c.heading or None,
            )
        )
    return evidence


def retrieve(query_text: str, top_k: int = 4, category: Optional[str] = None) -> List[Evidence]:
    """Performs semantic search over the indexed knowledge base with automatic fast fallback."""
    if not query_text or not query_text.strip():
        return []

    cleaned_query = query_text.strip()

    # Fast in-memory retrieval by default (0.002s, 0MB overhead) to prevent cloud container timeouts.
    # NEVER import heavy ChromaDB / PyTorch on Render unless explicitly requested.
    if os.getenv("USE_CHROMA_EMBEDDINGS", "false").lower() != "true":
        return _keyword_retrieve(cleaned_query, top_k=top_k, category=category)

    # Try ChromaDB dense retrieval only when USE_CHROMA_EMBEDDINGS=true
    try:
        from app.rag import vector_store
        from app.rag.embedding_service import embed_query
        embedding = embed_query(cleaned_query)
        where = {"category": category} if category else None
        results = vector_store.query(embedding, top_k=top_k, where=where)

        docs = results.get("documents", [[]])[0] if results else []
        metas = results.get("metadatas", [[]])[0] if results else []
        dists = results.get("distances", [[]])[0] if results else []

        if docs:
            evidence: List[Evidence] = []
            for doc, meta, dist in zip(docs, metas, dists):
                similarity = max(0.0, 1.0 - dist)
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
    except Exception:
        pass

    # Instantaneous in-memory fallback
    return _keyword_retrieve(cleaned_query, top_k=top_k, category=category)


def retrieve_for_recommendation(
    soil: Optional[SoilReport] = None,
    selected_crop: Optional[str] = None,
    deficiencies: Optional[List[Deficiency]] = None,
    user_question: Optional[str] = None,
    top_k: int = 4,
) -> List[Evidence]:
    """Constructs targeted agronomical queries and retrieves top evidence quickly."""
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

    # Retrieve from primary query to keep latency minimal
    evidence = retrieve(queries[0], top_k=top_k)
    if len(evidence) < top_k and len(queries) > 1:
        extra = retrieve(queries[1], top_k=top_k - len(evidence))
        seen = {e.text[:40] for e in evidence}
        for item in extra:
            if item.text[:40] not in seen:
                seen.add(item.text[:40])
                evidence.append(item)

    evidence.sort(key=lambda x: x.score, reverse=True)
    return evidence[:top_k]

