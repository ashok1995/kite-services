"""
Data Contract V1 - IMMUTABLE API SCHEMA
========================================

⚠️  CRITICAL: This is a versioned data contract.
    DO NOT modify existing fields or their types.
    Only ADD new optional fields if absolutely necessary.
    Breaking changes require a new version (v2).

Version: 1.1.0
Created: 2025-10-14
Updated: 2025-10-14
Status: STABLE - Production Ready

Changelog:
- V1.1.0: Added detailed_context, ml_features, context_quality_score, data_freshness_seconds,
  processing_time_ms, data_source_summary fields (all optional for backward compatibility)

Contract Principles:
1. Backward compatibility is MANDATORY
2. Field types are IMMUTABLE once released
3. Field names are IMMUTABLE once released
4. Value ranges are DOCUMENTED and ENFORCED
5. All fields have validation rules
6. Breaking changes = new version number

Usage:
    from models.data_contract_v1 import (
        MarketContextResponseV1,
        PrimaryContextV1,
        IntradayContextV1
    )
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from common.time_utils import now_ist_naive

# ============================================================================
# VERSION METADATA
# ============================================================================


class DataContractVersion(BaseModel):
    """Version information for data contract."""

    version: str = "1.0.0"
    created_date: str = "2025-10-14"
    status: Literal["stable", "deprecated", "draft"] = "stable"
    breaking_changes_from_previous: Optional[str] = None


# ============================================================================
# ENUMS - IMMUTABLE VALUE SETS
# ============================================================================


class MarketRegimeV1(str, Enum):
    """Market regime classification - IMMUTABLE."""

    BULL_STRONG = "bull_strong"
    BULL_WEAK = "bull_weak"
    SIDEWAYS = "sideways"
    BEAR_WEAK = "bear_weak"
    BEAR_STRONG = "bear_strong"


class TrendDirectionV1(str, Enum):
    """Trend direction - IMMUTABLE."""

    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"
    MIXED = "mixed"


class TrendStrengthV1(str, Enum):
    """Trend strength - IMMUTABLE."""

    STRONG = "strong"
    MODERATE = "moderate"
    WEAK = "weak"


class VolatilityLevelV1(str, Enum):
    """Volatility level - IMMUTABLE."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class RiskLevelV1(str, Enum):
    """Risk level - IMMUTABLE."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class DataQualityV1(str, Enum):
    """Data quality level - IMMUTABLE."""

    HIGH = "HIGH"  # >70% real data
    MEDIUM = "MEDIUM"  # 40-70% real data
    LOW = "LOW"  # <40% real data


class MarketValuationV1(str, Enum):
    """Market valuation - IMMUTABLE."""

    UNDERVALUED = "undervalued"
    FAIR = "fair"
    OVERVALUED = "overvalued"


class EconomicCycleV1(str, Enum):
    """Economic cycle phase - IMMUTABLE."""

    EXPANSION = "expansion"
    PEAK = "peak"
    CONTRACTION = "contraction"
    TROUGH = "trough"


class TradingStyleV1(str, Enum):
    """Trading style - IMMUTABLE."""

    INTRADAY = "intraday"
    SWING = "swing"
    LONG_TERM = "long_term"
    ALL = "all"


# ============================================================================
# PRIMARY MARKET CONTEXT - IMMUTABLE SCHEMA
# ============================================================================


class GlobalMarketContextV1(BaseModel):
    """Global market context - IMMUTABLE SCHEMA.

    Contract Rules:
    - All percentage fields: -100.0 to +100.0
    - Trend: enum only (no free text)
    - Volatility: enum only
    """

    model_config = ConfigDict(frozen=False, extra="forbid")

    overall_trend: TrendDirectionV1 = Field(..., description="Global market trend direction")
    us_markets_change: float = Field(
        ..., ge=-100.0, le=100.0, description="US markets percentage change"
    )
    asia_markets_change: float = Field(
        ..., ge=-100.0, le=100.0, description="Asia markets percentage change"
    )
    europe_markets_change: float = Field(
        ..., ge=-100.0, le=100.0, description="Europe markets percentage change"
    )
    risk_on_off: Literal["risk_on", "risk_off", "neutral"] = Field(
        ..., description="Risk sentiment"
    )
    volatility_level: VolatilityLevelV1 = Field(..., description="Global volatility level")


class IndianMarketContextV1(BaseModel):
    """Indian market context - IMMUTABLE SCHEMA.

    Contract Rules:
    - All percentage fields: -100.0 to +100.0
    - Price fields: > 0
    - Regime: enum only
    """

    model_config = ConfigDict(frozen=False, extra="forbid")

    nifty_change: float = Field(..., ge=-100.0, le=100.0, description="Nifty 50 percentage change")
    banknifty_change: float = Field(
        ..., ge=-100.0, le=100.0, description="Bank Nifty percentage change"
    )
    sensex_change: float = Field(..., ge=-100.0, le=100.0, description="Sensex percentage change")
    market_regime: MarketRegimeV1 = Field(..., description="Current market regime")
    fii_activity: Literal["buying", "selling", "neutral"] = Field(
        ..., description="Foreign Institutional Investor activity"
    )
    current_nifty_price: Optional[float] = Field(
        None, gt=0, description="Current Nifty 50 price (INR)"
    )


class PrimaryMarketContextV1(BaseModel):
    """Primary market context - IMMUTABLE SCHEMA.

    Contract Rules:
    - overall_market_score: -100 to +100 (integer)
    - market_confidence: 0.0 to 1.0 (float)
    - favorable_for: array of TradingStyleV1 enums
    """

    model_config = ConfigDict(frozen=False, extra="forbid")

    overall_market_score: int = Field(
        ...,
        ge=-100,
        le=100,
        description="Composite market sentiment score (-100 bearish to +100 bullish)",
    )
    market_confidence: float = Field(
        ..., ge=0.0, le=1.0, description="System confidence in data quality (0.0 to 1.0)"
    )
    favorable_for: List[TradingStyleV1] = Field(
        ..., min_length=0, max_length=3, description="Trading styles favorable in current market"
    )
    global_context: GlobalMarketContextV1 = Field(..., description="Global market indicators")
    indian_context: IndianMarketContextV1 = Field(..., description="Indian market indicators")


# ============================================================================
# INTRADAY TRADING CONTEXT - IMMUTABLE SCHEMA
# ============================================================================


class IntradayContextV1(BaseModel):
    """Intraday trading context - IMMUTABLE SCHEMA.

    Contract Rules:
    - All price fields: > 0 or None
    - Momentum: enum only
    - Volatility: enum only
    """

    model_config = ConfigDict(frozen=False, extra="forbid")

    # Pivot points (IMMUTABLE)
    pivot_point: Optional[float] = Field(None, gt=0, description="Daily pivot point price level")
    resistance_1: Optional[float] = Field(None, gt=0, description="First resistance level")
    resistance_2: Optional[float] = Field(None, gt=0, description="Second resistance level")
    resistance_3: Optional[float] = Field(None, gt=0, description="Third resistance level")
    support_1: Optional[float] = Field(None, gt=0, description="First support level")
    support_2: Optional[float] = Field(None, gt=0, description="Second support level")
    support_3: Optional[float] = Field(None, gt=0, description="Third support level")

    # VWAP (IMMUTABLE)
    vwap: Optional[float] = Field(None, gt=0, description="Volume-weighted average price")
    price_vs_vwap: Optional[Literal["above", "below", "at"]] = Field(
        None, description="Current price position relative to VWAP"
    )

    # Momentum (IMMUTABLE)
    current_momentum: TrendDirectionV1 = Field(
        ..., description="Current intraday momentum direction"
    )
    momentum_strength: Optional[TrendStrengthV1] = Field(None, description="Momentum strength")
    volume_trend: Optional[Literal["high", "average", "low"]] = Field(
        None, description="Volume trend relative to average"
    )

    # Volatility (IMMUTABLE)
    intraday_volatility: VolatilityLevelV1 = Field(..., description="Intraday volatility level")
    expected_range_high: Optional[float] = Field(None, gt=0, description="Expected intraday high")
    expected_range_low: Optional[float] = Field(None, gt=0, description="Expected intraday low")

    # Signals (IMMUTABLE)
    breakout_candidates: List[str] = Field(
        default_factory=list, description="Stock symbols showing breakout potential"
    )
    reversal_candidates: List[str] = Field(
        default_factory=list, description="Stock symbols showing reversal potential"
    )
    high_impact_events_today: List[str] = Field(
        default_factory=list, description="High impact events scheduled for today"
    )


# ============================================================================
# SWING TRADING CONTEXT - IMMUTABLE SCHEMA
# ============================================================================


class SwingContextV1(BaseModel):
    """Swing trading context - IMMUTABLE SCHEMA.

    Contract Rules:
    - Trend: enum only
    - Strength: enum only
    - Age: >= 0
    - Levels: arrays of positive floats
    """

    model_config = ConfigDict(frozen=False, extra="forbid")

    # Trend (IMMUTABLE)
    multi_day_trend: Literal["uptrend", "downtrend", "sideways"] = Field(
        ..., description="Multi-day trend direction"
    )
    trend_strength: TrendStrengthV1 = Field(..., description="Trend strength")
    trend_age_days: int = Field(..., ge=0, description="Number of days current trend has persisted")
    weekly_momentum: TrendDirectionV1 = Field(..., description="Weekly momentum direction")
    momentum_divergence: bool = Field(..., description="Whether momentum divergence detected")

    # Support/Resistance (IMMUTABLE)
    swing_support_levels: List[float] = Field(
        default_factory=list, description="Swing support price levels"
    )
    swing_resistance_levels: List[float] = Field(
        default_factory=list, description="Swing resistance price levels"
    )

    # Patterns (IMMUTABLE)
    chart_patterns: List[str] = Field(default_factory=list, description="Detected chart patterns")

    # Sector Rotation (IMMUTABLE)
    hot_sectors: List[str] = Field(default_factory=list, description="Outperforming sectors")
    cold_sectors: List[str] = Field(default_factory=list, description="Underperforming sectors")
    rotating_sectors: List[str] = Field(default_factory=list, description="Sectors in rotation")

    # Opportunities (IMMUTABLE)
    oversold_stocks: List[str] = Field(default_factory=list, description="Oversold stock symbols")
    overbought_stocks: List[str] = Field(
        default_factory=list, description="Overbought stock symbols"
    )

    # Risk (IMMUTABLE)
    risk_level: RiskLevelV1 = Field(..., description="Overall risk level for swing trading")
    stop_loss_suggestion: str = Field(..., description="Stop loss recommendation")


# ============================================================================
# LONG-TERM INVESTMENT CONTEXT - IMMUTABLE SCHEMA
# ============================================================================


class LongTermContextV1(BaseModel):
    """Long-term investment context - IMMUTABLE SCHEMA.

    Contract Rules:
    - P/E, P/B: > 0
    - Valuation: enum only
    - Cycle: enum only
    """

    model_config = ConfigDict(frozen=False, extra="forbid")

    # Economic Indicators (IMMUTABLE)
    economic_cycle: EconomicCycleV1 = Field(..., description="Current economic cycle phase")
    interest_rate_trend: Literal["rising", "falling", "stable"] = Field(
        ..., description="Interest rate trend"
    )
    inflation_trend: Literal["low", "moderate", "high"] = Field(..., description="Inflation trend")

    # Valuation Metrics (IMMUTABLE)
    nifty_pe: Optional[float] = Field(None, gt=0, description="Nifty 50 Price-to-Earnings ratio")
    nifty_pb: Optional[float] = Field(None, gt=0, description="Nifty 50 Price-to-Book ratio")
    market_valuation: MarketValuationV1 = Field(
        ..., description="Overall market valuation assessment"
    )

    # Themes (IMMUTABLE)
    emerging_themes: List[str] = Field(
        default_factory=list, description="Emerging investment themes"
    )
    declining_themes: List[str] = Field(
        default_factory=list, description="Declining investment themes"
    )

    # Allocation (IMMUTABLE)
    recommended_sector_weights: Dict[str, float] = Field(
        default_factory=dict, description="Recommended sector allocation percentages"
    )

    # Opportunities (IMMUTABLE)
    value_opportunities: List[str] = Field(
        default_factory=list, description="Value investment opportunities"
    )
    growth_opportunities: List[str] = Field(
        default_factory=list, description="Growth investment opportunities"
    )
    dividend_opportunities: List[str] = Field(
        default_factory=list, description="Dividend investment opportunities"
    )

    # Risk (IMMUTABLE)
    systemic_risk_level: RiskLevelV1 = Field(..., description="Systemic market risk level")
    key_risks: List[str] = Field(default_factory=list, description="Key risk factors")


# ============================================================================
# DATA QUALITY REPORT - IMMUTABLE SCHEMA
# ============================================================================


class DataQualityReportV1(BaseModel):
    """Data quality report - IMMUTABLE SCHEMA.

    Contract Rules:
    - Percentages: 0.0 to 100.0
    - Quality: enum only
    """

    model_config = ConfigDict(frozen=False, extra="forbid")

    overall_quality: DataQualityV1 = Field(..., description="Overall data quality level")
    real_data_percentage: float = Field(
        ..., ge=0.0, le=100.0, description="Percentage of real data (0-100)"
    )
    approximated_percentage: float = Field(
        ..., ge=0.0, le=100.0, description="Percentage of approximated data (0-100)"
    )
    fallback_percentage: float = Field(
        ..., ge=0.0, le=100.0, description="Percentage of fallback data (0-100)"
    )
    data_sources: List[str] = Field(..., description="List of data sources used")
    recommendations: List[str] = Field(
        default_factory=list, description="Recommendations for improving data quality"
    )

    @field_validator("real_data_percentage", "approximated_percentage", "fallback_percentage")
    @classmethod
    def validate_percentages_sum(cls, v, info):
        """Validate that percentages are reasonable."""
        if v < 0 or v > 100:
            raise ValueError(f"Percentage must be between 0 and 100, got {v}")
        return v


# ============================================================================
# COMPLETE MARKET CONTEXT RESPONSE - IMMUTABLE SCHEMA
# ============================================================================


class MarketContextResponseV1(BaseModel):
    """Complete market context response - IMMUTABLE SCHEMA V1.

    This is the TOP-LEVEL contract for the enhanced market context API.

    Contract Rules:
    - success: boolean (REQUIRED)
    - All context fields: Optional (can be None if not requested)
    - context_quality_score: 0.0 to 1.0
    - processing_time_ms: >= 0
    - timestamp: ISO 8601 format

    Breaking Changes Policy:
    - Any change to field names, types, or validation rules requires V2
    - Only optional fields can be added to V1
    - Existing fields CANNOT be removed or modified
    """

    model_config = ConfigDict(frozen=False, extra="forbid")

    # Response Metadata (IMMUTABLE - REQUIRED)
    success: bool = Field(..., description="Whether request was successful")
    contract_version: str = Field(default="1.0.0", description="Data contract version")

    # Context Data (IMMUTABLE - OPTIONAL)
    primary_context: Optional[PrimaryMarketContextV1] = Field(
        None, description="Primary market context"
    )
    detailed_context: Optional[Dict[str, Any]] = Field(  # ADDITIVE: Detailed analysis
        None, description="Detailed market analysis (sectors, technicals, etc.)"
    )
    intraday_context: Optional[IntradayContextV1] = Field(
        None, description="Intraday trading context"
    )
    swing_context: Optional[SwingContextV1] = Field(None, description="Swing trading context")
    long_term_context: Optional[LongTermContextV1] = Field(
        None, description="Long-term investment context"
    )

    # ML Features (ADDITIVE - OPTIONAL)
    ml_features: Optional[Dict[str, Any]] = Field(
        None, description="Flattened ML-ready features for machine learning (47+ features)"
    )

    # Data Quality (IMMUTABLE - OPTIONAL)
    data_quality: Optional[DataQualityReportV1] = Field(None, description="Data quality report")

    # Quality Metrics (IMMUTABLE - OPTIONAL)
    context_quality_score: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Overall quality score of context data (0.0-1.0)"
    )
    data_freshness_seconds: Optional[int] = Field(None, ge=0, description="Age of data in seconds")

    # Performance Metrics (IMMUTABLE - OPTIONAL)
    processing_time_ms: Optional[float] = Field(
        None, ge=0.0, description="Processing time in milliseconds"
    )

    # Data Source Summary (IMMUTABLE - OPTIONAL)
    data_source_summary: Optional[Dict[str, int]] = Field(
        None, description="Summary of data sources: {real: N, approximated: N, fallback: N}"
    )

    # Performance Metrics (IMMUTABLE - OPTIONAL)
    context_quality_score: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Overall context quality score (0.0 to 1.0)"
    )
    processing_time_ms: Optional[float] = Field(
        None, ge=0.0, description="Processing time in milliseconds"
    )

    # Messages (IMMUTABLE - OPTIONAL)
    message: Optional[str] = Field(None, description="Human-readable message")
    warnings: List[str] = Field(default_factory=list, description="Warning messages")

    # Timestamp (IMMUTABLE - REQUIRED)
    timestamp: datetime = Field(
        default_factory=now_ist_naive, description="Response timestamp (IST, ISO 8601)"
    )


# ============================================================================
# CONTRACT VALIDATION
# ============================================================================


def validate_contract_v1():
    """Validate that the contract schema is properly defined.

    This function should be called during application startup to ensure
    the contract is valid and all enums/types are properly defined.
    """
    try:
        # Test all enums
        assert len(MarketRegimeV1) == 5
        assert len(TrendDirectionV1) == 4
        assert len(VolatilityLevelV1) == 3
        assert len(RiskLevelV1) == 3
        assert len(DataQualityV1) == 3

        # Test schema creation
        version = DataContractVersion()
        assert version.version == "1.1.0"
        assert version.status == "stable"

        return True
    except Exception as e:
        raise ValueError(f"Contract V1 validation failed: {e}")


# ============================================================================
# EXPORT CONTRACT VERSION
# ============================================================================

__version__ = "1.1.0"
__status__ = "stable"
__all__ = [
    # Version
    "DataContractVersion",
    "__version__",
    "__status__",
    # Enums
    "MarketRegimeV1",
    "TrendDirectionV1",
    "TrendStrengthV1",
    "VolatilityLevelV1",
    "RiskLevelV1",
    "DataQualityV1",
    "MarketValuationV1",
    "EconomicCycleV1",
    "TradingStyleV1",
    # Context Models
    "GlobalMarketContextV1",
    "IndianMarketContextV1",
    "PrimaryMarketContextV1",
    "IntradayContextV1",
    "SwingContextV1",
    "LongTermContextV1",
    "DataQualityReportV1",
    # Response Model
    "MarketContextResponseV1",
    # Validation
    "validate_contract_v1",
]
