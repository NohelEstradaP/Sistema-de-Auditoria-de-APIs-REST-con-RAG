from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Order, Product

User = get_user_model()


class BOLATestCase(APITestCase):
    """API1: Broken Object Level Authorization — un usuario autenticado accede a
    una orden de otro usuario porque OrderDetailView no filtra por owner."""

    def setUp(self):
        self.alice = User.objects.create_user(username="alice", password="alice123")
        self.bob = User.objects.create_user(username="bob", password="bob123")
        product = Product.objects.create(name="Laptop", price="999.99", stock=10)
        self.alice_order = Order.objects.create(owner=self.alice, product=product, quantity=1)

    def _login(self, username, password):
        response = self.client.post("/api/auth/login/", {"username": username, "password": password})
        return response.data["access"]

    def test_bob_can_read_alice_order(self):
        token = self._login("bob", "bob123")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = self.client.get(f"/api/orders/{self.alice_order.id}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["owner"], self.alice.id)


class BrokenAuthenticationTestCase(APITestCase):
    """API2: Broken Authentication — UserListView no declara permission_classes,
    así que el permiso efectivo es AllowAny y no exige ningún token."""

    def setUp(self):
        User.objects.create_user(username="alice", password="alice123")

    def test_user_list_accessible_without_token(self):
        response = self.client.get("/api/users/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)


class BrokenObjectPropertyAuthTestCase(APITestCase):
    """API3: Broken Object Property Level Authorization — UserSerializer expone
    password/is_admin sin read_only, y OrderSerializer permite mass assignment
    del campo owner."""

    def setUp(self):
        self.alice = User.objects.create_user(username="alice", password="alice123")
        self.bob = User.objects.create_user(username="bob", password="bob123")
        self.product = Product.objects.create(name="Mouse", price="29.99", stock=50)

    def test_password_and_is_admin_exposed(self):
        response = self.client.get(f"/api/users/{self.alice.id}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("password", response.data)
        self.assertIn("is_admin", response.data)

    def test_mass_assignment_on_order_owner(self):
        token_response = self.client.post("/api/auth/login/", {"username": "bob", "password": "bob123"})
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token_response.data['access']}")

        response = self.client.post("/api/orders/", {
            "owner": self.alice.id,
            "product": self.product.id,
            "quantity": 1,
        })

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["owner"], self.alice.id)


class UnrestrictedResourceConsumptionTestCase(APITestCase):
    """API4: Unrestricted Resource Consumption — no hay DEFAULT_THROTTLE_CLASSES
    configurado, así que ninguna cantidad de peticiones consecutivas es limitada."""

    def setUp(self):
        Product.objects.create(name="Teclado", price="59.99", stock=30)

    def test_no_rate_limiting_after_20_requests(self):
        statuses = [self.client.get("/api/products/").status_code for _ in range(20)]

        self.assertNotIn(status.HTTP_429_TOO_MANY_REQUESTS, statuses)
        self.assertTrue(all(s == status.HTTP_200_OK for s in statuses))


class BrokenFunctionLevelAuthorizationTestCase(APITestCase):
    """API5: Broken Function Level Authorization — AdminPanelView no verifica
    autenticación ni rol de administrador antes de exponer datos de admin."""

    def setUp(self):
        User.objects.create_user(username="admin", password="admin123", is_admin=True)

    def test_admin_panel_accessible_without_auth(self):
        response = self.client.get("/api/admin-panel/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("admin_data", response.data)
