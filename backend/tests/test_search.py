"""
Unit tests for the GET /search endpoint.

Tests cover:
- Case-insensitive text search (Req 7.1, 7.2)
- Tag filtering (Req 7.3)
- Date range filtering (Req 7.4)
- Combined filters (Req 7.5)
- Message snippet generation with context (Req 7.6)
- Authentication requirement
- Invalid date format handling
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
from datetime import datetime, timedelta, timezone
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from database import Base, get_db
from main import app
import routes.auth as _auth_routes
from models import User, ChatSession, ChatMessage
from routes.search import build_snippet

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


@pytest.fixture(scope="module")
def client():
    for table in _TABLES:
        table.create(bind=_engine, checkfirst=True)

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[_auth_routes.get_db] = _override_get_db

    c = TestClient(app, raise_server_exceptions=False)
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


def signup_and_login(client, email="search_test@example.com", username="search_test_user"):
    """Create a user and return auth headers."""
    client.post(
        "/signup",
        json={
            "email": email,
            "password": "Password123!",
            "name": "Search Test User",
            "username": username,
        },
    )
    login = client.post(
        "/login",
        json={"email": email, "password": "Password123!"},
    )
    token = login.json()["token"]
    return {"Authorization": f"Bearer {token}"}


def get_user_id_by_email(email: str) -> int:
    """Get user ID directly from the test DB."""
    db = _Session()
    try:
        user = db.query(User).filter(User.email == email).first()
        return user.id if user else None
    finally:
        db.close()


def create_test_session(
    user_id: int,
    title: str = "Test Session",
    tag: str = "General",
    messages: list = None,
    created_at: datetime = None,
) -> int:
    """Helper to directly insert a session and messages into the test DB. Returns session ID."""
    db = _Session()
    try:
        session = ChatSession(
            user_id=user_id,
            title=title,
            tag=tag,
            created_at=created_at or datetime.now(timezone.utc).replace(tzinfo=None).replace(tzinfo=None),
            updated_at=created_at or datetime.now(timezone.utc).replace(tzinfo=None).replace(tzinfo=None),
        )
        db.add(session)
        db.flush()

        for msg in (messages or []):
            chat_msg = ChatMessage(
                session_id=session.id,
                sender=msg.get("sender", "user"),
                text=msg["text"],
            )
            db.add(chat_msg)

        db.commit()
        return session.id
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Unit tests for build_snippet helper
# ---------------------------------------------------------------------------

class TestBuildSnippet:
    def test_snippet_includes_matched_text(self):
        text = "I have been feeling very anxious about work lately"
        snippet = build_snippet(text, "anxious")
        assert "anxious" in snippet

    def test_snippet_adds_ellipsis_for_truncated_start(self):
        text = "a" * 100 + "match" + "b" * 100
        snippet = build_snippet(text, "match")
        assert snippet.startswith("...")

    def test_snippet_adds_ellipsis_for_truncated_end(self):
        text = "match" + "b" * 200
        snippet = build_snippet(text, "match")
        assert snippet.endswith("...")

    def test_snippet_no_ellipsis_for_short_text(self):
        text = "short text with match here"
        snippet = build_snippet(text, "match")
        assert not snippet.startswith("...")
        assert not snippet.endswith("...")

    def test_snippet_case_insensitive_match(self):
        text = "I feel ANXIOUS today"
        snippet = build_snippet(text, "anxious")
        assert "ANXIOUS" in snippet

    def test_snippet_fallback_when_no_match(self):
        text = "This text does not contain the query"
        snippet = build_snippet(text, "xyz_not_found")
        assert len(snippet) > 0

    def test_snippet_context_around_match(self):
        text = "This is some context before the word anxious and some context after it too"
        snippet = build_snippet(text, "anxious")
        assert "context before" in snippet
        assert "context after" in snippet


# ---------------------------------------------------------------------------
# Integration tests for GET /search endpoint
# ---------------------------------------------------------------------------

class TestSearchEndpoint:
    def test_search_requires_authentication(self, client):
        """Endpoint must reject unauthenticated requests."""
        response = client.get("/search?q=anxiety")
        assert response.status_code == 401

    def test_search_returns_empty_list_when_no_sessions(self, client):
        """Returns empty list when user has no sessions."""
        headers = signup_and_login(client)
        response = client.get("/search", headers=headers)
        assert response.status_code == 200
        assert response.json() == []

    def test_search_case_insensitive_lowercase_query(self, client):
        """Req 7.2: Case-insensitive search — lowercase query matches uppercase text."""
        headers = signup_and_login(client)
        user_id = get_user_id_by_email("search_test@example.com")
        create_test_session(
            user_id, title="Anxiety Session", tag="Anxiety",
            messages=[{"sender": "user", "text": "I feel ANXIOUS about my job"}],
        )

        response = client.get("/search?q=anxious", headers=headers)
        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_search_case_insensitive_uppercase_query(self, client):
        """Req 7.2: Case-insensitive search — uppercase query matches lowercase text."""
        headers = signup_and_login(client)
        user_id = get_user_id_by_email("search_test@example.com")
        create_test_session(
            user_id, title="Anxiety Session", tag="Anxiety",
            messages=[{"sender": "user", "text": "I feel anxious about my job"}],
        )

        response = client.get("/search?q=ANXIOUS", headers=headers)
        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_search_returns_matching_sessions(self, client):
        """Req 7.1: Returns sessions containing messages that match the query."""
        headers = signup_and_login(client)
        user_id = get_user_id_by_email("search_test@example.com")
        create_test_session(user_id, title="Anxiety Session", tag="Anxiety",
                            messages=[{"sender": "user", "text": "I feel anxious about my presentation"}])
        create_test_session(user_id, title="Happy Session", tag="General",
                            messages=[{"sender": "user", "text": "I had a great day today"}])

        response = client.get("/search?q=anxious", headers=headers)
        assert response.status_code == 200
        results = response.json()
        assert len(results) == 1
        assert results[0]["session_title"] == "Anxiety Session"

    def test_search_excludes_non_matching_sessions(self, client):
        """Req 7.1: Sessions without matching messages are excluded."""
        headers = signup_and_login(client)
        user_id = get_user_id_by_email("search_test@example.com")
        create_test_session(user_id, title="Stress Session", tag="Stress",
                            messages=[{"sender": "user", "text": "I feel stressed about deadlines"}])

        response = client.get("/search?q=anxiety", headers=headers)
        assert response.status_code == 200
        assert len(response.json()) == 0

    def test_search_result_contains_required_fields(self, client):
        """Search results include session_id, session_title, message_snippet, created_at, tag."""
        headers = signup_and_login(client)
        user_id = get_user_id_by_email("search_test@example.com")
        create_test_session(user_id, title="Anxiety Session", tag="Anxiety",
                            messages=[{"sender": "user", "text": "I feel anxious about my job"}])

        response = client.get("/search?q=anxious", headers=headers)
        assert response.status_code == 200
        results = response.json()
        assert len(results) == 1
        result = results[0]
        assert "session_id" in result
        assert "session_title" in result
        assert "message_snippet" in result
        assert "created_at" in result
        assert "tag" in result

    def test_search_snippet_contains_matched_text(self, client):
        """Req 7.6: Message snippet includes the matched text."""
        headers = signup_and_login(client)
        user_id = get_user_id_by_email("search_test@example.com")
        create_test_session(user_id, title="Anxiety Session", tag="Anxiety",
                            messages=[{"sender": "user", "text": "I have been feeling very anxious lately"}])

        response = client.get("/search?q=anxious", headers=headers)
        assert response.status_code == 200
        results = response.json()
        assert len(results) == 1
        snippet = results[0]["message_snippet"]
        assert snippet is not None
        assert "anxious" in snippet.lower()

    def test_search_filter_by_tag(self, client):
        """Req 7.3: Filter by session tag returns only sessions with that tag."""
        headers = signup_and_login(client)
        user_id = get_user_id_by_email("search_test@example.com")
        create_test_session(user_id, title="Anxiety Session", tag="Anxiety",
                            messages=[{"sender": "user", "text": "Feeling anxious"}])
        create_test_session(user_id, title="Sleep Session", tag="Sleep",
                            messages=[{"sender": "user", "text": "Can't sleep"}])

        response = client.get("/search?tag=Anxiety", headers=headers)
        assert response.status_code == 200
        results = response.json()
        assert len(results) == 1
        assert results[0]["tag"] == "Anxiety"

    def test_search_tag_filter_excludes_other_tags(self, client):
        """Req 7.3: Tag filter excludes sessions with different tags."""
        headers = signup_and_login(client)
        user_id = get_user_id_by_email("search_test@example.com")
        create_test_session(user_id, title="Anxiety Session", tag="Anxiety",
                            messages=[{"sender": "user", "text": "Feeling anxious"}])

        response = client.get("/search?tag=Work", headers=headers)
        assert response.status_code == 200
        assert len(response.json()) == 0

    def test_search_no_query_returns_all_sessions(self, client):
        """When no query is provided, all sessions are returned."""
        headers = signup_and_login(client)
        user_id = get_user_id_by_email("search_test@example.com")
        create_test_session(user_id, title="Session 1", messages=[{"sender": "user", "text": "First"}])
        create_test_session(user_id, title="Session 2", messages=[{"sender": "user", "text": "Second"}])

        response = client.get("/search", headers=headers)
        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_search_no_query_snippet_is_null(self, client):
        """When no query is provided, message_snippet is null."""
        headers = signup_and_login(client)
        user_id = get_user_id_by_email("search_test@example.com")
        create_test_session(user_id, title="Session 1", messages=[{"sender": "user", "text": "Some message"}])

        response = client.get("/search", headers=headers)
        assert response.status_code == 200
        results = response.json()
        assert len(results) == 1
        assert results[0]["message_snippet"] is None

    def test_search_date_range_start_filter(self, client):
        """Req 7.4: Filter by start date excludes sessions before that date."""
        headers = signup_and_login(client)
        user_id = get_user_id_by_email("search_test@example.com")
        create_test_session(user_id, title="Old Session",
                            created_at=datetime.now(timezone.utc).replace(tzinfo=None).replace(tzinfo=None) - timedelta(days=5),
                            messages=[{"sender": "user", "text": "Old message"}])

        yesterday = (datetime.now(timezone.utc).replace(tzinfo=None).replace(tzinfo=None) - timedelta(days=1)).isoformat()
        response = client.get(f"/search?start={yesterday}", headers=headers)
        assert response.status_code == 200
        assert len(response.json()) == 0

    def test_search_date_range_end_filter(self, client):
        """Req 7.4: Filter by end date excludes sessions after that date."""
        headers = signup_and_login(client)
        user_id = get_user_id_by_email("search_test@example.com")
        create_test_session(user_id, title="Recent Session",
                            created_at=datetime.now(timezone.utc).replace(tzinfo=None).replace(tzinfo=None),
                            messages=[{"sender": "user", "text": "Recent message"}])

        yesterday = (datetime.now(timezone.utc).replace(tzinfo=None).replace(tzinfo=None) - timedelta(days=1)).isoformat()
        response = client.get(f"/search?end={yesterday}", headers=headers)
        assert response.status_code == 200
        assert len(response.json()) == 0

    def test_search_date_range_includes_current_sessions(self, client):
        """Req 7.4: Date range that includes now returns current sessions."""
        headers = signup_and_login(client)
        user_id = get_user_id_by_email("search_test@example.com")
        create_test_session(user_id, title="Current Session",
                            messages=[{"sender": "user", "text": "A message"}])

        past = (datetime.now(timezone.utc).replace(tzinfo=None).replace(tzinfo=None) - timedelta(days=1)).isoformat()
        future = (datetime.now(timezone.utc).replace(tzinfo=None).replace(tzinfo=None) + timedelta(days=1)).isoformat()
        response = client.get(f"/search?start={past}&end={future}", headers=headers)
        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_search_combined_query_and_tag(self, client):
        """Req 7.5: Combining query and tag filter works correctly."""
        headers = signup_and_login(client)
        user_id = get_user_id_by_email("search_test@example.com")
        create_test_session(user_id, title="Anxiety Session", tag="Anxiety",
                            messages=[{"sender": "user", "text": "I feel anxious about work"}])
        create_test_session(user_id, title="Sleep Session", tag="Sleep",
                            messages=[{"sender": "user", "text": "I feel anxious about sleep"}])

        response = client.get("/search?q=anxious&tag=Anxiety", headers=headers)
        assert response.status_code == 200
        results = response.json()
        assert len(results) == 1
        assert results[0]["tag"] == "Anxiety"
        assert "anxious" in results[0]["message_snippet"].lower()

    def test_search_combined_query_and_date_range(self, client):
        """Req 7.5: Combining query and date range filter works correctly."""
        headers = signup_and_login(client)
        user_id = get_user_id_by_email("search_test@example.com")
        create_test_session(user_id, title="Recent Anxiety",
                            created_at=datetime.now(timezone.utc).replace(tzinfo=None).replace(tzinfo=None),
                            messages=[{"sender": "user", "text": "I feel anxious today"}])
        create_test_session(user_id, title="Old Anxiety",
                            created_at=datetime.now(timezone.utc).replace(tzinfo=None).replace(tzinfo=None) - timedelta(days=10),
                            messages=[{"sender": "user", "text": "I felt anxious last week"}])

        past = (datetime.now(timezone.utc).replace(tzinfo=None).replace(tzinfo=None) - timedelta(days=5)).isoformat()
        future = (datetime.now(timezone.utc).replace(tzinfo=None).replace(tzinfo=None) + timedelta(days=1)).isoformat()
        response = client.get(f"/search?q=anxious&start={past}&end={future}", headers=headers)
        assert response.status_code == 200
        results = response.json()
        assert len(results) == 1
        assert results[0]["session_title"] == "Recent Anxiety"

    def test_search_combined_all_filters(self, client):
        """Req 7.5: Combining query, tag, and date range filter works correctly."""
        headers = signup_and_login(client)
        user_id = get_user_id_by_email("search_test@example.com")
        create_test_session(user_id, title="Recent Anxiety", tag="Anxiety",
                            created_at=datetime.now(timezone.utc).replace(tzinfo=None).replace(tzinfo=None),
                            messages=[{"sender": "user", "text": "I feel anxious today"}])
        create_test_session(user_id, title="Old Anxiety", tag="Anxiety",
                            created_at=datetime.now(timezone.utc).replace(tzinfo=None).replace(tzinfo=None) - timedelta(days=10),
                            messages=[{"sender": "user", "text": "I felt anxious last week"}])
        create_test_session(user_id, title="Recent Sleep", tag="Sleep",
                            created_at=datetime.now(timezone.utc).replace(tzinfo=None).replace(tzinfo=None),
                            messages=[{"sender": "user", "text": "I feel anxious about sleep"}])

        past = (datetime.now(timezone.utc).replace(tzinfo=None).replace(tzinfo=None) - timedelta(days=5)).isoformat()
        future = (datetime.now(timezone.utc).replace(tzinfo=None).replace(tzinfo=None) + timedelta(days=1)).isoformat()
        response = client.get(f"/search?q=anxious&tag=Anxiety&start={past}&end={future}", headers=headers)
        assert response.status_code == 200
        results = response.json()
        assert len(results) == 1
        assert results[0]["session_title"] == "Recent Anxiety"
        assert results[0]["tag"] == "Anxiety"

    def test_search_invalid_start_date_returns_422(self, client):
        """Invalid date format returns 422 error."""
        headers = signup_and_login(client)
        response = client.get("/search?start=not-a-date", headers=headers)
        assert response.status_code == 422

    def test_search_invalid_end_date_returns_422(self, client):
        """Invalid date format returns 422 error."""
        headers = signup_and_login(client)
        response = client.get("/search?end=not-a-date", headers=headers)
        assert response.status_code == 422

    def test_search_only_returns_current_user_sessions(self, client):
        """Search results are scoped to the authenticated user only."""
        headers1 = signup_and_login(client, "user1_search@example.com", "user1_search_test")
        user_id1 = get_user_id_by_email("user1_search@example.com")
        create_test_session(user_id1, title="User1 Session",
                            messages=[{"sender": "user", "text": "User 1 anxious message"}])

        headers2 = signup_and_login(client, "user2_search@example.com", "user2_search_test")

        response = client.get("/search?q=anxious", headers=headers2)
        assert response.status_code == 200
        assert len(response.json()) == 0
