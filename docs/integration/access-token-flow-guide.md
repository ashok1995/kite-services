# Access Token Flow – Frontend Integration Guide

<!-- markdownlint-disable MD013 MD040 -->

A step-by-step guide for frontend development. Use this when integrating Kite authentication with the kite-services backend

## Overview

| Token Type      | Purpose                                   | Lifetime     |
|-----------------|-------------------------------------------|--------------|
| `request_token` | One-time use; obtained after Kite login    | ~5 minutes   |
| `access_token`  | Used for all API calls (market, trading)  | Until 6 AM IST next day |

**Kite access tokens expire daily at 6:00 AM IST.** The frontend must detect expiry and trigger a refresh flow.

---

## Base URLs

| Environment  | Base URL                     |
|-------------|------------------------------|
| Production  | `http://203.57.85.72:8179`   |
| Development | `http://localhost:8079`     |

---

## Flow 1: Initial Login (First Time or After Expiry)

```
┌─────────────┐     GET /api/auth/login-url      ┌─────────────┐
│   Frontend  │ ───────────────────────────────►│ kite-services│
│   (User)    │                                  │   Backend    │
└─────────────┘                                  └─────────────┘
       │                                                 │
       │◄────────────────────────────────────────────────┘
       │   { "login_url": "https://kite.zerodha.com/connect/login?api_key=...", ... }
       │
       │   User opens login_url in browser
       │
       ▼
┌─────────────┐   User logs in at Kite (Zerodha)
│   Kite      │   → Redirected to: {callback_url}?request_token=xxx&status=success
│   (Zerodha) │
└─────────────┘
       │
       │   User sees request_token in callback page OR copies from URL
       │   User pastes request_token into your frontend
       │
       ▼
┌─────────────┐     POST /api/auth/login         ┌─────────────┐
│   Frontend  │     { "request_token": "xxx" }   │ kite-services│
│             │ ───────────────────────────────►│   Backend    │
└─────────────┘                                  └─────────────┘
       │                                                 │
       │◄────────────────────────────────────────────────┘
       │   { "status": "authenticated", "access_token": "...", "user_id": "...", ... }
       │
       │   Store access_token (e.g. memory, secure storage) for subsequent API calls
       ▼
   Done. Use access_token in backend calls (backend stores it server-side).
```

### Step-by-step (Frontend Code Logic)

1. **Get login URL**

   ```
   GET {BASE_URL}/api/auth/login-url
   → Use response.login_url
   ```

2. **Open login URL**  
   Open `login_url` in a new tab/window.

3. **Handle redirect**  
   After login, Kite redirects to `{BASE_URL}/api/auth/callback?request_token=XXX&status=success`.  
   - If your app controls the callback page: parse `request_token` from the URL.  
   - If using the backend callback page: user copies the token and pastes it into your UI.

4. **Exchange request_token for access_token**

   ```
   POST {BASE_URL}/api/auth/login
   Content-Type: application/json
   Body: { "request_token": "<request_token>" }
   → Store response.access_token and response.user_id for UI display
   ```

---

## Flow 2: Check Status (Before Each Session or API Call)

Always check status on app load and before sensitive operations.

```
┌─────────────┐     GET /api/auth/status         ┌─────────────┐
│   Frontend  │ ───────────────────────────────►│ kite-services│
└─────────────┘                                  └─────────────┘
       │                                                 │
       │◄────────────────────────────────────────────────┘
       │   { "status": "authenticated", "authenticated": true, "token_valid": true, ... }
       │   OR
       │   { "status": "expired", "authenticated": false, "token_valid": false }
       │   OR
       │   { "status": "not_configured", ... }
       │
       ▼
   If token_valid == true → Continue
   If token_valid == false or status == "expired" → Show "Refresh token" / run Flow 1
```

### Status values

| `status`         | `token_valid` | Action                                  |
|------------------|---------------|-----------------------------------------|
| `authenticated`  | `true`        | Token valid, proceed with API calls     |
| `expired`        | `false`       | Run refresh flow (Flow 1)               |
| `invalid`        | `false`       | Run refresh flow (Flow 1)                |
| `not_configured` | `false`       | Backend not configured; show setup note  |

---

## Flow 3: Handling Token Expiry During API Calls

Any API call (market data, trading, etc.) can return a token-expired error:

```json
{
  "success": false,
  "error": "token_expired",
  "error_type": "TokenExpired",
  "message": "Your Kite access token has expired. Please refresh your token to continue.",
  "details": {
    "requires_action": "token_refresh",
    "token_expiry_note": "Kite tokens expire daily at 6:00 AM IST"
  },
  "action_required": {
    "type": "token_refresh",
    "steps": [
      "1. Open Kite login URL",
      "2. Complete login and get request_token",
      "3. Call POST /api/auth/login with request_token"
    ],
    "endpoints": {
      "check_status": "GET /api/auth/status",
      "refresh_token": "POST /api/auth/login"
    }
  }
}
```

**Frontend behavior when `error === "token_expired"`:**

1. Show the user a message that the token has expired.
2. Trigger the refresh flow (same as Flow 1).
3. Optionally show a button like “Refresh Kite connection” that opens the login URL and guides the user to paste the `request_token`.

---

## Flow 4: Update Token (If User Obtains Token Elsewhere)

If the user has an access token from another source (e.g. another app or manual flow):

```
POST {BASE_URL}/api/auth/token
Content-Type: application/json
Body: { "access_token": "<new_access_token>", "user_id": "optional" }
```

This saves the token on the backend. Use when the user pastes a token obtained outside your normal flow.

---

## API Quick Reference

| Method | Endpoint                    | Purpose                                  |
|--------|-----------------------------|------------------------------------------|
| GET    | `/api/auth/status`         | Check if authenticated and token valid    |
| GET    | `/api/auth/login-url`      | Get Kite login URL                        |
| POST   | `/api/auth/login`          | Exchange `request_token` for `access_token` |
| PUT    | `/api/auth/token`          | Store a new access token                  |
| GET    | `/api/token/callback-url`  | Get callback URL for Kite app config      |

---

## Pseudocode for Frontend

```javascript
const BASE_URL = 'http://203.57.85.72:8179';  // or localhost:8079 for dev

// On app load
async function initAuth() {
  const res = await fetch(`${BASE_URL}/api/auth/status`);
  const data = await res.json();
  if (data.token_valid) {
    setUser(data.user_id, data.user_name);
    return true;
  }
  showRefreshTokenUI();
  return false;
}

// User clicks "Connect Kite" or "Refresh Token"
async function startLoginFlow() {
  const res = await fetch(`${BASE_URL}/api/auth/login-url`);
  const { login_url } = await res.json();
  window.open(login_url, '_blank');
  showInputForRequestToken();  // User pastes request_token after redirect
}

// User pastes request_token and submits
async function submitRequestToken(requestToken) {
  const res = await fetch(`${BASE_URL}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ request_token: requestToken }),
  });
  const data = await res.json();
  if (data.status === 'authenticated') {
    setUser(data.user_id, data.user_name);
    hideRefreshTokenUI();
    return true;
  }
  showError(data.message || 'Login failed');
  return false;
}

// When any API call returns error.token_expired
function onTokenExpired() {
  showMessage('Kite session expired. Please reconnect.');
  showRefreshTokenUI();
}
```

---

## Callback URL Setup (One-Time)

For the backend callback page to work, set this as the **Redirect URL** in your Kite Connect app at [developers.kite.trade](https://developers.kite.trade/):

- Production: `http://203.57.85.72:8179/api/auth/callback`
- Development: `http://localhost:8079/api/auth/callback`

Get the value dynamically: `GET /api/token/callback-url` returns `{ callback_url, configured }`.

---

## Summary for Agent / Implementer

1. **On load:** Call `GET /api/auth/status`. If `token_valid` is false, show the refresh flow.
2. **Refresh flow:** `GET /api/auth/login-url` → open URL → user logs in → user pastes `request_token` → `POST /api/auth/login` with `request_token`.
3. **On API errors:** If `error === "token_expired"`, trigger the refresh flow.
4. **Optional:** Use `PUT /api/auth/token` when the user provides an access token from another source.
