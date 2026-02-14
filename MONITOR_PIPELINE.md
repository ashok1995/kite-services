# Monitor CI/CD Pipeline

## Pipeline Status

Your code has been pushed to `main` branch. The CI/CD pipeline is now running.

## View Pipeline Status

### Option 1: GitHub Web Interface

1. Go to: <https://github.com/ashok1995/kite-services/actions>
2. Click on the latest workflow run
3. See all stages and their status

### Option 2: GitHub CLI (if installed)

```bash
gh run list --workflow=ci-cd.yml
gh run watch
```

## Pipeline Stages (in order)

### ✅ Stage 1: Lint

- Code quality checks
- Duration: ~2 minutes

### ✅ Stage 2: Unit Tests

- Component tests
- Coverage check (70% minimum)
- Duration: ~3-5 minutes

### ✅ Stage 3: Integration Tests

- Service integration tests
- Redis connectivity
- Duration: ~5-10 minutes

### ✅ Stage 4: E2E Tests

- End-to-end tests
- Production config tests
- Deployment reliability tests (27 tests)
- Duration: ~10-15 minutes

### ✅ Stage 5: Build Docker Image

- Builds Docker image
- Pushes to GitHub Container Registry
- Duration: ~5-10 minutes

### ✅ Stage 6: Deploy to Production

- Only runs if ALL tests passed
- Deploys to 203.57.85.72:8179
- Duration: ~5 minutes

### ✅ Stage 7: Post-Deployment Tests

- Smoke tests against production
- Verifies deployment success
- Duration: ~2 minutes

## Expected Timeline

- **Total Duration**: ~30-45 minutes
- **Test Stages**: ~20-30 minutes
- **Build & Deploy**: ~10-15 minutes

## What to Watch For

### ✅ Success Indicators

- All stages show green checkmarks ✅
- "Deploy to Production" stage completes
- "Post-Deployment Tests" passes
- Production endpoint responds: <http://203.57.85.72:8179/health>

### ❌ Failure Indicators

- Any stage shows red X ❌
- Pipeline stops at failed stage
- Deployment is automatically blocked

## If Pipeline Fails

1. **Check the failed stage** in GitHub Actions
2. **Review logs** for error details
3. **Fix the issue** locally
4. **Commit and push** again
5. **Pipeline re-runs** automatically

## Monitor Production After Deployment

```bash
# Check health
curl http://203.57.85.72:8179/health

# Check metrics
curl http://203.57.85.72:8179/metrics

# View logs (SSH to server)
ssh root@203.57.85.72
cd /opt/kite-services
docker compose -f docker-compose.prod.yml logs -f kite-services
```

## Quick Status Check

```bash
# Check if production is responding
curl -s http://203.57.85.72:8179/health | python3 -m json.tool
```

---

**Pipeline URL**: <https://github.com/ashok1995/kite-services/actions>

**Production URL**: <http://203.57.85.72:8179>
