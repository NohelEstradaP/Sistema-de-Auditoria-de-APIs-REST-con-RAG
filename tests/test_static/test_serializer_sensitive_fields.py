import ast
import pytest
from auditor.static_analyzer.rules.serializer_sensitive_fields import SerializerSensitiveFieldsRule

rule = SerializerSensitiveFieldsRule()


def _check(source: str):
    tree = ast.parse(source)
    return rule.check(tree, "serializers.py", source)


def test_password_without_read_only_detected():
    source = """
from rest_framework import serializers

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'password']
"""
    findings = _check(source)
    rule_ids = [f.rule_id for f in findings]
    assert "API3-SENSITIVE-FIELD" in rule_ids
    titles = [f.title for f in findings]
    assert any("password" in t for t in titles)


def test_is_admin_without_read_only_detected():
    source = """
from rest_framework import serializers

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'is_admin', 'is_staff']
"""
    findings = _check(source)
    sensitive_findings = [f for f in findings if f.rule_id == "API3-SENSITIVE-FIELD"]
    detected = {f.title for f in sensitive_findings}
    assert any("is_admin" in t for t in detected)
    assert any("is_staff" in t for t in detected)


def test_explicit_read_only_field_not_flagged():
    source = """
from rest_framework import serializers

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'password']
"""
    findings = _check(source)
    sensitive = [f for f in findings if f.rule_id == "API3-SENSITIVE-FIELD"]
    assert sensitive == []


def test_extra_kwargs_read_only_not_flagged():
    source = """
from rest_framework import serializers

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'password']
        extra_kwargs = {'password': {'read_only': True}}
"""
    findings = _check(source)
    sensitive = [f for f in findings if f.rule_id == "API3-SENSITIVE-FIELD"]
    assert sensitive == []


def test_fields_all_flagged():
    source = """
from rest_framework import serializers

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'
"""
    findings = _check(source)
    assert any(f.rule_id == "API3-FIELDS-ALL" for f in findings)


def test_non_sensitive_fields_not_flagged():
    source = """
from rest_framework import serializers

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'price']
"""
    findings = _check(source)
    sensitive = [f for f in findings if f.rule_id == "API3-SENSITIVE-FIELD"]
    assert sensitive == []
