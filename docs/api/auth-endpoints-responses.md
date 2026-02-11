<!-- markdownlint-disable MD013 -->

# Auth Endpoints – Response for Each

Use this to decide which endpoints you need.

---

## 1. GET /api/token/callback-url

**Purpose:** Get the URL to put in Kite app as Redirect URL (developers.kite.trade).

**Response (200):**

```json
{
  "callback_url": "http://203.57.85.72:8179/api/auth/callback",
  "configured": true,
  "message": null
}
```

When not configured: `configured: false`, `message` has setup hint.

---

## 2. GET /api/auth/token-status

**Purpose:** Diagnostic endpoint for access token status. Use when services (quotes, trading, opportunities) fail. Works even when market is closed.

**Response (200):**

```json
{
  "api_key_configured": true,
  "access_token_present": true,
  "token_file_path": "/Users/you/.kite-services/kite_token.json",
  "kite_client_initialized": true,
  "profile_verified": false,
  "message": "Token invalid or expired (Kite tokens expire daily at 6 AM IST)",
  "action_required": "1. GET /api/auth/login-url\n2. Open URL, login, copy request_token\n3. POST /api/auth/login with request_token",
  "timestamp": "2026-02-11T..."
}
```

---

## 3. GET /api/auth/status

**Purpose:** Check if access token is valid and who is logged in.

**Response (200) – valid token:**

```json
{
  "status": "authenticated",
  "authenticated": true,
  "token_valid": true,
  "user_id": "AB1234",
  "user_name": "User Name",
  "broker": "ZERODHA",
  "message": "Token verified via Kite API (profile)",
  "timestamp": "2026-02-11T..."
}
```

**Response (200) – no/expired token:**

```json
{
  "status": "not_configured",
  "authenticated": false,
  "token_valid": false,
  "user_id": null,
  "user_name": null,
  "message": "Kite credentials not configured...",
  "timestamp": "..."
}
```

---

## 4. GET /api/auth/login-url

**Purpose:** Get Kite login page URL to open in browser (OAuth flow).

**Response (200):**

```json
{
  "login_url": "https://kite.zerodha.com/connect/login?api_key=...",
  "message": "Open URL, login, copy request_token from redirect"
}
```

---

## 5. GET /api/auth/callback

**Purpose:** OAuth redirect target. Kite sends user here with `?request_token=...` after login. Returns HTML, not JSON.

**Response (200) – with request_token:**
HTML page with `request_token` shown and a copy button.

**Response (200) – without request_token:**
HTML page with error message.

---

## 6. POST /api/auth/login

**Purpose:** Exchange `request_token` → `access_token` (and validate). Does NOT save token to file.

**Request:** `{"request_token": "..."}` or `{"access_token": "..."}` (validate only)

**Response (200):**

```json
{
  "status": "authenticated",
  "access_token": "...",
  "user_id": "AB1234",
  "user_name": "User Name",
  "email": "...",
  "broker": "ZERODHA",
  "exchanges": ["NSE", "BSE", ...],
  "products": ["mis", "cnc", ...],
  "order_types": ["market", "limit", ...],
  "message": "Authentication successful",
  "timestamp": "..."
}
```

---

## 7. PUT /api/auth/token

**Purpose:** Save `access_token` to token file (persists across restarts). Validates token and returns profile.

**Request:** `{"access_token": "...", "user_id": "optional"}`

**Response (200):**

```json
{
  "status": "authenticated",
  "access_token": "...",
  "user_id": "AB1234",
  "user_name": "User Name",
  "email": "...",
  "broker": "ZERODHA",
  "exchanges": ["NSE", "BSE", ...],
  "products": ["mis", "cnc", ...],
  "order_types": ["market", "limit", ...],
  "message": "Token updated successfully",
  "timestamp": "..."
}
```

---

## Summary

| # | Endpoint | Returns |
|---|----------|---------|
| 1 | GET /api/token/callback-url | `callback_url`, `configured` |
| 2 | GET /api/auth/token-status | Token diagnostic (api_key, token_present, profile_verified) |
| 3 | GET /api/auth/status | `token_valid`, `user_id`, `user_name`, etc. |
| 4 | GET /api/auth/login-url | `login_url` (Kite page) |
| 5 | GET /api/auth/callback | HTML with `request_token` |
| 6 | POST /api/auth/login | `access_token`, profile (no persist) |
| 7 | PUT /api/auth/token | Profile (saves token to file) |
