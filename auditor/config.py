from pathlib import Path

# Directorio raíz del proyecto auditor
_ROOT = Path(__file__).parent.parent

# Directorio por defecto de la knowledge base
DEFAULT_KB_DIR = str(_ROOT / "knowledge_base")

# Directorio por defecto donde ChromaDB persiste los datos
DEFAULT_CHROMA_DIR = str(_ROOT / ".chroma_db")
