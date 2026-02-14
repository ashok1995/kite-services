# Deploy Kite Services on Production VM

**Port:** 8179  
**Branch:** `main` (deploy only after merging from develop/feature)

---

## 0. VM checklist (before deploy)

SSH to the VM and ensure:

**Credentials (required for Docker run):**

- In `/opt/kite-services`, create `kite-credentials` and token file
  (compose mounts it as `/root/.kite-services`):

  ```bash
  mkdir -p /opt/kite-services/kite-credentials
  # Create kite-credentials/kite_token.json with: api_key, api_secret, access_token
  ```

**Resources (if health check fails or OOM):**

```bash
df -h                    # disk space
free -m                  # memory
docker stats --no-stream # container CPU/memory
```

If disk or memory is full, free space or increase VM resources before redeploying.

---

## 1. On the VM (SSH in first)

```bash
# Go to project directory (adjust path if different)
cd /opt/kite-services

# Pull latest from main
git fetch origin
git checkout main
git pull origin main

# Ensure token file exists for Docker (see section 0)
mkdir -p kite-credentials
# Add kite_token.json with api_key, api_secret, access_token inside kite-credentials/
```

---

## 2. Run the service

### Option A: Direct run (no Docker)

```bash
cd /opt/kite-services
export ENVIRONMENT=production
source venv/bin/activate   # or: poetry run
python src/main.py
```

Run in background (e.g. with nohup or systemd):

```bash
nohup env ENVIRONMENT=production python src/main.py > logs/kite-prod.log 2>&1 &
```

### Option B: Docker

```bash
cd /opt/kite-services
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d --force-recreate
```

---

## 3. Verify

```bash
curl -s http://localhost:8179/health | jq .
curl -s http://localhost:8179/api/auth/status | jq .
```

---

## 4. Token refresh (no restart)

From anywhere (browser or script):

1. Get login URL: `GET http://YOUR_VM_IP:8179/api/auth/login-url`
2. Open URL, log in, get `request_token` from redirect.
3. Update token: `POST http://YOUR_VM_IP:8179/api/auth/login`
   with body `{"request_token": "..."}`

Service keeps running; no restart needed.

---

## 5. Branch and deploy flow

- **Feature work:** Use a feature branch (e.g. `fix/prod-deployment-vm`); never
  commit directly to `main`.
- **Deploy-related changes:** Can go on `develop` or a fix branch.
- **Merge to main:** Done by you via **Git UI** (e.g. GitHub/GitLab PR). The
  deploy script on the VM uses `origin/main`; run deploy only after merging.
- **Updating prod:** **First** merge your branch into `main` in the Git UI,
  **then** run deploy from your machine:

  ```bash
  export VM_PASSWORD=your_vm_password
  ./deploy_to_prod.sh
  ```

- **Never** push directly to `main`; merge via Git UI only. Agent will remind:
  merge to main first, then deploy.

---

## 6. Paper trading (orders)

- Default in code is **paper trading ON** (safe).
- For **real orders** on prod, set in `envs/production.env`:
  - `KITE_PAPER_TRADING_MODE=false`
- Restart the service after changing env.
