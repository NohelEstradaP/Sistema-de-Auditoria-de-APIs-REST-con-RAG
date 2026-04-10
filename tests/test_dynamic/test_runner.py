import responses as resp_mock
import requests
import pytest
from auditor.dynamic_analyzer.runner import run_dynamic_analysis
from auditor.dynamic_analyzer.probes.unauthenticated_access import UnauthenticatedAccessProbe
from auditor.dynamic_analyzer.probes.bola import BOLAProbe

BASE = "http://testserver"


@resp_mock.activate
def test_runner_returns_sorted_by_owasp_id():
    # Mock para BOLA (API1)
    resp_mock.add(resp_mock.POST, f"{BASE}/api/auth/login/",
                  json={"access": "token"}, status=200)
    resp_mock.add(resp_mock.GET, f"{BASE}/api/orders/1/",
                  json={"id": 1}, status=200)
    # Mock para auth abierta (API2)
    resp_mock.add(resp_mock.GET, f"{BASE}/api/users/", json=[], status=200)
    resp_mock.add(resp_mock.GET, f"{BASE}/api/orders/", json=[], status=200)
    resp_mock.add(resp_mock.GET, f"{BASE}/api/admin-panel/", json={}, status=200)

    findings = run_dynamic_analysis(BASE, probes=[BOLAProbe, UnauthenticatedAccessProbe])

    assert len(findings) >= 2
    owasp_ids = [f.owasp_id for f in findings]
    assert owasp_ids == sorted(owasp_ids)


@resp_mock.activate
def test_runner_skips_failed_probes_gracefully():
    """El runner no debe lanzar excepción si una probe falla."""
    # Sin mocks: todas las requests van a fallar con ConnectionError
    findings = run_dynamic_analysis(BASE, probes=[UnauthenticatedAccessProbe])
    # No importa si hay hallazgos; lo importante es que no explota
    assert isinstance(findings, list)


@resp_mock.activate
def test_runner_empty_when_all_secure():
    resp_mock.add(resp_mock.POST, f"{BASE}/api/auth/login/",
                  json={"access": "token"}, status=200)
    resp_mock.add(resp_mock.GET, f"{BASE}/api/orders/1/", status=403)
    resp_mock.add(resp_mock.GET, f"{BASE}/api/users/", status=401)
    resp_mock.add(resp_mock.GET, f"{BASE}/api/orders/", status=401)
    resp_mock.add(resp_mock.GET, f"{BASE}/api/admin-panel/", status=401)

    findings = run_dynamic_analysis(BASE, probes=[BOLAProbe, UnauthenticatedAccessProbe])

    assert findings == []
