# CloudGentic Gateway -- Architecture

## Overview

CloudGentic Gateway is a 5-service Docker Compose stack that acts as a secure proxy between AI agents and external user accounts.

## Services

```
gateway-api     (FastAPI, port 8421)    -- REST API + auth + rules engine
gateway-web     (Next.js 15, port 3000) -- Dashboard UI
gateway-worker  (Celery)                -- Background tasks (token refresh, cleanup)
gateway-db      (PostgreSQL 16)         -- Primary data store
gateway-redis   (Redis 7)              -- Cache, rate limiting, session data, Celery broker
```

## Request Flow

```
Agent sends request with API key (cgw_...)
    |
    v
gateway-api receives POST /api/v1/agent/execute
    |
    v
1. API key authentication (SHA-256 hash lookup, expiration check)
    |
    v
2. Rules evaluation (rate limits, whitelists, blacklists, approvals)
   Rules are checked BEFORE token decryption (fail fast)
    |
    v
3. Token decryption (AES-256-GCM with per-user HKDF-derived key)
    |
    v
4. Provider service execution (e.g., Google Gmail API call)
    |
    v
5. Audit log entry (append-only, includes IP, action, status)
    |
    v
6. Response returned to agent
```

## Database Schema

```
users                  -- Email/password auth, TOTP 2FA, admin flag
connected_accounts     -- OAuth tokens (encrypted), provider metadata
api_keys               -- Agent API keys (SHA-256 hashed), scoped permissions
rules                  -- Rate limits, whitelists, blacklists, approval rules
audit_logs             -- Append-only action log (INSERT only, no UPDATE/DELETE)
provider_configs       -- OAuth app credentials (encrypted), per-provider
```

All tables use UUID primary keys. Users, accounts, and rules support soft-delete via `deleted_at`.

## Encryption Architecture

```
GATEWAY_MASTER_KEY (env var, hex-encoded 256-bit key)
    |
    v
HKDF (SHA-256, random 16-byte salt, user-specific info string)
    |
    v
Per-user 256-bit AES key
    |
    v
AES-256-GCM (random 12-byte nonce per encryption)
    |
    v
Ciphertext format: v2:{salt}:{nonce}:{ciphertext}
```

- Each user's tokens are encrypted with a unique derived key
- Compromising one user's data doesn't expose others
- Master key never stored in DB -- only in environment variable
- Legacy v1 format (no salt) auto-detected for backwards compatibility

## Authentication

### User Auth (Dashboard)
- Argon2id password hashing (time_cost=3, memory_cost=64MB, parallelism=4)
- Mandatory TOTP 2FA (no skip option)
- JWT access tokens (30 min) + refresh tokens (7 days)
- JWTs include `iat` claim -- invalidated on password change

### Agent Auth (API)
- API keys prefixed with `cgw_`, SHA-256 hashed before storage
- Scoped to specific providers and actions
- Expiration support with automatic enforcement
- `last_used_at` updated on each use

## Rules Engine

Rules are evaluated in priority order before token decryption:

1. **Rate Limit** -- Redis atomic INCR with TTL window
2. **Action Whitelist** -- Only listed actions allowed
3. **Action Blacklist** -- Listed actions blocked
4. **Require Approval** -- Action blocked pending manual approval

## Provider System

Providers have two layers:

1. **Registry** (`providers/registry.py`) -- Metadata, setup steps, developer console URLs for 15 providers
2. **Service** (`providers/google/service.py`) -- Actual API proxy with explicit action allowlist

Provider OAuth credentials can be configured via:
- Dashboard UI (encrypted in `provider_configs` table) -- preferred
- Environment variables (`.env`) -- fallback

## MCP Server

FastMCP server exposes gateway tools for AI agents:
- `gmail_send`, `gmail_search`, `gmail_read`
- `calendar_list_events`, `calendar_create_event`
- `drive_list_files`, `drive_read_file`

Each tool proxies through the gateway's `/api/v1/agent/execute` endpoint, so all rules and audit logging apply.
