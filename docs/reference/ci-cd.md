# CI/CD Reference

This repository uses GitHub Actions for CI, security scanning, release
automation, and deployment.

## Workflows

- `ci.yml`
  - Triggers: push/pull_request on `main`, manual dispatch
  - Jobs:
    - `lint`: `ruff` error-focused checks (`E,F,I,W`)
    - `compatibility (py3.11)`: unit test compatibility sweep
    - `test`: full test suite with `dev+science` extras
    - `package`: build wheel/sdist and run `twine check`
- `security.yml`
  - Triggers: push/pull_request on `main`, weekly schedule, manual dispatch
  - Jobs:
    - `dependency-audit`: `pip-audit`
    - `codeql`: static analysis (non-PR events)
- `release.yml`
  - Triggers: `v*` tags, manual dispatch with a tag
  - Jobs:
    - `verify-release-gate`:
      - Validates tag format (`vMAJOR.MINOR.PATCH`)
      - Verifies tag version equals `project.version` in `pyproject.toml`
      - Verifies matching version heading exists in `CHANGELOG.md`
      - Verifies tagged commit is reachable from `origin/main`
      - Runs lint/type/test gates (including `--cov-fail-under=100`)
    - Build artifacts (+ wheel smoke-import)
    - Publish GitHub Release (protected `release` environment)
    - Publish PyPI (protected `pypi` environment)
- `deploy.yml`
  - Trigger: manual dispatch
  - Syncs code, installs dependencies on remote host, restarts systemd service,
    and optionally runs smoke checks.

## Branch Protection

Recommended required status checks for `main`:

- `lint`
- `test`
- `package`

Also require:

- Pull request reviews (`>=1`)
- Conversation resolution
- Linear history
- No force-pushes
- No branch deletion

## Secrets and Variables

### Release

- PyPI Trusted Publishing (OIDC): no `PYPI_API_TOKEN` required by default
- `release` environment: recommended required reviewers before GitHub release
- `pypi` environment: required for publish job (already configured in workflow)

### Deploy

Required secrets:

- `DEPLOY_HOST`
- `DEPLOY_USER`
- `DEPLOY_SSH_PRIVATE_KEY`

Optional secret:

- `DEPLOY_SSH_PORT` (defaults to `22`)

Optional repository variables:

- `DEPLOY_REMOTE_DIR` (default `/opt/labclaw`)
- `DEPLOY_SERVICE_NAME` (default `labclaw`)

## Operational Notes

- The deploy workflow currently expects a root-capable deploy user because it
  provisions users and writes systemd units.
- `pip-audit` may show local package names (`labclaw`) as non-PyPI packages;
  this is expected and non-blocking.
- `security.yml` currently ignores `nltk` advisories `GHSA-rf74-v2fm-23pw`,
  `CVE-2026-33230`, and `CVE-2026-33231` because no upstream fixed version is
  published yet. Remove these ignore flags once a fixed `nltk` release exists.
