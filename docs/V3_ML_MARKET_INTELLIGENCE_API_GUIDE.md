# V3 ML Market Intelligence API - Integration Guide

## 🧠 Overview

The V3 ML Market Intelligence API provides **self-explanatory, actionable market context** specifically designed for machine learning systems and automated trading decisions. Every data point includes clear trading implications and confidence scores.

## 🎯 Perfect For

- **ML Model Training** - Features ready for direct model consumption
- **Automated Trading Systems** - Clear buy/sell/hold signals
- **Risk Management** - Volatility regimes and risk assessments
- **Portfolio Management** - Sector rotation and allocation signals

---

## 📊 API Endpoints

### 1. Complete Market Intelligence
```
GET /api/v3/market-intelligence?horizon={intraday|swing|long_term}
```

**Returns comprehensive market analysis with:**
- Indian market intelligence (NIFTY 50, Banking)
- Global market context (S&P 500, NASDAQ, Dow)
- Sector leadership and rotation signals
- Volatility regime and risk environment
- Key trading levels with breakout analysis
- ML-ready numerical features

### 2. ML Features Only
```
GET /api/v3/market-intelligence/features-only?horizon={intraday|swing|long_term}
```

**Returns numerical features for direct ML consumption:**
- Trend strength scores (0-5 scale)
- Momentum strength scores (0-5 scale)
- Volatility regime scores (1-5 scale)
- Trading environment score (0-100)

---

## 🔧 Integration Examples

### Python Integration

```python
import requests
import json

# Basic usage
def get_market_intelligence(horizon="swing"):
    url = f"http://localhost:8079/api/v3/market-intelligence?horizon={horizon}"
    response = requests.get(url)
    return response.json()

# Get ML features for model input
def get_ml_features(horizon="swing"):
    url = f"http://localhost:8079/api/v3/market-intelligence/features-only?horizon={horizon}"
    response = requests.get(url)
    data = response.json()
    return data['ml_features']

# Example usage
market_data = get_market_intelligence("long_term")
ml_features = get_ml_features("swing")

# Extract trading signals
nifty_trend = market_data['nifty_intelligence']['primary_trend']
momentum_signal = market_data['nifty_intelligence']['momentum_condition']
sector_leaders = [s['sector_name'] for s in market_data['sector_leadership'][:3]]

print(f"NIFTY Trend: {nifty_trend}")
print(f"Momentum: {momentum_signal}")
print(f"Leading Sectors: {sector_leaders}")
```

### JavaScript Integration

```javascript
// Fetch market intelligence
async function getMarketIntelligence(horizon = 'swing') {
    const response = await fetch(`http://localhost:8079/api/v3/market-intelligence?horizon=${horizon}`);
    return await response.json();
}

// Get ML features for model input
async function getMLFeatures(horizon = 'swing') {
    const response = await fetch(`http://localhost:8079/api/v3/market-intelligence/features-only?horizon=${horizon}`);
    const data = await response.json();
    return data.ml_features;
}

// Example usage
const marketData = await getMarketIntelligence('long_term');
const mlFeatures = await getMLFeatures('swing');

// Extract actionable insights
const tradingScore = marketData.trading_environment_score;
const volatilityRegime = marketData.market_health.volatility_regime;
const sectorRotation = marketData.sector_rotation_signal;

console.log(`Trading Environment: ${tradingScore}/100`);
console.log(`Volatility: ${volatilityRegime}`);
console.log(`Sector Theme: ${sectorRotation}`);
```

---

## 📊 Response Model Structure

### Complete Market Intelligence Response

```json
{
  "analysis_horizon": "swing",
  "analysis_timestamp": "2025-09-21T15:37:32.767427",
  "data_freshness_minutes": 5,
  "trading_environment_score": 66.5,
  
  "nifty_intelligence": {
    "index_name": "NIFTY 50",
    "current_level": 25327.05,
    "daily_change_percent": -0.38,
    "period_change_percent": 0.94,
    "primary_trend": "bullish",
    "trend_confidence": 58.6,
    "momentum_condition": "extreme_overbought",
    "risk_level": "Low Risk",
    "key_observation": "Trend: Bullish | Momentum: Extreme Overbought",
    "trend_signals": [
      {
        "indicator_name": "Price vs 20-SMA Trend",
        "signal_strength": "bullish",
        "confidence_score": 58.6,
        "trading_implication": "Uptrend - consider long positions",
        "raw_value": 1.17
      }
    ],
    "momentum_signals": [
      {
        "indicator_name": "RSI Momentum",
        "momentum_signal": "extreme_overbought",
        "signal_strength": 90,
        "trading_implication": "Extremely overbought - high probability of reversal",
        "raw_value": 82.5
      }
    ]
  },
  
  "banking_intelligence": {
    "index_name": "NIFTY BANK",
    "current_level": 55458.85,
    "primary_trend": "bullish",
    "momentum_condition": "overbought",
    "key_observation": "Banking sector - Trend: Bullish | Momentum: Overbought"
  },
  
  "sector_leadership": [
    {
      "sector_name": "Metal",
      "performance_rank": 1,
      "period_return_percent": 7.98,
      "sector_momentum": "strong_bullish",
      "relative_strength": "Outperforming",
      "trading_recommendation": "Strong sector - consider overweight"
    },
    {
      "sector_name": "Auto",
      "performance_rank": 2,
      "period_return_percent": 5.06,
      "sector_momentum": "strong_bullish",
      "relative_strength": "Outperforming",
      "trading_recommendation": "Strong sector - consider overweight"
    }
  ],
  
  "sector_rotation_signal": "Cyclical Rotation - Economic optimism",
  
  "global_context": {
    "overall_global_sentiment": "Strong Risk-On",
    "sentiment_confidence": 90,
    "global_risk_appetite": "High Risk Appetite - Favor growth assets",
    "currency_impact": "USD weakness likely - positive for Indian markets"
  },
  
  "market_health": {
    "volatility_regime": "extreme_calm",
    "volatility_trend": "Stable",
    "risk_environment": "Very Low Risk - Favorable for aggressive strategies"
  },
  
  "key_trading_levels": {
    "index_name": "NIFTY 50",
    "current_price": 25327.05,
    "pivot_point": 25175.85,
    "immediate_support": 24902.75,
    "immediate_resistance": 25600.15,
    "price_position": "Above pivot - bullish bias",
    "breakout_potential": "Watch for resistance break",
    "all_support_levels": [24902.75, 24478.45, 24205.35],
    "all_resistance_levels": [25600.15, 25873.25, 26297.55]
  },
  
  "ml_features_summary": {
    "nifty_trend_strength": 4.0,
    "nifty_momentum_strength": 0.0,
    "nifty_period_return": 0.94,
    "banking_trend_strength": 4.0,
    "banking_period_return": -2.62,
    "global_sentiment_confidence": 90.0,
    "volatility_regime_score": 1.0
  }
}
```

### ML Features Only Response

```json
{
  "horizon": "swing",
  "timestamp": "2025-09-21T15:37:32.767427",
  "ml_features": {
    "nifty_trend_strength": 4.0,
    "nifty_momentum_strength": 0.0,
    "nifty_period_return": 0.94,
    "banking_trend_strength": 4.0,
    "banking_period_return": -2.62,
    "global_sentiment_confidence": 90.0,
    "volatility_regime_score": 1.0
  },
  "trading_environment_score": 66.5,
  "data_quality": {
    "nifty_data_available": true,
    "global_data_available": true,
    "sector_data_available": true,
    "data_freshness_minutes": 5
  }
}
```

---

## 🎯 Trading Horizon Guide

### Intraday (`horizon=intraday`)
- **Use Case**: Same-day trades, scalping, day trading
- **Data Period**: 5 days of historical data
- **Indicators**: Short-term moving averages (5/20), fast RSI
- **Best For**: Quick entry/exit decisions

### Swing (`horizon=swing`)
- **Use Case**: Multi-day trades, 2-10 day positions
- **Data Period**: 2 months of historical data
- **Indicators**: Medium-term moving averages (20/50), standard RSI
- **Best For**: Trend following, momentum strategies

### Long-term (`horizon=long_term`)
- **Use Case**: Position trades, weeks to months
- **Data Period**: 1 year of historical data
- **Indicators**: Long-term moving averages (50/200), extended RSI
- **Best For**: Investment decisions, portfolio allocation

---

## 🔧 Field Explanations

### Trend Strength Values
- `5.0` - **Strong Bullish**: Very strong upward momentum
- `4.0` - **Bullish**: Moderate upward momentum
- `2.5` - **Neutral**: No clear direction
- `1.0` - **Bearish**: Moderate downward momentum
- `0.0` - **Strong Bearish**: Very strong downward momentum

### Momentum Signal Values
- `5.0` - **Extreme Oversold**: Strong buy signal
- `4.0` - **Oversold**: Potential buy opportunity
- `3.0` - **Bullish Momentum**: Positive momentum
- `2.5` - **Neutral Momentum**: No clear momentum
- `2.0` - **Bearish Momentum**: Negative momentum
- `1.0` - **Overbought**: Caution, potential reversal
- `0.0` - **Extreme Overbought**: Strong sell signal

### Volatility Regime Scores
- `1.0` - **Extreme Calm**: VIX < 12, very low risk
- `2.0` - **Low Volatility**: VIX 12-15, calm conditions
- `3.0` - **Moderate**: VIX 15-20, normal conditions
- `4.0` - **High Volatility**: VIX 20-25, elevated risk
- `5.0` - **Extreme Fear**: VIX > 25, high risk

### Trading Environment Score
- `80-100`: **Excellent** - All systems go, aggressive strategies
- `60-80`: **Good** - Favorable conditions, normal strategies
- `40-60`: **Neutral** - Mixed signals, cautious approach
- `20-40`: **Poor** - Unfavorable conditions, defensive strategies
- `0-20`: **Terrible** - High risk, capital preservation mode

---

## 🤖 ML Model Integration

### Feature Vector Creation

```python
def create_feature_vector(horizon="swing"):
    """Create feature vector for ML model input."""
    
    # Get ML features
    features_response = requests.get(
        f"http://localhost:8079/api/v3/market-intelligence/features-only?horizon={horizon}"
    ).json()
    
    ml_features = features_response['ml_features']
    
    # Create standardized feature vector
    feature_vector = [
        ml_features.get('nifty_trend_strength', 2.5),
        ml_features.get('nifty_momentum_strength', 2.5),
        ml_features.get('nifty_period_return', 0.0),
        ml_features.get('banking_trend_strength', 2.5),
        ml_features.get('banking_period_return', 0.0),
        ml_features.get('global_sentiment_confidence', 50.0),
        ml_features.get('volatility_regime_score', 3.0),
        features_response.get('trading_environment_score', 50.0)
    ]
    
    return feature_vector

# Example usage in ML pipeline
import numpy as np

features = create_feature_vector("swing")
features_array = np.array(features).reshape(1, -1)

# Ready for model prediction
# prediction = your_model.predict(features_array)
```

### Real-time Market Context for Trading Decisions

```python
def get_trading_context(horizon="swing"):
    """Get actionable trading context."""
    
    response = requests.get(
        f"http://localhost:8079/api/v3/market-intelligence?horizon={horizon}"
    ).json()
    
    # Extract key trading insights
    context = {
        'overall_bias': response['nifty_intelligence']['primary_trend'],
        'momentum_warning': response['nifty_intelligence']['momentum_condition'],
        'volatility_regime': response['market_health']['volatility_regime'],
        'sector_theme': response['sector_rotation_signal'],
        'risk_level': response['market_health']['risk_environment'],
        'trading_score': response['trading_environment_score'],
        
        # Key levels for entries/exits
        'support_level': response['key_trading_levels']['immediate_support'],
        'resistance_level': response['key_trading_levels']['immediate_resistance'],
        'price_position': response['key_trading_levels']['price_position'],
        
        # Sector allocation guidance
        'overweight_sectors': [
            s['sector_name'] for s in response['sector_leadership'][:3]
            if s['trading_recommendation'].startswith('Strong')
        ],
        'underweight_sectors': [
            s['sector_name'] for s in response['sector_leadership'][-3:]
            if 'Avoid' in s['trading_recommendation']
        ]
    }
    
    return context

# Usage example
context = get_trading_context("swing")

if context['overall_bias'] == 'bullish' and context['momentum_warning'] != 'extreme_overbought':
    print("✅ Favorable for long positions")
elif context['momentum_warning'] == 'extreme_overbought':
    print("⚠️ Caution: Overbought conditions")

if context['volatility_regime'] == 'extreme_calm':
    print("📈 Low risk - can increase position sizes")
```

---

## 🎯 Trading Strategy Integration

### Intraday Trading

```python
def intraday_signals():
    """Get intraday trading signals."""
    data = get_market_intelligence("intraday")
    
    signals = {
        'trend_bias': data['nifty_intelligence']['primary_trend'],
        'momentum_state': data['nifty_intelligence']['momentum_condition'],
        'volatility_regime': data['market_health']['volatility_regime'],
        'key_levels': {
            'support': data['key_trading_levels']['immediate_support'],
            'resistance': data['key_trading_levels']['immediate_resistance']
        }
    }
    
    # Trading logic
    if signals['trend_bias'] == 'bullish' and signals['momentum_state'] != 'extreme_overbought':
        return "LONG_BIAS"
    elif signals['trend_bias'] == 'bearish' and signals['momentum_state'] != 'extreme_oversold':
        return "SHORT_BIAS"
    else:
        return "NEUTRAL"
```

### Swing Trading

```python
def swing_strategy_signals():
    """Get swing trading strategy signals."""
    data = get_market_intelligence("swing")
    
    # Multi-factor analysis
    factors = {
        'nifty_trend': data['nifty_intelligence']['primary_trend'],
        'global_sentiment': data['global_context']['overall_global_sentiment'],
        'sector_rotation': data['sector_rotation_signal'],
        'volatility': data['market_health']['volatility_regime'],
        'trading_score': data['trading_environment_score']
    }
    
    # Strategy selection
    if factors['trading_score'] > 70:
        return "AGGRESSIVE_LONG"
    elif factors['trading_score'] > 50 and factors['nifty_trend'] == 'bullish':
        return "MODERATE_LONG"
    elif factors['trading_score'] < 30:
        return "DEFENSIVE"
    else:
        return "NEUTRAL"
```

### Portfolio Allocation

```python
def get_sector_allocation():
    """Get sector allocation recommendations."""
    data = get_market_intelligence("long_term")
    
    allocation = {
        'overweight': [],
        'neutral': [],
        'underweight': []
    }
    
    for sector in data['sector_leadership']:
        if 'overweight' in sector['trading_recommendation'].lower():
            allocation['overweight'].append({
                'sector': sector['sector_name'],
                'performance': sector['period_return_percent'],
                'momentum': sector['sector_momentum']
            })
        elif 'underweight' in sector['trading_recommendation'].lower():
            allocation['underweight'].append({
                'sector': sector['sector_name'],
                'performance': sector['period_return_percent']
            })
        else:
            allocation['neutral'].append(sector['sector_name'])
    
    return allocation
```

---

## 🔄 Real-time Integration

### WebSocket-Style Polling

```python
import time
import threading

class MarketIntelligenceMonitor:
    def __init__(self, update_interval=300):  # 5 minutes
        self.update_interval = update_interval
        self.current_intelligence = None
        self.callbacks = []
    
    def add_callback(self, callback):
        """Add callback for intelligence updates."""
        self.callbacks.append(callback)
    
    def start_monitoring(self):
        """Start monitoring market intelligence."""
        def monitor():
            while True:
                try:
                    new_data = get_market_intelligence("swing")
                    
                    # Check for significant changes
                    if self._has_significant_change(new_data):
                        self.current_intelligence = new_data
                        
                        # Notify all callbacks
                        for callback in self.callbacks:
                            callback(new_data)
                
                except Exception as e:
                    print(f"Monitor error: {e}")
                
                time.sleep(self.update_interval)
        
        thread = threading.Thread(target=monitor, daemon=True)
        thread.start()
    
    def _has_significant_change(self, new_data):
        """Check if there's a significant change worth notifying."""
        if not self.current_intelligence:
            return True
        
        # Check for trend changes
        old_trend = self.current_intelligence['nifty_intelligence']['primary_trend']
        new_trend = new_data['nifty_intelligence']['primary_trend']
        
        if old_trend != new_trend:
            return True
        
        # Check for momentum changes
        old_momentum = self.current_intelligence['nifty_intelligence']['momentum_condition']
        new_momentum = new_data['nifty_intelligence']['momentum_condition']
        
        if old_momentum != new_momentum:
            return True
        
        return False

# Usage
def on_market_change(data):
    print(f"🚨 Market Change: {data['nifty_intelligence']['primary_trend']}")
    print(f"📊 New Trading Score: {data['trading_environment_score']}")

monitor = MarketIntelligenceMonitor()
monitor.add_callback(on_market_change)
monitor.start_monitoring()
```

---

## 🚨 Error Handling

### Robust API Integration

```python
import requests
from typing import Optional, Dict

class MarketIntelligenceClient:
    def __init__(self, base_url="http://localhost:8079"):
        self.base_url = base_url
    
    def get_intelligence(self, horizon="swing", timeout=30) -> Optional[Dict]:
        """Get market intelligence with error handling."""
        try:
            response = requests.get(
                f"{self.base_url}/api/v3/market-intelligence",
                params={'horizon': horizon},
                timeout=timeout
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"API Error: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            print("⏰ API timeout - market data may be delayed")
            return None
        except requests.exceptions.ConnectionError:
            print("🔌 Connection error - service may be down")
            return None
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return None
    
    def get_ml_features_safe(self, horizon="swing") -> Dict:
        """Get ML features with safe defaults."""
        try:
            response = requests.get(
                f"{self.base_url}/api/v3/market-intelligence/features-only",
                params={'horizon': horizon},
                timeout=15
            )
            
            if response.status_code == 200:
                return response.json()['ml_features']
            else:
                # Return neutral defaults for ML models
                return {
                    'nifty_trend_strength': 2.5,
                    'nifty_momentum_strength': 2.5,
                    'nifty_period_return': 0.0,
                    'banking_trend_strength': 2.5,
                    'banking_period_return': 0.0,
                    'global_sentiment_confidence': 50.0,
                    'volatility_regime_score': 3.0
                }
                
        except Exception as e:
            print(f"❌ ML features error: {e}")
            # Return neutral defaults
            return {
                'nifty_trend_strength': 2.5,
                'nifty_momentum_strength': 2.5,
                'nifty_period_return': 0.0,
                'banking_trend_strength': 2.5,
                'banking_period_return': 0.0,
                'global_sentiment_confidence': 50.0,
                'volatility_regime_score': 3.0
            }

# Usage
client = MarketIntelligenceClient()
intelligence = client.get_intelligence("swing")
ml_features = client.get_ml_features_safe("swing")
```

---

## 📈 Performance Optimization

### Caching Strategy

```python
import time
from functools import lru_cache

class CachedMarketIntelligence:
    def __init__(self, cache_duration=300):  # 5 minutes
        self.cache_duration = cache_duration
        self.cache = {}
    
    def get_cached_intelligence(self, horizon):
        """Get cached intelligence or fetch new."""
        cache_key = f"intelligence_{horizon}"
        current_time = time.time()
        
        # Check cache
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if current_time - timestamp < self.cache_duration:
                return cached_data
        
        # Fetch new data
        new_data = get_market_intelligence(horizon)
        self.cache[cache_key] = (new_data, current_time)
        
        return new_data

# Usage
cached_client = CachedMarketIntelligence()
data = cached_client.get_cached_intelligence("swing")
```

---

## 🎯 Production Deployment

### Environment Configuration

```bash
# .env file for production
ENVIRONMENT=production
SERVICE_PORT=8079
LOG_LEVEL=INFO
DEBUG=false

# Kite Connect credentials
KITE_API_KEY=your_api_key
KITE_API_SECRET=your_api_secret
KITE_ACCESS_TOKEN=your_access_token

# CORS settings
CORS_ORIGINS=["http://localhost:3000", "https://your-trading-app.com"]
```

### Docker Deployment

```bash
# Build V3 container
docker build -f Dockerfile.v3-final -t kite-services-v3:latest .

# Deploy with proper configuration
docker run -d \
  --name kite-services-v3 \
  -p 8079:8079 \
  --env-file .env \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/data:/app/data \
  --restart unless-stopped \
  kite-services-v3:latest

# Health check
curl http://localhost:8079/health
```

---

## 🔍 Monitoring & Debugging

### Health Checks

```python
def check_api_health():
    """Comprehensive API health check."""
    try:
        # Basic health
        health = requests.get("http://localhost:8079/health").json()
        print(f"Service: {health['status']}")
        
        # Data quality check
        features = requests.get(
            "http://localhost:8079/api/v3/market-intelligence/features-only"
        ).json()
        
        data_quality = features['data_quality']
        print(f"NIFTY Data: {'✅' if data_quality['nifty_data_available'] else '❌'}")
        print(f"Global Data: {'✅' if data_quality['global_data_available'] else '❌'}")
        print(f"Sector Data: {'✅' if data_quality['sector_data_available'] else '❌'}")
        print(f"Data Freshness: {data_quality['data_freshness_minutes']} minutes")
        
    except Exception as e:
        print(f"❌ Health check failed: {e}")

# Usage
check_api_health()
```

---

## 🎯 Current Deployment Status

### ✅ Available Endpoints (Port 8079)

- **Health**: `GET /health`
- **V1 Basic**: `GET /api/market-context-data/quick-context`
- **V2 Enhanced**: `GET /api/v2/market-context?horizon={horizon}`
- **V3 ML Intelligence**: `GET /api/v3/market-intelligence?horizon={horizon}` ⭐
- **V3 ML Features**: `GET /api/v3/market-intelligence/features-only?horizon={horizon}` ⭐
- **Token Management**: `GET /api/token/status`, `POST /api/token/submit-token`
- **Documentation**: `GET /docs`

### 🎯 Recommended Integration

**For ML Systems**: Use V3 endpoints exclusively
- Primary: `/api/v3/market-intelligence`
- Features: `/api/v3/market-intelligence/features-only`

**For Simple Dashboards**: Use V2 endpoint
- Basic: `/api/v2/market-context`

---

## 🚀 Next Steps

1. **Integrate V3 API** into your recommendation system
2. **Train ML models** using the ML features endpoint
3. **Implement real-time monitoring** with polling or webhooks
4. **Add custom indicators** specific to your trading strategies
5. **Scale horizontally** with multiple API instances

---

**🎉 Your ML Market Intelligence Engine is ready for production use!**

The V3 API provides everything your recommendation system needs:
- ✅ Self-explanatory data model
- ✅ Professional technical analysis
- ✅ Clear trading implications
- ✅ ML-ready numerical features
- ✅ Real market data validation
- ✅ Database persistence for performance

**Perfect foundation for intelligent trading decisions! 🧠📈**

