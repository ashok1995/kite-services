# UI Integration Guide (Client / Production)

<!-- markdownlint-disable MD013 -->

**Flow:** Check api_key → Save api_key from web → Get callback URL → User logs in at Kite → Get request_token from callback URL → Exchange for access_token → Save access_token

**Production base URL:** `http://203.57.85.72:8179`

---

## 1. Check if api_key configured

```bash
curl -s http://203.57.85.72:8179/api/auth/credentials/status
```

**Response:** `{ "api_key_configured": true }` or `{ "api_key_configured": false }`

---

## 2. Save api_key (and api_secret) from web

<!-- pragma: allowlist secret -->

```bash
curl -X POST http://203.57.85.72:8179/api/auth/credentials \
  -H "Content-Type: application/json" \
  -d '{"api_key": "YOUR_API_KEY", "api_secret": "YOUR_API_SECRET"}'
```

**Response:** `{ "success": true, "message": "Credentials saved. Use callback URL for login." }`

api_secret is required to exchange request_token for access_token after Kite login.

---

## 3. Get callback URL

Set this as **Redirect URL** in Kite app at [developers.kite.trade](https://developers.kite.trade/). After login, Kite redirects here with `request_token` in the URL.

```bash
curl -s http://203.57.85.72:8179/api/token/callback-url
```

**Response:** `{ "callback_url": "http://203.57.85.72:8179/api/auth/callback", "configured": true }`

---

## 4. After Kite login – get access_token

User logs in at Kite, is redirected to callback URL with `?request_token=XXX`. Extract request_token from URL, then:

```bash
curl -X POST http://203.57.85.72:8179/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"request_token": "REQUEST_TOKEN_FROM_URL"}'
```

**Response:** `{ "status": "authenticated", "access_token": "...", "user_id": "...", "user_name": "..." }` – token is saved automatically.

---

## 5. Or: paste access_token directly

If user has access_token from elsewhere:

```bash
curl -X PUT http://203.57.85.72:8179/api/auth/token \
  -H "Content-Type: application/json" \
  -d '{"access_token": "YOUR_ACCESS_TOKEN"}'
```

---

## 6. Check token status

```bash
curl -s http://203.57.85.72:8179/api/auth/status
```

**Response:** `{ "token_valid": true, "user_id": "...", "user_name": "..." }` or `{ "token_valid": false }`

---

## Summary

| # | Endpoint | Purpose |
|---|----------|---------|
| 1 | `GET /api/auth/credentials/status` | Check if api_key configured |
| 2 | `POST /api/auth/credentials` | Save api_key + api_secret from web |
| 3 | `GET /api/token/callback-url` | Get callback URL for Kite app |
| 4 | `POST /api/auth/login` | Exchange request_token → access_token (saves automatically) |
| 5 | `PUT /api/auth/token` | Save access_token (when user pastes directly) |
| 6 | `GET /api/auth/status` | Check token valid |
