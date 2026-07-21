"""
Report Builder — Fase 7.

Agrupa hallazgos estáticos, dinámicos y recomendaciones LLM en un
AuditReport listo para exportar a HTML o PDF.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Union

from ..dynamic_analyzer.findings import DynamicFinding
from ..static_analyzer.findings import Finding
from ..rag.generator import LLMRecommendation

AnyFinding = Union[Finding, DynamicFinding]

_SEVERITY_ORDER = {"HIGH": 0, "MEDIUM": 1, "LOW": 2, "INFO": 3}


@dataclass
class ReportMetrics:
    total_findings: int
    high: int
    medium: int
    low: int
    info: int
    static_count: int
    dynamic_count: int
    recommendations_count: int
    owasp_coverage: List[str]   # IDs únicos detectados, ej. ["API1", "API2"]


@dataclass
class AuditReport:
    project_path: str
    generated_at: str
    findings: List[AnyFinding]
    recommendations: List[LLMRecommendation]
    metrics: ReportMetrics


def build_report(
    project_path: str,
    findings: List[AnyFinding],
    recommendations: List[LLMRecommendation] = None,
) -> AuditReport:
    """
    Construye un AuditReport a partir de los hallazgos y recomendaciones.

    Args:
        project_path: Ruta del proyecto auditado.
        findings: Lista combinada de Finding y DynamicFinding.
        recommendations: Lista de LLMRecommendation (puede ser vacía).

    Returns:
        AuditReport listo para exportar.
    """
    if recommendations is None:
        recommendations = []

    sorted_findings = sorted(
        findings,
        key=lambda f: (_SEVERITY_ORDER.get(f.severity, 9), f.owasp_id),
    )

    counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0}
    static_count = 0
    dynamic_count = 0
    owasp_ids = set()

    for f in findings:
        counts[f.severity] = counts.get(f.severity, 0) + 1
        owasp_ids.add(f.owasp_id)
        if isinstance(f, DynamicFinding):
            dynamic_count += 1
        else:
            static_count += 1

    metrics = ReportMetrics(
        total_findings=len(findings),
        high=counts["HIGH"],
        medium=counts["MEDIUM"],
        low=counts["LOW"],
        info=counts["INFO"],
        static_count=static_count,
        dynamic_count=dynamic_count,
        recommendations_count=len(recommendations),
        owasp_coverage=sorted(owasp_ids),
    )

    return AuditReport(
        project_path=project_path,
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        findings=sorted_findings,
        recommendations=recommendations,
        metrics=metrics,
    )
