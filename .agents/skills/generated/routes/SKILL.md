---
name: routes
description: "Skill for the Routes area of mental-health-chatbot. 43 symbols across 8 files."
---

# Routes

43 symbols | 8 files | Cohesion: 81%

## When to Use

- Working with code in `backend/`
- Understanding how get_redis_client, cache_get, cache_set work
- Modifying routes-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `backend/routes/insights.py` | get_mood_trend, get_mood_analytics, average, calculate_streaks, pearson_correlation (+6) |
| `backend/routes/history.py` | PaginatedSessionResponse, get_all_sessions, SessionResponse, _build_session_responses_batch, build_session_response (+5) |
| `backend/redis_client.py` | get_redis_client, cache_get, cache_set, invalidate_user_caches, cache_delete |
| `backend/routes/export.py` | _session_to_dict, _mood_to_dict, export_as_json, export_as_csv, export_data |
| `backend/routes/auth.py` | get_profile, build_user_payload, signup, update_profile |
| `backend/routes/notifications.py` | NotificationsListResponse, get_notifications, MarkReadResponse, mark_notification_read |
| `backend/tests/test_cache_fallback.py` | test_cache_get_returns_none_on_connection_error, test_cache_set_returns_false_on_connection_error, test_cache_delete_returns_false_on_connection_error |
| `frontend/src/apiClient.js` | sleep |

## Entry Points

Start here when exploring this area:

- **`get_redis_client`** (Function) — `backend/redis_client.py:32`
- **`cache_get`** (Function) — `backend/redis_client.py:115`
- **`cache_set`** (Function) — `backend/redis_client.py:130`
- **`test_cache_get_returns_none_on_connection_error`** (Function) — `backend/tests/test_cache_fallback.py:229`
- **`test_cache_set_returns_false_on_connection_error`** (Function) — `backend/tests/test_cache_fallback.py:239`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `PaginatedSessionResponse` | Class | `backend/routes/history.py` | 60 |
| `SessionResponse` | Class | `backend/routes/history.py` | 29 |
| `NotificationsListResponse` | Class | `backend/routes/notifications.py` | 24 |
| `MarkReadResponse` | Class | `backend/routes/notifications.py` | 29 |
| `get_redis_client` | Function | `backend/redis_client.py` | 32 |
| `cache_get` | Function | `backend/redis_client.py` | 115 |
| `cache_set` | Function | `backend/redis_client.py` | 130 |
| `test_cache_get_returns_none_on_connection_error` | Function | `backend/tests/test_cache_fallback.py` | 229 |
| `test_cache_set_returns_false_on_connection_error` | Function | `backend/tests/test_cache_fallback.py` | 239 |
| `get_mood_trend` | Function | `backend/routes/insights.py` | 105 |
| `get_mood_analytics` | Function | `backend/routes/insights.py` | 160 |
| `get_all_sessions` | Function | `backend/routes/history.py` | 127 |
| `get_profile` | Function | `backend/routes/auth.py` | 225 |
| `invalidate_user_caches` | Function | `backend/redis_client.py` | 207 |
| `build_session_response` | Function | `backend/routes/history.py` | 121 |
| `delete_sessions_bulk` | Function | `backend/routes/history.py` | 195 |
| `rename_session` | Function | `backend/routes/history.py` | 236 |
| `update_session_status` | Function | `backend/routes/history.py` | 270 |
| `delete_session` | Function | `backend/routes/history.py` | 299 |
| `delete_all_sessions` | Function | `backend/routes/history.py` | 315 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Delete_sessions_bulk → GetAccessToken` | cross_community | 6 |
| `Delete_sessions_bulk → ShouldRetry` | cross_community | 6 |
| `Delete_sessions_bulk → Sleep` | cross_community | 6 |
| `Delete_sessions_bulk → ExponentialDelay` | cross_community | 6 |
| `Delete_session → GetAccessToken` | cross_community | 6 |
| `Delete_session → ShouldRetry` | cross_community | 6 |
| `Delete_session → Sleep` | cross_community | 6 |
| `Delete_session → ExponentialDelay` | cross_community | 6 |
| `Delete_all_sessions → GetAccessToken` | cross_community | 6 |
| `Delete_all_sessions → ShouldRetry` | cross_community | 6 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Tests | 8 calls |
| Pages | 4 calls |
| Backend | 1 calls |

## How to Explore

1. `gitnexus_context({name: "get_redis_client"})` — see callers and callees
2. `gitnexus_query({query: "routes"})` — find related execution flows
3. Read key files listed above for implementation details
