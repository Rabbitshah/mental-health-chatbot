"""
Integration tests for the mental health chatbot application.

Uses an in-memory SQLite database with FastAPI dependency injection to avoid
touching the real PostgreSQL database. The Gemini model is replaced with a
fake implementation so no external API calls are made.
"""
# ---------------------------------------------------------------------------
# Compatibility patch: bcrypt 4.x+ removed __about__. Must be applied before
# any passlib import.
# ---------------------------------------------------------------------------
import bcrypt as _bcrypt_compat
import types as _types_compat

if not hasattr(_bcrypt_compat, '__about__'):
    _about = _types_compat.ModuleType('bcrypt.__about__')
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

from database import Base, get_db
from main import app
from routes import chat as chat_routes
import routes.auth as _auth_routes

# ---------------------------------------------------------------------------
# In-memory SQLite engine shared across all tests in this module
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


# Only create SQLite-compatible tables (no ARRAY columns)
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
# Fake Gemini model — no network calls
# ---------------------------------------------------------------------------

class FakeGeminiResponse:
    def __init__(self, text):
        self.text = text


class FakeGeminiChat:
    def send_message(self, message):
        return FakeGeminiResponse(f"Support reply: {message}")


class FakeGeminiModel:
    def start_chat(self, history=None):
        return FakeGeminiChat()


# ---------------------------------------------------------------------------
# Module-scoped client fixture
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def client():
    """TestClient backed by an isolated in-memory SQLite database."""
    import sys
    print("FIXTURE: creating tables", file=sys.stderr)
    for table in _TABLES:
        table.create(bind=_engine, checkfirst=True)
    print("FIXTURE: tables created", file=sys.stderr)

    # Override DB dependency
    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[_auth_routes.get_db] = _override_get_db
    print("FIXTURE: overrides set", file=sys.stderr)

    # Replace Gemini model with fake
    original_model = chat_routes.model
    chat_routes.model = FakeGeminiModel()
    print("FIXTURE: model replaced", file=sys.stderr)

    c = TestClient(app, raise_server_exceptions=False)
    print("FIXTURE: client created", file=sys.stderr)
    yield c

    chat_routes.model = original_model
    app.dependency_overrides.clear()

    for table in reversed(_TABLES):
        table.drop(bind=_engine, checkfirst=True)


@pytest.fixture(autouse=True)
def clean_db():
    """Truncate all tables before each test for isolation."""
    yield
    db = _Session()
    try:
        for table in reversed(_TABLES):
            db.execute(table.delete())
        db.commit()
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def signup_and_login(client):
    signup = client.post(
        "/signup",
        json={
            "email": "test@example.com",
            "password": "Password123!",
            "name": "Test User",
            "username": "test_user",
        },
    )
    assert signup.status_code == 200, f"Signup failed: {signup.text}"

    login = client.post(
        "/login",
        json={"email": "test@example.com", "password": "Password123!"},
    )
    assert login.status_code == 200, f"Login failed: {login.text}"
    token = login.json()["token"]
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestAuthFlow:
    def test_auth_flow(self, client):
        import sys
        print("TEST: starting", file=sys.stderr)
        headers = signup_and_login(client)
        print("TEST: signup_and_login done", file=sys.stderr)

        profile_response = client.put(
            "/profile",
            json={
                "name": "Updated User",
                "email": "updated@example.com",
                "current_password": "Password123!",
            },
            headers=headers,
        )
        print("TEST: profile_response done", file=sys.stderr)

        assert profile_response.status_code == 200
        body = profile_response.json()
        assert body["user"]["name"] == "Updated User"
        assert body["user"]["email"] == "updated@example.com"
        print("TEST: done", file=sys.stderr)

    def test_preference_persistence_flow(self, client):
        headers = signup_and_login(client)

        preference_response = client.put(
            "/profile",
            json={
                "dark_mode": True,
                "email_notifications": False,
                "push_notifications": False,
                "language": "Spanish",
            },
            headers=headers,
        )

        assert preference_response.status_code == 200
        user = preference_response.json()["user"]
        assert user["dark_mode"] is True
        assert user["email_notifications"] is False
        assert user["push_notifications"] is False
        assert user["language"] == "Spanish"

        privacy_summary = client.get("/privacy-summary", headers=headers)
        assert privacy_summary.status_code == 200
        assert privacy_summary.json()["preferences"]["dark_mode"] is True


class TestChatAndHistory:
    def test_chat_and_history_flow(self, client):
        headers = signup_and_login(client)

        chat_response = client.post(
            "/chat",
            json={"message": "I feel anxious about work lately."},
            headers=headers,
        )
        assert chat_response.status_code == 200
        chat_body = chat_response.json()
        assert "Support reply" in chat_body["response"]
        session_id = chat_body["session_id"]

        history_response = client.get("/history/", headers=headers)
        assert history_response.status_code == 200
        sessions = history_response.json()["sessions"]
        assert len(sessions) == 1
        assert sessions[0]["tag"] == "Anxiety"
        assert sessions[0]["title"] == "Work Anxiety Support"

        messages_response = client.get(f"/history/{session_id}", headers=headers)
        assert messages_response.status_code == 200
        messages = messages_response.json()
        assert len(messages) == 2
        assert messages[0]["sender"] == "user"
        assert messages[1]["sender"] == "ai"

    def test_chat_title_generation_for_general_topics(self, client):
        headers = signup_and_login(client)

        response = client.post(
            "/chat",
            json={"message": "I keep overthinking conversations and confidence at social events lately."},
            headers=headers,
        )
        assert response.status_code == 200

        history_response = client.get("/history/", headers=headers)
        assert history_response.status_code == 200
        sessions = history_response.json()["sessions"]
        assert len(sessions) == 1
        assert sessions[0]["title"] == "Overthinking Conversations Confidence"

    def test_history_management_flow(self, client):
        headers = signup_and_login(client)

        first_chat = client.post(
            "/chat",
            json={"message": "I need help with my goals."},
            headers=headers,
        )
        second_chat = client.post(
            "/chat",
            json={"message": "My sleep has been difficult."},
            headers=headers,
        )
        first_session_id = first_chat.json()["session_id"]
        second_session_id = second_chat.json()["session_id"]

        rename_response = client.put(
            f"/history/{first_session_id}",
            json={"title": "Goals Session"},
            headers=headers,
        )
        assert rename_response.status_code == 200
        assert rename_response.json()["title"] == "Goals Session"

        delete_one_response = client.delete(
            f"/history/{second_session_id}",
            headers=headers,
        )
        assert delete_one_response.status_code == 200

        delete_all_response = client.delete("/history/", headers=headers)
        assert delete_all_response.status_code == 200
        assert delete_all_response.json()["message"] == "All conversation history deleted successfully"

    def test_history_search_flow(self, client):
        headers = signup_and_login(client)

        client.post(
            "/chat",
            json={"message": "I feel anxious about an upcoming presentation."},
            headers=headers,
        )
        client.post(
            "/chat",
            json={"message": "My relationship has been feeling distant lately."},
            headers=headers,
        )

        anxiety_search = client.get("/history/?q=anxious", headers=headers)
        assert anxiety_search.status_code == 200
        anxiety_sessions = anxiety_search.json()["sessions"]
        assert len(anxiety_sessions) == 1
        assert anxiety_sessions[0]["tag"] == "Anxiety"

        relationship_search = client.get("/history/?q=relationship", headers=headers)
        assert relationship_search.status_code == 200
        relationship_sessions = relationship_search.json()["sessions"]
        assert len(relationship_sessions) == 1
        assert relationship_sessions[0]["tag"] == "Relationships"

    def test_history_bulk_delete_flow(self, client):
        headers = signup_and_login(client)

        first_chat = client.post(
            "/chat",
            json={"message": "I feel anxious about work lately."},
            headers=headers,
        )
        second_chat = client.post(
            "/chat",
            json={"message": "My relationship has been feeling distant lately."},
            headers=headers,
        )
        third_chat = client.post(
            "/chat",
            json={"message": "I want to reflect on my week."},
            headers=headers,
        )

        bulk_delete_response = client.request(
            "DELETE",
            "/history/bulk",
            json={
                "session_ids": [
                    first_chat.json()["session_id"],
                    second_chat.json()["session_id"],
                ]
            },
            headers=headers,
        )
        assert bulk_delete_response.status_code == 200
        assert bulk_delete_response.json()["deleted_sessions"] == 2

        remaining_history = client.get("/history/", headers=headers)
        assert remaining_history.status_code == 200
        remaining_sessions = remaining_history.json()["sessions"]
        assert len(remaining_sessions) == 1
        assert remaining_sessions[0]["id"] == third_chat.json()["session_id"]

    def test_history_status_flow(self, client):
        headers = signup_and_login(client)

        first_chat = client.post(
            "/chat",
            json={"message": "I feel anxious about work lately."},
            headers=headers,
        )
        second_chat = client.post(
            "/chat",
            json={"message": "My relationship has been feeling distant lately."},
            headers=headers,
        )

        first_session_id = first_chat.json()["session_id"]
        second_session_id = second_chat.json()["session_id"]

        pin_response = client.patch(
            f"/history/{second_session_id}/status",
            json={"is_pinned": True},
            headers=headers,
        )
        assert pin_response.status_code == 200
        assert pin_response.json()["is_pinned"] is True

        archive_response = client.patch(
            f"/history/{first_session_id}/status",
            json={"is_archived": True},
            headers=headers,
        )
        assert archive_response.status_code == 200
        assert archive_response.json()["is_archived"] is True
        assert archive_response.json()["is_pinned"] is False

        active_history = client.get("/history/", headers=headers)
        assert active_history.status_code == 200
        active_sessions = active_history.json()["sessions"]
        assert len(active_sessions) == 1
        assert active_sessions[0]["id"] == second_session_id
        assert active_sessions[0]["is_pinned"] is True

        archived_history = client.get("/history/?include_archived=true", headers=headers)
        assert archived_history.status_code == 200
        archived_sessions = archived_history.json()["sessions"]
        assert len(archived_sessions) == 2
        assert any(session["is_archived"] for session in archived_sessions)


class TestExportAndInsights:
    def test_export_data_includes_preferences_and_session_metadata(self, client):
        headers = signup_and_login(client)

        preference_response = client.put(
            "/profile",
            json={
                "dark_mode": True,
                "email_notifications": False,
                "push_notifications": True,
                "language": "French",
            },
            headers=headers,
        )
        assert preference_response.status_code == 200

        chat_response = client.post(
            "/chat",
            json={"message": "I feel anxious about work lately."},
            headers=headers,
        )
        session_id = chat_response.json()["session_id"]

        status_response = client.patch(
            f"/history/{session_id}/status",
            json={"is_pinned": True},
            headers=headers,
        )
        assert status_response.status_code == 200

        export_response = client.get("/export", headers=headers)
        assert export_response.status_code == 200
        export_data = export_response.json()
        assert export_data["user"]["preferences"]["dark_mode"] is True
        assert export_data["user"]["preferences"]["language"] == "French"
        assert len(export_data["sessions"]) == 1
        assert export_data["sessions"][0]["is_pinned"] is True

    def test_insights_flow(self, client):
        headers = signup_and_login(client)

        for payload in [
            {"mood_score": 7, "energy_level": 6, "stress_level": 4},
            {"mood_score": 8, "energy_level": 7, "stress_level": 3},
            {"mood_score": 6, "energy_level": 5, "stress_level": 5},
        ]:
            response = client.post("/insights/mood", json=payload, headers=headers)
            assert response.status_code == 200

        client.post(
            "/chat",
            json={"message": "I feel stress at work and some anxiety."},
            headers=headers,
        )

        stats_response = client.get("/insights/stats", headers=headers)
        assert stats_response.status_code == 200
        assert "total_sessions" in stats_response.json()

        summary_response = client.get("/insights/summary?days=7", headers=headers)
        assert summary_response.status_code == 200
        assert len(summary_response.json()["insights"]) == 4

        topics_response = client.get("/insights/topics", headers=headers)
        assert topics_response.status_code == 200
        assert len(topics_response.json()["topics"]) >= 1

        patterns_response = client.get("/insights/patterns?days=7", headers=headers)
        assert patterns_response.status_code == 200
        assert "current_streak" in patterns_response.json()
        assert "correlations" in patterns_response.json()

        achievements_response = client.get("/insights/achievements", headers=headers)
        assert achievements_response.status_code == 200
        assert len(achievements_response.json()["achievements"]) == 4
