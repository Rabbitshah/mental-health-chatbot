"""
Property-Based Tests for Authentication Token Validation

This module contains property tests that validate:
- Property 1: Authentication Token Validation
- Property 2: Authenticated Request Processing
- Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5
"""
import pytest
import uuid
from datetime import datetime, timedelta, timezone
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from jose import jwt, JWTError
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, ForeignKey, event
from sqlalchemy.orm import sessionmaker, relationship, declarative_base, Session

from jwt_handler import (
    create_access_token,
    decode_token,
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)

# ---------------------------------------------------------------------------
# Minimal in-memory models (SQLite-compatible, no ARRAY columns)
# ---------------------------------------------------------------------------

TestBase = declarative_base()


class _User(TestBase):
    __tablename__ = "pbt_auth_users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False)
    name = Column(String)
    username = Column(String, unique=True, nullable=True)
    password = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


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
    """A single persisted user for tests that need one."""
    uid = uuid.uuid4().hex[:8]
    user = _User(
        email=f"pbt_auth_{uid}@example.com",
        name="PBT Auth User",
        username=f"pbt_auth_{uid}",
    )
    pbt_db.add(user)
    pbt_db.commit()
    pbt_db.refresh(user)
    return user


# ---------------------------------------------------------------------------
# Helper: simulate get_current_user dependency logic
# ---------------------------------------------------------------------------

def _extract_user_from_token(token: str, db: Session) -> _User:
    """
    Mirrors the logic in dependencies.get_current_user:
    1. Decode the JWT
    2. Extract email claim
    3. Look up user in DB
    Raises ValueError on any failure (maps to 401 in production).
    """
    try:
        payload = decode_token(token)
    except JWTError:
        raise ValueError("Could not validate credentials")

    email = payload.get("email")
    if email is None:
        raise ValueError("Could not validate credentials")

    user = db.query(_User).filter(_User.email == email).first()
    if user is None:
        raise ValueError("Could not validate credentials")

    return user


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

_email_st = st.emails()
_garbage_token_st = st.text(min_size=1, max_size=300).filter(
    lambda s: s.strip() and not s.startswith("eyJ")
)
_user_count_st = st.integers(min_value=2, max_value=6)


# ===========================================================================
# Property 1: Authentication Token Validation
# Requirements 1.1, 1.3, 1.4, 1.5
# ===========================================================================

class TestProperty1AuthenticationTokenValidation:
    """
    PROPERTY 1: The JWT authentication system MUST accept any structurally valid,
    non-expired token containing a known email claim, and MUST reject any token
    that is expired, malformed, signed with the wrong key, or missing the email
    claim.

    Validates Requirements:
    - 1.1: /chat endpoint requires valid JWT_Token
    - 1.3: Expired JWT_Token → 401
    - 1.4: Backend extracts User identity from JWT_Token
    - 1.5: Invalid/malformed JWT_Token → 401 without processing
    """

    @given(email=_email_st)
    @settings(
        max_examples=10,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_valid_token_with_email_claim_is_accepted(
        self, pbt_db: Session, email: str
    ):
        """
        Property: Any token created with a valid email and not yet expired
        must decode successfully and yield the email claim.

        Given: An arbitrary email address
        When: An access token is created for that email
        Then: decode_token returns a payload containing the same email
        """
        token = create_access_token({"email": email})
        payload = decode_token(token)

        assert payload.get("email") == email, (
            f"Decoded email '{payload.get('email')}' must equal original '{email}'"
        )

    @given(email=_email_st)
    @settings(
        max_examples=10,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_valid_token_contains_future_expiry(self, email: str):
        """
        Property: Every freshly created access token has an expiry strictly
        in the future.

        Given: An arbitrary email
        When: An access token is created
        Then: The 'exp' claim is greater than the current UTC timestamp
        """
        before = datetime.now(timezone.utc)
        token = create_access_token({"email": email})
        payload = decode_token(token)

        exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        assert exp > before, (
            f"Token expiry {exp} must be in the future (created at {before})"
        )

    @given(email=_email_st)
    @settings(
        max_examples=10,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_access_token_expiry_matches_15_minute_policy(self, email: str):
        """
        Property: Access token expiry is approximately ACCESS_TOKEN_EXPIRE_MINUTES
        (15 minutes) from creation time.

        Given: An arbitrary email
        When: An access token is created
        Then: exp ≈ now + 15 minutes (within 5 seconds tolerance)
        """
        before = datetime.now(timezone.utc)
        token = create_access_token({"email": email})
        after = datetime.now(timezone.utc)

        payload = decode_token(token)
        exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)

        # JWT exp is stored as a whole second (floor), so allow 1s slack on the lower bound
        expected_min = before + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES) - timedelta(seconds=1)
        expected_max = after + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES, seconds=5)

        assert expected_min <= exp <= expected_max, (
            f"Token expiry {exp} must be ~{ACCESS_TOKEN_EXPIRE_MINUTES} minutes from creation"
        )

    @given(email=_email_st)
    @settings(
        max_examples=10,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_expired_token_raises_jwt_error(self, email: str):
        """
        Property: Any token whose expiry is in the past MUST be rejected by
        decode_token with a JWTError (maps to 401 in production).

        Validates Requirement 1.3: expired JWT_Token → 401

        Given: An arbitrary email
        When: A token is created with a past expiry
        Then: decode_token raises JWTError
        """
        expired_token = create_access_token(
            {"email": email},
            expires_delta=timedelta(seconds=-1),
        )

        with pytest.raises(JWTError):
            decode_token(expired_token)

    @given(garbage=_garbage_token_st)
    @settings(
        max_examples=10,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_malformed_token_raises_jwt_error(self, garbage: str):
        """
        Property: Any string that is not a valid JWT MUST be rejected by
        decode_token with a JWTError (maps to 401 in production).

        Validates Requirement 1.5: invalid/malformed JWT_Token → 401

        Given: An arbitrary non-JWT string
        When: It is passed to decode_token
        Then: JWTError is raised
        """
        with pytest.raises(JWTError):
            decode_token(garbage)

    @given(email=_email_st)
    @settings(
        max_examples=10,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_token_signed_with_wrong_key_raises_jwt_error(self, email: str):
        """
        Property: A token signed with a different secret key MUST be rejected.

        Validates Requirement 1.5: invalid JWT_Token → 401

        Given: An arbitrary email
        When: A token is signed with a wrong key and decoded with the real key
        Then: JWTError is raised
        """
        wrong_key = "completely_different_secret_key_xyz_987"
        payload = {
            "email": email,
            "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
        }
        tampered_token = jwt.encode(payload, wrong_key, algorithm=ALGORITHM)

        with pytest.raises(JWTError):
            decode_token(tampered_token)

    @given(email=_email_st)
    @settings(
        max_examples=10,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_token_without_email_claim_is_rejected(self, email: str):
        """
        Property: A structurally valid JWT that lacks the 'email' claim MUST
        be treated as invalid by the auth dependency (email is None → 401).

        Validates Requirement 1.5: invalid JWT_Token → 401

        Given: A valid JWT with no email field
        When: The auth dependency extracts the email claim
        Then: The email claim is None, triggering a 401
        """
        # Build a token with no email claim (only exp)
        payload = {"exp": datetime.now(timezone.utc) + timedelta(minutes=15)}
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

        decoded = decode_token(token)
        assert decoded.get("email") is None, (
            "Token without email claim must yield None for the email field"
        )

    @given(email=_email_st)
    @settings(
        max_examples=10,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_tokens_for_different_emails_are_distinct(self, email: str):
        """
        Property: Two tokens created for different emails must not be equal.

        Given: An email and a different email (email + suffix)
        When: Tokens are created for both
        Then: The token strings are different
        """
        other_email = f"other_{email}"
        token1 = create_access_token({"email": email})
        token2 = create_access_token({"email": other_email})

        assert token1 != token2, (
            "Tokens for different emails must be distinct"
        )


# ===========================================================================
# Property 2: Authenticated Request Processing
# Requirements 1.1, 1.2, 1.4
# ===========================================================================

class TestProperty2AuthenticatedRequestProcessing:
    """
    PROPERTY 2: The authentication dependency MUST correctly identify the
    requesting user from a valid JWT, and MUST reject requests with no token,
    an expired token, or a token for an unknown user.

    Validates Requirements:
    - 1.1: Request without valid JWT_Token → 401
    - 1.2: Request with valid JWT_Token → processed, AI response returned
    - 1.4: Backend extracts User identity from JWT_Token for all /chat requests
    """

    @given(user_count=_user_count_st)
    @settings(
        max_examples=10,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_valid_token_resolves_to_correct_user(
        self, pbt_db: Session, user_count: int
    ):
        """
        Property: For any set of users, a token created for user X always
        resolves to user X and never to any other user.

        Validates Requirement 1.4: Backend extracts User identity from JWT_Token

        Given: N users each with their own access token
        When: Each token is resolved via the auth dependency
        Then: The resolved user matches the token's owner
        """
        users = []
        for _ in range(user_count):
            uid = uuid.uuid4().hex[:8]
            u = _User(
                email=f"req_{uid}@example.com",
                name="Req User",
                username=f"req_{uid}",
            )
            pbt_db.add(u)
            pbt_db.flush()
            users.append(u)
        pbt_db.commit()

        user_tokens = {u.id: create_access_token({"email": u.email}) for u in users}

        for user in users:
            resolved = _extract_user_from_token(user_tokens[user.id], pbt_db)
            assert resolved.id == user.id, (
                f"Token for user {user.id} resolved to user {resolved.id}"
            )
            assert resolved.email == user.email

    @given(email=_email_st)
    @settings(
        max_examples=10,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_token_for_unknown_user_raises_value_error(
        self, pbt_db: Session, email: str
    ):
        """
        Property: A structurally valid, non-expired token whose email does not
        correspond to any user in the database MUST be rejected (→ 401).

        Validates Requirement 1.1: unauthorized users cannot consume API resources

        Given: A valid token for an email not in the database
        When: The auth dependency attempts to resolve the user
        Then: ValueError is raised (maps to 401)
        """
        token = create_access_token({"email": email})

        with pytest.raises(ValueError, match="Could not validate credentials"):
            _extract_user_from_token(token, pbt_db)

    @given(email=_email_st)
    @settings(
        max_examples=10,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_expired_token_rejected_before_user_lookup(self, pbt_db: Session, email: str):
        """
        Property: An expired token MUST be rejected at the decode stage,
        before any database lookup occurs (→ 401).

        Validates Requirement 1.3: expired JWT_Token → 401

        Given: A user in the database and an expired token for their email
        When: The auth dependency processes the expired token
        Then: ValueError is raised due to JWTError (not a DB miss)
        """
        uid = uuid.uuid4().hex[:8]
        user = _User(
            email=f"exp_{uid}@example.com",
            name="Exp User",
            username=f"exp_{uid}",
        )
        pbt_db.add(user)
        pbt_db.commit()

        expired_token = create_access_token(
            {"email": user.email},
            expires_delta=timedelta(seconds=-1),
        )

        with pytest.raises(ValueError, match="Could not validate credentials"):
            _extract_user_from_token(expired_token, pbt_db)

    @given(garbage=_garbage_token_st)
    @settings(
        max_examples=10,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_malformed_token_rejected_without_db_lookup(
        self, pbt_db: Session, garbage: str
    ):
        """
        Property: A malformed token string MUST be rejected immediately
        without reaching the database (→ 401).

        Validates Requirement 1.5: invalid/malformed JWT_Token → 401 without processing

        Given: An arbitrary non-JWT string
        When: The auth dependency processes it
        Then: ValueError is raised
        """
        with pytest.raises(ValueError, match="Could not validate credentials"):
            _extract_user_from_token(garbage, pbt_db)

    @given(email=_email_st)
    @settings(
        max_examples=10,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_token_without_email_claim_rejected(self, pbt_db: Session, email: str):
        """
        Property: A valid JWT missing the email claim MUST be rejected (→ 401).

        Validates Requirement 1.5: invalid JWT_Token → 401

        Given: A JWT with no email claim
        When: The auth dependency processes it
        Then: ValueError is raised because email is None
        """
        payload = {"exp": datetime.now(timezone.utc) + timedelta(minutes=15)}
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

        with pytest.raises(ValueError, match="Could not validate credentials"):
            _extract_user_from_token(token, pbt_db)

    @given(email=_email_st)
    @settings(
        max_examples=10,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_valid_token_for_existing_user_succeeds(
        self, pbt_db: Session, email: str
    ):
        """
        Property: A valid, non-expired token for a user that exists in the
        database MUST resolve successfully (→ request processed, Req 1.2).

        Validates Requirement 1.2: valid JWT_Token → request processed

        Given: A user in the database and a valid token for their email
        When: The auth dependency processes the token
        Then: The correct user is returned without error
        """
        uid = uuid.uuid4().hex[:8]
        user = _User(
            email=f"ok_{uid}@example.com",
            name="OK User",
            username=f"ok_{uid}",
        )
        pbt_db.add(user)
        pbt_db.commit()

        token = create_access_token({"email": user.email})
        resolved = _extract_user_from_token(token, pbt_db)

        assert resolved.id == user.id
        assert resolved.email == user.email

    @given(user_count=_user_count_st)
    @settings(
        max_examples=10,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_token_isolation_across_concurrent_users(
        self, pbt_db: Session, user_count: int
    ):
        """
        Property: Tokens are isolated — user A's token never resolves to user B.

        Validates Requirement 1.4: Backend extracts correct User identity

        Given: N users each with a token
        When: Each token is resolved
        Then: No token resolves to a different user's identity
        """
        users = []
        for _ in range(user_count):
            uid = uuid.uuid4().hex[:8]
            u = _User(
                email=f"iso_{uid}@example.com",
                name="Iso User",
                username=f"iso_{uid}",
            )
            pbt_db.add(u)
            pbt_db.flush()
            users.append(u)
        pbt_db.commit()

        tokens = {u.id: create_access_token({"email": u.email}) for u in users}

        for user in users:
            resolved = _extract_user_from_token(tokens[user.id], pbt_db)
            for other in users:
                if other.id != user.id:
                    assert resolved.id != other.id, (
                        f"Token for user {user.id} must not resolve to user {other.id}"
                    )
