from typing import List
from .base import BaseProbe
from ..findings import DynamicFinding

# Endpoints que deben requerir autenticación
_PROTECTED_ENDPOINTS = [
    ("GET", "/api/users/"),
    ("GET", "/api/orders/"),
    ("GET", "/api/admin-panel/"),
]


class UnauthenticatedAccessProbe(BaseProbe):
    """
    API2 — Broken Authentication.
    Verifica que los endpoints protegidos devuelvan 401 sin token.
    Si responden 200, la autenticación está rota.
    """

    def run(self) -> List[DynamicFinding]:
        findings = []

        for method, path in _PROTECTED_ENDPOINTS:
            try:
                resp = self.session.request(method, self.url(path), timeout=5)
            except Exception as exc:
                continue

            if resp.status_code == 200:
                findings.append(DynamicFinding(
                    rule_id="API2-UNAUTH",
                    owasp_id="API2",
                    title=f"Acceso sin autenticación: {method} {path}",
                    severity="HIGH",
                    endpoint=path,
                    method=method,
                    description=(
                        "El endpoint responde 200 sin requerir token de autenticación. "
                        "Cualquier cliente puede acceder a datos sensibles sin identificarse."
                    ),
                    evidence=f"HTTP {resp.status_code} (esperado 401). "
                             f"Body (primeros 200 chars): {resp.text[:200]}",
                ))

        return findings
