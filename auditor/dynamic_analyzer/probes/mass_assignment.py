from typing import List
from .base import BaseProbe
from ..findings import DynamicFinding


class MassAssignmentProbe(BaseProbe):
    """
    API3 — Broken Object Property Level Authorization (Mass Assignment).
    Envía POST /api/users/ con is_admin=true e is_staff=true.
    Si el objeto creado contiene esos valores, el serializer acepta campos
    privilegiados sin protección.
    """

    def run(self) -> List[DynamicFinding]:
        payload = {
            "username": "hacker_probe",
            "email": "hacker@probe.com",
            "password": "probe1234",
            "is_admin": True,
            "is_staff": True,
        }
        path = "/api/users/"

        try:
            resp = self.session.post(self.url(path), json=payload, timeout=5)
        except Exception:
            return []

        if resp.status_code not in (200, 201):
            return []

        body = resp.json()
        vulnerable_fields = [f for f in ("is_admin", "is_staff") if body.get(f) is True]

        if vulnerable_fields:
            return [DynamicFinding(
                rule_id="API3-MASS-ASSIGN",
                owasp_id="API3",
                title="Mass assignment: campos privilegiados aceptados en POST",
                severity="HIGH",
                endpoint=path,
                method="POST",
                description=(
                    f"El endpoint acepta y persiste los campos {vulnerable_fields} "
                    "enviados por el cliente sin restricción. Un atacante puede crear "
                    "usuarios con privilegios de administrador."
                ),
                evidence=f"Campos {vulnerable_fields} con valor True en respuesta {resp.status_code}. "
                         f"Body: {resp.text[:200]}",
            )]

        return []
