from typing import List, Optional
from .base import BaseProbe
from ..findings import DynamicFinding


def _get_token(session, base_url: str, username: str, password: str) -> Optional[str]:
    try:
        resp = session.post(
            f"{base_url}/api/auth/login/",
            json={"username": username, "password": password},
            timeout=5,
        )
        return resp.json().get("access")
    except Exception:
        return None


class BOLAProbe(BaseProbe):
    """
    API1 — Broken Object Level Authorization (BOLA).
    Inicia sesión como 'bob' y solicita /api/orders/1/ (que pertenece a alice).
    Si responde 200, el servidor no verifica ownership del objeto.
    """

    def run(self) -> List[DynamicFinding]:
        token = _get_token(self.session, self.base_url, "bob", "bob123")
        if token is None:
            return []

        headers = {"Authorization": f"Bearer {token}"}
        path = "/api/orders/1/"

        try:
            resp = self.session.get(self.url(path), headers=headers, timeout=5)
        except Exception:
            return []

        if resp.status_code == 200:
            return [DynamicFinding(
                rule_id="API1-BOLA",
                owasp_id="API1",
                title="BOLA: acceso a objeto de otro usuario",
                severity="HIGH",
                endpoint=path,
                method="GET",
                description=(
                    "El usuario 'bob' puede acceder a /api/orders/1/ que pertenece a 'alice'. "
                    "El servidor no verifica que el objeto solicitado pertenezca al usuario autenticado."
                ),
                evidence=f"HTTP {resp.status_code} con token de bob. "
                         f"Body: {resp.text[:200]}",
            )]

        return []
