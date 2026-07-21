import pytest
from auditor.report.builder import build_report, AuditReport, ReportMetrics
from auditor.static_analyzer.findings import Finding
from auditor.dynamic_analyzer.findings import DynamicFinding
from auditor.rag.generator import LLMRecommendation


def _static(rule_id="API2-NO-PERMISSION", owasp_id="API2", severity="HIGH"):
    return Finding(
        rule_id=rule_id, owasp_id=owasp_id,
        title="Test finding", severity=severity,
        file="views.py", line=10,
        description="No permission classes.", evidence="class MyView(APIView):",
    )


def _dynamic(rule_id="API1-BOLA", owasp_id="API1", severity="HIGH"):
    return DynamicFinding(
        rule_id=rule_id, owasp_id=owasp_id,
        title="BOLA test", severity=severity,
        endpoint="/api/orders/1/", method="GET",
        description="Ownership not checked.", evidence="HTTP 200",
    )


def _rec(rule_id="API1-BOLA"):
    return LLMRecommendation(
        rule_id=rule_id,
        recommendation="Use get_queryset filtered by owner.",
        sources=["owasp_api_top10_2023.md — API1"],
        model="mistral",
    )


# ── build_report ──────────────────────────────

def test_build_report_returns_audit_report():
    report = build_report("/proj", [_static()], [_rec()])
    assert isinstance(report, AuditReport)


def test_build_report_stores_project_path():
    report = build_report("/my/project", [_static()])
    assert report.project_path == "/my/project"


def test_build_report_has_generated_at():
    report = build_report("/proj", [_static()])
    assert report.generated_at  # no vacío
    assert "-" in report.generated_at  # tiene formato fecha


def test_build_report_no_findings():
    report = build_report("/proj", [])
    assert report.metrics.total_findings == 0
    assert report.metrics.high == 0


def test_build_report_no_recommendations_default():
    report = build_report("/proj", [_static()])
    assert report.recommendations == []


# ── ReportMetrics ─────────────────────────────

def test_metrics_counts_severity():
    findings = [
        _static(severity="HIGH"),
        _static(severity="HIGH"),
        _static(severity="MEDIUM"),
        _static(severity="LOW"),
        _static(severity="INFO"),
    ]
    report = build_report("/proj", findings)
    m = report.metrics
    assert m.high == 2
    assert m.medium == 1
    assert m.low == 1
    assert m.info == 1
    assert m.total_findings == 5


def test_metrics_static_vs_dynamic():
    findings = [_static(), _static(), _dynamic()]
    report = build_report("/proj", findings)
    assert report.metrics.static_count == 2
    assert report.metrics.dynamic_count == 1


def test_metrics_owasp_coverage():
    findings = [
        _static(owasp_id="API1"),
        _static(owasp_id="API2"),
        _static(owasp_id="API2"),  # duplicado
    ]
    report = build_report("/proj", findings)
    assert sorted(report.metrics.owasp_coverage) == ["API1", "API2"]


def test_metrics_recommendations_count():
    report = build_report("/proj", [_static()], [_rec(), _rec()])
    assert report.metrics.recommendations_count == 2


# ── Ordenamiento ──────────────────────────────

def test_findings_sorted_by_severity():
    findings = [
        _static(severity="INFO"),
        _static(severity="HIGH"),
        _static(severity="LOW"),
        _static(severity="MEDIUM"),
    ]
    report = build_report("/proj", findings)
    severities = [f.severity for f in report.findings]
    assert severities == ["HIGH", "MEDIUM", "LOW", "INFO"]
