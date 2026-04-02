# CloudGentic Gateway

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker)](https://hub.docker.com)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?logo=python)](https://python.org)
[![Next.js 15](https://img.shields.io/badge/Next.js-15-000000?logo=next.js)](https://nextjs.org)

**Open-source AI agent account gateway** — a secure, rules-enforced bridge between AI agents and external user accounts.

CloudGentic Gateway enables any AI agent to perform actions on a user's connected accounts (Google, social media, email, messaging) while respecting user-defined permissions, rate limits, and content policies.

---

## Why CloudGentic Gateway?

- **Centralized Credential Management** — OAuth tokens stored in an AES-256-GCM encrypted vault with per-user key derivation
- **Rules Engine** — Rate limits, action whitelists, time windows, content filters, and approval workflows
- **Audit Trail** — Every agent action logged to an immutable, append-only audit log
- **Universal Compatibility** — REST API + MCP server + native plugins for OpenClaw, Agent Zero, and n8n
- **Self-Hostable** — Single `docker compose up` command, runs on 512 MB RAM
- **Open Source** — MIT license, free forever

---

## Architecture

```
+-----------------+   +-----------------+   +-----------------+
|  OpenClaw Agent |   | Agent Zero      |   |  Any AI Agent   |
+--------+--------+   +--------+--------+   +--------+--------+
         |                      |                      |
         +----------------------+----------------------+
                                |  API Key / MCP
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
| Google APIs     |   | Social Media    |   | Email / Chat    |
| Gmail,Cal,Drive |   | X, FB, Insta    |   | IMAP,Discord,Tg |
+-----------------+   +-----------------+   +-----------------+
```

---

## Quick Start (Self-Hosted)

```bash
git clone https://github.com/cloudgentic/cloudgentic-gateway.git
cd cloudgentic-gateway
cp .env.example .env
# Generate encryption keys:
openssl rand -hex 32  # paste as GATEWAY_MASTER_KEY in .env
openssl rand -hex 32  # paste as GATEWAY_JWT_SECRET in .env
docker compose up -d
open http://localhost:8420
```

On first visit, you'll be guided through a setup wizard to create your admin account with mandatory two-factor authentication.

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
| Encryption | AES-256-GCM + HKDF key derivation |
| Auth | Argon2id + TOTP + WebAuthn |
| Containers | Docker + Docker Compose |

---

## Supported Providers (v1)

| Provider | Actions |
|----------|--------|
| **Gmail** | List, Read, Send, Draft |
| **Google Calendar** | List, Create, Update |
| **Google Drive** | List, Read, Upload |
| **X / Twitter** | Post, Read Timeline, DMs |
| **Facebook** | Post, Read Feed |
| **Instagram** | Post, Read Media |
| **Discord** | Send, Read |
| **Telegram** | Send, Read |
| **Slack** | Send, Read |
| **Email (IMAP/SMTP)** | List, Read, Send, Search |

---

## Rules Engine

The Rules Engine evaluates every agent action before execution:

| Rule Type | Example |
|-----------|--------|
| Rate Limit | Max 10 tweets per day |
| Action Whitelist | Agent can only read Gmail, not send |
| Time Window | Only allow actions Mon-Fri 9am-5pm |
| Content Filter | Block tweets containing profanity |
| Approval Required | Require user approval before sending emails |
| Recipient Whitelist | Agent can only email approved contacts |
| Budget Cap | Max 1000 API calls per month |

---

## Agent Integration

### REST API (Any Agent)
```bash
curl -X POST https://your-gateway/api/v1/actions/gmail/send \
  -H "Authorization: Bearer cgw_your_api_key" \
  -H "Content-Type: application/json" \
  -d '{"to": "user@example.com", "subject": "Hello", "body": "World"}'
```

### MCP Server
Connect your agent to the MCP endpoint — tools are discovered automatically based on connected accounts.

### Native Plugins
- **OpenClaw:** `clawhub install cloudgentic-gateway`
- **Agent Zero:** Drop `gateway_tool.py` into `/a0/usr/tools/`
- **n8n:** `npm install n8n-nodes-cloudgentic-gateway`

---

## Cloud Version

A free cloud-hosted version is available at **[gateway.cloudgentic.ai](https://gateway.cloudgentic.ai)** with 5 connected accounts, 500 actions/day, and 30-day audit log retention. Self-hosted users get unlimited everything.

---

## Documentation

- [Architecture Design](docs/ARCHITECTURE.md)
- [Security Audit & Hardening](docs/SECURITY-AUDIT.md)
- [Git Workflow & Branching](docs/GIT-WORKFLOW.md)
- [API Reference](docs/) *(coming soon)*

---

## Contributing

We welcome contributions! Please read our [Contributing Guide](CONTRIBUTING.md).

## Security

If you discover a vulnerability, please report it responsibly via [SECURITY.md](SECURITY.md).

## License

MIT License — see [LICENSE](LICENSE) for details.

---

**Built by [CloudGentic AI](https://cloudgentic.ai)** — A product of Forester Information Technology Corp.
