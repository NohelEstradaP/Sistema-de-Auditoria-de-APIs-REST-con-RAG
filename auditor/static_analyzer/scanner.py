import ast
from pathlib import Path
from typing import List

from .findings import Finding
from .rules import ALL_RULES

# Directorios que no deben analizarse
_SKIP_DIRS = {
    "venv", ".venv", "env", ".env",
    "migrations", "__pycache__",
    ".git", "node_modules",
    "site-packages",
}


def _should_skip(path: Path) -> bool:
    return any(part in _SKIP_DIRS for part in path.parts)


def scan_project(project_path: str) -> List[Finding]:
    """
    Analiza estáticamente todos los archivos .py de un proyecto DRF.

    Args:
        project_path: Ruta raíz del proyecto Django a auditar.

    Returns:
        Lista de Finding ordenada por archivo y número de línea.
    """
    root = Path(project_path).resolve()
    findings: List[Finding] = []

    for py_file in sorted(root.rglob("*.py")):
        if _should_skip(py_file):
            continue

        try:
            source = py_file.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(py_file))
        except (SyntaxError, UnicodeDecodeError):
            continue

        for rule in ALL_RULES:
            findings.extend(rule.check(tree, str(py_file), source))

    findings.sort(key=lambda f: (f.file, f.line))
    return findings
