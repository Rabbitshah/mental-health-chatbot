"""
Integration tests for security headers on all responses.

Verifies that SecurityHeadersMiddleware sets the required headers on every
response, across public and protected endpoints, and for various HTTP status
codes.

Requirements: 10.3, 10.4, 10.6
"""
# ---------------------------------------------------------------------------
# Disable Redis before any app imports
# ---------------------------------------------------------------------------
import os as _os
_os.environ.setdefault("REDIS_ENABLED", "false")

# ---------------------------------------------------------------------------
# bcrypt compatibility patch (must run before passlib imports)
# ---------------------------------------------------------------------------
import bcrypt as _bcrypt_compat
import types as _types_compat

if not hasattr(_bcrypt_compat, "__about__"):
    _about = _types_compat.ModuleType("bcrypt.__about__")
    _about.__version__ = _bcrypt_compat.__version__
    _bcrypt_compat.__about__ = _about

_orig_hashpw = _bcrypt_compat.hashpw
def _patched_hashpw(password, salt):
    if isinstance(password, (bytes, bytearray)) and len(password) > 72:
        password = password[:72]
    return _orig_hashpw(password, salt)
_bcrypt_compat.hashpw = _patched_hashpw

_orig_checkpw = _bcrypt_compat.checkpw
def _patched_checkpw(password, hashed_password):
    if isinstance(password, (bytes, bytearray)) and len(password) > 72:
        password = password[:72]
    return _orig_checkpw(password, hashed_password)
_bcrypt_compat.checkpw = _patched_checkpw

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from fastapi import FastAPI

from database import Base, get_db
from main import app, SecurityHeadersMiddleware
from routes import chat as chat_routes
import routes.auth as _auth_routes

# ---------------------------------------------------------------------------
# In-memory SQLite engine
# ---------------------------------------------------------------------------

_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@event.listens_for(_engine, "connect")
def _enable_fk(dbapi_conn, _):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


_TABLES = [
    Base.metadata.tables["users"],
    Base.metadata.tables["chat_sessions"],
    Base.metadata.tables["chat_messages"],
    Base.metadata.tables["mood_entries"],
    Base.metadata.tables["refresh_tokens"],
]

_Session = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


def _override_get_db():
    db = _Session()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Fake Gemini model
# ---------------------------------------------------------------------------

class _FakeGeminiResponse:
    def __init__(self, text):
        self.text = text


class _FakeGeminiChat:
    def send_message(self, message):
        return _FakeGeminiResponse(f"Support reply: {message}")


class _FakeGeminiModel:
    def start_chat(self, history=None):
        return _FakeGeminiChat()


# ---------------------------------------------------------------------------
# Module-scoped client fixture
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def client():
    for table in _TABLES:
        table.create(bind=_engine, checkfirst=True)

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[_auth_routes.get_db] = _override_get_db

    original_model = chat_routes.model
    chat_routes.model = _FakeGeminiModel()

    c = TestClient(app, raise_server_exceptions=False)
    yield c

    chat_routes.model = original_model
    app.dependency_overrides.clear()

    for table in reversed(_TABLES):
        table.drop(bind=_engine, checkfirst=True)


@pytest.fixture(autouse=True)
def clean_db():
    yield
    db = _Session()
    try:
        for table in reversed(_TABLES):
            db.execute(table.delete())
        db.commit()
    finally:
        db.close()
    try:
        from limiter import limiter
        limiter._storage.reset()
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _signup_and_login(client) -> dict:
    client.post(
        "/signup",
        json={
            "email": "hdr_test@example.com",
            "password": "Password123!",
            "name": "Header Tester",
            "username": "hdr_tester",
        },
    )
    login = client.post(
        "/login",
        json={"email": "hdr_test@example.com", "password": "Password123!"},
    )
    token = login.json()["token"]
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Required header constants (Req 10.3, 10.4)
# ---------------------------------------------------------------------------

REQUIRED_HEADERS = {
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


# ===========================================================================
# Tests
# ===========================================================================

class TestSecurityHeadersOnPublicEndpoints:
    """Security headers must be present on public (unauthenticated) endpoints."""

    def test_signup_endpoint_has_security_headers(self, client):
        """POST /signup (public) must include all required security headers. Req 10.3"""
        response = client.post(
            "/signup",
            json={
                "email": "pub1@example.com",
                "password": "Password123!",
                "name": "Pub User",
                "username": "pub_user1",
            },
        )
        for header, value in REQUIRED_HEADERS.items():
            assert response.headers.get(header) == value, (
                f"POST /signup: expected {header}='{value}', "
                f"got '{response.headers.get(header)}'"
            )

    def test_login_endpoint_has_security_headers(self, client):
        """POST /login (public) must include all required security headers. Req 10.3"""
        # Create user first
        client.post(
            "/signup",
            json={
                "email": "pub2@example.com",
                "password": "Password123!",
                "name": "Pub User2",
                "username": "pub_user2",
            },
        )
        response = client.post(
            "/login",
            json={"email": "pub2@example.com", "password": "Password123!"},
        )
        for header, value in REQUIRED_HEADERS.items():
            assert response.headers.get(header) == value, (
                f"POST /login: expected {header}='{value}', "
                f"got '{response.headers.get(header)}'"
            )

    def test_login_endpoint_has_csp_header(self, client):
        """POST /login must include Content-Security-Policy header. Req 10.4"""
        client.post(
            "/signup",
            json={
                "email": "pub3@example.com",
                "password": "Password123!",
                "name": "Pub User3",
                "username": "pub_user3",
            },
        )
        response = client.post(
            "/login",
            json={"email": "pub3@example.com", "password": "Password123!"},
        )
        csp = response.headers.get("content-security-policy", "")
        assert csp, "POST /login: Content-Security-Policy header is missing"
        for directive in REQUIRED_CSP_DIRECTIVES:
            assert directive in csp, (
                f"POST /login: CSP missing '{directive}' directive (got: '{csp}')"
            )

    def test_unauthenticated_request_to_protected_endpoint_has_security_headers(
        self, client
    ):
        """401 responses from protected endpoints must still include security headers. Req 10.3"""
        response = client.get("/history/")
        assert response.status_code == 401
        for header, value in REQUIRED_HEADERS.items():
            assert response.headers.get(header) == value, (
                f"GET /history/ (401): expected {header}='{value}', "
                f"got '{response.headers.get(header)}'"
            )


class TestSecurityHeadersOnProtectedEndpoints:
    """Security headers must be present on authenticated (protected) endpoints."""

    def test_chat_endpoint_has_security_headers(self, client):
        """POST /chat must include all required security headers. Req 10.3"""
        headers = _signup_and_login(client)
        response = client.post(
            "/chat",
            json={"message": "I feel anxious today."},
            headers=headers,
        )
        assert response.status_code == 200
        for header, value in REQUIRED_HEADERS.items():
            assert response.headers.get(header) == value, (
                f"POST /chat: expected {header}='{value}', "
                f"got '{response.headers.get(header)}'"
            )

    def test_chat_endpoint_has_csp_header(self, client):
        """POST /chat must include Content-Security-Policy header. Req 10.4"""
        headers = _signup_and_login(client)
        response = client.post(
            "/chat",
            json={"message": "I feel anxious today."},
            headers=headers,
        )
        csp = response.headers.get("content-security-policy", "")
        assert csp, "POST /chat: Content-Security-Policy header is missing"
        for directive in REQUIRED_CSP_DIRECTIVES:
            assert directive in csp, (
                f"POST /chat: CSP missing '{directive}' directive (got: '{csp}')"
            )

    def test_history_endpoint_has_security_headers(self, client):
        """GET /history/ must include all required security headers. Req 10.3"""
        headers = _signup_and_login(client)
        response = client.get("/history/", headers=headers)
        assert response.status_code == 200
        for header, value in REQUIRED_HEADERS.items():
            assert response.headers.get(header) == value, (
                f"GET /history/: expected {header}='{value}', "
                f"got '{response.headers.get(header)}'"
            )

    def test_insights_mood_endpoint_has_security_headers(self, client):
        """POST /insights/mood must include all required security headers. Req 10.3"""
        headers = _signup_and_login(client)
        response = client.post(
            "/insights/mood",
            json={"mood_score": 7, "energy_level": 6, "stress_level": 4},
            headers=headers,
        )
        assert response.status_code == 200
        for header, value in REQUIRED_HEADERS.items():
            assert response.headers.get(header) == value, (
                f"POST /insights/mood: expected {header}='{value}', "
                f"got '{response.headers.get(header)}'"
            )

    def test_export_endpoint_has_security_headers(self, client):
        """GET /export must include all required security headers. Req 10.3"""
        headers = _signup_and_login(client)
        response = client.get("/export", headers=headers)
        assert response.status_code == 200
        for header, value in REQUIRED_HEADERS.items():
            assert response.headers.get(header) == value, (
                f"GET /export: expected {header}='{value}', "
                f"got '{response.headers.get(header)}'"
            )


class TestSecurityHeaderValues:
    """Verify the exact values of each security header. Req 10.3, 10.4"""

    def test_x_content_type_options_is_nosniff(self, client):
        """X-Content-Type-Options must be exactly 'nosniff'. Req 10.3"""
        headers = _signup_and_login(client)
        response = client.get("/history/", headers=headers)
        assert response.headers.get("x-content-type-options") == "nosniff"

    def test_x_frame_options_is_deny(self, client):
        """X-Frame-Options must be exactly 'DENY'. Req 10.3"""
        headers = _signup_and_login(client)
        response = client.get("/history/", headers=headers)
        assert response.headers.get("x-frame-options") == "DENY"

    def test_x_xss_protection_value(self, client):
        """X-XSS-Protection must be '1; mode=block'. Req 10.3"""
        headers = _signup_and_login(client)
        response = client.get("/history/", headers=headers)
        assert response.headers.get("x-xss-protection") == "1; mode=block"

    def test_csp_contains_default_src_self(self, client):
        """CSP must restrict default-src to 'self'. Req 10.4"""
        headers = _signup_and_login(client)
        response = client.get("/history/", headers=headers)
        csp = response.headers.get("content-security-policy", "")
        assert "default-src 'self'" in csp, (
            f"CSP must contain \"default-src 'self'\" (got: '{csp}')"
        )

    def test_csp_contains_all_required_directives(self, client):
        """CSP must contain all required directives. Req 10.4"""
        headers = _signup_and_login(client)
        response = client.get("/history/", headers=headers)
        csp = response.headers.get("content-security-policy", "")
        for directive in REQUIRED_CSP_DIRECTIVES:
            assert directive in csp, (
                f"CSP missing '{directive}' directive (got: '{csp}')"
            )


class TestHSTSProductionHeader:
    """Strict-Transport-Security must be set in production mode. Req 10.6"""

    def test_hsts_absent_in_development_mode(self, client):
        """HSTS must NOT be set when ENVIRONMENT != 'production'. Req 10.6"""
        # The test client uses the app as configured; default env is development
        current_env = _os.getenv("ENVIRONMENT", "development")
        if current_env == "production":
            pytest.skip("Skipping: environment is production")

        headers = _signup_and_login(client)
        response = client.get("/history/", headers=headers)
        hsts = response.headers.get("strict-transport-security", "")
        assert hsts == "", (
            f"HSTS must not be set in development mode (got: '{hsts}')"
        )

    def test_hsts_present_in_production_mode(self):
        """HSTS must be set with max-age and includeSubDomains in production. Req 10.6"""
        # Build a minimal app with SecurityHeadersMiddleware in production mode
        mini_app = FastAPI()
        mini_app.add_middleware(SecurityHeadersMiddleware, environment="production")

        @mini_app.get("/ping")
        async def ping():
            return {"ok": True}

        test_client = TestClient(mini_app, raise_server_exceptions=False)
        response = test_client.get("/ping")
        hsts = response.headers.get("strict-transport-security", "")
        assert "max-age=" in hsts, (
            f"HSTS must include max-age in production (got: '{hsts}')"
        )
        assert "includeSubDomains" in hsts, (
            f"HSTS must include includeSubDomains in production (got: '{hsts}')"
        )

    def test_hsts_not_present_in_development_mode_isolated(self):
        """HSTS must NOT be set when middleware is configured for development. Req 10.6"""
        mini_app = FastAPI()
        mini_app.add_middleware(SecurityHeadersMiddleware, environment="development")

        @mini_app.get("/ping")
        async def ping():
            return {"ok": True}

        test_client = TestClient(mini_app, raise_server_exceptions=False)
        response = test_client.get("/ping")
        hsts = response.headers.get("strict-transport-security", "")
        assert hsts == "", (
            f"HSTS must not be set in development mode (got: '{hsts}')"
        )
