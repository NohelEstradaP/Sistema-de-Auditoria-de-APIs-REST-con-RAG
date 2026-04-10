from typing import List
from .base import BaseProbe
from ..findings import DynamicFinding

_REQUESTS_TO_SEND = 20   # En la API vulnerable no hay throttling: 20 bastan para confirmar
_ENDPOINT = "/api/products/"


class ThrottlingProbe(BaseProbe):
    """
    API4 — Unrestricted Resource Consumption.
    Envía múltiples requests rápidos al mismo endpoint.
    Si ninguno devuelve 429 (Too Many Requests), no hay throttling configurado.
    """

    def run(self) -> List[DynamicFinding]:
        got_429 = False

        for _ in range(_REQUESTS_TO_SEND):
            try:
                resp = self.session.get(self.url(_ENDPOINT), timeout=5)
                if resp.status_code == 429:
                    got_429 = True
                    break
            except Exception:
                break

        if not got_429:
            return [DynamicFinding(
                rule_id="API4-NO-THROTTLE",
                owasp_id="API4",
                title="Sin throttling: endpoint no limita requests",
                severity="MEDIUM",
                endpoint=_ENDPOINT,
                method="GET",
                description=(
                    f"Se enviaron {_REQUESTS_TO_SEND} requests consecutivos a {_ENDPOINT} "
                    "sin recibir respuesta 429 (Too Many Requests). "
                    "La API no tiene rate limiting configurado."
                ),
                evidence=f"{_REQUESTS_TO_SEND} requests respondidos sin HTTP 429.",
            )]

        return []
