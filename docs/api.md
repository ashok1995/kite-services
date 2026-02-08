# Complete API Reference

## Base URL

- **Development**: `http://localhost:8079`
- **Production**: `http://localhost:8179`

## Authentication

Currently uses Kite Connect OAuth tokens configured via environment variables. API key authentication planned for future.

---

## Core Endpoints

### Health & Status

#### GET /health
Health check endpoint

**Response**: 200 OK
```json
{
  "status": "healthy",
  "service": "kite-services",
  "version": "1.0.0",
  "environment": "production",
  "services": {
    "kite_client": {"status": "running"},
    "yahoo_service": {"status": "running"}
  }
}
```

#### GET /
Service information

**Response**: 200 OK
```json
{
  "service": "kite-services",
  "version": "1.0.0",
  "environment": "production",
  "docs_url": "/docs",
  "health_url": "/health",
  "api_prefix": "/api"
}
```

---

## Stock Data API

### POST /api/stock-data/real-time
Get real-time stock quotes

**Request Body**:
```json
{
  "symbols": ["RELIANCE", "TCS"],
  "exchange": "NSE"
}
```

**Response**: 200 OK
```json
{
  "stocks": [
    {
      "symbol": "RELIANCE",
      "last_price": 2500.50,
      "volume": 1000000,
      "change": 25.50,
      "change_percent": 1.03,
      "timestamp": "2024-01-15T14:30:00Z"
    }
  ],
  "successful_symbols": 2,
  "failed_symbols": 0,
  "timestamp": "2024-01-15T14:30:00Z",
  "request_id": "req_123abc"
}
```

### POST /api/stock-data/historical
Get historical candlestick data

**Request Body**:
```json
{
  "symbol": "RELIANCE",
  "from_date": "2024-01-01T00:00:00Z",
  "to_date": "2024-01-31T23:59:59Z",
  "interval": "day"
}
```

**Response**: 200 OK
```json
{
  "symbol": "RELIANCE",
  "candles": [
    {
      "timestamp": "2024-01-01T00:00:00Z",
      "open": 2480.0,
      "high": 2520.0,
      "low": 2475.0,
      "close": 2500.0,
      "volume": 1000000
    }
  ],
  "from_date": "2024-01-01T00:00:00Z",
  "to_date": "2024-01-31T23:59:59Z",
  "total_candles": 22,
  "request_id": "req_456def"
}
```

### GET /api/stock-data/examples
API usage examples

---

## Market Context API

### GET /api/market-context-data/quick-context
Quick market intelligence (no stock recommendations)

**Response**: 200 OK
```json
{
  "market_regime": "bullish",
  "global_sentiment": "positive",
  "india_vix": 15.5,
  "advance_decline_ratio": 1.5,
  "leading_sectors": ["IT", "Banking", "Pharma"],
  "processing_time_ms": 470,
  "timestamp": "2024-01-15T14:30:00Z"
}
```

### GET /api/market-context/full
Comprehensive market context

**Response**: 200 OK
```json
{
  "market_regime": "bullish",
  "regime_confidence": 0.85,
  "indian_indices": {
    "nifty50": {
      "symbol": "NIFTY 50",
      "last_price": 19500.0,
      "change_percent": 0.5,
      "trend": "bullish"
    }
  },
  "global_markets": {
    "us_markets": {...},
    "asian_markets": {...}
  },
  "volatility": {
    "india_vix": 15.5,
    "vix": 18.2
  },
  "market_breadth": {
    "advance_decline_ratio": 1.5,
    "new_highs": 45,
    "new_lows": 12
  },
  "sector_rotation": {
    "leading_sectors": ["IT", "Banking"],
    "lagging_sectors": ["Metals", "Energy"]
  },
  "timestamp": "2024-01-15T14:30:00Z"
}
```

---

## Token Management API

### POST /api/token/submit
Submit request token for access token generation

**Request Body**:
```json
{
  "request_token": "abc123xyz"
}
```

**Response**: 200 OK
```json
{
  "status": "success",
  "access_token": "generated_token",
  "expires_at": "2024-01-15T15:30:00Z",
  "message": "Token generated successfully"
}
```

### GET /api/token/status
Check token status and validity

**Response**: 200 OK
```json
{
  "status": "valid",
  "expires_at": "2024-01-15T15:30:00Z",
  "time_remaining_minutes": 45
}
```

---

## WebSocket API

### WS /ws/market-data
Real-time market data stream

**Subscribe Message**:
```json
{
  "type": "subscribe",
  "symbols": ["RELIANCE", "TCS"]
}
```

**Data Message**:
```json
{
  "type": "tick",
  "symbol": "RELIANCE",
  "last_price": 2500.50,
  "volume": 1000000,
  "timestamp": "2024-01-15T14:30:00Z"
}
```

---

## Error Responses

### 400 Bad Request
```json
{
  "error": "ValidationError",
  "message": "Invalid symbols list",
  "details": {...}
}
```

### 401 Unauthorized
```json
{
  "error": "Unauthorized",
  "message": "Invalid or expired access token"
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal server error",
  "message": "An unexpected error occurred",
  "type": "ServerError"
}
```

---

## Rate Limits

- 100 requests per minute (configurable)
- WebSocket: 3 requests per second for subscriptions

---

## Interactive Documentation

- **Swagger UI**: `/docs`
- **ReDoc**: `/redoc` (if enabled)

For complete interactive API documentation with try-it-out functionality, visit the `/docs` endpoint.

