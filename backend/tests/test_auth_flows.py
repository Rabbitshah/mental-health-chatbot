"""
Unit tests for authentication flows (task 2.7).

Tests login, token refresh, and logout via FastAPI TestClient.
Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 15.1, 15.2, 15.3, 15.4, 15.5, 15.6
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine, event, StaticPool
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from database import Base, get_db
from models import User, RefreshToken
from main import app
import routes.auth as _auth_routes

# ---------------------------------------------------------------------------
# Test database setup — shared in-memory SQLite connection so all sessions
# (app + fixture teardown) see the same data.
# ---------------------------------------------------------------------------

_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,  # single shared connection — all sessions see same DB
)


@event.listens_for(_engine, "connect")
def _enable_fk(dbapi_conn, _):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


_Session = sessionmaker(autocommit=False, autoflush=False, bind=_engine)

# Tables that are SQLite-compatible (no ARRAY type)
_TABLES = [
    Base.metadata.tables["users"],
    Base.metadata.tables["chat_sessions"],
    Base.metadata.tables["chat_messages"],
    Base.metadata.tables["mood_entries"],
    Base.metadata.tables["refresh_tokens"],
]


def _override_get_db():
    db = _Session()
    try:
        yield db
    finally:
        db.close()


from sqlalchemy import text


def _delete_user_raw(db, user_id: int) -> None:
    """Delete a user and their related rows using raw SQL to avoid cascade
    loading relationships that reference SQLite-incompatible tables (ARRAY)."""
    for stmt in [
        "DELETE FROM refresh_tokens WHERE user_id = :uid",
        "DELETE FROM chat_messages WHERE session_id IN "
        "  (SELECT id FROM chat_sessions WHERE user_id = :uid)",
        "DELETE FROM chat_sessions WHERE user_id = :uid",
        "DELETE FROM mood_entries WHERE user_id = :uid",
        "DELETE FROM users WHERE id = :uid",
    ]:
        db.execute(text(stmt), {"uid": user_id})
    db.commit()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def client():
    """TestClient backed by an isolated in-memory SQLite database."""
    for table in _TABLES:
        table.create(bind=_engine, checkfirst=True)

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[_auth_routes.get_db] = _override_get_db
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c

    app.dependency_overrides.clear()
    for table in reversed(_TABLES):
        table.drop(bind=_engine, checkfirst=True)


@pytest.fixture()
def registered_user(client):
    """
    Ensure a fresh test user exists before each test.
    Cleans up the user (and cascade-deletes tokens) after the test.
    """
    payload = {
        "email": "authflow@example.com",
        "password": "SecurePass123!",
        "name": "Auth Flow User",
        "username": "authflowuser",
    }

    # Remove any leftover user from a previous test — use raw SQL to avoid
    # cascade-loading relationships that reference SQLite-incompatible tables.
    db = _Session()
    try:
        existing = db.query(User).filter(User.email == payload["email"]).first()
        if existing:
            _delete_user_raw(db, existing.id)
    finally:
        db.close()

    resp = client.post("/signup", json=payload)
    assert resp.status_code == 200, f"Signup failed: {resp.text}"

    yield payload

    # Teardown: remove the user so the next test starts clean
    db = _Session()
    try:
        user = db.query(User).filter(User.email == payload["email"]).first()
        if user:
            _delete_user_raw(db, user.id)
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Login endpoint tests
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestLoginEndpoint:
    """Tests for POST /login — Requirements 15.1, 1.1, 1.2"""

    def test_login_valid_credentials_returns_tokens(self, client, registered_user):
        """Login with correct credentials returns both access and refresh tokens."""
        resp = client.post(
            "/login",
            json={"email": registered_user["email"], "password": registered_user["password"]},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "token" in body, "access token missing from response"
        assert "refresh_token" in body, "refresh token missing from response"
        assert len(body["token"]) > 0
        assert len(body["refresh_token"]) > 0

    def test_login_returns_user_info(self, client, registered_user):
        """Login response includes the authenticated user's details."""
        resp = client.post(
            "/login",
            json={"email": registered_user["email"], "password": registered_user["password"]},
        )
        assert resp.status_code == 200
        user_data = resp.json()["user"]
        assert user_data["email"] == registered_user["email"]
        assert user_data["name"] == registered_user["name"]

    def test_login_invalid_password_returns_401(self, client, registered_user):
        """Login with wrong password is rejected with 401."""
        resp = client.post(
            "/login",
            json={"email": registered_user["email"], "password": "WrongPassword!"},
        )
        assert resp.status_code == 401
        assert "Invalid credentials" in resp.json()["detail"]

    def test_login_unknown_email_returns_401(self, client):
        """Login with a non-existent email is rejected with 401."""
        resp = client.post(
            "/login",
            json={"email": "nobody@nowhere.com", "password": "SomePassword1!"},
        )
        assert resp.status_code == 401
        assert "Invalid credentials" in resp.json()["detail"]

    def test_login_stores_refresh_token_in_db(self, client, registered_user):
        """Successful login persists a non-revoked refresh token in the database."""
        resp = client.post(
            "/login",
            json={"email": registered_user["email"], "password": registered_user["password"]},
        )
        assert resp.status_code == 200
        token_value = resp.json()["refresh_token"]

        db = _Session()
        try:
            record = db.query(RefreshToken).filter(RefreshToken.token == token_value).first()
            assert record is not None, "refresh token not found in DB"
            assert record.revoked is False
            assert record.expires_at > datetime.utcnow()
        finally:
            db.close()


# ---------------------------------------------------------------------------
# Token refresh endpoint tests
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestTokenRefreshEndpoint:
    """Tests for POST /auth/refresh — Requirements 15.4, 15.6"""

    def test_refresh_with_valid_token_returns_new_access_token(self, client, registered_user):
        """A valid refresh token exchanges for a new access token."""
        login = client.post(
            "/login",
            json={"email": registered_user["email"], "password": registered_user["password"]},
        )
        assert login.status_code == 200
        refresh_token = login.json()["refresh_token"]

        resp = client.post("/auth/refresh", json={"refresh_token": refresh_token})
        assert resp.status_code == 200
        body = resp.json()
        assert "token" in body
        assert len(body["token"]) > 0

    def test_refresh_with_invalid_token_returns_401(self, client):
        """A completely invalid refresh token is rejected with 401."""
        resp = client.post("/auth/refresh", json={"refresh_token": "totally_invalid_xyz"})
        assert resp.status_code == 401

    def test_refresh_with_expired_token_returns_401(self, client, registered_user):
        """An expired refresh token is rejected with 401."""
        login = client.post(
            "/login",
            json={"email": registered_user["email"], "password": registered_user["password"]},
        )
        assert login.status_code == 200
        refresh_token = login.json()["refresh_token"]

        # Manually expire the token
        db = _Session()
        try:
            record = db.query(RefreshToken).filter(RefreshToken.token == refresh_token).first()
            assert record is not None
            record.expires_at = datetime.utcnow() - timedelta(days=1)
            db.commit()
        finally:
            db.close()

        resp = client.post("/auth/refresh", json={"refresh_token": refresh_token})
        assert resp.status_code == 401
        assert "expired" in resp.json()["detail"].lower()

    def test_refresh_with_revoked_token_returns_401(self, client, registered_user):
        """A revoked refresh token is rejected with 401."""
        login = client.post(
            "/login",
            json={"email": registered_user["email"], "password": registered_user["password"]},
        )
        assert login.status_code == 200
        refresh_token = login.json()["refresh_token"]

        # Revoke via logout
        client.post("/logout", json={"refresh_token": refresh_token})

        resp = client.post("/auth/refresh", json={"refresh_token": refresh_token})
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Logout endpoint tests
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestLogoutEndpoint:
    """Tests for POST /logout — Requirements 15.5"""

    def test_logout_revokes_refresh_token(self, client, registered_user):
        """Logout marks the refresh token as revoked in the database."""
        login = client.post(
            "/login",
            json={"email": registered_user["email"], "password": registered_user["password"]},
        )
        assert login.status_code == 200
        refresh_token = login.json()["refresh_token"]

        logout_resp = client.post("/logout", json={"refresh_token": refresh_token})
        assert logout_resp.status_code == 200
        assert "Logged out" in logout_resp.json()["msg"]

        db = _Session()
        try:
            record = db.query(RefreshToken).filter(RefreshToken.token == refresh_token).first()
            assert record is not None
            assert record.revoked is True
        finally:
            db.close()

    def test_logout_prevents_subsequent_token_refresh(self, client, registered_user):
        """After logout, the same refresh token cannot obtain a new access token."""
        login = client.post(
            "/login",
            json={"email": registered_user["email"], "password": registered_user["password"]},
        )
        assert login.status_code == 200
        refresh_token = login.json()["refresh_token"]

        client.post("/logout", json={"refresh_token": refresh_token})

        resp = client.post("/auth/refresh", json={"refresh_token": refresh_token})
        assert resp.status_code == 401

    def test_logout_with_invalid_token_returns_401(self, client):
        """Logout with a non-existent token returns 401."""
        resp = client.post("/logout", json={"refresh_token": "nonexistent_token_abc"})
        assert resp.status_code == 401
