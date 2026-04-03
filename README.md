# CloudGentic Gateway

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker)](https://hub.docker.com)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?logo=python)](https://python.org)
[![Next.js 15](https://img.shields.io/badge/Next.js-15-000000?logo=next.js)](https://nextjs.org)

**Open-source AI agent account gateway** -- a secure, rules-enforced bridge between AI agents and external user accounts.

CloudGentic Gateway enables any AI agent to perform actions on a user's connected accounts (Gmail, Calendar, Drive, and more) while respecting user-defined permissions, rate limits, and approval workflows.

---

## Why CloudGentic Gateway?

- **Encrypted Token Vault** -- OAuth tokens stored with AES-256-GCM + per-user HKDF key derivation
- **Rules Engine** -- Rate limits, action whitelists/blacklists, and approval workflows
- **Audit Trail** -- Every agent action logged to an immutable, append-only audit log
- **15 Provider Setup Wizards** -- Step-by-step OAuth setup for Google, Slack, Twitter/X, Salesforce, HubSpot, and more
- **MCP Server** -- FastMCP tools for Gmail, Calendar, and Drive
- **Self-Hostable** -- Single `docker compose up` command
- **Open Source** -- MIT license, free forever

---

## Architecture

```
+-----------------+   +-----------------+   +-----------------+
|  OpenClaw Agent |   | Agent Zero      |   |  Any AI Agent   |
+--------+--------+   +--------+--------+   +--------+--------+
         |                      |                      |
         +----------------------+----------------------+
                                |  API Key (cgw_...) / MCP
                  +-------------v--------------+
                  |   CLOUDGENTIC GATEWAY       |
                  |   - Rules Engine            |
                  |   - Token Vault (AES-256)   |
                  |   - MCP Server              |
                  |   - Audit Logger            |
                  +-------------+--------------+
                                | OAuth Tokens
         +----------------------+----------------------+
         |                      |                      |
+--------v--------+   +--------v--------+   +---------v-------+
| Google APIs     |   | CRMs            |   | Social / Chat   |
| Gmail,Cal,Drive |   | HubSpot, SF, GL |   | Slack, X, etc.  |
+-----------------+   +-----------------+   +-----------------+
```

---

## Quick Start (Self-Hosted)

```bash
git clone https://github.com/cloudgentic/cloudgentic-gateway.git
cd cloudgentic-gateway
cp .env.example .env
```

Edit `.env` and fill in the required values:

```bash
# Generate encryption keys (paste output into .env):
openssl rand -hex 32  # GATEWAY_MASTER_KEY
openssl rand -hex 32  # GATEWAY_JWT_SECRET

# Set database and Redis passwords:
POSTGRES_PASSWORD=your_secure_password
REDIS_PASSWORD=your_secure_password
```

Then start everything:

```bash
docker compose up -d
```

Open **http://localhost:3000** -- you'll be guided through a setup wizard to create your admin account with mandatory two-factor authentication.

- **Dashboard:** http://localhost:3000
- **API Docs:** http://localhost:8421/docs
- **API Health:** http://localhost:8421/api/v1/health

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| API | FastAPI 0.115+ (Python 3.12) |
| Frontend | Next.js 15, React 19, Tailwind CSS |
| Database | PostgreSQL 16 |
| Cache | Redis 7 |
| Task Queue | Celery 5 |
| MCP Server | FastMCP (Python) |
| Encryption | AES-256-GCM + salted HKDF key derivation |
| Password Hashing | Argon2id |
| 2FA | TOTP (Google Authenticator, Authy, etc.) |
| Containers | Docker + Docker Compose |

---

## Providers

### Fully implemented (v0.1.0)

| Provider | Services |
|----------|----------|
| **Google** | Gmail (list, read, send, search), Calendar (list, create, delete), Drive (list, read, download) |

### OAuth setup wizards available (connect flow ready, service proxy coming soon)

Slack, Twitter/X, Facebook, Instagram, TikTok, Stripe, HubSpot, GoHighLevel, Salesforce, Discord, LinkedIn, GitHub, Notion, Shopify

Each provider has a **step-by-step setup wizard** in the dashboard with direct links to developer consoles and callback URLs pre-filled.

---

## Rules Engine

Rules are evaluated **before** token decryption (fail fast):

| Rule Type | Example |
|-----------|--------|
| **Rate Limit** | Max 100 requests per hour per API key |
| **Action Whitelist** | Agent can only read Gmail, not send |
| **Action Blacklist** | Block specific actions (e.g., gmail.send) |
| **Require Approval** | Require manual approval before executing |

Rules are configured per-user through the dashboard with a visual builder.

---

## Agent Integration

### REST API

```bash
curl -X POST http://localhost:8421/api/v1/agent/execute \
  -H "Authorization: Bearer cgw_your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "google",
    "service": "gmail",
    "action": "send",
    "params": {
      "to": "user@example.com",
      "subject": "Hello",
      "body": "Sent via CloudGentic Gateway"
    }
  }'
```

### MCP Server

The gateway includes a FastMCP server with tools for Gmail, Calendar, and Drive. Run it alongside the API:

```bash
docker exec gateway-api fastmcp run app.mcp.server:mcp
```

Each tool requires an `api_key` parameter (your `cgw_...` key).

---

## Dashboard

The web dashboard (http://localhost:3000) includes:

- **Provider Setup** -- Step-by-step OAuth credential wizards for 15 providers
- **Connected Accounts** -- Connect/disconnect external accounts
- **API Keys** -- Create, list, and revoke agent API keys (shown once on creation)
- **Rules** -- Visual rule builder for rate limits, whitelists, blacklists, approvals
- **Audit Log** -- Filterable history of all agent actions
- **Settings** -- Profile, password change, 2FA management

---

## Security

- AES-256-GCM encryption with salted HKDF per-user key derivation
- Argon2id password hashing (time_cost=3, memory_cost=64MB)
- Mandatory TOTP 2FA on all accounts
- API keys: SHA-256 hashed, `cgw_` prefixed, shown once
- Append-only audit logs (INSERT only, no UPDATE/DELETE)
- JWT revocation on password change
- CSRF protection on OAuth flows
- Security headers on all responses (CSP, HSTS, X-Frame-Options)
- Registration closed by default after first admin
- Tokens never logged, never in API responses

See [SECURITY.md](SECURITY.md) for vulnerability reporting.

---

## CLI Management

```bash
# List users
docker exec gateway-api python -m app.cli list-users

# Reset password
docker exec gateway-api python -m app.cli reset-password user@email.com "newpassword"

# Disable 2FA (emergency recovery)
docker exec gateway-api python -m app.cli disable-2fa user@email.com

# Create admin
docker exec gateway-api python -m app.cli create-admin admin@email.com "password"
```

---

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Security](docs/SECURITY-AUDIT.md)
- [Git Workflow](docs/GIT-WORKFLOW.md)
- [API Reference](http://localhost:8421/docs) (auto-generated OpenAPI)

---

## Contributing

We welcome contributions! Please read our [Contributing Guide](CONTRIBUTING.md).

---

## License

MIT License -- see [LICENSE](LICENSE) for details.

---

**Built by [CloudGentic AI](https://cloudgentic.ai)** -- A product of Forester Information Technology Corp.
