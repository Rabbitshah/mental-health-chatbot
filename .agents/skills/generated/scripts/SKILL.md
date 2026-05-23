---
name: scripts
description: "Skill for the Scripts area of mental-health-chatbot. 8 symbols across 2 files."
---

# Scripts

8 symbols | 2 files | Cohesion: 83%

## When to Use

- Working with code in `backend/`
- Understanding how verify_database, verify_redis, verify_models work
- Modifying scripts-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `backend/scripts/verify_infrastructure.py` | verify_database, verify_redis, verify_models, main |
| `backend/scripts/migrate_enhancements.py` | column_exists, table_exists, index_exists, migrate |

## Entry Points

Start here when exploring this area:

- **`verify_database`** (Function) — `backend/scripts/verify_infrastructure.py:10`
- **`verify_redis`** (Function) — `backend/scripts/verify_infrastructure.py:69`
- **`verify_models`** (Function) — `backend/scripts/verify_infrastructure.py:90`
- **`main`** (Function) — `backend/scripts/verify_infrastructure.py:108`
- **`column_exists`** (Function) — `backend/scripts/migrate_enhancements.py:10`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `verify_database` | Function | `backend/scripts/verify_infrastructure.py` | 10 |
| `verify_redis` | Function | `backend/scripts/verify_infrastructure.py` | 69 |
| `verify_models` | Function | `backend/scripts/verify_infrastructure.py` | 90 |
| `main` | Function | `backend/scripts/verify_infrastructure.py` | 108 |
| `column_exists` | Function | `backend/scripts/migrate_enhancements.py` | 10 |
| `table_exists` | Function | `backend/scripts/migrate_enhancements.py` | 18 |
| `index_exists` | Function | `backend/scripts/migrate_enhancements.py` | 26 |
| `migrate` | Function | `backend/scripts/migrate_enhancements.py` | 34 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Main → GetAccessToken` | cross_community | 5 |
| `Main → ShouldRetry` | cross_community | 5 |
| `Main → Sleep` | cross_community | 5 |
| `Main → ExponentialDelay` | cross_community | 5 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Routes | 1 calls |
| Tests | 1 calls |
| Pages | 1 calls |

## How to Explore

1. `gitnexus_context({name: "verify_database"})` — see callers and callees
2. `gitnexus_query({query: "scripts"})` — find related execution flows
3. Read key files listed above for implementation details
