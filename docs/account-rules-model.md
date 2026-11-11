# Gateway — Account Rules Model (PROPRIETARY — cloud/commercial side)

Design notes from Aldo Grillo, 2026-11-11. NOT for the public open-source repo —
these belong with the commercial cloud version (cloudgentic-cloud / AgentForge).
Still to be built out; this document is the starting research record.

## What the gateway is

- The gateway is NOT an MCP server. It is a regulated, rule-based,
  permission-based gateway between the AI agent and every personal account the
  user has — banking, email, insurance, doctors, and more.
- Credentials (usernames, passwords, API keys) live in the gateway's vault. The
  user never hands them to the AI; the user gives the AI permissions through
  the gateway, per account. (Contrast: the Restaurant Suite AI MCP is a data
  service that sits behind this kind of gateway; the gateway itself is the
  permission layer.)
- The primary reason for the commercial cloud version: the agent reaches
  personal accounts only through this regulated gateway.

## The open-source app (user experience)

- The user installs the application on their own computer.
- They log into the application with two-factor authentication (Google as the
  authenticator, as currently set up).
- In the dashboard, they connect all of their personal accounts — email,
  banking, insurance, doctors, etc.

## Rules: every account needs its own rule set

- Rules differ by account type. Base verbs: read, write — plus category-
  specific rules still to be researched and defined per account type
  (a research document is needed: what rule dimensions each account class
  requires).
- Banking / finance rules (Aldo's example):
  - Can the AI send a check or make a payment at all? Yes / no.
  - If yes: how much? Per-action and/or periodic limits.
  - Two-factor confirmation required for payments sent through the system.
- Open question (Aldo, 2026-11-11): how would two-factor for payments work in
  the open-source version? Unresolved — and itself a reason users would move
  to the cloud version, where 2FA can be centrally managed.

## Status

Vision and rules model recorded 2026-11-11. Nothing here is built yet — the
rule taxonomy per account type is the first research task.

## Deployment parity: local gateway vs cloud

- The same gateway capability has to be offered on both sides. The commercial
  cloud version must provide the same vault, permissions and rules as the
  local/open-source gateway — not a reduced subset.
- Local/open-source limit: the gateway runs on the user's own desktop
  (Aldo believes it runs as a container). The AI application, or even a
  web-based app, has to read/connect into that gateway on that computer. So it
  only works while the user is at that desktop, the machine is on, and the
  gateway application is open/running.
- Example Aldo gave: if the user is away from the computer and simply talks to
  their AI — "what's the balance of my account?" — the local gateway cannot
  answer, because the request has to reach the gateway running on the desktop.
- Cloud/commercial answer: the same gateway is hosted and always reachable, so
  the user does not have to be in front of their computer or keep the local
  gateway application open. That always-available parity is a core reason to
  choose the cloud version.

## Integrations: partnerships and API keys

- The majority of email and basic account services must be integrated and kept
  working — on BOTH the open gateway and the cloud service. That means
  partnerships with the providers and obtaining/maintaining API keys.
- These connectors are core product surface, not extras: without working
  email/account integrations the gateway has nothing to govern.

## Self-hosting note

- Some open-source users may get the bright idea to host the gateway on a VM
  themselves to get always-on access without the cloud version. Possible in
  principle; noted for the record. The cloud version's offer stands on being
  managed, secure, and maintained — not on the local version being crippled.

## Why this matters

These are major features. Developed well, they are what will really promote
the gateway — the rules model, the pre-send check, deployment parity, and
working integrations are the product story.
