import ast
from typing import List
from .base import BaseRule
from ..findings import Finding


class DebugEnabledRule(BaseRule):
    """
    API8 — Detecta DEBUG = True en archivos de settings.
    Expone stack traces completos con información sensible del sistema.
    """

    def check(self, tree: ast.AST, filepath: str, source: str) -> List[Finding]:
        findings = []

        for node in ast.walk(tree):
            if not isinstance(node, ast.Assign):
                continue
            for target in node.targets:
                if not (isinstance(target, ast.Name) and target.id == "DEBUG"):
                    continue
                if isinstance(node.value, ast.Constant) and node.value.value is True:
                    findings.append(Finding(
                        rule_id="API8-DEBUG-ENABLED",
                        owasp_id="API8",
                        title="DEBUG=True habilitado en settings",
                        severity="HIGH",
                        file=filepath,
                        line=node.lineno,
                        description=(
                            "DEBUG=True expone stack traces completos con rutas del sistema, "
                            "variables de entorno y configuración interna ante cualquier error. "
                            "Debe ser False en cualquier entorno no local."
                        ),
                        evidence=self._get_line(source, node.lineno),
                    ))

        return findings
