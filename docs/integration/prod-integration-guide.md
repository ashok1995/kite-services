# Production Integration Guide

Tested against **<http://203.57.85.72:8179>**.
Use these cURL commands to verify prod.

**Prerequisite:** Authenticate first (see [auth-curl-commands.md](auth-curl-commands.md)).
Most endpoints require a valid token; check with `GET /api/auth/status`.

---

## Base URL

```text
http://203.57.85.72:8179
```

---

## 1. Health & Service Info

### GET /health

```bash
curl -s http://203.57.85.72:8179/health | python3 -m json.tool
```

**Response:** `status: "healthy"`, services (cache, kite_client,
market_context, stock_data).

### GET /

```bash
curl -s http://203.57.85.72:8179/ | python3 -m json.tool
```

**Response:** Service name, version, environment, `health_url`, `api_prefix`.

---

## 2. Authentication

### GET /api/auth/status

Check if token is valid (verified via Kite API).

```bash
curl -s http://203.57.85.72:8179/api/auth/status | python3 -m json.tool
```

**Response:** `authenticated`, `token_valid`, `user_id`, `user_name`, `broker`.

### GET /api/auth/login-url

Get Kite login URL (for re-login when token expires).

```bash
curl -s http://203.57.85.72:8179/api/auth/login-url | python3 -m json.tool
```

### POST /api/auth/login

Exchange `request_token` for `access_token` (after opening login URL in browser).

```bash
curl -X POST http://203.57.85.72:8179/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"request_token": "YOUR_REQUEST_TOKEN"}' | python3 -m json.tool
```

---

## 3. Market Data

### GET /api/market/status

Market open/closed and exchange session.

```bash
curl -s http://203.57.85.72:8179/api/market/status | python3 -m json.tool
```

**Response:** `market_status`, `market_open`, `exchanges` (NSE, BSE session).

### POST /api/market/quotes

Real-time quotes for multiple symbols (recommended for quotes). Up to 200 symbols.

```bash
curl -s -X POST http://203.57.85.72:8179/api/market/quotes \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["RELIANCE", "TCS"], "exchange": "NSE"}' | python3 -m json.tool
```

**Response:** `stocks` array with `symbol`, `last_price`, `open_price`, `high_price`,
`low_price`, `close_price`, `change_percent`, `volume`, etc.

### GET /api/market/historical/{symbol}

Historical OHLCV candles.

**Query params:** `interval` (minute, 5minute, 15minute, hour, day),
`from_date`, `to_date` (YYYY-MM-DD).

```bash
curl -s "http://203.57.85.72:8179/api/market/historical/RELIANCE?interval=day&\
from_date=2025-02-01&to_date=2025-02-14" | python3 -m json.tool
```

**Response:** `symbol`, `interval`, `candles` array with `date`, `open`,
`high`, `low`, `close`, `volume`.

### GET /api/market/instruments

List instruments. Query: `?limit=10`, `?exchange=NSE`.

```bash
curl -s "http://203.57.85.72:8179/api/market/instruments?limit=5" | python3 -m json.tool
```

**Response:** `instruments` array (tradingsymbol, exchange,
instrument_type, etc.).

### POST /api/market/data (quote)

Universal market data; use `data_type: "quote"` for real-time quotes. Symbols use
request `exchange` (e.g. NSE); response keys are plain symbols.

```bash
curl -s -X POST http://203.57.85.72:8179/api/market/data \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["RELIANCE", "TCS"], '\
'"exchange": "NSE", "data_type": "quote"}' | python3 -m json.tool
```

**Response:** `success`, `data` (map of symbol → last_price, ohlc, volume),
`successful_symbols`, `failed_symbols`.

---

## 4. Market Context & Quick Data

### GET /api/market-context-data/quick-context

Quick market context: regime, VIX, breadth, Nifty 50, sectors (JSON).

```bash
curl -s http://203.57.85.72:8179/api/market-context-data/quick-context \
  | python3 -m json.tool
```

**Response:** `market_regime`, `volatility_regime`, `india_vix`,
`market_breadth` (advances/declines, ratio), `nifty_50`, `sectors`.

---

## 5. Trading

### GET /api/trading/status

Trading status: auth, positions, holdings, PnL. Requires valid token.

```bash
curl -s http://203.57.85.72:8179/api/trading/status | python3 -m json.tool
```

**Response:** `authenticated`, `holdings`, `positions`, `total_pnl`, `day_pnl`.

---

## Test Summary (Prod)

| Endpoint | Method | Auth | Tested |
|----------|--------|------|--------|
| /health | GET | No | OK |
| / | GET | No | OK |
| /api/auth/status | GET | No | OK |
| /api/auth/login-url | GET | No | OK |
| /api/auth/login | POST | No | OK |
| /api/market/status | GET | Yes | OK |
| /api/market/quotes | POST | Yes | OK |
| /api/market/historical/{symbol} | GET | Yes | OK |
| /api/market/instruments | GET | Yes | OK |
| /api/market/data (quote) | POST | Yes | OK |
| /api/market-context-data/quick-context | GET | Yes | OK |
| /api/trading/status | GET | Yes | OK |

---

## Notes

- **Quotes:** Use `POST /api/market/quotes` or `POST /api/market/data`
  with `data_type: "quote"`; both accept `symbols` and `exchange` (e.g. NSE).
- **Historical:** Use `GET /api/market/historical/{symbol}` with `interval`, `from_date`,
  `to_date`. Symbol without exchange prefix (e.g. RELIANCE).
- **Token refresh:** When token expires, use login-url → browser login → POST
  /api/auth/login with `request_token`. No service restart needed.
