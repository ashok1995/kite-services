# Consolidated Kite Services Market API

## 🎯 **Philosophy: 4 Endpoints, Rich Information Coverage**

**From 10+ endpoints to 4 core endpoints** - Each endpoint is designed to provide comprehensive data to minimize API calls while maintaining flexibility through scope parameters.

---

## **API Endpoints Overview**

| Endpoint | Purpose | Replaces |
|----------|---------|----------|
| `GET /api/market/data` | Universal market data | 6+ individual endpoints |
| `GET /api/market/portfolio` | Portfolio/watchlist management | Watchlist + P&L endpoints |
| `GET /api/market/context` | Complete market overview | Market status + indices + sectors |
| `GET /api/market/status` | Health & simple status | Health check + market hours |

---

## **1. Universal Market Data Endpoint**

**`GET /api/market/data`** - One endpoint to rule them all!

### **Parameters**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `symbols` | string | ✅ | Comma-separated symbols (e.g., "RELIANCE,TCS,HDFC") |
| `scope` | enum | ❌ | Data richness: `basic`, `standard`, `comprehensive`, `full` |
| `historical_days` | int | ❌ | Include historical data (1-365 days) |
| `timeframe` | enum | ❌ | Historical timeframe: `daily`, `weekly`, `monthly`, `intraday` |
| `include_context` | bool | ❌ | Include market context in response |

### **Scope Levels**

| Scope | Includes |
|-------|----------|
| **basic** | Price, change, volume |
| **standard** | Basic + OHLC, market status, market cap |
| **comprehensive** | Standard + fundamentals (PE, PB), technical indicators (RSI, SMA, Bollinger) |
| **full** | Comprehensive + news sentiment, analyst ratings |

### **Example Requests**

```bash
# Basic price data
GET /api/market/data?symbols=RELIANCE,TCS&scope=basic

# Comprehensive data with 30-day history
GET /api/market/data?symbols=RELIANCE&scope=comprehensive&historical_days=30

# Full data with market context
GET /api/market/data?symbols=RELIANCE,TCS,HDFC&scope=full&include_context=true
```

### **Response Structure**

```json
{
  "request_id": "md_1642509000",
  "timestamp": "2025-01-18T10:30:00",
  "scope": "comprehensive",
  "stocks": {
    "RELIANCE": {
      "symbol": "RELIANCE",
      "name": "Reliance Industries Ltd",
      "last_price": 2450.50,
      "change": 25.30,
      "change_percent": 1.04,
      "volume": 1250000,
      "high": 2465.00,
      "low": 2420.00,
      "open": 2430.00,
      "previous_close": 2425.20,
      "market_cap": 16500000000000,
      "pe_ratio": 24.5,
      "pb_ratio": 2.8,
      "dividend_yield": 0.35,
      "rsi": 65.2,
      "sma_20": 2435.0,
      "bollinger_upper": 2483.7,
      "bollinger_lower": 2386.3,
      "timestamp": "2025-01-18T10:30:00",
      "market_status": "OPEN"
    }
  },
  "historical": {
    "RELIANCE": {
      "symbol": "RELIANCE",
      "timeframe": "daily",
      "from_date": "2024-12-18T00:00:00",
      "to_date": "2025-01-18T00:00:00",
      "candles": [...],
      "total_candles": 30,
      "price_change": 40.50,
      "price_change_percent": 1.68,
      "volume_avg": 1200000,
      "volatility": 2.5,
      "high_period": 2650.00,
      "low_period": 2100.00
    }
  },
  "market_context": { ... },
  "total_symbols": 1,
  "successful_symbols": 1,
  "failed_symbols": []
}
```

---

## **2. Portfolio/Watchlist Management**

**`GET /api/market/portfolio`** - Portfolio view with P&L and risk metrics

### **Parameters**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | string | ❌ | Portfolio name (default: "My Portfolio") |
| `symbols` | string | ✅ | Comma-separated symbols |
| `quantities` | string | ❌ | Comma-separated quantities for P&L calculation |
| `avg_prices` | string | ❌ | Comma-separated average purchase prices |
| `scope` | enum | ❌ | Data richness level |

### **Usage Modes**

1. **Watchlist Mode** (no quantities): Track multiple stocks
2. **Portfolio Mode** (with quantities): Full P&L analysis

### **Example Requests**

```bash
# Watchlist mode
GET /api/market/portfolio?name=Tech%20Watchlist&symbols=TCS,INFY,WIPRO

# Portfolio mode with P&L
GET /api/market/portfolio?name=My%20Portfolio&symbols=RELIANCE,TCS,HDFC&quantities=100,50,200&avg_prices=2400,3800,1650
```

### **Response Structure**

```json
{
  "name": "My Portfolio",
  "symbols": ["RELIANCE", "TCS", "HDFC"],
  "holdings": {
    "RELIANCE": { ... stock data ... },
    "TCS": { ... stock data ... },
    "HDFC": { ... stock data ... }
  },
  "metrics": {
    "total_value": 975037.50,
    "total_change": 8537.50,
    "total_change_percent": 0.88,
    "invested_value": 966500.00,
    "current_value": 975037.50,
    "unrealized_pnl": 8537.50,
    "realized_pnl": 0.0,
    "portfolio_beta": 1.15,
    "sharpe_ratio": 0.85,
    "max_drawdown": -5.2
  },
  "last_updated": "2025-01-18T10:30:00"
}
```

---

## **3. Market Context & Overview**

**`GET /api/market/context`** - Everything about the market in one call

### **No Parameters Required** - Returns comprehensive market data

### **Response Structure**

```json
{
  "timestamp": "2025-01-18T10:30:00",
  "market_status": "OPEN",
  "trading_session": "regular",
  "indices": [
    {
      "symbol": "^NSEI",
      "name": "NIFTY 50",
      "value": 21500.50,
      "change": 125.30,
      "change_percent": 0.58,
      "timestamp": "2025-01-18T10:30:00"
    }
  ],
  "advances": 1250,
  "declines": 850,
  "unchanged": 100,
  "new_highs": 45,
  "new_lows": 23,
  "sector_performance": {
    "Banking": 1.25,
    "IT": 0.85,
    "Pharma": -0.45,
    "Auto": 2.10
  },
  "vix": 18.5,
  "put_call_ratio": 1.15,
  "fii_activity": {
    "net_investment": 1250.5,
    "equity": 850.2,
    "debt": 400.3
  },
  "dii_activity": {
    "net_investment": -650.8,
    "equity": -450.2,
    "debt": -200.6
  },
  "usd_inr": 83.25,
  "crude_oil": 78.50,
  "gold": 2050.0
}
```

---

## **4. Simple Status & Health**

**`GET /api/market/status`** - Lightweight health check

### **Response Structure**

```json
{
  "service": "healthy",
  "version": "2.0.0",
  "timestamp": "2025-01-18T10:30:00",
  "market": {
    "status": "OPEN",
    "session": "regular",
    "hours": {
      "open": "09:15",
      "close": "15:30",
      "timezone": "IST"
    },
    "is_trading_day": true
  },
  "api": {
    "endpoints_active": 4,
    "total_requests_today": 1250,
    "avg_response_time": "45ms"
  }
}
```

---

## **Benefits of Consolidated Design**

### **🚀 Performance Benefits**

1. **Reduced API Calls**: Get everything you need in 1-2 requests instead of 5-10
2. **Lower Latency**: Fewer round trips to server
3. **Bandwidth Efficiency**: Optimized payload sizes
4. **Rate Limit Friendly**: Stay within API limits easily

### **🎯 Developer Experience**

1. **Single Source of Truth**: One endpoint for all market data needs
2. **Flexible Scoping**: Choose data richness based on use case
3. **Consistent Response Format**: Predictable JSON structure
4. **Rich Context**: Get related data in single request

### **💼 Business Logic Benefits**

1. **Portfolio Management**: Complete P&L analysis in one call
2. **Market Analysis**: Full market context with economic indicators
3. **Risk Management**: Portfolio metrics and risk indicators
4. **Trading Decisions**: All necessary data for informed decisions

---

## **Migration from Old API**

| Old Endpoints | New Consolidated Endpoint |
|---------------|---------------------------|
| `/prices`, `/price/{symbol}`, `/quotes` | `/api/market/data?scope=standard` |
| `/historical/{symbol}`, `/historical-enhanced/{symbol}` | `/api/market/data?historical_days=30` |
| `/overview`, `/indices`, `/sectors` | `/api/market/context` |
| `/watchlist` | `/api/market/portfolio` |
| `/status`, `/health` | `/api/market/status` |

---

## **Example Use Cases**

### **Dashboard Application**

```bash
# Get complete market overview + top stocks
GET /api/market/data?symbols=RELIANCE,TCS,HDFC,INFY&scope=standard&include_context=true
```

### **Trading Application**

```bash
# Get comprehensive data for decision making
GET /api/market/data?symbols=RELIANCE&scope=comprehensive&historical_days=30
```

### **Portfolio Tracker**

```bash
# Track portfolio performance
GET /api/market/portfolio?name=My%20Investments&symbols=RELIANCE,TCS,HDFC&quantities=100,50,200&avg_prices=2400,3800,1650&scope=standard
```

### **Market Analysis**

```bash
# Complete market context for analysis
GET /api/market/context
```

---

## **Response Codes**

| Code | Description |
|------|-------------|
| 200 | Success |
| 400 | Bad Request (invalid parameters) |
| 404 | Symbol not found |
| 429 | Rate limit exceeded |
| 500 | Internal server error |

---

## **Rate Limits**

| Endpoint | Limit |
|----------|-------|
| `/api/market/data` | 60 requests/minute |
| `/api/market/portfolio` | 30 requests/minute |
| `/api/market/context` | 20 requests/minute |
| `/api/market/status` | 120 requests/minute |

---

This consolidated API design reduces complexity while providing richer information coverage, making it perfect for modern trading and financial applications!
