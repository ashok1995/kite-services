# Quick Start - CI/CD Pipeline

## ✅ Code Pushed Successfully

Your code has been pushed to the `main` branch. The CI/CD pipeline is now running.

## 🔗 View Pipeline

**GitHub Actions**: <https://github.com/ashok1995/kite-services/actions>

Click on the latest workflow run to see:

- ✅ Test stages running
- ✅ Docker image being built
- ✅ Production deployment (if tests pass)

## ⚠️ Required: Set Up GitHub Secrets

The pipeline needs secrets to run tests and deploy. **Set these up now:**

### Quick Setup

1. **Go to Secrets**: <https://github.com/ashok1995/kite-services/settings/secrets/actions>

2. **Add 3 Secrets**:

   **Secret 1: KITE_API_KEY**

   ```
   Name: KITE_API_KEY
   Value: dmy4m1i95o6myj60 (from your .env)
   ```

   **Secret 2: KITE_ACCESS_TOKEN**

   ```
   Name: KITE_ACCESS_TOKEN
   Value: 0jxjnbflzXVzX4EzjYSziVmDnB3yFvf1 (from your .env)
   ```

   **Secret 3: PROD_SSH_PRIVATE_KEY**

   ```bash
   # Generate SSH key
   ssh-keygen -t ed25519 -C "github-actions" -f ~/.ssh/github_actions_prod

   # Copy public key to server
   ssh-copy-id -i ~/.ssh/github_actions_prod.pub root@203.57.85.72

   # Copy private key (entire output)
   cat ~/.ssh/github_actions_prod
   # Paste entire output (including BEGIN/END lines) to GitHub Secret
   ```

3. **Pipeline will automatically re-run** after secrets are added

## 📊 Pipeline Stages

1. **Lint** (2 min) - Code quality ✅
2. **Unit Tests** (5 min) - Component tests ✅
3. **Integration Tests** (10 min) - Service tests ✅
4. **E2E Tests** (15 min) - End-to-end + production config ✅
5. **Build Image** (10 min) - Docker image build ✅
6. **Deploy Production** (5 min) - Deploy to 203.57.85.72:8179 ✅
7. **Post-Deploy Tests** (2 min) - Smoke tests ✅

**Total**: ~45-50 minutes

## 🎯 What Happens Next

### If Secrets Are Set Up

- ✅ All tests run
- ✅ Docker image built and pushed to GitHub Container Registry
- ✅ Production deployment happens automatically
- ✅ Post-deployment tests verify success

### If Secrets Are Missing

- ⚠️ Tests will fail (can't connect to APIs)
- ⚠️ Deployment will fail (can't SSH to server)
- ✅ You can still see the pipeline structure

## 🔍 Monitor Pipeline

### Option 1: GitHub Web Interface

1. Go to: <https://github.com/ashok1995/kite-services/actions>
2. Click latest workflow run
3. Watch stages complete in real-time

### Option 2: Check Production

After deployment completes:

```bash
# Health check
curl http://203.57.85.72:8179/health

# Metrics
curl http://203.57.85.72:8179/metrics
```

## ✅ Success Criteria

Pipeline is successful when:

- ✅ All test stages pass (green checkmarks)
- ✅ Docker image built successfully
- ✅ Production deployment completed
- ✅ Post-deployment tests passed
- ✅ Production endpoint responds: <http://203.57.85.72:8179/health>

## 🐛 Troubleshooting

### Pipeline Fails at Tests

- Check if secrets are set up
- Review test logs in GitHub Actions
- Run tests locally: `poetry run pytest`

### Pipeline Fails at Deployment

- Verify PROD_SSH_PRIVATE_KEY is correct
- Check SSH key is on production server
- Test SSH manually: `ssh root@203.57.85.72`

### Production Not Responding

- Check container logs: `docker compose logs kite-services`
- Verify port 8179 is accessible
- Check firewall settings

---

**🚀 Your pipeline is running! Check GitHub Actions to see progress.**
