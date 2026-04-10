from dataclasses import dataclass
from typing import Literal

Severity = Literal["HIGH", "MEDIUM", "LOW", "INFO"]


@dataclass
class DynamicFinding:
    rule_id: str       # e.g. "API1-BOLA", "API2-UNAUTH"
    owasp_id: str      # e.g. "API1", "API2"
    title: str
    severity: Severity
    endpoint: str      # e.g. "/api/orders/2/"
    method: str        # e.g. "GET", "POST"
    description: str
    evidence: str      # Respuesta o dato que confirma la vulnerabilidad
