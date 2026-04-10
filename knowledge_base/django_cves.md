# Django Security Advisories and CVEs

Selected advisories relevant to REST API security in Django projects.

---

## CVE-2023-41164 — Potential Denial of Service in django.utils.encoding.uri_to_iri()

- **Severity:** Moderate
- **Affected versions:** Django < 4.2.5, < 4.1.9, < 3.2.21
- **Description:** The `uri_to_iri()` function was subject to a potential denial of service attack via a crafted URI. An attacker could craft a URI with certain characters that would cause excessive CPU usage.
- **Fix:** Upgrade to Django 4.2.5, 4.1.9, or 3.2.21+.
- **API relevance:** Affects any API endpoint that processes user-supplied URLs or URIs.

---

## CVE-2023-36053 — Potential ReDoS via EmailValidator and URLValidator

- **Severity:** Moderate
- **Affected versions:** Django < 4.2.3, < 4.1.9, < 3.2.20
- **Description:** `EmailValidator` and `URLValidator` were subject to potential ReDoS (Regular Expression Denial of Service) attacks via specially crafted email addresses or URLs.
- **Fix:** Upgrade to Django 4.2.3+.
- **API relevance:** Any API endpoint that validates email or URL fields with Django validators is at risk. DRF serializers using `EmailField` or `URLField` call these validators automatically.

---

## CVE-2022-28347 — SQL Injection via QuerySet.explain() on Oracle

- **Severity:** Critical (on Oracle databases)
- **Affected versions:** Django < 3.2.13, < 4.0.4
- **Description:** `QuerySet.explain()` did not properly sanitize the `format` parameter on Oracle databases, allowing SQL injection.
- **Fix:** Upgrade to Django 3.2.13 or 4.0.4+.
- **API relevance:** Affects APIs that expose query explanation functionality or use `explain()` with user-controlled input.

---

## CVE-2022-28346 — SQL Injection via QuerySet.annotate(), aggregate(), extra()

- **Severity:** Critical
- **Affected versions:** Django < 3.2.13, < 4.0.4
- **Description:** An issue in column aliases allowed SQL injection in `QuerySet.annotate()`, `aggregate()`, and `extra()` calls on some database backends.
- **Fix:** Upgrade to Django 3.2.13 or 4.0.4+.
- **API relevance:** Any DRF view that uses `annotate()` or `extra()` with user-supplied values is vulnerable.

---

## CVE-2021-45116 — Potential Information Disclosure in dictsort

- **Severity:** Low
- **Affected versions:** Django < 3.2.11, < 4.0.1
- **Description:** `dictsort` template filter could expose sensitive data when used with untrusted input via attribute access.
- **Fix:** Upgrade to Django 3.2.11+.
- **API relevance:** Primarily affects Django templates, not pure API backends.

---

## CVE-2021-35042 — SQL Injection via QuerySet.order_by()

- **Severity:** Critical
- **Affected versions:** Django < 3.1.13, < 3.2.5
- **Description:** Unsanitized column names were allowed in `QuerySet.order_by()` when using `union()`, `intersection()`, or `difference()`, enabling SQL injection.
- **Fix:** Upgrade to Django 3.1.13 or 3.2.5+.
- **API relevance:** Any API endpoint accepting a `?ordering=` query parameter that passes it directly to `order_by()` is critically vulnerable. DRF's `OrderingFilter` does NOT pass user input directly — it validates against `ordering_fields`. Always use `OrderingFilter` rather than passing request data to `order_by()` directly.

---

## CVE-2021-33203 — Potential Directory Traversal via admindocs

- **Severity:** Moderate
- **Affected versions:** Django < 3.1.12, < 3.2.4, < 2.2.24
- **Description:** Staff users could read arbitrary files from the file system using the admindocs view if the optional `django.contrib.admindocs` app was installed.
- **Fix:** Upgrade or remove `django.contrib.admindocs` from `INSTALLED_APPS`.

---

## CVE-2020-13254 — Potential Data Leakage via Memcached Cache Backend

- **Severity:** Moderate
- **Affected versions:** Django < 2.2.13, < 3.0.7
- **Description:** Memcached key validation was insufficient, allowing keys containing whitespace or control characters. Depending on the Memcached library, this could result in cache poisoning.
- **Fix:** Upgrade to Django 2.2.13 or 3.0.7+. Validate cache keys before use.

---

## CVE-2019-14234 — SQL Injection via Key/Index Lookups in JSONField

- **Severity:** Critical
- **Affected versions:** Django < 1.11.23, < 2.1.11, < 2.2.4
- **Description:** Key and index lookups for `JSONField` and `HStoreField` on PostgreSQL did not properly escape column names, enabling SQL injection.
- **Fix:** Upgrade to Django 2.2.4+.
- **API relevance:** APIs accepting filter parameters on JSON or HStore fields are vulnerable on PostgreSQL.

---

## General Security Hardening Checklist for Django REST APIs

| Item | Setting / Action |
|------|-----------------|
| Disable debug mode | `DEBUG = False` |
| Restrict allowed hosts | `ALLOWED_HOSTS = ['yourdomain.com']` |
| Use HTTPS | `SECURE_SSL_REDIRECT = True` |
| Secure cookies | `SESSION_COOKIE_SECURE = True`, `CSRF_COOKIE_SECURE = True` |
| HSTS | `SECURE_HSTS_SECONDS = 31536000` |
| Require authentication | `DEFAULT_PERMISSION_CLASSES = [IsAuthenticated]` |
| Require JWT auth | `DEFAULT_AUTHENTICATION_CLASSES = [JWTAuthentication]` |
| Set token expiry | `SIMPLE_JWT = {'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15)}` |
| Enable throttling | `DEFAULT_THROTTLE_CLASSES` configured |
| Read-only sensitive fields | `extra_kwargs = {'is_admin': {'read_only': True}}` |
| Keep Django updated | Monitor https://www.djangoproject.com/weblog/ |
| Run `python manage.py check --deploy` | Detects common misconfigurations |
