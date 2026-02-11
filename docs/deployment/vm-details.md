# Test VM – Prod Only

**VM runs prod only.** Staging runs locally (see [local-staging.md](local-staging.md)).

## VM Connection

| Field | Value |
|-------|-------|
| Hostname | vm488109385.manageserver.in |
| IP | 203.57.85.72 |
| Username | root |
| OS | Ubuntu 24.04 |
| Project path on VM | /opt/kite-services |

## Prod (VM)

| Port | Base URL |
|------|----------|
| 8179 | <http://203.57.85.72:8179> |

### Deploy

```bash
./deploy_to_prod.sh
```

### E2E tests against prod

```bash
TEST_BASE_URL=http://203.57.85.72:8179 \
  pytest tests/e2e/test_prod_endpoints.py -v --tb=short
```

### Token flow (prod)

1. Get login URL: `curl -s http://203.57.85.72:8179/api/auth/login-url | jq .`
2. Open URL in browser, log in, copy `request_token` from redirect.
3. Exchange:

   ```bash
   curl -X POST http://203.57.85.72:8179/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{"request_token":"<TOKEN>"}' | jq .
   ```

4. Verify: `curl -s http://203.57.85.72:8179/api/auth/status | jq .`

### Health check

```bash
curl -s http://203.57.85.72:8179/health | jq .
```
