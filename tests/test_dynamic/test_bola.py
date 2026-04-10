import responses as resp_mock
import requests
import pytest
from auditor.dynamic_analyzer.probes.bola import BOLAProbe

BASE = "http://testserver"


def _make_probe():
    return BOLAProbe(base_url=BASE, session=requests.Session())


@resp_mock.activate
def test_bola_detected():
    resp_mock.add(
        resp_mock.POST, f"{BASE}/api/auth/login/",
        json={"access": "token-bob"}, status=200,
    )
    resp_mock.add(
        resp_mock.GET, f"{BASE}/api/orders/1/",
        json={"id": 1, "owner": 1, "product": 1}, status=200,
    )

    findings = _make_probe().run()

    assert len(findings) == 1
    assert findings[0].rule_id == "API1-BOLA"
    assert findings[0].severity == "HIGH"
    assert findings[0].owasp_id == "API1"


@resp_mock.activate
def test_no_bola_when_403():
    resp_mock.add(
        resp_mock.POST, f"{BASE}/api/auth/login/",
        json={"access": "token-bob"}, status=200,
    )
    resp_mock.add(
        resp_mock.GET, f"{BASE}/api/orders/1/",
        status=403,
    )

    findings = _make_probe().run()

    assert findings == []


@resp_mock.activate
def test_no_finding_when_login_fails():
    resp_mock.add(
        resp_mock.POST, f"{BASE}/api/auth/login/",
        json={"detail": "No active account"}, status=401,
    )

    findings = _make_probe().run()

    assert findings == []


@resp_mock.activate
def test_evidence_contains_status_and_body():
    resp_mock.add(
        resp_mock.POST, f"{BASE}/api/auth/login/",
        json={"access": "token-bob"}, status=200,
    )
    resp_mock.add(
        resp_mock.GET, f"{BASE}/api/orders/1/",
        json={"id": 1, "owner": 1}, status=200,
    )

    findings = _make_probe().run()

    assert "200" in findings[0].evidence
    assert "bob" in findings[0].description
