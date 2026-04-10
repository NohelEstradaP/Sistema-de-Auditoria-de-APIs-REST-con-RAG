from typing import List, Type
import requests

from .findings import DynamicFinding
from .probes import ALL_PROBES
from .probes.base import BaseProbe


def run_dynamic_analysis(
    base_url: str,
    probes: List[Type[BaseProbe]] = None,
) -> List[DynamicFinding]:
    """
    Ejecuta todas las pruebas dinámicas contra la API en base_url.

    Args:
        base_url: URL base de la API (ej. "http://localhost:8000").
        probes: Lista de clases probe a ejecutar. Por defecto ALL_PROBES.

    Returns:
        Lista de DynamicFinding ordenada por owasp_id.
    """
    if probes is None:
        probes = ALL_PROBES

    session = requests.Session()
    findings: List[DynamicFinding] = []

    for ProbeClass in probes:
        probe = ProbeClass(base_url=base_url, session=session)
        try:
            results = probe.run()
            findings.extend(results)
        except Exception:
            pass

    findings.sort(key=lambda f: f.owasp_id)
    return findings
