# Auth Service Integration Guide

<!-- markdownlint-disable MD013 -->

Base URL: `http://localhost:8079` (dev) | `http://203.57.85.72:8179` (prod)

## Endpoints

### 0. GET /api/token/callback-url

Get the callback URL to configure in Kite Connect app (Redirect URL at developers.kite.trade).

**cURL:**

```bash
curl -s "http://203.57.85.72:8179/api/token/callback-url" | jq .
```

**Response 200:**

```json
{
  "callback_url": "http://203.57.85.72:8179/api/auth/callback",
  "configured": true,
  "message": null
}
```

When `configured` is false, add api_key and api_secret to the token file on the server. See [token-flow-setup.md](token-flow-setup.md).

### 1. GET /api/auth/login-url

Get Kite Connect login URL for OAuth flow.

**cURL:**

```bash
curl -s "http://localhost:8079/api/auth/login-url"
```

**Response 200:**

```json
{
  "login_url": "https://kite.zerodha.com/connect/login?api_key=...",
  "message": "Open URL, login, copy request_token from redirect"
}
```

### 2. POST /api/auth/login

Generate access token from request token, or validate existing access token.

**Request:**

<!-- pragma: allowlist secret -->

```json
{
  "request_token": "xxx_from_redirect_url",
  "access_token": null,
  "api_secret": "optional_if_in_env"
}
```

**cURL:**

```bash
curl -X POST "http://localhost:8079/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"request_token": "YOUR_REQUEST_TOKEN"}'
```

**Response 200:**

```json
{
  "status": "authenticated",
  "access_token": "...",
  "user_id": "AB1234",
  "user_name": "User Name",
  "message": "Authentication successful"
}
```

### 3. PUT /api/auth/token

Update access token (daily refresh without restart).

**Request:**

```json
{
  "access_token": "new_access_token",
  "user_id": "optional_user_id"
}
```

**cURL:**

```bash
curl -X PUT "http://localhost:8079/api/auth/token" \
  -H "Content-Type: application/json" \
  -d '{"access_token": "YOUR_NEW_ACCESS_TOKEN"}'
```

### 4. GET /api/auth/status

Check current authentication status.

**cURL:**

```bash
curl -s "http://localhost:8079/api/auth/status"
```

**Response 200:**

```json
{
  "status": "authenticated",
  "authenticated": true,
  "user_id": "AB1234",
  "user_name": "User Name",
  "message": "Token is valid and active"
}
```

## Integration Flow

1. Call `GET /api/auth/login-url` → Open `login_url` in browser
2. After login, copy `request_token` from redirect URL query param
3. Call `POST /api/auth/login` with `{"request_token": "..."}` → Store `access_token`
4. Call `GET /api/auth/status` to verify before trading
5. For daily refresh: `PUT /api/auth/token` with new token
