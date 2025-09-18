# Kite Services API Documentation

## Market Data API Endpoints

### Base URL
```
http://localhost:8080/api/market
```

## Current Stock Prices

### Get Multiple Stock Prices
**POST** `/prices`

Get current prices for multiple stocks.

**Request Body:**
```json
{
  "symbols": ["RELIANCE", "TCS", "HDFC", "INFY"],
  "include_fundamentals": false,
  "include_technical_indicators": false
}
```

**Response:**
```json
{
  "prices": {
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
      "timestamp": "2025-01-18T10:30:00",
      "market_status": "open"
    }
  },
  "market_status": "open",
  "timestamp": "2025-01-18T10:30:00",
  "request_id": "prices_1642509000"
}
```

### Get Multiple Stock Prices (GET)
**GET** `/prices?symbols=RELIANCE,TCS,HDFC&include_fundamentals=false`

Same as POST version but via GET request with query parameters.

### Get Single Stock Price
**GET** `/price/{symbol}?include_fundamentals=false`

Get current price for a single stock.

**Response:**
```json
{
  "price": {
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
    "timestamp": "2025-01-18T10:30:00",
    "market_status": "open"
  },
  "fundamentals": {
    "market_cap": 16500000000000,
    "pe_ratio": 24.5,
    "dividend_yield": 0.35
  },
  "timestamp": "2025-01-18T10:30:00"
}
```

## Historical Data

### Get Enhanced Historical Data
**GET** `/historical-enhanced/{symbol}?days=30&interval=day&include_stats=true`

Get historical data with additional statistical analysis.

**Response:**
```json
{
  "symbol": "RELIANCE",
  "interval": "day",
  "from_date": "2024-12-18T00:00:00",
  "to_date": "2025-01-18T00:00:00",
  "data": [
    {
      "timestamp": "2024-12-18T00:00:00",
      "open": 2400.00,
      "high": 2420.00,
      "low": 2385.00,
      "close": 2410.00,
      "volume": 1100000
    }
  ],
  "total_candles": 30,
  "price_change": 40.50,
  "price_change_percent": 1.68,
  "volume_average": 1200000,
  "high_52_week": 2650.00,
  "low_52_week": 2100.00,
  "timestamp": "2025-01-18T10:30:00"
}
```

### Get Historical Data (Original)
**GET** `/historical/{symbol}?days=30&interval=day`

Get basic historical data.

**POST** `/historical`

Get historical data via POST request.

## Market Context & Overview

### Get Market Overview
**GET** `/overview`

Get comprehensive market overview including indices, sector performance, and market breadth.

**Response:**
```json
{
  "timestamp": "2025-01-18T10:30:00",
  "market_status": "open",
  "major_indices": [
    {
      "symbol": "^NSEI",
      "name": "NIFTY 50",
      "last_price": 21500.50,
      "change": 125.30,
      "change_percent": 0.58,
      "timestamp": "2025-01-18T10:30:00"
    }
  ],
  "top_gainers": [],
  "top_losers": [],
  "most_active": [],
  "sector_performance": {
    "Banking": 1.25,
    "IT": 0.85,
    "Pharma": -0.45,
    "Auto": 2.10
  },
  "market_breadth": {
    "advances": 1250,
    "declines": 850,
    "unchanged": 100
  },
  "volatility_index": 18.5
}
```

### Get Market Context
**POST** `/context`

Get comprehensive market context for specific symbols.

**GET** `/context?symbols=RELIANCE,TCS&include_sentiment=true&include_indices=true&include_sectors=true`

## Market Status & Information

### Get Market Status
**GET** `/status`

Get current market status and trading hours.

**Response:**
```json
{
  "status": "OPEN",
  "timestamp": "2025-01-18T10:30:00",
  "market_hours": {
    "open": "09:15",
    "close": "15:30",
    "timezone": "IST"
  },
  "is_trading_day": true
}
```

### Get Market Indices
**GET** `/indices`

Get major market indices data.

### Get Sector Performance
**GET** `/sectors`

Get sector-wise performance data.

### Get Economic Indicators
**GET** `/economic-indicators`

Get key economic indicators including VIX, USD/INR, Gold, Oil prices.

## Symbol Search & Instruments

### Search Symbols
**POST** `/search`
**GET** `/search?q=reliance&exchange=NSE&limit=10`

Search for symbols matching a query.

**Response:**
```json
{
  "results": [
    {
      "symbol": "RELIANCE.NS",
      "name": "RELIANCE",
      "exchange": "NSE",
      "instrument_type": "EQ"
    }
  ],
  "total_count": 1,
  "query": "reliance"
}
```

### Get Instruments
**GET** `/instruments?exchange=NSE`

Get list of available instruments for an exchange.

### Get Instrument Details
**GET** `/instruments/{symbol}`

Get details for a specific instrument.

## Quotes & Real-time Data

### Get Quotes
**POST** `/quotes`

Get real-time quotes for multiple symbols.

**GET** `/quote/{symbol}`

Get real-time quote for a single symbol.

## Watchlists

### Create Watchlist
**POST** `/watchlist`

Create a watchlist and get current prices for all symbols.

**Request Body:**
```json
{
  "name": "My Portfolio",
  "symbols": ["RELIANCE", "TCS", "HDFC", "INFY"]
}
```

**Response:**
```json
{
  "name": "My Portfolio",
  "symbols": ["RELIANCE", "TCS", "HDFC", "INFY"],
  "prices": {
    "RELIANCE": {
      "symbol": "RELIANCE",
      "last_price": 2450.50,
      "change": 25.30,
      "change_percent": 1.04
    }
  },
  "total_value": 9800.00,
  "total_change": 125.20,
  "total_change_percent": 1.29,
  "timestamp": "2025-01-18T10:30:00"
}
```

## Error Responses

All endpoints return consistent error responses:

```json
{
  "error": "Error type",
  "message": "Detailed error message",
  "type": "ErrorType",
  "timestamp": "2025-01-18T10:30:00",
  "request_id": "optional_request_id"
}
```

## Status Codes

- **200**: Success
- **400**: Bad Request (invalid parameters)
- **404**: Not Found (symbol not found)
- **500**: Internal Server Error
- **503**: Service Unavailable

## Rate Limits

- **Market Data**: 100 requests per minute
- **Historical Data**: 50 requests per minute
- **Real-time Quotes**: 200 requests per minute

## Authentication

Currently, the API does not require authentication for market data endpoints. Authentication will be required for trading endpoints.

## Examples

### Get Current Price for RELIANCE
```bash
curl -X GET "http://localhost:8080/api/market/price/RELIANCE?include_fundamentals=true"
```

### Get Multiple Stock Prices
```bash
curl -X GET "http://localhost:8080/api/market/prices?symbols=RELIANCE,TCS,HDFC"
```

### Get Historical Data
```bash
curl -X GET "http://localhost:8080/api/market/historical-enhanced/RELIANCE?days=30&include_stats=true"
```

### Get Market Overview
```bash
curl -X GET "http://localhost:8080/api/market/overview"
```

### Create Watchlist
```bash
curl -X POST "http://localhost:8080/api/market/watchlist" \
  -H "Content-Type: application/json" \
  -d '{"name": "My Stocks", "symbols": ["RELIANCE", "TCS", "HDFC"]}'
```
