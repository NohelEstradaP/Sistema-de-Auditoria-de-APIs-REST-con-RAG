import pytest
from pathlib import Path
from auditor.report.builder import build_report
from auditor.report.exporter import export_html, export_pdf, export
from auditor.static_analyzer.findings import Finding


def _finding():
    return Finding(
        rule_id="API2-NO-PERMISSION", owasp_id="API2",
        title="No permissions", severity="HIGH",
        file="views.py", line=5,
        description="Missing permission_classes.", evidence="class V(APIView):",
    )


def _report(tmp_path):
    return build_report(str(tmp_path), [_finding()])


# ── export_html ───────────────────────────────

def test_export_html_creates_file(tmp_path):
    report = _report(tmp_path)
    out = tmp_path / "report.html"
    result = export_html(report, str(out))
    assert Path(result).exists()


def test_export_html_returns_absolute_path(tmp_path):
    report = _report(tmp_path)
    out = tmp_path / "report.html"
    result = export_html(report, str(out))
    assert Path(result).is_absolute()


def test_export_html_content_is_valid(tmp_path):
    report = _report(tmp_path)
    out = tmp_path / "report.html"
    export_html(report, str(out))
    content = Path(out).read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in content
    assert "No permissions" in content


def test_export_html_creates_parent_dirs(tmp_path):
    report = _report(tmp_path)
    out = tmp_path / "subdir" / "deep" / "report.html"
    export_html(report, str(out))
    assert out.exists()


# ── export_pdf ────────────────────────────────

def test_export_pdf_creates_file(tmp_path):
    report = _report(tmp_path)
    out = tmp_path / "report.pdf"
    result = export_pdf(report, str(out))
    assert Path(result).exists()


def test_export_pdf_is_not_empty(tmp_path):
    report = _report(tmp_path)
    out = tmp_path / "report.pdf"
    export_pdf(report, str(out))
    assert out.stat().st_size > 1000  # PDF real, no vacío


def test_export_pdf_starts_with_pdf_magic(tmp_path):
    report = _report(tmp_path)
    out = tmp_path / "report.pdf"
    export_pdf(report, str(out))
    magic = out.read_bytes()[:4]
    assert magic == b"%PDF"


# ── export (router) ───────────────────────────

def test_export_routes_html(tmp_path):
    report = _report(tmp_path)
    out = tmp_path / "report.html"
    export(report, str(out))
    assert out.exists()
    assert "<!DOCTYPE html>" in out.read_text(encoding="utf-8")


def test_export_routes_pdf(tmp_path):
    report = _report(tmp_path)
    out = tmp_path / "report.pdf"
    export(report, str(out))
    assert out.read_bytes()[:4] == b"%PDF"


def test_export_raises_on_unknown_extension(tmp_path):
    report = _report(tmp_path)
    with pytest.raises(ValueError, match="Extensión no soportada"):
        export(report, str(tmp_path / "report.docx"))
