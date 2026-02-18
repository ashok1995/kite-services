# Kite Services – Integration Guide (Single Source)

This is the **only** integration guide. All endpoint behaviour and examples are kept in sync with `docs/api/api-reference.md`.

**Base URLs:**

| Env      | URL                        | Port |
|----------|----------------------------|------|
| Dev      | `http://localhost:8079`    | 8079 |
| Staging  | `http://localhost:8279`    | 8279 |
| Prod     | `http://YOUR_HOST:8179`    | 8179 |

Use `BASE` below as your base URL (e.g. `http://localhost:8079` or prod URL).

---

## 1. Authentication

### 1.1 Set API key and secret (first-time)

<!-- pragma: allowlist secret -->
```bash
curl -X POST "$BASE/api/auth/credentials" \
  -H "Content-Type: application/json" \
  -d '{"api_key": "YOUR_KITE_API_KEY", "api_secret": "YOUR_KITE_API_SECRET"}' \
  | python3 -m json.tool
```

### 1.2 Get login URL

```bash
curl -s "$BASE/api/auth/login-url" | python3 -m json.tool
```

Open the returned `login_url` in a browser, log in, then copy `request_token` from the redirect URL.

### 1.3 Exchange request token for access token

```bash
curl -X POST "$BASE/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"request_token": "YOUR_REQUEST_TOKEN"}' | python3 -m json.tool
```

### 1.4 Check auth status

```bash
curl -s "$BASE/api/auth/status" | python3 -m json.tool
```

### 1.5 Update access token (e.g. after refresh)

```bash
curl -X PUT "$BASE/api/auth/token" \
  -H "Content-Type: application/json" \
  -d '{"access_token": "NEW_ACCESS_TOKEN", "user_id": "optional"}' | python3 -m json.tool
```

---

## 2. Health and service info

```bash
curl -s "$BASE/health" | python3 -m json.tool
curl -s "$BASE/"      | python3 -m json.tool
```

---

## 3. Market data

### 3.1 Market status

```bash
curl -s "$BASE/api/market/status" | python3 -m json.tool
```

### 3.2 Quotes (up to 200 symbols)

```bash
curl -s -X POST "$BASE/api/market/quotes" \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["RELIANCE", "TCS"], "exchange": "NSE"}' | python3 -m json.tool
```

### 3.3 Universal market data (quote)

```bash
curl -s -X POST "$BASE/api/market/data" \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["RELIANCE", "TCS"], "exchange": "NSE", "data_type": "quote"}' \
  | python3 -m json.tool
```

### 3.4 Historical OHLCV

```bash
curl -s "$BASE/api/market/historical/RELIANCE?interval=day&from_date=2025-02-01&to_date=2025-02-14" \
  | python3 -m json.tool
```

### 3.5 Instruments

```bash
curl -s "$BASE/api/market/instruments?limit=10&exchange=NSE" | python3 -m json.tool
```

---

## 4. Analysis

### 4.1 Indian market context (internal)

```bash
curl -s "$BASE/api/internal-market-context" | python3 -m json.tool
```

### 4.2 Intelligence

```bash
curl -s -X POST "$BASE/api/analysis/intelligence" \
  -H "Content-Type: application/json" \
  -d '{"symbol": "RELIANCE", "time_horizon": "short"}' | python3 -m json.tool
```

### 4.3 Stock analysis

```bash
curl -s -X POST "$BASE/api/analysis/stock" \
  -H "Content-Type: application/json" \
  -d '{"symbol": "RELIANCE", "analysis_type": "comprehensive", "time_horizon": "intraday"}' \
  | python3 -m json.tool
```

### 4.4 Enhanced context

```bash
curl -s -X POST "$BASE/api/analysis/context/enhanced" \
  -H "Content-Type: application/json" \
  -d '{"include_primary": true, "include_detailed": false, "include_style_specific": true}' \
  | python3 -m json.tool
```

---

## 5. Trading

### 5.1 Trading status

```bash
curl -s "$BASE/api/trading/status" | python3 -m json.tool
```

### 5.2 Quick opportunities

```bash
curl -s -X POST "$BASE/api/opportunities/quick" \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["NSE:NIFTY 50"], "timeframe": "5minute"}' | python3 -m json.tool
```

---

## 6. Request bodies (reference)

| Endpoint | Request body |
|----------|---------------|
| POST /api/auth/credentials | `{"api_key":"...", "api_secret":"..."}` |
| POST /api/auth/login | `{"request_token":"..."}` |
| PUT /api/auth/token | `{"access_token":"...", "user_id":"optional"}` |
| POST /api/market/data | `{"symbols":["RELIANCE"], "exchange":"NSE", "data_type":"quote"}` |
| POST /api/market/quotes | `{"symbols":["RELIANCE","TCS"], "exchange":"NSE"}` |
| GET /api/internal-market-context | (no body) |
| POST /api/analysis/intelligence | `{"symbol":"RELIANCE", "time_horizon":"short"}` |
| POST /api/analysis/stock | `{"symbol":"RELIANCE", "analysis_type":"comprehensive", "time_horizon":"intraday"}` |
| POST /api/opportunities/quick | `{"symbols":["NSE:NIFTY 50"], "timeframe":"5minute"}` |

Full request/response shapes: see **API Reference** (`docs/api/api-reference.md`) and **Request/Response models** (`docs/html/request-response-models.html`).

---

## 7. Interactive docs

- **Swagger UI:** `$BASE/docs`
- **ReDoc:** `$BASE/redoc` (if enabled)
