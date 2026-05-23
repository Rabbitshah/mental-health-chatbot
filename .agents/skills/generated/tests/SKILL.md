---
name: tests
description: "Skill for the Tests area of mental-health-chatbot. 319 symbols across 39 files."
---

# Tests

319 symbols | 39 files | Cohesion: 63%

## When to Use

- Working with code in `backend/`
- Understanding how test_signup_endpoint_has_security_headers, test_login_endpoint_has_security_headers, test_login_endpoint_has_csp_header work
- Modifying tests-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `backend/tests/test_e2e_flows.py` | test_chat_requires_authentication, test_mood_requires_authentication, test_invalid_refresh_token_returns_401, test_unauthenticated_request_returns_401, test_export_requires_authentication (+29) |
| `backend/tests/test_export.py` | test_export_requires_authentication, test_export_with_invalid_token_returns_401, unique_user, signup_and_login, test_invalid_format_returns_422 (+28) |
| `backend/tests/test_search.py` | test_search_requires_authentication, signup_and_login, get_user_id_by_email, create_test_session, test_search_returns_empty_list_when_no_sessions (+26) |
| `backend/tests/test_security_headers.py` | test_signup_endpoint_has_security_headers, test_login_endpoint_has_security_headers, test_login_endpoint_has_csp_header, test_unauthenticated_request_to_protected_endpoint_has_security_headers, test_hsts_present_in_production_mode (+19) |
| `backend/tests/test_property_input_validation.py` | _make_validation_app, test_mood_score_out_of_range_returns_422, test_energy_level_out_of_range_returns_422, test_stress_level_out_of_range_returns_422, test_missing_required_field_returns_422_with_detail (+16) |
| `backend/tests/test_property_refresh_tokens.py` | _RefreshToken, _patched_create, test_token_persisted_with_correct_user_association, test_token_stored_with_future_expiry, test_token_stored_as_not_revoked (+14) |
| `backend/tests/test_property_auth_token_validation.py` | test_expired_token_raises_jwt_error, test_malformed_token_raises_jwt_error, test_token_signed_with_wrong_key_raises_jwt_error, test_token_without_email_claim_is_rejected, test_valid_token_with_email_claim_is_accepted (+13) |
| `backend/tests/test_app.py` | signup_and_login, test_auth_flow, test_preference_persistence_flow, test_chat_and_history_flow, test_chat_title_generation_for_general_topics (+10) |
| `backend/tests/test_contextual_ai.py` | test_empty_messages_returns_empty_list, test_user_sender_maps_to_user_role, test_ai_sender_maps_to_model_role, test_parts_structure_is_list_of_text_dicts, test_multiple_messages_preserve_order (+10) |
| `backend/tests/test_auth_flows.py` | _delete_user_raw, registered_user, test_login_valid_credentials_returns_tokens, test_login_returns_user_info, test_login_invalid_password_returns_401 (+9) |

## Entry Points

Start here when exploring this area:

- **`test_signup_endpoint_has_security_headers`** (Function) — `backend/tests/test_security_headers.py:201`
- **`test_login_endpoint_has_security_headers`** (Function) — `backend/tests/test_security_headers.py:218`
- **`test_login_endpoint_has_csp_header`** (Function) — `backend/tests/test_security_headers.py:240`
- **`test_mood_score_out_of_range_returns_422`** (Function) — `backend/tests/test_property_input_validation.py:214`
- **`test_energy_level_out_of_range_returns_422`** (Function) — `backend/tests/test_property_input_validation.py:244`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `SearchResult` | Class | `backend/routes/search.py` | 16 |
| `ChatMessage` | Class | `backend/models.py` | 44 |
| `User` | Class | `backend/models.py` | 5 |
| `ChatSession` | Class | `backend/models.py` | 28 |
| `FakeGeminiResponse` | Class | `backend/tests/test_cache_fallback.py` | 90 |
| `FakeGeminiChat` | Class | `backend/tests/test_cache_fallback.py` | 95 |
| `FakeGeminiModel` | Class | `backend/tests/test_cache_fallback.py` | 100 |
| `FakeGeminiResponse` | Class | `backend/tests/test_app.py` | 93 |
| `FakeGeminiChat` | Class | `backend/tests/test_app.py` | 98 |
| `FakeGeminiModel` | Class | `backend/tests/test_app.py` | 103 |
| `test_signup_endpoint_has_security_headers` | Function | `backend/tests/test_security_headers.py` | 201 |
| `test_login_endpoint_has_security_headers` | Function | `backend/tests/test_security_headers.py` | 218 |
| `test_login_endpoint_has_csp_header` | Function | `backend/tests/test_security_headers.py` | 240 |
| `test_mood_score_out_of_range_returns_422` | Function | `backend/tests/test_property_input_validation.py` | 214 |
| `test_energy_level_out_of_range_returns_422` | Function | `backend/tests/test_property_input_validation.py` | 244 |
| `test_stress_level_out_of_range_returns_422` | Function | `backend/tests/test_property_input_validation.py` | 271 |
| `test_missing_required_field_returns_422_with_detail` | Function | `backend/tests/test_property_input_validation.py` | 292 |
| `test_wrong_type_for_mood_score_returns_422` | Function | `backend/tests/test_property_input_validation.py` | 313 |
| `test_message_exceeding_5000_chars_returns_422` | Function | `backend/tests/test_property_input_validation.py` | 335 |
| `test_valid_mood_request_returns_success` | Function | `backend/tests/test_property_input_validation.py` | 358 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `HandleKeyDown → GetAccessToken` | cross_community | 6 |
| `HandleKeyDown → ShouldRetry` | cross_community | 6 |
| `HandleKeyDown → Sleep` | cross_community | 6 |
| `HandleKeyDown → ExponentialDelay` | cross_community | 6 |
| `SelectNode → GetAccessToken` | cross_community | 6 |
| `SelectNode → ShouldRetry` | cross_community | 6 |
| `SelectNode → Sleep` | cross_community | 6 |
| `SelectNode → ExponentialDelay` | cross_community | 6 |
| `HighlightFilter → GetAccessToken` | cross_community | 6 |
| `HighlightFilter → ShouldRetry` | cross_community | 6 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Pages | 8 calls |
| Backend | 6 calls |
| Components | 2 calls |

## How to Explore

1. `gitnexus_context({name: "test_signup_endpoint_has_security_headers"})` — see callers and callees
2. `gitnexus_query({query: "tests"})` — find related execution flows
3. Read key files listed above for implementation details
