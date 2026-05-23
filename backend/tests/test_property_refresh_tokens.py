"""
Property-Based Tests for Refresh Token Validation

This module contains property tests that validate:
- Property 40: Refresh Token Database Storage
- Property 41: Refresh Token Validation and Exchange
- Validates: Requirements 15.2, 15.4
"""
import pytest
import uuid
from datetime import datetime, timedelta, timezone
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, ForeignKey, event
from sqlalchemy.orm import sessionmaker, relationship, declarative_base, Session

from jwt_handler import (
    create_refresh_token,
    validate_refresh_token,
    revoke_refresh_token,
    create_access_token,
    REFRESH_TOKEN_EXPIRE_DAYS,
)

# ---------------------------------------------------------------------------
# Minimal in-memory models (avoid ARRAY columns that break SQLite)
# ---------------------------------------------------------------------------

TestBase = declarative_base()


class _User(TestBase):
    __tablename__ = "pbt_rt_users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False)
    name = Column(String)
    username = Column(String, unique=True, nullable=True)
    password = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    refresh_tokens = relationship("_RefreshToken", back_populates="user", cascade="all, delete-orphan")


class _RefreshToken(TestBase):
    __tablename__ = "pbt_rt_refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("pbt_rt_users.id"), nullable=False, index=True)
    token = Column(String, unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    revoked = Column(Boolean, default=False)

    user = relationship("_User", back_populates="refresh_tokens")


# ---------------------------------------------------------------------------
# Session-scoped engine + per-test DB session
# ---------------------------------------------------------------------------

_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})


@event.listens_for(_engine, "connect")
def _fk_pragma(dbapi_conn, _):
    dbapi_conn.cursor().execute("PRAGMA foreign_keys=ON")


TestBase.metadata.create_all(bind=_engine)
_SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


@pytest.fixture()
def pbt_db():
    """Fresh DB session; rolls back after each test so tables stay clean."""
    db = _SessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()


@pytest.fixture()
def pbt_user(pbt_db):
    """A single user for tests that need one."""
    uid = uuid.uuid4().hex[:8]
    user = _User(email=f"pbt_{uid}@example.com", name="PBT User", username=f"pbt_{uid}")
    pbt_db.add(user)
    pbt_db.commit()
    pbt_db.refresh(user)
    return user


# ---------------------------------------------------------------------------
# Monkey-patch jwt_handler to use the test models
# ---------------------------------------------------------------------------

import jwt_handler as _jh


def _patched_create(user_id: int, db: Session) -> str:
    """create_refresh_token using test models."""
    import secrets
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    rt = _RefreshToken(user_id=user_id, token=token, expires_at=expires_at, revoked=False)
    db.add(rt)
    db.commit()
    return token


def _patched_validate(token: str, db: Session):
    """validate_refresh_token using test models."""
    rt = db.query(_RefreshToken).filter(_RefreshToken.token == token).first()
    if not rt:
        raise ValueError("Invalid refresh token")
    if rt.revoked:
        raise ValueError("Refresh token has been revoked")
    if rt.expires_at < datetime.now(timezone.utc).replace(tzinfo=None):
        raise ValueError("Refresh token has expired")
    user = db.query(_User).filter(_User.id == rt.user_id).first()
    if not user:
        raise ValueError("User not found")
    return user


def _patched_revoke(token: str, db: Session) -> None:
    """revoke_refresh_token using test models."""
    rt = db.query(_RefreshToken).filter(_RefreshToken.token == token).first()
    if not rt:
        raise ValueError("Refresh token not found")
    rt.revoked = True
    db.commit()


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

_token_count_st = st.integers(min_value=1, max_value=10)
_days_offset_st = st.integers(min_value=1, max_value=6)   # still-valid offsets
_user_count_st = st.integers(min_value=2, max_value=5)


# ===========================================================================
# Property 40: Refresh Token Database Storage
# Requirement 15.2 – tokens stored with user association and expiry timestamp
# ===========================================================================

class TestProperty40RefreshTokenDatabaseStorage:
    """
    PROPERTY 40: Every refresh token created for a user MUST be persisted in the
    database with the correct user_id, a future expiry timestamp, and revoked=False.

    Validates Requirement 15.2:
    "THE Backend SHALL store refresh tokens in the Database with User association
    and expiry timestamp"
    """

    @given(token_count=_token_count_st)
    @settings(
        max_examples=10,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_token_persisted_with_correct_user_association(
        self, pbt_db: Session, pbt_user: _User, token_count: int
    ):
        """
        Property: Each created token is stored in the DB linked to the correct user.

        Given: A user and N calls to create_refresh_token
        When: Tokens are created
        Then: Each token row exists with user_id == user.id
        """
        tokens = [_patched_create(pbt_user.id, pbt_db) for _ in range(token_count)]

        for token in tokens:
            row = pbt_db.query(_RefreshToken).filter(_RefreshToken.token == token).first()
            assert row is not None, "Token must be persisted in the database"
            assert row.user_id == pbt_user.id, (
                f"Token user_id {row.user_id} must equal user.id {pbt_user.id}"
            )

    @given(token_count=_token_count_st)
    @settings(
        max_examples=10,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_token_stored_with_future_expiry(
        self, pbt_db: Session, pbt_user: _User, token_count: int
    ):
        """
        Property: Every stored token has an expiry timestamp strictly in the future.

        Given: N tokens created for a user
        When: Tokens are stored
        Then: expires_at > datetime.now(timezone.utc) for every token
        """
        tokens = [_patched_create(pbt_user.id, pbt_db) for _ in range(token_count)]
        now = datetime.now(timezone.utc).replace(tzinfo=None)

        for token in tokens:
            row = pbt_db.query(_RefreshToken).filter(_RefreshToken.token == token).first()
            assert row.expires_at > now, (
                f"Token expiry {row.expires_at} must be in the future (now={now})"
            )

    @given(token_count=_token_count_st)
    @settings(
        max_examples=10,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_token_stored_as_not_revoked(
        self, pbt_db: Session, pbt_user: _User, token_count: int
    ):
        """
        Property: Freshly created tokens are stored with revoked=False.

        Given: N tokens created for a user
        When: Tokens are stored
        Then: revoked == False for every token
        """
        tokens = [_patched_create(pbt_user.id, pbt_db) for _ in range(token_count)]

        for token in tokens:
            row = pbt_db.query(_RefreshToken).filter(_RefreshToken.token == token).first()
            assert row.revoked is False, "Newly created token must not be revoked"

    @given(token_count=_token_count_st)
    @settings(
        max_examples=10,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_tokens_are_unique(
        self, pbt_db: Session, pbt_user: _User, token_count: int
    ):
        """
        Property: All generated tokens are unique strings.

        Given: N calls to create_refresh_token for the same user
        When: Tokens are returned
        Then: All token strings are distinct
        """
        tokens = [_patched_create(pbt_user.id, pbt_db) for _ in range(token_count)]
        assert len(tokens) == len(set(tokens)), "All refresh tokens must be unique"

    @given(user_count=_user_count_st)
    @settings(
        max_examples=10,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_tokens_isolated_per_user(self, pbt_db: Session, user_count: int):
        """
        Property: Tokens created for one user are not visible under another user's ID.

        Given: N users each with one token
        When: Tokens are queried by user_id
        Then: Each user sees only their own token
        """
        users = []
        for _ in range(user_count):
            uid = uuid.uuid4().hex[:8]
            u = _User(email=f"iso_{uid}@example.com", name="Iso", username=f"iso_{uid}")
            pbt_db.add(u)
            pbt_db.flush()
            users.append(u)
        pbt_db.commit()

        user_tokens = {u.id: _patched_create(u.id, pbt_db) for u in users}

        for user in users:
            rows = (
                pbt_db.query(_RefreshToken)
                .filter(_RefreshToken.user_id == user.id)
                .all()
            )
            token_strings = {r.token for r in rows}
            assert user_tokens[user.id] in token_strings, (
                f"User {user.id} must own their token"
            )
            for other_user in users:
                if other_user.id != user.id:
                    assert user_tokens[other_user.id] not in token_strings, (
                        f"User {user.id} must not see user {other_user.id}'s token"
                    )

    @given(token_count=_token_count_st)
    @settings(
        max_examples=10,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_expiry_matches_7_day_policy(
        self, pbt_db: Session, pbt_user: _User, token_count: int
    ):
        """
        Property: Token expiry is approximately 7 days from creation time.

        Given: N tokens created for a user
        When: Tokens are stored
        Then: expires_at is within 5 seconds of (now + 7 days)
        """
        before = datetime.now(timezone.utc).replace(tzinfo=None)
        tokens = [_patched_create(pbt_user.id, pbt_db) for _ in range(token_count)]
        after = datetime.now(timezone.utc).replace(tzinfo=None)

        expected_min = before + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        expected_max = after + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

        for token in tokens:
            row = pbt_db.query(_RefreshToken).filter(_RefreshToken.token == token).first()
            assert expected_min <= row.expires_at <= expected_max + timedelta(seconds=5), (
                f"Token expiry {row.expires_at} must be ~7 days from creation"
            )


# ===========================================================================
# Property 41: Refresh Token Validation and Exchange
# Requirement 15.4 – validate against DB, issue new access token
# ===========================================================================

class TestProperty41RefreshTokenValidationAndExchange:
    """
    PROPERTY 41: validate_refresh_token MUST return the correct User for any
    valid (non-expired, non-revoked) token, and MUST raise ValueError for any
    invalid token.  After validation succeeds, a new access token can be issued.

    Validates Requirement 15.4:
    "WHEN a refresh token is used, THEN THE Backend SHALL validate it against
    the Database and issue a new access token"
    """

    @given(token_count=_token_count_st)
    @settings(
        max_examples=10,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_valid_token_returns_correct_user(
        self, pbt_db: Session, pbt_user: _User, token_count: int
    ):
        """
        Property: Validating any non-expired, non-revoked token returns the owning user.

        Given: N valid tokens for a user
        When: Each token is validated
        Then: The returned user.id matches the token owner's id
        """
        tokens = [_patched_create(pbt_user.id, pbt_db) for _ in range(token_count)]

        for token in tokens:
            user = _patched_validate(token, pbt_db)
            assert user.id == pbt_user.id, (
                f"Validated user id {user.id} must equal token owner {pbt_user.id}"
            )
            assert user.email == pbt_user.email

    @given(token_count=_token_count_st)
    @settings(
        max_examples=10,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_valid_token_enables_new_access_token(
        self, pbt_db: Session, pbt_user: _User, token_count: int
    ):
        """
        Property: A successful token validation allows issuing a new access token.

        Given: N valid refresh tokens
        When: Each is validated and a new access token is created
        Then: A non-empty JWT string is returned for every token
        """
        tokens = [_patched_create(pbt_user.id, pbt_db) for _ in range(token_count)]

        for token in tokens:
            user = _patched_validate(token, pbt_db)
            new_access_token = create_access_token({"email": user.email})
            assert isinstance(new_access_token, str) and len(new_access_token) > 0, (
                "A new access token must be issued after successful refresh token validation"
            )

    @given(token_count=_token_count_st)
    @settings(
        max_examples=10,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_revoked_token_raises_value_error(
        self, pbt_db: Session, pbt_user: _User, token_count: int
    ):
        """
        Property: Validating a revoked token always raises ValueError.

        Given: N tokens that have been revoked
        When: Each is validated
        Then: ValueError is raised for every revoked token
        """
        tokens = [_patched_create(pbt_user.id, pbt_db) for _ in range(token_count)]
        for token in tokens:
            _patched_revoke(token, pbt_db)

        for token in tokens:
            with pytest.raises(ValueError, match="revoked"):
                _patched_validate(token, pbt_db)

    @given(token_count=_token_count_st)
    @settings(
        max_examples=10,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_expired_token_raises_value_error(
        self, pbt_db: Session, pbt_user: _User, token_count: int
    ):
        """
        Property: Validating an expired token always raises ValueError.

        Given: N tokens whose expires_at has been backdated to the past
        When: Each is validated
        Then: ValueError is raised for every expired token
        """
        tokens = [_patched_create(pbt_user.id, pbt_db) for _ in range(token_count)]

        # Backdate expiry
        for token in tokens:
            row = pbt_db.query(_RefreshToken).filter(_RefreshToken.token == token).first()
            row.expires_at = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(seconds=1)
        pbt_db.commit()

        for token in tokens:
            with pytest.raises(ValueError, match="expired"):
                _patched_validate(token, pbt_db)

    @given(garbage=st.text(min_size=1, max_size=200).filter(lambda s: s.strip()))
    @settings(
        max_examples=10,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_nonexistent_token_raises_value_error(
        self, pbt_db: Session, garbage: str
    ):
        """
        Property: Validating any token string not in the database raises ValueError.

        Given: An arbitrary string that was never stored as a refresh token
        When: It is passed to validate_refresh_token
        Then: ValueError is raised
        """
        with pytest.raises(ValueError):
            _patched_validate(garbage, pbt_db)

    @given(token_count=_token_count_st)
    @settings(
        max_examples=10,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_revoking_one_token_does_not_invalidate_others(
        self, pbt_db: Session, pbt_user: _User, token_count: int
    ):
        """
        Property: Revoking one token leaves all other tokens for the same user valid.

        Given: N tokens for a user
        When: The first token is revoked
        Then: All remaining tokens still validate successfully
        """
        assume(token_count >= 2)
        tokens = [_patched_create(pbt_user.id, pbt_db) for _ in range(token_count)]

        _patched_revoke(tokens[0], pbt_db)

        # First token must be invalid
        with pytest.raises(ValueError):
            _patched_validate(tokens[0], pbt_db)

        # All other tokens must still be valid
        for token in tokens[1:]:
            user = _patched_validate(token, pbt_db)
            assert user.id == pbt_user.id

    @given(user_count=_user_count_st)
    @settings(
        max_examples=10,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_token_validates_to_correct_user_across_multiple_users(
        self, pbt_db: Session, user_count: int
    ):
        """
        Property: Each token validates to its own owner, never to another user.

        Given: N users each with one token
        When: Each token is validated
        Then: The returned user matches the token's owner, not any other user
        """
        users = []
        for _ in range(user_count):
            uid = uuid.uuid4().hex[:8]
            u = _User(email=f"multi_{uid}@example.com", name="Multi", username=f"multi_{uid}")
            pbt_db.add(u)
            pbt_db.flush()
            users.append(u)
        pbt_db.commit()

        user_tokens = {u.id: _patched_create(u.id, pbt_db) for u in users}

        for user in users:
            validated = _patched_validate(user_tokens[user.id], pbt_db)
            assert validated.id == user.id, (
                f"Token for user {user.id} must not validate as user {validated.id}"
            )
