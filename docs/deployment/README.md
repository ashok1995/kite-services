# Deployment

| Doc | Purpose |
|-----|---------|
| [local-staging.md](local-staging.md) | **Local staging** – run on this machine (port 8279) before prod |
| [vm-details.md](vm-details.md) | VM connection & runbook – **prod only** |
| [production.md](production.md) | Production deployment guide (Docker) |
| [testing-and-deployment.md](testing-and-deployment.md) | Branch strategy, testing workflow |

## Before deploy (staging)

- **Commit and push first.** Staging deploy pulls from `origin/develop`. The script will **fail** if there are
  uncommitted changes or if local `develop` is ahead of `origin/develop`. Fix: commit and push, then run
  `./deploy_to_staging.sh`.

## Deploy speed

- **Default (with cache):** Deploy reuses Docker layers. Only changed layers rebuild (usually just `src/`),
  so deploy typically takes **1–3 minutes** instead of 30–60.
- **Full rebuild:** Use `FULL_REBUILD=1 ./deploy_to_prod.sh` or `FULL_REBUILD=1 ./deploy_to_staging.sh` when you
  changed `pyproject.toml`/`poetry.lock` or want a clean image. This runs `build --no-cache` (~30–60 min once).
- **Cleanup (this service only):** After each deploy, the script removes only **kite-services** dangling images.
  Other services on the same VM are unaffected. Image is labeled `project=kite-services` in the Dockerfile.

## Token persistence across deploys

- **Yes — existing token is reused.** The token is stored in `kite-credentials/kite_token.json` on the VM
  (mounted into the container as `/root/.kite-services/kite_token.json`). That directory is not in git and is
  not overwritten by `git pull` or the deploy script.
- On container start, the app loads the token from that file and verifies it via the Kite API (profile call).
  If the token is valid, the web app shows "already authenticated" and GET `/api/auth/status` returns
  `authenticated: true`, `token_valid: true`. No re-login is needed after a deploy unless the token has expired.
