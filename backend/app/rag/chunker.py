"""Chunking strategy for the RAG pipeline.

Preserves layout semantics:
1. Splits on Markdown headings (##, #) so each section stays whole.
2. Preserves Markdown tables (| ... |) and Q/A units intact without mid-table cuts.
3. Only falls back to a sliding window over raw paragraphs when a section exceeds max_chars.
4. Each chunk carries its originating heading and rich source metadata
   (title, issuing_organization, doc_date, url_or_file, applicable_crops, applicable_regions).
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Tuple, Optional

from app.rag.knowledge_loader import RawDocument

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$", re.MULTILINE)
QA_START_RE = re.compile(r"^\s*(Q(?:uestion)?\s*[:.\)]|Q\d+[:.\)])", re.IGNORECASE)


@dataclass
class Chunk:
    text: str
    source: str
    category: str
    heading: Optional[str]
    title: str = ""
    issuing_organization: str = ""
    doc_date: Optional[str] = None
    url_or_file: str = ""
    page_number: Optional[int] = None
    applicable_crops: str = "all"
    applicable_regions: str = "all"


def _split_by_headings(text: str) -> List[Tuple[Optional[str], str]]:
    """Return list of (heading, section_text) preserving heading context."""
    matches = list(HEADING_RE.finditer(text))
    if not matches:
        return [(None, text)]

    sections: List[Tuple[Optional[str], str]] = []
    # If text precedes the first heading, preserve it
    first_start = matches[0].start()
    if first_start > 0:
        preamble = text[:first_start].strip()
        if preamble:
            sections.append((None, preamble))

    for i, m in enumerate(matches):
        heading = m.group(2).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        if body:
            sections.append((heading, body))
    return sections


def _is_table_block(paragraph: str) -> bool:
    """Checks if a paragraph is predominantly a Markdown table."""
    lines = [line.strip() for line in paragraph.splitlines() if line.strip()]
    if not lines:
        return False
    table_lines = [l for l in lines if l.startswith("|") and l.endswith("|")]
    return len(table_lines) >= 2 and len(table_lines) >= len(lines) * 0.7


def _keep_semantic_units_together(section_text: str) -> List[str]:
    """Splits section into paragraph-like units while keeping Q/A pairs and tables intact."""
    raw_paragraphs = [p.strip() for p in re.split(r"\n\s*\n", section_text) if p.strip()]
    units: List[str] = []
    i = 0

    while i < len(raw_paragraphs):
        para = raw_paragraphs[i]

        # 1. Markdown tables are preserved as whole units
        if _is_table_block(para):
            units.append(para)
            i += 1
            continue

        # 2. Re-merge a question line with its following answer
        looks_like_question = bool(QA_START_RE.match(para)) or para.rstrip().endswith("?")
        is_short_question_only = looks_like_question and len(para) < 200
        if is_short_question_only and i + 1 < len(raw_paragraphs):
            units.append(para + "\n\n" + raw_paragraphs[i + 1])
            i += 2
        else:
            units.append(para)
            i += 1

    return units


def _sliding_window(text: str, max_chars: int, overlap: int) -> List[str]:
    """Splits large text blocks on paragraph or word boundaries."""
    if len(text) <= max_chars:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        if end < len(text):
            # Prefer cutting on whitespace
            last_space = text.rfind(" ", start, end)
            if last_space > start:
                end = last_space
        chunk_slice = text[start:end].strip()
        if chunk_slice:
            chunks.append(chunk_slice)
        start = max(end - overlap, end)
    return chunks


def chunk_document(doc: RawDocument, max_chars: int = 900, overlap: int = 100) -> List[Chunk]:
    """Splits a single document into layout-aware, metadata-rich chunks."""
    chunks: List[Chunk] = []

    for heading, section_text in _split_by_headings(doc.text):
        units = _keep_semantic_units_together(section_text)
        for unit in units:
            # If the unit is a table and exceeds max_chars slightly, keep it whole up to 1800 chars
            if _is_table_block(unit) and len(unit) <= max_chars * 2:
                pieces = [unit]
            else:
                pieces = _sliding_window(unit, max_chars=max_chars, overlap=overlap)

            for piece in pieces:
                prefixed = f"{heading}\n{piece}" if heading else piece
                chunks.append(
                    Chunk(
                        text=prefixed,
                        source=doc.source,
                        category=doc.category,
                        heading=heading,
                        title=doc.title,
                        issuing_organization=doc.issuing_organization,
                        doc_date=doc.doc_date,
                        url_or_file=doc.url_or_file,
                        applicable_crops=doc.applicable_crops,
                        applicable_regions=doc.applicable_regions,
                    )
                )

    return chunks


def chunk_documents(docs: List[RawDocument], **kwargs) -> List[Chunk]:
    """Chunks a list of RawDocument objects."""
    all_chunks: List[Chunk] = []
    for doc in docs:
        all_chunks.extend(chunk_document(doc, **kwargs))
    return all_chunks
