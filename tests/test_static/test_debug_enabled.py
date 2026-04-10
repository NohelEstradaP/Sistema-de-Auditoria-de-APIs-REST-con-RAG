import ast
import pytest
from auditor.static_analyzer.rules.debug_enabled import DebugEnabledRule

rule = DebugEnabledRule()


def _check(source: str):
    tree = ast.parse(source)
    return rule.check(tree, "settings.py", source)


def test_debug_true_detected():
    source = "DEBUG = True"
    findings = _check(source)
    assert len(findings) == 1
    assert findings[0].rule_id == "API8-DEBUG-ENABLED"
    assert findings[0].severity == "HIGH"


def test_debug_false_not_flagged():
    findings = _check("DEBUG = False")
    assert findings == []


def test_debug_variable_not_flagged():
    # DEBUG = alguna_variable  — no es un literal True
    findings = _check("DEBUG = os.environ.get('DEBUG', False)")
    assert findings == []


def test_other_assignment_not_flagged():
    findings = _check("ALLOWED_HOSTS = ['*']")
    assert findings == []
