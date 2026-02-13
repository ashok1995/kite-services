# External APIs Used

## Overview

This document describes all external and internal APIs consumed by Kite Services, including data models, authentication, and usage patterns.

## 1. Kite Connect API

### API Information

- **Name**: Kite Connect API
- **Provider**: Zerodha
- **Base URL**: `https://api.kite.trade`
- **Documentation**: <https://kite.trade/docs/connect/v3/>
- **Purpose**: Real-time Indian stock market data

### Authentication

- **Type**: OAuth 2.0
- **Flow**:
  1. Redirect user to login URL
  2. Receive request token via callback
  3. Exchange for access token
  4. Token valid for entire trading day

### Endpoints Used

#### 1.1 Quote API

**Endpoint**: `/quote`  
**Method**: GET  
**Purpose**: Get real-time quotes for stocks

**Request Model**:

```python
{
    "instruments": ["NSE:RELIANCE", "NSE:TCS"]
}
```

**Response Model**:

```python
{
    "NSE:RELIANCE": {
        "instrument_token": 738561,
        "last_price": 2500.50,
        "volume": 1000000,
        "ohlc": {
            "open": 2480.0,
            "high": 2520.0,
            "low": 2475.0,
            "close": 2540.0
        }
    }
}
```

**Usage in System**:

- File: `src/services/stock_data_service.py`
- Function: `get_real_time_data()`
- Frequency: On-demand (user requests)

#### 1.2 Historical Data API

**Endpoint**: `/instruments/historical/{instrument_token}/{interval}`  
**Method**: GET  
**Purpose**: Get historical candlestick data

**Request Model**:

```python
{
    "instrument_token": 738561,
    "from_date": "2024-01-01",
    "to_date": "2024-01-31",
    "interval": "day"  # minute, day, 3minute, etc.
}
```

**Response Model**:

```python
{
    "candles": [
        ["2024-01-01T09:15:00+0530", 2480, 2490, 2475, 2485, 500000],
        # [timestamp, open, high, low, close, volume]
    ]
}
```

**Usage in System**:

- File: `src/services/stock_data_service.py`
- Function: `get_historical_data()`
- Frequency: On-demand

#### 1.3 Instruments List

**Endpoint**: `/instruments`  
**Method**: GET  
**Purpose**: Get list of all tradable instruments

**Usage in System**:

- File: `src/core/kite_client.py`
- Function: `get_instruments()`
- Frequency: Daily cache update

### Rate Limits

- 3 requests per second
- 1000 requests per day for historical data
- Implemented in: `src/core/kite_client.py`

### Error Handling

- Token expiry: Refresh flow
- Rate limit: Exponential backoff
- Network errors: Retry with timeout

---

## 2. Yahoo Finance API

### API Information

- **Name**: Yahoo Finance API
- **Provider**: Yahoo / yfinance library
- **Base URL**: `https://query1.finance.yahoo.com`
- **Documentation**: <https://github.com/ranaroussi/yfinance>
- **Purpose**: Global market data, US indices, fundamentals

### Authentication

- **Type**: None (public API)
- **Rate Limits**: ~100 requests per minute

### Endpoints Used

#### 2.1 Ticker Information

**Purpose**: Get current quote for global instruments

**Request Model** (yfinance):

```python
import yfinance as yf
ticker = yf.Ticker("^GSPC")  # S&P 500
```

**Response Model**:

```python
{
    "symbol": "^GSPC",
    "shortName": "S&P 500",
    "regularMarketPrice": 4500.0,
    "regularMarketChange": 25.0,
    "regularMarketChangePercent": 0.56,
    "regularMarketVolume": 1000000
}
```

**Usage in System**:

- File: `src/services/yahoo_finance_service.py`
- Function: `get_quote()`
- Instruments: `^GSPC`, `^DJI`, `^IXIC`, `^FTSE`, `^N225`, `^HSI`

#### 2.2 Historical Data

**Purpose**: Get historical price data

**Request Model**:

```python
{
    "symbol": "^GSPC",
    "period": "1mo",  # or start/end dates
    "interval": "1d"  # 1m, 5m, 1d, 1wk
}
```

**Response Model**:

```python
DataFrame with columns:
- Date (index)
- Open
- High
- Low
- Close
- Volume
```

**Usage in System**:

- File: `src/services/yahoo_finance_service.py`
- Function: `get_historical_data()`
- Frequency: As needed for analysis

#### 2.3 Fundamental Data

**Purpose**: Company fundamentals (PE ratio, market cap, etc.)

**Response Fields Used**:

- Market cap
- PE ratio
- Dividend yield
- 52-week high/low

**Usage in System**:

- File: `src/services/yahoo_finance_service.py`
- Function: `get_fundamentals()`

### Symbols Used

**Global Indices**:

- `^GSPC` - S&P 500
- `^DJI` - Dow Jones Industrial Average
- `^IXIC` - NASDAQ Composite
- `^FTSE` - FTSE 100 (UK)
- `^N225` - Nikkei 225 (Japan)
- `^HSI` - Hang Seng (Hong Kong)

**Volatility Indices**:

- `^VIX` - CBOE Volatility Index
- `^INDIA VIX` - India VIX (via Kite)

### Rate Limits

- ~100 requests per minute (unofficial)
- Implemented retry logic with backoff

### Error Handling

- Missing data: Return None or default values
- Network errors: Retry 3 times
- Malformed responses: Log and skip

---

## 3. Internal Services

### 3.1 Market Context Service

**Purpose**: Generate market intelligence from raw data

**Input Data Models**:

```python
# From Kite Connect
KiteQuote = {
    "last_price": float,
    "volume": int,
    "ohlc": {...}
}

# From Yahoo Finance
GlobalQuote = {
    "symbol": str,
    "last_price": float,
    "change_percent": float
}
```

**Output Data Model**:

```python
MarketContext = {
    "market_regime": "bullish" | "bearish" | "sideways" | "volatile",
    "global_sentiment": "positive" | "neutral" | "negative",
    "india_vix": float,
    "advance_decline_ratio": float,
    "leading_sectors": List[str],
    "processing_time_ms": int
}
```

**Usage**:

- Called by: `market_context_routes.py`, `consolidated_routes.py`
- Frequency: On-demand

---

## API Client Wrappers

### Kite Client

**File**: `src/core/kite_client.py`

**Key Methods**:

```python
class KiteClient:
    async def get_quote(self, symbols: List[str]) -> Dict
    async def get_historical(self, symbol: str, interval: str, ...) -> List[Candle]
    async def initialize(self) -> None
    async def cleanup(self) -> None
```

**Features**:

- Token management
- Rate limiting
- Error handling
- Retry logic
- Logging

### Yahoo Finance Service

**File**: `src/services/yahoo_finance_service.py`

**Key Methods**:

```python
class YahooFinanceService:
    async def get_quote(self, symbol: str) -> Dict
    async def get_historical_data(self, symbol: str, ...) -> DataFrame
    async def get_fundamentals(self, symbol: str) -> Dict
    async def initialize(self) -> None
```

**Features**:

- Async wrapper around yfinance
- Caching (future enhancement)
- Error handling
- Data transformation

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────┐
│  User Request (Stock Data / Market Context)    │
└─────────────────────┬───────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────┐
│           API Routes (FastAPI)                  │
│  - Validate request                             │
│  - Generate request ID                          │
└─────────────────────┬───────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────┐
│          Service Layer                          │
│  - StockDataService / MarketContextService      │
│  - Orchestrate data collection                  │
└─────┬───────────────────────────────────────┬───┘
      │                                       │
      ▼                                       ▼
┌─────────────┐                     ┌──────────────────┐
│ Kite Client │                     │ Yahoo Finance    │
│             │                     │ Service          │
│ • Quotes    │                     │ • Global indices │
│ • Historical│                     │ • Fundamentals   │
└─────┬───────┘                     └─────┬────────────┘
      │                                   │
      ▼                                   ▼
┌─────────────┐                     ┌──────────────────┐
│Kite Connect │                     │Yahoo Finance API │
│ REST API    │                     │                  │
└─────────────┘                     └──────────────────┘
```

---

## Testing External APIs

### Mock Responses

All external API calls are mocked in unit tests:

**File**: `tests/unit/test_services/test_yahoo_finance_service.py`

```python
@patch('yfinance.Ticker')
def test_get_quote_mock(mock_ticker):
    mock_ticker.return_value.info = {
        "regularMarketPrice": 4500.0
    }
    # Test service with mocked data
```

### Integration Tests

Real API calls in integration tests (with rate limiting):

**File**: `tests/integration/test_stock_data_service.py`

```python
@pytest.mark.integration
async def test_real_kite_api():
    # Only run if credentials available
    if not has_credentials():
        pytest.skip("No credentials")
    # Make real API call
```

---

## Monitoring & Logging

### API Call Logging

All external API calls are logged:

```python
logger.info(
    "External API call",
    extra={
        "api": "kite_connect",
        "endpoint": "/quote",
        "symbols": ["RELIANCE"],
        "response_time_ms": 150,
        "success": True
    }
)
```

### Metrics Tracked

- API call count
- Response times
- Error rates
- Rate limit hits
- Token refresh frequency

---

## Future APIs

### Planned Integrations

1. **NSE API** - Direct NSE data feed
2. **Redis** - Caching layer
3. **Prometheus** - Metrics collection
4. **Sentiment APIs** - News sentiment analysis

---

## Summary Table

| API | Purpose | Auth | Rate Limit | Used In |
|-----|---------|------|-----------|---------|
| Kite Connect | Indian stocks real-time | OAuth 2.0 | 3/sec | stock_data_service.py |
| Yahoo Finance | Global markets | None | ~100/min | yahoo_finance_service.py |
| Internal Services | Market intelligence | N/A | N/A | market_context_service.py |
