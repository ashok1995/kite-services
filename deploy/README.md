# Deployment — Single source of truth

## Environments

| Env        | Port | Image tag | Where it runs | How to deploy |
|------------|------|-----------|---------------|---------------|
| **Dev**    | 8079 | —         | Local (no Docker) | `poetry run python src/main.py` |
| **Staging**| 8279 | `:stage`  | Local laptop  | `./deploy_to_staging.sh` |
| **Prod**   | 8179 | `:latest` | GCP VM `35.232.205.155` | `./deploy_to_prod.sh` (or run directly on VM) |

## Image flow

```
feature branch ──PR──> develop ──merge──> main
                          │                  │
                    CI: build+push      CI: build+push
                    :stage tag          :latest tag
                          │                  │
                   staging pull         prod pull
```

## CI/CD (GitHub Actions)

- **Push to `develop`** → `.github/workflows/deploy-stage.yml` → builds + pushes `ghcr.io/ashok1995/kite-services:stage`
- **Push to `main`** → `.github/workflows/deploy-prod.yml` → builds + pushes `ghcr.io/ashok1995/kite-services:latest`
- **No Docker builds on PRs or feature branches**

## Deploy commands

### Staging (any laptop)
```bash
./deploy_to_staging.sh
```
Pulls `:stage` from GHCR, runs on port 8279.

### Production (from laptop via SSH, or directly on VM)
```bash
# From laptop (needs VM_PASSWORD set):
VM_PASSWORD=xxx ./deploy_to_prod.sh

# Or SSH into VM and run:
cd /opt/kite-services && git pull origin main
docker compose -f docker-compose.prod.yml down --remove-orphans
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
```
Pulls `:latest` from GHCR, runs on port 8179.

## Files

| File | Purpose |
|------|---------|
| `docker-compose.staging.yml` | Staging compose (GHCR `:stage` image) |
| `docker-compose.prod.yml` | Production compose (GHCR `:latest` image) |
| `deploy_to_staging.sh` | One-command staging deploy (local) |
| `deploy_to_prod.sh` | One-command prod deploy (SSH to VM) |
| `Dockerfile` | Image definition (used by CI only) |
