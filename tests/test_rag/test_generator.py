"""
Tests para auditor/rag/generator.py.

El cliente Ollama se mockea con unittest.mock para que los tests
sean rápidos y no dependan del servidor en CI.
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from dataclasses import dataclass

from auditor.rag.indexer import index_knowledge_base
from auditor.rag.generator import (
    generate_recommendation,
    enrich_findings,
    LLMRecommendation,
    _build_context,
    _extract_sources,
)
from auditor.rag.retriever import RetrievedChunk


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def _make_ollama_client(response_text: str) -> MagicMock:
    """Crea un cliente Ollama falso que devuelve response_text."""
    mock_response = MagicMock()
    mock_response.response = response_text
    client = MagicMock()
    client.generate.return_value = mock_response
    return client


def _make_chunks() -> list[RetrievedChunk]:
    return [
        RetrievedChunk(
            text="BOLA occurs when ownership is not verified.",
            source="owasp_api_top10_2023.md",
            section="API1 — BOLA",
            score=0.95,
        ),
        RetrievedChunk(
            text="Use get_queryset() filtered by request.user.",
            source="drf_security_guide.md",
            section="Object-Level Authorization",
            score=0.87,
        ),
    ]


# ──────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────

@pytest.fixture(scope="module")
def indexed_chroma(tmp_path_factory):
    kb = tmp_path_factory.mktemp("kb_gen")
    chroma = tmp_path_factory.mktemp("chroma_gen")
    (kb / "owasp.md").write_text(
        "## API1 — Broken Object Level Authorization\n\n"
        "BOLA occurs when object ownership is not validated. "
        "Use get_queryset filtered by owner.\n\n"
        "## API2 — Broken Authentication\n\n"
        "Require JWT tokens on every protected endpoint.\n",
        encoding="utf-8",
    )
    index_knowledge_base(str(kb), str(chroma))
    return str(chroma)


# ──────────────────────────────────────────────
# Tests de helpers internos
# ──────────────────────────────────────────────

def test_build_context_numbered():
    chunks = _make_chunks()
    ctx = _build_context(chunks)
    assert "[1]" in ctx
    assert "[2]" in ctx
    assert "owasp_api_top10_2023.md" in ctx
    assert "BOLA occurs" in ctx


def test_extract_sources_unique():
    chunks = _make_chunks() + [_make_chunks()[0]]  # Duplicado
    sources = _extract_sources(chunks)
    assert len(sources) == 2  # Deduplicado


def test_extract_sources_format():
    chunks = _make_chunks()
    sources = _extract_sources(chunks)
    assert any("owasp_api_top10_2023.md" in s for s in sources)
    assert any("drf_security_guide.md" in s for s in sources)


# ──────────────────────────────────────────────
# Tests de generate_recommendation
# ──────────────────────────────────────────────

def test_generate_returns_llm_recommendation(indexed_chroma):
    client = _make_ollama_client(
        "This endpoint is vulnerable to BOLA.\n\nSources: owasp_api_top10_2023.md"
    )
    rec = generate_recommendation(
        rule_id="API1-BOLA",
        owasp_id="API1",
        severity="HIGH",
        title="BOLA detected",
        location="GET /api/orders/1/",
        description="Bob accessed alice's order without ownership check.",
        chroma_dir=indexed_chroma,
        ollama_client=client,
    )
    assert isinstance(rec, LLMRecommendation)
    assert rec.rule_id == "API1-BOLA"
    assert rec.recommendation
    assert len(rec.sources) > 0
    assert len(rec.chunks_used) > 0


def test_generate_calls_ollama_with_prompt(indexed_chroma):
    client = _make_ollama_client("Fix: filter queryset by owner.\n\nSources: drf.md")
    generate_recommendation(
        rule_id="API1-BOLA",
        owasp_id="API1",
        severity="HIGH",
        title="BOLA",
        location="GET /api/orders/1/",
        description="Ownership not verified.",
        chroma_dir=indexed_chroma,
        ollama_client=client,
    )
    client.generate.assert_called_once()
    call_kwargs = client.generate.call_args
    prompt = call_kwargs[1].get("prompt") or call_kwargs[0][1]
    assert "API1-BOLA" in prompt
    assert "Ownership not verified" in prompt


def test_generate_prompt_includes_context(indexed_chroma):
    client = _make_ollama_client("Recommendation text.\n\nSources: owasp.md")
    rec = generate_recommendation(
        rule_id="API1-BOLA",
        owasp_id="API1",
        severity="HIGH",
        title="BOLA",
        location="GET /api/orders/1/",
        description="Ownership not verified.",
        chroma_dir=indexed_chroma,
        ollama_client=client,
    )
    # Los chunks deben haberse recuperado e incluido
    assert len(rec.chunks_used) > 0


def test_generate_model_stored_in_result(indexed_chroma):
    client = _make_ollama_client("Text.\n\nSources: x")
    rec = generate_recommendation(
        rule_id="API2-UNAUTH",
        owasp_id="API2",
        severity="HIGH",
        title="No auth",
        location="GET /api/users/",
        description="No token required.",
        chroma_dir=indexed_chroma,
        model="mistral",
        ollama_client=client,
    )
    assert rec.model == "mistral"


# ──────────────────────────────────────────────
# Tests de enrich_findings
# ──────────────────────────────────────────────

@dataclass
class _FakeFinding:
    rule_id: str
    owasp_id: str
    severity: str
    title: str
    description: str
    file: str = "views.py"
    line: int = 10


def test_enrich_findings_high_medium_only(indexed_chroma):
    client = _make_ollama_client("Fix it.\n\nSources: owasp.md")
    findings = [
        _FakeFinding("API1-BOLA", "API1", "HIGH", "BOLA", "Ownership not checked."),
        _FakeFinding("API2-UNAUTH", "API2", "MEDIUM", "No auth", "No token."),
        _FakeFinding("API8-DEBUG", "API8", "LOW", "Debug on", "DEBUG=True."),
        _FakeFinding("API8-INFO", "API8", "INFO", "Info", "Info finding."),
    ]
    recs = enrich_findings(findings, chroma_dir=indexed_chroma, ollama_client=client)
    assert len(recs) == 2  # Solo HIGH y MEDIUM
    rule_ids = {r.rule_id for r in recs}
    assert "API1-BOLA" in rule_ids
    assert "API2-UNAUTH" in rule_ids


def test_enrich_findings_returns_list(indexed_chroma):
    client = _make_ollama_client("OK.\n\nSources: x")
    findings = [
        _FakeFinding("API1-BOLA", "API1", "HIGH", "BOLA", "Desc."),
    ]
    recs = enrich_findings(findings, chroma_dir=indexed_chroma, ollama_client=client)
    assert isinstance(recs, list)
    assert all(isinstance(r, LLMRecommendation) for r in recs)


def test_enrich_findings_empty_list(indexed_chroma):
    client = _make_ollama_client("OK.\n\nSources: x")
    recs = enrich_findings([], chroma_dir=indexed_chroma, ollama_client=client)
    assert recs == []


def test_enrich_findings_skips_failed_gracefully(indexed_chroma):
    """Si el LLM falla en un hallazgo, no debe explotar el resto."""
    client = MagicMock()
    client.generate.side_effect = Exception("Ollama down")
    findings = [
        _FakeFinding("API1-BOLA", "API1", "HIGH", "BOLA", "Desc."),
    ]
    recs = enrich_findings(findings, chroma_dir=indexed_chroma, ollama_client=client)
    assert recs == []
