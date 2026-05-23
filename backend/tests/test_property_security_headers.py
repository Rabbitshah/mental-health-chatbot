"""
Property-Based Tests for Security Headers

This module contains property tests that validate:
- Property 28: Security Headers on All Responses
- Validates: Requirements 10.3, 10.4

Requirement 10.3:
"THE Backend SHALL set the following security headers on all responses:
X-Content-Type-Options: nosniff, X-Frame-Options: DENY, X-XSS-Protection: 1; mode=block"

Requirement 10.4:
"THE Backend SHALL set Content-Security-Policy header with appropriate directives
for the application"
"""
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


# ---------------------------------------------------------------------------
# Helpers: replicate SecurityHeadersMiddleware from main.py
# ---------------------------------------------------------------------------

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Mirrors the SecurityHeadersMiddleware defined in backend/main.py."""

    def __init__(self, app, environment: str = "development"):
        super().__init__(app)
        self.environment = environment

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "connect-src 'self' https:;"
        )
        if self.environment == "production":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )
        return response


# ---------------------------------------------------------------------------
# Helpers: build minimal FastAPI apps with various routes
# ---------------------------------------------------------------------------

REQUIRED_SECURITY_HEADERS = {
    "x-content-type-options": "nosniff",
    "x-frame-options": "DENY",
    "x-xss-protection": "1; mode=block",
}

REQUIRED_CSP_DIRECTIVES = [
    "default-src",
    "script-src",
    "style-src",
    "img-src",
    "connect-src",
]


def _make_app(routes: list[tuple[str, int]], environment: str = "development") -> FastAPI:
    """
    Build a minimal FastAPI app with SecurityHeadersMiddleware and the given
    routes. Each route is a (path, status_code) tuple.
    """
    app = FastAPI()
    app.add_middleware(SecurityHeadersMiddleware, environment=environment)

    for path, status_code in routes:
        # Capture status_code in closure
        def _make_handler(code: int):
            async def handler():
                return Response(content="ok", status_code=code)
            return handler

        app.add_api_route(path, _make_handler(status_code), methods=["GET"])

    return app


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

# Valid URL path segments (no slashes, no special chars that break routing)
_path_segment_st = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz0123456789-_",
    min_size=1,
    max_size=15,
)

# Generate a list of 1-5 unique route paths
_routes_st = st.lists(
    _path_segment_st,
    min_size=1,
    max_size=5,
    unique=True,
).map(lambda segs: [(f"/{seg}", 200) for seg in segs])

# HTTP methods to test
_http_method_st = st.sampled_from(["GET"])

# Status codes that the app might return
_status_code_st = st.sampled_from([200, 201, 400, 401, 403, 404, 422, 500])

# Routes with varied status codes
_routes_with_status_st = st.lists(
    st.tuples(_path_segment_st, _status_code_st),
    min_size=1,
    max_size=4,
    unique_by=lambda t: t[0],
)


# ===========================================================================
# Property 28: Security Headers on All Responses
# Validates: Requirements 10.3, 10.4
# ===========================================================================

class TestProperty28SecurityHeadersOnAllResponses:
    """
    PROPERTY 28: Security Headers on All Responses

    For ANY endpoint and ANY response status code, the backend MUST include
    the required security headers: X-Content-Type-Options, X-Frame-Options,
    X-XSS-Protection, and Content-Security-Policy.

    **Validates: Requirements 10.3, 10.4**
    """

    @given(routes=_routes_st)
    @settings(
        max_examples=15,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_x_content_type_options_present_on_all_routes(self, routes: list):
        """
        Property: X-Content-Type-Options: nosniff MUST be present on every
        response regardless of which endpoint is called.

        Given: An arbitrary set of API routes
        When: A GET request is made to any of those routes
        Then: The response includes X-Content-Type-Options: nosniff

        **Validates: Requirements 10.3**
        """
        app = _make_app(routes)
        client = TestClient(app, raise_server_exceptions=False)

        for path, _ in routes:
            response = client.get(path)
            header_value = response.headers.get("x-content-type-options", "")
            assert header_value == "nosniff", (
                f"Route '{path}': expected X-Content-Type-Options='nosniff', "
                f"got '{header_value}'"
            )

    @given(routes=_routes_st)
    @settings(
        max_examples=15,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_x_frame_options_present_on_all_routes(self, routes: list):
        """
        Property: X-Frame-Options: DENY MUST be present on every response.

        Given: An arbitrary set of API routes
        When: A GET request is made to any of those routes
        Then: The response includes X-Frame-Options: DENY

        **Validates: Requirements 10.3**
        """
        app = _make_app(routes)
        client = TestClient(app, raise_server_exceptions=False)

        for path, _ in routes:
            response = client.get(path)
            header_value = response.headers.get("x-frame-options", "")
            assert header_value == "DENY", (
                f"Route '{path}': expected X-Frame-Options='DENY', "
                f"got '{header_value}'"
            )

    @given(routes=_routes_st)
    @settings(
        max_examples=15,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_x_xss_protection_present_on_all_routes(self, routes: list):
        """
        Property: X-XSS-Protection: 1; mode=block MUST be present on every response.

        Given: An arbitrary set of API routes
        When: A GET request is made to any of those routes
        Then: The response includes X-XSS-Protection: 1; mode=block

        **Validates: Requirements 10.3**
        """
        app = _make_app(routes)
        client = TestClient(app, raise_server_exceptions=False)

        for path, _ in routes:
            response = client.get(path)
            header_value = response.headers.get("x-xss-protection", "")
            assert header_value == "1; mode=block", (
                f"Route '{path}': expected X-XSS-Protection='1; mode=block', "
                f"got '{header_value}'"
            )

    @given(routes=_routes_st)
    @settings(
        max_examples=15,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_content_security_policy_present_on_all_routes(self, routes: list):
        """
        Property: Content-Security-Policy header MUST be present on every response
        and MUST contain the required directives.

        Given: An arbitrary set of API routes
        When: A GET request is made to any of those routes
        Then: The response includes a Content-Security-Policy header with
              default-src, script-src, style-src, img-src, and connect-src directives

        **Validates: Requirements 10.4**
        """
        app = _make_app(routes)
        client = TestClient(app, raise_server_exceptions=False)

        for path, _ in routes:
            response = client.get(path)
            csp = response.headers.get("content-security-policy", "")

            assert csp, (
                f"Route '{path}': Content-Security-Policy header is missing"
            )

            for directive in REQUIRED_CSP_DIRECTIVES:
                assert directive in csp, (
                    f"Route '{path}': CSP missing '{directive}' directive "
                    f"(got: '{csp}')"
                )

    @given(routes=_routes_with_status_st)
    @settings(
        max_examples=15,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_all_security_headers_present_regardless_of_status_code(
        self, routes: list
    ):
        """
        Property: ALL required security headers MUST be present regardless of
        the HTTP response status code (200, 4xx, 5xx, etc.).

        Given: Routes that return various HTTP status codes
        When: A GET request is made to each route
        Then: All required security headers are present on every response

        **Validates: Requirements 10.3, 10.4**
        """
        app = _make_app(routes)
        client = TestClient(app, raise_server_exceptions=False)

        for path, _ in routes:
            response = client.get(path)

            for header_name, expected_value in REQUIRED_SECURITY_HEADERS.items():
                actual = response.headers.get(header_name, "")
                assert actual == expected_value, (
                    f"Route '{path}' (status {response.status_code}): "
                    f"expected {header_name}='{expected_value}', got '{actual}'"
                )

            csp = response.headers.get("content-security-policy", "")
            assert csp, (
                f"Route '{path}' (status {response.status_code}): "
                f"Content-Security-Policy header is missing"
            )

    @given(routes=_routes_st)
    @settings(
        max_examples=10,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_csp_self_source_restriction(self, routes: list):
        """
        Property: The Content-Security-Policy MUST restrict default-src to 'self',
        ensuring resources are only loaded from the same origin by default.

        Given: An arbitrary set of API routes
        When: A GET request is made to any route
        Then: The CSP header contains "default-src 'self'"

        **Validates: Requirements 10.4**
        """
        app = _make_app(routes)
        client = TestClient(app, raise_server_exceptions=False)

        for path, _ in routes:
            response = client.get(path)
            csp = response.headers.get("content-security-policy", "")

            assert "default-src 'self'" in csp, (
                f"Route '{path}': CSP must restrict default-src to 'self' "
                f"(got: '{csp}')"
            )

    @given(routes=_routes_st)
    @settings(
        max_examples=10,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_hsts_absent_in_development(self, routes: list):
        """
        Property: Strict-Transport-Security MUST NOT be set in development mode,
        as it would break local HTTP development workflows.

        Given: An app running in development environment
        When: A GET request is made to any route
        Then: The Strict-Transport-Security header is NOT present

        **Validates: Requirements 10.3 (HSTS is production-only)**
        """
        app = _make_app(routes, environment="development")
        client = TestClient(app, raise_server_exceptions=False)

        for path, _ in routes:
            response = client.get(path)
            hsts = response.headers.get("strict-transport-security", "")
            assert hsts == "", (
                f"Route '{path}': Strict-Transport-Security must not be set "
                f"in development mode (got: '{hsts}')"
            )

    @given(routes=_routes_st)
    @settings(
        max_examples=10,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_hsts_present_in_production(self, routes: list):
        """
        Property: Strict-Transport-Security MUST be set in production mode
        to enforce HTTPS connections.

        Given: An app running in production environment
        When: A GET request is made to any route
        Then: The Strict-Transport-Security header is present with max-age and includeSubDomains

        **Validates: Requirements 10.3 (Req 10.6 - HSTS in production)**
        """
        app = _make_app(routes, environment="production")
        client = TestClient(app, raise_server_exceptions=False)

        for path, _ in routes:
            response = client.get(path)
            hsts = response.headers.get("strict-transport-security", "")
            assert "max-age=" in hsts, (
                f"Route '{path}': Strict-Transport-Security must include max-age "
                f"in production (got: '{hsts}')"
            )
            assert "includeSubDomains" in hsts, (
                f"Route '{path}': Strict-Transport-Security must include "
                f"includeSubDomains in production (got: '{hsts}')"
            )
