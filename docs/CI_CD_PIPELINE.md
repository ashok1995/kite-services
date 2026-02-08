# CI/CD Pipeline Documentation

## Overview

The Kite Services project uses GitHub Actions for continuous integration and deployment with a multi-stage pipeline that ensures code quality, testing, and safe deployments.

## Pipeline Stages

### 1. **Code Quality & Linting** (`lint`)
- Runs on: All branches and PRs
- Purpose: Validate code quality and style
- Duration: ~2 minutes
- **Blocks**: Next stages if fails

### 2. **Unit Tests** (`unit-tests`)
- Runs on: All branches and PRs
- Purpose: Test individual components
- Coverage: Reports code coverage
- Duration: ~3-5 minutes
- **Blocks**: Next stages if fails

### 3. **Integration Tests** (`integration-tests`)
- Runs on: All branches and PRs
- Purpose: Test service interactions
- Services: Redis (test container)
- Duration: ~5-10 minutes
- **Blocks**: Next stages if fails

### 4. **E2E & Production Config Tests** (`e2e-tests`)
- Runs on: All branches and PRs
- Purpose: End-to-end and production readiness tests
- Includes: Production config validation
- Duration: ~10-15 minutes
- **Blocks**: Next stages if fails

### 5. **Build Docker Image** (`build-image`)
- Runs on: `main` and `dev` branches (push only)
- Purpose: Build and tag Docker image
- Registry: GitHub Container Registry (ghcr.io)
- Tags: Branch name, SHA, semantic version
- Duration: ~5-10 minutes
- **Conditional**: Only runs if previous stages pass

### 6. **Deploy to Test** (`deploy-test`)
- Runs on: `dev` branch (push only)
- Purpose: Deploy to test/staging environment
- Environment: Test server
- Duration: ~5 minutes
- **Conditional**: Only runs on `dev` branch

### 7. **Deploy to Production** (`deploy-production`)
- Runs on: `main` branch (push only)
- Purpose: Deploy to production
- Environment: Production server (203.57.85.72:8179)
- Duration: ~5-10 minutes
- **Conditional**: Only runs on `main` branch
- **Requires**: Manual approval (if configured)

### 8. **Post-Deployment Tests** (`post-deployment-tests`)
- Runs on: `main` branch (after production deploy)
- Purpose: Verify production deployment
- Tests: Smoke tests against live production
- Duration: ~2 minutes
- **Conditional**: Only runs after production deploy

## Branch Strategy

### `main` Branch
- **Purpose**: Production-ready code
- **Triggers**: Full pipeline including production deployment
- **Protection**: 
  - Requires PR approval
  - Requires all tests to pass
  - No direct pushes (use PRs)

### `dev` Branch
- **Purpose**: Development and integration testing
- **Triggers**: Full pipeline up to test deployment
- **Deployment**: Test environment only
- **Merges**: Feature branches → dev → main

### `feature/*` Branches
- **Purpose**: Feature development
- **Triggers**: Lint, unit, integration, E2E tests only
- **No Deployment**: Tests only, no image building
- **Merges**: Feature → dev → main

## Workflow Files

### `.github/workflows/ci-cd.yml`
Main CI/CD pipeline with all stages.

### `.github/workflows/pr-checks.yml`
Lightweight checks for pull requests (faster feedback).

## Deployment Conditions

### Test Environment (dev branch)
```yaml
if: github.ref == 'refs/heads/dev' && github.event_name == 'push'
```
- Automatically deploys after all tests pass
- No manual approval required
- Safe for frequent deployments

### Production Environment (main branch)
```yaml
if: github.ref == 'refs/heads/main' && github.event_name == 'push'
```
- Deploys after all tests pass
- Can require manual approval (configure in GitHub)
- Only merges from `dev` branch

## Required GitHub Secrets

Configure these in GitHub repository settings:

1. **KITE_API_KEY**: Kite Connect API key
2. **KITE_ACCESS_TOKEN**: Kite Connect access token
3. **PROD_SSH_PRIVATE_KEY**: SSH private key for production server
4. **GITHUB_TOKEN**: Auto-provided by GitHub Actions

## Manual Deployment

If needed, you can manually trigger deployments:

```bash
# Deploy to test
git push origin dev

# Deploy to production
git checkout main
git merge dev
git push origin main
```

## Rollback Procedure

If production deployment fails:

1. **Automatic**: Post-deployment tests will fail, deployment marked as failed
2. **Manual Rollback**:
   ```bash
   ssh root@203.57.85.72
   cd /opt/kite-services
   docker compose -f docker-compose.prod.yml pull
   docker compose -f docker-compose.prod.yml up -d --force-recreate
   ```

## Monitoring Pipeline

### View Pipeline Status
- GitHub Actions tab in repository
- Each stage shows pass/fail status
- Click stage for detailed logs

### Pipeline Notifications
- Email on failure (configure in GitHub)
- Slack/Discord webhooks (optional)
- Status badges in README

## Best Practices

1. **Always test locally first**:
   ```bash
   poetry install
   poetry run pytest
   ```

2. **Keep PRs small**: Easier to review and test

3. **Run tests before pushing**:
   ```bash
   poetry run pytest tests/
   ```

4. **Check pipeline before merging**: Ensure all stages pass

5. **Monitor production after deploy**: Check `/health` and `/metrics`

## Troubleshooting

### Pipeline Fails at Lint Stage
- Check code style
- Fix syntax errors
- Run: `poetry run python -m py_compile src/**/*.py`

### Pipeline Fails at Test Stage
- Run tests locally: `poetry run pytest tests/`
- Check test logs in GitHub Actions
- Fix failing tests

### Deployment Fails
- Check SSH key permissions
- Verify server connectivity
- Check Docker logs: `docker compose logs`

### Image Build Fails
- Check Dockerfile syntax
- Verify dependencies in `pyproject.toml`
- Check build logs in GitHub Actions

## Future Enhancements

- [ ] Add security scanning (Snyk, Dependabot)
- [ ] Add performance testing
- [ ] Add database migration checks
- [ ] Add blue-green deployment
- [ ] Add canary releases
- [ ] Add automated rollback on health check failure
