---
name: pages
description: "Skill for the Pages area of mental-health-chatbot. 26 symbols across 7 files."
---

# Pages

26 symbols | 7 files | Cohesion: 61%

## When to Use

- Working with code in `frontend/`
- Understanding how History, fetchHistory, handleDelete work
- Modifying pages-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `frontend/src/pages/History.jsx` | History, fetchHistory, handleDelete, toggleChatSelection, handleRename (+6) |
| `frontend/src/pages/ManageProfile.jsx` | handleProfileUpdate, handlePasswordChange, handlePreferenceSave, handleResetPreferences, handleDeleteHistory (+1) |
| `frontend/src/apiClient.js` | put, delete |
| `backend/tests/test_e2e_flows.py` | test_filter_history_by_tag, test_invalid_tag_returns_422 |
| `backend/tests/test_app.py` | test_export_data_includes_preferences_and_session_metadata, test_history_management_flow |
| `frontend/src/pages/Signup.jsx` | Signup, getPasswordStrength |
| `frontend/src/api.js` | updateProfile |

## Entry Points

Start here when exploring this area:

- **`History`** (Function) — `frontend/src/pages/History.jsx:19`
- **`fetchHistory`** (Function) — `frontend/src/pages/History.jsx:43`
- **`handleDelete`** (Function) — `frontend/src/pages/History.jsx:88`
- **`toggleChatSelection`** (Function) — `frontend/src/pages/History.jsx:106`
- **`handleRename`** (Function) — `frontend/src/pages/History.jsx:148`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `History` | Function | `frontend/src/pages/History.jsx` | 19 |
| `fetchHistory` | Function | `frontend/src/pages/History.jsx` | 43 |
| `handleDelete` | Function | `frontend/src/pages/History.jsx` | 88 |
| `toggleChatSelection` | Function | `frontend/src/pages/History.jsx` | 106 |
| `handleRename` | Function | `frontend/src/pages/History.jsx` | 148 |
| `saveRename` | Function | `frontend/src/pages/History.jsx` | 154 |
| `cancelRename` | Function | `frontend/src/pages/History.jsx` | 170 |
| `handleStatusUpdate` | Function | `frontend/src/pages/History.jsx` | 175 |
| `handleTagUpdate` | Function | `frontend/src/pages/History.jsx` | 205 |
| `getTagColor` | Function | `frontend/src/pages/History.jsx` | 252 |
| `updateProfile` | Function | `frontend/src/api.js` | 12 |
| `test_filter_history_by_tag` | Function | `backend/tests/test_e2e_flows.py` | 400 |
| `test_invalid_tag_returns_422` | Function | `backend/tests/test_e2e_flows.py` | 431 |
| `test_export_data_includes_preferences_and_session_metadata` | Function | `backend/tests/test_app.py` | 432 |
| `handleProfileUpdate` | Function | `frontend/src/pages/ManageProfile.jsx` | 79 |
| `handlePasswordChange` | Function | `frontend/src/pages/ManageProfile.jsx` | 116 |
| `handlePreferenceSave` | Function | `frontend/src/pages/ManageProfile.jsx` | 158 |
| `handleResetPreferences` | Function | `frontend/src/pages/ManageProfile.jsx` | 267 |
| `test_history_management_flow` | Function | `backend/tests/test_app.py` | 284 |
| `handleDeleteHistory` | Function | `frontend/src/pages/ManageProfile.jsx` | 235 |

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
| Tests | 13 calls |
| Components | 2 calls |

## How to Explore

1. `gitnexus_context({name: "History"})` — see callers and callees
2. `gitnexus_query({query: "pages"})` — find related execution flows
3. Read key files listed above for implementation details
