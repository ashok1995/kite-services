# Test VM – Connection & Runbook

**Use this doc when deploying, testing, or getting token on the test VM.**

## VM Connection

| Field | Value |
|-------|-------|
| Hostname | vm488109385.manageserver.in |
| IP | 203.57.85.72 |
| Username | root |
| OS | Ubuntu 24.04 |
| Project path on VM | /opt/kite-services |
| Service port | 8179 |

## Base URL

```
http://203.57.85.72:8179
```

## Commands (run from project root)

### Deploy

```bash
./deploy_to_prod.sh
```

### E2E tests against VM

```bash
TEST_BASE_URL=http://203.57.85.72:8179 pytest tests/e2e/test_prod_endpoints.py -v --tb=short
```

### Token flow

1. Get login URL: `curl -s http://203.57.85.72:8179/api/auth/login-url | jq .`
2. Open URL in browser, log in, copy `request_token` from redirect.
3. Exchange: `curl -X POST http://203.57.85.72:8179/api/auth/login -H "Content-Type: application/json" -d '{"request_token":"<TOKEN>"}' | jq .`
4. Verify: `curl -s http://203.57.85.72:8179/api/auth/status | jq .`

### Quick health check

```bash
curl -s http://203.57.85.72:8179/health | jq .
```
