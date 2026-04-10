import ast
from typing import List
from .base import BaseRule
from ..findings import Finding


class MissingJWTConfigRule(BaseRule):
    """
    API2 — Detecta ausencia de configuración SIMPLE_JWT en settings.
    Sin configurar tiempos de expiración, los tokens JWT tienen vida larga
    por defecto (5 min access / 1 día refresh en simplejwt), aumentando el
    riesgo ante robo de tokens.
    """

    def check(self, tree: ast.AST, filepath: str, source: str) -> List[Finding]:
        has_simple_jwt = any(
            isinstance(node, ast.Assign)
            and any(
                isinstance(t, ast.Name) and t.id == "SIMPLE_JWT"
                for t in node.targets
            )
            for node in ast.walk(tree)
        )

        has_rest_framework = any(
            isinstance(node, ast.Assign)
            and any(
                isinstance(t, ast.Name) and t.id == "REST_FRAMEWORK"
                for t in node.targets
            )
            for node in ast.walk(tree)
        )

        # Solo reportar si el archivo parece ser un settings (tiene REST_FRAMEWORK)
        if has_rest_framework and not has_simple_jwt:
            return [Finding(
                rule_id="API2-NO-JWT-CONFIG",
                owasp_id="API2",
                title="Configuración SIMPLE_JWT ausente en settings",
                severity="LOW",
                file=filepath,
                line=1,
                description=(
                    "No se encontró la variable SIMPLE_JWT en settings. "
                    "Sin configuración explícita, los tokens usan los tiempos de expiración "
                    "por defecto de djangorestframework-simplejwt. Se recomienda definir "
                    "ACCESS_TOKEN_LIFETIME y REFRESH_TOKEN_LIFETIME según la política de seguridad."
                ),
                evidence="# SIMPLE_JWT = { ... }  <-- ausente",
            )]

        return []
