import pytest
from auditor.report.builder import build_report
from auditor.report.html_template import render_html
from auditor.static_analyzer.findings import Finding
from auditor.dynamic_analyzer.findings import DynamicFinding
from auditor.rag.generator import LLMRecommendation


def _static_finding():
    return Finding(
        rule_id="API2-NO-PERMISSION", owasp_id="API2",
        title="Vista sin permission_classes",
        severity="HIGH", file="views.py", line=12,
        description="APIView sin autenticación.",
        evidence="class OrderView(APIView):",
    )


def _dynamic_finding():
    return DynamicFinding(
        rule_id="API1-BOLA", owasp_id="API1",
        title="BOLA detectado",
        severity="HIGH", endpoint="/api/orders/1/", method="GET",
        description="Bob accede a orden de alice.",
        evidence="HTTP 200 con token de bob",
    )


def _rec():
    return LLMRecommendation(
        rule_id="API1-BOLA",
        recommendation="Filter queryset by owner.\n\nSources: owasp.md",
        sources=["owasp_api_top10_2023.md — API1"],
        model="mistral",
    )


def test_render_returns_string():
    report = build_report("/proj", [_static_finding()])
    html = render_html(report)
    assert isinstance(html, str)
    assert len(html) > 100


def test_render_contains_doctype():
    report = build_report("/proj", [_static_finding()])
    html = render_html(report)
    assert "<!DOCTYPE html>" in html


def test_render_contains_finding_title():
    report = build_report("/proj", [_static_finding()])
    html = render_html(report)
    assert "Vista sin permission_classes" in html


def test_render_contains_severity_badge():
    report = build_report("/proj", [_static_finding()])
    html = render_html(report)
    assert "HIGH" in html


def test_render_shows_static_file_location():
    report = build_report("/proj", [_static_finding()])
    html = render_html(report)
    assert "views.py" in html
    assert "12" in html


def test_render_shows_dynamic_endpoint():
    report = build_report("/proj", [_dynamic_finding()])
    html = render_html(report)
    assert "/api/orders/1/" in html
    assert "GET" in html


def test_render_shows_recommendation():
    report = build_report("/proj", [_dynamic_finding()], [_rec()])
    html = render_html(report)
    assert "Filter queryset by owner" in html
    assert "owasp_api_top10_2023.md" in html


def test_render_no_findings_message():
    report = build_report("/proj", [])
    html = render_html(report)
    assert "No se encontraron hallazgos" in html


def test_render_owasp_coverage_chips():
    report = build_report("/proj", [_static_finding(), _dynamic_finding()])
    html = render_html(report)
    assert "API1" in html
    assert "API2" in html


def test_render_escapes_special_chars():
    f = Finding(
        rule_id="API2-TEST", owasp_id="API2",
        title='XSS <script>alert("x")</script>',
        severity="HIGH", file="views.py", line=1,
        description="Desc", evidence="evidence",
    )
    report = build_report("/proj", [f])
    html = render_html(report)
    assert "<script>" not in html
    assert "&lt;script&gt;" in html


def test_render_summary_cards_present():
    report = build_report("/proj", [_static_finding()])
    html = render_html(report)
    assert "Total" in html
    assert "High" in html
    assert "Medium" in html
