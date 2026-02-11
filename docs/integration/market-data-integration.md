# Market Data Service Integration Guide

Base URL: `http://localhost:8079` (dev) | `http://YOUR_HOST:8179` (prod)

## Endpoints

### 1. POST /api/market/data

Universal market data – quotes, historical, fundamentals.

**Request:**

```json
{
  "symbols": ["RELIANCE", "TCS", "NSE:RELIANCE"],
  "exchange": "NSE",
  "data_type": "quote"
}
```

**cURL:**

```bash
curl -X POST "http://localhost:8079/api/market/data" \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["RELIANCE", "TCS"], "exchange": "NSE"}'
```

**Response 200:**

```json
{
  "success": true,
  "data": {
    "NSE:RELIANCE": {
      "symbol": "RELIANCE",
      "last_price": 2500.5,
      "open": 2480.0,
      "high": 2520.0,
      "low": 2475.0,
      "volume": 1000000,
      "net_change": 20.5,
      "net_change_percent": 0.83
    }
  },
  "total_symbols": 2,
  "successful_symbols": 2,
  "failed_symbols": 0,
  "processing_time_ms": 150.5,
  "timestamp": "2024-01-15T14:30:00Z"
}
```

### 2. GET /api/market/status

Market open/closed status, next open/close times.

**cURL:**

```bash
curl -s "http://localhost:8079/api/market/status"
```

**Response 200:**

```json
{
  "market_status": "open",
  "market_open": true,
  "current_time": "2024-01-15T14:30:00Z",
  "next_open": null,
  "next_close": "2024-01-15T15:30:00Z",
  "exchanges": {},
  "message": null
}
```

### 3. GET /api/market/instruments

List instruments. Use `?limit=10` and `?exchange=NSE` to filter.

**cURL:**

```bash
curl -s "http://localhost:8079/api/market/instruments?limit=5"
```

**Response 200:**

```json
{
  "success": true,
  "instruments": [
    {
      "instrument_token": 738561,
      "tradingsymbol": "RELIANCE",
      "name": "Reliance Industries",
      "last_price": 2500.5,
      "lot_size": 1,
      "instrument_type": "EQ",
      "exchange": "NSE"
    }
  ],
  "total_count": 5,
  "exchanges": ["NSE", "BSE"]
}
```

### 4. POST /api/market/quotes

Real-time quotes for symbols.

**Request:**

```json
{
  "symbols": ["NSE:RELIANCE", "NSE:TCS"],
  "exchange": "NSE"
}
```

**cURL:**

```bash
curl -X POST "http://localhost:8079/api/market/quotes" \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["NSE:RELIANCE", "NSE:TCS"]}'
```
