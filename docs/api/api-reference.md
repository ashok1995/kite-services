# Complete API Reference

## Base URL

- **Development**: `http://localhost:8079`
- **Production**: `http://localhost:8179`

## Authentication

Kite Connect OAuth token flow. Get access token in 3 steps:

### Token Flow

1. **GET /api/auth/login-url** – Get Kite login URL  
2. Open URL in browser, log in, copy `request_token` from redirect URL  
3. **POST /api/auth/login** with `request_token` – Receive `access_token`

#### GET /api/auth/login-url

Returns Kite Connect login URL.

**Response**: 200 OK

```json
{
  "login_url": "https://kite.zerodha.com/connect/login?api_key=...",
  "message": "Open URL, login, copy request_token from redirect"
}
```

#### POST /api/auth/login

Generate access token from request token.

**Request Body**:

<!-- pragma: allowlist secret -->

```json
{
  "request_token": "from_redirect_url",
  "api_secret": "optional_if_in_env"
}
```

**Response**: 200 OK

```json
{
  "status": "authenticated",
  "access_token": "...",
  "user_id": "AB1234",
  "user_name": "User Name",
  "message": "Authentication successful"
}
```

#### GET /api/auth/status

Check current auth status. Verifies token via Kite API (profile call).

**Response**: 200 OK

```json
{
  "status": "authenticated",
  "authenticated": true,
  "token_valid": true,
  "user_id": "AB1234",
  "user_name": "User Name",
  "message": "Token verified via Kite API (profile)"
}
```

#### PUT /api/auth/token

Update access token (saved to KITE_TOKEN_FILE; survives git pull).

**Request Body**:

```json
{
  "access_token": "new_access_token",
  "user_id": "optional_user_id"
}
```

---

## Core Endpoints

### Health & Status

#### GET /health

Health check endpoint

**Response**: 200 OK

```json
{
  "status": "healthy",
  "service": "kite-services",
  "version": "1.0.0",
  "environment": "production",
  "services": {
    "kite_client": {"status": "running"},
    "yahoo_service": {"status": "running"}
  }
}
```

#### GET /

Service information

**Response**: 200 OK

```json
{
  "service": "kite-services",
  "version": "1.0.0",
  "environment": "production",
  "docs_url": "/docs",
  "health_url": "/health",
  "api_prefix": "/api"
}
```

---

## Market Data API

### POST /api/market/data

Universal market data (quotes, historical, fundamentals).

**Request:** `{"symbols": ["RELIANCE", "TCS"], "exchange": "NSE", "data_type": "quote"}`

### GET /api/market/status

Market open/closed status.

### GET /api/market/instruments

List instruments. Query: `?limit=10`, `?exchange=NSE`.

### POST /api/market/quotes

Real-time quotes. **Request:** `{"symbols": ["NSE:RELIANCE"], "exchange": "NSE"}`

---

## Analysis API

### POST /api/analysis/context

Market context (global, Indian, sentiment, technicals).

**Request:** `{"symbols": [], "include_global": true, "include_indian": true}`

### POST /api/analysis/intelligence

Stock intelligence. **Request:** `{"symbol": "RELIANCE", "time_horizon": "short"}`

### POST /api/analysis/stock

Single-stock analysis. **Request:** `{"symbol": "RELIANCE", "analysis_type": "comprehensive", "time_horizon": "intraday"}`

### POST /api/analysis/context/enhanced

Enhanced hierarchical context. **Request:** `{"trading_styles": ["intraday"], "include_primary": true}`

---

## Trading API

### GET /api/trading/status

Portfolio, positions, holdings, P&L.

### POST /api/opportunities/quick

Quick trading opportunities. **Request:** `{"symbols": ["NSE:NIFTY 50"], "timeframe": "5minute"}`

---

## Error Responses

### 400 Bad Request

```json
{
  "error": "ValidationError",
  "message": "Invalid symbols list",
  "details": {...}
}
```

### 401 Unauthorized

```json
{
  "error": "Unauthorized",
  "message": "Invalid or expired access token"
}
```

### 500 Internal Server Error

```json
{
  "error": "Internal server error",
  "message": "An unexpected error occurred",
  "type": "ServerError"
}
```

---

## Rate Limits

- 100 requests per minute (configurable)
- WebSocket: 3 requests per second for subscriptions

---

## Interactive Documentation

- **Swagger UI**: `/docs`
- **ReDoc**: `/redoc` (if enabled)

For complete interactive API documentation with try-it-out functionality, visit the `/docs` endpoint.
