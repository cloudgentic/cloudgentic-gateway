# CloudGentic Gateway -- Git Workflow

## Branches

| Branch | Purpose |
|--------|---------|
| `main` | Production-ready, tagged releases |
| `develop` | Integration branch, PRs merge here |
| `feature/*` | Feature branches off `develop` |
| `bugfix/*` | Bug fix branches off `develop` |
| `docs/*` | Documentation branches off `develop` |

## Commit Convention

We use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(scope): add new feature
fix(scope): fix a bug
chore: maintenance task
docs: documentation only
test: add or update tests
```

### Scopes

`api`, `auth`, `vault`, `rules`, `providers/google`, `mcp`, `dashboard`, `audit`, `db`, `docker`, `ci`

## Pull Request Process

1. Branch from `develop`
2. Make changes, commit with conventional commits
3. Open PR against `develop`
4. All checks must pass
5. Squash merge or regular merge

## Releases

1. Create PR from `develop` to `main`
2. Review and merge
3. Tag with version: `git tag v0.1.0`
4. Push tag: `git push origin v0.1.0`
