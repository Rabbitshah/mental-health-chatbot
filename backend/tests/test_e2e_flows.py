# bcrypt compat patch
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

import io
import zipfile
from unittest.mock import patch, MagicMock

import pytest
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from database import Base, get_db
from main import app
import routes.auth as _auth_routes
from models import User, RefreshToken

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
    Base.metadata.tables["safety_plans"],
    Base.metadata.tables["journal_entries"],
]

_Session = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


def _override_get_db():
    db = _Session()
    try:
        yield db
    finally:
        db.close()


def _delete_user_raw(db, user_id):
    for stmt in [
        "DELETE FROM refresh_tokens WHERE user_id = :uid",
        "DELETE FROM chat_messages WHERE session_id IN (SELECT id FROM chat_sessions WHERE user_id = :uid)",
        "DELETE FROM chat_sessions WHERE user_id = :uid",
        "DELETE FROM mood_entries WHERE user_id = :uid",
        "DELETE FROM users WHERE id = :uid",
    ]:
        db.execute(text(stmt), {"uid": user_id})
    db.commit()


@pytest.fixture(scope="module")
def client():
    for table in _TABLES:
        table.create(bind=_engine, checkfirst=True)
    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[_auth_routes.get_db] = _override_get_db
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    app.dependency_overrides.clear()
    for table in reversed(_TABLES):
        table.drop(bind=_engine, checkfirst=True)


@pytest.fixture(autouse=True)
def clean_db():
    yield
    db = _Session()
    try:
        for table in reversed(_TABLES):
            try:
                db.execute(table.delete())
            except Exception:
                db.rollback()
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()


_counter = {"n": 0}


def _unique_user(prefix="e2e"):
    _counter["n"] += 1
    n = _counter["n"]
    return f"{prefix}_{n}@test.com", f"{prefix}_user_{n}"


def _signup_and_login(client, email=None, username=None, password="Password123!"):
    if email is None:
        email, username = _unique_user()
    client.post(
        "/signup",
        json={"email": email, "password": password, "name": "E2E User", "username": username},
    )
    resp = client.post("/login", json={"email": email, "password": password})
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    data = resp.json()
    return {
        "access_token": data["token"],
        "refresh_token": data["refresh_token"],
        "headers": {"Authorization": f"Bearer {data['token']}"},
        "email": email,
    }


def _mock_gemini():
    mock_response = MagicMock()
    mock_response.text = "I hear you. You are not alone."
    mock_chat = MagicMock()
    mock_chat.send_message.return_value = mock_response
    mock_model = MagicMock()
    mock_model.start_chat.return_value = mock_chat
    return mock_model


# ---------------------------------------------------------------------------
# 1. Full auth flow
# ---------------------------------------------------------------------------

class TestAuthFlow:
    def test_signup_returns_tokens(self, client):
        email, username = _unique_user("auth")
        resp = client.post(
            "/signup",
            json={"email": email, "password": "Password123!", "name": "Auth User", "username": username},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body or "token" in body

    def test_login_returns_access_and_refresh_tokens(self, client):
        auth = _signup_and_login(client)
        assert auth["access_token"]
        assert auth["refresh_token"]

    def test_access_token_allows_authenticated_request(self, client):
        auth = _signup_and_login(client)
        resp = client.get("/history/", headers=auth["headers"])
        assert resp.status_code == 200

    def test_unauthenticated_request_returns_401(self, client):
        resp = client.get("/history/")
        assert resp.status_code == 401

    def test_logout_revokes_refresh_token(self, client):
        auth = _signup_and_login(client)
        resp = client.post(
            "/logout",
            json={"refresh_token": auth["refresh_token"]},
            headers=auth["headers"],
        )
        assert resp.status_code == 200
        # After logout, refresh token should be invalid
        refresh_resp = client.post("/auth/refresh", json={"refresh_token": auth["refresh_token"]})
        assert refresh_resp.status_code == 401


# ---------------------------------------------------------------------------
# 2. Chat flow
# ---------------------------------------------------------------------------

class TestChatFlow:
    def test_chat_creates_new_session(self, client):
        auth = _signup_and_login(client)
        with patch("routes.chat.model", _mock_gemini()):
            resp = client.post(
                "/chat",
                json={"message": "I have been feeling anxious lately"},
                headers=auth["headers"],
            )
        assert resp.status_code == 200
        body = resp.json()
        assert "session_id" in body
        assert body["session_id"] is not None
        assert "response" in body

    def test_chat_continues_existing_session(self, client):
        auth = _signup_and_login(client)
        with patch("routes.chat.model", _mock_gemini()):
            first = client.post(
                "/chat",
                json={"message": "I feel stressed"},
                headers=auth["headers"],
            )
        assert first.status_code == 200
        session_id = first.json()["session_id"]

        with patch("routes.chat.model", _mock_gemini()):
            second = client.post(
                "/chat",
                json={"message": "Tell me more about stress relief", "session_id": session_id},
                headers=auth["headers"],
            )
        assert second.status_code == 200
        assert second.json()["session_id"] == session_id

    def test_get_history_returns_sessions(self, client):
        auth = _signup_and_login(client)
        with patch("routes.chat.model", _mock_gemini()):
            client.post("/chat", json={"message": "Hello"}, headers=auth["headers"])
        resp = client.get("/history/", headers=auth["headers"])
        assert resp.status_code == 200
        body = resp.json()
        assert "sessions" in body
        assert len(body["sessions"]) >= 1

    def test_get_history_by_id_returns_messages(self, client):
        auth = _signup_and_login(client)
        with patch("routes.chat.model", _mock_gemini()):
            chat_resp = client.post(
                "/chat",
                json={"message": "I need help with anxiety"},
                headers=auth["headers"],
            )
        session_id = chat_resp.json()["session_id"]
        resp = client.get(f"/history/{session_id}", headers=auth["headers"])
        assert resp.status_code == 200
        messages = resp.json()
        assert len(messages) >= 2  # user message + AI response
        senders = {m["sender"] for m in messages}
        assert "user" in senders
        assert "ai" in senders

    def test_chat_requires_authentication(self, client):
        resp = client.post("/chat", json={"message": "Hello"})
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# 3. Mood flow
# ---------------------------------------------------------------------------

class TestMoodFlow:
    def test_post_mood_entry(self, client):
        auth = _signup_and_login(client)
        resp = client.post(
            "/insights/mood",
            json={"mood_score": 7.0, "energy_level": 6.0, "stress_level": 4.0},
            headers=auth["headers"],
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["mood_score"] == 7.0
        assert body["energy_level"] == 6.0
        assert body["stress_level"] == 4.0

    def test_get_mood_trend(self, client):
        auth = _signup_and_login(client)
        client.post(
            "/insights/mood",
            json={"mood_score": 6.0, "energy_level": 5.0, "stress_level": 5.0},
            headers=auth["headers"],
        )
        resp = client.get("/insights/mood", headers=auth["headers"])
        assert resp.status_code == 200
        entries = resp.json()
        assert isinstance(entries, list)
        assert len(entries) >= 1

    def test_get_mood_analytics(self, client):
        auth = _signup_and_login(client)
        client.post(
            "/insights/mood",
            json={"mood_score": 8.0, "energy_level": 7.0, "stress_level": 3.0},
            headers=auth["headers"],
        )
        resp = client.get("/insights/analytics", headers=auth["headers"])
        assert resp.status_code == 200
        body = resp.json()
        assert "avg_mood" in body
        assert "avg_energy" in body
        assert "avg_stress" in body
        assert "trend" in body

    def test_get_dashboard_stats(self, client):
        auth = _signup_and_login(client)
        resp = client.get("/insights/stats", headers=auth["headers"])
        assert resp.status_code == 200
        body = resp.json()
        assert "total_sessions" in body
        assert "mood_score_percent" in body
        assert "day_streak" in body

    def test_mood_requires_authentication(self, client):
        resp = client.post(
            "/insights/mood",
            json={"mood_score": 5.0, "energy_level": 5.0, "stress_level": 5.0},
        )
        assert resp.status_code == 401

    def test_mood_score_out_of_range_returns_422(self, client):
        auth = _signup_and_login(client)
        resp = client.post(
            "/insights/mood",
            json={"mood_score": 11.0, "energy_level": 5.0, "stress_level": 5.0},
            headers=auth["headers"],
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# 4. Export flow
# ---------------------------------------------------------------------------

class TestExportFlow:
    def test_export_json(self, client):
        auth = _signup_and_login(client)
        resp = client.get("/export?format=json", headers=auth["headers"])
        assert resp.status_code == 200
        body = resp.json()
        assert "sessions" in body
        assert "moods" in body
        assert "user" in body

    def test_export_csv_returns_zip(self, client):
        auth = _signup_and_login(client)
        resp = client.get("/export?format=csv", headers=auth["headers"])
        assert resp.status_code == 200
        assert "application/zip" in resp.headers["content-type"]
        buf = io.BytesIO(resp.content)
        assert zipfile.is_zipfile(buf)

    def test_export_csv_zip_contains_expected_files(self, client):
        auth = _signup_and_login(client)
        resp = client.get("/export?format=csv", headers=auth["headers"])
        buf = io.BytesIO(resp.content)
        with zipfile.ZipFile(buf) as zf:
            names = set(zf.namelist())
        assert "sessions.csv" in names
        assert "messages.csv" in names
        assert "moods.csv" in names

    def test_export_requires_authentication(self, client):
        resp = client.get("/export?format=json")
        assert resp.status_code == 401

    def test_export_json_excludes_password(self, client):
        auth = _signup_and_login(client)
        resp = client.get("/export?format=json", headers=auth["headers"])
        raw = resp.text
        assert '"password"' not in raw


# ---------------------------------------------------------------------------
# 5. Session tagging and search flow
# ---------------------------------------------------------------------------

class TestSessionTaggingAndSearch:
    def test_create_session_and_update_tag(self, client):
        auth = _signup_and_login(client)
        with patch("routes.chat.model", _mock_gemini()):
            chat_resp = client.post(
                "/chat",
                json={"message": "I feel overwhelmed at work"},
                headers=auth["headers"],
            )
        assert chat_resp.status_code == 200
        session_id = chat_resp.json()["session_id"]

        update_resp = client.put(
            f"/history/{session_id}",
            json={"tag": "Anxiety"},
            headers=auth["headers"],
        )
        assert update_resp.status_code == 200
        assert update_resp.json()["tag"] == "Anxiety"

    def test_filter_history_by_tag(self, client):
        auth = _signup_and_login(client)
        with patch("routes.chat.model", _mock_gemini()):
            resp1 = client.post("/chat", json={"message": "Feeling anxious"}, headers=auth["headers"])
            resp2 = client.post("/chat", json={"message": "Feeling tired"}, headers=auth["headers"])
        session_id_1 = resp1.json()["session_id"]

        client.put(f"/history/{session_id_1}", json={"tag": "Anxiety"}, headers=auth["headers"])

        history_resp = client.get("/history/?tag=Anxiety", headers=auth["headers"])
        assert history_resp.status_code == 200
        body = history_resp.json()
        sessions = body["sessions"]
        assert len(sessions) >= 1
        for s in sessions:
            assert s["tag"] == "Anxiety"

    def test_search_sessions_by_query(self, client):
        auth = _signup_and_login(client)
        with patch("routes.chat.model", _mock_gemini()):
            client.post(
                "/chat",
                json={"message": "I have been struggling with insomnia"},
                headers=auth["headers"],
            )
        search_resp = client.get("/search?q=insomnia", headers=auth["headers"])
        assert search_resp.status_code == 200
        results = search_resp.json()
        assert isinstance(results, list)
        assert len(results) >= 1

    def test_invalid_tag_returns_422(self, client):
        auth = _signup_and_login(client)
        with patch("routes.chat.model", _mock_gemini()):
            chat_resp = client.post("/chat", json={"message": "Hello"}, headers=auth["headers"])
        session_id = chat_resp.json()["session_id"]
        resp = client.put(
            f"/history/{session_id}",
            json={"tag": "InvalidTag"},
            headers=auth["headers"],
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# 6. Crisis detection flow
# ---------------------------------------------------------------------------

class TestCrisisDetectionFlow:
    def test_crisis_keyword_sets_crisis_detected_true(self, client):
        auth = _signup_and_login(client)
        resp = client.post(
            "/chat",
            json={"message": "I want to kill myself"},
            headers=auth["headers"],
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["crisis_detected"] is True

    def test_crisis_response_includes_emergency_resources(self, client):
        auth = _signup_and_login(client)
        resp = client.post(
            "/chat",
            json={"message": "I want to end my life"},
            headers=auth["headers"],
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["crisis_detected"] is True
        assert body["emergency_resources"] is not None
        assert len(body["emergency_resources"]) >= 1

    def test_normal_message_does_not_trigger_crisis(self, client):
        auth = _signup_and_login(client)
        with patch("routes.chat.model", _mock_gemini()):
            resp = client.post(
                "/chat",
                json={"message": "I feel a bit stressed today"},
                headers=auth["headers"],
            )
        assert resp.status_code == 200
        body = resp.json()
        assert body["crisis_detected"] is False

    def test_crisis_creates_session(self, client):
        auth = _signup_and_login(client)
        resp = client.post(
            "/chat",
            json={"message": "I want to hurt myself"},
            headers=auth["headers"],
        )
        assert resp.status_code == 200
        assert resp.json()["session_id"] is not None


# ---------------------------------------------------------------------------
# 7. Token refresh flow
# ---------------------------------------------------------------------------

class TestTokenRefreshFlow:
    def test_refresh_token_returns_new_access_token(self, client):
        auth = _signup_and_login(client)
        resp = client.post("/auth/refresh", json={"refresh_token": auth["refresh_token"]})
        assert resp.status_code == 200
        body = resp.json()
        assert "token" in body
        assert len(body["token"]) > 0

    def test_new_access_token_is_usable(self, client):
        auth = _signup_and_login(client)
        refresh_resp = client.post("/auth/refresh", json={"refresh_token": auth["refresh_token"]})
        assert refresh_resp.status_code == 200
        new_token = refresh_resp.json()["token"]
        new_headers = {"Authorization": f"Bearer {new_token}"}
        resp = client.get("/history/", headers=new_headers)
        assert resp.status_code == 200

    def test_invalid_refresh_token_returns_401(self, client):
        resp = client.post("/auth/refresh", json={"refresh_token": "invalid_token_xyz"})
        assert resp.status_code == 401

    def test_revoked_refresh_token_returns_401(self, client):
        auth = _signup_and_login(client)
        client.post(
            "/logout",
            json={"refresh_token": auth["refresh_token"]},
            headers=auth["headers"],
        )
        resp = client.post("/auth/refresh", json={"refresh_token": auth["refresh_token"]})
        assert resp.status_code == 401
