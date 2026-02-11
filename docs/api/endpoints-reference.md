<!-- markdownlint-disable MD013 -->

# Endpoints Reference

All exposed endpoints with functionality. Prefix: `/api` unless noted.

---

## Auth (auth.py)

| Method | Endpoint | Functionality |
|--------|----------|---------------|
| GET | `/api/auth/credentials/status` | Check if api_key configured |
| POST | `/api/auth/credentials` | Save api_key + api_secret from web |
| GET | `/api/token/callback-url` | Returns callback URL for Kite app Redirect URL config |
| GET | `/api/auth/callback` | Kite OAuth redirect target; shows `request_token` in HTML |
| GET | `/api/auth/login-url` | Returns Kite Connect login URL to open in browser |
| POST | `/api/auth/login` | Accepts `request_token` → exchanges for access_token (saves); OR `access_token` → validates only |
| PUT | `/api/auth/token` | Accepts `access_token` → saves to token file, validates, returns profile |
| GET | `/api/auth/status` | Returns auth status: token_valid, user info |

---

## Market Data (market_data.py)

| Method | Endpoint | Functionality |
|--------|----------|---------------|
| POST | `/api/market/data` | Universal market data: quotes, historical, fundamentals |
| GET | `/api/market/status` | Market open/closed status |
| GET | `/api/market/instruments` | List instruments (optional limit, exchange) |
| POST | `/api/market/quotes` | Real-time quotes |

---

## Analysis (analysis.py)

| Method | Endpoint | Functionality |
|--------|----------|---------------|
| POST | `/api/analysis/context` | Market context: global, Indian, sentiment, technicals |
| POST | `/api/analysis/intelligence` | Stock intelligence |
| POST | `/api/analysis/stock` | Single-stock analysis |

---

## Analysis Enhanced (analysis_enhanced.py)

| Method | Endpoint | Functionality |
|--------|----------|---------------|
| POST | `/api/analysis/context/enhanced` | Hierarchical context with trading styles |

---

## Trading (trading.py)

| Method | Endpoint | Functionality |
|--------|----------|---------------|
| GET | `/api/trading/status` | Portfolio, positions, holdings, P&L |

---

## Opportunities (quick_opportunities.py)

| Method | Endpoint | Functionality |
|--------|----------|---------------|
| POST | `/api/opportunities/quick` | Quick trading opportunities |

---

## Core (non-/api)

| Method | Endpoint | Functionality |
|--------|----------|---------------|
| GET | `/health` | Health check |
| GET | `/` | Service info (version, docs URL) |
| GET | `/docs` | Swagger UI (when debug) |
| GET | `/redoc` | ReDoc (when debug) |
| GET | `/openapi.json` | OpenAPI schema |

---

## Duplicate / Overlap Check

| Issue | Endpoints | Resolution |
|-------|-----------|------------|
| **Token save vs validate** | POST `/api/auth/login` with `access_token` vs PUT `/api/auth/token` | Different: POST validates in memory only (no persist). PUT persists to file. For client paste flow use PUT `/api/auth/token`. |
| **Context endpoints** | POST `/api/analysis/context` vs POST `/api/analysis/context/enhanced` | Different: basic context vs enhanced hierarchical. Not duplicate. |
| **market_context_routes.py** | POST `/context`, GET `/quick-context`, GET `/context/examples` | Not exposed in main.py. Routers not included. Consider remove if unused. |

---

## Summary

- Auth: 6 endpoints (callback-url, callback, login-url, login, token, status)
- Market: 4 endpoints
- Analysis: 4 endpoints (3 basic + 1 enhanced)
- Trading: 1 endpoint
- Opportunities: 1 endpoint
- Core: 3+ (health, root, docs)
