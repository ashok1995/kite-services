# Unified Trading API Guide

## Overview

The Unified Trading API provides a minimal, stable interface for all trading analysis with consistent data models optimized for ML pipeline integration.

## Key Features

- **Single Endpoint**: One API for swing, intraday, and position trading
- **Unified Data Models**: Consistent request/response structures
- **Pipeline Stability**: Built-in error handling and circuit breakers
- **ML Optimized**: Numerical features and confidence scores
- **Type Safe**: Full Pydantic validation

---

## Core Endpoints

### 1. Unified Trading Analysis

**Endpoint**: `POST /api/trading/analyze`

Single endpoint for all trading strategies with unified data models.

**Request Model**:
```json
{
  "symbol": "^NSEI",
  "horizon": "swing",
  "min_confidence": 50.0,
  "include_market_context": true,
  "max_signals": 5
}
```

**Response Model**:
```json
{
  "symbol": "^NSEI",
  "horizon": "swing",
  "timestamp": "2025-09-21T16:45:00Z",
  "signals": [
    {
      "signal_id": "^NSEI_buy_1695317100",
      "symbol": "^NSEI",
      "timestamp": "2025-09-21T16:45:00Z",
      "signal_type": "buy",
      "signal_strength": "strong",
      "confidence": 85.2,
      "current_price": 25350.0,
      "entry_price": 25350.0,
      "target_price": 26100.0,
      "stop_loss": 24800.0,
      "risk_reward_ratio": 2.3,
      "potential_return_percent": 2.96,
      "risk_percent": 2.17,
      "horizon": "swing",
      "time_to_target_hours": 48,
      "volume_confirmation": true,
      "reason": "Local minimum detected with strong volume confirmation",
      "supporting_indicators": ["RSI", "MACD", "Volume"],
      "technical_strength": 88.5,
      "momentum_score": 82.1,
      "volatility_score": 65.3
    }
  ],
  "market_context": {
    "market_sentiment": "bullish",
    "volatility_regime": "normal",
    "trend_direction": "up",
    "vix_level": 9.97,
    "market_strength_score": 75.5,
    "sector_rotation_score": 68.2,
    "leading_sectors": ["Auto", "Metal", "Pharma"],
    "lagging_sectors": ["Banking", "IT"],
    "global_sentiment": "positive",
    "risk_on_off": "risk_on"
  },
  "data_quality": {
    "overall_score": 80.0,
    "quality_level": "good",
    "data_points": 65,
    "data_freshness_minutes": 15,
    "completeness_percent": 98.5,
    "technical_analysis_ready": true,
    "ml_ready": true,
    "issues": [],
    "recommendations": []
  },
  "best_signal": { /* Same as signal object */ },
  "signals_count": 1,
  "trading_recommendation": "Strong BUY opportunity with 85.2% confidence",
  "risk_level": "low",
  "success": true,
  "message": "Analysis completed successfully"
}
```

### 2. Multi-Symbol Analysis

**Endpoint**: `POST /api/trading/multi-analyze`

Analyze multiple symbols simultaneously with unified ranking.

**Request Model**:
```json
{
  "symbols": ["^NSEI", "^NSEBANK", "RELIANCE.NS"],
  "horizon": "swing",
  "min_confidence": 60.0,
  "sort_by": "confidence"
}
```

**Response Model**:
```json
{
  "symbols": ["^NSEI", "^NSEBANK", "RELIANCE.NS"],
  "horizon": "swing",
  "timestamp": "2025-09-21T16:45:00Z",
  "signals": [ /* All signals from all symbols */ ],
  "market_context": { /* Global market context */ },
  "symbol_results": {
    "^NSEI": { /* Individual TradingResponse */ },
    "^NSEBANK": { /* Individual TradingResponse */ },
    "RELIANCE.NS": { /* Individual TradingResponse */ }
  },
  "best_opportunities": [ /* Top 5 signals across all symbols */ ],
  "total_signals": 8,
  "bullish_symbols": 2,
  "bearish_symbols": 1,
  "neutral_symbols": 0,
  "success": true,
  "message": "Multi-symbol analysis completed successfully"
}
```

### 3. System Health

**Endpoint**: `GET /api/health`

Comprehensive system health and performance monitoring.

**Response Model**:
```json
{
  "status": "healthy",
  "timestamp": "2025-09-21T16:45:00Z",
  "services": {
    "data_quality": true,
    "data_collector": true,
    "signal_engine": true
  },
  "data_quality_score": 80.0,
  "response_time_ms": 250.5,
  "uptime_seconds": 3600,
  "issues": [],
  "warnings": []
}
```

---

## Data Models

### Core Signal Model

Every signal follows the same unified structure:

```typescript
interface TradingSignal {
  // Identity
  signal_id: string;
  symbol: string;
  timestamp: string;
  
  // Signal Details
  signal_type: "buy" | "sell" | "hold";
  signal_strength: "weak" | "moderate" | "strong";
  confidence: number; // 0-100
  
  // Price Information
  current_price: number;
  entry_price: number;
  target_price: number;
  stop_loss: number;
  
  // Risk Metrics
  risk_reward_ratio: number;
  potential_return_percent: number;
  risk_percent: number;
  
  // Trading Context
  horizon: "intraday" | "swing" | "position";
  time_to_target_hours?: number;
  volume_confirmation: boolean;
  
  // Analysis
  reason: string;
  supporting_indicators: string[];
  
  // ML Features
  technical_strength: number; // 0-100
  momentum_score: number; // 0-100
  volatility_score: number; // 0-100
}
```

### Market Context Model

```typescript
interface MarketContext {
  market_sentiment: "bullish" | "bearish" | "neutral";
  volatility_regime: "low" | "normal" | "high" | "extreme";
  trend_direction: "up" | "down" | "sideways";
  vix_level?: number;
  market_strength_score: number; // 0-100
  sector_rotation_score: number; // 0-100
  leading_sectors: string[];
  lagging_sectors: string[];
  global_sentiment?: "positive" | "negative" | "neutral";
  risk_on_off: "risk_on" | "risk_off" | "neutral";
}
```

### Data Quality Model

```typescript
interface DataQualityInfo {
  overall_score: number; // 0-100
  quality_level: "poor" | "fair" | "good" | "excellent";
  data_points: number;
  data_freshness_minutes: number;
  completeness_percent: number; // 0-100
  technical_analysis_ready: boolean;
  ml_ready: boolean;
  issues: string[];
  recommendations: string[];
}
```

---

## ML Integration Patterns

### 1. Feature Engineering

```python
def extract_ml_features(signal: TradingSignal) -> dict:
    return {
        # Core features
        'confidence': signal.confidence,
        'risk_reward_ratio': signal.risk_reward_ratio,
        'technical_strength': signal.technical_strength,
        'momentum_score': signal.momentum_score,
        'volatility_score': signal.volatility_score,
        
        # Derived features
        'signal_strength_numeric': {
            'weak': 1, 'moderate': 2, 'strong': 3
        }[signal.signal_strength],
        
        'horizon_numeric': {
            'intraday': 1, 'swing': 2, 'position': 3
        }[signal.horizon],
        
        # Risk features
        'potential_return': signal.potential_return_percent,
        'risk_percent': signal.risk_percent,
        'volume_confirmed': 1 if signal.volume_confirmation else 0,
        
        # Time features
        'time_to_target_hours': signal.time_to_target_hours or 0,
        'signal_age_minutes': calculate_age(signal.timestamp)
    }
```

### 2. Signal Filtering

```python
def filter_signals_for_ml(signals: List[TradingSignal]) -> List[TradingSignal]:
    return [
        signal for signal in signals
        if (
            signal.confidence >= 60 and
            signal.risk_reward_ratio >= 1.5 and
            signal.technical_strength >= 50 and
            signal.volume_confirmation
        )
    ]
```

### 3. Position Sizing

```python
def calculate_position_size(signal: TradingSignal, portfolio_value: float) -> float:
    # Base position size on confidence and risk-reward
    base_size = portfolio_value * 0.02  # 2% base
    
    # Adjust for confidence
    confidence_multiplier = signal.confidence / 100
    
    # Adjust for risk-reward ratio
    rr_multiplier = min(signal.risk_reward_ratio / 2, 2.0)
    
    # Adjust for signal strength
    strength_multiplier = {
        'weak': 0.5,
        'moderate': 1.0,
        'strong': 1.5
    }[signal.signal_strength]
    
    position_size = base_size * confidence_multiplier * rr_multiplier * strength_multiplier
    
    # Cap at 5% of portfolio
    return min(position_size, portfolio_value * 0.05)
```

---

## Error Handling

### Error Response Model

```json
{
  "success": false,
  "error_code": "VALIDATION_ERROR",
  "message": "Invalid symbol format: INVALID_SYMBOL",
  "timestamp": "2025-09-21T16:45:00Z",
  "details": {
    "field": "symbol",
    "value": "INVALID_SYMBOL"
  },
  "suggestions": [
    "Use valid symbol format (e.g., '^NSEI', 'RELIANCE.NS')",
    "Check symbol availability in our supported markets"
  ],
  "request_id": "req_12345",
  "symbol": "INVALID_SYMBOL",
  "horizon": "swing"
}
```

### Common Error Codes

- `VALIDATION_ERROR`: Invalid request parameters
- `SYMBOL_NOT_FOUND`: Symbol not available
- `DATA_QUALITY_LOW`: Insufficient data quality
- `RATE_LIMITED`: Too many requests
- `SERVICE_UNAVAILABLE`: Service temporarily down
- `INTERNAL_ERROR`: Unexpected system error

---

## Pipeline Stability Features

### Circuit Breakers

Automatic service protection with:
- **Failure Threshold**: 5 consecutive failures opens circuit
- **Recovery Timeout**: 60 seconds before retry
- **Success Threshold**: 3 successes to close circuit

### Rate Limiting

Request throttling with:
- **API Limit**: 60 requests per minute
- **Concurrent Limit**: 10 simultaneous requests
- **Burst Limit**: 15 requests in 10 seconds

### Data Validation

Automatic request sanitization:
- Symbol format validation
- Parameter range checking
- Input sanitization
- Type validation

---

## Usage Examples

### Python Client

```python
import httpx
import asyncio

class UnifiedTradingClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client = httpx.AsyncClient()
    
    async def analyze_symbol(
        self, 
        symbol: str, 
        horizon: str = "swing",
        min_confidence: float = 50.0
    ):
        response = await self.client.post(
            f"{self.base_url}/api/trading/analyze",
            json={
                "symbol": symbol,
                "horizon": horizon,
                "min_confidence": min_confidence,
                "include_market_context": True,
                "max_signals": 5
            }
        )
        return response.json()
    
    async def analyze_multiple(
        self, 
        symbols: List[str], 
        horizon: str = "swing"
    ):
        response = await self.client.post(
            f"{self.base_url}/api/trading/multi-analyze",
            json={
                "symbols": symbols,
                "horizon": horizon,
                "min_confidence": 60.0,
                "sort_by": "confidence"
            }
        )
        return response.json()

# Usage
client = UnifiedTradingClient("http://localhost:8079")

# Single symbol analysis
nifty_analysis = await client.analyze_symbol("^NSEI", "swing")
print(f"Best signal: {nifty_analysis['best_signal']}")

# Multi-symbol analysis
portfolio_analysis = await client.analyze_multiple(
    ["^NSEI", "^NSEBANK", "RELIANCE.NS"], 
    "swing"
)
print(f"Best opportunities: {portfolio_analysis['best_opportunities']}")
```

### JavaScript/Node.js Client

```javascript
class UnifiedTradingClient {
    constructor(baseUrl) {
        this.baseUrl = baseUrl;
    }
    
    async analyzeSymbol(symbol, horizon = 'swing', minConfidence = 50.0) {
        const response = await fetch(`${this.baseUrl}/api/trading/analyze`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                symbol,
                horizon,
                min_confidence: minConfidence,
                include_market_context: true,
                max_signals: 5
            })
        });
        return response.json();
    }
    
    async analyzeMultiple(symbols, horizon = 'swing') {
        const response = await fetch(`${this.baseUrl}/api/trading/multi-analyze`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                symbols,
                horizon,
                min_confidence: 60.0,
                sort_by: 'confidence'
            })
        });
        return response.json();
    }
}

// Usage
const client = new UnifiedTradingClient('http://localhost:8079');

// Single symbol analysis
const niftyAnalysis = await client.analyzeSymbol('^NSEI', 'swing');
console.log('Best signal:', niftyAnalysis.best_signal);

// Multi-symbol analysis
const portfolioAnalysis = await client.analyzeMultiple(
    ['^NSEI', '^NSEBANK', 'RELIANCE.NS'], 
    'swing'
);
console.log('Best opportunities:', portfolioAnalysis.best_opportunities);
```

---

## Performance Optimization

### Caching Strategy

- **Signal Cache**: 5 minutes for intraday, 1 hour for swing
- **Market Context Cache**: 15 minutes
- **Data Quality Cache**: 30 minutes

### Batch Processing

Use multi-symbol endpoint for analyzing multiple symbols:
- More efficient than individual requests
- Shared market context calculation
- Unified ranking across symbols

### Rate Limiting Best Practices

- Implement client-side rate limiting
- Use exponential backoff for retries
- Cache results when possible
- Batch multiple symbols in single request

---

## Migration Guide

### From Individual Endpoints

**Old Approach**:
```python
# Multiple endpoints, different data models
swing_data = await client.get('/api/swing-trading/analysis')
intraday_data = await client.get('/api/intraday-trading/signals')
market_data = await client.get('/api/v3/market-intelligence')
```

**New Unified Approach**:
```python
# Single endpoint, unified data model
swing_analysis = await client.post('/api/trading/analyze', {
    'symbol': '^NSEI',
    'horizon': 'swing'
})

intraday_analysis = await client.post('/api/trading/analyze', {
    'symbol': '^NSEI', 
    'horizon': 'intraday'
})
```

### Benefits of Migration

1. **Consistent Data Models**: Same structure across all strategies
2. **Better Error Handling**: Unified error responses
3. **Pipeline Stability**: Built-in circuit breakers and rate limiting
4. **ML Optimization**: Features designed for ML consumption
5. **Reduced Complexity**: Single API to maintain and integrate

---

## Support and Troubleshooting

### Health Check

Always check system health before processing:
```python
health = await client.get('/api/health')
if health['status'] != 'healthy':
    print(f"System issues: {health['issues']}")
```

### Common Issues

1. **Low Data Quality**: Check `data_quality.overall_score` in response
2. **No Signals Generated**: Lower `min_confidence` threshold
3. **Rate Limited**: Implement exponential backoff
4. **Circuit Breaker Open**: Wait for service recovery

### Debug Information

Enable detailed logging:
```python
import logging
logging.getLogger('unified_trading_api').setLevel(logging.DEBUG)
```

---

## Changelog

### Version 1.0.0
- Initial unified API release
- Consolidated swing, intraday, and position trading
- Unified data models across all strategies
- Built-in pipeline stability features
- ML-optimized response structure

