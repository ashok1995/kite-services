# Kite Service — Requirements for Bayesian Engine

**Related**: [Design doc](../architecture/bayesian-engine-design.md), [Data Source Boundaries](./data-source-boundaries.md)

This document defines **exactly what we need** from the Kite service (running on port 8179)
for the Bayesian Continuous Intelligence Engine.

---

## Service overview

The Kite service is a separate service that wraps Kite Connect (Zerodha) API.
It runs on port **8179** and is referenced as `MARKET_CONTEXT_SERVICE_URL` in env config.

**IMPORTANT**: Kite is the **PRIMARY and ONLY source** for all NSE/BSE stock data:
- ✅ Real-time stock quotes (LTP, volume, OHLC)
- ✅ Historical candles (5m, 15m, 1h, 1d)
- ✅ Market context (Nifty regime, VIX India, breadth, sectors)
- ✅ Instrument metadata (tokens, lot sizes)
- ❌ Does NOT provide: US indices, global VIX, commodities, forex → use Yahoo for these

**Existing endpoints already used by seed-stocks-service:**
- `GET /api/market-context-data/quick-context` — market regime, VIX, sectors
- `GET /api/v1/quotes/{symbol}` — last traded price for a single symbol

---

## What we need (new + existing)

### 1. Real-time quotes (batch) — CRITICAL

**Purpose**: Update prices for all stocks in the pool every 1 minute.

**Current**: Single symbol quotes via `GET /api/v1/quotes/{symbol}` (one at a time).

**Needed**: Batch quotes for up to 200 symbols in one call.

```
GET /api/v1/quotes/batch?symbols=RELIANCE,SBIN,HDFCBANK,...
```

**Expected response**:
```json
{
  "quotes": {
    "RELIANCE": {
      "ltp": 2456.75,
      "last_price": 2456.75,
      "volume": 1500000,
      "average_price": 2445.50,
      "open": 2440.00,
      "high": 2460.00,
      "low": 2435.00,
      "close": 2430.00,
      "change_percent": 1.10,
      "last_trade_time": "2026-02-12T14:30:00+05:30",
      "oi": 0,
      "buy_quantity": 50000,
      "sell_quantity": 45000
    },
    "SBIN": { ... }
  },
  "timestamp": "2026-02-12T14:30:05+05:30"
}
```

**Kite Connect API mapping**: `kite.quote(["NSE:RELIANCE", "NSE:SBIN", ...])`

**Fields we use**:

| Field | Used for | Priority |
|-------|----------|----------|
| `ltp` / `last_price` | Current price in stock_pool, price_snapshots | MUST |
| `volume` | Volume enrichment | MUST |
| `open`, `high`, `low`, `close` | Intraday range analysis | SHOULD |
| `change_percent` | Quick momentum signal | SHOULD |
| `average_price` | VWAP comparison | NICE |
| `buy_quantity`, `sell_quantity` | Order book imbalance signal | NICE |
| `last_trade_time` | Stale data detection | SHOULD |

**Call frequency**: Every 1 minute during market hours.
**Symbols per call**: Up to 200 (Kite API limit is 500 instruments per call).
**Timeout**: 5 seconds.

---

### 2. Market context — CRITICAL

**Purpose**: Market regime, VIX, sector strength, breadth for Bayesian scoring.

**Current**: Already implemented via `GET /api/market-context-data/quick-context`.

**What we need (verify these fields exist)**:
```
GET /api/market-context-data/quick-context?include_global=true&include_sector=true&include_institutional=true
```

**Expected response structure**:
```json
{
  "market_regime": "bullish",
  "volatility_regime": "low",
  "india_vix": 12.45,
  "vix_level": "low",
  "market_breadth": {
    "advance_decline_ratio": 2.3,
    "advancing_stocks": 35,
    "declining_stocks": 15,
    "total_stocks": 50
  },
  "nifty_50": {
    "price": 21450.50,
    "change_percent": 0.75
  },
  "sectors": {
    "IT": {"change_percent": 1.2, "leader": true},
    "BANK": {"change_percent": 0.8, "leader": false},
    ...
  },
  "institutional_sentiment": "bullish",
  "fii_dii_data": {...},
  "confidence_score": 0.85,
  "timestamp": "2026-02-12T14:30:00+05:30"
}
```

**Fields we use**:

| Field | Used for | Priority |
|-------|----------|----------|
| `market_regime` | Bayesian context feature (bullish/bearish/neutral) | MUST |
| `india_vix` / `vix_level` | Volatility regime (low/medium/high) | MUST |
| `volatility_regime` | Score adjustment (penalize high vol) | MUST |
| `market_breadth.advance_decline_ratio` | Overall market health | MUST |
| `market_breadth.advancing_stocks` | Number of stocks up | MUST |
| `market_breadth.declining_stocks` | Number of stocks down | MUST |
| `nifty_50.change_percent` | Index momentum | SHOULD |
| `sectors` | Sector-level scoring (boost stocks in leading sectors) | SHOULD |
| `sector_leadership` | Top sector detection | SHOULD |
| `institutional_sentiment` | FII/DII flow direction | SHOULD |
| `confidence_score` | Data reliability indicator | SHOULD |

**Call frequency**: Every 5 minutes during market hours.
**Timeout**: 10 seconds.

**Note**: If `market_breadth` data is missing, we can calculate it from Nifty 50 constituent quotes (batch quotes endpoint).

---

### 3. OHLCV candles (historical) — IMPORTANT

**Purpose**: Compute returns for past recommendations (performance tracking).

**Needed**: Intraday candle data (5-minute or 15-minute) for specific symbols.

```
GET /api/v1/historical/{symbol}?interval=5minute&from=2026-02-12&to=2026-02-12
```

**Expected response**:
```json
{
  "candles": [
    {
      "timestamp": "2026-02-12T09:15:00+05:30",
      "open": 2440.00,
      "high": 2445.50,
      "low": 2438.00,
      "close": 2443.25,
      "volume": 125000
    },
    ...
  ],
  "symbol": "RELIANCE",
  "interval": "5minute"
}
```

**Kite Connect API mapping**: `kite.historical_data(instrument_token, from_date, to_date, "5minute")`

**Fields we use**:

| Field | Used for | Priority |
|-------|----------|----------|
| `close` | Return calculation at specific timestamps | MUST |
| `volume` | Volume profile analysis | SHOULD |
| `high`, `low` | Max favorable/adverse excursion | SHOULD |

**Call frequency**: Every 10 minutes (only for symbols with open recommendations).
**Symbols per call**: 10-50 (only tracked symbols).
**Timeout**: 10 seconds.

---

### 4. Instrument list — IMPORTANT

**Purpose**: Map symbols to instrument tokens, get lot sizes, tick sizes, filter tradable stocks.

```
GET /api/v1/instruments?exchange=NSE&segment=EQ
```

**Expected response**:
```json
{
  "instruments": [
    {
      "instrument_token": 738561,
      "tradingsymbol": "RELIANCE",
      "exchange": "NSE",
      "name": "Reliance Industries",
      "lot_size": 1,
      "tick_size": 0.05,
      "instrument_type": "EQ",
      "segment": "NSE"
    },
    ...
  ]
}
```

**Fields we use**:

| Field | Used for | Priority |
|-------|----------|----------|
| `instrument_token` | Required for historical data API | MUST |
| `tradingsymbol` | Map ChartInk symbols to Kite symbols | MUST |
| `exchange` | Filter NSE/BSE stocks | MUST |
| `segment` | Filter equity (EQ) vs derivatives | MUST |
| `name` | Display name for UI | SHOULD |
| `lot_size`, `tick_size` | Trading constraints | NICE |

**Call frequency**: Once at startup (cache for 24 hours, refresh daily).
**Timeout**: 30 seconds.

**Why important**: Without instrument tokens, we can't call historical data API.

---

### 5. Nifty 50 constituents (batch quotes) — SHOULD HAVE

**Purpose**: Calculate market breadth (advance/decline ratio) if not provided by market context endpoint.

**Option A**: Use batch quotes endpoint with Nifty 50 symbols
```
GET /api/v1/quotes/batch?symbols=RELIANCE,TCS,HDFCBANK,...(all 50)
```

**Option B**: Dedicated Nifty 50 endpoint (if available)
```
GET /api/v1/indices/nifty50/constituents
```

**Expected response (Option B)**:
```json
{
  "index": "NIFTY 50",
  "constituents": [
    {
      "symbol": "RELIANCE",
      "ltp": 2456.75,
      "change_percent": 1.10,
      "volume": 1500000
    },
    ...
  ],
  "advancing": 35,
  "declining": 15,
  "unchanged": 0,
  "advance_decline_ratio": 2.33,
  "timestamp": "2026-02-12T14:30:00+05:30"
}
```

**Call frequency**: Every 5 minutes (only if market breadth not in market context).
**Priority**: SHOULD — needed for market breadth if not in quick-context.

---

### 6. Market depth (order book) — FUTURE

**Purpose**: Advanced feature for scoring (institutional buying signal).

```
GET /api/v1/quotes/depth?symbols=RELIANCE,SBIN
```

**Expected response**:
```json
{
  "RELIANCE": {
    "buy": [
      {"price": 2456.00, "quantity": 5000, "orders": 12},
      {"price": 2455.50, "quantity": 3000, "orders": 8},
      ...
    ],
    "sell": [
      {"price": 2457.00, "quantity": 4000, "orders": 10},
      ...
    ]
  }
}
```

**Call frequency**: Phase 6+ (optimization phase).
**Priority**: LOW (future enhancement).

---

## What Kite CANNOT provide (use Yahoo instead)

| Data type | Why not Kite | Use instead |
|-----------|--------------|-------------|
| S&P 500, NASDAQ, Dow Jones | Not available in Kite | Yahoo (yahoo-services) |
| US VIX (fear gauge) | Only has India VIX | Yahoo (yahoo-services) |
| Commodities (Gold, Crude Oil) | Not available | Yahoo (yahoo-services) |
| Forex (USD/INR) | Limited coverage | Yahoo (yahoo-services) |
| Fundamentals (P/E, ROE, margins) | Minimal fundamental data | Yahoo (yahoo-services) |
| Market cap | Not easily available | Yahoo (yahoo-services) |

See [Data Source Boundaries](./data-source-boundaries.md) for full matrix.

---

## Summary of requirements

| # | Endpoint | Priority | Frequency | Status |
|---|----------|----------|-----------|--------|
| 1 | `GET /api/v1/quotes/batch?symbols=...` | CRITICAL | Every 1 min | **NEW** — need batch support |
| 2 | `GET /api/market-context-data/quick-context` | CRITICAL | Every 5 min | **EXISTS** — verify breadth data |
| 3 | `GET /api/v1/historical/{symbol}` | IMPORTANT | Every 10 min | **NEW** — need historical candles |
| 4 | `GET /api/v1/instruments?exchange=NSE` | IMPORTANT | Once at startup | **NEW** — instrument tokens |
| 5 | `GET /api/v1/indices/nifty50/constituents` | SHOULD | Every 5 min | **OPTIONAL** — if breadth not in context |
| 6 | `GET /api/v1/quotes/depth` | FUTURE | Phase 6+ | **NEW** — market depth |

---

## Pre-integration verification

Before integrating with seed-stocks-service, run these commands to verify kite-services is ready:

```bash
# 1. Batch quotes (CRITICAL - check if endpoint exists)
curl -s "http://localhost:8179/api/v1/quotes/batch?symbols=RELIANCE,SBIN,TCS" | jq .
# Expected: {"quotes": {"RELIANCE": {"ltp": ..., "volume": ...}, ...}}

# 2. Market context (CRITICAL - verify breadth data exists)
curl -s "http://localhost:8179/api/market-context-data/quick-context?include_global=true&include_sector=true" | jq .
# Expected: {"market_regime": "bullish", "india_vix": 12.45, "market_breadth": {"advance_decline_ratio": 2.3, ...}}
# IMPORTANT: Check if "market_breadth" or "advance_decline_ratio" exists

# 3. Historical candles (IMPORTANT - for return calculation)
curl -s "http://localhost:8179/api/v1/historical/RELIANCE?interval=5minute&from=2026-02-12&to=2026-02-12" | jq .
# Expected: {"candles": [{"timestamp": ..., "open": ..., "close": ..., "volume": ...}], ...}

# 4. Instruments (IMPORTANT - for instrument tokens)
curl -s "http://localhost:8179/api/v1/instruments?exchange=NSE&segment=EQ" | jq . | head -50
# Expected: {"instruments": [{"instrument_token": 738561, "tradingsymbol": "RELIANCE", ...}]}

# 5. Nifty 50 constituents (OPTIONAL - only if breadth not in #2)
curl -s "http://localhost:8179/api/v1/indices/nifty50/constituents" | jq .
# OR use batch quotes with all 50 symbols

# 6. Single quote (existing fallback for testing)
curl -s "http://localhost:8179/api/v1/quotes/RELIANCE" | jq .
```

**Checklist**:
- [ ] Batch quotes endpoint exists and returns valid data
- [ ] Market context includes `market_breadth` or `advance_decline_ratio`
- [ ] Historical endpoint returns OHLCV candles
- [ ] Instruments endpoint returns NSE equity list with tokens
- [ ] Service is running on port 8179 and reachable

---

## Kite Connect API reference (for kite-service implementation)

For the kite-service developer, these are the underlying Kite Connect SDK calls:

| Our endpoint | Kite Connect SDK call | Notes |
|---|---|---|
| Batch quotes | `kite.quote(["NSE:SYM1", "NSE:SYM2", ...])` | Up to 500 instruments |
| Market context | Combination of: `kite.quote("NSE:NIFTY 50")`, India VIX, sector indices | Aggregated by kite-service |
| Historical | `kite.historical_data(token, from, to, "5minute")` | Per instrument, rate limited |
| Instruments | `kite.instruments("NSE")` | Returns full list, cache for 24h |
| Market depth | `kite.quote(instruments)` → `depth` field | Included in quote response |

---

## Configuration

Add to `envs/env.dev`, `envs/env.prod`, `envs/env.stage`:

```bash
# Kite service (already exists)
MARKET_CONTEXT_SERVICE_URL=http://localhost:8179

# New: batch quote settings
KITE_BATCH_QUOTE_ENDPOINT=/api/v1/quotes/batch
KITE_BATCH_QUOTE_MAX_SYMBOLS=200
KITE_HISTORICAL_ENDPOINT=/api/v1/historical
KITE_INSTRUMENTS_ENDPOINT=/api/v1/instruments

# Intervals
PRICE_ENRICHMENT_INTERVAL_SECONDS=60
MARKET_CONTEXT_INTERVAL_SECONDS=300
PERFORMANCE_TRACKING_INTERVAL_SECONDS=600
PRIOR_UPDATE_INTERVAL_SECONDS=900
```

---

## Related

- [Data Source Boundaries](./data-source-boundaries.md) — Kite vs Yahoo usage matrix
- [Yahoo Services Requirements](./yahoo-services-requirements.md) — What yahoo-services provides (global data only)
- [Design doc](../architecture/bayesian-engine-design.md) — Full Bayesian engine design
- [DB Schema](../architecture/bayesian-db-schema.md) — PostgreSQL tables
- [External Endpoints](../reference/EXTERNAL_ENDPOINTS.md) — Current external services
