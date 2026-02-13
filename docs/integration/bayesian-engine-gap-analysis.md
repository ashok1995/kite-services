# Bayesian Engine Integration - Gap Analysis

**Date**: 2026-02-13  
**Branch**: `feat/bayesian-engine-endpoints`  
**Related**: [Kite Service Requirements](../../kite-service-requirements.md)

## Purpose

This document analyzes the gap between current kite-services endpoints and what's required by the Bayesian Continuous Intelligence Engine.

---

## Summary

| Requirement | Current Endpoint | Status | Action Needed |
|-------------|------------------|--------|---------------|
| Batch quotes (200 symbols) | `/api/market/quotes` (POST) | ✅ EXISTS | Verify 200-symbol limit |
| Market context with breadth | `/api/analysis/context` (POST) | ⚠️ PARTIAL | Add breadth data |
| Historical candles (5m, 15m) | `/api/market/data` (POST) | ✅ EXISTS | Verify interval support |
| Instrument tokens (NSE/BSE) | `/api/market/instruments` (GET) | ✅ EXISTS | Verify token field |
| Nifty 50 constituents | N/A | ❌ MISSING | Create new endpoint |

---

## Detailed Analysis

### 1. Batch Quotes - ✅ MOSTLY READY

**Requirement**: Batch quotes for up to 200 symbols in one call

```
GET /api/v1/quotes/batch?symbols=RELIANCE,SBIN,HDFCBANK,...
```

**Current Endpoint**: `/api/market/quotes` (POST)

```json
{
  "symbols": ["RELIANCE", "SBIN", "TCS"],
  "exchange": "NSE"
}
```

**Status**: ✅ Endpoint exists, supports batch quotes

**Verification Needed**:

- [ ] Check `QUOTES_MAX_SYMBOLS` config (current default unknown)
- [ ] Ensure it supports at least 200 symbols (Kite API limit is 500)
- [ ] Verify all required fields are returned:
  - ✅ `last_price` / `ltp`
  - ✅ `volume`
  - ✅ `open`, `high`, `low`, `close`
  - ✅ `change_percent`
  - ✅ `average_price`
  - ⚠️ `buy_quantity`, `sell_quantity` (need to verify)
  - ⚠️ `last_trade_time` (need to verify)

**Action Items**:

1. Read config to verify `QUOTES_MAX_SYMBOLS` setting
2. Test with 200 symbols to ensure it works
3. Add missing fields if not present in response model
4. Update response model if needed

---

### 2. Market Context - ⚠️ NEEDS BREADTH DATA

**Requirement**: Market context with breadth data

```
GET /api/market-context-data/quick-context?include_global=true&include_sector=true
```

Expected fields:

- `market_regime` (bullish/bearish/neutral)
- `india_vix` / `vix_level`
- `volatility_regime`
- **`market_breadth.advance_decline_ratio`** ⚠️
- **`market_breadth.advancing_stocks`** ⚠️
- **`market_breadth.declining_stocks`** ⚠️
- `nifty_50.change_percent`
- `sectors` (sector performance)

**Current Endpoint**: `/api/analysis/context` (POST)

**Status**: ⚠️ Endpoint exists but may be missing breadth data

**Verification Needed**:

- [ ] Check if `market_breadth` data is included in response
- [ ] Check if `advance_decline_ratio` is calculated
- [ ] Verify sector data structure matches requirement

**Action Items**:

1. Read current response model for `/api/analysis/context`
2. If breadth data missing, add calculation logic:
   - Option A: Calculate from Nifty 50 constituent quotes
   - Option B: Calculate from broader NSE symbol set
3. Add breadth fields to response model
4. Implement breadth calculation service method

---

### 3. Historical Candles - ✅ EXISTS

**Requirement**: Historical OHLCV candles (5-minute, 15-minute)

```
GET /api/v1/historical/{symbol}?interval=5minute&from=2026-02-12&to=2026-02-12
```

**Current Endpoint**: `/api/market/data` (POST)

```json
{
  "symbols": ["RELIANCE"],
  "exchange": "NSE",
  "data_type": "historical",
  "from_date": "2026-02-12",
  "to_date": "2026-02-12",
  "interval": "5minute"
}
```

**Status**: ✅ Endpoint exists and supports historical data

**Verification Needed**:

- [ ] Verify supported intervals: `5minute`, `15minute`, `1hour`, `1day`
- [ ] Verify candle data structure matches requirement
- [ ] Test with date range (intraday)

**Action Items**:

1. Test endpoint with required intervals
2. Verify response format matches requirements document
3. No changes needed if tests pass

---

### 4. Instruments List - ✅ EXISTS

**Requirement**: Instrument list with tokens, lot sizes, tick sizes

```
GET /api/v1/instruments?exchange=NSE&segment=EQ
```

**Current Endpoint**: `/api/market/instruments` (GET)

```
GET /api/market/instruments?exchange=NSE&instrument_type=EQ&limit=1000
```

**Status**: ✅ Endpoint exists

**Verification Needed**:

- [ ] Verify `instrument_token` field is included
- [ ] Verify filtering by exchange and segment works
- [ ] Check if `segment` parameter is supported (currently uses `instrument_type`)

**Action Items**:

1. Test endpoint with NSE/BSE filters
2. Verify response includes all required fields:
   - `instrument_token` ✅
   - `tradingsymbol` ✅
   - `exchange` ✅
   - `segment` or `instrument_type` ⚠️
   - `name` ✅
   - `lot_size`, `tick_size` ✅
3. Add `segment` parameter support if missing

---

### 5. Nifty 50 Constituents - ❌ MISSING (OPTIONAL)

**Requirement**: Nifty 50 constituent quotes (for breadth calculation)

**Option A**: Use batch quotes

```
POST /api/market/quotes
{"symbols": ["RELIANCE", "TCS", "HDFCBANK", ... all 50], "exchange": "NSE"}
```

**Option B**: Dedicated endpoint

```
GET /api/v1/indices/nifty50/constituents
```

**Status**: ❌ Dedicated endpoint doesn't exist

**Decision**: Use Option A (batch quotes with hardcoded Nifty 50 list)

**Action Items**:

1. Create a constants file with Nifty 50 constituent symbols
2. Use existing `/api/market/quotes` endpoint to fetch all 50
3. Calculate breadth metrics (advances/declines) in market context service
4. No new endpoint needed

---

## Implementation Plan

### Phase 1: Verification (Current Sprint)

1. ✅ Pull latest code from main
2. ✅ Create feature branch `feat/bayesian-engine-endpoints`
3. ⬜ Test each existing endpoint with requirements
4. ⬜ Document gaps and missing fields

### Phase 2: Extensions (Current Sprint)

1. ⬜ Add market breadth calculation to market context service
2. ⬜ Create Nifty 50 constants file
3. ⬜ Update response models with missing fields
4. ⬜ Increase `QUOTES_MAX_SYMBOLS` to 200 if needed

### Phase 3: Testing (Current Sprint)

1. ⬜ Write integration tests for batch quotes (200 symbols)
2. ⬜ Test market context with breadth data
3. ⬜ Test historical candles with 5m/15m intervals
4. ⬜ Verify instruments endpoint returns tokens

### Phase 4: Documentation (Current Sprint)

1. ⬜ Update API reference with verified capabilities
2. ⬜ Create integration guide for Bayesian engine
3. ⬜ Document curl commands for pre-integration verification

---

## Endpoint Mapping

| Requirements Doc | Current Endpoint | Notes |
|------------------|------------------|-------|
| `GET /api/v1/quotes/batch` | `POST /api/market/quotes` | Works, verify limit |
| `GET /api/market-context-data/quick-context` | `POST /api/analysis/context` | Add breadth data |
| `GET /api/v1/historical/{symbol}` | `POST /api/market/data` | Works, verify intervals |
| `GET /api/v1/instruments` | `GET /api/market/instruments` | Works, verify fields |
| `GET /api/v1/indices/nifty50/constituents` | Use batch quotes | No dedicated endpoint |

---

## Configuration Updates Needed

Add to `envs/development.env`, `envs/staging.env`, `envs/production.env`:

```bash
# Batch quote settings (verify/update)
QUOTES_MAX_SYMBOLS=200  # Ensure this is at least 200

# Market context settings
MARKET_BREADTH_ENABLED=true
MARKET_BREADTH_SOURCE=nifty50  # Use Nifty 50 constituents

# Historical data settings
HISTORICAL_MAX_DAYS=90  # For return calculation
```

---

## Next Steps

1. **Immediate**: Verify existing endpoints against requirements
2. **Short-term**: Implement market breadth calculation
3. **Before integration**: Run curl commands from requirements doc to verify all endpoints
4. **Final**: Update integration docs with actual endpoint URLs

---

## Related Documents

- [Kite Service Requirements](../../kite-service-requirements.md) - Full requirements from Bayesian engine team
- [API Reference](../api/api-reference.md) - Current API documentation
- [Architecture](../architecture/architecture.md) - System architecture
