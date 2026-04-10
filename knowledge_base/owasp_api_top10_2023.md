# OWASP API Security Top 10 — 2023

Source: https://owasp.org/API-Security/editions/2023/en/0x00-header/

---

## API1:2023 — Broken Object Level Authorization (BOLA)

### Description
APIs tend to expose endpoints that handle object identifiers, creating a wide attack surface of Object Level Access Control issues. Object level authorization checks should be considered in every function that accesses a data source using an ID from the user.

### Attack Scenario
An attacker authenticates as User A and then calls GET /api/orders/1235 — an order belonging to User B. The API returns User B's order because it only checks that the request is authenticated, not that the authenticated user owns the object.

### How to Prevent
- Implement a proper authorization mechanism that relies on user policies and hierarchy.
- Use the authorization mechanism to check if the logged-in user has access to perform the requested action on the record in every function that uses an input from the client to access a record in the database.
- Prefer the use of random and unpredictable values as GUIDs for records' IDs.
- Write tests to evaluate the authorization mechanism. Do not deploy vulnerable changes that break the tests.

### Django REST Framework Mitigation
In DRF, override `get_queryset()` to filter by the authenticated user:

```python
class OrderDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(owner=self.request.user)
```

Never use `queryset = Order.objects.all()` for user-owned resources without ownership filtering.

---

## API2:2023 — Broken Authentication

### Description
Authentication mechanisms are often implemented incorrectly, allowing attackers to compromise authentication tokens or to exploit implementation flaws to assume other user's identities temporarily or permanently. Compromising a system's ability to identify the client/user, compromises API security overall.

### Attack Scenario
An attacker calls GET /api/users/ without providing any authentication token. The API returns a list of all users including their email addresses and password hashes because no authentication is required.

### How to Prevent
- Make sure you know all the possible flows to authenticate to the API (mobile/web/deep links that implement one-click authentication/etc.).
- Ask yourself what the authentication mechanisms are. Make sure you understand what and how they are used.
- Don't reinvent the wheel in authentication, token generation, or password storage. Use the standards.
- Use JWT tokens — but ensure they are validated on every request.
- Implement proper token expiration.

### Django REST Framework Mitigation
Configure authentication globally in settings.py:

```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}
```

Each view should declare `permission_classes = [IsAuthenticated]` explicitly, or rely on the global default.

---

## API3:2023 — Broken Object Property Level Authorization

### Description
This category combines API3:2019 Excessive Data Exposure and API6:2019 Mass Assignment, focusing on the root cause: the lack of or improper authorization validation at the object property level. This leads to information exposure or manipulation by unauthorized parties.

### Attack Scenario — Excessive Data Exposure
A mobile application calls GET /api/users/1/ and the API returns the full user object including `password_hash`, `is_admin`, `ssn`, and other sensitive fields that the client application never displays.

### Attack Scenario — Mass Assignment
An attacker sends POST /api/users/ with `{"username": "hacker", "is_admin": true}`. The API accepts all fields without filtering and creates an admin account.

### How to Prevent
- Do not rely on the client to filter data — always return only the minimum required fields.
- Use `read_only=True` in serializers for sensitive or privileged fields.
- Explicitly whitelist properties that can be updated by the client.
- Use `extra_kwargs` to mark sensitive fields as read-only.

### Django REST Framework Mitigation

```python
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']
        # Never include 'password', 'is_admin', 'is_staff' without read_only
        extra_kwargs = {
            'password': {'write_only': True},
            'is_admin': {'read_only': True},
            'is_staff': {'read_only': True},
        }
```

---

## API4:2023 — Unrestricted Resource Consumption

### Description
Satisfying API requests requires resources such as network bandwidth, CPU, memory, and storage. Other resources such as emails/SMS/phone calls or biometrics validation are made available by service providers via API integrations. A successful attack can lead to Denial of Service (DoS) or increased operational costs.

### Attack Scenario
An attacker sends 1000 requests per second to GET /api/products/ without any rate limit in place. The server becomes overwhelmed and legitimate users cannot access the API.

### How to Prevent
- Implement rate limiting on all endpoints.
- Use throttling to restrict the number of times a user can call an API within a specific time frame.
- Limit payload sizes.
- Define and enforce a maximum size of data on all incoming parameters and payloads.

### Django REST Framework Mitigation

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

For stricter per-view throttling, use `throttle_classes` on individual views.

---

## API5:2023 — Broken Function Level Authorization

### Description
Complex access control policies with different hierarchies, groups, and roles, and an unclear separation between administrative and regular functions, tend to lead to authorization flaws. By exploiting these issues, attackers can gain access to other users' resources and/or administrative functions.

### Attack Scenario
An attacker calls GET /api/admin-panel/ without any authentication or admin role. The endpoint responds with 200 OK and returns all users' data including password hashes, because the view has no permission check.

### How to Prevent
- Enforce access control at the function level on every endpoint.
- Deny access by default to all sensitive/administrative endpoints.
- Use role-based access control (RBAC) and verify the role on every request.
- Make administrative APIs separate, or protect them with additional authentication layers.

### Django REST Framework Mitigation

```python
from rest_framework.permissions import IsAdminUser

class AdminPanelView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        # Only reachable by admin users
        ...
```

---

## API6:2023 — Unrestricted Access to Sensitive Business Flows

### Description
APIs vulnerable to this risk expose a business flow that can be abused by excessive use in an automated fashion. This does not necessarily involve bugs in the implementation.

### How to Prevent
- Identify the business flows that might harm the business if they are excessively used.
- Choose the right protection — for example, device fingerprinting, captcha, or extra authentication steps.

---

## API7:2023 — Server Side Request Forgery (SSRF)

### Description
Server-Side Request Forgery (SSRF) flaws can occur when an API is fetching a remote resource without validating the user-supplied URL.

### How to Prevent
- Validate and sanitize all client-supplied input URLs.
- Use an allowlist of permitted schemas, domains, and ports.
- Disable HTTP redirections in your HTTP client.

---

## API8:2023 — Security Misconfiguration

### Description
APIs and the systems supporting them typically contain complex configurations, intended to make the APIs more customizable. Software and DevOps engineers can miss these configurations, or don't follow security best practices when it comes to configuration, opening the door for different types of attacks.

### Attack Scenarios
- `DEBUG = True` in a Django production environment exposes full stack traces, environment variables, and internal settings to any user who triggers an error.
- Missing CORS configuration allows any origin to make cross-origin requests.
- Missing security headers (X-Content-Type-Options, HSTS, etc.).

### How to Prevent
- Disable DEBUG in production: `DEBUG = False`.
- Define ALLOWED_HOSTS explicitly.
- Set SECURE_SSL_REDIRECT, SESSION_COOKIE_SECURE, CSRF_COOKIE_SECURE.
- Regularly review and update configurations.

### Django Mitigation

```python
# settings.py (production)
DEBUG = False
ALLOWED_HOSTS = ['api.example.com']
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
```

---

## API9:2023 — Improper Inventory Management

### Description
APIs tend to expose more endpoints than traditional web applications, making proper and updated documentation highly important. Proper hosts and deployed API versions inventory also plays an important role to mitigate issues such as deprecated API versions and exposed debug endpoints.

### How to Prevent
- Document all API endpoints, including deprecated ones.
- Use API gateways to enforce version management.
- Retire old API versions promptly.

---

## API10:2023 — Unsafe Consumption of APIs

### Description
Developers tend to trust data received from third-party APIs more than user input. This is especially true for APIs offered by well-known companies. Because of that, developers tend to adopt weaker security standards, for instance, in regards to input validation and sanitization.

### How to Prevent
- Validate and sanitize all data received from integrated APIs.
- Evaluate the security controls of integrated APIs.
- Encrypt all communication with external APIs using TLS.
