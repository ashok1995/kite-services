# Bayesian Engine Integration - Implementation Plan

**Date**: 2026-02-13  
**Branch**: `feat/bayesian-engine-endpoints`  
**Status**: In Progress  
**Related**: [Gap Analysis](./bayesian-engine-gap-analysis.md), [Requirements](../../kite-service-requirements.md)

---

## Executive Summary

**Goal**: Extend kite-services to support Bayesian Continuous Intelligence Engine requirements

**Current State**: Core endpoints exist but need extensions:

- ✅ Batch quotes exist (50 symbol limit → needs 200)
- ⚠️ Market context exists (missing breadth data)
- ✅ Historical data exists (verify intervals)
- ✅ Instruments endpoint exists (verify token field)

**Effort Estimate**: 4-6 hours

- Phase 1 (Config): 30 min
- Phase 2 (Market Breadth): 2-3 hours
- Phase 3 (Testing): 1-2 hours
- Phase 4 (Documentation): 1 hour

---

## Phase 1: Configuration Updates ⬜

### 1.1 Increase Batch Quote Limit

**Files to modify**:

- `src/config/settings.py` (line 216)
- `envs/development.env`
- `envs/staging.env`
- `envs/production.env`

**Changes**:

```python
# settings.py (line 216)
quotes_max_symbols: int = Field(200, env="QUOTES_MAX_SYMBOLS")  # Was: 50
```

```bash
# All env files
QUOTES_MAX_SYMBOLS=200  # Allow up to 200 symbols (Kite API limit: 500)
```

**Rationale**: Bayesian engine needs to fetch 100-200 stock prices every minute

**Testing**:

```bash
# Test with 200 symbols
curl -X POST http://localhost:8079/api/market/quotes \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["SYM1", "SYM2", ... 200 symbols], "exchange": "NSE"}'
```

---

### 1.2 Add Market Context Configuration

**Files to modify**:

- `envs/development.env`
- `envs/staging.env`
- `envs/production.env`

**Add to all env files**:

```bash
# Market Context Configuration
MARKET_BREADTH_ENABLED=true
MARKET_BREADTH_SOURCE=nifty50  # Calculate from Nifty 50 constituents
NIFTY50_QUOTE_CACHE_TTL=60     # Cache Nifty 50 quotes for 60 seconds

# Historical data configuration
HISTORICAL_MAX_DAYS=90         # For return calculation
HISTORICAL_DEFAULT_INTERVAL=5minute
```

---

## Phase 2: Market Breadth Implementation ⬜

### 2.1 Create Nifty 50 Constants

**File**: `src/common/constants.py` (create if doesn't exist)

```python
"""
Common Constants
================

Shared constants across the application.
"""

# Nifty 50 constituent symbols (as of 2026-02-13)
NIFTY_50_CONSTITUENTS = [
    "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK",
    "HINDUNILVR", "BHARTIARTL", "KOTAKBANK", "ITC", "LT",
    "SBIN", "AXISBANK", "BAJFINANCE", "ASIANPAINT", "MARUTI",
    "HCLTECH", "WIPRO", "ULTRACEMCO", "TITAN", "NESTLEIND",
    "SUNPHARMA", "TECHM", "BAJAJFINSV", "ONGC", "NTPC",
    "POWERGRID", "M&M", "ADANIPORTS", "COALINDIA", "TATASTEEL",
    "TATAMOTORS", "DIVISLAB", "GRASIM", "JSWSTEEL", "HINDALCO",
    "INDUSINDBK", "DRREDDY", "BRITANNIA", "APOLLOHOSP", "CIPLA",
    "EICHERMOT", "BAJAJ-AUTO", "HEROMOTOCO", "BPCL", "SHREECEM",
    "SBILIFE", "UPL", "ADANIENT", "HDFCLIFE", "TATACONSUM"
]

# Exchange prefixes
EXCHANGE_PREFIX = {
    "NSE": "NSE:",
    "BSE": "BSE:"
}
```

**Testing**:

```python
from common.constants import NIFTY_50_CONSTITUENTS
assert len(NIFTY_50_CONSTITUENTS) == 50
```

---

### 2.2 Create Market Breadth Service

**File**: `src/services/market_breadth_service.py` (new file)

```python
"""
Market Breadth Service
======================

Calculates market breadth metrics (advance/decline ratio, advancing/declining stocks).
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional

from common.constants import NIFTY_50_CONSTITUENTS
from core.kite_client import KiteClient


logger = logging.getLogger(__name__)


class MarketBreadthService:
    """Service for calculating market breadth metrics."""

    def __init__(self, kite_client: KiteClient):
        """Initialize market breadth service.

        Args:
            kite_client: Kite Connect client for fetching quotes
        """
        self.kite_client = kite_client
        self._cache: Optional[Dict] = None
        self._cache_timestamp: Optional[datetime] = None
        self._cache_ttl_seconds = 60  # Cache for 1 minute

    async def get_market_breadth(self, force_refresh: bool = False) -> Dict:
        """Get market breadth metrics.

        Calculates advance/decline ratio from Nifty 50 constituents.

        Args:
            force_refresh: Force refresh cache

        Returns:
            Dict with breadth metrics:
            {
                "advance_decline_ratio": Decimal,
                "advancing_stocks": int,
                "declining_stocks": int,
                "unchanged_stocks": int,
                "total_stocks": int,
                "timestamp": datetime
            }
        """
        # Check cache
        if not force_refresh and self._is_cache_valid():
            logger.debug("Returning cached market breadth data")
            return self._cache

        try:
            # Fetch Nifty 50 quotes
            logger.info("Fetching Nifty 50 quotes for breadth calculation")
            nse_symbols = [f"NSE:{symbol}" for symbol in NIFTY_50_CONSTITUENTS]
            quotes = await self.kite_client.quote(nse_symbols)

            if not quotes:
                logger.warning("No quotes returned for Nifty 50 constituents")
                return self._get_default_breadth()

            # Calculate breadth metrics
            advancing = 0
            declining = 0
            unchanged = 0

            for symbol_key, quote_data in quotes.items():
                if not quote_data:
                    continue

                change_percent = quote_data.get("net_change_percent", 0)

                if change_percent > 0:
                    advancing += 1
                elif change_percent < 0:
                    declining += 1
                else:
                    unchanged += 1

            total = advancing + declining + unchanged

            # Calculate advance/decline ratio (handle division by zero)
            ad_ratio = Decimal(str(advancing / declining if declining > 0 else advancing))

            breadth_data = {
                "advance_decline_ratio": round(ad_ratio, 2),
                "advancing_stocks": advancing,
                "declining_stocks": declining,
                "unchanged_stocks": unchanged,
                "total_stocks": total,
                "timestamp": datetime.now(),
            }

            # Update cache
            self._cache = breadth_data
            self._cache_timestamp = datetime.now()

            logger.info(
                f"Market breadth calculated: {advancing} up, {declining} down, "
                f"ratio: {ad_ratio:.2f}"
            )

            return breadth_data

        except Exception as e:
            logger.error(f"Failed to calculate market breadth: {e}", exc_info=True)
            return self._get_default_breadth()

    def _is_cache_valid(self) -> bool:
        """Check if cached data is still valid."""
        if not self._cache or not self._cache_timestamp:
            return False

        age_seconds = (datetime.now() - self._cache_timestamp).total_seconds()
        return age_seconds < self._cache_ttl_seconds

    def _get_default_breadth(self) -> Dict:
        """Return default breadth data when calculation fails."""
        return {
            "advance_decline_ratio": Decimal("1.0"),
            "advancing_stocks": 0,
            "declining_stocks": 0,
            "unchanged_stocks": 0,
            "total_stocks": 0,
            "timestamp": datetime.now(),
        }
```

**Testing**:

```python
# Unit test
async def test_market_breadth():
    service = MarketBreadthService(kite_client)
    breadth = await service.get_market_breadth()
    assert "advance_decline_ratio" in breadth
    assert breadth["total_stocks"] <= 50
```

---

### 2.3 Add Breadth to Market Context Response

**File**: `src/models/unified_api_models.py` (or market context models)

**Add to MarketContextResponse model**:

```python
class MarketBreadth(BaseModel):
    """Market breadth metrics."""
    advance_decline_ratio: Decimal = Field(..., description="Advance/decline ratio")
    advancing_stocks: int = Field(..., description="Number of advancing stocks")
    declining_stocks: int = Field(..., description="Number of declining stocks")
    unchanged_stocks: int = Field(0, description="Number of unchanged stocks")
    total_stocks: int = Field(..., description="Total stocks analyzed")
    timestamp: datetime = Field(..., description="Breadth calculation timestamp")


class MarketContextResponse(BaseModel):
    """Market context response with breadth data."""
    # ... existing fields ...

    # Add breadth field
    market_breadth: Optional[MarketBreadth] = Field(
        None,
        description="Market breadth metrics (advance/decline ratio)"
    )
```

---

### 2.4 Integrate Breadth into Market Context Service

**File**: `src/services/market_context_service.py` (or similar)

**Add breadth service to initialization**:

```python
from services.market_breadth_service import MarketBreadthService

class MarketContextService:
    def __init__(self, kite_client, yahoo_service):
        self.kite_client = kite_client
        self.yahoo_service = yahoo_service
        self.breadth_service = MarketBreadthService(kite_client)

    async def get_market_context(self, request):
        # ... existing logic ...

        # Add breadth data
        breadth_data = None
        if request.include_breadth or request.scope in ["comprehensive", "standard"]:
            breadth_data = await self.breadth_service.get_market_breadth()

        return MarketContextResponse(
            # ... existing fields ...
            market_breadth=breadth_data
        )
```

---

## Phase 3: Verification & Testing ⬜

### 3.1 Endpoint Verification

**Script**: `tests/integration/test_bayesian_endpoints.sh` (new file)

```bash
#!/bin/bash
# Integration tests for Bayesian engine endpoints

BASE_URL="${1:-http://localhost:8079}"

echo "Testing Bayesian Engine Endpoints..."
echo "Base URL: $BASE_URL"
echo ""

# Test 1: Batch quotes (200 symbols)
echo "✅ Test 1: Batch quotes with 200 symbols"
# Generate 200 symbols for testing
SYMBOLS="RELIANCE,SBIN,TCS,INFY,HDFC..."  # Full 200 symbols
curl -s -X POST "$BASE_URL/api/market/quotes" \
  -H "Content-Type: application/json" \
  -d "{\"symbols\": [$SYMBOLS], \"exchange\": \"NSE\"}" | jq '.total_symbols, .successful_symbols'

# Test 2: Market context with breadth
echo ""
echo "✅ Test 2: Market context with breadth data"
curl -s -X POST "$BASE_URL/api/analysis/context" \
  -H "Content-Type: application/json" \
  -d '{"include_global": true, "include_indian": true}' | \
  jq '.market_breadth'

# Test 3: Historical candles (5-minute)
echo ""
echo "✅ Test 3: Historical candles (5-minute interval)"
curl -s -X POST "$BASE_URL/api/market/data" \
  -H "Content-Type: application/json" \
  -d '{
    "symbols": ["RELIANCE"],
    "exchange": "NSE",
    "data_type": "historical",
    "from_date": "2026-02-12",
    "to_date": "2026-02-12",
    "interval": "5minute"
  }' | jq '.data.RELIANCE'

# Test 4: Instruments with tokens
echo ""
echo "✅ Test 4: Instruments endpoint (NSE EQ)"
curl -s "$BASE_URL/api/market/instruments?exchange=NSE&instrument_type=EQ&limit=5" | \
  jq '.instruments[0:2]'

echo ""
echo "All tests completed!"
```

**Run**:

```bash
chmod +x tests/integration/test_bayesian_endpoints.sh
./tests/integration/test_bayesian_endpoints.sh http://localhost:8079
```

---

### 3.2 Unit Tests

**File**: `tests/unit/test_market_breadth_service.py` (new file)

```python
"""Unit tests for market breadth service."""

import pytest
from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

from services.market_breadth_service import MarketBreadthService


@pytest.mark.asyncio
async def test_market_breadth_calculation():
    """Test market breadth calculation with mock data."""
    # Mock Kite client
    kite_client = MagicMock()
    kite_client.quote = AsyncMock(return_value={
        "NSE:RELIANCE": {"net_change_percent": 1.5},
        "NSE:TCS": {"net_change_percent": 0.8},
        "NSE:INFY": {"net_change_percent": -0.5},
        "NSE:HDFC": {"net_change_percent": -1.2},
        "NSE:SBIN": {"net_change_percent": 0.0},
    })

    # Test service
    service = MarketBreadthService(kite_client)
    breadth = await service.get_market_breadth()

    # Assertions
    assert breadth["advancing_stocks"] == 2
    assert breadth["declining_stocks"] == 2
    assert breadth["unchanged_stocks"] == 1
    assert breadth["total_stocks"] == 5
    assert breadth["advance_decline_ratio"] == Decimal("1.0")


@pytest.mark.asyncio
async def test_market_breadth_caching():
    """Test market breadth caching mechanism."""
    kite_client = MagicMock()
    kite_client.quote = AsyncMock(return_value={
        "NSE:RELIANCE": {"net_change_percent": 1.5},
    })

    service = MarketBreadthService(kite_client)

    # First call - should fetch data
    breadth1 = await service.get_market_breadth()
    assert kite_client.quote.call_count == 1

    # Second call - should use cache
    breadth2 = await service.get_market_breadth()
    assert kite_client.quote.call_count == 1  # No additional call

    # Force refresh
    breadth3 = await service.get_market_breadth(force_refresh=True)
    assert kite_client.quote.call_count == 2  # New call made
```

**Run**:

```bash
pytest tests/unit/test_market_breadth_service.py -v
```

---

## Phase 4: Documentation Updates ⬜

### 4.1 Update API Reference

**File**: `docs/api/api-reference.md`

**Add section**:

```markdown
### POST /api/analysis/context (Updated)

Market context with breadth data.

**Request**:
```json
{
  "symbols": [],
  "include_global": true,
  "include_indian": true,
  "include_sentiment": true
}
```

**Response** (new fields highlighted):

```json
{
  "global_markets": [...],
  "indian_markets": [...],
  "market_breadth": {                    // ⭐ NEW
    "advance_decline_ratio": 2.33,
    "advancing_stocks": 35,
    "declining_stocks": 15,
    "unchanged_stocks": 0,
    "total_stocks": 50,
    "timestamp": "2026-02-13T14:30:00"
  },
  "timestamp": "2026-02-13T14:30:00"
}
```

```

---

### 4.2 Create Integration Guide

**File**: `docs/integration/bayesian-engine-integration.md` (new file)

**Content**:
```markdown
# Bayesian Engine Integration Guide

Complete guide for integrating with Kite Services for Bayesian Continuous Intelligence Engine.

## Prerequisites
- Kite Services running on port 8179 (production) or 8079 (development)
- Valid Kite Connect credentials configured

## Endpoint Usage

### 1. Batch Quotes (Every 1 minute)
Fetch real-time prices for 100-200 stocks

### 2. Market Context (Every 5 minutes)
Get market regime, VIX, breadth, sectors

### 3. Historical Candles (Every 10 minutes)
Get OHLCV for return calculation

### 4. Instruments (Once at startup)
Map symbols to tokens

## Sample Code

### Python Example
```python
import httpx

# Batch quotes
async def fetch_batch_quotes(symbols: List[str]):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8179/api/market/quotes",
            json={"symbols": symbols, "exchange": "NSE"}
        )
        return response.json()

# Market context
async def fetch_market_context():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8179/api/analysis/context",
            json={"include_global": true, "include_indian": true}
        )
        return response.json()
```

## Rate Limits

- Batch quotes: 100 requests/minute
- Market context: 100 requests/minute
- Historical data: 100 requests/minute

## Error Handling

[...]

```

---

### 4.3 Update CHANGELOG

**File**: `CHANGELOG.md`

**Add entry**:
```markdown
## [1.1.0] - 2026-02-13

### Added
- Market breadth calculation (advance/decline ratio) from Nifty 50 constituents
- Increased batch quote limit to 200 symbols (was 50)
- Nifty 50 constituent constants
- Market breadth service with 60-second caching
- Integration guide for Bayesian engine

### Changed
- Updated `QUOTES_MAX_SYMBOLS` default to 200
- Added breadth data to market context response
- Enhanced market context endpoint with breadth metrics

### Fixed
- None

### Deprecated
- None
```

---

## Summary Checklist

### Configuration ⬜

- [ ] Update `quotes_max_symbols` to 200 in settings.py
- [ ] Add `QUOTES_MAX_SYMBOLS=200` to all env files
- [ ] Add market breadth config to env files

### Implementation ⬜

- [ ] Create `src/common/constants.py` with Nifty 50 list
- [ ] Create `src/services/market_breadth_service.py`
- [ ] Add `MarketBreadth` model to response models
- [ ] Integrate breadth service into market context service
- [ ] Update market context endpoint to include breadth

### Testing ⬜

- [ ] Create integration test script
- [ ] Create unit tests for market breadth service
- [ ] Test batch quotes with 200 symbols
- [ ] Test market context with breadth data
- [ ] Test historical candles with 5m/15m intervals
- [ ] Verify instruments endpoint returns tokens

### Documentation ⬜

- [ ] Update API reference with breadth fields
- [ ] Create Bayesian engine integration guide
- [ ] Update CHANGELOG.md
- [ ] Link docs in `/docs/README.md`
- [ ] Add curl examples for pre-integration verification

---

## Timeline

- **Phase 1 (Config)**: 30 minutes
- **Phase 2 (Implementation)**: 2-3 hours
- **Phase 3 (Testing)**: 1-2 hours
- **Phase 4 (Documentation)**: 1 hour

**Total**: 4-6 hours

---

## Next Steps

1. ✅ Create feature branch `feat/bayesian-engine-endpoints`
2. ✅ Create gap analysis document
3. ✅ Create implementation plan document
4. ⬜ Start Phase 1: Configuration updates
5. ⬜ Continue with Phase 2-4

---

## Related Documents

- [Gap Analysis](./bayesian-engine-gap-analysis.md)
- [Requirements](../../kite-service-requirements.md)
- [API Reference](../api/api-reference.md)
