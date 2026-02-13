# Environment configuration

Single source for all env config. No other `.env` files.

| File              | Port | Use                     |
|-------------------|------|-------------------------|
| `development.env`  | 8079 | Local development       |
| `staging.env`     | 8279 | Local staging (pre-prod)|
| `production.env`  | 8179 | Production (VM)         |

Settings loads `envs/{ENVIRONMENT}.env` based on `ENVIRONMENT`.

**Kite credentials** (api_key, api_secret, access_token) go in `~/.kite-services/kite_token.json` — not in env files. Copy `kite_token.json.example` and add your values.
