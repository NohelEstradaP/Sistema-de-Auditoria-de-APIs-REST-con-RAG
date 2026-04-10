import ast
import pytest
from auditor.static_analyzer.rules.missing_throttling import MissingThrottlingRule

rule = MissingThrottlingRule()


def _check(source: str):
    tree = ast.parse(source)
    return rule.check(tree, "settings.py", source)


def test_missing_throttle_detected():
    source = """
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
}
"""
    findings = _check(source)
    assert len(findings) == 1
    assert findings[0].rule_id == "API4-NO-THROTTLING"
    assert findings[0].severity == "MEDIUM"


def test_throttle_present_not_flagged():
    source = """
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': ['rest_framework.throttling.AnonRateThrottle'],
    'DEFAULT_THROTTLE_RATES': {'anon': '100/day'},
}
"""
    findings = _check(source)
    assert findings == []


def test_no_rest_framework_not_flagged():
    # Si no hay REST_FRAMEWORK, no reportamos nada
    findings = _check("DEBUG = True")
    assert findings == []
