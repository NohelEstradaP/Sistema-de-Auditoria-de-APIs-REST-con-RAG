"""
RAG Generator — Fase 6.

Flujo:
    Hallazgo → retrieve_for_finding() → chunks → build_prompt() → Ollama → LLMRecommendation

La recomendación incluye citas a los fragmentos de documentación recuperados,
lo que garantiza trazabilidad hacia OWASP / DRF docs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

import ollama

from .retriever import RetrievedChunk, retrieve_for_finding
from ..config import DEFAULT_CHROMA_DIR

# Modelo por defecto (configurable en tiempo de ejecución)
DEFAULT_MODEL = "mistral"

# Número de chunks de contexto a inyectar en el prompt
DEFAULT_TOP_K = 4

# Temperatura baja → respuestas deterministas y enfocadas
_TEMPERATURE = 0.2

# Límite de tokens de salida
_MAX_TOKENS = 512

_PROMPT_TEMPLATE = """\
You are a security expert specializing in Django REST Framework (DRF) API security.
A security audit has detected the following vulnerability:

FINDING
-------
Rule ID   : {rule_id}
OWASP ID  : {owasp_id}
Severity  : {severity}
Title     : {title}
Location  : {location}
Description: {description}

REFERENCE DOCUMENTATION (retrieved from OWASP and DRF knowledge base)
----------------------------------------------------------------------
{context}

TASK
----
Based ONLY on the reference documentation above, write a concise security recommendation
that explains:
1. Why this is dangerous.
2. The specific code fix for Django REST Framework.
3. Which OWASP API Security category it maps to.

End your response with a "Sources:" section listing the document names you cited.
Write in English. Be direct and actionable. Do not invent information not present in the references.
"""


@dataclass
class LLMRecommendation:
    rule_id: str
    recommendation: str          # Texto generado por el LLM
    sources: List[str]           # Nombres de documentos citados
    chunks_used: List[RetrievedChunk] = field(default_factory=list)
    model: str = DEFAULT_MODEL


def _build_context(chunks: List[RetrievedChunk]) -> str:
    """Formatea los chunks como contexto numerado para el prompt."""
    parts = []
    for i, chunk in enumerate(chunks, 1):
        parts.append(
            f"[{i}] Source: {chunk.source} — {chunk.section}\n"
            f"{chunk.text.strip()}"
        )
    return "\n\n".join(parts)


def _extract_sources(chunks: List[RetrievedChunk]) -> List[str]:
    """Extrae los nombres de fuente únicos de los chunks usados."""
    seen = set()
    sources = []
    for c in chunks:
        key = f"{c.source} — {c.section}"
        if key not in seen:
            seen.add(key)
            sources.append(key)
    return sources


def generate_recommendation(
    rule_id: str,
    owasp_id: str,
    severity: str,
    title: str,
    location: str,
    description: str,
    chroma_dir: str = DEFAULT_CHROMA_DIR,
    model: str = DEFAULT_MODEL,
    top_k: int = DEFAULT_TOP_K,
    ollama_client: Optional[ollama.Client] = None,
) -> LLMRecommendation:
    """
    Genera una recomendación de seguridad enriquecida con RAG para un hallazgo.

    Args:
        rule_id: Identificador de la regla (ej. "API1-BOLA").
        owasp_id: Categoría OWASP (ej. "API1").
        severity: Severidad del hallazgo.
        title: Título del hallazgo.
        location: Archivo:línea o endpoint:método.
        description: Descripción detallada del hallazgo.
        chroma_dir: Directorio ChromaDB con la KB indexada.
        model: Modelo Ollama a usar.
        top_k: Número de chunks RAG a recuperar.
        ollama_client: Cliente Ollama inyectable (para tests).

    Returns:
        LLMRecommendation con el texto generado y sus citas.
    """
    # 1. Recuperar chunks relevantes
    chunks = retrieve_for_finding(
        rule_id=rule_id,
        description=description,
        chroma_dir=chroma_dir,
        top_k=top_k,
    )

    # 2. Construir prompt
    context = _build_context(chunks)
    prompt = _PROMPT_TEMPLATE.format(
        rule_id=rule_id,
        owasp_id=owasp_id,
        severity=severity,
        title=title,
        location=location,
        description=description,
        context=context,
    )

    # 3. Llamar al LLM
    client = ollama_client or ollama.Client()
    response = client.generate(
        model=model,
        prompt=prompt,
        options={
            "temperature": _TEMPERATURE,
            "num_predict": _MAX_TOKENS,
        },
    )

    recommendation_text = response.response.strip()
    sources = _extract_sources(chunks)

    return LLMRecommendation(
        rule_id=rule_id,
        recommendation=recommendation_text,
        sources=sources,
        chunks_used=chunks,
        model=model,
    )


def enrich_findings(
    findings,
    chroma_dir: str = DEFAULT_CHROMA_DIR,
    model: str = DEFAULT_MODEL,
    ollama_client: Optional[ollama.Client] = None,
) -> List[LLMRecommendation]:
    """
    Genera recomendaciones LLM para una lista de hallazgos (estáticos o dinámicos).
    Solo procesa hallazgos de severidad HIGH o MEDIUM.

    Args:
        findings: Lista de Finding o DynamicFinding.
        chroma_dir: Directorio ChromaDB.
        model: Modelo Ollama.
        ollama_client: Cliente inyectable para tests.

    Returns:
        Lista de LLMRecommendation, una por hallazgo procesado.
    """
    from ..dynamic_analyzer.findings import DynamicFinding

    recommendations = []
    for f in findings:
        if f.severity not in ("HIGH", "MEDIUM"):
            continue

        # Normalizar la "ubicación" según tipo de hallazgo
        if isinstance(f, DynamicFinding):
            location = f"{f.method} {f.endpoint}"
        else:
            location = f"{f.file}:{f.line}"

        try:
            rec = generate_recommendation(
                rule_id=f.rule_id,
                owasp_id=f.owasp_id,
                severity=f.severity,
                title=f.title,
                location=location,
                description=f.description,
                chroma_dir=chroma_dir,
                model=model,
                ollama_client=ollama_client,
            )
            recommendations.append(rec)
        except Exception:
            pass

    return recommendations
