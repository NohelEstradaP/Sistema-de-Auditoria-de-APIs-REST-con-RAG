"""
Tests para auditor/rag/retriever.py.

Indexa una KB mínima en un directorio temporal y luego verifica
que el retriever devuelva chunks relevantes.
"""

import pytest
from pathlib import Path
from auditor.rag.indexer import index_knowledge_base
from auditor.rag.retriever import retrieve, retrieve_for_finding, RetrievedChunk


# ──────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────

@pytest.fixture(scope="module")
def indexed_chroma(tmp_path_factory):
    """
    Crea e indexa una knowledge base mínima una sola vez para todos
    los tests del módulo (scope=module para no repetir la codificación).
    """
    kb = tmp_path_factory.mktemp("kb")
    chroma = tmp_path_factory.mktemp("chroma")

    (kb / "owasp.md").write_text(
        "## API1 — Broken Object Level Authorization\n\n"
        "BOLA occurs when an API endpoint allows a user to access objects "
        "belonging to other users by manipulating the object ID in the URL.\n\n"
        "## API2 — Broken Authentication\n\n"
        "Authentication is broken when endpoints do not require a valid JWT token. "
        "Unauthenticated access to protected resources is a critical vulnerability.\n\n"
        "## API3 — Mass Assignment\n\n"
        "Mass assignment happens when serializers expose writable fields like "
        "is_admin or is_staff that should be read_only.\n\n"
        "## API4 — Unrestricted Resource Consumption\n\n"
        "Without throttling, an API is vulnerable to brute force and DoS attacks. "
        "Configure DEFAULT_THROTTLE_CLASSES in Django REST Framework settings.\n\n"
        "## API5 — Broken Function Level Authorization\n\n"
        "Admin endpoints accessible without checking the user's role allow privilege escalation.",
        encoding="utf-8",
    )

    index_knowledge_base(str(kb), str(chroma))
    return str(chroma)


# ──────────────────────────────────────────────
# Tests de retrieve
# ──────────────────────────────────────────────

def test_retrieve_returns_list(indexed_chroma):
    results = retrieve("BOLA object level authorization", indexed_chroma)
    assert isinstance(results, list)
    assert len(results) > 0


def test_retrieve_returns_retrieved_chunk_type(indexed_chroma):
    results = retrieve("JWT authentication token", indexed_chroma)
    for chunk in results:
        assert isinstance(chunk, RetrievedChunk)


def test_retrieve_chunk_has_text(indexed_chroma):
    results = retrieve("throttling rate limit", indexed_chroma)
    for chunk in results:
        assert chunk.text
        assert chunk.source
        assert isinstance(chunk.score, float)


def test_retrieve_score_between_0_and_1(indexed_chroma):
    results = retrieve("serializer is_admin read_only", indexed_chroma)
    for chunk in results:
        assert 0.0 <= chunk.score <= 1.0


def test_retrieve_top_k_respected(indexed_chroma):
    results = retrieve("authorization", indexed_chroma, top_k=2)
    assert len(results) <= 2


def test_retrieve_most_relevant_first(indexed_chroma):
    results = retrieve("BOLA object ownership", indexed_chroma, top_k=5)
    scores = [c.score for c in results]
    assert scores == sorted(scores, reverse=True)


# ──────────────────────────────────────────────
# Tests de retrieve_for_finding
# ──────────────────────────────────────────────

def test_retrieve_for_finding_api1(indexed_chroma):
    results = retrieve_for_finding(
        rule_id="API1-BOLA",
        description="El usuario bob accede a la orden de alice sin verificación de ownership.",
        chroma_dir=indexed_chroma,
    )
    assert len(results) > 0
    top_text = results[0].text.lower()
    assert any(kw in top_text for kw in ("bola", "object", "authorization", "ownership", "url"))


def test_retrieve_for_finding_api4(indexed_chroma):
    results = retrieve_for_finding(
        rule_id="API4-NO-THROTTLE",
        description="No se recibió 429 tras 20 requests consecutivos.",
        chroma_dir=indexed_chroma,
    )
    assert len(results) > 0
    combined = " ".join(c.text.lower() for c in results)
    assert "throttl" in combined or "rate" in combined or "consumpt" in combined


def test_retrieve_for_finding_unknown_rule(indexed_chroma):
    """Una regla desconocida no debe lanzar excepción."""
    results = retrieve_for_finding(
        rule_id="UNKNOWN-RULE",
        description="Some unknown finding description.",
        chroma_dir=indexed_chroma,
    )
    assert isinstance(results, list)
