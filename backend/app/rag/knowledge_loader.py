"""Walks data/knowledge/** and loads raw documents with structured metadata.

Supports .md and .txt files, parsing YAML frontmatter when present to extract
authoritative source title, issuing organization, document date, license,
applicable crops, and applicable regions.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Optional, Dict, Tuple, List

KNOWLEDGE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "knowledge")

H1_RE = re.compile(r"^#\s+(.+)$", re.MULTILINE)


@dataclass
class RawDocument:
    text: str
    source: str                 # relative file path, used for citations (e.g. "soil/icar_soil_fertility_guidelines.md")
    category: str               # soil | crops | fertilizer | organic | pesticides
    title: str = ""             # Document title (from frontmatter or H1)
    issuing_organization: str = "Agricultural Extension Reference"   # Authoritative body
    doc_date: Optional[str] = None
    url_or_file: str = ""
    license: Optional[str] = "Agricultural Public Domain / Extension"
    applicable_crops: str = "all"
    applicable_regions: str = "India"


def _parse_frontmatter(raw_text: str) -> Tuple[Dict[str, str], str]:
    """Extracts key-value frontmatter bounded by --- markers."""
    if raw_text.startswith("---"):
        parts = raw_text.split("---", 2)
        if len(parts) >= 3:
            fm_text = parts[1]
            body = parts[2].strip()
            meta: Dict[str, str] = {}
            for line in fm_text.splitlines():
                line = line.strip()
                if ":" in line and not line.startswith("#"):
                    k, v = line.split(":", 1)
                    meta[k.strip().lower()] = v.strip().strip('"').strip("'")
            return meta, body
    return {}, raw_text.strip()


def load_documents(knowledge_dir: str = KNOWLEDGE_DIR) -> List[RawDocument]:
    """Loads all knowledge markdown documents, parsing structured metadata."""
    docs: List[RawDocument] = []
    knowledge_dir = os.path.abspath(knowledge_dir)

    if not os.path.exists(knowledge_dir):
        return docs

    for category in sorted(os.listdir(knowledge_dir)):
        category_path = os.path.join(knowledge_dir, category)
        if not os.path.isdir(category_path):
            continue

        for fname in sorted(os.listdir(category_path)):
            if not fname.lower().endswith((".md", ".txt")):
                continue

            fpath = os.path.join(category_path, fname)
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()

            meta, body = _parse_frontmatter(content)

            # Derive title: from frontmatter -> first H1 -> filename
            title = meta.get("title")
            if not title:
                h1_match = H1_RE.search(body)
                title = h1_match.group(1).strip() if h1_match else fname.replace("_", " ").replace(".md", "").title()

            doc_source = f"{category}/{fname}"
            issuing_org = meta.get("issuing_organization") or "Agricultural Extension Reference"
            doc_date = meta.get("doc_date")
            url_or_file = meta.get("url_or_file") or f"data/knowledge/{doc_source}"
            license_info = meta.get("license") or "Agricultural Public Domain / Extension"
            applicable_crops = meta.get("applicable_crops") or "all"
            applicable_regions = meta.get("applicable_regions") or "India"

            docs.append(
                RawDocument(
                    text=body,
                    source=doc_source,
                    category=meta.get("category") or category,
                    title=title,
                    issuing_organization=issuing_org,
                    doc_date=doc_date,
                    url_or_file=url_or_file,
                    license=license_info,
                    applicable_crops=applicable_crops,
                    applicable_regions=applicable_regions,
                )
            )

    return docs
