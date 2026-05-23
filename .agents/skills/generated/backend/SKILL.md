---
name: backend
description: "Skill for the Backend area of mental-health-chatbot. 29 symbols across 11 files."
---

# Backend

29 symbols | 11 files | Cohesion: 76%

## When to Use

- Working with code in `backend/`
- Understanding how detect_crisis, get_crisis_resources, log_crisis_event work
- Modifying backend-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `backend/crisis_service.py` | EmergencyResource, CrisisDetection, detect_crisis, get_crisis_resources, log_crisis_event (+3) |
| `backend/routes/chat.py` | extract_keywords, infer_session_tag, build_session_title, is_auto_generated_title, generate_summary (+1) |
| `backend/models.py` | CrisisEvent, RefreshToken, MoodEntry |
| `backend/database.py` | _boolean_default_sql, ensure_chat_session_status_columns, ensure_user_preference_columns |
| `backend/tests/test_auth_enhancements.py` | test_create_refresh_token, test_refresh_token_expiry_is_7_days |
| `backend/logger.py` | JsonFormatter, setup_logging |
| `backend/jwt_handler.py` | create_refresh_token |
| `backend/routes/auth.py` | login |
| `backend/redis_client.py` | cache_delete_pattern |
| `backend/routes/insights.py` | add_mood_entry |

## Entry Points

Start here when exploring this area:

- **`detect_crisis`** (Function) — `backend/crisis_service.py:83`
- **`get_crisis_resources`** (Function) — `backend/crisis_service.py:100`
- **`log_crisis_event`** (Function) — `backend/crisis_service.py:119`
- **`extract_keywords`** (Function) — `backend/routes/chat.py:176`
- **`infer_session_tag`** (Function) — `backend/routes/chat.py:198`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `CrisisEvent` | Class | `backend/models.py` | 87 |
| `EmergencyResource` | Class | `backend/crisis_service.py` | 66 |
| `CrisisDetection` | Class | `backend/crisis_service.py` | 74 |
| `RefreshToken` | Class | `backend/models.py` | 75 |
| `MoodEntry` | Class | `backend/models.py` | 59 |
| `JsonFormatter` | Class | `backend/logger.py` | 11 |
| `detect_crisis` | Function | `backend/crisis_service.py` | 83 |
| `get_crisis_resources` | Function | `backend/crisis_service.py` | 100 |
| `log_crisis_event` | Function | `backend/crisis_service.py` | 119 |
| `extract_keywords` | Function | `backend/routes/chat.py` | 176 |
| `infer_session_tag` | Function | `backend/routes/chat.py` | 198 |
| `build_session_title` | Function | `backend/routes/chat.py` | 206 |
| `is_auto_generated_title` | Function | `backend/routes/chat.py` | 252 |
| `generate_summary` | Function | `backend/routes/chat.py` | 256 |
| `chat` | Function | `backend/routes/chat.py` | 309 |
| `create_refresh_token` | Function | `backend/jwt_handler.py` | 30 |
| `test_create_refresh_token` | Function | `backend/tests/test_auth_enhancements.py` | 109 |
| `test_refresh_token_expiry_is_7_days` | Function | `backend/tests/test_auth_enhancements.py` | 123 |
| `login` | Function | `backend/routes/auth.py` | 159 |
| `cache_delete_pattern` | Function | `backend/redis_client.py` | 162 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Add_mood_entry → GetAccessToken` | cross_community | 5 |
| `Add_mood_entry → ShouldRetry` | cross_community | 5 |
| `Add_mood_entry → Sleep` | cross_community | 5 |
| `Add_mood_entry → ExponentialDelay` | cross_community | 5 |
| `Populate → GetAccessToken` | cross_community | 4 |
| `Populate → ShouldRetry` | cross_community | 4 |
| `Populate → Sleep` | cross_community | 4 |
| `Populate → ExponentialDelay` | cross_community | 4 |
| `Get_crisis_resources → GetAccessToken` | cross_community | 4 |
| `Get_crisis_resources → ShouldRetry` | cross_community | 4 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Tests | 9 calls |
| Routes | 2 calls |
| Pages | 2 calls |

## How to Explore

1. `gitnexus_context({name: "detect_crisis"})` — see callers and callees
2. `gitnexus_query({query: "backend"})` — find related execution flows
3. Read key files listed above for implementation details
