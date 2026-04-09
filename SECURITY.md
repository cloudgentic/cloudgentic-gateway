# Security Policy

## Reporting a Vulnerability

**Do NOT open a public GitHub issue for security vulnerabilities.**

Email: **security@cloudgentic.ai**

Include: description, steps to reproduce, potential impact, and suggested fix.

Expect acknowledgment within 48 hours and a status update within 7 days.

## Security Features

- AES-256-GCM token encryption with per-user HKDF key derivation
- Mandatory TOTP 2FA for self-hosted deployments
- Argon2id password hashing
- SHA-256 hashed API keys (raw key shown once)
- Append-only audit logs
- HTTPS detection with warning banners
- Security headers (CSP, HSTS, X-Frame-Options)
