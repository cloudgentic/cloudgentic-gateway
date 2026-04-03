# Changelog

All notable changes to CloudGentic Gateway will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-04-03

### Added
- **FastAPI backend** with async SQLAlchemy, Alembic migrations, PostgreSQL 16
- **User authentication** with Argon2id password hashing and mandatory TOTP 2FA
- **Token vault** with AES-256-GCM encryption and salted HKDF per-user key derivation
- **Agent API keys** with `cgw_` prefix, SHA-256 hashed storage, scoped permissions
- **Google provider** with full OAuth flow -- Gmail (list, read, send, search), Calendar (list, create, delete), Drive (list, read, download)
- **15 provider setup wizards** with step-by-step instructions and direct developer console links (Google, Slack, Twitter/X, Facebook, Instagram, TikTok, Stripe, HubSpot, GoHighLevel, Salesforce, Discord, LinkedIn, GitHub, Notion, Shopify)
- **Provider credentials** stored encrypted in DB (configured via dashboard, not just .env)
- **Rules engine** with rate limits, action whitelist/blacklist, and require-approval rule types
- **Append-only audit log** with filterable query endpoint and auto-captured IP addresses
- **MCP server** (FastMCP) with tools for Gmail, Calendar, and Drive
- **Celery worker** for background tasks with Redis broker
- **Next.js 15 dashboard** with dark mode, Framer Motion animations:
  - Login with TOTP 2FA support
  - First-run setup wizard
  - Forgot password / reset password flow
  - Dashboard overview with stats
  - Provider Setup page with step-by-step wizards
  - Connected Accounts (dynamic, shows only configured providers)
  - API Keys management (create/revoke, one-time key display)
  - Rules builder (rate limits, whitelists, blacklists, approvals)
  - Audit log viewer with filters
  - Settings page (profile, change password, reset 2FA)
- **CLI management tool** -- reset-password, disable-2fa, create-admin, list-users
- **Docker Compose stack** -- 5 services (API, Web, Worker, PostgreSQL, Redis)
- **Production Docker Compose** config (no exposed DB/Redis ports)

### Security
- Password reset tokens never exposed in API responses (server-side log only)
- OAuth CSRF state validation via Redis
- TOTP secrets encrypted at rest (AES-256-GCM)
- API key expiration enforcement + last_used_at tracking
- Action dispatch via explicit allowlist (no dynamic attribute lookup)
- Atomic Redis rate limiting (no race conditions)
- Registration closed by default after first admin (ALLOW_REGISTRATION)
- JWT revocation on password change (iat + password_changed_at)
- Pydantic schema validation on all endpoints
- Password strength validation at API level (min 8 characters)
- Unique constraint on connected accounts
- HKDF salt added to encryption key derivation (v2 format, backwards compatible)
- Security headers on all responses (CSP, HSTS, X-Frame-Options)
