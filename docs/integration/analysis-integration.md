# Analysis Service Integration Guide

Base URL: `http://localhost:8079` (dev) | `http://YOUR_HOST:8179` (prod)

## Endpoints

### 1. POST /api/analysis/context

Complete market context – global, Indian markets, sentiment, technicals.

**Request:**

```json
{
  "symbols": ["RELIANCE", "TCS"],
  "include_global": true,
  "include_indian": true,
  "include_sentiment": true,
  "include_technical": true
}
```

**cURL:**

```bash
curl -X POST "http://localhost:8079/api/analysis/context" \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["RELIANCE"], "include_global": true, "include_indian": true}'
```

**Response 200:** `MarketContextResponse` with `global_markets`, `indian_markets`, `market_sentiment`, `technical_analysis`, `processing_time_ms`.

### 2. POST /api/analysis/intelligence

Stock-specific intelligence – trends, levels, signals.

**Request:**

```json
{
  "symbol": "RELIANCE",
  "include_trends": true,
  "include_levels": true,
  "include_signals": true,
  "time_horizon": "short"
}
```

**cURL:**

```bash
curl -X POST "http://localhost:8079/api/analysis/intelligence" \
  -H "Content-Type: application/json" \
  -d '{"symbol": "RELIANCE"}'
```

**Response 200:**

```json
{
  "success": true,
  "intelligence": {
    "symbol": "RELIANCE",
    "overall_trend": "bullish",
    "support_levels": [2480.0, 2450.0],
    "resistance_levels": [2550.0, 2580.0],
    "trading_signals": [],
    "risk_level": "medium"
  },
  "processing_time_ms": 120.5,
  "message": null
}
```

### 3. POST /api/analysis/stock

Single-stock analysis – price, technicals, signals.

**Request:**

```json
{
  "symbol": "RELIANCE",
  "analysis_type": "comprehensive",
  "time_horizon": "intraday"
}
```

**cURL:**

```bash
curl -X POST "http://localhost:8079/api/analysis/stock" \
  -H "Content-Type: application/json" \
  -d '{"symbol": "RELIANCE", "analysis_type": "comprehensive", "time_horizon": "intraday"}'
```

**Response 200:**

```json
{
  "success": true,
  "symbol": "RELIANCE",
  "analysis_type": "comprehensive",
  "time_horizon": "intraday",
  "current_price": 2500.5,
  "open_price": 2480.0,
  "rsi_14": 55.0,
  "trend": "bullish",
  "signal": "BUY",
  "confidence": 0.7,
  "processing_time_ms": 180.2,
  "message": "Stock analysis completed for RELIANCE (comprehensive)"
}
```

### 4. POST /api/analysis/context/enhanced

Enhanced hierarchical context – primary, detailed, style-specific (intraday/swing/long-term).

**Request:**

```json
{
  "trading_styles": ["intraday", "swing"],
  "include_primary": true,
  "include_detailed": true,
  "include_style_specific": true,
  "include_sectors": true,
  "include_technicals": true,
  "focus_symbols": ["RELIANCE"]
}
```

**cURL:**

```bash
curl -X POST "http://localhost:8079/api/analysis/context/enhanced" \
  -H "Content-Type: application/json" \
  -d '{"trading_styles": ["intraday"], "include_primary": true, "include_detailed": false, "include_style_specific": true}'
```

**Response 200:** `EnhancedMarketContextResponse` with `primary_context`, `detailed_context`, `intraday_context`, `swing_context`, `long_term_context`, `context_quality_score`, `ml_features`.
