import ast
import re
from typing import List
from .base import BaseRule
from ..findings import Finding

# Detecta patrones como <int:pk>, <int:id>, <int:user_id>, etc.
_INT_PARAM_RE = re.compile(r"<int:\w+>")


class BolaUrlParamsRule(BaseRule):
    """
    API1 — Detecta rutas con parámetros enteros (ej. <int:pk>) que son
    candidatos a BOLA (Broken Object Level Authorization).
    El análisis estático no puede verificar si la vista valida ownership,
    por lo que se reporta como hallazgo de revisión manual requerida.
    """

    def check(self, tree: ast.AST, filepath: str, source: str) -> List[Finding]:
        findings = []

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue

            # Busca llamadas a path(...) o re_path(...)
            func_name = None
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                func_name = node.func.attr

            if func_name not in ("path", "re_path"):
                continue

            if not node.args:
                continue

            first_arg = node.args[0]
            if not isinstance(first_arg, ast.Constant):
                continue

            pattern = str(first_arg.value)
            if _INT_PARAM_RE.search(pattern):
                findings.append(Finding(
                    rule_id="API1-BOLA-URL",
                    owasp_id="API1",
                    title=f"Posible BOLA en ruta '{pattern}'",
                    severity="HIGH",
                    file=filepath,
                    line=node.lineno,
                    description=(
                        f"La ruta '{pattern}' acepta un identificador numérico. "
                        "Si la vista correspondiente no verifica que el objeto solicitado "
                        "pertenece al usuario autenticado, cualquier usuario puede acceder "
                        "a datos ajenos cambiando el parámetro (BOLA/IDOR)."
                    ),
                    evidence=self._get_line(source, node.lineno),
                ))

        return findings
