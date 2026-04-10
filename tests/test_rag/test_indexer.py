"""
Tests para auditor/rag/indexer.py.

Usa directorios temporales — no toca la knowledge base ni ChromaDB reales.
"""

import pytest
from pathlib import Path
from auditor.rag.indexer import (
    index_knowledge_base,
    get_collection,
    _load_markdown_files,
    _split_by_sections,
    COLLECTION_NAME,
)


# ──────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────

@pytest.fixture()
def kb_dir(tmp_path: Path) -> Path:
    """Knowledge base mínima con dos documentos."""
    doc1 = tmp_path / "owasp.md"
    doc1.write_text(
        "# OWASP API Top 10\n\n"
        "## API1 — BOLA\n\nBroken Object Level Authorization occurs when...\n\n"
        "## API2 — Broken Authentication\n\nAuthentication is broken when tokens are not validated.\n",
        encoding="utf-8",
    )
    doc2 = tmp_path / "drf.md"
    doc2.write_text(
        "# DRF Security\n\n"
        "## Permission Classes\n\nAlways set permission_classes = [IsAuthenticated].\n\n"
        "## Throttling\n\nConfigure DEFAULT_THROTTLE_CLASSES in settings.\n",
        encoding="utf-8",
    )
    return tmp_path


@pytest.fixture()
def chroma_dir(tmp_path: Path) -> Path:
    return tmp_path / "chroma"


# ──────────────────────────────────────────────
# Tests de _load_markdown_files
# ──────────────────────────────────────────────

def test_load_markdown_files(kb_dir):
    docs = _load_markdown_files(kb_dir)
    filenames = [d[0] for d in docs]
    assert "owasp.md" in filenames
    assert "drf.md" in filenames
    assert len(docs) == 2


def test_load_markdown_files_empty_dir(tmp_path):
    docs = _load_markdown_files(tmp_path)
    assert docs == []


# ──────────────────────────────────────────────
# Tests de _split_by_sections
# ──────────────────────────────────────────────

def test_split_produces_chunks():
    content = (
        "# Title\n\n"
        "## Section A\n\nContent about BOLA.\n\n"
        "## Section B\n\nContent about authentication.\n"
    )
    chunks = _split_by_sections("test.md", content)
    assert len(chunks) >= 2


def test_chunk_has_required_keys():
    content = "## API1 — BOLA\n\nSome content here."
    chunks = _split_by_sections("owasp.md", content)
    assert len(chunks) >= 1
    assert "text" in chunks[0]
    assert "source" in chunks[0]
    assert "section" in chunks[0]
    assert chunks[0]["source"] == "owasp.md"


def test_section_title_extracted():
    content = "## API1 — Broken Object Level Authorization\n\nContent."
    chunks = _split_by_sections("owasp.md", content)
    assert any("API1" in c["section"] for c in chunks)


# ──────────────────────────────────────────────
# Tests de index_knowledge_base
# ──────────────────────────────────────────────

def test_index_returns_chunk_count(kb_dir, chroma_dir):
    count = index_knowledge_base(str(kb_dir), str(chroma_dir))
    assert count > 0


def test_index_creates_chroma_dir(kb_dir, tmp_path):
    chroma = tmp_path / "new_chroma"
    assert not chroma.exists()
    index_knowledge_base(str(kb_dir), str(chroma))
    assert chroma.exists()


def test_index_collection_has_documents(kb_dir, chroma_dir):
    count = index_knowledge_base(str(kb_dir), str(chroma_dir))
    collection = get_collection(str(chroma_dir))
    assert collection.count() == count


def test_index_reset_clears_previous(kb_dir, chroma_dir):
    index_knowledge_base(str(kb_dir), str(chroma_dir))
    first_count = get_collection(str(chroma_dir)).count()

    # Reset debe limpiar y reindexar
    index_knowledge_base(str(kb_dir), str(chroma_dir), reset=True)
    second_count = get_collection(str(chroma_dir)).count()

    assert second_count == first_count


def test_index_raises_on_empty_kb(tmp_path, chroma_dir):
    with pytest.raises(ValueError, match="No se encontraron"):
        index_knowledge_base(str(tmp_path), str(chroma_dir))
