import ast
import pytest
from auditor.static_analyzer.rules.bola_url_params import BolaUrlParamsRule

rule = BolaUrlParamsRule()


def _check(source: str):
    tree = ast.parse(source)
    return rule.check(tree, "urls.py", source)


def test_int_pk_detected():
    source = """
from django.urls import path
urlpatterns = [
    path('orders/<int:pk>/', views.OrderDetailView.as_view()),
]
"""
    findings = _check(source)
    assert len(findings) == 1
    assert findings[0].rule_id == "API1-BOLA-URL"
    assert findings[0].severity == "HIGH"
    assert "orders/<int:pk>/" in findings[0].title


def test_multiple_int_params_each_flagged():
    source = """
from django.urls import path
urlpatterns = [
    path('users/<int:pk>/', views.UserDetailView.as_view()),
    path('orders/<int:pk>/', views.OrderDetailView.as_view()),
]
"""
    findings = _check(source)
    assert len(findings) == 2


def test_string_param_not_flagged():
    source = """
from django.urls import path
urlpatterns = [
    path('items/<str:slug>/', views.ItemView.as_view()),
]
"""
    findings = _check(source)
    assert findings == []


def test_no_params_not_flagged():
    source = """
from django.urls import path
urlpatterns = [
    path('products/', views.ProductListView.as_view()),
]
"""
    findings = _check(source)
    assert findings == []


def test_int_id_param_detected():
    source = """
from django.urls import path
urlpatterns = [
    path('users/<int:user_id>/profile/', views.ProfileView.as_view()),
]
"""
    findings = _check(source)
    assert len(findings) == 1
