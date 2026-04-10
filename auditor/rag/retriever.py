"""
RAG Retriever — Fase 5.

Dado un hallazgo (rule_id + descripción), recupera los chunks más
relevantes de ChromaDB para enriquecer el prompt del LLM.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from sentence_transformers import SentenceTransformer

from .indexer import EMBEDDING_MODEL, get_collection

# Número de chunks a recuperar por hallazgo
DEFAULT_TOP_K = 5


@dataclass
class RetrievedChunk:
    text: str
    source: str       # nombre del archivo .md
    section: str      # título de la sección
    score: float      # similitud coseno (0–1, mayor = más relevante)


def retrieve(
    query: str,
    chroma_dir: str,
    top_k: int = DEFAULT_TOP_K,
) -> List[RetrievedChunk]:
    """
    Recupera los chunks más relevantes para una consulta.

    Args:
        query: Texto de búsqueda (ej. descripción de un hallazgo).
        chroma_dir: Directorio donde ChromaDB está persistido.
        top_k: Número máximo de chunks a retornar.

    Returns:
        Lista de RetrievedChunk ordenada por relevancia descendente.
    """
    model = SentenceTransformer(EMBEDDING_MODEL)
    query_embedding = model.encode([query], show_progress_bar=False).tolist()[0]

    collection = get_collection(chroma_dir)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k, collection.count()),
        include=["documents", "metadatas", "distances"],
    )

    chunks = []
    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    for doc, meta, dist in zip(documents, metadatas, distances):
        # ChromaDB con cosine distance: distance = 1 - similarity
        similarity = 1.0 - dist
        chunks.append(RetrievedChunk(
            text=doc,
            source=meta.get("source", ""),
            section=meta.get("section", ""),
            score=round(similarity, 4),
        ))

    return chunks


def retrieve_for_finding(
    rule_id: str,
    description: str,
    chroma_dir: str,
    top_k: int = DEFAULT_TOP_K,
) -> List[RetrievedChunk]:
    """
    Construye una consulta combinando rule_id y descripción del hallazgo
    para recuperar contexto relevante de la knowledge base.

    Args:
        rule_id: Identificador de la regla (ej. "API1-BOLA").
        description: Descripción textual del hallazgo.
        chroma_dir: Directorio ChromaDB.
        top_k: Número de chunks a recuperar.
    """
    # Mapeo de rule_id a términos de búsqueda explícitos
    _OWASP_TERMS = {
        "API1": "Broken Object Level Authorization BOLA ownership",
        "API2": "Broken Authentication JWT token permission",
        "API3": "Mass Assignment read_only serializer sensitive fields",
        "API4": "Unrestricted Resource Consumption throttling rate limit",
        "API5": "Broken Function Level Authorization admin role",
    }

    owasp_id = rule_id.split("-")[0] if "-" in rule_id else rule_id
    owasp_terms = _OWASP_TERMS.get(owasp_id, "")

    query = f"{owasp_terms} {description}".strip()
    return retrieve(query, chroma_dir, top_k=top_k)
