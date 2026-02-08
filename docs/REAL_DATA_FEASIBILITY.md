# Real Data Feasibility Analysis for Enhanced Market Context

**Date:** October 13, 2025  
**Status:** Analysis Complete

---

## 🎯 Objective

Replace mock data in `/api/analysis/context/enhanced` with real market data from:
1. **Kite Connect API** - Indian market data
2. **Yahoo Finance API** - Global indices and fundamentals

---

## 📊 Data Requirements vs Availability

### PRIMARY CONTEXT

| Required Data | Source | Availability | API Call Cost | Feasibility |
|--------------|--------|--------------|---------------|-------------|
| **Global Market Sentiment** |
| US markets change (S&P500, NASDAQ, DOW) | Yahoo Finance | ✅ Available | 1 call (batch) | ✅ HIGH |
| Asia markets change (Nikkei, Hang Seng) | Yahoo Finance | ✅ Available | Included above | ✅ HIGH |
| Europe markets change (FTSE, DAX) | Yahoo Finance | ✅ Available | Included above | ✅ HIGH |
| **Indian Market Data** |
| Nifty/Sensex/BankNifty change | Kite Connect | ✅ Available | 1 call (batch) | ✅ HIGH |
| Advance/Decline ratio | Kite Connect | ⚠️ Calculated | 1 call (breadth) | ⚠️ MEDIUM |
| Support/Resistance levels | Calculated | ✅ Derivable | 0 (from price) | ✅ HIGH |

**Primary Context Feasibility:** ✅ **HIGH** - All data available with 2-3 API calls

---

### DETAILED CONTEXT

| Required Data | Source | Availability | API Call Cost | Feasibility |
|--------------|--------|--------------|---------------|-------------|
| **Technical Indicators** |
| RSI, MACD, Bollinger Bands | Calculated | ✅ Derivable | 1 call (OHLC) | ✅ HIGH |
| Moving Averages (20/50/200) | Calculated | ✅ Derivable | Included above | ✅ HIGH |
| **Sector Performance** |
| Sector-wise changes | Kite Connect | ⚠️ Limited | Multiple calls | ⚠️ MEDIUM |
| Top gainers/losers per sector | Kite Connect | ✅ Available | 1-2 calls | ✅ HIGH |
| **Market Breadth** |
| Advances/Declines/Unchanged | Kite Connect | ⚠️ Calculated | 1 call | ⚠️ MEDIUM |
| New 52-week highs/lows | Kite Connect | ⚠️ Calculated | Heavy | ❌ LOW |
| **Options Data** |
| Put/Call Ratio | Kite Connect | ✅ Available | 1 call | ✅ HIGH |
| FII/DII Activity | External | ❌ Not available | N/A | ❌ LOW |

**Detailed Context Feasibility:** ⚠️ **MEDIUM** - Core data available, some calculated fields

---

### INTRADAY CONTEXT

| Required Data | Source | Availability | API Call Cost | Feasibility |
|--------------|--------|--------------|---------------|-------------|
| **Real-Time Momentum** |
| Current price & momentum | Kite Connect | ✅ Available | 1 call (quote) | ✅ HIGH |
| VWAP | Calculated | ✅ Derivable | 1 call (ticks) | ⚠️ MEDIUM |
| **Pivot Points** |
| Pivot/R1/R2/S1/S2 | Calculated | ✅ Derivable | 0 (from OHLC) | ✅ HIGH |
| **Breakout Candidates** |
| Stocks near breakout | Calculated | ⚠️ Complex | Multiple calls | ⚠️ MEDIUM |

**Intraday Context Feasibility:** ⚠️ **MEDIUM** - Basic data easy, advanced features complex

---

### SWING CONTEXT

| Required Data | Source | Availability | API Call Cost | Feasibility |
|--------------|--------|--------------|---------------|-------------|
| **Multi-Day Trends** |
| 5-day trend analysis | Calculated | ✅ Derivable | 1 call (historical) | ✅ HIGH |
| Trend strength | Calculated | ✅ Derivable | Included above | ✅ HIGH |
| **Sector Rotation** |
| Hot/cold sectors | Yahoo Finance | ✅ Available | 1 call | ✅ HIGH |
| **Mean Reversion** |
| Oversold/overbought stocks | Calculated | ⚠️ Complex | Multiple calls | ⚠️ MEDIUM |

**Swing Context Feasibility:** ✅ **HIGH** - Most data readily available

---

### LONG-TERM CONTEXT

| Required Data | Source | Availability | API Call Cost | Feasibility |
|--------------|--------|--------------|---------------|-------------|
| **Macro Data** |
| Economic cycle | External | ❌ Manual | N/A | ❌ LOW |
| Interest rates | External | ✅ Manual entry | 0 | ⚠️ MEDIUM |
| Inflation | External | ✅ Manual entry | 0 | ⚠️ MEDIUM |
| **Valuation** |
| Nifty P/E, P/B | Yahoo Finance | ✅ Available | 1 call | ✅ HIGH |
| **Themes** |
| Emerging/Declining themes | Manual | ❌ Curated | N/A | ❌ LOW |

**Long-Term Context Feasibility:** ⚠️ **MEDIUM** - Mix of API data and manual curation

---

## 🚨 API Rate Limit Analysis

### Kite Connect API Limits
- **Rate Limit:** 3 requests/second
- **Daily Limit:** Unlimited (within rate limit)
- **WebSocket:** Real-time data available

### Yahoo Finance API Limits
- **Rate Limit:** ~60 requests/minute (unofficial)
- **Daily Limit:** ~2000 requests/day
- **Cost:** Free

### Enhanced Context API Call Requirements

| Context Level | Min API Calls | Max API Calls | Time (Sequential) | Time (Parallel) |
|--------------|---------------|---------------|-------------------|-----------------|
| Primary Only | 2 | 3 | ~700ms | ~350ms |
| Primary + Detailed | 5 | 8 | ~2.5s | ~800ms |
| All Contexts (1 style) | 8 | 12 | ~4s | ~1.2s |
| All Contexts (all styles) | 12 | 18 | ~6s | ~2s |

**Conclusion:** With parallel API calls, targets are achievable ✅

---

## ✅ Recommended Implementation Strategy

### Phase 1: PRIMARY CONTEXT (HIGH Priority)

**Implement immediately with real data:**

```python
async def _generate_primary_context_real(market_service, intelligence_service):
    # 1. Get global indices from Yahoo Finance (1 call, batch)
    global_indices = await yahoo_service.get_market_indices()
    
    # 2. Get Indian indices from Kite Connect (1 call, batch)
    indian_quotes = await kite_client.quote([
        "NSE:NIFTY 50", "NSE:NIFTY BANK", "NSE:SENSEX"
    ])
    
    # 3. Calculate metrics
    global_context = calculate_global_sentiment(global_indices)
    indian_context = calculate_indian_sentiment(indian_quotes)
    market_score = calculate_overall_score(global_context, indian_context)
    
    return PrimaryMarketContext(...)
```

**API Calls:** 2 (parallel)  
**Response Time:** ~350ms  
**Feasibility:** ✅ **HIGH**

---

### Phase 2: DETAILED CONTEXT (MEDIUM Priority)

**Implement with calculated technicals:**

```python
async def _generate_detailed_context_real(market_service, intelligence_service):
    # 1. Get Nifty historical data for technicals (1 call)
    nifty_candles = await kite_client.historical_data(
        "NSE:NIFTY 50", from_date, to_date, "day"
    )
    
    # 2. Calculate technical indicators
    technicals = calculate_technicals(nifty_candles)  # RSI, MACD, MA, Bollinger
    
    # 3. Get sector performance from Yahoo (1 call)
    sectors = await yahoo_service.get_sector_performance()
    
    # 4. Get market breadth (simplified - use available data)
    breadth = await get_simplified_market_breadth()
    
    return DetailedMarketContext(...)
```

**API Calls:** 3-4 (parallel)  
**Response Time:** ~800ms  
**Feasibility:** ✅ **HIGH** (with simplifications)

---

### Phase 3: STYLE-SPECIFIC CONTEXTS (Prioritized)

#### A. INTRADAY (HIGH Priority - Most Requested)

```python
async def _generate_intraday_context_real(...):
    # 1. Get real-time quotes (1 call)
    quotes = await kite_client.quote(["NSE:NIFTY 50"])
    
    # 2. Calculate pivot points from today's OHLC
    pivots = calculate_pivot_points(quotes['NSE:NIFTY 50'])
    
    # 3. Get VWAP (if available from WebSocket, else approximate)
    vwap = approximate_vwap(quotes) if not websocket_data else websocket_vwap
    
    # 4. Momentum from price action
    momentum = calculate_momentum(quotes, previous_quotes)
    
    return IntradayContext(...)
```

**API Calls:** 2-3  
**Response Time:** ~500ms  
**Feasibility:** ✅ **HIGH**

#### B. SWING (MEDIUM Priority)

```python
async def _generate_swing_context_real(...):
    # 1. Get 5-10 day historical data (1 call)
    historical = await kite_client.historical_data(...)
    
    # 2. Analyze multi-day trend
    trend = analyze_multi_day_trend(historical)
    
    # 3. Get sector performance (reuse from detailed)
    sectors = cached_sector_performance or await fetch_sectors()
    
    # 4. Identify oversold/overbought (simplified)
    opportunities = identify_opportunities_simplified(historical, sectors)
    
    return SwingContext(...)
```

**API Calls:** 2-3 (some cached)  
**Response Time:** ~600ms  
**Feasibility:** ✅ **HIGH**

#### C. LONG-TERM (LOW Priority - Less Frequent)

```python
async def _generate_long_term_context_real(...):
    # 1. Get Nifty fundamentals from Yahoo (1 call)
    nifty_info = await yahoo_service.get_stock_data("^NSEI")
    
    # 2. Extract P/E, P/B
    pe = nifty_info.pe_ratio
    pb = nifty_info.fundamentals.get('priceToBook')
    
    # 3. Use config for macro data (rates, inflation)
    macro = get_macro_config()  # From settings/config file
    
    # 4. Use predefined themes (from config)
    themes = get_market_themes_config()
    
    return LongTermContext(...)
```

**API Calls:** 1-2  
**Response Time:** ~400ms  
**Feasibility:** ✅ **HIGH** (with config-based macro data)

---

## 🎯 Simplifications for Feasibility

### What to Simplify

1. **Market Breadth:** Use available data, don't calculate all 2000+ stocks
   ```python
   # Instead of: All NSE stocks
   # Use: Nifty 50 + Nifty Next 50 (100 stocks)
   simplified_breadth = calculate_breadth_nifty_universe()
   ```

2. **Breakout Candidates:** Use pre-defined watchlist
   ```python
   # Instead of: Scanning all stocks
   # Use: Predefined watchlist of liquid stocks
   watchlist = get_liquid_stocks_watchlist()  # 50-100 stocks
   breakout_candidates = scan_watchlist_for_breakouts(watchlist)
   ```

3. **Sector Analysis:** Use Yahoo Finance sectors (simpler)
   ```python
   # Yahoo Finance has pre-calculated sector performance
   sectors = await yahoo_service.get_sector_performance()
   ```

4. **FII/DII Data:** Use last available or manual entry
   ```python
   # FII/DII data is published daily, not real-time
   fii_dii = get_latest_fii_dii_data()  # From daily update
   ```

5. **Economic Cycle:** Use config-based assessment
   ```python
   # Economic cycle changes slowly, can be config
   economic_cycle = settings.macro.economic_cycle  # Updated monthly
   ```

### What NOT to Simplify

1. **Primary Context:** Keep 100% real-time
2. **Technical Indicators:** Calculate accurately
3. **Intraday Momentum:** Keep real-time
4. **Pivot Points:** Calculate accurately

---

## 📦 Caching Strategy

### Cache TTLs by Data Type

| Data Type | TTL | Rationale |
|-----------|-----|-----------|
| Global indices | 1 minute | Changes slowly |
| Indian quotes | 30 seconds | Moderately volatile |
| Sector performance | 5 minutes | Changes slowly |
| Technical indicators | 5 minutes | Based on historical data |
| Intraday momentum | 10 seconds | Real-time critical |
| Swing trends | 1 hour | Multi-day analysis |
| Long-term metrics | 24 hours | Rarely changes |

### Cache Implementation

```python
from functools import lru_cache
from datetime import datetime, timedelta

class CachedContextData:
    def __init__(self):
        self.cache = {}
        self.cache_times = {}
    
    async def get_or_fetch(self, key, fetch_fn, ttl_seconds):
        now = datetime.now()
        
        if key in self.cache:
            cache_time = self.cache_times[key]
            if (now - cache_time).total_seconds() < ttl_seconds:
                return self.cache[key]
        
        # Fetch fresh data
        data = await fetch_fn()
        self.cache[key] = data
        self.cache_times[key] = now
        
        return data
```

---

## 💰 Cost Analysis

### API Call Costs (Per Enhanced Context Request)

| Context Configuration | Kite API Calls | Yahoo API Calls | Total Calls | Cost |
|----------------------|----------------|-----------------|-------------|------|
| Primary only | 1 | 1 | 2 | ✅ FREE |
| Primary + Detailed | 2-3 | 2 | 4-5 | ✅ FREE |
| All contexts | 4-6 | 2-3 | 6-9 | ✅ FREE |

**Daily Usage Estimate:**
- Trading hours: 6.25 hours = 375 minutes
- Context refresh rate: Every 1 minute (primary), 5 minutes (detailed)
- Primary calls/day: 375 × 2 = **750 calls**
- Detailed calls/day: 75 × 5 = **375 calls**
- **Total: ~1,125 API calls/day**

**Within Limits:**
- Kite: ✅ 3 calls/sec = 64,800 calls/day available
- Yahoo: ✅ 2,000 calls/day limit

---

## ✅ Final Recommendation

### Phase 1: Implement Now (Week 1)
- ✅ PRIMARY CONTEXT with real data
- ✅ INTRADAY CONTEXT with real data
- ✅ Basic caching layer

### Phase 2: Enhance (Week 2)
- ✅ DETAILED CONTEXT with calculated technicals
- ✅ SWING CONTEXT with real data
- ✅ Advanced caching with TTLs

### Phase 3: Polish (Week 3)
- ✅ LONG-TERM CONTEXT with mixed real + config data
- ✅ Optimize parallel API calls
- ✅ Add fallback mechanisms

### Not Implementing (Low ROI)
- ❌ Full market breadth (2000+ stocks) - Use Nifty universe
- ❌ Real-time FII/DII - Use daily data
- ❌ Economic cycle detection - Use config/manual entry
- ❌ Automated theme identification - Use curated list

---

## 🎯 Success Criteria

1. ✅ Primary context responds in <500ms with real data
2. ✅ All contexts respond in <2s with real data
3. ✅ Cache hit rate > 60% during trading hours
4. ✅ API rate limits never exceeded
5. ✅ Graceful degradation if APIs fail

---

**Conclusion:** ✅ **HIGHLY FEASIBLE** with smart simplifications and caching!

**Next Steps:** Implement Phase 1 (PRIMARY + INTRADAY contexts) immediately.

