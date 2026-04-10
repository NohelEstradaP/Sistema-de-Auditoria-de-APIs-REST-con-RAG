# Django REST Framework — Security Guide

Source: Django REST Framework official documentation and Django security advisories.

---

## Authentication in DRF

DRF supports multiple authentication schemes. The scheme is selected per-request based on the order defined in `DEFAULT_AUTHENTICATION_CLASSES`.

### JWT Authentication (recommended)

Use `djangorestframework-simplejwt` for token-based authentication:

```python
# settings.py
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
}

# Configure token lifetimes
from datetime import timedelta
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'AUTH_HEADER_TYPES': ('Bearer',),
}
```

If `SIMPLE_JWT` is absent from settings, JWT token lifetimes use insecure defaults (very long or undefined expiry).

### Session Authentication

Only appropriate for browser-based clients with CSRF protection. Do not use for public APIs.

---

## Permission Classes

Permissions determine whether a request should be granted or denied. They are checked at the start of the view, before any other code runs.

### Global Default

```python
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}
```

### Per-View Override

```python
class PublicProductListView(generics.ListAPIView):
    permission_classes = [AllowAny]  # Explicitly public
    serializer_class = ProductSerializer
    queryset = Product.objects.all()
```

### Available Permission Classes

| Class | Description |
|-------|-------------|
| `IsAuthenticated` | Requires the user to be authenticated |
| `IsAdminUser` | Requires `user.is_staff == True` |
| `IsAuthenticatedOrReadOnly` | Authenticated for write, read-only for anonymous |
| `AllowAny` | No restriction (use explicitly, never by omission) |
| `DjangoModelPermissions` | Tied to Django's model-level permissions |
| `DjangoObjectPermissions` | Object-level permissions (requires custom backend) |

**Critical rule:** A view without `permission_classes` inherits the global default. If no global default is set, DRF defaults to `AllowAny` — which means the endpoint is public. Always set a global default and override explicitly when needed.

---

## Serializer Security

Serializers control what data enters and leaves the system. Insecure serializers are the primary cause of mass assignment and data exposure vulnerabilities.

### read_only Fields

Fields marked `read_only=True` are included in serialized output but are ignored on input (create/update). Use this for any field the client should not control:

```python
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'is_admin', 'created_at']
        extra_kwargs = {
            'is_admin': {'read_only': True},
            'is_staff': {'read_only': True},
            'created_at': {'read_only': True},
        }
```

### write_only Fields

Fields marked `write_only=True` are accepted on input but never included in the response. Use for passwords:

```python
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'password']
        extra_kwargs = {
            'password': {'write_only': True, 'min_length': 8},
        }
```

### Explicit Field Listing

Avoid `fields = '__all__'` for user-facing serializers. Always explicitly list fields to prevent accidental exposure of new model fields:

```python
# BAD — any new model field is automatically exposed
class Meta:
    fields = '__all__'

# GOOD — explicit control
class Meta:
    fields = ['id', 'username', 'email']
```

---

## Throttling (Rate Limiting)

DRF provides built-in throttling to protect against brute force and DoS attacks.

### Global Configuration

```python
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/day',
        'user': '1000/day',
    },
}
```

### Per-View Throttling

```python
class LoginView(APIView):
    throttle_classes = [AnonRateThrottle]
    throttle_scope = 'login'
```

If `DEFAULT_THROTTLE_CLASSES` is not configured, there is no rate limiting by default.

---

## Object-Level Authorization (Ownership Checks)

DRF does not automatically enforce that a user can only access their own objects. This must be implemented manually by overriding `get_queryset()` or using `get_object()` with a manual check.

### Correct Pattern — Filter by Owner

```python
class OrderListView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializer

    def get_queryset(self):
        # Only returns objects belonging to the authenticated user
        return Order.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        # Forces owner to be the authenticated user regardless of input
        serializer.save(owner=self.request.user)
```

### Vulnerable Pattern (BOLA)

```python
# WRONG — returns all orders regardless of owner
class OrderDetailView(generics.RetrieveAPIView):
    queryset = Order.objects.all()  # No ownership filter
    serializer_class = OrderSerializer
```

---

## QuerySet Security

### Use select_related and prefetch_related Carefully

Avoid exposing related objects that the user does not own.

### Prevent Information Leakage via 404 vs 403

When a user requests an object they don't own, return 404 (not found) rather than 403 (forbidden) to avoid confirming the object's existence:

```python
def get_object(self):
    try:
        obj = Order.objects.get(pk=self.kwargs['pk'], owner=self.request.user)
    except Order.DoesNotExist:
        raise Http404  # Don't reveal if object exists for other users
    self.check_object_permissions(self.request, obj)
    return obj
```

---

## Django Settings Security

### Critical Settings for Production

```python
DEBUG = False                          # Never True in production
SECRET_KEY = os.environ['SECRET_KEY'] # Never hardcoded
ALLOWED_HOSTS = ['api.example.com']   # Explicit list, never ['*']

# HTTPS
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True

# Content security
X_FRAME_OPTIONS = 'DENY'
SECURE_CONTENT_TYPE_NOSNIFF = True
```

### DEBUG = True Risks

When `DEBUG = True`:
- Full stack traces with local variables are shown to any user who triggers an error.
- The Django debug toolbar (if installed) may expose SQL queries.
- ALLOWED_HOSTS validation is relaxed.
- Internal URLs and settings may be revealed.

---

## Common DRF CVEs and Security Advisories

### CVE-2020-25626 — XSS in Browsable API
DRF versions prior to 3.12.0 were vulnerable to XSS via the browsable API when `format_suffix_patterns` was used. Fixed by upgrading to DRF 3.12.0+.

### Django CVE-2021-45116 — Potential Information Disclosure
Django's `dictsort` template filter could expose sensitive information when used with untrusted data. Always escape template output.

### Django CVE-2022-28347 — SQL Injection via QuerySet.explain()
Versions before Django 3.2.13 and 4.0.4 were vulnerable to SQL injection in `QuerySet.explain()`. Fixed by upgrading Django.

### Django CVE-2023-31047 — File Upload Bypass
Insufficient validation in Django's file upload allowed bypass of extension validation. Use `FileExtensionValidator` and validate MIME types server-side.

### General Recommendation
Always run the latest stable version of Django and DRF. Subscribe to Django security announcements at: https://www.djangoproject.com/weblog/
