import ast
from abc import ABC, abstractmethod
from typing import List
from ..findings import Finding


class BaseRule(ABC):
    """Clase base para todas las reglas de análisis estático."""

    @abstractmethod
    def check(self, tree: ast.AST, filepath: str, source: str) -> List[Finding]:
        """
        Analiza el AST de un archivo y retorna los hallazgos encontrados.

        Args:
            tree: AST del archivo Python.
            filepath: Ruta absoluta del archivo analizado.
            source: Código fuente completo del archivo.
        """
        ...

    def _get_line(self, source: str, lineno: int) -> str:
        """Retorna la línea de código (1-indexed) limpia de espacios."""
        lines = source.splitlines()
        if 1 <= lineno <= len(lines):
            return lines[lineno - 1].strip()
        return ""
