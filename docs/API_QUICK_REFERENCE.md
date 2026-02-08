# Kite Services - API Quick Reference

**Version:** 2.0  
**Base URL:** `http://127.0.0.1:8079`  
**Total Endpoints:** 11 (9 API + 2 utility)

---

## 🔐 Authentication (2 endpoints)

### 1. POST `/api/auth/login`
Complete authentication flow with Kite Connect.

**Request:**
```json
{
  "request_token": "your_request_token_here"
}
```

**Response:**
```json
{
  "success": true,
  "access_token": "xxxx",
  "user_id": "XX1234",
  "message": "Authentication successful"
}
```

**cURL:**
```bash
curl -X POST http://127.0.0.1:8079/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"request_token": "your_token"}'
```

---

### 2. GET `/api/auth/status`
Check current authentication status.

**Response:**
```json
{
  "status": "valid",
  "authenticated": true,
  "user_id": "XX1234",
  "user_name": "John Doe",
  "broker": "Zerodha",
  "last_updated": "2025-10-13T10:30:00",
  "token_expiry": "2025-10-13T23:59:59"
}
```

**cURL:**
```bash
curl http://127.0.0.1:8079/api/auth/status
```

---

## 📊 Market Data (3 endpoints)

### 3. POST `/api/market/data`
Universal market data endpoint - quotes, historical, fundamentals.

**Request (Quote Data):**
```json
{
  "symbols": ["RELIANCE", "TCS"],
  "exchange": "NSE",
  "data_type": "quote"
}
```

**Request (Historical Data):**
```json
{
  "symbols": ["NIFTY"],
  "exchange": "NSE",
  "data_type": "historical",
  "interval": "day",
  "from_date": "2025-10-01",
  "to_date": "2025-10-13"
}
```

**Response:**
```json
{
  "success": true,
  "data": [...],
  "count": 2,
  "processing_time_ms": 125.5
}
```

**cURL:**
```bash
curl -X POST http://127.0.0.1:8079/api/market/data \
  -H "Content-Type: application/json" \
  -d '{
    "symbols": ["RELIANCE"],
    "exchange": "NSE",
    "data_type": "quote"
  }'
```

---

### 4. GET `/api/market/status`
Current market status and trading hours.

**Response:**
```json
{
  "success": true,
  "market_open": true,
  "current_time": "2025-10-13T14:30:00",
  "exchange_status": {
    "NSE": "open",
    "BSE": "open"
  },
  "next_close": "2025-10-13T15:30:00"
}
```

**cURL:**
```bash
curl http://127.0.0.1:8079/api/market/status
```

---

### 5. GET `/api/market/instruments`
Available instruments and exchanges.

**Response:**
```json
{
  "success": true,
  "exchanges": ["NSE", "BSE", "NFO"],
  "instrument_count": 5000,
  "popular_symbols": ["RELIANCE", "TCS", "INFY", "HDFCBANK"]
}
```

**cURL:**
```bash
curl http://127.0.0.1:8079/api/market/instruments
```

---

## 🧠 Analysis (3 endpoints)

### 6. POST `/api/analysis/context`
Complete market context analysis (legacy, comprehensive).

**Request:**
```json
{
  "symbols": ["NIFTY"],
  "include_global": true,
  "include_indian": true,
  "include_sentiment": true
}
```

**Response:**
```json
{
  "success": true,
  "global_context": {...},
  "indian_context": {...},
  "sentiment": {...},
  "processing_time_ms": 450.2
}
```

**cURL:**
```bash
curl -X POST http://127.0.0.1:8079/api/analysis/context \
  -H "Content-Type: application/json" \
  -d '{
    "symbols": ["NIFTY"],
    "include_global": true
  }'
```

---

### 7. POST `/api/analysis/context/enhanced` ⭐ NEW
**Enhanced hierarchical market context for trading recommendation systems.**

**Key Features:**
- **Primary Context:** Quick overview (<100ms)
- **Detailed Context:** Granular analysis (<500ms)
- **Style-Specific:** Optimized for intraday/swing/long-term (<1s)

**Request (All Contexts):**
```json
{
  "include_primary": true,
  "include_detailed": true,
  "include_style_specific": true,
  "trading_styles": ["intraday", "swing"],
  "include_sectors": true,
  "include_technicals": true,
  "include_opportunities": true
}
```

**Request (Fast, Primary Only):**
```json
{
  "include_primary": true,
  "include_detailed": false,
  "include_style_specific": false
}
```

**Response:**
```json
{
  "success": true,
  "primary_context": {
    "overall_market_score": 45,        // -100 to +100
    "market_confidence": 0.85,
    "favorable_for": ["swing", "long_term"],
    "global_context": {
      "overall_trend": "bullish",
      "volatility_level": "normal"
    },
    "indian_context": {
      "nifty_change": "0.8",
      "market_regime": "bull_weak"
    }
  },
  "detailed_context": {
    "nifty_analysis": {
      "technicals": {
        "rsi_14": "58.5",
        "macd_signal": "bullish_crossover"
      },
      "support": ["19500", "19450"],
      "resistance": ["19700", "19750"]
    },
    "sectors": [
      {
        "sector_name": "IT",
        "strength_score": 75,
        "momentum": "accelerating"
      }
    ]
  },
  "intraday_context": {
    "market_phase": "Mid-session",
    "current_momentum": "bullish",
    "pivot_point": "19600",
    "breakout_candidates": ["RELIANCE", "TCS"]
  },
  "swing_context": {
    "multi_day_trend": "uptrend",
    "hot_sectors": ["IT", "Pharma"],
    "oversold_stocks": ["AXISBANK"]
  },
  "context_quality_score": 0.9,
  "processing_time_ms": 850.5
}
```

**cURL (All Contexts):**
```bash
curl -X POST http://127.0.0.1:8079/api/analysis/context/enhanced \
  -H "Content-Type: application/json" \
  -d '{
    "include_primary": true,
    "include_detailed": true,
    "include_style_specific": true,
    "trading_styles": ["intraday"],
    "include_sectors": true,
    "include_technicals": true
  }'
```

**cURL (Fast Primary Only):**
```bash
curl -X POST http://127.0.0.1:8079/api/analysis/context/enhanced \
  -H "Content-Type: application/json" \
  -d '{
    "include_primary": true,
    "include_detailed": false,
    "include_style_specific": false
  }'
```

**Use Cases:**
- Real-time trading recommendation systems
- ML feature engineering for trading models
- Multi-timeframe market analysis
- Risk assessment and position sizing
- Sector rotation strategies

📚 **[Full Documentation](./ENHANCED_MARKET_CONTEXT.md)**

---

### 8. POST `/api/analysis/intelligence`
Stock-specific intelligence and recommendations.

**Request:**
```json
{
  "symbol": "RELIANCE",
  "exchange": "NSE",
  "include_technicals": true,
  "include_fundamentals": true
}
```

**Response:**
```json
{
  "success": true,
  "symbol": "RELIANCE",
  "recommendation": "BUY",
  "confidence": 0.82,
  "technicals": {...},
  "fundamentals": {...},
  "risk_score": 3.5
}
```

**cURL:**
```bash
curl -X POST http://127.0.0.1:8079/api/analysis/intelligence \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "RELIANCE",
    "exchange": "NSE",
    "include_technicals": true
  }'
```

---

## 💼 Trading (1 endpoint)

### 9. GET `/api/trading/status`
Portfolio and positions status.

**Response:**
```json
{
  "success": true,
  "portfolio_value": "1500000.00",
  "day_pnl": "5000.00",
  "positions": [
    {
      "symbol": "RELIANCE",
      "quantity": 100,
      "pnl": "2500.00"
    }
  ],
  "holdings": [...]
}
```

**cURL:**
```bash
curl http://127.0.0.1:8079/api/trading/status
```

---

## 🛠️ Utility Endpoints (2)

### 10. GET `/health`
Service health check.

**Response:**
```json
{
  "status": "healthy",
  "service": "kite-services",
  "version": "1.0.0",
  "environment": "development",
  "services": {
    "kite_client": {"status": "running"},
    "yahoo_service": {"status": "running"},
    "market_context_service": {"status": "running"}
  }
}
```

**cURL:**
```bash
curl http://127.0.0.1:8079/health
```

---

### 11. GET `/`
Service information and available endpoints.

**Response:**
```json
{
  "service": "kite-services",
  "version": "1.0.0",
  "environment": "development",
  "docs_url": "/docs",
  "health_url": "/health",
  "api_prefix": "/api"
}
```

**cURL:**
```bash
curl http://127.0.0.1:8079/
```

---

## 📚 Interactive Documentation

### Swagger UI
Open in browser: **http://127.0.0.1:8079/docs**

### ReDoc
Open in browser: **http://127.0.0.1:8079/redoc**

---

## 🚀 Common Workflows

### Workflow 1: Morning Market Check (Fast)
```bash
# 1. Check auth status
curl http://127.0.0.1:8079/api/auth/status

# 2. Get quick market overview (primary context only)
curl -X POST http://127.0.0.1:8079/api/analysis/context/enhanced \
  -H "Content-Type: application/json" \
  -d '{"include_primary": true, "include_detailed": false, "include_style_specific": false}'

# 3. Check market status
curl http://127.0.0.1:8079/api/market/status
```

**Total Time:** <200ms

---

### Workflow 2: Intraday Trading Setup
```bash
# 1. Get intraday-optimized market context
curl -X POST http://127.0.0.1:8079/api/analysis/context/enhanced \
  -H "Content-Type: application/json" \
  -d '{
    "include_primary": true,
    "include_detailed": true,
    "include_style_specific": true,
    "trading_styles": ["intraday"],
    "include_sectors": true,
    "include_technicals": true,
    "include_opportunities": true
  }'

# 2. Get current positions
curl http://127.0.0.1:8079/api/trading/status

# 3. Get quotes for watchlist
curl -X POST http://127.0.0.1:8079/api/market/data \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["RELIANCE", "TCS"], "exchange": "NSE", "data_type": "quote"}'
```

**Total Time:** <2s

---

### Workflow 3: Swing Trading Analysis
```bash
# 1. Get swing-optimized context with sector rotation
curl -X POST http://127.0.0.1:8079/api/analysis/context/enhanced \
  -H "Content-Type: application/json" \
  -d '{
    "trading_styles": ["swing"],
    "include_primary": true,
    "include_detailed": true,
    "include_style_specific": true,
    "include_sectors": true,
    "include_opportunities": true
  }'

# 2. Get intelligence for specific stock
curl -X POST http://127.0.0.1:8079/api/analysis/intelligence \
  -H "Content-Type: application/json" \
  -d '{"symbol": "RELIANCE", "exchange": "NSE", "include_technicals": true}'
```

**Total Time:** <2s

---

## 🔑 Response Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | Success | Request processed successfully |
| 400 | Bad Request | Invalid request parameters |
| 401 | Unauthorized | Authentication required or invalid |
| 404 | Not Found | Endpoint or resource not found |
| 500 | Server Error | Internal server error |
| 503 | Service Unavailable | Service temporarily unavailable |

---

## 📊 Performance Benchmarks

| Endpoint | Avg Response Time | Max Response Time | Use Case |
|----------|-------------------|-------------------|----------|
| `/api/auth/status` | <50ms | <100ms | Authentication check |
| `/api/market/status` | <30ms | <80ms | Market status |
| `/api/market/data` (quotes) | <150ms | <300ms | Real-time quotes |
| `/api/analysis/context/enhanced` (primary only) | <100ms | <200ms | Quick sentiment |
| `/api/analysis/context/enhanced` (all) | <1s | <2s | Full analysis |
| `/api/trading/status` | <200ms | <400ms | Portfolio check |

---

## 🎯 Best Practices

1. **Use Enhanced Context for ML:** The `/api/analysis/context/enhanced` endpoint is specifically designed for ML feature engineering

2. **Cache Appropriately:**
   - Primary context: 30-60 seconds
   - Detailed context: 2-5 minutes
   - Long-term context: 15-30 minutes

3. **Parallel Requests:** Fetch market context and stock data in parallel for better performance

4. **Error Handling:** Always check `success` field and handle warnings

5. **Rate Limiting:** Respect Kite Connect rate limits (3 requests/second)

---

## 📚 Documentation Links

- [Enhanced Market Context Guide](./ENHANCED_MARKET_CONTEXT.md) ⭐
- [API Consolidation Summary](./API_CONSOLIDATION_COMPLETE.md)
- [Unified API Guide](./UNIFIED_API_GUIDE.md)
- [ML Market Intelligence](./V3_ML_MARKET_INTELLIGENCE_API_GUIDE.md)
- [Project Summary](./PROJECT_SUMMARY.md)

---

**Last Updated:** October 13, 2025  
**API Version:** 2.0  
**Total Endpoints:** 11 (9 API + 2 utility)

