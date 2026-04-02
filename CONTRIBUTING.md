# Contributing to CloudGentic Gateway

Thank you for your interest in contributing!

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/cloudgentic-gateway.git`
3. Create a feature branch from `develop`: `git checkout -b feature/your-feature develop`
4. Make your changes
5. Run tests: `make test`
6. Commit using [Conventional Commits](https://www.conventionalcommits.org/): `git commit -m "feat(scope): description"`
7. Push and open a Pull Request against `develop`

## Branch Naming

- Feature: `feature/<name>` (e.g., `feature/slack-provider`)
- Bugfix: `bugfix/<name>` (e.g., `bugfix/token-refresh-race`)
- Docs: `docs/<name>` (e.g., `docs/api-reference`)
- Chore: `chore/<name>` (e.g., `chore/update-deps`)

## Code Standards

- **Python:** PEP 8, use `ruff` for linting
- **TypeScript:** ESLint config in project
- **Tests:** Unit tests required for every feature
- **Security:** Never log tokens. Never return tokens in API responses. Validate all inputs.

## Pull Request Checklist

- [ ] Branch is based on `develop`
- [ ] Tests pass locally
- [ ] `docker compose up` succeeds from clean state
- [ ] No secrets in code
- [ ] CHANGELOG.md updated

## Security Issues

Do NOT open public issues for security vulnerabilities. See [SECURITY.md](SECURITY.md).

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
