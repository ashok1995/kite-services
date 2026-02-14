# Bayesian Engine Endpoints - Testing Guide

**Date**: 2026-02-13  
**Related**: Phase 1 & 2 Implementation

---

## Overview

This guide covers testing for the Bayesian engine integration features:

- Market breadth calculation
- Increased batch quote limit (200 symbols)
- Market context with breadth data

---

## Test Coverage

### Unit Tests

**File**: `tests/unit/test_services/test_market_breadth_service.py`

**Test Cases** (15 tests):

1. ✅ Service initialization
2. ✅ Successful market breadth calculation
3. ✅ All stocks advancing scenario
4. ✅ All stocks declining scenario
5. ✅ Caching mechanism
6. ✅ Force refresh bypasses cache
7. ✅ No quotes returned handling
8. ✅ API error handling
9. ✅ Missing change_percent field
10. ✅ Threshold boundary testing (0.01%)
11. ✅ Manual cache invalidation
12. ✅ Service cleanup
13. ✅ Breadth calculation disabled
14. ✅ Advanced/declining ratio calculations
15. ✅ Failed symbols tracking

**Run Unit Tests**:

```bash
# Install dependencies first
pip install pytest pytest-asyncio

# Run tests
python -m pytest tests/unit/test_services/test_market_breadth_service.py -v

# Run with coverage
python -m pytest tests/unit/test_services/test_market_breadth_service.py -v --cov=src/services/market_breadth_service
```

---

### Integration Tests

**File**: `tests/integration/test_bayesian_endpoints.sh`

**Test Cases** (7 tests):

1. ✅ Health check
2. ✅ Batch quotes with 50 symbols
3. ✅ Batch quotes with 200 symbols (new limit)
4. ✅ Market context with breadth data
5. ✅ Historical data (5-minute candles)
6. ✅ Historical data (15-minute candles)
7. ✅ Instruments endpoint with tokens
8. ✅ Real breadth data verification

**Run Integration Tests**:

```bash
# Start the service first
python src/main.py
# or
./scripts/run-dev.sh

# In another terminal, run integration tests
./tests/integration/test_bayesian_endpoints.sh http://localhost:8079

# Verbose mode (shows full responses)
./tests/integration/test_bayesian_endpoints.sh http://localhost:8079 true
```

**Expected Output**:

```
========================================================
  Bayesian Engine Endpoints - Integration Tests
========================================================
Base URL: http://localhost:8079

[TEST 1] Health Check
  ✅ PASS: Service is running

[TEST 2] Batch Quotes - Multiple Symbols (50 symbols)
  ✅ PASS: Request accepts 50 symbols
  ✅ PASS: Successfully fetched data for 45 symbols

[TEST 3] Batch Quotes - Large Batch (200 symbols)
  ✅ PASS: Service accepts 200 symbols

[TEST 4] Market Context - Breadth Data
  ✅ PASS: Advancing stocks: 35
  ✅ PASS: Declining stocks: 15
  ✅ PASS: Advance/Decline Ratio: 2.33

... (more tests)

========================================================
  Test Summary
========================================================
Total Tests:  7
Passed:       7
Failed:       0

✅ All tests passed!
```

---

## Manual Testing

### 1. Test Configuration Loading

```bash
# Verify settings
python3 -c "
import sys
sys.path.insert(0, 'src')
from config.settings import get_settings
s = get_settings()
print(f'QUOTES_MAX_SYMBOLS: {s.service.quotes_max_symbols}')
print(f'MARKET_BREADTH_ENABLED: {s.service.market_breadth_enabled}')
print(f'MARKET_BREADTH_CACHE_TTL: {s.service.market_breadth_cache_ttl}')
"
```

**Expected Output**:

```
QUOTES_MAX_SYMBOLS: 200
MARKET_BREADTH_ENABLED: True
MARKET_BREADTH_CACHE_TTL: 60
```

---

### 2. Test Batch Quotes (50 symbols)

```bash
curl -X POST http://localhost:8079/api/market/quotes \
  -H "Content-Type: application/json" \
  -d '{
    "symbols": ["RELIANCE", "TCS", "INFY", "HDFC", "ICICIBANK",
                "HINDUNILVR", "BHARTIARTL", "KOTAKBANK", "ITC", "LT",
                "SBIN", "AXISBANK", "BAJFINANCE", "ASIANPAINT", "MARUTI",
                "HCLTECH", "WIPRO", "ULTRACEMCO", "TITAN", "NESTLEIND",
                "SUNPHARMA", "TECHM", "BAJAJFINSV", "ONGC", "NTPC",
                "POWERGRID", "M&M", "ADANIPORTS", "COALINDIA", "TATASTEEL",
                "TATAMOTORS", "DIVISLAB", "GRASIM", "JSWSTEEL", "HINDALCO",
                "INDUSINDBK", "DRREDDY", "BRITANNIA", "APOLLOHOSP", "CIPLA",
                "EICHERMOT", "BAJAJ-AUTO", "HEROMOTOCO", "BPCL", "SHREECEM",
                "SBILIFE", "UPL", "ADANIENT", "HDFCLIFE", "TATACONSUM"],
    "exchange": "NSE"
  }' | jq '.total_symbols, .successful_symbols'
```

**Expected**: Both should show 50 (or close, depending on market data)

---

### 3. Test Batch Quotes (200 symbols - NEW)

```bash
# Create a file with 200 symbols
cat > /tmp/symbols_200.json << 'EOF'
{
  "symbols": ["RELIANCE", "TCS", "INFY", "HDFC", "ICICIBANK", ...repeat to 200...],
  "exchange": "NSE"
}
EOF

# Test with 200 symbols
curl -X POST http://localhost:8079/api/market/quotes \
  -H "Content-Type: application/json" \
  -d @/tmp/symbols_200.json | jq '.total_symbols, .successful_symbols, .processing_time_ms'
```

**Expected**:

- `total_symbols`: 200
- `successful_symbols`: 150-200 (depending on market data availability)
- `processing_time_ms`: <5000ms

---

### 4. Test Market Context with Breadth

```bash
curl -X POST http://localhost:8079/api/analysis/context \
  -H "Content-Type: application/json" \
  -d '{
    "include_global_data": true,
    "include_sector_data": true
  }' | jq '.market_context.indian_data | {
    advances,
    declines,
    unchanged,
    advance_decline_ratio
  }'
```

**Expected Output**:

```json
{
  "advances": 35,
  "declines": 15,
  "unchanged": 0,
  "advance_decline_ratio": "2.33"
}
```

**Verify**:

- Values should be real (not 0 or default)
- Total (advances + declines + unchanged) should be ≤50 (Nifty 50)
- AD ratio should match: advances / declines

---

### 5. Test Historical Data (5-minute)

```bash
curl -X POST http://localhost:8079/api/market/data \
  -H "Content-Type: application/json" \
  -d '{
    "symbols": ["RELIANCE"],
    "exchange": "NSE",
    "data_type": "historical",
    "from_date": "2026-02-13",
    "to_date": "2026-02-13",
    "interval": "5minute"
  }' | jq '.success, .data.RELIANCE'
```

**Expected**: Should return candle data if during market hours

---

### 6. Test Instruments Endpoint

```bash
curl -s "http://localhost:8079/api/market/instruments?exchange=NSE&instrument_type=EQ&limit=5" | \
  jq '.instruments[0:2] | .[] | {
    tradingsymbol,
    instrument_token,
    exchange,
    instrument_type
  }'
```

**Expected Output**:

```json
{
  "tradingsymbol": "RELIANCE",
  "instrument_token": 738561,
  "exchange": "NSE",
  "instrument_type": "EQ"
}
```

---

## Performance Testing

### 1. Batch Quote Performance

Test response times with different batch sizes:

```bash
# 50 symbols
time curl -X POST http://localhost:8079/api/market/quotes \
  -H "Content-Type: application/json" \
  -d '{"symbols": [...50 symbols...], "exchange": "NSE"}' \
  > /dev/null 2>&1

# 100 symbols
time curl -X POST http://localhost:8079/api/market/quotes \
  -H "Content-Type: application/json" \
  -d '{"symbols": [...100 symbols...], "exchange": "NSE"}' \
  > /dev/null 2>&1

# 200 symbols
time curl -X POST http://localhost:8079/api/market/quotes \
  -H "Content-Type: application/json" \
  -d '{"symbols": [...200 symbols...], "exchange": "NSE"}' \
  > /dev/null 2>&1
```

**Expected**:

- 50 symbols: ~1-2s
- 100 symbols: ~2-3s
- 200 symbols: ~3-5s

---

### 2. Market Breadth Cache Performance

Test cache effectiveness:

```bash
# First call (cache miss)
time curl -s -X POST http://localhost:8079/api/analysis/context \
  -H "Content-Type: application/json" \
  -d '{}' | jq '.processing_time_ms'

# Second call within 60s (cache hit)
time curl -s -X POST http://localhost:8079/api/analysis/context \
  -H "Content-Type: application/json" \
  -d '{}' | jq '.processing_time_ms'
```

**Expected**:

- First call: 500-1000ms
- Second call: 50-200ms (much faster due to cache)

---

## Regression Testing

Ensure existing functionality still works:

```bash
# 1. Single stock quote (existing)
curl -X POST http://localhost:8079/api/market/quotes \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["RELIANCE"], "exchange": "NSE"}' | \
  jq '.stocks[0].symbol, .stocks[0].last_price'

# 2. Market context without breadth fields (backward compatible)
curl -X POST http://localhost:8079/api/analysis/context \
  -H "Content-Type: application/json" \
  -d '{"include_global_data": false}' | jq '.market_context'

# 3. Health endpoint
curl -s http://localhost:8079/health | jq '.status'
```

All should return successfully without errors.

---

## Error Testing

### 1. Test with Too Many Symbols (>200)

```bash
# Generate 250 symbols
curl -X POST http://localhost:8079/api/market/quotes \
  -H "Content-Type: application/json" \
  -d '{"symbols": [...250 symbols...], "exchange": "NSE"}' | \
  jq '.detail'
```

**Expected**: `"Maximum 200 symbols allowed. Requested: 250"`

---

### 2. Test Market Breadth Service Failure

Simulate by stopping Kite service and checking fallback:

```bash
# Should return default breadth values gracefully
curl -X POST http://localhost:8079/api/analysis/context \
  -H "Content-Type: application/json" \
  -d '{}' | jq '.market_context.indian_data.advance_decline_ratio'
```

**Expected**: Should return "1.0" (default) without crashing

---

## Smoke Tests (Quick Verification)

Run these after deployment:

```bash
#!/bin/bash
# Quick smoke test

BASE_URL="http://localhost:8079"

echo "1. Health check..."
curl -sf "$BASE_URL/health" > /dev/null && echo "✅" || echo "❌"

echo "2. Batch quotes (10 symbols)..."
curl -sf -X POST "$BASE_URL/api/market/quotes" \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["RELIANCE", "TCS", "INFY", "HDFC", "ICICIBANK", "SBIN", "LT", "BAJFINANCE", "HCLTECH", "WIPRO"], "exchange": "NSE"}' \
  | jq -e '.total_symbols == 10' > /dev/null && echo "✅" || echo "❌"

echo "3. Market context with breadth..."
curl -sf -X POST "$BASE_URL/api/analysis/context" \
  -H "Content-Type: application/json" \
  -d '{}' | jq -e '.market_context.indian_data.advance_decline_ratio' > /dev/null && echo "✅" || echo "❌"

echo "Done!"
```

---

## Test Data

### Nifty 50 Symbols (for breadth testing)

```
RELIANCE, TCS, HDFCBANK, INFY, ICICIBANK, HINDUNILVR, BHARTIARTL, KOTAKBANK,
ITC, LT, SBIN, AXISBANK, BAJFINANCE, ASIANPAINT, MARUTI, HCLTECH, WIPRO,
ULTRACEMCO, TITAN, NESTLEIND, SUNPHARMA, TECHM, BAJAJFINSV, ONGC, NTPC,
POWERGRID, M&M, ADANIPORTS, COALINDIA, TATASTEEL, TATAMOTORS, DIVISLAB,
GRASIM, JSWSTEEL, HINDALCO, INDUSINDBK, DRREDDY, BRITANNIA, APOLLOHOSP,
CIPLA, EICHERMOT, BAJAJ-AUTO, HEROMOTOCO, BPCL, SHREECEM, SBILIFE, UPL,
ADANIENT, HDFCLIFE, TATACONSUM
```

---

## Troubleshooting

### Issue: Unit tests fail with import errors

**Solution**:

```bash
# Add src to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
pytest tests/unit/test_services/test_market_breadth_service.py -v
```

### Issue: Integration tests fail - "Service not accessible"

**Solution**:

- Ensure service is running: `python src/main.py`
- Check port: `netstat -an | grep 8079`
- Verify health: `curl http://localhost:8079/health`

### Issue: Market breadth returns all zeros

**Solution**:

- Check if Kite Connect is authenticated
- Verify during market hours (9:15 AM - 3:30 PM IST)
- Check logs: `tail -f logs/kite_services.log`

### Issue: Batch quotes fail with 200 symbols

**Solution**:

- Verify config: `grep QUOTES_MAX_SYMBOLS envs/development.env`
- Restart service after config change
- Check service logs for errors

---

## Continuous Integration

Add to CI/CD pipeline:

```yaml
# .github/workflows/test.yml
- name: Run unit tests
  run: |
    pip install pytest pytest-asyncio
    pytest tests/unit/test_services/test_market_breadth_service.py -v

- name: Run integration tests
  run: |
    python src/main.py &
    sleep 5
    ./tests/integration/test_bayesian_endpoints.sh http://localhost:8079
```

---

## Test Checklist

Before merging to main:

- [ ] All unit tests pass
- [ ] Integration tests pass
- [ ] Manual smoke tests pass
- [ ] Performance tests within acceptable ranges
- [ ] Regression tests pass (existing functionality works)
- [ ] Error handling tests pass
- [ ] Documentation updated
- [ ] No linter errors

---

## Related Documents

- Unit Tests: `tests/unit/test_services/test_market_breadth_service.py`
- Integration Tests: `tests/integration/test_bayesian_endpoints.sh`
- Verification Script: `scripts/verify_bayesian_changes.sh`
- Implementation: `docs/integration/bayesian-phase1-phase2-complete.md`
