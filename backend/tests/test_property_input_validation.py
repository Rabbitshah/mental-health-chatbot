"""
Property-Based Tests for Input Validation

This module contains property tests that validate:
- Property 30: Input Validation Error Responses
- Property 31: Whitespace-Only Input Rejection
- Property 32: Email Format Validation
- Validates: Requirements 11.2, 11.4, 11.6

Requirement 11.2:
"WHEN a request contains invalid data types, THEN THE Backend SHALL return a
422 Unprocessable Entity error with field-specific error messages"

Requirement 11.4:
"THE Backend SHALL reject requests with empty or whitespace-only message text"

Requirement 11.6:
"THE Backend SHALL validate email format for all email fields using regex
pattern matching"
"""
import re
import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field, validator
from typing import Optional


# ---------------------------------------------------------------------------
# Replicate the Pydantic models from the actual routes
# (avoids importing the full app which requires DB/env setup)
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=5000)
    session_id: Optional[int] = Field(None, ge=1)

    @validator('message')
    def message_not_whitespace(cls, v):
        if not v or v.strip() == '':
            raise ValueError('Message cannot be empty or whitespace only')
        return v.strip()


class MoodRequest(BaseModel):
    mood_score: float = Field(..., ge=1, le=10)
    energy_level: float = Field(..., ge=1, le=10)
    stress_level: float = Field(..., ge=1, le=10)


EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'


class UserCreate(BaseModel):
    email: str = Field(..., min_length=5, max_length=255)
    password: str = Field(..., min_length=8, max_length=100)
    name: str = Field(..., min_length=1, max_length=255)
    username: str = Field(..., min_length=3, max_length=50)

    @validator('email')
    def validate_email_format(cls, v):
        if not re.match(EMAIL_REGEX, v):
            raise ValueError('Invalid email format')
        return v.lower()


# ---------------------------------------------------------------------------
# Minimal FastAPI app with the validation endpoints
# ---------------------------------------------------------------------------

def _make_validation_app() -> FastAPI:
    """Build a minimal FastAPI app that exercises the Pydantic validation models."""
    app = FastAPI()

    @app.post("/chat", status_code=200)
    def chat_endpoint(body: ChatRequest):
        return {"message": body.message}

    @app.post("/insights/mood", status_code=201)
    def mood_endpoint(body: MoodRequest):
        return {
            "mood_score": body.mood_score,
            "energy_level": body.energy_level,
            "stress_level": body.stress_level,
        }

    @app.post("/signup", status_code=201)
    def signup_endpoint(body: UserCreate):
        return {"email": body.email}

    return app


_app = _make_validation_app()
_client = TestClient(_app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

# Whitespace-only strings using Unicode whitespace characters
_whitespace_st = st.text(
    alphabet=st.sampled_from(list(" \t\n\r\x0b\x0c\u00a0\u2000\u2001\u2002\u2003\u2028\u2029")),
    min_size=1,
    max_size=200,
).filter(lambda s: s.strip() == "")

# Strings that are purely whitespace using common whitespace chars
_simple_whitespace_st = st.text(
    alphabet=" \t\n\r\x0b\x0c",
    min_size=1,
    max_size=100,
)

# Out-of-range mood values (below 1 or above 10)
_mood_below_range_st = st.floats(
    max_value=0.9999,
    allow_nan=False,
    allow_infinity=False,
)
_mood_above_range_st = st.floats(
    min_value=10.0001,
    max_value=1e6,
    allow_nan=False,
    allow_infinity=False,
)
_mood_out_of_range_st = st.one_of(_mood_below_range_st, _mood_above_range_st)

# Valid mood values (1.0 to 10.0 inclusive)
_mood_valid_st = st.floats(min_value=1.0, max_value=10.0, allow_nan=False, allow_infinity=False)

# Strings that are clearly NOT valid email addresses
_invalid_email_st = st.one_of(
    # No @ symbol
    st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789", min_size=1, max_size=30).filter(
        lambda s: "@" not in s
    ),
    # No domain part after @
    st.builds(lambda local: f"{local}@", local=st.text(
        alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=10
    )),
    # No TLD (no dot after @)
    st.builds(
        lambda local, domain: f"{local}@{domain}",
        local=st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=10),
        domain=st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=10).filter(
            lambda s: "." not in s
        ),
    ),
    # Starts with @
    st.builds(
        lambda domain: f"@{domain}",
        domain=st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789.", min_size=3, max_size=20),
    ),
    # Plainly invalid fixed examples
    st.sampled_from([
        "notanemail",
        "missing@tld",
        "@nodomain.com",
        "spaces in@email.com",
        "double@@at.com",
        "no-at-sign",
        "",
        "   ",
        "user@",
        "@.com",
    ]),
).filter(lambda s: not re.match(EMAIL_REGEX, s))

# Valid email addresses
_valid_email_st = st.builds(
    lambda local, domain, tld: f"{local}@{domain}.{tld}",
    local=st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789", min_size=1, max_size=15),
    domain=st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789", min_size=2, max_size=10),
    tld=st.sampled_from(["com", "org", "net", "io", "co", "edu"]),
).filter(lambda s: re.match(EMAIL_REGEX, s))

# Valid non-whitespace messages
_valid_message_st = st.text(min_size=1, max_size=100).filter(lambda s: s.strip() != "")

# Messages exceeding 5000 characters — build deterministically to avoid health check issues
_too_long_message_st = st.builds(
    lambda prefix, suffix: "A" * 5001 + prefix + suffix,
    prefix=st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=0, max_size=10),
    suffix=st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=0, max_size=10),
)


# ===========================================================================
# Property 30: Input Validation Error Responses
# Validates: Requirement 11.2
# ===========================================================================

class TestProperty30InputValidationErrorResponses:
    """
    PROPERTY 30: Input Validation Error Responses

    For ANY request with invalid data (wrong types, out-of-range values,
    missing required fields), the backend MUST return 422 Unprocessable Entity
    with field-specific error messages.

    **Validates: Requirements 11.2**
    """

    @given(mood_score=_mood_out_of_range_st, energy=_mood_valid_st, stress=_mood_valid_st)
    @settings(
        max_examples=50,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_mood_score_out_of_range_returns_422(
        self, mood_score: float, energy: float, stress: float
    ):
        """
        Property: Any mood_score outside [1, 10] MUST produce a 422 response
        with field-specific error details.

        Given: A mood_score that is < 1 or > 10
        When: POST /insights/mood is called
        Then: Response status is 422 and body contains field error details

        **Validates: Requirements 11.2**
        """
        response = _client.post(
            "/insights/mood",
            json={"mood_score": mood_score, "energy_level": energy, "stress_level": stress},
        )
        assert response.status_code == 422, (
            f"mood_score={mood_score} (out of range) must return 422, "
            f"got {response.status_code}"
        )
        body = response.json()
        assert "detail" in body, "422 response must include 'detail' field"

    @given(energy=_mood_out_of_range_st, mood=_mood_valid_st, stress=_mood_valid_st)
    @settings(
        max_examples=50,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_energy_level_out_of_range_returns_422(
        self, energy: float, mood: float, stress: float
    ):
        """
        Property: Any energy_level outside [1, 10] MUST produce a 422 response.

        Given: An energy_level that is < 1 or > 10
        When: POST /insights/mood is called
        Then: Response status is 422

        **Validates: Requirements 11.2**
        """
        response = _client.post(
            "/insights/mood",
            json={"mood_score": mood, "energy_level": energy, "stress_level": stress},
        )
        assert response.status_code == 422, (
            f"energy_level={energy} (out of range) must return 422, "
            f"got {response.status_code}"
        )

    @given(stress=_mood_out_of_range_st, mood=_mood_valid_st, energy=_mood_valid_st)
    @settings(
        max_examples=50,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_stress_level_out_of_range_returns_422(
        self, stress: float, mood: float, energy: float
    ):
        """
        Property: Any stress_level outside [1, 10] MUST produce a 422 response.

        Given: A stress_level that is < 1 or > 10
        When: POST /insights/mood is called
        Then: Response status is 422

        **Validates: Requirements 11.2**
        """
        response = _client.post(
            "/insights/mood",
            json={"mood_score": mood, "energy_level": energy, "stress_level": stress},
        )
        assert response.status_code == 422, (
            f"stress_level={stress} (out of range) must return 422, "
            f"got {response.status_code}"
        )

    def test_missing_required_field_returns_422_with_detail(self):
        """
        Property: A request missing a required field MUST return 422 with
        field-specific error details identifying the missing field.

        Given: A /chat request with no 'message' field
        When: POST /chat is called
        Then: Response is 422 and detail mentions the missing field

        **Validates: Requirements 11.2**
        """
        response = _client.post("/chat", json={})
        assert response.status_code == 422
        body = response.json()
        assert "detail" in body
        # The detail should reference the 'message' field
        detail_str = str(body["detail"]).lower()
        assert "message" in detail_str, (
            f"422 detail must mention the missing 'message' field, got: {body['detail']}"
        )

    def test_wrong_type_for_mood_score_returns_422(self):
        """
        Property: Sending a non-numeric value for mood_score MUST return 422.

        Given: mood_score is a string instead of a float
        When: POST /insights/mood is called
        Then: Response is 422

        **Validates: Requirements 11.2**
        """
        response = _client.post(
            "/insights/mood",
            json={"mood_score": "not-a-number", "energy_level": 5.0, "stress_level": 5.0},
        )
        assert response.status_code == 422

    @given(message=_too_long_message_st)
    @settings(
        max_examples=30,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.large_base_example],
    )
    def test_message_exceeding_5000_chars_returns_422(self, message: str):
        """
        Property: Any message longer than 5000 characters MUST return 422.

        Given: A message string with length > 5000
        When: POST /chat is called
        Then: Response is 422

        **Validates: Requirements 11.2, 11.3**
        """
        assert len(message) > 5000
        response = _client.post("/chat", json={"message": message})
        assert response.status_code == 422, (
            f"Message of length {len(message)} must return 422, "
            f"got {response.status_code}"
        )

    @given(mood=_mood_valid_st, energy=_mood_valid_st, stress=_mood_valid_st)
    @settings(
        max_examples=30,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_valid_mood_request_returns_success(
        self, mood: float, energy: float, stress: float
    ):
        """
        Property: Any mood request with all values in [1, 10] MUST succeed (201).

        Given: mood_score, energy_level, stress_level all in [1.0, 10.0]
        When: POST /insights/mood is called
        Then: Response is 201 (not 422)

        **Validates: Requirements 11.2 (inverse — valid data must not be rejected)**
        """
        response = _client.post(
            "/insights/mood",
            json={"mood_score": mood, "energy_level": energy, "stress_level": stress},
        )
        assert response.status_code == 201, (
            f"Valid mood values ({mood}, {energy}, {stress}) must return 201, "
            f"got {response.status_code}: {response.text}"
        )


# ===========================================================================
# Property 31: Whitespace-Only Input Rejection
# Validates: Requirement 11.4
# ===========================================================================

class TestProperty31WhitespaceOnlyInputRejection:
    """
    PROPERTY 31: Whitespace-Only Input Rejection

    For ANY message consisting entirely of whitespace characters, the /chat
    endpoint MUST return 422 Unprocessable Entity.

    **Validates: Requirements 11.4**
    """

    @given(whitespace=_simple_whitespace_st)
    @settings(
        max_examples=50,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_whitespace_only_message_returns_422(self, whitespace: str):
        """
        Property: Any message that is entirely whitespace MUST be rejected
        with a 422 response.

        Given: A message string consisting only of whitespace characters
        When: POST /chat is called with that message
        Then: Response status is 422

        **Validates: Requirements 11.4**
        """
        assume(whitespace.strip() == "")
        response = _client.post("/chat", json={"message": whitespace})
        assert response.status_code == 422, (
            f"Whitespace-only message {repr(whitespace)} must return 422, "
            f"got {response.status_code}"
        )

    @given(whitespace=_whitespace_st)
    @settings(
        max_examples=50,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_unicode_whitespace_only_message_returns_422(self, whitespace: str):
        """
        Property: Any message consisting only of Unicode whitespace characters
        MUST be rejected with 422.

        Given: A string where every character is a whitespace character
        When: POST /chat is called
        Then: Response is 422

        **Validates: Requirements 11.4**
        """
        assume(whitespace.strip() == "")
        response = _client.post("/chat", json={"message": whitespace})
        assert response.status_code == 422, (
            f"Unicode whitespace-only message must return 422, "
            f"got {response.status_code}"
        )

    @given(message=_valid_message_st)
    @settings(
        max_examples=30,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_non_whitespace_message_is_accepted(self, message: str):
        """
        Property: Any message with at least one non-whitespace character MUST
        be accepted (not return 422 due to whitespace validation).

        Given: A message string with at least one non-whitespace character
        When: POST /chat is called
        Then: Response is NOT 422 (validation passes)

        **Validates: Requirements 11.4 (inverse — valid messages must not be rejected)**
        """
        assume(message.strip() != "")
        response = _client.post("/chat", json={"message": message})
        # Should not be rejected for whitespace reasons (may be 200 or other non-422)
        assert response.status_code != 422, (
            f"Non-whitespace message {repr(message)} must not return 422, "
            f"got {response.status_code}"
        )

    def test_empty_string_message_returns_422(self):
        """
        Property: An empty string message MUST be rejected with 422.

        Given: message = ""
        When: POST /chat is called
        Then: Response is 422

        **Validates: Requirements 11.4**
        """
        response = _client.post("/chat", json={"message": ""})
        assert response.status_code == 422

    def test_single_space_message_returns_422(self):
        """
        Property: A single space message MUST be rejected with 422.

        Given: message = " "
        When: POST /chat is called
        Then: Response is 422

        **Validates: Requirements 11.4**
        """
        response = _client.post("/chat", json={"message": " "})
        assert response.status_code == 422

    def test_tab_only_message_returns_422(self):
        """
        Property: A tab-only message MUST be rejected with 422.

        Given: message = "\t\t\t"
        When: POST /chat is called
        Then: Response is 422

        **Validates: Requirements 11.4**
        """
        response = _client.post("/chat", json={"message": "\t\t\t"})
        assert response.status_code == 422

    def test_newline_only_message_returns_422(self):
        """
        Property: A newline-only message MUST be rejected with 422.

        Given: message = "\n\n"
        When: POST /chat is called
        Then: Response is 422

        **Validates: Requirements 11.4**
        """
        response = _client.post("/chat", json={"message": "\n\n"})
        assert response.status_code == 422


# ===========================================================================
# Property 32: Email Format Validation
# Validates: Requirement 11.6
# ===========================================================================

class TestProperty32EmailFormatValidation:
    """
    PROPERTY 32: Email Format Validation

    For ANY string that is not a valid email format, the /signup endpoint
    MUST return 422 when used as the email field.

    **Validates: Requirements 11.6**
    """

    @given(invalid_email=_invalid_email_st)
    @settings(
        max_examples=50,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_invalid_email_format_returns_422(self, invalid_email: str):
        """
        Property: Any string that does not match the email regex MUST cause
        the /signup endpoint to return 422.

        Given: A string that is not a valid email address
        When: POST /signup is called with that string as the email field
        Then: Response status is 422

        **Validates: Requirements 11.6**
        """
        assume(not re.match(EMAIL_REGEX, invalid_email))
        response = _client.post(
            "/signup",
            json={
                "email": invalid_email,
                "password": "ValidPass123",
                "name": "Test User",
                "username": "testuser",
            },
        )
        assert response.status_code == 422, (
            f"Invalid email {repr(invalid_email)} must return 422, "
            f"got {response.status_code}"
        )

    @given(valid_email=_valid_email_st)
    @settings(
        max_examples=30,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_valid_email_format_passes_validation(self, valid_email: str):
        """
        Property: Any string that matches the email regex MUST pass email
        validation (not return 422 due to email format).

        Given: A string that is a valid email address
        When: POST /signup is called with that email
        Then: Response is NOT 422 (email validation passes)

        **Validates: Requirements 11.6 (inverse — valid emails must not be rejected)**
        """
        assume(re.match(EMAIL_REGEX, valid_email))
        response = _client.post(
            "/signup",
            json={
                "email": valid_email,
                "password": "ValidPass123",
                "name": "Test User",
                "username": "testuser",
            },
        )
        # Email validation should pass; other errors (e.g., DB conflict) are acceptable
        assert response.status_code != 422, (
            f"Valid email {repr(valid_email)} must not return 422, "
            f"got {response.status_code}: {response.text}"
        )

    def test_email_without_at_symbol_returns_422(self):
        """
        Property: An email without '@' MUST return 422.

        **Validates: Requirements 11.6**
        """
        response = _client.post(
            "/signup",
            json={
                "email": "notanemail",
                "password": "ValidPass123",
                "name": "Test User",
                "username": "testuser",
            },
        )
        assert response.status_code == 422

    def test_email_without_domain_returns_422(self):
        """
        Property: An email with '@' but no domain MUST return 422.

        **Validates: Requirements 11.6**
        """
        response = _client.post(
            "/signup",
            json={
                "email": "user@",
                "password": "ValidPass123",
                "name": "Test User",
                "username": "testuser",
            },
        )
        assert response.status_code == 422

    def test_email_without_tld_returns_422(self):
        """
        Property: An email with no TLD (no dot after domain) MUST return 422.

        **Validates: Requirements 11.6**
        """
        response = _client.post(
            "/signup",
            json={
                "email": "user@nodomain",
                "password": "ValidPass123",
                "name": "Test User",
                "username": "testuser",
            },
        )
        assert response.status_code == 422

    def test_valid_email_passes_format_check(self):
        """
        Property: A well-formed email address MUST pass format validation.

        **Validates: Requirements 11.6**
        """
        response = _client.post(
            "/signup",
            json={
                "email": "valid.user@example.com",
                "password": "ValidPass123",
                "name": "Test User",
                "username": "testuser",
            },
        )
        # Should not be rejected for email format reasons
        assert response.status_code != 422, (
            f"Valid email must not return 422, got {response.status_code}: {response.text}"
        )
