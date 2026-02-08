# 📜 Data Contract V1 - API Schema Specification

**Version:** 1.0.0  
**Status:** ✅ STABLE - Production Ready  
**Created:** 2025-10-14  
**Breaking Changes:** None (initial version)

---

## 🎯 PURPOSE

This document defines the **IMMUTABLE** data contract for the Kite Trading Services API. This contract ensures:

1. **API Stability** - No breaking changes without version bump
2. **Type Safety** - All fields have strict types and validation
3. **Backward Compatibility** - Existing integrations never break
4. **Predictability** - Consumers know exactly what to expect

---

## 🔒 CONTRACT PRINCIPLES

### IMMUTABILITY RULES

1. **Field Names** - CANNOT be changed once released
2. **Field Types** - CANNOT be changed once released
3. **Validation Rules** - CANNOT be made stricter once released
4. **Enum Values** - CANNOT be removed once released
5. **Required Fields** - CANNOT become optional once released

### ALLOWED CHANGES IN V1.x

✅ **Allowed:**
- Adding NEW optional fields
- Adding NEW enum values (append only)
- Making validation LESS strict
- Adding NEW endpoints
- Improving documentation

❌ **NOT Allowed (Requires V2):**
- Removing fields
- Renaming fields
- Changing field types
- Removing enum values
- Making optional fields required
- Making validation stricter

---

## 📊 DATA TYPES & RANGES

### Numeric Ranges

| Field Type | Range | Example | Validation |
|------------|-------|---------|------------|
| `overall_market_score` | -100 to +100 | 38 | Integer, inclusive |
| `market_confidence` | 0.0 to 1.0 | 0.85 | Float, inclusive |
| `percentage_change` | -100.0 to +100.0 | -0.23 | Float, inclusive |
| `price` | > 0 | 25199.50 | Float, positive |
| `pe_ratio` | > 0 | 22.5 | Float, positive |
| `trend_age_days` | >= 0 | 15 | Integer, non-negative |
| `processing_time_ms` | >= 0 | 89.14 | Float, non-negative |

### Enum Types (IMMUTABLE)

#### MarketRegimeV1
```python
"bull_strong"    # Strong bullish trend
"bull_weak"      # Weak bullish trend
"sideways"       # No clear trend
"bear_weak"      # Weak bearish trend
"bear_strong"    # Strong bearish trend
```

#### TrendDirectionV1
```python
"bullish"   # Upward trend
"bearish"   # Downward trend
"neutral"   # No trend
"mixed"     # Mixed signals
```

#### VolatilityLevelV1
```python
"low"      # Low volatility
"medium"   # Medium volatility
"high"     # High volatility
```

#### RiskLevelV1
```python
"low"      # Low risk
"medium"   # Medium risk
"high"     # High risk
```

#### DataQualityV1
```python
"HIGH"     # >70% real data
"MEDIUM"   # 40-70% real data
"LOW"      # <40% real data
```

#### MarketValuationV1
```python
"undervalued"  # Market is undervalued
"fair"         # Market is fairly valued
"overvalued"   # Market is overvalued
```

#### EconomicCycleV1
```python
"expansion"     # Economic expansion
"peak"          # Economic peak
"contraction"   # Economic contraction
"trough"        # Economic trough
```

---

## 📋 SCHEMA DEFINITIONS

### MarketContextResponseV1 (Top-Level)

```json
{
  "success": true,                    // REQUIRED: boolean
  "contract_version": "1.0.0",        // REQUIRED: string
  "primary_context": {...},           // OPTIONAL: PrimaryMarketContextV1
  "intraday_context": {...},          // OPTIONAL: IntradayContextV1
  "swing_context": {...},             // OPTIONAL: SwingContextV1
  "long_term_context": {...},         // OPTIONAL: LongTermContextV1
  "data_quality": {...},              // OPTIONAL: DataQualityReportV1
  "context_quality_score": 0.85,      // REQUIRED: float (0.0-1.0)
  "processing_time_ms": 89.14,        // REQUIRED: float (>=0)
  "message": "Success message",       // OPTIONAL: string
  "warnings": [],                     // REQUIRED: array of strings
  "timestamp": "2025-10-14T01:00:00"  // REQUIRED: ISO 8601 datetime
}
```

### PrimaryMarketContextV1

```json
{
  "overall_market_score": 38,         // REQUIRED: int (-100 to +100)
  "market_confidence": 0.9,           // REQUIRED: float (0.0 to 1.0)
  "favorable_for": ["intraday"],      // REQUIRED: array (0-3 items)
  "global_context": {
    "overall_trend": "bullish",       // REQUIRED: TrendDirectionV1
    "us_markets_change": 1.2,         // REQUIRED: float (-100 to +100)
    "asia_markets_change": 0.5,       // REQUIRED: float (-100 to +100)
    "europe_markets_change": -0.3,    // REQUIRED: float (-100 to +100)
    "risk_on_off": "risk_on",         // REQUIRED: literal enum
    "volatility_level": "low"         // REQUIRED: VolatilityLevelV1
  },
  "indian_context": {
    "nifty_change": -0.23,            // REQUIRED: float (-100 to +100)
    "banknifty_change": 0.15,         // REQUIRED: float (-100 to +100)
    "sensex_change": -0.18,           // REQUIRED: float (-100 to +100)
    "market_regime": "sideways",      // REQUIRED: MarketRegimeV1
    "fii_activity": "neutral",        // REQUIRED: literal enum
    "current_nifty_price": 25199.50   // OPTIONAL: float (>0) or null
  }
}
```

### IntradayContextV1

```json
{
  "pivot_point": 25199,               // OPTIONAL: float (>0) or null
  "resistance_1": 25450,              // OPTIONAL: float (>0) or null
  "resistance_2": 25700,              // OPTIONAL: float (>0) or null
  "resistance_3": 25950,              // OPTIONAL: float (>0) or null
  "support_1": 24950,                 // OPTIONAL: float (>0) or null
  "support_2": 24700,                 // OPTIONAL: float (>0) or null
  "support_3": 24450,                 // OPTIONAL: float (>0) or null
  "vwap": 25180,                      // OPTIONAL: float (>0) or null
  "price_vs_vwap": "above",           // OPTIONAL: literal enum or null
  "current_momentum": "neutral",      // REQUIRED: TrendDirectionV1
  "momentum_strength": "weak",        // OPTIONAL: TrendStrengthV1 or null
  "volume_trend": "average",          // OPTIONAL: literal enum or null
  "intraday_volatility": "low",       // REQUIRED: VolatilityLevelV1
  "expected_range_high": 25449,       // OPTIONAL: float (>0) or null
  "expected_range_low": 24949,        // OPTIONAL: float (>0) or null
  "breakout_candidates": [],          // REQUIRED: array of strings
  "reversal_candidates": [],          // REQUIRED: array of strings
  "high_impact_events_today": []      // REQUIRED: array of strings
}
```

### SwingContextV1

```json
{
  "multi_day_trend": "uptrend",       // REQUIRED: literal enum
  "trend_strength": "moderate",       // REQUIRED: TrendStrengthV1
  "trend_age_days": 15,               // REQUIRED: int (>=0)
  "weekly_momentum": "bullish",       // REQUIRED: TrendDirectionV1
  "momentum_divergence": false,       // REQUIRED: boolean
  "swing_support_levels": [24723],    // REQUIRED: array of floats
  "swing_resistance_levels": [25675], // REQUIRED: array of floats
  "chart_patterns": [],               // REQUIRED: array of strings
  "hot_sectors": ["IT"],              // REQUIRED: array of strings
  "cold_sectors": ["Realty"],         // REQUIRED: array of strings
  "rotating_sectors": ["Auto"],       // REQUIRED: array of strings
  "oversold_stocks": [],              // REQUIRED: array of strings
  "overbought_stocks": [],            // REQUIRED: array of strings
  "risk_level": "medium",             // REQUIRED: RiskLevelV1
  "stop_loss_suggestion": "2-3%"      // REQUIRED: string
}
```

### LongTermContextV1

```json
{
  "economic_cycle": "expansion",      // REQUIRED: EconomicCycleV1
  "interest_rate_trend": "stable",    // REQUIRED: literal enum
  "inflation_trend": "moderate",      // REQUIRED: literal enum
  "nifty_pe": 22.5,                   // OPTIONAL: float (>0) or null
  "nifty_pb": 3.8,                    // OPTIONAL: float (>0) or null
  "market_valuation": "fair",         // REQUIRED: MarketValuationV1
  "emerging_themes": ["Digital"],     // REQUIRED: array of strings
  "declining_themes": [],             // REQUIRED: array of strings
  "recommended_sector_weights": {},   // REQUIRED: dict
  "value_opportunities": ["L&T"],     // REQUIRED: array of strings
  "growth_opportunities": ["INFY"],   // REQUIRED: array of strings
  "dividend_opportunities": ["ITC"],  // REQUIRED: array of strings
  "systemic_risk_level": "medium",    // REQUIRED: RiskLevelV1
  "key_risks": []                     // REQUIRED: array of strings
}
```

### DataQualityReportV1

```json
{
  "overall_quality": "HIGH",          // REQUIRED: DataQualityV1
  "real_data_percentage": 85.5,       // REQUIRED: float (0-100)
  "approximated_percentage": 10.2,    // REQUIRED: float (0-100)
  "fallback_percentage": 4.3,         // REQUIRED: float (0-100)
  "data_sources": ["Kite", "Yahoo"], // REQUIRED: array of strings
  "recommendations": []               // REQUIRED: array of strings
}
```

---

## ✅ VALIDATION RULES

### Field-Level Validation

All fields are validated according to their type and range:

```python
# Example validations
overall_market_score: int = Field(ge=-100, le=100)  # -100 to +100
market_confidence: float = Field(ge=0.0, le=1.0)    # 0.0 to 1.0
nifty_change: float = Field(ge=-100.0, le=100.0)    # -100% to +100%
current_nifty_price: Optional[float] = Field(gt=0)  # > 0 or None
trend_age_days: int = Field(ge=0)                   # >= 0
```

### Schema-Level Validation

- **Extra fields forbidden** - Only defined fields allowed
- **Type checking** - Strict type enforcement
- **Enum validation** - Only defined enum values allowed
- **Required fields** - Must be present in response

---

## 🔄 VERSIONING STRATEGY

### Version Format

`MAJOR.MINOR.PATCH`

- **MAJOR** - Breaking changes (incompatible API changes)
- **MINOR** - New features (backward compatible)
- **PATCH** - Bug fixes (backward compatible)

### Version History

| Version | Date | Status | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-10-14 | ✅ STABLE | Initial release |

### Migration Path

When V2 is released:
1. V1 will be maintained for 6 months minimum
2. Both versions will run in parallel
3. Deprecation warnings will be added to V1 responses
4. Migration guide will be provided

---

## 🧪 CONTRACT TESTING

### Validation Function

```python
from models.data_contract_v1 import validate_contract_v1

# Run during application startup
validate_contract_v1()  # Raises ValueError if contract is invalid
```

### Example Usage

```python
from models.data_contract_v1 import (
    MarketContextResponseV1,
    PrimaryMarketContextV1,
    MarketRegimeV1
)

# Create response (will validate automatically)
response = MarketContextResponseV1(
    success=True,
    contract_version="1.0.0",
    primary_context=PrimaryMarketContextV1(
        overall_market_score=38,
        market_confidence=0.9,
        # ... other fields
    ),
    context_quality_score=0.85,
    processing_time_ms=89.14
)

# Pydantic will validate:
# - All required fields present
# - All types correct
# - All values within ranges
# - No extra fields
```

---

## 📖 INTEGRATION GUIDE

### For API Consumers

1. **Use the contract version** in your integration
2. **Validate responses** against the schema
3. **Handle optional fields** gracefully (check for null)
4. **Use enum values** exactly as specified
5. **Respect value ranges** in your logic

### TypeScript Example

```typescript
interface MarketContextResponseV1 {
  success: boolean;
  contract_version: string;
  primary_context?: PrimaryMarketContextV1;
  context_quality_score: number;  // 0.0-1.0
  processing_time_ms: number;     // >=0
  timestamp: string;              // ISO 8601
}

// Validate response
function validateResponse(data: any): MarketContextResponseV1 {
  if (!data.success || data.contract_version !== "1.0.0") {
    throw new Error("Invalid response");
  }
  return data as MarketContextResponseV1;
}
```

### Python Example

```python
from models.data_contract_v1 import MarketContextResponseV1

# Parse and validate response
response_data = api.get_market_context()
validated = MarketContextResponseV1(**response_data)

# Access with type safety
if validated.primary_context:
    score = validated.primary_context.overall_market_score
    # score is guaranteed to be int between -100 and +100
```

---

## 🚨 BREAKING CHANGE POLICY

### What Constitutes a Breaking Change

- Removing a field
- Renaming a field
- Changing a field's type
- Removing an enum value
- Making validation stricter
- Making an optional field required

### How Breaking Changes Are Handled

1. **New major version** (V2) is created
2. **Both versions run in parallel** for transition period
3. **Deprecation notice** added to old version
4. **Migration guide** provided
5. **Minimum 6 months** before old version removal

---

## 📞 SUPPORT

### Questions About Contract

- **Schema questions:** See this document
- **Validation errors:** Check field types and ranges
- **Integration help:** See integration examples above
- **Breaking changes:** Will be announced in advance

### Contract Validation

```bash
# Test contract validity
python -c "from models.data_contract_v1 import validate_contract_v1; validate_contract_v1()"
```

---

**Status:** ✅ STABLE - Ready for Production  
**Version:** 1.0.0  
**Last Updated:** 2025-10-14

**This contract is IMMUTABLE. Any breaking changes will result in V2.**

