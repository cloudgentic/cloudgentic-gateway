# Changelog

All notable changes to CloudGentic Gateway will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.3.0] - 2026-04-03

### Added — Phase 6: Community & Polish
- **Rule Templates** -- 5 bundled presets (read-only Gmail, safe social, business hours, require approval, cautious starter) with gallery page and one-click apply
- **Multi-Agent Dashboard** -- all API keys shown as agent cards with 24h stats, top actions, last active time
- **Push Notifications** -- configurable channels (Email, Telegram, Discord, Webhook) with test buttons and quiet hours
- **Audit Export** -- streaming CSV download with date range and filter parameters
- **Preflight API** -- agent startup health check endpoint (GET /agents/preflight)
- **Full dashboard** -- all 12 features now have frontend pages with polished dark-mode UI

## [1.2.0] - 2026-04-03

### Added — Phase 5: Events & Observability
- **Webhook Events** -- subscribe to gateway events, create/list/delete subscriptions, view delivery status
- **Action Chains** -- post-action workflows ("if Gmail send succeeds, notify Slack") with template variables and depth limits
- **Provider Health Dashboard** -- token status bars, rate limit usage, overall health indicator per connected account

## [1.1.0] - 2026-04-03

### Added — Phase 4: Security Hardening
- **Emergency Kill Switch** -- one click to revoke all agent API keys, with optional account disconnect
- **Dry-Run Mode** -- test agent actions without executing (header or body flag)
- **Anomaly Detection** -- real-time behavioral analysis with configurable sensitivity (2/3/4 sigma), auto-pause on critical
- **Skill Security Scanner** -- pattern-based malware analysis for OpenClaw skills with risk scoring

### Security
- SSRF prevention on webhook/notification URLs (blocks private IPs, internal hostnames)
- Kill switch always revokes keys (bypass removed)
- Route shadowing fixed on rule templates endpoint
- Audit export uses actual streaming (batched reads, not memory-loaded)
- Redis INCR+EXPIRE atomicity via pipeline
- Anomaly sensitivity validated to low/medium/high only
- Quiet hours respects user timezone
- Skill scanner content size limited to prevent ReDoS
- Template path traversal prevention

## [0.1.0] - 2026-04-03

### Added — Phase 1: Core Gateway
- FastAPI backend with async SQLAlchemy, Alembic migrations, PostgreSQL 16
- User authentication with Argon2id password hashing and mandatory TOTP 2FA
- Token vault with AES-256-GCM encryption and salted HKDF per-user key derivation
- Agent API keys with cgw_ prefix, SHA-256 hashed storage, scoped permissions
- Google provider with full OAuth flow (Gmail, Calendar, Drive)
- 15 provider setup wizards with encrypted credential storage
- Rules engine with rate limits, whitelists, blacklists, approval workflows
- Append-only audit log with auto-captured IP addresses
- MCP server (FastMCP) with Gmail, Calendar, Drive tools
- Celery worker for background tasks
- Next.js 15 dashboard with dark mode and Framer Motion animations
- CLI management (reset-password, disable-2fa, create-admin, list-users)
- Docker Compose stack (5 services)
- Password reset flow (tokens in Redis, never in API response)
- Registration closed by default after first admin

### Security (22 issues found in code review, all fixed)
- OAuth CSRF state validation, TOTP secrets encrypted at rest
- API key expiration enforcement, JWT revocation on password change
- Action dispatch via explicit allowlist, atomic rate limiting
- Pydantic validation on all endpoints, password strength enforcement
- HKDF salt added (v2 format, backwards compatible)
