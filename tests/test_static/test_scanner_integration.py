"""
Test de integración: el scanner detecta todas las vulnerabilidades
conocidas en la API vulnerable incluida en el proyecto.
"""
import pytest
from auditor.static_analyzer import scan_project

VULNERABLE_API_PATH = "vulnerable_api"


@pytest.fixture(scope="module")
def findings():
    return scan_project(VULNERABLE_API_PATH)


def test_debug_enabled_found(findings):
    assert any(f.rule_id == "API8-DEBUG-ENABLED" for f in findings)


def test_missing_throttling_found(findings):
    assert any(f.rule_id == "API4-NO-THROTTLING" for f in findings)


def test_missing_jwt_config_found(findings):
    assert any(f.rule_id == "API2-NO-JWT-CONFIG" for f in findings)


def test_sensitive_fields_found(findings):
    sensitive = [f for f in findings if f.rule_id == "API3-SENSITIVE-FIELD"]
    detected_fields = {t for f in sensitive for t in [f.title]}
    assert any("password" in t for t in detected_fields)
    assert any("is_admin" in t for t in detected_fields)


def test_missing_permissions_found(findings):
    no_perm = [f for f in findings if f.rule_id == "API2-NO-PERMISSION"]
    view_names = {f.title for f in no_perm}
    assert any("UserListView" in t for t in view_names)
    assert any("AdminPanelView" in t for t in view_names)


def test_bola_urls_found(findings):
    bola = [f for f in findings if f.rule_id == "API1-BOLA-URL"]
    patterns = {f.title for f in bola}
    assert any("orders/<int:pk>/" in t for t in patterns)


def test_total_high_severity(findings):
    high = [f for f in findings if f.severity == "HIGH"]
    assert len(high) >= 10  # la API tiene muchas vulnerabilidades HIGH conocidas
