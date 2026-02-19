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

- **Prod (VM):** Image is built in CI and pushed to ghcr.io. VM only pulls and restarts (~15–30 sec). No build on VM.
- **After merging to main:** Wait for [CI](https://github.com/ashok1995/kite-services/actions) to complete (~5–10 min), then deploy.
- **Staging:** Still builds locally; use `./deploy_to_staging.sh`.
- **Cleanup (prod only):** Script removes **kite-services** dangling images. Other services unaffected.

## Token persistence across deploys

- **Yes — existing token is reused.** The token is stored in `kite-credentials/kite_token.json` on the VM
  (mounted into the container as `/root/.kite-services/kite_token.json`). That directory is not in git and is
  not overwritten by `git pull` or the deploy script.
- On container start, the app loads the token from that file and verifies it via the Kite API (profile call).
  If the token is valid, the web app shows "already authenticated" and GET `/api/auth/status` returns
  `authenticated: true`, `token_valid: true`. No re-login is needed after a deploy unless the token has expired.
