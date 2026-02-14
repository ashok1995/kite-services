# Authentication & Access Token Generation - cURL Commands

Complete reference for all authentication endpoints with ready-to-use cURL commands.

**Base URLs:**

- **Development**: `http://localhost:8079`
- **Production**: `http://203.57.85.72:8179`

---

## 1. Check API Key Configuration Status

Check if `api_key` is already configured on the server.

```bash
# Production
curl -s http://203.57.85.72:8179/api/auth/credentials/status | python3 -m json.tool

# Development
curl -s http://localhost:8079/api/auth/credentials/status | python3 -m json.tool
```

**Response:**

```json
{
    "api_key_configured": true,
    "message": null
}
```

---

## 2. Set API Key & Secret (First-Time Setup)

Save `api_key` and `api_secret` to the server's token file. Required before login flow.

```bash
# Production
curl -X POST http://203.57.85.72:8179/api/auth/credentials \
  -H "Content-Type: application/json" \
  -d '{
    "api_key": "YOUR_KITE_API_KEY",
    "api_secret": "YOUR_KITE_API_SECRET"
  }' | python3 -m json.tool
<!-- pragma: allowlist secret -->

# Development
curl -X POST http://localhost:8079/api/auth/credentials \
  -H "Content-Type: application/json" \
  -d '{
    "api_key": "YOUR_KITE_API_KEY",
    "api_secret": "YOUR_KITE_API_SECRET"
  }' | python3 -m json.tool
```

**Response:**

```json
{
    "success": true,
    "message": "Credentials saved. Use callback URL for login."
}
```

---

## 3. Get Callback URL

Get the callback/redirect URL to configure in your Kite Connect app at [developers.kite.trade](https://developers.kite.trade/).

```bash
# Production
curl -s http://203.57.85.72:8179/api/token/callback-url | python3 -m json.tool

# Development
curl -s http://localhost:8079/api/token/callback-url | python3 -m json.tool
```

**Response:**

```json
{
    "callback_url": "http://203.57.85.72:8179/api/redirect",
    "configured": true,
    "message": null
}
```

**Action:** Copy the `callback_url` and set it as **Redirect URL** in your Kite Connect app settings.

---

## 4. Get Kite Login URL

Get the Kite Connect OAuth login URL. Open this URL in your browser to start the login flow.

```bash
# Production
curl -s http://203.57.85.72:8179/api/auth/login-url | python3 -m json.tool

# Development
curl -s http://localhost:8079/api/auth/login-url | python3 -m json.tool
```

**Response:**

```json
{
    "login_url": "https://kite.zerodha.com/connect/login?api_key=dmy4m1i95o6myj60&v=3",
    "message": "Open URL, login, copy request_token from redirect"
}
```

**Action:**

1. Open the `login_url` in your browser
2. Log in to Kite
3. After login, Kite redirects to your callback URL with `request_token` in the query string
4. Copy the `request_token` from the redirect URL (e.g., `?request_token=XXX&status=success`)

---

## 5. Exchange Request Token for Access Token

Generate an `access_token` from the `request_token` obtained after Kite login.

```bash
# Production
curl -X POST http://203.57.85.72:8179/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "request_token": "YOUR_REQUEST_TOKEN_FROM_REDIRECT"
  }' | python3 -m json.tool

# Development
curl -X POST http://localhost:8079/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "request_token": "YOUR_REQUEST_TOKEN_FROM_REDIRECT"
  }' | python3 -m json.tool
```

**Response:**

```json
{
    "status": "authenticated",
    "access_token": "b4b0WC64hcmGsVD6a5ARqii0174ezmVU",
    "user_id": "YF0364",
    "user_name": "Ashok Kumar",
    "email": "akm551995@gmail.com",
    "broker": "ZERODHA",
    "exchanges": ["BSE", "NFO", "BCD", "BFO", "NSE", "MF"],
    "products": ["CNC", "NRML", "MIS", "BO", "CO"],
    "order_types": ["MARKET", "LIMIT", "SL", "SL-M"],
    "message": "Authentication successful",
    "timestamp": "2026-02-11T13:09:04.674976"
}
```

**Note:** This endpoint does **NOT** persist the token to file. Use `PUT /api/auth/token` (step 6) to save it permanently.

---

## 6. Save Access Token to File (Persist)

Save the `access_token` to the server's token file so it persists across restarts. Use this after step 5.

```bash
# Production
curl -X PUT http://203.57.85.72:8179/api/auth/token \
  -H "Content-Type: application/json" \
  -d '{
    "access_token": "YOUR_ACCESS_TOKEN",
    "user_id": "YF0364"
  }' | python3 -m json.tool

# Development
curl -X PUT http://localhost:8079/api/auth/token \
  -H "Content-Type: application/json" \
  -d '{
    "access_token": "YOUR_ACCESS_TOKEN",
    "user_id": "YF0364"
  }' | python3 -m json.tool
```

**Response:**

```json
{
    "status": "authenticated",
    "access_token": "b4b0WC64hcmGsVD6a5ARqii0174ezmVU",
    "user_id": "YF0364",
    "user_name": "Ashok Kumar",
    "email": "akm551995@gmail.com",
    "broker": "ZERODHA",
    "exchanges": ["BSE", "NFO", "BCD", "BFO", "NSE", "MF"],
    "products": ["CNC", "NRML", "MIS", "BO", "CO"],
    "order_types": ["MARKET", "LIMIT", "SL", "SL-M"],
    "message": "Token updated successfully",
    "timestamp": "2026-02-11T13:09:04.674976"
}
```

---

## 7. Check Token Status (Diagnostic)

Comprehensive diagnostic endpoint to check token configuration and validity. Use when services (quotes, trading, opportunities) fail.

```bash
# Production
curl -s http://203.57.85.72:8179/api/auth/token-status | python3 -m json.tool

# Development
curl -s http://localhost:8079/api/auth/token-status | python3 -m json.tool
```

**Response (Token Valid):**

```json
{
    "api_key_configured": true,
    "access_token_present": true,
    "token_file_path": "/root/.kite-services/kite_token.json",
    "kite_client_initialized": true,
    "profile_verified": true,
    "message": "Token valid - all Kite APIs (quotes, trading) should work",
    "action_required": null,
    "timestamp": "2026-02-11T16:41:43.739619"
}
```

**Response (Token Missing/Invalid):**

```json
{
    "api_key_configured": true,
    "access_token_present": false,
    "token_file_path": "/root/.kite-services/kite_token.json",
    "kite_client_initialized": false,
    "profile_verified": false,
    "message": "No access_token in file - complete login flow",
    "action_required": "1. GET /api/auth/login-url\n2. Open URL, login, copy request_token from redirect\n3. POST /api/auth/login with request_token",
    "timestamp": "2026-02-11T16:41:43.739619"
}
```

---

## 8. Check Authentication Status

Check current authentication status and user information.

```bash
# Production
curl -s http://203.57.85.72:8179/api/auth/status | python3 -m json.tool

# Development
curl -s http://localhost:8079/api/auth/status | python3 -m json.tool
```

**Response (Authenticated):**

```json
{
    "status": "authenticated",
    "authenticated": true,
    "token_valid": true,
    "user_id": "YF0364",
    "user_name": "Ashok Kumar",
    "broker": "ZERODHA",
    "last_updated": null,
    "token_expiry": null,
    "message": "Token verified via Kite API (profile)",
    "timestamp": "2026-02-11T16:41:43.920338"
}
```

**Response (Not Configured):**

```json
{
    "status": "not_configured",
    "authenticated": false,
    "token_valid": false,
    "user_id": null,
    "user_name": null,
    "broker": null,
    "last_updated": null,
    "token_expiry": null,
    "message": "Kite credentials not configured (create ~/.kite-services/kite_token.json)",
    "timestamp": "2026-02-11T16:41:43.920338"
}
```

---

## Complete Flow Example

### First-Time Setup (Production)

```bash
# Step 1: Set API credentials
curl -X POST http://203.57.85.72:8179/api/auth/credentials \
  -H "Content-Type: application/json" \
  -d '{"api_key":"dmy4m1i95o6myj60","api_secret":"vwquiugjo9degz32sj2mrzot4d1nrmll"}' | python3 -m json.tool
<!-- pragma: allowlist secret -->

# Step 2: Get login URL
curl -s http://203.57.85.72:8179/api/auth/login-url | python3 -m json.tool

# Step 3: Open login_url in browser, log in, copy request_token from redirect

# Step 4: Exchange request_token for access_token
curl -X POST http://203.57.85.72:8179/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"request_token":"YOUR_REQUEST_TOKEN"}' | python3 -m json.tool

# Step 5: Save access_token (optional but recommended)
curl -X PUT http://203.57.85.72:8179/api/auth/token \
  -H "Content-Type: application/json" \
  -d '{"access_token":"YOUR_ACCESS_TOKEN","user_id":"YF0364"}' | python3 -m json.tool

# Step 6: Verify
curl -s http://203.57.85.72:8179/api/auth/token-status | python3 -m json.tool
curl -s http://203.57.85.72:8179/api/auth/status | python3 -m json.tool
```

### Daily Token Refresh (After Expiry)

Kite tokens expire daily at **6:00 AM IST**. When expired:

```bash
# Step 1: Get new login URL
curl -s http://203.57.85.72:8179/api/auth/login-url | python3 -m json.tool

# Step 2: Open URL, log in, copy request_token

# Step 3: Exchange for new access_token
curl -X POST http://203.57.85.72:8179/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"request_token":"NEW_REQUEST_TOKEN"}' | python3 -m json.tool

# Step 4: Save new token
curl -X PUT http://203.57.85.72:8179/api/auth/token \
  -H "Content-Type: application/json" \
  -d '{"access_token":"NEW_ACCESS_TOKEN","user_id":"YF0364"}' | python3 -m json.tool
```

---

## Notes

- **Token File Location**: Tokens are saved to `/root/.kite-services/kite_token.json` on the server (prod) or `~/.kite-services/kite_token.json` (dev)
- **Token Expiry**: Kite access tokens expire daily at **6:00 AM IST**. Refresh using the flow above.
- **API Secret**: Required only for exchanging `request_token` → `access_token`. Can be provided in request or stored in token file.
- **Callback URL**: Must match exactly what's configured in your Kite Connect app at [developers.kite.trade](https://developers.kite.trade/)
- **Production Callback**: `http://203.57.85.72:8179/api/redirect`
- **Development Callback**: `http://localhost:8079/api/auth/callback`

---

## Troubleshooting

### "api_key not configured"

- Run: `POST /api/auth/credentials` with your `api_key` and `api_secret`

### "No access_token in file"

- Complete the login flow: `GET /api/auth/login-url` → open URL → copy `request_token` → `POST /api/auth/login`

### "Token invalid or expired"

- Token expired (daily at 6 AM IST). Refresh using the daily token refresh flow above.

### "Token verification failed"

- Token may be invalid. Generate a new one using the complete flow.
