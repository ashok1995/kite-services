# GitHub Secrets Setup - REQUIRED for CI/CD

## ⚠️ Important

The CI/CD pipeline **requires** GitHub Secrets to be configured. Without these, the pipeline will fail at the test or deployment stages.

## Required Secrets

Go to: **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

### 1. KITE_API_KEY

- **Name**: `KITE_API_KEY`
- **Value**: Your Kite Connect API key
- **How to get**: Check your `.env` file or Kite Connect dashboard
- **Example**: `dmy4m1i95o6myj60`

### 2. KITE_ACCESS_TOKEN

- **Name**: `KITE_ACCESS_TOKEN`
- **Value**: Your current Kite Connect access token
- **How to get**: Check your `.env` file or generate new one via login
- **Note**: This will be used for API tests

### 3. PROD_SSH_PRIVATE_KEY

- **Name**: `PROD_SSH_PRIVATE_KEY`
- **Value**: SSH private key for production server
- **Required for**: Production deployment stage

#### Generate SSH Key:

```bash
# Generate SSH key (on your local machine)
ssh-keygen -t ed25519 -C "github-actions-prod" -f ~/.ssh/github_actions_prod

# Copy public key to production server
ssh-copy-id -i ~/.ssh/github_actions_prod.pub root@203.57.85.72

# Display private key (copy ENTIRE output including BEGIN/END lines)
cat ~/.ssh/github_actions_prod
```

**Important**: Copy the ENTIRE output including:
```
-----BEGIN OPENSSH PRIVATE KEY-----
...key content...
-----END OPENSSH PRIVATE KEY-----
```

## Quick Setup Steps

1. **Go to GitHub**: https://github.com/ashok1995/kite-services/settings/secrets/actions

2. **Add each secret**:
   - Click "New repository secret"
   - Enter name and value
   - Click "Add secret"

3. **Verify secrets are added**:
   - You should see 3 secrets listed
   - Values are hidden (showing only `***`)

## Test Pipeline After Setup

After adding secrets, the pipeline will automatically re-run if it failed, or you can:

1. Make a small change and push:
   ```bash
   echo "# Test" >> README.md
   git add README.md
   git commit -m "test: Trigger CI/CD pipeline"
   git push origin main
   ```

2. Or manually trigger (if workflow_dispatch is enabled)

## Pipeline Behavior Without Secrets

### Without KITE_API_KEY / KITE_ACCESS_TOKEN:
- ❌ Integration tests will fail
- ❌ E2E tests will fail
- ❌ Production config tests will fail
- ✅ Unit tests may still pass
- ❌ Pipeline stops, no deployment

### Without PROD_SSH_PRIVATE_KEY:
- ✅ All tests can pass
- ✅ Image can be built
- ❌ Production deployment will fail
- ❌ Post-deployment tests will fail

## Verify Secrets Are Working

After adding secrets, check the pipeline logs:

1. Go to: https://github.com/ashok1995/kite-services/actions
2. Click on latest workflow run
3. Check test stages - should use secrets successfully
4. Check deployment stage - should SSH successfully

## Security Best Practices

- ✅ Never commit secrets to repository
- ✅ Use GitHub Secrets (encrypted)
- ✅ Rotate secrets regularly
- ✅ Use different keys for dev/prod if possible
- ✅ Limit SSH key permissions

## Troubleshooting

### Secret Not Found Error
- Verify secret name matches exactly (case-sensitive)
- Check you're adding to correct repository
- Ensure secret is in "Actions" secrets, not "Dependabot"

### SSH Connection Failed
- Verify public key is on production server
- Check SSH key format (should be OpenSSH format)
- Test SSH manually: `ssh -i ~/.ssh/github_actions_prod root@203.57.85.72`

### Tests Fail with "Invalid API Key"
- Verify KITE_API_KEY is correct
- Check KITE_ACCESS_TOKEN is valid (not expired)
- Regenerate token if needed

---

**After setting up secrets, the pipeline will work correctly!** 🚀
