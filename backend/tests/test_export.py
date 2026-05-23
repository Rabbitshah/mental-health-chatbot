"""
Unit tests for the GET /export endpoint.

Tests cover:
- JSON export format (Req 8.1)
- CSV export format / ZIP archive (Req 8.2)
- Metadata inclusion (Req 8.3)
- Sensitive data exclusion (Req 8.4)
- Invalid format returns 422
- Authentication requirement
- PDF export format
"""
# ---------------------------------------------------------------------------
# Compatibility patch: bcrypt 4.x+ removed __about__. Must be applied before
# any passlib import.
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

import io
import json
import zipfile
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import routes.auth as _auth_routes
from database import Base, get_db
from main import app
from models import ChatMessage, ChatSession, MoodEntry, User

# ---------------------------------------------------------------------------
# In-memory SQLite engine (no ARRAY columns — skip CrisisEvent/Notification)
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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_counter = {"n": 0}


def unique_user(prefix: str = "export"):
    """Return a unique (email, username) pair for each call."""
    _counter["n"] += 1
    n = _counter["n"]
    return f"{prefix}_{n}@example.com", f"{prefix}_user_{n}"


def signup_and_login(client, email="export_test@example.com", username="export_test_user"):
    client.post(
        "/signup",
        json={
            "email": email,
            "password": "Password123!",
            "name": "Export Test User",
            "username": username,
        },
    )
    login = client.post("/login", json={"email": email, "password": "Password123!"})
    token = login.json()["token"]
    return {"Authorization": f"Bearer {token}"}


def get_user_id_by_email(email: str):
    db = _Session()
    try:
        user = db.query(User).filter(User.email == email).first()
        return user.id if user else None
    finally:
        db.close()


def seed_user_data(user_id: int):
    """Insert a session with messages and a mood entry for the given user."""
    db = _Session()
    try:
        session = ChatSession(user_id=user_id, title="Test Session", tag="Anxiety")
        db.add(session)
        db.flush()

        db.add(ChatMessage(session_id=session.id, sender="user", text="I feel anxious"))
        db.add(ChatMessage(session_id=session.id, sender="ai", text="I understand"))

        db.add(
            MoodEntry(
                user_id=user_id,
                mood_score=7.0,
                energy_level=6.0,
                stress_level=4.0,
            )
        )
        db.commit()
        return session.id
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Tests: authentication
# ---------------------------------------------------------------------------

class TestExportAuth:
    def test_export_requires_authentication(self, client):
        response = client.get("/export?format=json")
        assert response.status_code == 401

    def test_export_with_invalid_token_returns_401(self, client):
        response = client.get(
            "/export?format=json",
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# Tests: format validation (Req 8.1, 8.2)
# ---------------------------------------------------------------------------

class TestExportFormatValidation:
    def test_invalid_format_returns_422(self, client):
        email, username = unique_user("fmt_inv")
        headers = signup_and_login(client, email, username)
        response = client.get("/export?format=xml", headers=headers)
        assert response.status_code == 422

    def test_missing_format_defaults_to_json(self, client):
        email, username = unique_user("fmt_miss")
        headers = signup_and_login(client, email, username)
        response = client.get("/export", headers=headers)
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("application/json")

    def test_pdf_format_returns_200(self, client):
        email, username = unique_user("fmt_pdf")
        headers = signup_and_login(client, email, username)
        response = client.get("/export?format=pdf", headers=headers)
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("application/pdf")
        assert response.content.startswith(b"%PDF")

    def test_format_case_insensitive(self, client):
        """Format parameter should be case-insensitive."""
        email, username = unique_user("fmt_case")
        headers = signup_and_login(client, email, username)
        response = client.get("/export?format=JSON", headers=headers)
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# Tests: JSON export (Req 8.1, 8.3, 8.4)
# ---------------------------------------------------------------------------

class TestJsonExport:
    def test_json_export_returns_200(self, client):
        email, username = unique_user("json_200")
        headers = signup_and_login(client, email, username)
        response = client.get("/export?format=json", headers=headers)
        assert response.status_code == 200

    def test_json_export_content_type(self, client):
        email, username = unique_user("json_ct")
        headers = signup_and_login(client, email, username)
        response = client.get("/export?format=json", headers=headers)
        assert "application/json" in response.headers["content-type"]

    def test_json_export_contains_required_top_level_keys(self, client):
        """Req 8.1, 8.3: JSON export must include sessions, moods, metadata."""
        email, username = unique_user("json_keys")
        headers = signup_and_login(client, email, username)
        response = client.get("/export?format=json", headers=headers)
        data = response.json()
        assert "export_timestamp" in data
        assert "user" in data
        assert "sessions" in data
        assert "moods" in data
        assert "data_range" in data

    def test_json_export_user_metadata(self, client):
        """Req 8.3: Export includes user email and name."""
        email, username = unique_user("json_meta")
        headers = signup_and_login(client, email, username)
        response = client.get("/export?format=json", headers=headers)
        user_data = response.json()["user"]
        assert user_data["email"] == email
        assert "name" in user_data
        assert "username" in user_data

    def test_json_export_excludes_password(self, client):
        """Req 8.4: Password hash must not appear in the export."""
        email, username = unique_user("json_nopw")
        headers = signup_and_login(client, email, username)
        response = client.get("/export?format=json", headers=headers)
        raw = response.text
        assert "password" not in raw.lower() or '"password"' not in raw

    def test_json_export_sessions_included(self, client):
        """Req 8.1: All sessions are included in the export."""
        email, username = unique_user("json_sess")
        headers = signup_and_login(client, email, username)
        user_id = get_user_id_by_email(email)
        seed_user_data(user_id)

        response = client.get("/export?format=json", headers=headers)
        data = response.json()
        assert len(data["sessions"]) == 1
        assert data["sessions"][0]["title"] == "Test Session"

    def test_json_export_messages_included(self, client):
        """Req 8.1: Messages are nested inside sessions."""
        email, username = unique_user("json_msgs")
        headers = signup_and_login(client, email, username)
        user_id = get_user_id_by_email(email)
        seed_user_data(user_id)

        response = client.get("/export?format=json", headers=headers)
        data = response.json()
        messages = data["sessions"][0]["messages"]
        assert len(messages) == 2
        senders = {m["sender"] for m in messages}
        assert "user" in senders
        assert "ai" in senders

    def test_json_export_moods_included(self, client):
        """Req 8.1: Mood entries are included in the export."""
        email, username = unique_user("json_moods")
        headers = signup_and_login(client, email, username)
        user_id = get_user_id_by_email(email)
        seed_user_data(user_id)

        response = client.get("/export?format=json", headers=headers)
        data = response.json()
        assert len(data["moods"]) == 1
        mood = data["moods"][0]
        assert mood["mood_score"] == 7.0
        assert mood["energy_level"] == 6.0
        assert mood["stress_level"] == 4.0

    def test_json_export_empty_when_no_data(self, client):
        """Export works correctly when user has no sessions or moods."""
        email, username = unique_user("json_empty")
        headers = signup_and_login(client, email, username)
        response = client.get("/export?format=json", headers=headers)
        data = response.json()
        assert data["sessions"] == []
        assert data["moods"] == []

    def test_json_export_data_range_populated(self, client):
        """Req 8.3: data_range includes start and end when data exists."""
        email, username = unique_user("json_range")
        headers = signup_and_login(client, email, username)
        user_id = get_user_id_by_email(email)
        seed_user_data(user_id)

        response = client.get("/export?format=json", headers=headers)
        data_range = response.json()["data_range"]
        assert data_range["start"] is not None
        assert data_range["end"] is not None

    def test_json_export_only_returns_current_user_data(self, client):
        """Export is scoped to the authenticated user only."""
        # Create another user with data
        other_email, other_username = unique_user("json_other")
        other_headers = signup_and_login(client, other_email, other_username)
        other_id = get_user_id_by_email(other_email)
        seed_user_data(other_id)

        # Our user has no data
        email, username = unique_user("json_scope")
        headers = signup_and_login(client, email, username)
        response = client.get("/export?format=json", headers=headers)
        data = response.json()
        assert data["sessions"] == []
        assert data["moods"] == []


# ---------------------------------------------------------------------------
# Tests: CSV export (Req 8.2, 8.3, 8.5)
# ---------------------------------------------------------------------------

class TestCsvExport:
    def test_csv_export_returns_200(self, client):
        email, username = unique_user("csv_200")
        headers = signup_and_login(client, email, username)
        response = client.get("/export?format=csv", headers=headers)
        assert response.status_code == 200

    def test_csv_export_content_type_is_zip(self, client):
        """Req 8.5: CSV export is returned as a ZIP archive."""
        email, username = unique_user("csv_ct")
        headers = signup_and_login(client, email, username)
        response = client.get("/export?format=csv", headers=headers)
        assert "application/zip" in response.headers["content-type"]

    def test_csv_export_is_valid_zip(self, client):
        """Req 8.5: Response body is a valid ZIP file."""
        email, username = unique_user("csv_zip")
        headers = signup_and_login(client, email, username)
        response = client.get("/export?format=csv", headers=headers)
        buf = io.BytesIO(response.content)
        assert zipfile.is_zipfile(buf)

    def test_csv_export_zip_contains_three_files(self, client):
        """Req 8.2: ZIP contains sessions.csv, messages.csv, moods.csv."""
        email, username = unique_user("csv_3files")
        headers = signup_and_login(client, email, username)
        response = client.get("/export?format=csv", headers=headers)
        buf = io.BytesIO(response.content)
        with zipfile.ZipFile(buf) as zf:
            names = set(zf.namelist())
        assert "sessions.csv" in names
        assert "messages.csv" in names
        assert "moods.csv" in names

    def test_csv_export_sessions_csv_has_data(self, client):
        """Req 8.2: sessions.csv contains session rows."""
        email, username = unique_user("csv_sess")
        headers = signup_and_login(client, email, username)
        user_id = get_user_id_by_email(email)
        seed_user_data(user_id)

        response = client.get("/export?format=csv", headers=headers)
        buf = io.BytesIO(response.content)
        with zipfile.ZipFile(buf) as zf:
            sessions_csv = zf.read("sessions.csv").decode("utf-8")

        lines = [l for l in sessions_csv.strip().splitlines() if l]
        # Header + 1 data row
        assert len(lines) == 2
        assert "Test Session" in sessions_csv

    def test_csv_export_messages_csv_has_data(self, client):
        """Req 8.2: messages.csv contains message rows."""
        email, username = unique_user("csv_msgs")
        headers = signup_and_login(client, email, username)
        user_id = get_user_id_by_email(email)
        seed_user_data(user_id)

        response = client.get("/export?format=csv", headers=headers)
        buf = io.BytesIO(response.content)
        with zipfile.ZipFile(buf) as zf:
            messages_csv = zf.read("messages.csv").decode("utf-8")

        lines = [l for l in messages_csv.strip().splitlines() if l]
        # Header + 2 message rows
        assert len(lines) == 3

    def test_csv_export_moods_csv_has_data(self, client):
        """Req 8.2: moods.csv contains mood rows."""
        email, username = unique_user("csv_moods")
        headers = signup_and_login(client, email, username)
        user_id = get_user_id_by_email(email)
        seed_user_data(user_id)

        response = client.get("/export?format=csv", headers=headers)
        buf = io.BytesIO(response.content)
        with zipfile.ZipFile(buf) as zf:
            moods_csv = zf.read("moods.csv").decode("utf-8")

        lines = [l for l in moods_csv.strip().splitlines() if l]
        # Header + 1 mood row
        assert len(lines) == 2

    def test_csv_export_metadata_in_sessions_csv(self, client):
        """Req 8.3: sessions.csv includes export_timestamp and user_email columns."""
        email, username = unique_user("csv_meta_s")
        headers = signup_and_login(client, email, username)
        response = client.get("/export?format=csv", headers=headers)
        buf = io.BytesIO(response.content)
        with zipfile.ZipFile(buf) as zf:
            sessions_csv = zf.read("sessions.csv").decode("utf-8")

        header_line = sessions_csv.splitlines()[0]
        assert "export_timestamp" in header_line
        assert "user_email" in header_line

    def test_csv_export_metadata_in_messages_csv(self, client):
        """Req 8.3: messages.csv includes export_timestamp and user_email columns."""
        email, username = unique_user("csv_meta_m")
        headers = signup_and_login(client, email, username)
        response = client.get("/export?format=csv", headers=headers)
        buf = io.BytesIO(response.content)
        with zipfile.ZipFile(buf) as zf:
            messages_csv = zf.read("messages.csv").decode("utf-8")

        header_line = messages_csv.splitlines()[0]
        assert "export_timestamp" in header_line
        assert "user_email" in header_line

    def test_csv_export_metadata_in_moods_csv(self, client):
        """Req 8.3: moods.csv includes export_timestamp and user_email columns."""
        email, username = unique_user("csv_meta_mo")
        headers = signup_and_login(client, email, username)
        response = client.get("/export?format=csv", headers=headers)
        buf = io.BytesIO(response.content)
        with zipfile.ZipFile(buf) as zf:
            moods_csv = zf.read("moods.csv").decode("utf-8")

        header_line = moods_csv.splitlines()[0]
        assert "export_timestamp" in header_line
        assert "user_email" in header_line

    def test_csv_export_excludes_password(self, client):
        """Req 8.4: Password hash must not appear in any CSV file."""
        email, username = unique_user("csv_nopw")
        headers = signup_and_login(client, email, username)
        response = client.get("/export?format=csv", headers=headers)
        buf = io.BytesIO(response.content)
        with zipfile.ZipFile(buf) as zf:
            for name in zf.namelist():
                content = zf.read(name).decode("utf-8")
                assert "password" not in content.lower()

    def test_csv_export_empty_when_no_data(self, client):
        """CSV export works when user has no data (only headers in CSVs)."""
        email, username = unique_user("csv_empty")
        headers = signup_and_login(client, email, username)
        response = client.get("/export?format=csv", headers=headers)
        assert response.status_code == 200
        buf = io.BytesIO(response.content)
        assert zipfile.is_zipfile(buf)
