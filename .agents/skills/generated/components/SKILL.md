---
name: components
description: "Skill for the Components area of mental-health-chatbot. 21 symbols across 4 files."
---

# Components

21 symbols | 4 files | Cohesion: 80%

## When to Use

- Working with code in `frontend/`
- Understanding how Sidebar, fetchRecentChats, getActiveNav work
- Modifying components-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `frontend/src/components/Sidebar.jsx` | Sidebar, fetchRecentChats, getActiveNav, handleDelete, handleRename (+3) |
| `frontend/src/components/Chatbot.jsx` | streamAssistantMessage, sendPrompt, handleSend, handleRetryOrRegenerate, handleKeyDown (+2) |
| `frontend/src/apiClient.js` | getAccessToken, clearTokens, shouldRetry, exponentialDelay, request |
| `frontend/src/components/Toast.jsx` | showToast |

## Entry Points

Start here when exploring this area:

- **`Sidebar`** (Function) — `frontend/src/components/Sidebar.jsx:24`
- **`fetchRecentChats`** (Function) — `frontend/src/components/Sidebar.jsx:35`
- **`getActiveNav`** (Function) — `frontend/src/components/Sidebar.jsx:74`
- **`handleDelete`** (Function) — `frontend/src/components/Sidebar.jsx:86`
- **`handleRename`** (Function) — `frontend/src/components/Sidebar.jsx:102`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `Sidebar` | Function | `frontend/src/components/Sidebar.jsx` | 24 |
| `fetchRecentChats` | Function | `frontend/src/components/Sidebar.jsx` | 35 |
| `getActiveNav` | Function | `frontend/src/components/Sidebar.jsx` | 74 |
| `handleDelete` | Function | `frontend/src/components/Sidebar.jsx` | 86 |
| `handleRename` | Function | `frontend/src/components/Sidebar.jsx` | 102 |
| `saveRename` | Function | `frontend/src/components/Sidebar.jsx` | 108 |
| `handleStatusUpdate` | Function | `frontend/src/components/Sidebar.jsx` | 131 |
| `getAccessToken` | Function | `frontend/src/apiClient.js` | 15 |
| `clearTokens` | Function | `frontend/src/apiClient.js` | 31 |
| `showToast` | Function | `frontend/src/components/Toast.jsx` | 13 |
| `streamAssistantMessage` | Function | `frontend/src/components/Chatbot.jsx` | 87 |
| `sendPrompt` | Function | `frontend/src/components/Chatbot.jsx` | 108 |
| `handleSend` | Function | `frontend/src/components/Chatbot.jsx` | 142 |
| `handleRetryOrRegenerate` | Function | `frontend/src/components/Chatbot.jsx` | 180 |
| `handleKeyDown` | Function | `frontend/src/components/Chatbot.jsx` | 240 |
| `handleCopyMessage` | Function | `frontend/src/components/Chatbot.jsx` | 210 |
| `handleShareMessage` | Function | `frontend/src/components/Chatbot.jsx` | 221 |
| `request` | Method | `frontend/src/apiClient.js` | 73 |
| `formatRelativeDate` | Function | `frontend/src/components/Sidebar.jsx` | 412 |
| `shouldRetry` | Function | `frontend/src/apiClient.js` | 41 |

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
| Tests | 2 calls |
| Pages | 2 calls |
| Routes | 1 calls |
| Cluster_23 | 1 calls |

## How to Explore

1. `gitnexus_context({name: "Sidebar"})` — see callers and callees
2. `gitnexus_query({query: "components"})` — find related execution flows
3. Read key files listed above for implementation details
