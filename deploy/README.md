# Deploy Kite Services

Two scripts only: **prod** (GCP VM) and **staging** (local).

## Production — `deploy/deploy-prod.sh`

Deploys to GCP VM. Uses `gcloud`; image from ghcr.io (CI builds on push to main). VM pulls only (no build).

**Config:** Create `deploy/.deploy.env` (gitignored) with:

- `GCP_INSTANCE` – VM name (e.g. `stocks-vm`)
- `GCP_ZONE` – e.g. `us-central1-a`
- `GCP_PROJECT` – GCP project ID
- `VM_HOST` – VM external IP (e.g. `35.232.205.155`)
- `GITHUB_TOKEN` – GitHub PAT with `read:packages` (for ghcr.io pull)
- `KITE_API_KEY`, `KITE_API_SECRET` – optional; if set, writes kite_token.json on VM

**Run from repo root:**

```bash
./deploy/deploy-prod.sh
```

## Staging — `deploy/deploy-staging.sh`

Deploys locally (port 8279). Uses `develop` branch; builds image and runs `docker-compose.staging.yml`.

**Run from repo root:**

```bash
./deploy/deploy-staging.sh
```

Requires: no uncommitted changes; local `develop` in sync with `origin/develop`. Use `FULL_REBUILD=1` for a no-cache build.

## Without Docker (staging)

To run staging as a single process (no Docker): `./scripts/run-staging.sh` (port 8279, uses `envs/staging.env`).
