"""
Intraday Market Context Models
==============================

Enhanced models for intraday trading decisions combining:
- Global indices trends (Yahoo Finance)
- Indian market context (Kite Connect)
- Multi-timeframe analysis
- Real-time contextual features

Building upon the excellent unified_seed_model.py patterns.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator


class IntradayTimeframe(str, Enum):
    """Intraday timeframe enumeration."""

    MINUTE_1 = "1min"
    MINUTE_5 = "5min"
    MINUTE_15 = "15min"
    MINUTE_30 = "30min"
    HOUR_1 = "1hour"
    HOUR_2 = "2hour"
    HOUR_4 = "4hour"


class GlobalMarketSession(str, Enum):
    """Global market session enumeration."""

    ASIAN_OPEN = "asian_open"
    ASIAN_CLOSE = "asian_close"
    EUROPEAN_OPEN = "european_open"
    EUROPEAN_CLOSE = "european_close"
    US_PREMARKET = "us_premarket"
    US_OPEN = "us_open"
    US_CLOSE = "us_close"
    INDIAN_PREMARKET = "indian_premarket"
    INDIAN_OPEN = "indian_open"
    INDIAN_CLOSE = "indian_close"


class MarketMomentum(str, Enum):
    """Market momentum classification."""

    ACCELERATING_UP = "accelerating_up"
    STEADY_UP = "steady_up"
    SLOWING_UP = "slowing_up"
    SIDEWAYS = "sideways"
    SLOWING_DOWN = "slowing_down"
    STEADY_DOWN = "steady_down"
    ACCELERATING_DOWN = "accelerating_down"


class IntradayTrendStrength(str, Enum):
    """Intraday trend strength (refined from unified model)."""

    VERY_STRONG = "very_strong"  # > 0.15
    STRONG = "strong"  # 0.07-0.15
    MODERATE = "moderate"  # 0.03-0.07
    WEAK = "weak"  # 0.01-0.03
    VERY_WEAK = "very_weak"  # < 0.01


# Global Market Models


class GlobalIndex(BaseModel):
    """Global market index with trend analysis."""

    symbol: str = Field(..., description="Index symbol")
    name: str = Field(..., description="Index name")
    region: str = Field(..., description="Geographic region")

    # Current data
    current_value: Decimal = Field(..., gt=0, description="Current index value")
    change: Decimal = Field(..., description="Absolute change")
    change_percent: Decimal = Field(..., description="Percentage change")

    # Intraday data
    day_high: Decimal = Field(..., description="Day high")
    day_low: Decimal = Field(..., description="Day low")
    day_open: Decimal = Field(..., description="Day open")
    volume: Optional[int] = Field(None, description="Trading volume")

    # Trend analysis
    intraday_trend: str = Field(..., description="Intraday trend direction")
    trend_strength: IntradayTrendStrength = Field(..., description="Trend strength")
    momentum: MarketMomentum = Field(..., description="Market momentum")

    # Technical levels
    key_support: Optional[Decimal] = Field(None, description="Key support level")
    key_resistance: Optional[Decimal] = Field(None, description="Key resistance level")

    # Session data
    session_high: Decimal = Field(..., description="Session high")
    session_low: Decimal = Field(..., description="Session low")
    session_change: Decimal = Field(..., description="Session change %")

    # Meta
    last_updated: datetime = Field(..., description="Last update time")
    market_session: GlobalMarketSession = Field(..., description="Current market session")


class GlobalMarketContext(BaseModel):
    """Global market context for Indian trading decisions."""

    timestamp: datetime = Field(..., description="Context timestamp")

    # Major global indices
    us_indices: Dict[str, GlobalIndex] = Field(
        default_factory=dict, description="US market indices"
    )
    european_indices: Dict[str, GlobalIndex] = Field(
        default_factory=dict, description="European indices"
    )
    asian_indices: Dict[str, GlobalIndex] = Field(default_factory=dict, description="Asian indices")

    # Global market sentiment
    global_sentiment: str = Field(..., description="Overall global sentiment")
    global_momentum: MarketMomentum = Field(..., description="Global momentum")
    global_volatility: str = Field(..., description="Global volatility level")

    # Cross-market correlations
    us_india_correlation: Decimal = Field(..., ge=-1, le=1, description="US-India correlation")
    europe_india_correlation: Decimal = Field(
        ..., ge=-1, le=1, description="Europe-India correlation"
    )
    asia_india_correlation: Decimal = Field(..., ge=-1, le=1, description="Asia-India correlation")

    # Global themes
    global_themes: List[str] = Field(default_factory=list, description="Global market themes")
    risk_on_off: str = Field(..., description="Risk-on/Risk-off sentiment")

    # Currency and commodities impact
    dollar_strength: Decimal = Field(..., description="Dollar strength index")
    commodity_trends: Dict[str, str] = Field(default_factory=dict, description="Commodity trends")

    # Session analysis
    overnight_changes: Dict[str, Decimal] = Field(
        default_factory=dict, description="Overnight changes"
    )
    session_momentum: str = Field(..., description="Current session momentum")


class IntradayMarketContext(BaseModel):
    """Enhanced intraday market context combining Indian and global data."""

    timestamp: datetime = Field(..., description="Context timestamp")
    request_id: str = Field(..., description="Request identifier")

    # Time context
    market_session: GlobalMarketSession = Field(..., description="Current market session")
    session_time: str = Field(..., description="Time within session")
    time_of_day_bias: str = Field(..., description="Time-based market bias")

    # Indian market context (from Kite)
    indian_indices: Dict[str, GlobalIndex] = Field(
        default_factory=dict, description="Indian indices"
    )
    indian_market_regime: str = Field(..., description="Indian market regime")
    indian_volatility: str = Field(..., description="Indian market volatility")

    # Global context (from Yahoo Finance)
    global_context: GlobalMarketContext = Field(..., description="Global market context")

    # Multi-timeframe analysis
    timeframe_alignment: Dict[IntradayTimeframe, str] = Field(
        default_factory=dict, description="Timeframe trends"
    )
    dominant_timeframe: IntradayTimeframe = Field(..., description="Dominant timeframe")
    timeframe_confluence: Decimal = Field(..., ge=0, le=100, description="Timeframe confluence %")

    # Market breadth (enhanced)
    advancing_stocks_ratio: Decimal = Field(..., ge=0, le=100, description="Advancing stocks %")
    new_highs_lows_ratio: Decimal = Field(..., description="New highs/lows ratio")
    volume_trend: str = Field(..., description="Volume trend")
    institutional_flow: str = Field(..., description="Institutional flow")

    # Volatility context
    vix_level: Decimal = Field(..., description="VIX level")
    vix_trend: str = Field(..., description="VIX trend direction")
    fear_greed_index: int = Field(..., ge=0, le=100, description="Fear & Greed index")

    # Sector rotation (enhanced)
    sector_momentum: Dict[str, str] = Field(default_factory=dict, description="Sector momentum")
    sector_rotation_stage: str = Field(..., description="Sector rotation stage")
    leading_sectors: List[str] = Field(default_factory=list, description="Leading sectors")
    lagging_sectors: List[str] = Field(default_factory=list, description="Lagging sectors")

    # Global influence factors
    global_influence_score: Decimal = Field(
        ..., ge=0, le=100, description="Global influence on Indian markets"
    )
    overnight_gap_analysis: Dict[str, Any] = Field(
        default_factory=dict, description="Overnight gap analysis"
    )
    foreign_flows: Dict[str, Decimal] = Field(
        default_factory=dict, description="Foreign institutional flows"
    )

    # Trading environment
    liquidity_conditions: str = Field(..., description="Market liquidity conditions")
    spread_conditions: str = Field(..., description="Bid-ask spread conditions")
    execution_quality: str = Field(..., description="Expected execution quality")

    # Sentiment confluence
    retail_sentiment: str = Field(..., description="Retail sentiment")
    institutional_sentiment: str = Field(..., description="Institutional sentiment")
    global_sentiment_impact: str = Field(..., description="Global sentiment impact")

    # Analysis metadata
    context_confidence: Decimal = Field(..., ge=0, le=100, description="Context confidence")
    data_freshness_score: Decimal = Field(..., ge=0, le=100, description="Data freshness score")
    processing_time_ms: int = Field(..., ge=0, description="Processing time")


class IntradayTradingSignal(BaseModel):
    """Intraday trading signal with contextual factors."""

    symbol: str = Field(..., description="Stock symbol")
    signal_type: str = Field(..., description="Signal type (buy/sell/hold)")
    signal_strength: Decimal = Field(..., ge=0, le=100, description="Signal strength %")

    # Contextual factors
    global_alignment: bool = Field(..., description="Aligned with global trends")
    sector_alignment: bool = Field(..., description="Aligned with sector trends")
    timeframe_alignment: bool = Field(..., description="Multi-timeframe alignment")

    # Entry/exit levels
    entry_price: Decimal = Field(..., description="Suggested entry price")
    target_price: Decimal = Field(..., description="Target price")
    stop_loss: Decimal = Field(..., description="Stop loss level")

    # Risk assessment
    risk_reward_ratio: Decimal = Field(..., description="Risk/reward ratio")
    position_size_percent: Decimal = Field(
        ..., ge=0, le=100, description="Suggested position size %"
    )

    # Contextual reasoning
    primary_reasons: List[str] = Field(default_factory=list, description="Primary signal reasons")
    global_factors: List[str] = Field(
        default_factory=list, description="Global influencing factors"
    )
    risk_factors: List[str] = Field(default_factory=list, description="Risk factors")

    # Timing
    signal_timestamp: datetime = Field(..., description="Signal generation time")
    expected_duration: str = Field(..., description="Expected signal duration")
    urgency: str = Field(..., description="Signal urgency level")


class IntradayContextRequest(BaseModel):
    """Request for intraday market context."""

    symbols: Optional[List[str]] = Field(None, description="Specific symbols to analyze")
    timeframes: List[IntradayTimeframe] = Field(
        default=[IntradayTimeframe.MINUTE_15, IntradayTimeframe.HOUR_1],
        description="Timeframes for analysis",
    )

    # Analysis options
    include_global_context: bool = Field(default=True, description="Include global market analysis")
    include_sector_rotation: bool = Field(
        default=True, description="Include sector rotation analysis"
    )
    include_multi_timeframe: bool = Field(
        default=True, description="Include multi-timeframe analysis"
    )
    include_trading_signals: bool = Field(default=True, description="Include trading signals")

    # Strategy context
    trading_strategy: str = Field(default="intraday", description="Trading strategy type")
    risk_tolerance: str = Field(default="medium", description="Risk tolerance level")
    position_size_preference: Decimal = Field(
        default=Decimal("5"), ge=1, le=20, description="Position size %"
    )

    @validator("timeframes")
    def validate_timeframes(cls, v):
        """Validate timeframes are appropriate for intraday."""
        if not v:
            return [IntradayTimeframe.MINUTE_15, IntradayTimeframe.HOUR_1]
        return v


class IntradayContextResponse(BaseModel):
    """Enhanced intraday context response."""

    timestamp: datetime = Field(..., description="Response timestamp")
    request_id: str = Field(..., description="Request identifier")

    # Core context
    intraday_context: IntradayMarketContext = Field(..., description="Intraday market context")

    # Trading signals (if symbols provided)
    trading_signals: Dict[str, IntradayTradingSignal] = Field(
        default_factory=dict, description="Symbol-specific trading signals"
    )

    # Market summary
    market_summary: str = Field(..., description="Market summary for intraday trading")
    key_themes: List[str] = Field(default_factory=list, description="Key intraday themes")
    trading_environment: str = Field(..., description="Trading environment assessment")

    # Global influence
    global_influence_summary: str = Field(..., description="Global market influence summary")
    overnight_developments: List[str] = Field(
        default_factory=list, description="Overnight developments"
    )

    # Recommendations
    intraday_strategy_suggestions: List[str] = Field(
        default_factory=list, description="Strategy suggestions"
    )
    risk_management_notes: List[str] = Field(
        default_factory=list, description="Risk management notes"
    )

    # Performance metrics
    analysis_confidence: Decimal = Field(..., ge=0, le=100, description="Analysis confidence")
    processing_time_ms: int = Field(..., ge=0, description="Processing time")
    data_sources_count: int = Field(..., description="Number of data sources used")


class GlobalIndexTrend(BaseModel):
    """Global index trend analysis for Indian market context."""

    # US Markets
    sp500_trend: str = Field(..., description="S&P 500 trend")
    nasdaq_trend: str = Field(..., description="NASDAQ trend")
    dow_trend: str = Field(..., description="Dow Jones trend")

    # European Markets
    ftse_trend: str = Field(..., description="FTSE 100 trend")
    dax_trend: str = Field(..., description="DAX trend")
    cac_trend: str = Field(..., description="CAC 40 trend")

    # Asian Markets
    nikkei_trend: str = Field(..., description="Nikkei 225 trend")
    hang_seng_trend: str = Field(..., description="Hang Seng trend")
    shanghai_trend: str = Field(..., description="Shanghai Composite trend")

    # Emerging Markets
    emerging_markets_trend: str = Field(..., description="Emerging markets trend")

    # Overnight changes
    overnight_us_change: Decimal = Field(..., description="Overnight US market change %")
    overnight_europe_change: Decimal = Field(..., description="Overnight Europe change %")
    overnight_asia_change: Decimal = Field(..., description="Overnight Asia change %")

    # Global sentiment
    global_risk_sentiment: str = Field(..., description="Global risk sentiment")
    global_momentum_score: Decimal = Field(
        ..., ge=-100, le=100, description="Global momentum score"
    )

    # Impact on Indian markets
    expected_indian_impact: str = Field(..., description="Expected impact on Indian markets")
    correlation_strength: Decimal = Field(..., ge=0, le=1, description="Correlation strength")

    last_updated: datetime = Field(..., description="Last update timestamp")


class IntradayMarketBreadth(BaseModel):
    """Enhanced market breadth for intraday trading."""

    timestamp: datetime = Field(..., description="Breadth timestamp")

    # Basic breadth
    advances: int = Field(..., ge=0, description="Advancing stocks")
    declines: int = Field(..., ge=0, description="Declining stocks")
    unchanged: int = Field(..., ge=0, description="Unchanged stocks")

    # Volume breadth
    up_volume: int = Field(..., ge=0, description="Up volume")
    down_volume: int = Field(..., ge=0, description="Down volume")
    total_volume: int = Field(..., ge=0, description="Total volume")

    # Breadth ratios
    advance_decline_ratio: Decimal = Field(..., description="Advance/Decline ratio")
    up_down_volume_ratio: Decimal = Field(..., description="Up/Down volume ratio")

    # Intraday breadth indicators
    breadth_momentum: Decimal = Field(..., description="Breadth momentum")
    breadth_thrust: bool = Field(..., description="Breadth thrust detected")
    breadth_divergence: bool = Field(..., description="Breadth divergence detected")

    # Sector breadth
    sectors_advancing: int = Field(..., ge=0, description="Sectors advancing")
    sectors_declining: int = Field(..., ge=0, description="Sectors declining")
    sector_leadership: str = Field(..., description="Sector leadership pattern")

    # Time-based breadth
    morning_breadth: Optional[Decimal] = Field(None, description="Morning session breadth")
    afternoon_breadth: Optional[Decimal] = Field(None, description="Afternoon session breadth")
    closing_breadth: Optional[Decimal] = Field(None, description="Closing session breadth")


class IntradayVolatilityContext(BaseModel):
    """Intraday volatility context for risk management."""

    timestamp: datetime = Field(..., description="Volatility timestamp")

    # Current volatility
    current_vix: Decimal = Field(..., description="Current VIX level")
    vix_change: Decimal = Field(..., description="VIX change from previous day")
    vix_trend: str = Field(..., description="VIX trend direction")

    # Intraday volatility
    intraday_volatility: Decimal = Field(..., description="Intraday volatility %")
    volatility_regime: str = Field(..., description="Current volatility regime")
    volatility_momentum: str = Field(..., description="Volatility momentum")

    # Global volatility
    global_vix: Optional[Decimal] = Field(None, description="Global VIX equivalent")
    emerging_market_volatility: Optional[Decimal] = Field(None, description="EM volatility")

    # Volatility clustering
    volatility_clustering: bool = Field(..., description="Volatility clustering detected")
    volatility_breakout: bool = Field(..., description="Volatility breakout detected")

    # Risk metrics
    expected_daily_range: Decimal = Field(..., description="Expected daily range %")
    risk_adjusted_returns: Decimal = Field(..., description="Risk-adjusted return expectation")


class IntradaySectorContext(BaseModel):
    """Enhanced sector context for intraday rotation analysis."""

    timestamp: datetime = Field(..., description="Sector context timestamp")

    # Sector performance (real-time)
    sector_performance: Dict[str, Decimal] = Field(
        default_factory=dict, description="Real-time sector performance"
    )
    sector_momentum: Dict[str, str] = Field(default_factory=dict, description="Sector momentum")
    sector_volume: Dict[str, int] = Field(default_factory=dict, description="Sector volume")

    # Sector rotation
    rotation_stage: str = Field(..., description="Current rotation stage")
    rotation_momentum: Decimal = Field(..., description="Rotation momentum")
    rotation_sustainability: str = Field(..., description="Rotation sustainability")

    # Leadership analysis
    current_leaders: List[str] = Field(default_factory=list, description="Current sector leaders")
    emerging_leaders: List[str] = Field(default_factory=list, description="Emerging sector leaders")
    fading_leaders: List[str] = Field(default_factory=list, description="Fading sector leaders")

    # Global sector influence
    global_sector_trends: Dict[str, str] = Field(
        default_factory=dict, description="Global sector trends"
    )
    sector_correlation_with_global: Dict[str, Decimal] = Field(
        default_factory=dict, description="Global correlation"
    )

    # Intraday patterns
    morning_sector_leaders: List[str] = Field(default_factory=list, description="Morning leaders")
    afternoon_sector_leaders: List[str] = Field(
        default_factory=list, description="Afternoon leaders"
    )
    sector_momentum_shifts: List[str] = Field(
        default_factory=list, description="Momentum shifts detected"
    )


# Request/Response Models for API


class EnhancedIntradayRequest(BaseModel):
    """Enhanced request for intraday market context."""

    # Core request
    symbols: Optional[List[str]] = Field(None, max_items=20, description="Symbols for analysis")
    strategy: str = Field(default="intraday", description="Trading strategy")

    # Analysis preferences
    include_global_indices: bool = Field(
        default=True, description="Include global indices analysis"
    )
    include_sector_rotation: bool = Field(default=True, description="Include sector rotation")
    include_multi_timeframe: bool = Field(
        default=True, description="Include multi-timeframe analysis"
    )
    include_volatility_analysis: bool = Field(
        default=True, description="Include volatility analysis"
    )
    include_trading_signals: bool = Field(default=True, description="Include trading signals")

    # Timeframe preferences
    primary_timeframe: IntradayTimeframe = Field(
        default=IntradayTimeframe.MINUTE_15, description="Primary timeframe"
    )
    secondary_timeframes: List[IntradayTimeframe] = Field(
        default=[IntradayTimeframe.MINUTE_5, IntradayTimeframe.HOUR_1],
        description="Secondary timeframes",
    )

    # Risk preferences
    risk_tolerance: str = Field(default="medium", description="Risk tolerance")
    max_position_size: Decimal = Field(
        default=Decimal("10"), ge=1, le=25, description="Max position size %"
    )

    # Context depth
    analysis_depth: str = Field(default="comprehensive", description="Analysis depth")
    real_time_priority: bool = Field(default=True, description="Prioritize real-time data")


class EnhancedIntradayResponse(BaseModel):
    """Enhanced response for intraday market context."""

    timestamp: datetime = Field(..., description="Response timestamp")
    request_id: str = Field(..., description="Request identifier")

    # Core context
    intraday_context: IntradayMarketContext = Field(
        ..., description="Comprehensive intraday context"
    )
    global_trends: GlobalIndexTrend = Field(..., description="Global index trends")

    # Analysis results
    market_regime_analysis: Dict[str, Any] = Field(
        default_factory=dict, description="Market regime analysis"
    )
    volatility_analysis: IntradayVolatilityContext = Field(..., description="Volatility analysis")
    sector_analysis: IntradaySectorContext = Field(..., description="Sector analysis")
    breadth_analysis: IntradayMarketBreadth = Field(..., description="Market breadth analysis")

    # Trading intelligence
    trading_signals: Dict[str, IntradayTradingSignal] = Field(
        default_factory=dict, description="Symbol-specific trading signals"
    )

    # Contextual insights
    key_insights: List[str] = Field(default_factory=list, description="Key market insights")
    global_influence_factors: List[str] = Field(
        default_factory=list, description="Global influence factors"
    )
    intraday_themes: List[str] = Field(default_factory=list, description="Intraday market themes")

    # Trading recommendations
    strategy_recommendations: List[str] = Field(
        default_factory=list, description="Strategy recommendations"
    )
    risk_management_notes: List[str] = Field(
        default_factory=list, description="Risk management notes"
    )
    execution_notes: List[str] = Field(default_factory=list, description="Execution notes")

    # Performance metrics
    context_quality_score: Decimal = Field(..., ge=0, le=100, description="Context quality score")
    global_data_coverage: Decimal = Field(..., ge=0, le=100, description="Global data coverage %")
    indian_data_coverage: Decimal = Field(..., ge=0, le=100, description="Indian data coverage %")
    total_processing_time_ms: int = Field(..., ge=0, description="Total processing time")

    # Data sources summary
    data_sources_used: Dict[str, int] = Field(default_factory=dict, description="Data sources used")
    real_time_data_points: int = Field(..., ge=0, description="Real-time data points")
    historical_data_points: int = Field(..., ge=0, description="Historical data points")
