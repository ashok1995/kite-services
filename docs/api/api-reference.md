# Complete API Reference

## Base URL

- **Development**: `http://localhost:8079`
- **Production**: `http://localhost:8179`

## Timestamps (IST)

All `timestamp` fields use exact Indian clock time (e.g. `2026-02-13T15:45:00`)
with no timezone suffix, for Indian market hours (9:15 AM–3:30 PM IST).

## Authentication

Credentials, login URL, callback, and token save.

### Flow

1. **POST /api/auth/credentials** – Save `api_key` and `api_secret` only (first-time).
2. **GET /api/auth/login-url** – Returns `{"login_url": "https://kite.zerodha.com/..."}`. Open in browser to log in.
3. After login, Kite redirects to callback (token saved) or copy request_token and call
   **PUT /api/auth/token** with `{"request_token": "..."}`.

#### POST /api/auth/credentials (first-time)

Save Kite API key and secret.

**Request Body**:

<!-- pragma: allowlist secret -->

```json
{
  "api_key": "your_kite_api_key",
  "api_secret": "your_kite_api_secret"
}
```

**Response**: 200 OK – `{"success": true, "message": "..."}`

#### GET /api/auth/login-url

Returns the Kite Connect login URL. Open this URL in browser; after login, Kite redirects to your callback with `request_token`.

**Response**: 200 OK

```json
{
  "login_url": "https://kite.zerodha.com/connect/login?api_key=...&v=3",
  "message": "Open URL, login, copy request_token from redirect"
}
```

#### GET /api/auth/callback

Callback URL for Kite redirect. Set this as redirect URL in Kite app. Query: `?request_token=xxx`. We exchange and save; return HTML success page.

#### PUT /api/auth/token

Exchange `request_token` for access_token and save. Body: `request_token` only.

**Request Body**:

```json
{
  "request_token": "from_kite_redirect"
}
```

**Response**: 200 OK – same shape as auth response (user_id, user_name, etc.).

#### GET /api/auth/status

Check current auth status. Verifies token via Kite API (profile call). If
`credentials_configured` is false, call POST /api/auth/credentials first.

**Response**: 200 OK

```json
{
  "status": true,
  "token_valid": true,
  "credentials_configured": true,
  "user_id": "AB1234",
  "user_name": "User Name",
  "token_refreshed_at": "2026-02-19T16:30:00",
  "message": "Token verified via Kite API (profile)"
}
```

- `status`: true if authenticated, false otherwise
- `token_valid`: true if token verified via Kite API
- `credentials_configured`: true if api_key and api_secret are set
- `action_required`: when status is false: `set_credentials` or `login_and_set_token`; omit when authenticated
- `token_refreshed_at`: Last token refresh time in IST (exact Indian time, no suffix)

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
    "market_context_service": {"status": "running"}
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

### GET /api/market/historical/{symbol}

Historical OHLCV candles for a symbol.

**Query params:**

- `symbol` (path) – e.g. RELIANCE, TCS
- `interval` – minute, 5minute, 15minute, 30minute, hour, day (default: 5minute)
- `from_date` – YYYY-MM-DD (default: 7 days ago)
- `to_date` – YYYY-MM-DD (default: today)

**Example:** `GET /api/market/historical/RELIANCE?interval=day&from_date=2025-02-01&to_date=2025-02-14`

**Response:** 200 OK

```json
{
  "symbol": "RELIANCE",
  "instrument_token": 738561,
  "interval": "day",
  "from_date": "2025-02-01",
  "to_date": "2025-02-14",
  "candles": [
    {
      "date": "2025-02-01",
      "open": 2500.0,
      "high": 2520.0,
      "low": 2490.0,
      "close": 2510.0,
      "volume": 1000000
    }
  ],
  "total_candles": 10,
  "processing_time_ms": 450,
  "timestamp": "2025-02-14T12:00:00"
}
```

### POST /api/market/quotes

Real-time quotes for multiple symbols (up to 200).

**Request:**

```json
{
  "symbols": ["RELIANCE", "TCS", "INFY"],
  "exchange": "NSE"
}
```

**Response:**

```json
{
  "success": true,
  "total_symbols": 3,
  "successful_symbols": 3,
  "stocks": [...],
  "processing_time_ms": 850
}
```

**Limits:** Maximum 200 symbols per request (increased from 50)

---

## Analysis API

### GET /api/internal-market-context

Indian market context only (Kite Connect). No request body. Global context is provided by a separate service.

**Response:**

- `market_regime`: bullish / bearish / sideways
- `volatility_regime`, `india_vix`, `vix_level`
- `market_breadth`: advances, declines, advance_decline_ratio (Nifty 50, cached 60s)
- `nifty_50`: price, change_percent
- `sectors`: sector name → change_percent
- `institutional_sentiment`, `confidence_score`, `processing_time_ms`

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
