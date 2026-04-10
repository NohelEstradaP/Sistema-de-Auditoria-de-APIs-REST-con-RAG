"""
RAG Indexer — Fase 5.

Carga los documentos Markdown de knowledge_base/, los trocea en chunks
semánticos y los persiste en ChromaDB usando embeddings de sentence-transformers.
"""

from __future__ import annotations

import re
import uuid
from pathlib import Path
from typing import List

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

# Nombre de la colección ChromaDB
COLLECTION_NAME = "owasp_drf_kb"

# Modelo de embeddings (CPU-friendly, ~80 MB)
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Tamaño máximo de chunk en caracteres y overlap
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100


def _load_markdown_files(kb_dir: Path) -> List[tuple[str, str]]:
    """
    Lee todos los archivos .md de kb_dir.
    Retorna lista de (filename, content).
    """
    docs = []
    for md_file in sorted(kb_dir.glob("*.md")):
        content = md_file.read_text(encoding="utf-8")
        docs.append((md_file.name, content))
    return docs


def _split_by_sections(filename: str, content: str) -> List[dict]:
    """
    Divide un documento Markdown en secciones usando encabezados (## y ###).
    Cada sección se convierte en un chunk. Si la sección supera CHUNK_SIZE,
    se subdivide en ventanas deslizantes.
    """
    # Divide en secciones por encabezados ## o ###
    section_pattern = re.compile(r"(?=^#{2,3} .+)", re.MULTILINE)
    sections = section_pattern.split(content)

    chunks = []
    for section in sections:
        section = section.strip()
        if not section:
            continue

        # Extraer título de la sección para metadata
        first_line = section.splitlines()[0] if section.splitlines() else ""
        title = first_line.lstrip("#").strip()

        if len(section) <= CHUNK_SIZE:
            chunks.append({
                "text": section,
                "source": filename,
                "section": title,
            })
        else:
            # Ventana deslizante para secciones largas
            start = 0
            while start < len(section):
                end = start + CHUNK_SIZE
                chunk_text = section[start:end]
                chunks.append({
                    "text": chunk_text,
                    "source": filename,
                    "section": title,
                })
                start += CHUNK_SIZE - CHUNK_OVERLAP

    return chunks


def _get_chroma_client(persist_dir: str) -> chromadb.ClientAPI:
    return chromadb.PersistentClient(
        path=persist_dir,
        settings=Settings(anonymized_telemetry=False),
    )


def index_knowledge_base(
    kb_dir: str,
    chroma_dir: str,
    reset: bool = False,
) -> int:
    """
    Indexa los documentos de kb_dir en ChromaDB.

    Args:
        kb_dir: Ruta al directorio knowledge_base/.
        chroma_dir: Ruta donde ChromaDB persiste los datos.
        reset: Si True, elimina la colección existente antes de indexar.

    Returns:
        Número de chunks indexados.
    """
    kb_path = Path(kb_dir).resolve()
    chroma_path = Path(chroma_dir).resolve()
    chroma_path.mkdir(parents=True, exist_ok=True)

    # Cargar documentos
    docs = _load_markdown_files(kb_path)
    if not docs:
        raise ValueError(f"No se encontraron archivos .md en {kb_path}")

    # Trocear en chunks
    all_chunks: List[dict] = []
    for filename, content in docs:
        all_chunks.extend(_split_by_sections(filename, content))

    # Cargar modelo de embeddings
    model = SentenceTransformer(EMBEDDING_MODEL)

    # Generar embeddings
    texts = [c["text"] for c in all_chunks]
    embeddings = model.encode(texts, show_progress_bar=False).tolist()

    # Conectar a ChromaDB
    client = _get_chroma_client(str(chroma_path))

    if reset:
        try:
            client.delete_collection(COLLECTION_NAME)
        except Exception:
            pass

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    # Insertar chunks (ChromaDB ignora duplicados si el ID ya existe)
    ids = [str(uuid.uuid4()) for _ in all_chunks]
    metadatas = [{"source": c["source"], "section": c["section"]} for c in all_chunks]

    collection.add(
        ids=ids,
        documents=texts,
        embeddings=embeddings,
        metadatas=metadatas,
    )

    return len(all_chunks)


def get_collection(chroma_dir: str) -> chromadb.Collection:
    """Retorna la colección ChromaDB ya indexada."""
    client = _get_chroma_client(chroma_dir)
    return client.get_collection(COLLECTION_NAME)
