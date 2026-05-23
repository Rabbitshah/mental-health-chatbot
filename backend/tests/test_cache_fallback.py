"""
Tests for cache fallback behavior (Requirement 12.5).

Verifies that when Redis is unavailable, the application continues to work
by falling back to direct database queries without errors.
"""
# ---------------------------------------------------------------------------
# Disable Redis before any app imports
# ---------------------------------------------------------------------------
import os as _os
_os.environ.setdefault("REDIS_ENABLED", "false")

# ---------------------------------------------------------------------------
# bcrypt compatibility patch (must be before passlib imports)
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
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from database import Base, get_db
from main import app
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

class FakeGeminiResponse:
    def __init__(self, text):
        self.text = text


class FakeGeminiChat:
    def send_message(self, message):
        return FakeGeminiResponse("I'm here to support you.")


class FakeGeminiModel:
    def start_chat(self, history=None):
        return FakeGeminiChat()


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

    original_model = chat_routes.model
    chat_routes.model = FakeGeminiModel()

    c = TestClient(app, raise_server_exceptions=False)
    yield c

    chat_routes.model = original_model
    app.dependency_overrides.clear()

    for table in reversed(_TABLES):
        table.drop(bind=_engine, checkfirst=True)


@pytest.fixture(autouse=True)
def clean_db():
    """Truncate all tables before each test."""
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


def signup_and_login(client) -> dict:
    """Helper: register a user and return auth headers."""
    client.post(
        "/signup",
        json={
            "email": "fallback@example.com",
            "password": "Password123!",
            "name": "Fallback User",
            "username": "fallback_user",
        },
    )
    login = client.post(
        "/login",
        json={"email": "fallback@example.com", "password": "Password123!"},
    )
    assert login.status_code == 200, f"Login failed: {login.text}"
    token = login.json()["token"]
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Helper: patch redis_client so every cache helper raises ConnectionError
# ---------------------------------------------------------------------------

def redis_down():
    """Context manager that makes all cache helpers simulate Redis being down."""
    return patch.multiple(
        "redis_client",
        cache_get=MagicMock(side_effect=ConnectionError("Redis is down")),
        cache_set=MagicMock(side_effect=ConnectionError("Redis is down")),
        cache_delete=MagicMock(side_effect=ConnectionError("Redis is down")),
        cache_delete_pattern=MagicMock(side_effect=ConnectionError("Redis is down")),
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestCacheFallback:
    """Validates Requirement 12.5: cache unavailability falls back to DB."""

    def test_get_history_returns_200_when_redis_down(self, client):
        """GET /history still returns 200 when Redis raises ConnectionError."""
        headers = signup_and_login(client)

        # Patch cache helpers in the history route module
        with patch("routes.history.cache_get", side_effect=ConnectionError("Redis is down")), \
             patch("routes.history.cache_set", side_effect=ConnectionError("Redis is down")):
            response = client.get("/history", headers=headers)

        assert response.status_code == 200

    def test_post_chat_returns_200_when_redis_down(self, client):
        """POST /chat still works when Redis raises ConnectionError."""
        headers = signup_and_login(client)

        with patch("routes.chat.cache_delete", side_effect=ConnectionError("Redis is down")):
            response = client.post(
                "/chat",
                json={"message": "Hello, I need support"},
                headers=headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "session_id" in data

    def test_get_insights_mood_returns_200_when_redis_down(self, client):
        """GET /insights/mood still works when Redis raises ConnectionError."""
        headers = signup_and_login(client)

        with patch("routes.insights.cache_get", side_effect=ConnectionError("Redis is down")), \
             patch("routes.insights.cache_set", side_effect=ConnectionError("Redis is down")):
            response = client.get("/insights/mood", headers=headers)

        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_cache_get_returns_none_on_connection_error(self):
        """cache_get() returns None instead of raising when Redis is unavailable."""
        import redis_client as rc
        with patch.object(rc, "_redis_client", None), \
             patch.object(rc, "_redis_unavailable", False), \
             patch("redis_client.redis.Redis") as mock_redis_cls:
            mock_redis_cls.return_value.ping.side_effect = ConnectionError("no redis")
            result = rc.cache_get("some:key")
        assert result is None

    def test_cache_set_returns_false_on_connection_error(self):
        """cache_set() returns False instead of raising when Redis is unavailable."""
        import redis_client as rc
        with patch.object(rc, "_redis_client", None), \
             patch.object(rc, "_redis_unavailable", False), \
             patch("redis_client.redis.Redis") as mock_redis_cls:
            mock_redis_cls.return_value.ping.side_effect = ConnectionError("no redis")
            result = rc.cache_set("some:key", "value", 300)
        assert result is False

    def test_cache_delete_returns_false_on_connection_error(self):
        """cache_delete() returns False instead of raising when Redis is unavailable."""
        import redis_client as rc
        with patch.object(rc, "_redis_client", None), \
             patch.object(rc, "_redis_unavailable", False), \
             patch("redis_client.redis.Redis") as mock_redis_cls:
            mock_redis_cls.return_value.ping.side_effect = ConnectionError("no redis")
            result = rc.cache_delete("some:key")
        assert result is False

    def test_history_falls_back_to_db_data(self, client):
        """GET /history returns actual DB data even when cache is unavailable."""
        headers = signup_and_login(client)

        # Create a chat session first
        client.post("/chat", json={"message": "Test message"}, headers=headers)

        with patch("routes.history.cache_get", return_value=None), \
             patch("routes.history.cache_set", side_effect=ConnectionError("Redis is down")):
            response = client.get("/history", headers=headers)

        assert response.status_code == 200
        body = response.json()
        # Should have at least one session from the chat above
        sessions = body.get("sessions", body) if isinstance(body, dict) else body
        assert len(sessions) >= 1
