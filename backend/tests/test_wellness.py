import os as _os
_os.environ.setdefault("REDIS_ENABLED", "false")

import bcrypt as _bcrypt_compat
import types as _types_compat

if not hasattr(_bcrypt_compat, "__about__"):
    _about = _types_compat.ModuleType("bcrypt.__about__")
    _about.__version__ = _bcrypt_compat.__version__
    _bcrypt_compat.__about__ = _about

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import routes.auth as _auth_routes
from database import Base, get_db
from main import app

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


def setup_module():
    for table in _TABLES:
        table.create(bind=_engine, checkfirst=True)
    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[_auth_routes.get_db] = _override_get_db


def teardown_module():
    app.dependency_overrides.clear()
    for table in reversed(_TABLES):
        table.drop(bind=_engine, checkfirst=True)


def setup_function():
    db = _Session()
    try:
        for table in reversed(_TABLES):
            db.execute(table.delete())
        db.commit()
    finally:
        db.close()


def auth_headers(client: TestClient):
    client.post(
        "/signup",
        json={
            "email": "wellness@example.com",
            "password": "Password123!",
            "name": "Wellness User",
            "username": "wellness_user",
        },
    )
    login = client.post("/login", json={"email": "wellness@example.com", "password": "Password123!"})
    return {"Authorization": f"Bearer {login.json()['token']}"}


def test_safety_plan_round_trip():
    client = TestClient(app, raise_server_exceptions=False)
    headers = auth_headers(client)

    response = client.put(
        "/wellness/safety-plan",
        headers=headers,
        json={
            "warning_signs": ["I isolate"],
            "coping_strategies": ["Box breathing"],
            "trusted_contacts": ["Sam"],
            "professional_contacts": ["Therapist"],
            "safe_environment_steps": ["Go downstairs"],
            "reasons_to_stay": ["My family"],
        },
    )

    assert response.status_code == 200
    assert response.json()["warning_signs"] == ["I isolate"]

    get_response = client.get("/wellness/safety-plan", headers=headers)
    assert get_response.status_code == 200
    assert get_response.json()["reasons_to_stay"] == ["My family"]


def test_journal_create_list_update_delete():
    client = TestClient(app, raise_server_exceptions=False)
    headers = auth_headers(client)

    create = client.post(
        "/wellness/journals",
        headers=headers,
        json={
            "title": "Hard morning",
            "mood_score": 4,
            "thought": "I cannot do this",
            "reframe": "I can do one small thing",
            "next_step": "Drink water",
            "tags": ["stress"],
        },
    )
    assert create.status_code == 200
    journal_id = create.json()["id"]

    listing = client.get("/wellness/journals", headers=headers)
    assert listing.status_code == 200
    assert listing.json()["total"] == 1

    update = client.put(
        f"/wellness/journals/{journal_id}",
        headers=headers,
        json={**create.json(), "title": "Better morning"},
    )
    assert update.status_code == 200
    assert update.json()["title"] == "Better morning"

    delete = client.delete(f"/wellness/journals/{journal_id}", headers=headers)
    assert delete.status_code == 200
    assert client.get("/wellness/journals", headers=headers).json()["total"] == 0
