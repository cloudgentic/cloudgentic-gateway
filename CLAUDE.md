# CloudGentic Gateway — Claude Code Instructions

## Project Overview

CloudGentic Gateway is an open-source AI agent account gateway (MIT license). It acts as a secure, rules-enforced bridge between AI agents and external user accounts. Read the full Master Plan in the project knowledge attached to this Claude Project.

## Repository

- **Org:** cloudgentic (display name: CloudGentic AI)
- **Repo:** cloudgentic-gateway
- **URL:** https://github.com/cloudgentic/cloudgentic-gateway
- **License:** MIT
- **Legal Entity:** Forester Information Technology Corp.
- **Local Path:** D:\projects\cloudgentic\cloudgentic-gateway\repo

## Tech Stack

| Layer | Technology |
|-------|------------|
| API | FastAPI 0.115+ (Python 3.12) |
| Frontend | Next.js 15, React 19, Tailwind CSS |
| Database | PostgreSQL 16 |
| Cache | Redis 7 |
| Task Queue | Celery 5 (Redis broker) |
| MCP Server | FastMCP (Python) |
| Encryption | cryptography lib — AES-256-GCM + HKDF |
| Password Hashing | argon2-cffi (Argon2id) |
| 2FA | pyotp (TOTP) + py_webauthn (WebAuthn/Passkeys) |
| OAuth | Authlib + httpx |
| Containers | Docker + Docker Compose |
| CI/CD | GitHub Actions |

## Docker Compose Stack (5 services)

- **gateway-api** — FastAPI (port 8421)
- **gateway-web** — Next.js 15 dashboard (port 3000)
- **gateway-worker** — Celery (same image as api, different entrypoint)
- **gateway-db** — PostgreSQL 16 (port 5432, internal only)
- **gateway-redis** — Redis 7 (port 6379, internal only)

## Repository Structure

```
cloudgentic-gateway/
├── apps/
│   ├── api/                    # FastAPI backend
│   │   ├── app/
│   │   │   ├── api/v1/         # Route handlers
│   │   │   ├── core/           # Config, security, encryption, 2FA
│   │   │   ├── models/         # SQLAlchemy models
│   │   │   ├── providers/      # External service integrations
│   │   │   ├── rules/          # Rules engine + evaluators
│   │   │   ├── mcp/            # MCP server implementation
│   │   │   └── schemas/        # Pydantic schemas
│   │   ├── alembic/            # DB migrations
│   │   ├── tests/
│   │   └── Dockerfile
│   └── web/                    # Next.js dashboard
│       ├── src/app/            # App Router pages
│       ├── src/components/
│       ├── src/lib/
│       └── Dockerfile
├── plugins/
│   ├── openclaw-skill/
│   ├── agent-zero-tool/
│   └── n8n-node/
├── docker-compose.yml
├── docker-compose.prod.yml
├── .env.example
├── Makefile
└── docs/
```

## Git Workflow

- **main** — production-ready, tagged releases
- **develop** — integration branch
- **feature/p1-xxx** — Phase 1 feature branches off develop
- Conventional Commits: `feat(scope):`, `fix(scope):`, `chore:`, `docs:`, `test:`
- Scopes: api, auth, vault, rules, providers/google, mcp, dashboard, audit, db, docker, ci

## Security Requirements (Non-Negotiable)

- OAuth tokens encrypted at rest with AES-256-GCM; per-user key via HKDF
- Master key from GATEWAY_MASTER_KEY env var only — never in DB or code
- Passwords hashed with Argon2id (time_cost=3, memory_cost=65536, parallelism=4)
- Agent API keys: SHA-256 hashed before storage, prefixed `cgw_`, shown once
- Mandatory TOTP 2FA at first-run setup (no skip option)
- Sensitive actions require TOTP re-entry
- Audit logs append-only — no UPDATE or DELETE on audit_logs table
- Tokens never logged, never returned in API responses, never sent to frontend
- Security headers on all responses (CSP, HSTS, X-Frame-Options, etc.)

## Phase 1 Tasks (Build Order)

1. Scaffold Docker Compose stack (FastAPI + Next.js + PG + Redis)
2. User auth: local email/password with Argon2id + mandatory TOTP 2FA + WebAuthn
3. Token vault with AES-256-GCM encryption and HKDF key derivation
4. Agent API key CRUD (create, list, revoke, scoped permissions)
5. Google provider (Gmail + Calendar + Drive) with full OAuth flow
6. Basic rules engine (rate limits + action whitelist/blacklist)
7. Audit log (append-only, basic query endpoint)
8. Dashboard: accounts page, API keys page, basic audit viewer

## Key Design Decisions

- All tables use UUID primary keys
- JSONB for flexible configs (rules, provider metadata, request summaries)
- Soft-delete via deleted_at (never hard delete users/accounts/rules)
- Separate DB role for audit writes (INSERT only, no UPDATE/DELETE)
- Per-user encryption key derivation ensures compromising one user doesn't expose others
- Rules evaluated BEFORE token decryption (fail fast)
- API key format: `cgw_<random>` — prefix for leak detection
- Self-hosted auth is fully local (zero external dependencies)
- Cloud auth uses Firebase (shared with main CloudGentic platform)

## Commands

- `make dev` — start all services
- `make test` — run pytest
- `make lint` — run ruff
- `make migrate` — run alembic upgrade head
- `make migrate-create` — create new migration
- `make logs` — tail all service logs
- `make clean` — remove volumes and containers
