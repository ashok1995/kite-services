# Deploy Kite Services on Production VM

**Port:** 8179  
**Branch:** `main`

---

## 1. On the VM (SSH in first)

```bash
# Go to project directory (adjust path if different)
cd /opt/kite-services

# Pull latest from main
git fetch origin
git checkout main
git pull origin main

# Ensure token file exists (create if missing)
mkdir -p ~/.kite-services
# Add api_key, api_secret, access_token to ~/.kite-services/kite_token.json
# (or /root/.kite-services/kite_token.json if running as root)
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

## 5. Paper trading (orders)

- Default in code is **paper trading ON** (safe).
- For **real orders** on prod, set in `envs/production.env`:
  - `KITE_PAPER_TRADING_MODE=false`
- Restart the service after changing env.
