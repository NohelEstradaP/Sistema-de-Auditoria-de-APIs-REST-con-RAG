from typing import List
from .base import BaseProbe
from ..findings import DynamicFinding

_ADMIN_ENDPOINTS = [
    ("GET", "/api/admin-panel/"),
]


class FunctionLevelAuthzProbe(BaseProbe):
    """
    API5 — Broken Function Level Authorization.
    Accede a endpoints de administración sin token ni rol de admin.
    Si responde 200, cualquier usuario (o anónimo) puede usar funciones privilegiadas.
    """

    def run(self) -> List[DynamicFinding]:
        findings = []

        for method, path in _ADMIN_ENDPOINTS:
            try:
                resp = self.session.request(method, self.url(path), timeout=5)
            except Exception:
                continue

            if resp.status_code == 200:
                findings.append(DynamicFinding(
                    rule_id="API5-FUNC-AUTHZ",
                    owasp_id="API5",
                    title=f"Función admin accesible sin rol: {method} {path}",
                    severity="HIGH",
                    endpoint=path,
                    method=method,
                    description=(
                        "El endpoint de administración responde 200 sin requerir autenticación "
                        "ni verificar que el usuario tenga rol de administrador. "
                        "Cualquier cliente puede invocar funciones privilegiadas."
                    ),
                    evidence=f"HTTP {resp.status_code} sin token. "
                             f"Body (primeros 200 chars): {resp.text[:200]}",
                ))

        return findings
