"""
Property-Based Tests for CORS Origin Validation

This module contains property tests that validate:
- Property 29: CORS Origin Validation
- Validates: Requirements 10.5

Requirement 10.5:
"WHEN a request comes from an unauthorized origin, THEN THE Backend SHALL
reject it with a CORS error"
"""
import os
import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Helpers: build a minimal FastAPI app with CORSMiddleware
# ---------------------------------------------------------------------------

ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:3000",
]


def _make_app(allowed_origins: list[str]) -> FastAPI:
    """Return a minimal FastAPI app configured with the given CORS origins."""
    app = FastAPI()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/ping")
    def ping():
        return {"status": "ok"}

    return app


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

# Allowed origins drawn from the configured list
_allowed_origin_st = st.sampled_from(ALLOWED_ORIGINS)

# ASCII lowercase letters only — valid for HTTP hostnames
_ascii_lower = "abcdefghijklmnopqrstuvwxyz"

# Unauthorized origins: well-formed URLs that are NOT in ALLOWED_ORIGINS
_unauthorized_origin_st = st.one_of(
    # Different host
    st.just("http://evil.com"),
    st.just("https://attacker.example.com"),
    st.just("http://malicious.io"),
    # Different port on localhost
    st.just("http://localhost:9999"),
    st.just("http://localhost:4000"),
    st.just("http://localhost:8080"),
    # Different scheme
    st.just("https://localhost:5173"),
    st.just("https://localhost:3000"),
    # Subdomain variations
    st.just("http://sub.localhost:5173"),
    st.just("http://notlocalhost:5173"),
    # Generated random-ish hostnames (ASCII only, valid for HTTP headers)
    st.builds(
        lambda host, port: f"http://{host}.example.com:{port}",
        host=st.text(alphabet=_ascii_lower, min_size=3, max_size=10),
        port=st.integers(min_value=1024, max_value=65535),
    ),
).filter(lambda o: o not in ALLOWED_ORIGINS)


# ===========================================================================
# Property 29: CORS Origin Validation
# Validates: Requirements 10.5
# ===========================================================================

class TestProperty29CORSOriginValidation:
    """
    PROPERTY 29: CORS Origin Validation

    *For any* request from an origin NOT in the allowed CORS origins list,
    the system should reject the request with a CORS error (no matching
    Access-Control-Allow-Origin header in the response).

    *For any* request from an origin IN the allowed CORS origins list,
    the system should include the correct Access-Control-Allow-Origin header.

    **Validates: Requirements 10.5**
    """

    @given(origin=_unauthorized_origin_st)
    @settings(
        max_examples=15,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_unauthorized_origin_is_rejected(self, origin: str):
        """
        Property: For any origin NOT in the allowed list, the backend MUST NOT
        echo that origin in the Access-Control-Allow-Origin response header.

        Given: An origin that is not in CORS_ORIGINS
        When: A preflight (OPTIONS) request is sent with that Origin header
        Then: The response does NOT include Access-Control-Allow-Origin matching
              the unauthorized origin
        """
        app = _make_app(ALLOWED_ORIGINS)
        client = TestClient(app, raise_server_exceptions=False)

        response = client.options(
            "/ping",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "GET",
            },
        )

        acao = response.headers.get("access-control-allow-origin", "")

        # The header must NOT match the unauthorized origin
        assert acao != origin, (
            f"Unauthorized origin '{origin}' must not be echoed in "
            f"Access-Control-Allow-Origin (got: '{acao}')"
        )
        # Also must not be a wildcard that would allow everything
        assert acao != "*", (
            "Access-Control-Allow-Origin must not be '*' when credentials are allowed"
        )

    @given(origin=_allowed_origin_st)
    @settings(
        max_examples=10,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_authorized_origin_is_accepted(self, origin: str):
        """
        Property: For any origin IN the allowed list, the backend MUST echo
        that origin in the Access-Control-Allow-Origin response header.

        Given: An origin that IS in CORS_ORIGINS
        When: A preflight (OPTIONS) request is sent with that Origin header
        Then: The response includes Access-Control-Allow-Origin matching the origin

        **Validates: Requirements 10.5**
        """
        app = _make_app(ALLOWED_ORIGINS)
        client = TestClient(app, raise_server_exceptions=False)

        response = client.options(
            "/ping",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "GET",
            },
        )

        acao = response.headers.get("access-control-allow-origin", "")

        assert acao == origin, (
            f"Authorized origin '{origin}' must be echoed in "
            f"Access-Control-Allow-Origin (got: '{acao}')"
        )

    @given(origin=_unauthorized_origin_st)
    @settings(
        max_examples=15,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_unauthorized_origin_simple_request_not_reflected(self, origin: str):
        """
        Property: For a simple GET request from an unauthorized origin, the
        backend MUST NOT reflect that origin in Access-Control-Allow-Origin.

        Given: An origin not in the allowed list
        When: A simple GET request is sent with that Origin header
        Then: The response does NOT include Access-Control-Allow-Origin matching
              the unauthorized origin

        **Validates: Requirements 10.5**
        """
        app = _make_app(ALLOWED_ORIGINS)
        client = TestClient(app, raise_server_exceptions=False)

        response = client.get("/ping", headers={"Origin": origin})

        acao = response.headers.get("access-control-allow-origin", "")

        assert acao != origin, (
            f"Unauthorized origin '{origin}' must not be reflected in "
            f"Access-Control-Allow-Origin for simple requests (got: '{acao}')"
        )

    @given(origin=_allowed_origin_st)
    @settings(
        max_examples=10,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_authorized_origin_simple_request_reflected(self, origin: str):
        """
        Property: For a simple GET request from an authorized origin, the
        backend MUST reflect that origin in Access-Control-Allow-Origin.

        Given: An origin that IS in the allowed list
        When: A simple GET request is sent with that Origin header
        Then: The response includes Access-Control-Allow-Origin matching the origin

        **Validates: Requirements 10.5**
        """
        app = _make_app(ALLOWED_ORIGINS)
        client = TestClient(app, raise_server_exceptions=False)

        response = client.get("/ping", headers={"Origin": origin})

        acao = response.headers.get("access-control-allow-origin", "")

        assert acao == origin, (
            f"Authorized origin '{origin}' must be reflected in "
            f"Access-Control-Allow-Origin for simple requests (got: '{acao}')"
        )

    @given(
        allowed_origins=st.lists(
            st.builds(
                lambda host, port: f"http://{host}.test:{port}",
                host=st.text(alphabet=_ascii_lower, min_size=3, max_size=8),
                port=st.integers(min_value=1024, max_value=9999),
            ),
            min_size=1,
            max_size=5,
            unique=True,
        )
    )
    @settings(
        max_examples=10,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_only_configured_origins_are_allowed(self, allowed_origins: list[str]):
        """
        Property: For any set of configured allowed origins, ONLY those origins
        receive the Access-Control-Allow-Origin header; all others are rejected.

        Given: An arbitrary list of allowed origins
        When: Requests are sent from each allowed origin and from a non-allowed origin
        Then: Allowed origins are reflected; non-allowed origins are not

        **Validates: Requirements 10.1, 10.5**
        """
        app = _make_app(allowed_origins)
        client = TestClient(app, raise_server_exceptions=False)

        # Each allowed origin should be accepted
        for origin in allowed_origins:
            response = client.get("/ping", headers={"Origin": origin})
            acao = response.headers.get("access-control-allow-origin", "")
            assert acao == origin, (
                f"Configured origin '{origin}' must be reflected (got: '{acao}')"
            )

        # A clearly non-allowed origin must be rejected
        non_allowed = "http://definitely-not-allowed.example.com:12345"
        assume(non_allowed not in allowed_origins)

        response = client.get("/ping", headers={"Origin": non_allowed})
        acao = response.headers.get("access-control-allow-origin", "")
        assert acao != non_allowed, (
            f"Non-allowed origin '{non_allowed}' must not be reflected (got: '{acao}')"
        )
