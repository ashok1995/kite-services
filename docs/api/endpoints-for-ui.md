# Endpoints for UI Integration

Base URL: **Production** `http://203.57.85.72:8179` | **Development** `http://localhost:8079`

All API routes are under `/api` unless noted.

---

## 1. Health & Info

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Service health (status, version, services). Optional `?detailed=true` for metrics. |
| GET | `/` | Service info (name, version, environment, api_prefix). |

---

## 2. Authentication

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/auth/login-url` | Get Kite login URL. Open in browser → log in → copy `request_token` from redirect. |
| POST | `/api/auth/login` | Exchange `request_token` for `access_token`. Body: `{"request_token": "..."}`. |
| GET | `/api/auth/status` | Current auth: `authenticated`, `token_valid`, `user_id`, `user_name`, `broker`. |
| PUT | `/api/auth/token` | Update stored token. Body: `{"access_token": "...", "user_id": "optional"}`. |

---

## 3. Market Data

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/market/quotes` | Real-time quotes. Body: `{"symbols": [...], "exchange": "NSE"}`. |
| POST | `/api/market/data` | Universal data: quote / historical / fundamentals. |
| GET | `/api/market/historical/{symbol}` | OHLCV candles. Query: `interval`, `from_date`, `to_date`. |
| GET | `/api/market/status` | Market status (open/closed, session). |
| GET | `/api/market/instruments` | Available instruments and exchanges. |

---

## 4. Indian Market Context

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/internal-market-context` | Indian market context only: regime, India VIX, Nifty 50, breadth, sectors. No body. |

---

## 5. Trading

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/trading/status` | Portfolio, positions, holdings, P&L (requires valid token). |
| POST | `/api/trading/orders/place` | Place order. Body: order details (symbol, quantity, type, etc.). |
| PUT | `/api/trading/orders/{order_id}/modify` | Modify open order. |
| DELETE | `/api/trading/orders/{order_id}/cancel` | Cancel order. |
| GET | `/api/trading/orders` | List orders (optional filters). |
| GET | `/api/trading/orders/{order_id}` | Order details. |
| GET | `/api/trading/order-history/{order_id}` | Execution history for an order. |

---

## 6. Opportunities (Optional)

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/opportunities/quick` | Quick opportunities. Body: e.g. `{"symbols": ["NSE:NIFTY 50"], "timeframe": "5minute"}`. |

---

## 7. Monitoring (Optional)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health?detailed=true` | Health + uptime, request counts, error rate, top endpoints. |
| GET | `/metrics` | Metrics summary (requests, performance, status codes). |

---

## Quick reference (copy-paste for UI)

<!-- markdownlint-disable MD013 -->

```
GET  /health
GET  /api/auth/login-url
POST /api/auth/login          Body: { "request_token": "..." }
GET  /api/auth/status
PUT  /api/auth/token          Body: { "access_token": "...", "user_id": "?" }

POST /api/market/quotes       Body: { "symbols": ["RELIANCE","TCS"], "exchange": "NSE" }
POST /api/market/data         Body: { "symbols": [...], "exchange": "NSE", "data_type": "quote" }
GET  /api/market/historical/{symbol}?interval=day&from_date=YYYY-MM-DD&to_date=YYYY-MM-DD
GET  /api/market/status
GET  /api/market/instruments

GET  /api/internal-market-context

GET  /api/trading/status
POST /api/trading/orders/place
PUT  /api/trading/orders/{order_id}/modify
DELETE /api/trading/orders/{order_id}/cancel
GET  /api/trading/orders
GET  /api/trading/orders/{order_id}
GET  /api/trading/order-history/{order_id}

POST /api/opportunities/quick
```

<!-- markdownlint-enable MD013 -->

## Notes for UI

- **Timestamps (IST):** All `timestamp` fields use exact Indian clock time, no timezone suffix.
- **Auth flow:** `GET /api/auth/login-url` → open URL → login → copy `request_token` from redirect → `POST
  /api/auth/login` with token → store returned `access_token`. Token saved on server.
- **Auth for protected routes:** Use `GET /api/auth/status` to check token and user info.
- **Content-Type:** Use `Content-Type: application/json` for all POST/PUT bodies.
- **CORS:** Ensure UI origin is in `CORS_ORIGINS` if you see CORS errors.
