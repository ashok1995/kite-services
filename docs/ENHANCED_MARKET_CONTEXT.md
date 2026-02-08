# Enhanced Market Context for Real-Time Trading Recommendations

**Version:** 2.0  
**Endpoint:** `/api/analysis/context/enhanced`  
**Purpose:** Multi-level hierarchical market context for ML-based trading decision systems

---

## 🎯 Overview

The Enhanced Market Context API provides a sophisticated, multi-layered view of market conditions specifically designed for **real-time trading recommendation systems**. It organizes market data into three hierarchical levels optimized for different trading styles:

### Hierarchical Structure

```
┌─────────────────────────────────────────────────────────────┐
│                    PRIMARY CONTEXT                          │
│  Quick Overview | <100ms | All Trading Styles              │
│  • Global sentiment                                         │
│  • Major index changes                                      │
│  • Market regime & risk appetite                            │
│  • Overall market score (-100 to +100)                      │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                   DETAILED CONTEXT                          │
│  Granular Analysis | <500ms | Swing & Long-term            │
│  • Sector performance with top movers                       │
│  • Technical indicators (RSI, MACD, Bollinger)              │
│  • Market breadth & internals                               │
│  • Support/resistance levels                                │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                STYLE-SPECIFIC CONTEXTS                      │
│  Trading Style Optimized | <1s | Per Style                 │
│                                                             │
│  INTRADAY: Real-time momentum, VWAP, pivot points          │
│  SWING: Multi-day patterns, sector rotation                │
│  LONG-TERM: Macro trends, fundamentals, themes             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Basic Request

```bash
curl -X POST http://127.0.0.1:8079/api/analysis/context/enhanced \
  -H "Content-Type: application/json" \
  -d '{
    "include_primary": true,
    "include_detailed": true,
    "include_style_specific": true,
    "trading_styles": ["intraday", "swing"],
    "include_sectors": true,
    "include_technicals": true,
    "include_opportunities": true
  }'
```

### Minimal Request (Fast, Primary Only)

```bash
curl -X POST http://127.0.0.1:8079/api/analysis/context/enhanced \
  -H "Content-Type: application/json" \
  -d '{
    "include_primary": true,
    "include_detailed": false,
    "include_style_specific": false
  }'
```

---

## 📊 Context Levels Explained

### 1. PRIMARY CONTEXT - The Foundation

**Response Time:** <100ms  
**Use Cases:**
- Quick market sentiment check before trading
- Feature input for fast ML models
- Real-time dashboard displays
- Pre-trade risk assessment

**Key Features:**

```json
{
  "primary_context": {
    "global_context": {
      "overall_trend": "bullish",
      "trend_strength": "moderate",
      "us_markets_change": "0.5",
      "risk_on_off": "risk_on",
      "volatility_level": "normal",
      "key_drivers": ["Tech earnings", "Fed comments"]
    },
    "indian_context": {
      "nifty_change": "0.8",
      "market_regime": "bull_weak",
      "trend_direction": "up",
      "advance_decline_ratio": "1.5",
      "nifty_support": "19500",
      "nifty_resistance": "19800"
    },
    "overall_market_score": 45,      // -100 (very bearish) to +100 (very bullish)
    "market_confidence": 0.85,        // Confidence in assessment
    "favorable_for": ["swing", "long_term"]  // Which trading styles are favorable
  }
}
```

**Market Score Interpretation:**
- **80-100:** Very Bullish - Strong uptrend, high confidence longs
- **50-79:** Bullish - Moderate uptrend, selective longs
- **20-49:** Mildly Bullish - Cautious longs, watch for reversals
- **-20 to 19:** Neutral/Sideways - Range trading, both sides possible
- **-49 to -21:** Mildly Bearish - Cautious shorts, wait for confirmation
- **-79 to -50:** Bearish - Moderate downtrend, selective shorts
- **-100 to -80:** Very Bearish - Strong downtrend, defensive positions

---

### 2. DETAILED CONTEXT - Deep Analysis

**Response Time:** <500ms  
**Use Cases:**
- Sector rotation analysis
- Technical level identification
- Market breadth assessment
- Comprehensive risk models

**Key Features:**

```json
{
  "detailed_context": {
    "nifty_analysis": {
      "index_name": "NIFTY 50",
      "current_value": "19650",
      "change_percent": "0.8",
      "immediate_support": ["19500", "19450", "19400"],
      "immediate_resistance": ["19700", "19750", "19800"],
      "technicals": {
        "rsi_14": "58.5",
        "macd_signal": "bullish_crossover",
        "price_vs_sma20": "2.5",
        "bollinger_position": "middle"
      },
      "stocks_above_sma20": 65,  // % of stocks above 20 SMA
      "put_call_ratio": "0.95"
    },
    "sectors": [
      {
        "sector_name": "IT",
        "change_percent": "1.5",
        "trend": "bullish",
        "strength_score": 75,      // -100 to +100
        "momentum": "accelerating",
        "top_gainers": ["TCS", "INFY", "WIPRO"]
      }
    ],
    "advances": 1250,
    "declines": 850,
    "new_highs": 45,
    "new_lows": 12
  }
}
```

**Sector Strength Interpretation:**
- **70-100:** Very Strong - Leading the market, high momentum
- **40-69:** Strong - Outperforming, good opportunities
- **10-39:** Moderate - In-line with market
- **-39 to 9:** Weak - Underperforming
- **-100 to -40:** Very Weak - Avoid or short candidates

---

### 3. STYLE-SPECIFIC CONTEXTS

#### 3A. INTRADAY CONTEXT

**Response Time:** <1s  
**Optimized For:** Day traders, scalpers, high-frequency recommendation systems

**Key Features:**

```json
{
  "intraday_context": {
    "market_phase": "Mid-session",   // Opening/Mid-session/Closing
    "time_remaining_minutes": 180,
    "current_momentum": "bullish",
    "momentum_shift": "stable",      // accelerating/stable/decelerating
    "intraday_volatility": "normal",
    
    // VWAP Analysis
    "volume_weighted_price": "19630",
    "current_vs_vwap": "0.3",        // % above/below VWAP
    
    // Pivot Points for Scalping
    "pivot_point": "19600",
    "r1": "19650", "r2": "19700",    // Resistance levels
    "s1": "19550", "s2": "19500",    // Support levels
    
    // Trading Opportunities
    "breakout_candidates": ["RELIANCE", "TCS"],
    "reversal_candidates": ["HDFC", "ICICI"],
    
    // Risk Factors
    "news_driven_volatility": false,
    "high_impact_events_today": []
  }
}
```

**How to Use for ML Features:**
```python
# Example feature engineering for intraday model
features = {
    'market_phase_encoded': encode_phase(intraday_context.market_phase),
    'time_to_close': intraday_context.time_remaining_minutes / 375,  # Normalize
    'momentum_score': momentum_to_score(intraday_context.current_momentum),
    'price_vs_vwap': float(intraday_context.current_vs_vwap) / 100,
    'volatility_level': volatility_to_numeric(intraday_context.intraday_volatility),
    'near_pivot': abs(current_price - intraday_context.pivot_point) < threshold
}
```

#### 3B. SWING CONTEXT

**Response Time:** <1s  
**Optimized For:** Swing traders, position traders, multi-day strategies

**Key Features:**

```json
{
  "swing_context": {
    "multi_day_trend": "uptrend",    // 5-day trend
    "trend_strength": "moderate",
    "trend_age_days": 12,            // Trend duration
    
    // Pattern Recognition
    "chart_patterns": ["Bull flag on Nifty", "Cup and handle on Bank Nifty"],
    
    // Key Levels
    "swing_support_levels": ["19400", "19200", "19000"],
    "swing_resistance_levels": ["19800", "20000", "20200"],
    
    // Sector Rotation
    "hot_sectors": ["IT", "Pharma", "Auto"],
    "cold_sectors": ["Metals", "Realty"],
    "rotating_sectors": ["FMCG", "Energy"],
    
    // Mean Reversion Opportunities
    "oversold_stocks": ["AXISBANK", "TATAMOTORS"],
    "overbought_stocks": ["ASIANPAINT", "TITAN"],
    
    // Risk Management
    "risk_level": "medium",
    "stop_loss_suggestion": "3-5% trailing stop loss recommended"
  }
}
```

**How to Use for ML Features:**
```python
# Example feature engineering for swing model
features = {
    'trend_direction': 1 if swing_context.multi_day_trend == "uptrend" else -1,
    'trend_strength_score': strength_to_score(swing_context.trend_strength),
    'trend_maturity': swing_context.trend_age_days / 30,  # Normalize
    'hot_sector_count': len(swing_context.hot_sectors),
    'sector_rotation_active': len(swing_context.rotating_sectors) > 0,
    'risk_level_numeric': risk_to_numeric(swing_context.risk_level)
}
```

#### 3C. LONG-TERM CONTEXT

**Response Time:** <1s  
**Optimized For:** Investors, portfolio managers, fundamental-based systems

**Key Features:**

```json
{
  "long_term_context": {
    // Macro Environment
    "economic_cycle": "expansion",
    "interest_rate_trend": "stable",
    "inflation_trend": "falling",
    
    // Market Valuation
    "nifty_pe": "22.5",
    "nifty_pb": "3.8",
    "market_valuation": "fair",     // overvalued/fair/undervalued
    
    // Structural Themes
    "emerging_themes": [
      "Digital transformation",
      "Green energy",
      "Make in India"
    ],
    "declining_themes": [
      "Legacy retail",
      "Traditional telecom"
    ],
    
    // Sector Allocation
    "recommended_sector_weights": {
      "IT": "18",
      "Banking": "15",
      "Auto": "12"
    },
    
    // Investment Opportunities
    "value_opportunities": ["L&T", "SBI"],
    "growth_opportunities": ["INFY", "HDFCBANK"],
    "dividend_opportunities": ["ITC", "COALINDIA"],
    
    // Risk Assessment
    "systemic_risk_level": "low",
    "key_risks": [
      "Global slowdown",
      "Oil price volatility",
      "Election uncertainty"
    ]
  }
}
```

---

## 🤖 Using as ML Features

### Example Integration for Trading Recommendation System

```python
import requests
import pandas as pd

def get_market_context_features(trading_style="intraday"):
    """
    Fetch hierarchical market context and convert to ML features.
    """
    response = requests.post(
        "http://127.0.0.1:8079/api/analysis/context/enhanced",
        json={
            "include_primary": True,
            "include_detailed": True,
            "include_style_specific": True,
            "trading_styles": [trading_style],
            "include_sectors": True,
            "include_technicals": True,
            "include_opportunities": True
        }
    )
    
    context = response.json()
    
    # PRIMARY LEVEL FEATURES (Always fast, baseline context)
    primary_features = {
        'market_score': context['primary_context']['overall_market_score'] / 100,
        'market_confidence': context['primary_context']['market_confidence'],
        'global_trend': 1 if context['primary_context']['global_context']['overall_trend'] == 'bullish' else -1,
        'risk_appetite': 1 if context['primary_context']['global_context']['risk_on_off'] == 'risk_on' else -1,
        'nifty_change': float(context['primary_context']['indian_context']['nifty_change']),
        'advance_decline_ratio': float(context['primary_context']['indian_context']['advance_decline_ratio'])
    }
    
    # DETAILED LEVEL FEATURES (Rich context for better decisions)
    detailed_features = {}
    if context.get('detailed_context'):
        nifty = context['detailed_context']['nifty_analysis']
        detailed_features = {
            'rsi_14': float(nifty['technicals']['rsi_14']) / 100,
            'macd_bullish': 1 if nifty['technicals']['macd_signal'] == 'bullish_crossover' else 0,
            'volume_vs_avg': float(nifty['technicals']['volume_vs_avg']) / 100,
            'stocks_above_sma20': nifty['stocks_above_sma20'] / 100,
            'put_call_ratio': float(nifty['put_call_ratio']),
            'market_breadth': (context['detailed_context']['advances'] - 
                             context['detailed_context']['declines']) / 
                             (context['detailed_context']['advances'] + 
                              context['detailed_context']['declines'])
        }
        
        # Sector features
        for sector in context['detailed_context']['sectors']:
            detailed_features[f"sector_{sector['sector_name'].lower()}_strength"] = sector['strength_score'] / 100
    
    # STYLE-SPECIFIC FEATURES
    style_features = {}
    if trading_style == "intraday" and context.get('intraday_context'):
        intraday = context['intraday_context']
        style_features = {
            'time_to_close_pct': intraday['time_remaining_minutes'] / 375,
            'price_vs_vwap': float(intraday['current_vs_vwap']) / 100,
            'intraday_momentum': momentum_to_score(intraday['current_momentum']),
            'volatility_high': 1 if intraday['intraday_volatility'] in ['high', 'very_high'] else 0
        }
    
    # Combine all features
    all_features = {**primary_features, **detailed_features, **style_features}
    
    return pd.DataFrame([all_features])

# Use in trading system
def make_trading_decision(stock_symbol, stock_features):
    """
    Combine stock features with market context for recommendation.
    """
    # Get market context features
    market_features = get_market_context_features(trading_style="intraday")
    
    # Combine with stock-specific features
    combined_features = pd.concat([stock_features, market_features], axis=1)
    
    # Feed to ML model
    prediction = model.predict(combined_features)
    
    return {
        'action': prediction,
        'market_score': market_features['market_score'].values[0],
        'confidence': market_features['market_confidence'].values[0]
    }
```

---

## 📈 Use Cases & Examples

### Use Case 1: Real-Time Intraday Stock Screener

```python
# Get intraday context
context = get_market_context(trading_styles=["intraday"])

# Filter stocks based on market conditions
if context['intraday_context']['current_momentum'] == 'bullish':
    # Look for breakout candidates
    candidates = context['intraday_context']['breakout_candidates']
    
    # Check if we're in favorable market phase
    if context['intraday_context']['market_phase'] != 'Closing':
        # Screen these stocks for entry
        for stock in candidates:
            if is_near_breakout(stock) and context['primary_context']['overall_market_score'] > 30:
                generate_buy_signal(stock)
```

### Use Case 2: Swing Trading with Sector Rotation

```python
# Get swing context
context = get_market_context(trading_styles=["swing"])

# Identify sector rotation opportunities
hot_sectors = context['swing_context']['hot_sectors']
rotating_sectors = context['swing_context']['rotating_sectors']

# Build watchlist from strong sectors
for sector in hot_sectors:
    if sector in rotating_sectors:
        # Early stage rotation - high potential
        watchlist.add_sector_stocks(sector, rank='high')
    else:
        # Established momentum - moderate potential
        watchlist.add_sector_stocks(sector, rank='medium')

# Avoid weak sectors
for sector in context['swing_context']['cold_sectors']:
    watchlist.remove_sector_stocks(sector)
```

### Use Case 3: Long-Term Portfolio Rebalancing

```python
# Get long-term context
context = get_market_context(trading_styles=["long_term"])

# Check macro environment
if context['long_term_context']['economic_cycle'] == 'expansion':
    # Favor growth and cyclicals
    recommended_allocation = context['long_term_context']['recommended_sector_weights']
    
    # Identify emerging themes
    for theme in context['long_term_context']['emerging_themes']:
        # Find stocks aligned with theme
        theme_stocks = find_stocks_by_theme(theme)
        portfolio.add_theme_allocation(theme, theme_stocks)
    
    # Exit declining themes
    for theme in context['long_term_context']['declining_themes']:
        portfolio.reduce_theme_exposure(theme)
```

---

## 🎛️ Configuration Options

### Request Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `include_primary` | boolean | `true` | Include primary context (recommended: always true) |
| `include_detailed` | boolean | `true` | Include detailed analysis |
| `include_style_specific` | boolean | `true` | Include trading style contexts |
| `trading_styles` | array | `["all"]` | Which styles: "intraday", "swing", "long_term", "all" |
| `focus_symbols` | array | `null` | Specific stocks for detailed analysis (max 10) |
| `include_sectors` | boolean | `true` | Include sector performance |
| `include_technicals` | boolean | `true` | Include technical indicators |
| `include_opportunities` | boolean | `true` | Include trading opportunities |

### Response Metadata

| Field | Description |
|-------|-------------|
| `context_quality_score` | Quality of data (0.0-1.0), higher is better |
| `data_freshness_seconds` | Age of data in seconds (real-time = 0) |
| `processing_time_ms` | API response time in milliseconds |
| `warnings` | Any data quality warnings |

---

## ⚡ Performance Guidelines

### Response Times by Configuration

| Configuration | Expected Time | Use Case |
|--------------|---------------|----------|
| Primary only | <100ms | Quick sentiment check, fast ML |
| Primary + Detailed | <500ms | Comprehensive analysis |
| All contexts (1 style) | <1s | Style-specific optimization |
| All contexts (all styles) | <2s | Full market understanding |

### Best Practices

1. **Start with Primary:** Always fetch primary context first for baseline
2. **Cache Appropriately:** 
   - Primary: Cache for 30-60 seconds
   - Detailed: Cache for 2-5 minutes
   - Long-term: Cache for 15-30 minutes
3. **Parallel Requests:** Fetch stock data and context in parallel
4. **Selective Loading:** Only request contexts you need for your trading style

---

## 🔄 Real-Time Update Strategy

```python
class MarketContextManager:
    """Manage market context with intelligent caching."""
    
    def __init__(self):
        self.cache = {}
        self.cache_ttl = {
            'primary': 60,      # 1 minute
            'detailed': 180,    # 3 minutes
            'intraday': 120,    # 2 minutes
            'swing': 300,       # 5 minutes
            'long_term': 1800   # 30 minutes
        }
    
    def get_context(self, trading_style, force_refresh=False):
        """Get context with intelligent caching."""
        cache_key = f"context_{trading_style}"
        
        if not force_refresh and cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            age = (datetime.now() - timestamp).total_seconds()
            
            if age < self.cache_ttl.get(trading_style, 180):
                return cached_data
        
        # Fetch fresh data
        context = fetch_enhanced_context(trading_style)
        self.cache[cache_key] = (context, datetime.now())
        
        return context
```

---

## 📊 Feature Importance for ML Models

Based on our testing with trading recommendation models:

### High Impact Features (Top 20%)
1. **overall_market_score** - Single strongest predictor
2. **market_confidence** - Quality of signal
3. **nifty_change** - Direct market momentum
4. **rsi_14** - Overbought/oversold conditions
5. **market_breadth** - Advance/decline ratio

### Medium Impact Features (60%)
6. Sector strength scores
7. Volume vs average
8. Technical indicators (MACD, Bollinger)
9. Support/resistance proximity
10. Trend strength and age

### Context Features (20%)
11. Market regime
12. Risk appetite
13. Volatility level
14. Time-based features (market phase, time to close)

---

## 🚨 Error Handling

```python
def safe_context_fetch(trading_style):
    """Fetch context with fallback handling."""
    try:
        response = requests.post(
            "http://127.0.0.1:8079/api/analysis/context/enhanced",
            json={"trading_styles": [trading_style]},
            timeout=5
        )
        
        data = response.json()
        
        # Check quality score
        if data['context_quality_score'] < 0.5:
            logger.warning(f"Low quality context: {data['warnings']}")
        
        return data
        
    except requests.Timeout:
        logger.error("Context fetch timeout, using cached data")
        return get_cached_context()
    
    except Exception as e:
        logger.error(f"Context fetch failed: {e}")
        return get_default_context()
```

---

## 📚 Further Reading

- [API Consolidation Guide](./API_CONSOLIDATION_COMPLETE.md)
- [Unified API Guide](./UNIFIED_API_GUIDE.md)
- [ML Market Intelligence](./V3_ML_MARKET_INTELLIGENCE_API_GUIDE.md)

---

**Last Updated:** October 13, 2025  
**API Version:** 2.0  
**Status:** ✅ Production Ready

