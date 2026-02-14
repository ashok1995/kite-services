# Local Staging

**Staging runs strictly on this machine (Mac).**
Test changes here before deploying to prod on VM.

## Ports

| Env | Port | Base URL |
|-----|------|----------|
| Dev | 8079 | <http://localhost:8079> |
| **Staging** | **8279** | <http://localhost:8279> |
| Prod (VM) | 8179 | <http://203.57.85.72:8179> |

## Run staging (same process as prod — Docker)

Staging uses Docker the same way as prod. From repo root, after merging to `develop`:

```bash
./deploy_to_staging.sh
```

This fetches/checks out `develop`, builds with `docker-compose.staging.yml`,
runs containers on port 8279, and runs a health check.

**Optional (without Docker):** `./scripts/run-staging.sh` — uses
`envs/staging.env` and runs the app directly with Poetry.

## E2E tests against staging

```bash
TEST_BASE_URL=http://localhost:8279 pytest tests/e2e/test_prod_endpoints.py -v --tb=short
```

## Quick checks

```bash
curl -s http://localhost:8279/health | jq .
curl -s http://localhost:8279/api/auth/login-url | jq .
curl -s http://localhost:8279/api/auth/status | jq .  # token_valid when verified
```

Token saved to `~/.kite-services/kite_token.json` (survives git pull).

## Workflow

1. Merge feature/fix to `develop` → run `./deploy_to_staging.sh` (Docker staging).
2. Test on <http://localhost:8279> → fix issues if needed.
3. When confident → merge `develop` to `main` (Git UI) → run `./deploy_to_prod.sh`.
