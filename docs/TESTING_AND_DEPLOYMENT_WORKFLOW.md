# Testing and Deployment Workflow

## Branch Strategy

- **main** – Production-ready code only. VM deploys from `main` via `git pull origin main`.
- **testing_and_improvement_v1.1** – Active testing and improvement branch.

## Workflow: testing_and_improvement_v1.1

```
1. Work on branch testing_and_improvement_v1.1
2. Test all endpoints (functional + e2e)
3. Find gaps/issues → fix
4. Run full test suite until confident
5. Commit changes on branch
6. You: manually review and merge to main (via PR or git merge)
7. On VM: git pull origin main → redeploy
```

### Rules

- **No SCP, rsync, or manual file transfer** to VM. All code must reach VM via `git pull origin main`.
- All changes are developed and tested on `testing_and_improvement_v1.1` before merge.
- Merge to `main` only after tests pass and you have reviewed the diff.

## Endpoint Test Sequence

1. **Test PROD first** (8179 on VM) – find gaps, fix
2. **Test DEV** (8079) – verify fixes locally
3. **Both pass** → ready to commit

```bash
# Step 1: Test prod
./tests/run_endpoint_tests.sh prod

# Step 2: After fixes, test dev (start dev server first: docker compose up or python src/main.py)
./tests/run_endpoint_tests.sh dev
```

## Running Tests

### Local / Dev (against localhost:8079)

```bash
# All tests (unit + integration + e2e)
poetry run pytest tests/ -v

# E2E only
poetry run pytest tests/e2e/ -v

# Functional/integration against live dev
TEST_BASE_URL=http://127.0.0.1:8079 poetry run pytest tests/integration/ tests/e2e/test_prod_endpoints.py -v
```

### Against Production (VM)

```bash
# Full prod endpoint test suite
TEST_BASE_URL=http://203.57.85.72:8179 poetry run pytest tests/e2e/test_prod_endpoints.py tests/integration/test_auth_token_flow.py -v

# Quick smoke
TEST_BASE_URL=http://203.57.85.72:8179 poetry run pytest tests/e2e/test_prod_endpoints.py -v -k "smoke"
```

### E2E In-Process (no live server)

```bash
# Runs against embedded ASGI app (no network)
poetry run pytest tests/e2e/test_deployment_reliability.py -v
```

## Test Types

| Type | Location | Purpose |
|------|----------|---------|
| **Unit** | `tests/unit/` | Pure logic, no I/O |
| **Integration** | `tests/integration/` | Live service, real HTTP |
| **E2E (in-process)** | `tests/e2e/test_deployment_reliability.py` | Full app lifecycle, contract validation |
| **E2E (prod)** | `tests/e2e/test_prod_endpoints.py` | All endpoints against prod URL |

## Deployment on VM

```bash
cd /opt/kite-services
git pull origin main
docker compose -f docker-compose.prod.yml up -d --force-recreate
curl -s http://localhost:8179/health
```

## Known Gaps (to fix on this branch)

| Endpoint | Gap | Status |
|----------|-----|--------|
| GET /api/auth/login-url | 404 on prod VM (not in current deploy) | Will work after merge + git pull |
| POST /api/opportunities/quick | 500 when Kite token invalid | Skip in test until credentials added; consider graceful fallback |
