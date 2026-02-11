# Kite Services – Consolidated Integration Guide

Copy-paste ready reference for all API endpoints.

**Base URL:** Dev `http://localhost:8079` | Prod `http://YOUR_HOST:8179`

---

## System

### Health

```bash
curl -s "http://localhost:8079/health"
```

### Root

```bash
curl -s "http://localhost:8079/"
```

---

## Auth

### Login URL

```bash
curl -s "http://localhost:8079/api/auth/login-url"
```

### Login (request token)

```bash
curl -X POST "http://localhost:8079/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"request_token": "YOUR_REQUEST_TOKEN"}'
```

### Update Token

```bash
curl -X PUT "http://localhost:8079/api/auth/token" \
  -H "Content-Type: application/json" \
  -d '{"access_token": "YOUR_NEW_ACCESS_TOKEN"}'
```

### Auth Status

```bash
curl -s "http://localhost:8079/api/auth/status"
```

---

## Market Data

### Market Data

```bash
curl -X POST "http://localhost:8079/api/market/data" \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["RELIANCE", "TCS"], "exchange": "NSE"}'
```

### Market Status

```bash
curl -s "http://localhost:8079/api/market/status"
```

### Instruments

```bash
curl -s "http://localhost:8079/api/market/instruments?limit=10"
```

### Quotes

```bash
curl -X POST "http://localhost:8079/api/market/quotes" \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["NSE:RELIANCE", "NSE:TCS"]}'
```

---

## Analysis

### Context

```bash
curl -X POST "http://localhost:8079/api/analysis/context" \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["RELIANCE"], "include_global": true, "include_indian": true}'
```

### Intelligence

```bash
curl -X POST "http://localhost:8079/api/analysis/intelligence" \
  -H "Content-Type: application/json" \
  -d '{"symbol": "RELIANCE"}'
```

### Stock Analysis

```bash
curl -X POST "http://localhost:8079/api/analysis/stock" \
  -H "Content-Type: application/json" \
  -d '{"symbol": "RELIANCE", "analysis_type": "comprehensive", "time_horizon": "intraday"}'
```

### Enhanced Context

```bash
curl -X POST "http://localhost:8079/api/analysis/context/enhanced" \
  -H "Content-Type: application/json" \
  -d '{"trading_styles": ["intraday"], "include_primary": true, "include_detailed": false, "include_style_specific": true}'
```

---

## Trading

### Trading Status

```bash
curl -s "http://localhost:8079/api/trading/status"
```

### Quick Opportunities

```bash
curl -X POST "http://localhost:8079/api/opportunities/quick" \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["NSE:NIFTY 50"], "timeframe": "5minute"}'
```

---

## Request Bodies Reference

| Endpoint | Request Body |
|----------|--------------|
| POST /api/auth/login | `{"request_token":"..."}` or `{"access_token":"..."}` |
| PUT /api/auth/token | `{"access_token":"...", "user_id":"optional"}` |
| POST /api/market/data | `{"symbols":["RELIANCE"], "exchange":"NSE", "data_type":"quote"}` |
| POST /api/market/quotes | `{"symbols":["NSE:RELIANCE"], "exchange":"NSE"}` |
| POST /api/analysis/context | `{"symbols":[], "include_global":true, "include_indian":true}` |
| POST /api/analysis/intelligence | `{"symbol":"RELIANCE", "time_horizon":"short"}` |
| POST /api/analysis/stock | `{"symbol":"RELIANCE", "analysis_type":"comprehensive", "time_horizon":"intraday"}` |
| POST /api/analysis/context/enhanced | `{"trading_styles":["intraday"], "include_primary":true}` |
| POST /api/opportunities/quick | `{"symbols":["NSE:NIFTY 50"], "timeframe":"5minute"}` |

---

## Interactive Docs

- Swagger: `http://localhost:8079/docs`
- ReDoc: `http://localhost:8079/redoc` (when debug enabled)
