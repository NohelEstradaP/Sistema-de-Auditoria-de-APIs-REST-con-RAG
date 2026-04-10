import responses as resp_mock
import requests
import pytest
from auditor.dynamic_analyzer.probes.function_level_authz import FunctionLevelAuthzProbe

BASE = "http://testserver"


def _make_probe():
    return FunctionLevelAuthzProbe(base_url=BASE, session=requests.Session())


@resp_mock.activate
def test_admin_endpoint_exposed():
    resp_mock.add(
        resp_mock.GET, f"{BASE}/api/admin-panel/",
        json={"admin_data": [{"id": 1, "username": "admin"}]}, status=200,
    )

    findings = _make_probe().run()

    assert len(findings) == 1
    assert findings[0].rule_id == "API5-FUNC-AUTHZ"
    assert findings[0].severity == "HIGH"
    assert findings[0].owasp_id == "API5"


@resp_mock.activate
def test_no_finding_when_403():
    resp_mock.add(resp_mock.GET, f"{BASE}/api/admin-panel/", status=403)

    findings = _make_probe().run()

    assert findings == []


@resp_mock.activate
def test_no_finding_when_401():
    resp_mock.add(resp_mock.GET, f"{BASE}/api/admin-panel/", status=401)

    findings = _make_probe().run()

    assert findings == []


@resp_mock.activate
def test_evidence_contains_body_snippet():
    resp_mock.add(
        resp_mock.GET, f"{BASE}/api/admin-panel/",
        json={"admin_data": [{"username": "admin", "password": "hash"}]}, status=200,
    )

    findings = _make_probe().run()

    assert "200" in findings[0].evidence
    assert "admin" in findings[0].evidence
