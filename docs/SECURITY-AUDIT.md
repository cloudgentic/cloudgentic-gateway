# CloudGentic Gateway -- Security Measures

## Encryption

| What | How |
|------|-----|
| OAuth tokens at rest | AES-256-GCM with salted HKDF per-user key derivation |
| TOTP secrets at rest | AES-256-GCM (same scheme as OAuth tokens) |
| Provider OAuth credentials | AES-256-GCM with system-level key context |
| Master key storage | Environment variable only -- never in DB or code |
| Key derivation | HKDF-SHA256 with random 16-byte salt per encryption |

## Authentication

| What | How |
|------|-----|
| Password hashing | Argon2id (time_cost=3, memory_cost=65536 KB, parallelism=4) |
| 2FA | Mandatory TOTP on all accounts (no skip) |
| JWT tokens | HS256, 30-min access / 7-day refresh, `iat` claim for revocation |
| API keys | `cgw_` prefix, SHA-256 hashed, shown once, expiration enforced |
| Password reset | Tokens stored in Redis (15-min TTL), never in API response |
| Registration | Closed by default after first admin (ALLOW_REGISTRATION env var) |

## Request Security

| What | How |
|------|-----|
| OAuth CSRF | State parameter stored in Redis, validated on callback, single-use |
| Rate limiting | Atomic Redis INCR (no TOCTOU race condition) |
| Action dispatch | Explicit allowlist -- no dynamic attribute lookup |
| Input validation | Pydantic schemas on all endpoints |
| Password validation | Minimum 8 characters enforced at API level |
| JWT revocation | Tokens issued before password change are rejected via `iat` check |

## Infrastructure

| What | How |
|------|-----|
| Security headers | CSP, HSTS, X-Frame-Options, X-Content-Type-Options, Referrer-Policy |
| Audit logging | Append-only table (INSERT only), auto-captured client IP |
| Admin access | Centralized `require_admin` dependency |
| DB/Redis ports | Not exposed in production Docker Compose |
| Audit DB role | Separate `gateway_audit_writer` role with INSERT-only permissions |
| Soft deletes | Users, accounts, and rules use `deleted_at` (never hard delete) |

## What We Don't Do

- Tokens are **never** logged
- Tokens are **never** returned in API responses
- Tokens are **never** sent to the frontend
- Password reset tokens are **never** in HTTP responses
- Raw API keys are shown **once** at creation, then only the prefix is stored
