from app.rag.knowledge_loader import RawDocument
from app.rag.chunker import chunk_document


def test_heading_kept_as_context():
    doc = RawDocument(
        text="# Nitrogen\nNitrogen is important.\n\n# Phosphorus\nPhosphorus is also important.",
        source="test.md",
        category="soil",
    )
    chunks = chunk_document(doc)
    headings = {c.heading for c in chunks}
    assert "Nitrogen" in headings
    assert "Phosphorus" in headings


def test_qa_pair_not_split_apart():
    doc = RawDocument(
        text="# FAQ\nQ: What is the ideal pH for tomato?\n\nA: Between 6.0 and 6.8.\n\nQ: What about wheat?\n\nA: 6.0 to 7.5.",
        source="faq.md",
        category="crops",
    )
    chunks = chunk_document(doc)
    combined_texts = [c.text for c in chunks]
    # Each question should appear in the SAME chunk as its answer.
    tomato_chunk = next(t for t in combined_texts if "tomato" in t.lower())
    assert "6.0 and 6.8" in tomato_chunk
