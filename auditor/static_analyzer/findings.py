from dataclasses import dataclass
from typing import Literal


Severity = Literal["HIGH", "MEDIUM", "LOW", "INFO"]


@dataclass
class Finding:
    rule_id: str       # e.g. "API1-BOLA", "API2-NO-PERMISSION"
    owasp_id: str      # e.g. "API1", "API2"
    title: str
    severity: Severity
    file: str
    line: int
    description: str
    evidence: str      # Línea de código que disparó la regla
