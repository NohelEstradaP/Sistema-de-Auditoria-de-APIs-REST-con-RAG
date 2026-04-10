import ast
from typing import List
from .base import BaseRule
from ..findings import Finding

_THROTTLE_KEY = "DEFAULT_THROTTLE_CLASSES"


class MissingThrottlingRule(BaseRule):
    """
    API4 — Detecta que REST_FRAMEWORK no define DEFAULT_THROTTLE_CLASSES.
    Sin rate limiting, la API es vulnerable a ataques de fuerza bruta y DoS.
    """

    def check(self, tree: ast.AST, filepath: str, source: str) -> List[Finding]:
        findings = []

        for node in ast.walk(tree):
            if not isinstance(node, ast.Assign):
                continue
            for target in node.targets:
                if not (isinstance(target, ast.Name) and target.id == "REST_FRAMEWORK"):
                    continue
                if not isinstance(node.value, ast.Dict):
                    continue

                keys = [
                    k.value
                    for k in node.value.keys
                    if isinstance(k, ast.Constant) and isinstance(k.value, str)
                ]

                if _THROTTLE_KEY not in keys:
                    findings.append(Finding(
                        rule_id="API4-NO-THROTTLING",
                        owasp_id="API4",
                        title="REST_FRAMEWORK sin DEFAULT_THROTTLE_CLASSES",
                        severity="MEDIUM",
                        file=filepath,
                        line=node.lineno,
                        description=(
                            "El diccionario REST_FRAMEWORK no define DEFAULT_THROTTLE_CLASSES "
                            "ni DEFAULT_THROTTLE_RATES. Sin rate limiting global, cualquier cliente "
                            "puede hacer requests ilimitados (fuerza bruta, scraping, DoS)."
                        ),
                        evidence=self._get_line(source, node.lineno),
                    ))

        return findings
