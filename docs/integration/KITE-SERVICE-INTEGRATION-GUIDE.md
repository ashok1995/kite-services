# Kite Service Integration Guide

**For Bayesian Continuous Intelligence Engine & Other Services**

Last Updated: 2026-02-13  
Version: 2.0 (Post-Yahoo Cleanup)

---

## 📌 Service Overview

The Kite service is a **standalone microservice** that wraps the Zerodha Kite Connect API for NSE/BSE market data.

### ✅ What This Service Provides (PRIMARY SOURCE)

- ✅ **Real-time stock quotes** (LTP, volume, OHLC) - up to 200 symbols per call
- ✅ **Historical candles** (5m, 15m, 1h, 1d intervals)
- ✅ **Indian market context** (Nifty 50 regime, India VIX, market breadth)
- ✅ **Market breadth** (advance/decline ratio from Nifty 50 constituents)
- ✅ **Instrument metadata** (tokens, lot sizes, tick sizes)
- ✅ **NSE/BSE sectors** performance

### ❌ What This Service Does NOT Provide

- ❌ US indices (S&P 500, Nasdaq, Dow Jones)
- ❌ Global VIX or fear/greed index
- ❌ Commodities (crude oil, gold)
- ❌ Forex rates (USD/INR)
- ❌ Global market sentiment

**👉 Use your separate Yahoo Finance service for global market data**

---

## 🚀 Quick Start

### Development Port Configuration

```bash
# Service runs on port 8079 (development)
ENVIRONMENT=development
SERVICE_PORT=8079
SERVICE_URL=http://localhost:8079
```

### Starting the Service

```bash
cd /Users/ashokkumar/Desktop/ashok-personal/stocks/kite-services

# Activate virtual environment
source venv/bin/activate

# Start server
python src/main.py
```

Server starts on: **`http://localhost:8079`**

### Health Check

```bash
curl http://localhost:8079/health | jq
```

Expected response:

```json
{
  "status": "healthy",
  "services": {
    "cache_service": "running",
    "kite_client": "running",
    "market_context_service": "running",
    "stock_data_service": "running"
  }
}
```

---

## 🔐 Authentication

### Prerequisites

1. Kite Connect API credentials (api_key, api_secret)
2. Fresh `request_token` (expires in ~2 minutes after generation)

### Authentication Flow

#### Step 1: Get Login URL

```bash
curl http://localhost:8079/api/auth/login-url | jq -r '.login_url'
```

This returns a Zerodha login URL. Open it in browser to get `request_token`.

#### Step 2: Exchange Token for Access Token

```bash
curl -X POST http://localhost:8079/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "request_token": "YOUR_REQUEST_TOKEN",
    "api_secret": "YOUR_API_SECRET"
  }' | jq
```

Response:

```json
{
  "status": "authenticated",
  "access_token": "ndobPo6XAns9QicMA4zsSS5wr7RgCG4b",
  "user_id": "YF0364",
  "user_name": "Ashok Kumar",
  "broker": "ZERODHA",
  "message": "Authentication successful"
}
```

#### Step 3: Verify Authentication

```bash
curl http://localhost:8079/api/auth/status | jq
```

---

## 📊 Core Endpoints for Bayesian Engine

### 1. Batch Quotes (CRITICAL)

**Fetch real-time quotes for up to 200 symbols**

```bash
POST /api/market/quotes
Content-Type: application/json

{
  "symbols": ["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK"],
  "exchange": "NSE"
}
```

**Response:**

```json
{
  "timestamp": "2026-02-13T15:21:49.582104",
  "stocks": [
    {
      "symbol": "RELIANCE",
      "exchange": "NSE",
      "last_price": "1420.3",
      "open_price": "1445.5",
      "high_price": "1450.7",
      "low_price": "1416.3",
      "close_price": "1448.9",
      "change_percent": "-2.06",
      "volume": 9798115,
      "average_price": "1424.21",
      "timestamp": "2026-02-13 15:11:25"
    }
  ],
  "total_symbols": 5,
  "successful_symbols": 5,
  "processing_time_ms": 62
}
```

**Important:**

- ✅ Max 200 symbols per request
- ✅ Call frequency: Every 1 minute during market hours
- ✅ Timeout: 5 seconds
- ✅ Returns empty array if market closed (no error)

**cURL Example:**

```bash
curl -X POST http://localhost:8079/api/market/quotes \
  -H "Content-Type: application/json" \
  -d '{
    "symbols": ["RELIANCE", "TCS", "INFY"],
    "exchange": "NSE"
  }' | jq
```

---

### 2. Market Context (CRITICAL)

**Get market regime, VIX, breadth for Bayesian scoring**

```bash
POST /api/analysis/context
Content-Type: application/json

{
  "include_global": false,
  "include_indian": true,
  "include_sector": true
}
```

**Response:**

```json
{
  "success": true,
  "indian_markets": [
    {
      "market": "India",
      "index": "NSE:NIFTY 50",
      "last_price": 22150.50,
      "change_percent": -0.82
    },
    {
      "market": "India",
      "index": "NSE:NIFTY BANK",
      "last_price": 48320.15,
      "change_percent": -1.15
    }
  ],
  "timestamp": "2026-02-13T15:21:49.582104"
}
```

**cURL Example:**

```bash
curl -X POST http://localhost:8079/api/analysis/context \
  -H "Content-Type: application/json" \
  -d '{"include_global": false, "include_indian": true}' | jq
```

**Note:** Currently returns limited data. Use quick-context endpoint for full breadth data.

---

### 3. Quick Market Context (WITH BREADTH)

**Fast endpoint with market breadth from Nifty 50 constituents**

```bash
GET /api/market-context-data/quick-context?include_global=false&include_sector=true
```

**Expected Fields (when working):**

```json
{
  "market_regime": "bearish",
  "india_vix": 18.5,
  "nifty_50": {
    "value": 22150.50,
    "change_percent": -0.82
  },
  "market_breadth": {
    "advances": 7,
    "declines": 42,
    "unchanged": 1,
    "advance_decline_ratio": 0.17
  },
  "sectors": {
    "IT": 0.5,
    "Banking": -1.2,
    "Auto": 0.8
  }
}
```

---

### 4. Historical Candles

**Get OHLCV data for technical analysis**

```bash
GET /api/market/historical/{symbol}?interval=5minute&from_date=2026-02-10&to_date=2026-02-13
```

**Response:**

```json
{
  "symbol": "RELIANCE",
  "interval": "5minute",
  "candles": [
    {
      "timestamp": "2026-02-13T09:15:00",
      "open": 1445.0,
      "high": 1448.5,
      "low": 1442.0,
      "close": 1446.5,
      "volume": 125000
    }
  ]
}
```

**Supported Intervals:**

- `minute` - 1 minute
- `5minute` - 5 minutes
- `15minute` - 15 minutes
- `hour` - 1 hour
- `day` - 1 day

---

### 5. Instrument Metadata

**Get instrument tokens, lot sizes, tick sizes**

```bash
GET /api/market/instruments?exchange=NSE&segment=EQUITY
```

**Response:**

```json
{
  "instruments": [
    {
      "instrument_token": 738561,
      "exchange_token": 2884,
      "tradingsymbol": "RELIANCE",
      "name": "RELIANCE INDUSTRIES LTD",
      "last_price": 1420.30,
      "expiry": null,
      "strike": null,
      "tick_size": 0.05,
      "lot_size": 1,
      "instrument_type": "EQ",
      "segment": "NSE",
      "exchange": "NSE"
    }
  ]
}
```

---

## 🔄 Integration Patterns

### Pattern 1: Stock Pool Updates (Every 1 minute)

```python
import httpx

async def update_stock_pool():
    """Update prices for all stocks in pool."""
    symbols = get_active_symbols()  # Your function

    # Batch symbols (max 200 per call)
    batches = [symbols[i:i+200] for i in range(0, len(symbols), 200)]

    for batch in batches:
        response = await httpx.post(
            "http://localhost:8079/api/market/quotes",
            json={"symbols": batch, "exchange": "NSE"},
            timeout=5.0
        )

        if response.status_code == 200:
            data = response.json()
            for stock in data["stocks"]:
                update_database(stock)  # Your function
```

### Pattern 2: Market Context for Bayesian Scoring

```python
async def get_market_context_for_scoring():
    """Get market context for Bayesian engine."""
    response = await httpx.post(
        "http://localhost:8079/api/analysis/context",
        json={
            "include_global": False,  # Use your Yahoo service for global
            "include_indian": True,
            "include_sector": True
        },
        timeout=3.0
    )

    if response.status_code == 200:
        context = response.json()
        return {
            "market_regime": extract_regime(context),
            "vix": extract_vix(context),
            # Get breadth from your calculations or separate endpoint
        }
```

### Pattern 3: Historical Data for Technical Indicators

```python
async def get_historical_for_indicators(symbol: str):
    """Get 5-minute candles for last 3 days."""
    from datetime import datetime, timedelta

    to_date = datetime.now()
    from_date = to_date - timedelta(days=3)

    response = await httpx.get(
        f"http://localhost:8079/api/market/historical/{symbol}",
        params={
            "interval": "5minute",
            "from_date": from_date.strftime("%Y-%m-%d"),
            "to_date": to_date.strftime("%Y-%m-%d")
        },
        timeout=10.0
    )

    if response.status_code == 200:
        data = response.json()
        return data["candles"]
```

---

## ⚠️ Known Issues & Limitations

### 🔴 Issue 1: Market Breadth Not Fully Exposed

**Status:** Market breadth is calculated internally but not exposed via `/api/analysis/context`

**Workaround:**

1. Use `/api/market-context-data/quick-context` endpoint (needs verification)
2. Or calculate breadth yourself:

   ```python
   # Fetch Nifty 50 constituents
   nifty_50 = ["RELIANCE", "TCS", "INFY", ...]  # 50 symbols

   response = await httpx.post(
       "http://localhost:8079/api/market/quotes",
       json={"symbols": nifty_50, "exchange": "NSE"}
   )

   # Calculate breadth
   advances = sum(1 for s in stocks if s["change_percent"] > 0.01)
   declines = sum(1 for s in stocks if s["change_percent"] < -0.01)
   ad_ratio = advances / declines if declines > 0 else advances
   ```

**Fix Required:** Expose breadth data in `/api/analysis/context` response

---

### 🟡 Issue 2: Global Market Data Removed

**Status:** All Yahoo Finance dependencies removed

**Impact:** No US indices, global VIX, commodities, forex

**Solution:** Use your separate Yahoo Finance service for:

- S&P 500, Nasdaq, Dow Jones
- Global VIX
- Crude oil, gold
- USD/INR

---

### 🟢 Issue 3: Some Endpoints Disabled

**Disabled Endpoints (Yahoo-dependent):**

- `/api/analysis/intelligence` - Stock intelligence
- `/api/analysis/stock` - Stock analysis
- `/api/analysis/context/enhanced` - Enhanced context
- All `/api/market-context/*` routes

**Working Endpoints:**

- ✅ `/api/market/quotes` - Batch quotes
- ✅ `/api/market/historical/{symbol}` - Historical data
- ✅ `/api/market/instruments` - Instruments
- ✅ `/api/analysis/context` - Basic market context
- ✅ `/api/auth/*` - Authentication

---

## 📝 Environment Variables

### Required in `envs/development.env`

```bash
# Service Config
ENVIRONMENT=development
SERVICE_PORT=8079
SERVICE_NAME="Kite Services"

# Kite Connect
KITE_TOKEN_FILE=~/.kite-services/kite_token.json

# Batch Quotes (Bayesian requirement)
QUOTES_MAX_SYMBOLS=200

# Market Breadth
MARKET_BREADTH_ENABLED=true
MARKET_BREADTH_CACHE_TTL=60

# Redis Cache (optional)
REDIS_HOST=localhost
REDIS_PORT=6379
```

---

## 🧪 Testing Checklist

Before integrating, verify:

```bash
# 1. Health check
curl http://localhost:8079/health | jq '.status'

# 2. Authentication working
curl http://localhost:8079/api/auth/status | jq '.authenticated'

# 3. Batch quotes (5 symbols)
curl -X POST http://localhost:8079/api/market/quotes \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK"], "exchange": "NSE"}' \
  | jq '.successful_symbols'

# 4. Batch quotes (50 symbols - stress test)
# [Use your Nifty 50 list]

# 5. Historical data
curl "http://localhost:8079/api/market/historical/RELIANCE?interval=5minute&from_date=2026-02-10&to_date=2026-02-13" | jq '.candles | length'

# 6. Instruments
curl "http://localhost:8079/api/market/instruments?exchange=NSE&segment=EQUITY" | jq '.instruments | length'
```

---

## 🚨 Important Notes

### Rate Limits

- **Kite Connect API:** 3 requests/second, 3000 requests/day per token
- **Recommended:** Batch all symbol fetches, use caching
- **Cache TTL:** Market breadth cached for 60 seconds

### Market Hours

- **Pre-market:** 09:00 - 09:15 IST (limited data)
- **Regular:** 09:15 - 15:30 IST (full data)
- **Post-market:** 15:30 - 16:00 IST (limited data)
- **Closed:** Returns last known prices (no error)

### Symbol Format

- Use raw symbols: `"RELIANCE"`, `"TCS"`, `"INFY"`
- Service adds `NSE:` prefix internally
- For indices: Use `"NIFTY 50"`, `"NIFTY BANK"`
- For VIX: Use `"INDIA VIX"`

### Error Handling

```python
try:
    response = await httpx.post(url, json=payload, timeout=5.0)
    response.raise_for_status()
    data = response.json()

    if data.get("successful_symbols", 0) < len(symbols):
        # Some symbols failed
        failed = data.get("failed_symbols", [])
        log_warning(f"Failed symbols: {failed}")

except httpx.TimeoutException:
    # Retry with exponential backoff
    pass
except httpx.HTTPStatusError as e:
    # Handle 429 (rate limit), 503 (service down)
    pass
```

---

## 📞 Support & Issues

### Common Issues

1. **"Token is invalid or has expired"**
   - Solution: Generate fresh `request_token` and re-authenticate

2. **Empty quotes array**
   - Check if market is open
   - Verify authentication: `curl http://localhost:8079/api/auth/status`

3. **"Maximum 200 symbols allowed"**
   - Batch your requests into chunks of 200

4. **Market breadth not in response**
   - Known issue - use workaround above or wait for fix

### Getting Fresh Request Token

```bash
# 1. Get login URL
curl http://localhost:8079/api/auth/login-url | jq -r '.login_url'

# 2. Open URL in browser, login, get request_token from redirect

# 3. Authenticate
curl -X POST http://localhost:8079/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "request_token": "FRESH_TOKEN",
    "api_secret": "YOUR_SECRET"
  }'
```

---

## ✅ Ready for Integration

Your Kite service is now:

- ✅ Running on port 8079 (development)
- ✅ Yahoo-free (use your Yahoo service for global data)
- ✅ Optimized for NSE/BSE data only
- ✅ Supporting batch quotes (200 symbols)
- ✅ Calculating market breadth (Nifty 50)
- ✅ Providing historical candles
- ✅ Exposing instrument metadata

**Next Steps:**

1. Integrate batch quotes into your stock pool updates
2. Use separate Yahoo service for global market context
3. Test with your Bayesian engine
4. Monitor rate limits and caching

---

**Questions or Issues?** Document them here and we'll address them! 🚀
