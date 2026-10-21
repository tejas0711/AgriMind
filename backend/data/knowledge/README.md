# AgriMind Knowledge Base Documentation & Document Setup Guide

This directory (`backend/data/knowledge/`) contains curated, authoritative agricultural documents and knowledge files indexed by AgriMind's RAG (Retrieval-Augmented Generation) pipeline.

---

## 1. Supported Categories & Directory Structure

```
backend/data/knowledge/
├── crops/           # Crop nutrient requirements, phenology, and suitability guides
├── fertilizer/      # 4R stewardship, fertilizer types, split dosing, and placement
├── organic/         # FYM, compost, green manuring, biofertilizers, and regenerative practices
├── pesticides/      # IPM principles, safety boundaries, and regulatory guidance
├── soil/            # Soil Health Card standards, ICAR critical limits, and diagnostic criteria
└── README.md        # This setup guide and document policy
```

---

## 2. Document Acquisition & Inclusion Policy

To prevent hallucinations, inaccurate dosages, or non-peer-reviewed advice, all documents included in this knowledge base must satisfy the following strict criteria:

1. **Authoritative Sources Only:**
   - Prefer material from **ICAR** (Indian Council of Agricultural Research), State Agricultural Universities (SAUs), Krishi Vigyan Kendras (KVKs), Ministry of Agriculture & Farmers Welfare (Government of India), or international agricultural research centers (CGIAR/ICRISAT/CIMMYT/IRRI).
2. **Established Reuse Conditions:**
   - Public domain government extension, Open Government Data (OGD) India, Creative Commons (e.g. CC BY, CC BY-NC), or documented fair-use academic extension summaries.
3. **No Fabricated Documents:**
   - Every file must represent real, verifiable agricultural practices. Synthetic or imagined citations are strictly forbidden.
4. **Structured Layout:**
   - Documents must use standard Markdown with clear headings (`#`, `##`) and Markdown tables (`|`) so that layout-aware chunking can preserve contextual integrity.

---

## 3. Metadata Specification (YAML Frontmatter)

Each Markdown document (`.md`) should begin with a YAML frontmatter block containing structured metadata:

```yaml
---
title: "Document Title"
issuing_organization: "Authoritative Organization (e.g. ICAR, Ministry of Ag)"
doc_date: "Year or YYYY-MM"
url_or_file: "data/knowledge/<category>/<filename>.md"
license: "License or terms of use"
applicable_crops: "all | comma-separated list of crops"
applicable_regions: "India | State/Region"
category: "soil | crops | fertilizer | organic | pesticides"
---
```

When documents are indexed, these fields are stored directly in ChromaDB chunk metadata and surfaced on retrieved `Evidence` objects in the UI.

---

## 4. Rebuilding the RAG Index

The indexing command is completely repeatable and idempotent:

```powershell
# From the backend directory with virtual environment activated:
python -m app.rag.index_knowledge
```

This command:
1. Scans `data/knowledge/**` for `.md` and `.txt` files.
2. Parses document frontmatter and headings.
3. Chunks documents using layout-aware rules (preserving headings, tables, and Q&A units).
4. Generates dense embeddings using `sentence-transformers/all-MiniLM-L6-v2`.
5. Idempotently upserts chunks into ChromaDB at `backend/vector_db` using deterministic content hashes.
