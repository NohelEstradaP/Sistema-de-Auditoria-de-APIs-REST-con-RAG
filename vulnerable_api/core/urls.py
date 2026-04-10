from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views

urlpatterns = [
    # Auth
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Users — VULNERABILIDAD API2/API3: sin autenticación requerida
    path('users/', views.UserListView.as_view(), name='user-list'),
    path('users/<int:pk>/', views.UserDetailView.as_view(), name='user-detail'),

    # Products
    path('products/', views.ProductListView.as_view(), name='product-list'),
    path('products/<int:pk>/', views.ProductDetailView.as_view(), name='product-detail'),

    # Orders — VULNERABILIDAD API1: parámetro numérico sin verificación de ownership
    path('orders/', views.OrderListView.as_view(), name='order-list'),
    path('orders/<int:pk>/', views.OrderDetailView.as_view(), name='order-detail'),

    # Admin — VULNERABILIDAD API5: accesible sin verificación de rol
    path('admin-panel/', views.AdminPanelView.as_view(), name='admin-panel'),
    path('admin-panel/<int:pk>/', views.AdminPanelView.as_view(), name='admin-panel-delete'),
]
