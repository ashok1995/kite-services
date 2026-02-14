# Bayesian Engine Integration Guide

**Service**: Kite Services v1.1.0  
**Port**: 8179 (Production) | 8079 (Development)  
**Date**: 2026-02-13  
**Status**: ✅ Ready for Integration

---

## Quick Start

### Prerequisites

1. Kite Services running on port 8179 (production) or 8079 (development)
2. Valid Kite Connect authentication (handled by service)
3. Network access to service endpoint

### Base URLs

- **Production**: `http://localhost:8179`
- **Development**: `http://localhost:8079`
- **Staging**: `http://localhost:8279` (local only)

---

## Available Endpoints

### 1. Batch Quotes (Real-time Prices)

**Purpose**: Fetch real-time prices for up to 200 symbols in one call

**Endpoint**: `POST /api/market/quotes`

**Request**:

```json
{
  "symbols": ["RELIANCE", "TCS", "INFY", ... up to 200],
  "exchange": "NSE"
}
```

**Response**:

```json
{
  "success": true,
  "timestamp": "2026-02-13T14:30:05+05:30",
  "request_id": "quotes_1707820805",
  "stocks": [
    {
      "symbol": "RELIANCE",
      "exchange": "NSE",
      "last_price": 2456.75,
      "open_price": 2440.00,
      "high_price": 2460.00,
      "low_price": 2435.00,
      "close_price": 2430.00,
      "change": 26.75,
      "change_percent": 1.10,
      "volume": 1500000,
      "average_price": 2445.50,
      "timestamp": "2026-02-13T14:30:00+05:30"
    }
  ],
  "total_symbols": 200,
  "successful_symbols": 195,
  "failed_symbols": ["SYM1", "SYM2"],
  "processing_time_ms": 2500,
  "data_source": "kite_connect"
}
```

**Usage Recommendations**:

- **Frequency**: Every 1 minute during market hours
- **Max Symbols**: 200 per request
- **Timeout**: 5 seconds
- **Error Handling**: Check `successful_symbols` vs `total_symbols`

**Python Example**:

```python
import httpx
from typing import List

async def fetch_batch_quotes(symbols: List[str]) -> dict:
    """Fetch batch quotes from kite-services."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8179/api/market/quotes",
            json={"symbols": symbols, "exchange": "NSE"},
            timeout=5.0
        )
        return response.json()

# Usage
symbols = ["RELIANCE", "TCS", "INFY", ...]  # Up to 200
quotes = await fetch_batch_quotes(symbols)
print(f"Fetched {quotes['successful_symbols']} of {quotes['total_symbols']} symbols")
```

**cURL Example**:

```bash
curl -X POST http://localhost:8179/api/market/quotes \
  -H "Content-Type: application/json" \
  -d '{
    "symbols": ["RELIANCE", "TCS", "INFY"],
    "exchange": "NSE"
  }'
```

---

### 2. Market Context (Market Breadth & Regime)

**Purpose**: Get market regime, VIX, breadth data, and sector performance

**Endpoint**: `POST /api/analysis/context`

**Request**:

```json
{
  "include_global_data": true,
  "include_sector_data": true,
  "include_institutional_data": true
}
```

**Response**:

```json
{
  "market_context": {
    "timestamp": "2026-02-13T14:30:00+05:30",
    "request_id": "context_1707820800",

    "indian_data": {
      "timestamp": "2026-02-13T14:30:00+05:30",
      "indices": {
        "NSE:NIFTY 50": {
          "value": 21450.50,
          "change_percent": 0.75
        },
        "NSE:NIFTY BANK": {
          "value": 45720.30,
          "change_percent": 0.52
        }
      },
      "market_regime": "bullish",
      "volatility_level": "low",

      "advances": 35,
      "declines": 15,
      "unchanged": 0,
      "advance_decline_ratio": "2.33",

      "new_highs": 0,
      "new_lows": 0,
      "total_volume": null,
      "volume_trend": "stable"
    },

    "volatility_data": {
      "india_vix": 12.45,
      "vix_change": -0.50,
      "vix_trend": "decreasing",
      "volatility_level": "low",
      "fear_greed_index": 65
    },

    "sector_data": {
      "sectors": {
        "IT": {"change_percent": 1.2, "is_leader": true},
        "BANK": {"change_percent": 0.8, "is_leader": false},
        "AUTO": {"change_percent": -0.3, "is_leader": false}
      },
      "leading_sectors": ["IT", "PHARMA"],
      "lagging_sectors": ["AUTO", "METAL"]
    }
  },
  "processing_time_ms": 850
}
```

**Key Fields for Bayesian Engine**:

| Field | Description | Priority |
|-------|-------------|----------|
| `market_regime` | Bullish/bearish/neutral/sideways | MUST |
| `india_vix` | India VIX level | MUST |
| `volatility_level` | Low/normal/elevated/high | MUST |
| `advances` | Number of advancing stocks (Nifty 50) | MUST |
| `declines` | Number of declining stocks (Nifty 50) | MUST |
| `advance_decline_ratio` | Breadth ratio | MUST |
| `indices` | Nifty 50, Bank Nifty levels | SHOULD |
| `sectors` | Sector-wise performance | SHOULD |

**Usage Recommendations**:

- **Frequency**: Every 5 minutes during market hours
- **Timeout**: 10 seconds
- **Caching**: Breadth data is cached for 60 seconds internally

**Python Example**:

```python
async def fetch_market_context() -> dict:
    """Fetch market context from kite-services."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8179/api/analysis/context",
            json={
                "include_global_data": true,
                "include_sector_data": true
            },
            timeout=10.0
        )
        return response.json()

# Usage
context = await fetch_market_context()
breadth = context['market_context']['indian_data']
print(f"Advances: {breadth['advances']}, Declines: {breadth['declines']}")
print(f"AD Ratio: {breadth['advance_decline_ratio']}")
print(f"Market Regime: {breadth['market_regime']}")
```

**cURL Example**:

```bash
curl -X POST http://localhost:8179/api/analysis/context \
  -H "Content-Type: application/json" \
  -d '{
    "include_global_data": true,
    "include_sector_data": true
  }' | jq '.market_context.indian_data'
```

---

### 3. Historical Candles (OHLCV Data)

**Purpose**: Fetch historical OHLCV candles for return calculation

**Endpoint**: `POST /api/market/data`

**Request**:

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

**Supported Intervals**:

- `minute` - 1 minute
- `5minute` - 5 minutes ✅ (Bayesian requirement)
- `15minute` - 15 minutes ✅ (Bayesian requirement)
- `30minute` - 30 minutes
- `hour` - 1 hour
- `day` - Daily

**Response**:

```json
{
  "success": true,
  "data": {
    "RELIANCE": {
      "symbol": "RELIANCE",
      "close": 2443.25,
      "timestamp": "2026-02-12T15:30:00+05:30"
    }
  },
  "total_symbols": 1,
  "successful_symbols": 1
}
```

**Usage Recommendations**:

- **Frequency**: Every 10 minutes (only for tracked symbols)
- **Symbols**: 10-50 per call
- **Timeout**: 10 seconds

**Python Example**:

```python
from datetime import date

async def fetch_historical_candles(
    symbol: str,
    interval: str = "5minute",
    date_: date = None
) -> dict:
    """Fetch historical candles for return calculation."""
    date_str = (date_ or date.today()).isoformat()

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8179/api/market/data",
            json={
                "symbols": [symbol],
                "exchange": "NSE",
                "data_type": "historical",
                "from_date": date_str,
                "to_date": date_str,
                "interval": interval
            },
            timeout=10.0
        )
        return response.json()

# Usage
candles = await fetch_historical_candles("RELIANCE", "5minute")
```

---

### 4. Instruments (Symbol → Token Mapping)

**Purpose**: Get instrument tokens and metadata for symbols

**Endpoint**: `GET /api/market/instruments`

**Request**:

```bash
GET /api/market/instruments?exchange=NSE&instrument_type=EQ&limit=1000
```

**Response**:

```json
{
  "success": true,
  "instruments": [
    {
      "instrument_token": 738561,
      "tradingsymbol": "RELIANCE",
      "exchange": "NSE",
      "name": "Reliance Industries",
      "lot_size": 1,
      "tick_size": "0.05",
      "instrument_type": "EQ",
      "segment": "NSE"
    }
  ],
  "total_count": 1000,
  "exchanges": ["NSE"]
}
```

**Usage Recommendations**:

- **Frequency**: Once at startup (cache for 24 hours)
- **Timeout**: 30 seconds

**Python Example**:

```python
async def fetch_instruments(exchange: str = "NSE") -> dict:
    """Fetch all instruments for exchange."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"http://localhost:8179/api/market/instruments",
            params={"exchange": exchange, "instrument_type": "EQ", "limit": 5000},
            timeout=30.0
        )
        return response.json()

# Usage - cache this for 24 hours
instruments = await fetch_instruments("NSE")
token_map = {
    inst['tradingsymbol']: inst['instrument_token']
    for inst in instruments['instruments']
}
```

---

## Integration Workflow

### Bayesian Engine Data Flow

```
1. Startup:
   └─> Fetch instruments (cache for 24h)

2. Every 1 minute (during market hours):
   └─> Fetch batch quotes (100-200 symbols)
       └─> Update stock_pool prices
       └─> Update price_snapshots table

3. Every 5 minutes:
   └─> Fetch market context
       └─> Extract market regime
       └─> Extract VIX level
       └─> Extract breadth data (advances/declines/ratio)
       └─> Extract sector performance
       └─> Update bayesian context features

4. Every 10 minutes (for tracked recommendations):
   └─> Fetch historical candles (5m or 15m)
       └─> Calculate returns for performance tracking
```

---

## Sample Integration Code

### Complete Integration Module

```python
"""
Kite Services Integration Module for Bayesian Engine
"""

import asyncio
import httpx
from datetime import datetime, date
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class KiteServicesClient:
    """Client for Kite Services API integration."""

    def __init__(self, base_url: str = "http://localhost:8179"):
        self.base_url = base_url
        self.timeout = httpx.Timeout(10.0)
        self._instruments_cache = None
        self._cache_timestamp = None

    async def health_check(self) -> bool:
        """Check if kite-services is accessible."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/health",
                    timeout=5.0
                )
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

    async def fetch_batch_quotes(
        self,
        symbols: List[str],
        exchange: str = "NSE"
    ) -> Dict:
        """Fetch batch quotes for up to 200 symbols."""
        if len(symbols) > 200:
            raise ValueError(f"Maximum 200 symbols allowed, got {len(symbols)}")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/market/quotes",
                json={"symbols": symbols, "exchange": exchange},
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()

    async def fetch_market_context(self) -> Dict:
        """Fetch market context with breadth data."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/analysis/context",
                json={
                    "include_global_data": True,
                    "include_sector_data": True
                },
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()

    async def fetch_historical_candles(
        self,
        symbol: str,
        interval: str = "5minute",
        from_date: Optional[date] = None,
        to_date: Optional[date] = None
    ) -> Dict:
        """Fetch historical OHLCV candles."""
        from_date = from_date or date.today()
        to_date = to_date or date.today()

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/market/data",
                json={
                    "symbols": [symbol],
                    "exchange": "NSE",
                    "data_type": "historical",
                    "from_date": from_date.isoformat(),
                    "to_date": to_date.isoformat(),
                    "interval": interval
                },
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()

    async def fetch_instruments(
        self,
        exchange: str = "NSE",
        use_cache: bool = True
    ) -> Dict:
        """Fetch instruments (cached for 24h by default)."""
        # Check cache
        if use_cache and self._instruments_cache:
            age = (datetime.now() - self._cache_timestamp).total_seconds()
            if age < 86400:  # 24 hours
                return self._instruments_cache

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/market/instruments",
                params={"exchange": exchange, "instrument_type": "EQ", "limit": 5000},
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()

            # Cache it
            self._instruments_cache = data
            self._cache_timestamp = datetime.now()

            return data


# Usage Example
async def main():
    """Example usage of Kite Services client."""
    client = KiteServicesClient("http://localhost:8179")

    # 1. Health check
    if not await client.health_check():
        logger.error("Kite services not available")
        return

    # 2. Fetch batch quotes
    symbols = ["RELIANCE", "TCS", "INFY", "HDFC", "ICICIBANK"]
    quotes = await client.fetch_batch_quotes(symbols)
    logger.info(f"Fetched quotes for {quotes['successful_symbols']} symbols")

    # 3. Fetch market context
    context = await client.fetch_market_context()
    breadth = context['market_context']['indian_data']
    logger.info(f"Market breadth: {breadth['advances']} up, {breadth['declines']} down")
    logger.info(f"AD Ratio: {breadth['advance_decline_ratio']}")

    # 4. Fetch historical data
    candles = await client.fetch_historical_candles("RELIANCE", "5minute")
    logger.info(f"Fetched historical data for RELIANCE")

    # 5. Fetch instruments (once at startup)
    instruments = await client.fetch_instruments("NSE")
    logger.info(f"Loaded {instruments['total_count']} instruments")


if __name__ == "__main__":
    asyncio.run(main())
```

---

## Rate Limits & Performance

### Rate Limits

- **Batch Quotes**: 100 requests/minute
- **Market Context**: 100 requests/minute
- **Historical Data**: 100 requests/minute
- **Instruments**: 10 requests/minute

### Performance Expectations

- **Batch Quotes (50 symbols)**: ~1-2s
- **Batch Quotes (200 symbols)**: ~3-5s
- **Market Context**: ~0.5-1s (cached breadth)
- **Historical Data**: ~1-3s per symbol
- **Instruments**: ~5-10s (one-time)

### Optimization Tips

1. **Batch requests**: Fetch 200 symbols at once instead of individual calls
2. **Cache instruments**: Load once at startup, refresh daily
3. **Respect cache**: Market breadth is cached for 60s, don't fetch more frequently
4. **Parallel requests**: Use asyncio to fetch quotes and context in parallel

---

## Error Handling

### Common Errors

**1. Maximum Symbols Exceeded**

```json
{
  "detail": "Maximum 200 symbols allowed. Requested: 250"
}
```

**Solution**: Split into multiple batches of 200

**2. Service Unavailable**

```json
{
  "detail": "Service manager not available"
}
```

**Solution**: Check if kite-services is running, check health endpoint

**3. Authentication Failed**

```json
{
  "detail": "Kite Connect authentication required"
}
```

**Solution**: Check Kite Connect credentials in kite-services

### Retry Strategy

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
async def fetch_with_retry(client: KiteServicesClient, symbols: List[str]):
    """Fetch quotes with automatic retry on failure."""
    return await client.fetch_batch_quotes(symbols)
```

---

## Testing

### Pre-Integration Verification

Run these commands to verify kite-services is ready:

```bash
# 1. Health check
curl -f http://localhost:8179/health

# 2. Batch quotes (50 symbols)
curl -X POST http://localhost:8179/api/market/quotes \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["RELIANCE", "TCS", ...50 symbols...], "exchange": "NSE"}' | \
  jq '.total_symbols, .successful_symbols'

# 3. Market context with breadth
curl -X POST http://localhost:8179/api/analysis/context \
  -H "Content-Type: application/json" \
  -d '{"include_global_data": true}' | \
  jq '.market_context.indian_data | {advances, declines, advance_decline_ratio}'

# Expected output:
# {
#   "advances": 35,
#   "declines": 15,
#   "advance_decline_ratio": "2.33"
# }

# 4. Historical candles
curl -X POST http://localhost:8179/api/market/data \
  -H "Content-Type: application/json" \
  -d '{
    "symbols": ["RELIANCE"],
    "exchange": "NSE",
    "data_type": "historical",
    "from_date": "2026-02-13",
    "to_date": "2026-02-13",
    "interval": "5minute"
  }' | jq '.success'

# 5. Instruments
curl "http://localhost:8179/api/market/instruments?exchange=NSE&limit=5" | \
  jq '.instruments[0] | {tradingsymbol, instrument_token}'
```

---

## Monitoring & Logging

### Health Monitoring

```python
async def monitor_health():
    """Monitor kite-services health."""
    client = KiteServicesClient()

    while True:
        healthy = await client.health_check()
        if not healthy:
            logger.error("Kite services health check failed!")
            # Alert or fallback

        await asyncio.sleep(60)  # Check every minute
```

### Performance Logging

Log response times to track performance:

```python
import time

async def fetch_with_metrics(client, symbols):
    start = time.time()
    response = await client.fetch_batch_quotes(symbols)
    duration = (time.time() - start) * 1000

    logger.info(f"Batch quotes: {len(symbols)} symbols in {duration:.0f}ms")
    return response
```

---

## Deployment Checklist

Before going live:

- [ ] Verify kite-services is running on port 8179
- [ ] Run pre-integration verification commands
- [ ] Test with production symbols list
- [ ] Verify market breadth data is real (not defaults)
- [ ] Test during market hours and off-hours
- [ ] Implement retry logic for network failures
- [ ] Set up health monitoring
- [ ] Configure rate limiting on your side
- [ ] Test with 200-symbol batches
- [ ] Verify historical data intervals (5m, 15m)

---

## Support & Troubleshooting

### Logs Location

- **Service**: `/app/logs/kite_services.log` (production)
- **Service**: `logs/kite_services.log` (development)

### Common Issues

**Issue**: Market breadth returns all zeros  
**Solution**: Check if during market hours (9:15 AM - 3:30 PM IST)

**Issue**: Batch quotes fail with 200 symbols  
**Solution**: Verify `QUOTES_MAX_SYMBOLS=200` in service config

**Issue**: Historical data returns empty  
**Solution**: Data only available during market hours for intraday intervals

### Contact

- **Documentation**: `docs/integration/`
- **API Reference**: `docs/api/api-reference.md`
- **Testing Guide**: `tests/integration/BAYESIAN_TESTING_GUIDE.md`

---

## Version History

- **v1.1.0** (2026-02-13): Added market breadth service, increased batch limit to 200
- **v1.0.0** (2026-01-15): Initial release

---

## Related Documents

- [Gap Analysis](./bayesian-engine-gap-analysis.md)
- [Implementation Plan](./bayesian-implementation-plan.md)
- [Testing Guide](../tests/integration/BAYESIAN_TESTING_GUIDE.md)
- [API Reference](../api/api-reference.md)
- [Requirements](../../kite-service-requirements.md)
