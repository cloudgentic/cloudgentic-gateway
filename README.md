# CloudGentic Gateway

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker)](https://hub.docker.com)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?logo=python)](https://python.org)
[![Next.js 15](https://img.shields.io/badge/Next.js-15-000000?logo=next.js)](https://nextjs.org)
[![GitHub Release](https://img.shields.io/github/v/release/cloudgentic/cloudgentic-gateway)](https://github.com/cloudgentic/cloudgentic-gateway/releases)

**The open-source security layer between AI agents and your accounts.**

CloudGentic Gateway is a self-hosted AI agent account gateway -- a secure, rules-enforced bridge that lets AI agents (OpenClaw, Agent Zero, LangChain, etc.) access your Gmail, Calendar, Drive, Slack, and 15+ services while you stay in control.

> You wouldn't give an intern unrestricted access to your Gmail. Why give it to an AI agent?

---

## Security-First Design

- **Emergency Kill Switch** -- One click to revoke all agent access instantly
- **Behavior Anomaly Detection** -- Automatic alerts when agents act unusually
- **Dry-Run Mode** -- Test agent actions without executing them
- **Skill Security Scanner** -- Scan OpenClaw skills for malware before installing
- **Mandatory 2FA** -- Every self-hosted instance requires TOTP authentication
- **AES-256-GCM Vault** -- Military-grade encryption for all stored tokens
- **Append-Only Audit Log** -- Immutable record of every agent action

---

## Quick Start

```bash
git clone https://github.com/cloudgentic/cloudgentic-gateway.git
cd cloudgentic-gateway
cp .env.example .env
```

Edit `.env` and set the required values:

```bash
# Generate keys:
openssl rand -hex 32  # GATEWAY_MASTER_KEY
openssl rand -hex 32  # GATEWAY_JWT_SECRET

# Set passwords:
POSTGRES_PASSWORD=your_secure_password
REDIS_PASSWORD=your_secure_password
```

Start everything:

```bash
docker compose up -d
```

Open **http://localhost:3000** -- create your admin account and set up 2FA.

- **Dashboard:** http://localhost:3000
- **API Docs:** http://localhost:8421/docs

---

## Features

### Core Gateway
| Feature | Description |
|---------|-------------|
| **Encrypted Token Vault** | AES-256-GCM + salted HKDF per-user key derivation |
| **15 Provider Wizards** | Step-by-step OAuth setup for Google, Slack, X, Salesforce, HubSpot, and more |
| **Agent API Keys** | `cgw_` prefixed, SHA-256 hashed, scoped permissions, expiration |
| **Rules Engine** | Rate limits, whitelists, blacklists, approval workflows, action chains, dry-run |
| **5 Rule Templates** | One-click presets: Read-Only Gmail, Safe Social, Business Hours, and more |
| **MCP Server** | FastMCP tools for Gmail, Calendar, Drive -- works with any MCP-compatible agent |

### Security & Monitoring
| Feature | Description |
|---------|-------------|
| **Emergency Kill Switch** | Instantly revoke all agent access from dashboard, API, or MCP |
| **Anomaly Detection** | Rate spikes, burst detection, unusual hours, new action alerts |
| **Skill Scanner** | Pattern-based malware analysis for OpenClaw ClawHub skills |
| **Provider Health** | Token status, rate limit usage, API availability per account |
| **Multi-Agent Dashboard** | All agents side-by-side with 24h stats |

### Events & Automation
| Feature | Description |
|---------|-------------|
| **Webhook Events** | Subscribe to gateway events, receive at your endpoints |
| **Action Chains** | "If Gmail send succeeds, notify Slack" -- simple workflows |
| **Push Notifications** | Alerts via Email, Telegram, Discord, or custom webhook |
| **Audit Export** | Streaming CSV download with date range and filters |
| **Preflight API** | Agent startup health check -- verify accounts, keys, rules |

### Dashboard Pages
| Page | What it does |
|------|-------------|
| Provider Setup | Step-by-step OAuth wizards with direct developer console links |
| Connected Accounts | Connect/disconnect accounts, shows only configured providers |
| API Keys | Create/revoke keys, shown once on creation |
| Agents | Multi-agent overview with 24h activity stats |
| Rules | Visual builder + template gallery |
| Webhooks | Subscribe to events, view delivery status |
| Security | Kill switch, anomaly feed, skill scanner |
| Health | Token expiry bars, rate limit usage, overall status |
| Audit Log | Filterable table + CSV export |
| Notifications | Toggle channels, configure credentials, test buttons |
| Settings | Profile, password change, 2FA management |

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
                  |   - Anomaly Detection       |
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

### Docker Compose Stack (5 services)

| Service | Port | Description |
|---------|------|-------------|
| `gateway-api` | 8421 | FastAPI backend |
| `gateway-web` | 3000 | Next.js 15 dashboard |
| `gateway-worker` | -- | Celery background tasks |
| `gateway-db` | 5432 | PostgreSQL 16 |
| `gateway-redis` | 6379 | Redis 7 |

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| API | FastAPI 0.115+ (Python 3.12) |
| Frontend | Next.js 15, React 19, Tailwind CSS, Framer Motion |
| Database | PostgreSQL 16 with Alembic migrations |
| Cache | Redis 7 |
| Task Queue | Celery 5 |
| MCP Server | FastMCP |
| Encryption | AES-256-GCM + salted HKDF |
| Password Hashing | Argon2id |
| 2FA | TOTP |
| Containers | Docker + Docker Compose |

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

### Dry-Run Mode

```bash
curl -X POST http://localhost:8421/api/v1/agent/execute \
  -H "Authorization: Bearer cgw_your_api_key" \
  -H "X-Gateway-Dry-Run: true" \
  -H "Content-Type: application/json" \
  -d '{"provider": "google", "service": "gmail", "action": "send", "params": {...}}'
```

### Preflight Check

```bash
curl http://localhost:8421/api/v1/agents/preflight \
  -H "Authorization: Bearer cgw_your_api_key"
```

### MCP Server

```bash
docker exec gateway-api fastmcp run app.mcp.server:mcp
```

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

## Providers

### Fully implemented
| Provider | Services |
|----------|----------|
| **Google** | Gmail (list, read, send, search), Calendar (list, create, delete), Drive (list, read, download) |

### OAuth setup wizards (connect flow ready, service proxy coming)
Slack, Twitter/X, Facebook, Instagram, TikTok, Stripe, HubSpot, GoHighLevel, Salesforce, Discord, LinkedIn, GitHub, Notion, Shopify

---

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Security Measures](docs/SECURITY-AUDIT.md)
- [Git Workflow](docs/GIT-WORKFLOW.md)
- [Feature Roadmap](docs/FEATURE-ROADMAP.md)
- [API Reference](http://localhost:8421/docs) (auto-generated OpenAPI)

---

## Contributing

We welcome contributions! Please read our [Contributing Guide](CONTRIBUTING.md).

If you discover a vulnerability, please report it via [SECURITY.md](SECURITY.md).

---

## License

MIT License -- see [LICENSE](LICENSE) for details.

---

**Built by [CloudGentic AI](https://cloudgentic.ai)** -- A product of Forester Information Technology Corp.
