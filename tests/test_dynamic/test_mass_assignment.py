import responses as resp_mock
import requests
import pytest
from auditor.dynamic_analyzer.probes.mass_assignment import MassAssignmentProbe

BASE = "http://testserver"


def _make_probe():
    return MassAssignmentProbe(base_url=BASE, session=requests.Session())


@resp_mock.activate
def test_mass_assignment_detected():
    resp_mock.add(
        resp_mock.POST, f"{BASE}/api/users/",
        json={"id": 99, "username": "hacker_probe", "is_admin": True, "is_staff": True},
        status=201,
    )

    findings = _make_probe().run()

    assert len(findings) == 1
    assert findings[0].rule_id == "API3-MASS-ASSIGN"
    assert findings[0].severity == "HIGH"
    assert "is_admin" in findings[0].evidence or "is_staff" in findings[0].evidence


@resp_mock.activate
def test_no_finding_when_fields_rejected():
    resp_mock.add(
        resp_mock.POST, f"{BASE}/api/users/",
        json={"id": 99, "username": "hacker_probe", "is_admin": False, "is_staff": False},
        status=201,
    )

    findings = _make_probe().run()

    assert findings == []


@resp_mock.activate
def test_no_finding_when_creation_fails():
    resp_mock.add(
        resp_mock.POST, f"{BASE}/api/users/",
        json={"error": "forbidden"}, status=403,
    )

    findings = _make_probe().run()

    assert findings == []


@resp_mock.activate
def test_partial_mass_assignment():
    """Solo is_admin=True es aceptado; is_staff=False."""
    resp_mock.add(
        resp_mock.POST, f"{BASE}/api/users/",
        json={"id": 99, "username": "hacker_probe", "is_admin": True, "is_staff": False},
        status=201,
    )

    findings = _make_probe().run()

    assert len(findings) == 1
    assert "is_admin" in findings[0].description or "is_admin" in findings[0].evidence
