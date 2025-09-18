# APIs Used by Kite Services

## External APIs Consumed

### 1. Kite Connect API

**Base URL:** `https://api.kite.trade/`

**Purpose:** Primary source for real-time market data, trading operations, and historical data

**Endpoints Used:**
- `GET /instruments` - Get list of tradable instruments
- `GET /quote` - Get real-time quotes for instruments  
- `GET /historical/{instrument_token}/{interval}` - Get historical OHLC data
- `POST /orders` - Place trading orders
- `GET /orders` - Get order status and history
- `GET /positions` - Get current positions

**Request Models:**
```python
class KiteQuoteRequest(BaseModel):
    symbols: List[str]
    
class KiteHistoricalRequest(BaseModel):
    instrument_token: str
    interval: str
    from_date: datetime
    to_date: datetime
```

**Response Models:**
```python
class KiteQuoteResponse(BaseModel):
    symbol: str
    last_price: Decimal
    change: Decimal
    change_percent: Decimal
    volume: int
    ohlc: Dict[str, Decimal]
    
class KiteHistoricalResponse(BaseModel):
    data: List[HistoricalCandle]
```

**Authentication:** API Key + Access Token
**Rate Limits:** 3 requests/second, 1000 requests/day
**Error Handling:** Exponential backoff, circuit breaker pattern

---

### 2. Yahoo Finance API

**Base URL:** `https://query1.finance.yahoo.com/`

**Purpose:** Fundamental data, market indices, sector performance, economic indicators

**Endpoints Used:**
- `GET /v1/finance/quote` - Get stock fundamentals
- `GET /v1/finance/chart/{symbol}` - Get price charts
- `GET /v7/finance/options/{symbol}` - Get options data
- `GET /v10/finance/quoteSummary/{symbol}` - Get comprehensive stock data

**Request Models:**
```python
class YahooQuoteRequest(BaseModel):
    symbols: List[str]
    modules: List[str] = ["price", "summaryDetail", "defaultKeyStatistics"]
    
class YahooChartRequest(BaseModel):
    symbol: str
    interval: str
    range: str
```

**Response Models:**
```python
class YahooStockData(BaseModel):
    symbol: str
    market_cap: Optional[Decimal]
    pe_ratio: Optional[Decimal]
    dividend_yield: Optional[Decimal]
    fundamentals: Dict[str, Any]
    
class YahooIndexData(BaseModel):
    symbol: str
    name: str
    value: Decimal
    change: Decimal
    change_percent: Decimal
```

**Authentication:** None (Public API)
**Rate Limits:** 100 requests/minute
**Error Handling:** Retry with backoff, fallback to cached data

---

### 3. Market Context Service (Internal)

**Base URL:** Internal service communication

**Purpose:** Technical analysis, market intelligence, trading signals

**Endpoints Used:**
- `GET /technical-indicators/{symbol}` - Get technical indicators
- `GET /market-sentiment` - Get overall market sentiment
- `GET /trading-signals/{symbol}` - Get trading recommendations

**Request Models:**
```python
class TechnicalIndicatorsRequest(BaseModel):
    symbol: str
    period: int = 14
    indicators: List[str] = ["RSI", "SMA", "EMA", "MACD"]
    
class MarketSentimentRequest(BaseModel):
    symbols: Optional[List[str]] = None
    timeframe: str = "1d"
```

**Response Models:**
```python
class TechnicalIndicators(BaseModel):
    symbol: str
    rsi: Decimal
    sma_20: Decimal
    ema_12: Decimal
    macd: Decimal
    bollinger_upper: Decimal
    bollinger_lower: Decimal
    
class MarketSentiment(BaseModel):
    overall_sentiment: str
    sentiment_score: Decimal
    vix_level: Decimal
    fear_greed_index: int
```

**Authentication:** Internal service authentication
**Rate Limits:** No limits (internal)
**Error Handling:** Circuit breaker, graceful degradation

---

## API Integration Architecture

### Data Flow
```
Client Request
    ↓
Consolidated API Route (Thin)
    ↓
Consolidated Market Service (Business Logic)
    ↓
┌─────────────────┬─────────────────┬─────────────────┐
│   Kite Connect  │  Yahoo Finance  │ Market Context  │
│   (Real-time)   │  (Fundamentals) │   (Technical)   │
└─────────────────┴─────────────────┴─────────────────┘
    ↓
Data Aggregation & Validation
    ↓
Pydantic Response Models
    ↓
JSON Response to Client
```

### Error Handling Strategy

1. **Circuit Breaker Pattern**
   - Open circuit after 5 consecutive failures
   - Half-open state after 30 seconds
   - Close circuit after 3 successful requests

2. **Retry Logic**
   - Exponential backoff: 1s, 2s, 4s, 8s
   - Maximum 3 retries per request
   - Jitter to prevent thundering herd

3. **Fallback Mechanisms**
   - Use cached data when APIs are unavailable
   - Graceful degradation of data richness
   - Mock data for development/testing

4. **Rate Limit Handling**
   - Token bucket algorithm for rate limiting
   - Queue requests during high load
   - Priority queuing for critical operations

### Monitoring & Observability

**Metrics Tracked:**
- Request count per API
- Response times (p50, p95, p99)
- Error rates by API and error type
- Rate limit utilization
- Cache hit rates

**Logging:**
- All API requests/responses logged
- Error details with stack traces
- Performance metrics
- Business logic decisions

**Alerting:**
- API availability < 95%
- Response time > 5 seconds
- Error rate > 5%
- Rate limit utilization > 80%

### Security Considerations

1. **API Keys Management**
   - Stored in environment variables
   - Rotated regularly (monthly)
   - Encrypted at rest

2. **Data Validation**
   - All API responses validated with Pydantic
   - Input sanitization and validation
   - SQL injection prevention

3. **Rate Limiting**
   - Per-client rate limiting
   - API key-based limits
   - IP-based fallback limits

### Testing Strategy

**Unit Tests:**
- Mock all external API calls
- Test error handling scenarios
- Validate data transformations

**Integration Tests:**
- Test against API sandboxes
- End-to-end data flow validation
- Performance benchmarking

**Contract Tests:**
- API response schema validation
- Breaking change detection
- Backward compatibility checks

---

## Configuration

All API configurations are managed through environment variables and the central configuration system:

```python
class KiteConfig(BaseSettings):
    api_key: str = Field(env="KITE_API_KEY")
    access_token: str = Field(env="KITE_ACCESS_TOKEN")
    rate_limit: int = Field(3, env="KITE_RATE_LIMIT")
    timeout: int = Field(30, env="KITE_TIMEOUT")

class YahooConfig(BaseSettings):
    base_url: str = Field("https://query1.finance.yahoo.com", env="YAHOO_BASE_URL")
    rate_limit: int = Field(100, env="YAHOO_RATE_LIMIT")
    timeout: int = Field(30, env="YAHOO_TIMEOUT")
```

This ensures all API integrations follow the workspace rules for configuration management and dependency injection.
