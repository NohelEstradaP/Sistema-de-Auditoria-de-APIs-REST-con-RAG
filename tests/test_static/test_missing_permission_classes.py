import ast
import pytest
from auditor.static_analyzer.rules.missing_permission_classes import MissingPermissionClassesRule

rule = MissingPermissionClassesRule()


def _check(source: str):
    tree = ast.parse(source)
    return rule.check(tree, "views.py", source)


def test_missing_permission_detected():
    source = """
from rest_framework import generics

class OrderListView(generics.ListCreateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
"""
    findings = _check(source)
    assert len(findings) == 1
    assert findings[0].rule_id == "API2-NO-PERMISSION"
    assert "OrderListView" in findings[0].title
    assert findings[0].severity == "HIGH"


def test_permission_classes_present_not_flagged():
    source = """
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

class OrderListView(generics.ListCreateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
"""
    findings = _check(source)
    assert findings == []


def test_apiview_without_permission_detected():
    source = """
from rest_framework.views import APIView

class AdminPanelView(APIView):
    def get(self, request):
        return Response({})
"""
    findings = _check(source)
    assert len(findings) == 1
    assert "AdminPanelView" in findings[0].title


def test_non_view_class_not_flagged():
    source = """
class MyForm:
    pass
"""
    findings = _check(source)
    assert findings == []


def test_multiple_views_each_flagged():
    source = """
from rest_framework import generics

class ViewA(generics.ListAPIView):
    pass

class ViewB(generics.CreateAPIView):
    pass
"""
    findings = _check(source)
    assert len(findings) == 2
