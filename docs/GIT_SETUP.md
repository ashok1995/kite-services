# Git Setup & CI/CD Guide

## Initial Git Setup

### 1. Initialize Repository (if not already done)

```bash
cd /path/to/kite-services
git init
git branch -M main  # or 'master' if preferred
```

### 2. Add Remote Repository

```bash
# Create repository on GitHub first, then:
git remote add origin https://github.com/YOUR_USERNAME/kite-services.git
# OR with SSH:
git remote add origin git@github.com:YOUR_USERNAME/kite-services.git
```

### 3. Stage All Files

```bash
git add .
```

### 4. Create Initial Commit

```bash
git commit -m "Initial commit: Kite Services with CI/CD pipeline

- FastAPI application with consolidated API
- Production monitoring and logging
- Docker deployment setup
- Poetry dependency management
- Comprehensive test suite
- CI/CD pipeline with GitHub Actions"
```

### 5. Push to GitHub

```bash
# First push
git push -u origin main

# Or if using master:
git push -u origin master
```

## Branch Strategy

### Main/Master Branch
- **Purpose**: Production-ready code
- **Deployment**: Automatic production deployment
- **Protection**: 
  - Require PR reviews
  - Require status checks to pass
  - No direct pushes

### Develop Branch
- **Purpose**: Integration and testing
- **Deployment**: Image build + test stage only
- **Workflow**: Feature branches → develop → main

### Feature Branches
- **Purpose**: Feature development
- **Naming**: `feature/feature-name`
- **Workflow**: Feature → develop → main

## Setting Up GitHub Secrets

Go to: `Settings` → `Secrets and variables` → `Actions`

Add these secrets:

1. **KITE_API_KEY**: Your Kite Connect API key
2. **KITE_ACCESS_TOKEN**: Your Kite Connect access token
3. **PROD_SSH_PRIVATE_KEY**: SSH private key for production server

### Generate SSH Key for Production

```bash
# On your local machine
ssh-keygen -t ed25519 -C "github-actions-prod" -f ~/.ssh/github_actions_prod

# Copy public key to production server
ssh-copy-id -i ~/.ssh/github_actions_prod.pub root@203.57.85.72

# Copy private key content to GitHub Secrets
cat ~/.ssh/github_actions_prod
# Copy the entire output (including -----BEGIN and -----END) to PROD_SSH_PRIVATE_KEY secret
```

## CI/CD Pipeline Flow

### For `develop` Branch:
1. ✅ Lint & Code Quality
2. ✅ Unit Tests
3. ✅ Integration Tests
4. ✅ E2E Tests
5. ✅ Build Docker Image → Push to registry
6. ✅ Test Docker Image (run container, test health)
7. ❌ **NO PRODUCTION DEPLOYMENT**

### For `main/master` Branch:
1. ✅ Lint & Code Quality
2. ✅ Unit Tests
3. ✅ Integration Tests
4. ✅ E2E Tests
5. ✅ Build Docker Image → Push to registry
6. ✅ Deploy to Production
7. ✅ Post-Deployment Smoke Tests

## Workflow Examples

### Feature Development

```bash
# Create feature branch
git checkout -b feature/new-endpoint

# Make changes, commit
git add .
git commit -m "Add new endpoint"

# Push feature branch
git push origin feature/new-endpoint

# Create PR: feature/new-endpoint → develop
# After PR merge, develop branch will:
# - Build image
# - Test image
# - NOT deploy to production
```

### Deploy to Production

```bash
# Merge develop to main
git checkout main
git pull origin main
git merge develop
git push origin main

# This triggers:
# - Full test suite
# - Image build
# - Production deployment
# - Post-deployment tests
```

## Viewing Pipeline Status

1. Go to GitHub repository
2. Click "Actions" tab
3. See all workflow runs
4. Click on a run to see detailed logs

## Manual Deployment (if needed)

```bash
# SSH to production
ssh root@203.57.85.72

# Navigate to project
cd /opt/kite-services

# Pull latest code
git pull origin main

# Rebuild and restart
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d

# Verify
curl http://localhost:8179/health
```

## Troubleshooting

### Pipeline Fails
1. Check "Actions" tab for error details
2. Review logs in failed stage
3. Fix issues locally
4. Push fixes

### Production Deployment Fails
1. Check SSH key in GitHub Secrets
2. Verify server connectivity
3. Check Docker logs: `docker compose logs`
4. Manual rollback if needed

### Image Build Fails
1. Check Dockerfile syntax
2. Verify dependencies in `pyproject.toml`
3. Check build logs in GitHub Actions

## Best Practices

1. **Always test locally first**:
   ```bash
   poetry install
   poetry run pytest
   ```

2. **Keep commits atomic**: One feature/fix per commit

3. **Write meaningful commit messages**:
   ```
   feat: Add new market data endpoint
   fix: Resolve CORS parsing issue
   docs: Update API documentation
   ```

4. **Create PRs for review**: Don't push directly to main

5. **Monitor pipeline**: Check Actions tab regularly

6. **Test in develop first**: Merge to develop, test, then merge to main
