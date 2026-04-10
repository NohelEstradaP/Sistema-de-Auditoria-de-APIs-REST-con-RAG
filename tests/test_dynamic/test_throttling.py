import responses as resp_mock
import requests
import pytest
from auditor.dynamic_analyzer.probes.throttling import ThrottlingProbe, _REQUESTS_TO_SEND

BASE = "http://testserver"


def _make_probe():
    return ThrottlingProbe(base_url=BASE, session=requests.Session())


@resp_mock.activate
def test_no_throttling_detected():
    for _ in range(_REQUESTS_TO_SEND):
        resp_mock.add(resp_mock.GET, f"{BASE}/api/products/", json=[], status=200)

    findings = _make_probe().run()

    assert len(findings) == 1
    assert findings[0].rule_id == "API4-NO-THROTTLE"
    assert findings[0].severity == "MEDIUM"


@resp_mock.activate
def test_no_finding_when_429_received():
    # Primera respuesta normal, segunda activa el rate limit
    resp_mock.add(resp_mock.GET, f"{BASE}/api/products/", json=[], status=200)
    resp_mock.add(resp_mock.GET, f"{BASE}/api/products/", status=429)

    findings = _make_probe().run()

    assert findings == []


@resp_mock.activate
def test_evidence_mentions_request_count():
    for _ in range(_REQUESTS_TO_SEND):
        resp_mock.add(resp_mock.GET, f"{BASE}/api/products/", json=[], status=200)

    findings = _make_probe().run()

    assert str(_REQUESTS_TO_SEND) in findings[0].evidence
