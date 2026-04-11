"""
Unit tests for authentication enhancements (refresh tokens).

Uses the real models and an in-memory SQLite database to avoid mapper conflicts.
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine, event, StaticPool
from sqlalchemy.orm import sessionmaker

from database import Base
from models import User, RefreshToken
from jwt_handler import (
    create_access_token,
    create_refresh_token,
    validate_refresh_token,
    revoke_refresh_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
)

# ---------------------------------------------------------------------------
# Shared in-memory SQLite engine (StaticPool so all sessions share one conn)
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

for table in _TABLES:
    table.create(bind=_engine, checkfirst=True)

_Session = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


@pytest.fixture
def db():
    """Provide a DB session that rolls back after each test."""
    session = _Session()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def test_user(db):
    """Create a test user (no real password hash needed for token tests)."""
    from sqlalchemy import text
    user = User(
        email="enhance_test@example.com",
        name="Test User",
        username="enhance_testuser",
        password="hashed_password_placeholder",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    yield user
    # Cleanup using raw SQL to avoid cascade-loading SQLite-incompatible tables
    for stmt in [
        "DELETE FROM refresh_tokens WHERE user_id = :uid",
        "DELETE FROM chat_messages WHERE session_id IN (SELECT id FROM chat_sessions WHERE user_id = :uid)",
        "DELETE FROM chat_sessions WHERE user_id = :uid",
        "DELETE FROM mood_entries WHERE user_id = :uid",
        "DELETE FROM users WHERE id = :uid",
    ]:
        db.execute(text(stmt), {"uid": user.id})
    db.commit()


class TestAccessToken:
    """Tests for access token functionality."""

    def test_create_access_token(self):
        """Access tokens are created as non-empty strings."""
        token = create_access_token({"email": "test@example.com"})
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_access_token_expiry_is_15_minutes(self):
        """Access token expiry constant is 15 minutes."""
        assert ACCESS_TOKEN_EXPIRE_MINUTES == 15


class TestRefreshToken:
    """Tests for refresh token functionality."""

    def test_create_refresh_token(self, db, test_user):
        """Creating a refresh token stores it in the database."""
        token = create_refresh_token(test_user.id, db)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

        db_token = db.query(RefreshToken).filter(RefreshToken.token == token).first()
        assert db_token is not None
        assert db_token.user_id == test_user.id
        assert db_token.revoked is False
        assert db_token.expires_at > datetime.utcnow()

    def test_refresh_token_expiry_is_7_days(self, db, test_user):
        """Refresh tokens expire in 7 days."""
        token = create_refresh_token(test_user.id, db)

        db_token = db.query(RefreshToken).filter(RefreshToken.token == token).first()
        expected_expiry = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        time_diff = abs((db_token.expires_at - expected_expiry).total_seconds())

        assert time_diff < 5
        assert REFRESH_TOKEN_EXPIRE_DAYS == 7

    def test_validate_refresh_token_success(self, db, test_user):
        """Validating a valid refresh token returns the correct user."""
        token = create_refresh_token(test_user.id, db)
        user = validate_refresh_token(token, db)

        assert user is not None
        assert user.id == test_user.id
        assert user.email == test_user.email

    def test_validate_refresh_token_invalid(self, db):
        """Validating an invalid token raises ValueError."""
        with pytest.raises(ValueError, match="Invalid refresh token"):
            validate_refresh_token("invalid_token_12345", db)

    def test_validate_refresh_token_revoked(self, db, test_user):
        """Validating a revoked token raises ValueError."""
        token = create_refresh_token(test_user.id, db)
        revoke_refresh_token(token, db)

        with pytest.raises(ValueError, match="Refresh token has been revoked"):
            validate_refresh_token(token, db)

    def test_validate_refresh_token_expired(self, db, test_user):
        """Validating an expired token raises ValueError."""
        token = create_refresh_token(test_user.id, db)

        db_token = db.query(RefreshToken).filter(RefreshToken.token == token).first()
        db_token.expires_at = datetime.utcnow() - timedelta(days=1)
        db.commit()

        with pytest.raises(ValueError, match="Refresh token has expired"):
            validate_refresh_token(token, db)

    def test_revoke_refresh_token(self, db, test_user):
        """Revoking a refresh token marks it as revoked in the database."""
        token = create_refresh_token(test_user.id, db)
        revoke_refresh_token(token, db)

        db_token = db.query(RefreshToken).filter(RefreshToken.token == token).first()
        assert db_token.revoked is True

    def test_revoke_nonexistent_token(self, db):
        """Revoking a non-existent token raises ValueError."""
        with pytest.raises(ValueError, match="Refresh token not found"):
            revoke_refresh_token("nonexistent_token", db)

    def test_multiple_refresh_tokens_per_user(self, db, test_user):
        """A user can have multiple independent refresh tokens."""
        token1 = create_refresh_token(test_user.id, db)
        token2 = create_refresh_token(test_user.id, db)

        assert token1 != token2

        user1 = validate_refresh_token(token1, db)
        user2 = validate_refresh_token(token2, db)
        assert user1.id == test_user.id
        assert user2.id == test_user.id

        revoke_refresh_token(token1, db)

        with pytest.raises(ValueError):
            validate_refresh_token(token1, db)

        # token2 should still be valid
        user2 = validate_refresh_token(token2, db)
        assert user2.id == test_user.id
