# Local Staging

**Staging runs strictly on this machine (Mac).**
Test changes here before deploying to prod on VM.

## Ports

| Env | Port | Base URL |
|-----|------|----------|
| Dev | 8079 | <http://localhost:8079> |
| **Staging** | **8279** | <http://localhost:8279> |
| Prod (VM) | 8179 | <http://203.57.85.72:8179> |

## Run staging

```bash
git pull origin main
ENVIRONMENT=staging SERVICE_PORT=8279 poetry run python src/main.py
```

Or use the script:

```bash
./scripts/run-staging.sh
```

## E2E tests against staging

```bash
TEST_BASE_URL=http://localhost:8279 pytest tests/e2e/test_prod_endpoints.py -v --tb=short
```

## Quick checks

```bash
curl -s http://localhost:8279/health | jq .
curl -s http://localhost:8279/api/auth/login-url | jq .
```

## Workflow

1. Run staging locally → test changes → fix issues.
2. When confident → commit, push, merge to main.
3. Deploy to prod VM via `./deploy_to_prod.sh`.
