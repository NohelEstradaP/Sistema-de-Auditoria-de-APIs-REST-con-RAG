import responses as resp_mock
import requests
import pytest
from auditor.dynamic_analyzer.probes.unauthenticated_access import UnauthenticatedAccessProbe

BASE = "http://testserver"


def _make_probe():
    return UnauthenticatedAccessProbe(base_url=BASE, session=requests.Session())


@resp_mock.activate
def test_detects_open_endpoint():
    resp_mock.add(resp_mock.GET, f"{BASE}/api/users/", json=[], status=200)
    resp_mock.add(resp_mock.GET, f"{BASE}/api/orders/", json=[], status=200)
    resp_mock.add(resp_mock.GET, f"{BASE}/api/admin-panel/", json={}, status=200)

    findings = _make_probe().run()

    assert len(findings) == 3
    rule_ids = {f.rule_id for f in findings}
    assert rule_ids == {"API2-UNAUTH"}
    assert all(f.severity == "HIGH" for f in findings)


@resp_mock.activate
def test_no_finding_when_401():
    resp_mock.add(resp_mock.GET, f"{BASE}/api/users/", status=401)
    resp_mock.add(resp_mock.GET, f"{BASE}/api/orders/", status=401)
    resp_mock.add(resp_mock.GET, f"{BASE}/api/admin-panel/", status=401)

    findings = _make_probe().run()

    assert findings == []


@resp_mock.activate
def test_partial_exposure():
    resp_mock.add(resp_mock.GET, f"{BASE}/api/users/", status=401)
    resp_mock.add(resp_mock.GET, f"{BASE}/api/orders/", json=[], status=200)
    resp_mock.add(resp_mock.GET, f"{BASE}/api/admin-panel/", status=403)

    findings = _make_probe().run()

    assert len(findings) == 1
    assert findings[0].endpoint == "/api/orders/"


@resp_mock.activate
def test_finding_has_evidence_with_status_code():
    resp_mock.add(resp_mock.GET, f"{BASE}/api/users/", json={"data": "secret"}, status=200)
    resp_mock.add(resp_mock.GET, f"{BASE}/api/orders/", status=401)
    resp_mock.add(resp_mock.GET, f"{BASE}/api/admin-panel/", status=401)

    findings = _make_probe().run()

    assert len(findings) == 1
    assert "200" in findings[0].evidence
