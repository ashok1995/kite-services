# Push Code to GitHub - Quick Guide

## ✅ Repository is Ready

Your code has been committed and is ready to push to GitHub.

## Step 1: Create GitHub Repository

1. Go to <https://github.com/new>
2. Repository name: `kite-services`
3. Description: "Kite Trading Services API with CI/CD"
4. Choose: **Private** (recommended for trading app)
5. **DO NOT** initialize with README, .gitignore, or license (we already have these)
6. Click "Create repository"

## Step 2: Add Remote and Push

```bash
# Add remote (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/kite-services.git

# Or with SSH (if you have SSH keys set up):
git remote add origin git@github.com:YOUR_USERNAME/kite-services.git

# Push main branch
git push -u origin main
```

## Step 3: Create Develop Branch

```bash
# Create and switch to develop branch
git checkout -b develop

# Push develop branch
git push -u origin develop

# Switch back to main
git checkout main
```

## Step 4: Set Up GitHub Secrets

Go to your repository: `Settings` → `Secrets and variables` → `Actions`

Add these secrets:

### 1. KITE_API_KEY

- Name: `KITE_API_KEY`
- Value: Your Kite Connect API key (from `.env`)

### 2. KITE_ACCESS_TOKEN

- Name: `KITE_ACCESS_TOKEN`
- Value: Your current Kite Connect access token

### 3. PROD_SSH_PRIVATE_KEY

- Name: `PROD_SSH_PRIVATE_KEY`
- Value: SSH private key for production server

#### Generate SSH Key for Production

```bash
# Generate SSH key
ssh-keygen -t ed25519 -C "github-actions-prod" -f ~/.ssh/github_actions_prod

# Copy public key to production server
ssh-copy-id -i ~/.ssh/github_actions_prod.pub root@203.57.85.72

# Display private key (copy entire output including BEGIN/END lines)
cat ~/.ssh/github_actions_prod

# Paste the entire output into PROD_SSH_PRIVATE_KEY secret
```

## Step 5: Protect Branches (Recommended)

### Protect Main Branch

1. Go to: `Settings` → `Branches`
2. Add rule for `main`:
   - ✅ Require a pull request before merging
   - ✅ Require approvals: 1
   - ✅ Require status checks to pass
   - ✅ Require branches to be up to date
   - ✅ Include administrators

### Protect Develop Branch

1. Add rule for `develop`:
   - ✅ Require a pull request before merging
   - ✅ Require status checks to pass

## Step 6: Verify CI/CD Pipeline

1. Go to `Actions` tab in GitHub
2. You should see workflows ready
3. Push a test commit to trigger:

```bash
# Make a small change
echo "# Test" >> README.md
git add README.md
git commit -m "test: Trigger CI/CD pipeline"
git push origin main
```

4. Watch the pipeline run in `Actions` tab

## CI/CD Pipeline Behavior

### When you push to `develop`

- ✅ Runs all tests
- ✅ Builds Docker image
- ✅ Tests Docker image (runs container, checks health)
- ❌ **Does NOT deploy to production**

### When you push to `main`

- ✅ Runs all tests
- ✅ Builds Docker image
- ✅ Deploys to production (203.57.85.72:8179)
- ✅ Runs post-deployment smoke tests

## Workflow

### Feature Development

```bash
# Create feature branch
git checkout -b feature/new-feature

# Make changes, commit
git add .
git commit -m "feat: Add new feature"

# Push and create PR
git push origin feature/new-feature
# Create PR: feature/new-feature → develop
```

### Deploy to Production

```bash
# Merge develop to main
git checkout main
git pull origin main
git merge develop
git push origin main
# This triggers production deployment
```

## Troubleshooting

### Push Fails - Authentication

```bash
# Use personal access token instead
git remote set-url origin https://YOUR_TOKEN@github.com/YOUR_USERNAME/kite-services.git
```

### Pipeline Fails

- Check `Actions` tab for error details
- Verify secrets are set correctly
- Check SSH key permissions

### Production Deployment Fails

- Verify `PROD_SSH_PRIVATE_KEY` secret is correct
- Check server connectivity
- Review deployment logs in Actions

## Next Steps

1. ✅ Push code to GitHub
2. ✅ Set up GitHub Secrets
3. ✅ Protect branches
4. ✅ Test CI/CD pipeline
5. ✅ Start developing features!

## Quick Commands Reference

```bash
# Check status
git status

# See remote
git remote -v

# Push main
git push origin main

# Push develop
git push origin develop

# Create feature branch
git checkout -b feature/name

# View pipeline status
# Go to: https://github.com/YOUR_USERNAME/kite-services/actions
```

---

**Your repository is ready! Just add the remote and push! 🚀**
