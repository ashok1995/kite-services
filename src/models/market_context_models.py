"""
Finalized Market Context Data Models
====================================

Comprehensive request/response models for the unified market context endpoint.
Combines global intelligence, Indian market data, and intraday context.

Building upon:
- unified_seed_model.py patterns
- intraday_context_models.py features
- consolidated_models.py structure
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator

# =============================================================================
# ENUMS AND TYPES
# =============================================================================


class ContextScope(str, Enum):
    """Context scope for different use cases."""

    QUICK = "quick"  # Fast context for immediate decisions
    STANDARD = "standard"  # Standard comprehensive context
    COMPREHENSIVE = "comprehensive"  # Full context with all features
    INTRADAY = "intraday"  # Intraday-specific context
    SWING = "swing"  # Swing trading context
    POSITIONAL = "positional"  # Positional trading context


class DataFreshness(str, Enum):
    """Data freshness requirements."""

    REAL_TIME = "real_time"  # < 1 minute old
    NEAR_REAL_TIME = "near_real_time"  # < 5 minutes old
    RECENT = "recent"  # < 15 minutes old
    ACCEPTABLE = "acceptable"  # < 60 minutes old


class MarketRegime(str, Enum):
    """Market regime classification."""

    STRONG_BULLISH = "strong_bullish"
    BULLISH = "bullish"
    SIDEWAYS_BULLISH = "sideways_bullish"
    SIDEWAYS = "sideways"
    SIDEWAYS_BEARISH = "sideways_bearish"
    BEARISH = "bearish"
    STRONG_BEARISH = "strong_bearish"
    VOLATILE = "volatile"
    TRENDING = "trending"
    RANGE_BOUND = "range_bound"


class VolatilityRegime(str, Enum):
    """Volatility regime classification."""

    VERY_LOW = "very_low"  # VIX < 12
    LOW = "low"  # VIX 12-16
    NORMAL = "normal"  # VIX 16-20
    ELEVATED = "elevated"  # VIX 20-25
    HIGH = "high"  # VIX 25-30
    VERY_HIGH = "very_high"  # VIX > 30


class TradingSession(str, Enum):
    """Trading session classification."""

    PRE_MARKET = "pre_market"
    OPENING = "opening"
    MORNING = "morning"
    MID_DAY = "mid_day"
    AFTERNOON = "afternoon"
    CLOSING = "closing"
    POST_MARKET = "post_market"
    AFTER_HOURS = "after_hours"


class GlobalSentiment(str, Enum):
    """Global market sentiment."""

    VERY_POSITIVE = "very_positive"
    POSITIVE = "positive"
    NEUTRAL_POSITIVE = "neutral_positive"
    NEUTRAL = "neutral"
    NEUTRAL_NEGATIVE = "neutral_negative"
    NEGATIVE = "negative"
    VERY_NEGATIVE = "very_negative"


# =============================================================================
# REQUEST MODELS
# =============================================================================


class MarketContextRequest(BaseModel):
    """
    Comprehensive market context request model.

    This is the unified request model for all market context needs,
    supporting different scopes and use cases.
    """

    # Request metadata
    request_id: Optional[str] = Field(None, description="Optional request identifier")
    timestamp: Optional[datetime] = Field(None, description="Request timestamp")

    # Context scope and depth
    scope: ContextScope = Field(
        default=ContextScope.STANDARD,
        description="Context scope - quick, standard, comprehensive, intraday, swing, positional",
    )

    # Symbols for analysis (optional)
    symbols: Optional[List[str]] = Field(
        None, max_items=20, description="Specific symbols for contextual analysis"
    )

    # Data requirements
    data_freshness: DataFreshness = Field(
        default=DataFreshness.NEAR_REAL_TIME, description="Required data freshness"
    )

    # Feature toggles
    include_global_context: bool = Field(default=True, description="Include global market analysis")

    include_sector_analysis: bool = Field(
        default=True, description="Include sector rotation and momentum"
    )

    include_technical_analysis: bool = Field(
        default=True, description="Include technical indicators and levels"
    )

    include_volatility_analysis: bool = Field(
        default=True, description="Include volatility and risk analysis"
    )

    include_sentiment_analysis: bool = Field(
        default=True, description="Include sentiment indicators"
    )

    include_trading_signals: bool = Field(
        default=False, description="Include trading signals (requires symbols)"
    )

    include_intraday_features: bool = Field(
        default=True, description="Include intraday-specific features"
    )

    # Timeframe preferences
    primary_timeframe: str = Field(default="15min", description="Primary timeframe for analysis")

    secondary_timeframes: List[str] = Field(
        default=["5min", "1hour"], description="Additional timeframes for confluence"
    )

    # Strategy context
    strategy_type: Optional[str] = Field(
        None, description="Trading strategy type for contextual filtering"
    )

    risk_tolerance: str = Field(default="medium", description="Risk tolerance level")

    # Historical context depth
    historical_days: int = Field(default=30, ge=1, le=365, description="Days of historical context")

    # Output preferences
    include_explanations: bool = Field(
        default=True, description="Include explanatory text and reasoning"
    )

    include_recommendations: bool = Field(
        default=True, description="Include actionable recommendations"
    )

    response_format: str = Field(
        default="detailed", description="Response format - minimal, standard, detailed"
    )

    @validator("symbols")
    def validate_symbols(cls, v):
        """Validate and clean symbols."""
        if v:
            return [symbol.strip().upper() for symbol in v if symbol.strip()]
        return v

    @validator("scope")
    def validate_scope_dependencies(cls, v, values):
        """Validate scope-specific requirements."""
        if v == ContextScope.INTRADAY:
            # Intraday scope should include intraday features
            values["include_intraday_features"] = True
        return v


# =============================================================================
# COMPONENT MODELS (Building blocks for response)
# =============================================================================


class GlobalMarketSnapshot(BaseModel):
    """Global market snapshot for context."""

    timestamp: datetime = Field(..., description="Snapshot timestamp")

    # Major indices
    us_markets: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict, description="US market indices and performance"
    )

    european_markets: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict, description="European market indices and performance"
    )

    asian_markets: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict, description="Asian market indices and performance"
    )

    # Global sentiment and trends
    global_sentiment: GlobalSentiment = Field(..., description="Overall global sentiment")
    global_momentum_score: Decimal = Field(
        ..., ge=-100, le=100, description="Global momentum score"
    )

    # Overnight changes and impact
    overnight_changes: Dict[str, Decimal] = Field(
        default_factory=dict, description="Overnight changes by region"
    )

    # Cross-market correlations
    correlations: Dict[str, Decimal] = Field(
        default_factory=dict, description="Cross-market correlation coefficients"
    )

    # Global themes and factors
    global_themes: List[str] = Field(default_factory=list, description="Current global themes")
    risk_on_off: str = Field(..., description="Risk-on/risk-off environment")

    # Economic indicators
    economic_indicators: Dict[str, Any] = Field(
        default_factory=dict, description="Key economic indicators"
    )


class IndianMarketSnapshot(BaseModel):
    """Indian market snapshot for context."""

    timestamp: datetime = Field(..., description="Snapshot timestamp")

    # Major indices
    indices: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict, description="Indian market indices"
    )

    # Market regime and characteristics
    market_regime: MarketRegime = Field(..., description="Current market regime")
    volatility_regime: VolatilityRegime = Field(..., description="Current volatility regime")

    # Market breadth
    market_breadth: Dict[str, Any] = Field(
        default_factory=dict, description="Market breadth indicators"
    )

    # Sector performance
    sector_performance: Dict[str, Decimal] = Field(
        default_factory=dict, description="Sector-wise performance"
    )

    # Institutional activity
    institutional_flows: Dict[str, Decimal] = Field(
        default_factory=dict, description="FII/DII flows and activity"
    )

    # Trading session info
    trading_session: TradingSession = Field(..., description="Current trading session")
    session_characteristics: Dict[str, Any] = Field(
        default_factory=dict, description="Session-specific characteristics"
    )


class TechnicalSnapshot(BaseModel):
    """Technical analysis snapshot."""

    timestamp: datetime = Field(..., description="Analysis timestamp")

    # Multi-timeframe analysis
    timeframe_analysis: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict, description="Analysis across multiple timeframes"
    )

    # Key levels
    support_resistance: Dict[str, List[Decimal]] = Field(
        default_factory=dict, description="Key support and resistance levels"
    )

    # Technical indicators
    technical_indicators: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict, description="Technical indicator values and signals"
    )

    # Momentum and trend
    trend_analysis: Dict[str, Any] = Field(
        default_factory=dict, description="Trend strength and momentum analysis"
    )

    # Volume analysis
    volume_analysis: Dict[str, Any] = Field(
        default_factory=dict, description="Volume patterns and analysis"
    )


class VolatilitySnapshot(BaseModel):
    """Volatility and risk snapshot."""

    timestamp: datetime = Field(..., description="Snapshot timestamp")

    # Volatility metrics
    current_vix: Decimal = Field(..., description="Current VIX level")
    vix_trend: str = Field(..., description="VIX trend direction")
    historical_volatility: Decimal = Field(..., description="Historical volatility")
    implied_volatility: Decimal = Field(..., description="Implied volatility")

    # Risk metrics
    fear_greed_index: int = Field(..., ge=0, le=100, description="Fear & Greed index")
    put_call_ratio: Decimal = Field(..., description="Put/Call ratio")

    # Volatility regime
    volatility_regime: VolatilityRegime = Field(..., description="Current volatility regime")
    regime_probability: Decimal = Field(..., ge=0, le=100, description="Regime confidence")

    # Expected ranges
    expected_daily_range: Decimal = Field(..., description="Expected daily range %")
    intraday_range_estimate: Decimal = Field(..., description="Intraday range estimate %")


class SentimentSnapshot(BaseModel):
    """Market sentiment snapshot."""

    timestamp: datetime = Field(..., description="Snapshot timestamp")

    # Sentiment indicators
    retail_sentiment: str = Field(..., description="Retail investor sentiment")
    institutional_sentiment: str = Field(..., description="Institutional sentiment")
    options_sentiment: str = Field(..., description="Options market sentiment")

    # Sentiment scores
    overall_sentiment_score: Decimal = Field(
        ..., ge=-100, le=100, description="Overall sentiment score"
    )
    sentiment_momentum: str = Field(..., description="Sentiment momentum direction")

    # News and social sentiment
    news_sentiment: Optional[str] = Field(None, description="News sentiment analysis")
    social_sentiment: Optional[str] = Field(None, description="Social media sentiment")

    # Sentiment extremes
    sentiment_extreme: bool = Field(..., description="Sentiment at extreme levels")
    contrarian_signal: bool = Field(..., description="Contrarian signal detected")


class TradingEnvironmentSnapshot(BaseModel):
    """Trading environment snapshot."""

    timestamp: datetime = Field(..., description="Snapshot timestamp")

    # Liquidity conditions
    liquidity_score: Decimal = Field(..., ge=0, le=100, description="Market liquidity score")
    spread_conditions: str = Field(..., description="Bid-ask spread conditions")

    # Execution environment
    execution_quality: str = Field(..., description="Expected execution quality")
    slippage_estimate: Decimal = Field(..., description="Expected slippage %")

    # Market microstructure
    market_impact: str = Field(..., description="Market impact assessment")
    order_flow: str = Field(..., description="Order flow characteristics")

    # Trading recommendations
    optimal_position_sizes: Dict[str, Decimal] = Field(
        default_factory=dict, description="Recommended position sizes by risk level"
    )

    execution_timing: str = Field(..., description="Optimal execution timing")


# =============================================================================
# CONTEXTUAL INSIGHTS AND RECOMMENDATIONS
# =============================================================================


class MarketInsights(BaseModel):
    """Market insights and analysis."""

    # Key insights
    key_insights: List[str] = Field(default_factory=list, description="Key market insights")

    # Market themes
    primary_themes: List[str] = Field(default_factory=list, description="Primary market themes")
    emerging_themes: List[str] = Field(default_factory=list, description="Emerging themes")

    # Risk factors
    key_risks: List[str] = Field(default_factory=list, description="Key risk factors")
    tail_risks: List[str] = Field(default_factory=list, description="Tail risk scenarios")

    # Opportunities
    opportunities: List[str] = Field(default_factory=list, description="Market opportunities")

    # Catalysts
    upcoming_catalysts: List[str] = Field(
        default_factory=list, description="Upcoming market catalysts"
    )


class TradingRecommendations(BaseModel):
    """Trading recommendations and guidance."""

    # Strategy recommendations
    recommended_strategies: List[str] = Field(
        default_factory=list, description="Recommended trading strategies"
    )

    strategies_to_avoid: List[str] = Field(
        default_factory=list, description="Strategies to avoid in current environment"
    )

    # Risk management
    risk_management_notes: List[str] = Field(
        default_factory=list, description="Risk management recommendations"
    )

    position_sizing_guidance: Dict[str, Any] = Field(
        default_factory=dict, description="Position sizing guidance by strategy"
    )

    # Execution guidance
    execution_recommendations: List[str] = Field(
        default_factory=list, description="Execution timing and method recommendations"
    )

    # Time horizon guidance
    optimal_time_horizons: Dict[str, str] = Field(
        default_factory=dict, description="Optimal time horizons for different strategies"
    )


class SymbolSpecificContext(BaseModel):
    """Symbol-specific contextual analysis."""

    symbol: str = Field(..., description="Stock symbol")

    # Current state
    current_price: Decimal = Field(..., description="Current price")
    price_change: Decimal = Field(..., description="Price change")
    price_change_percent: Decimal = Field(..., description="Price change %")

    # Technical context
    technical_bias: str = Field(..., description="Technical bias")
    key_levels: Dict[str, Decimal] = Field(default_factory=dict, description="Key price levels")

    # Relative performance
    relative_strength: Decimal = Field(..., description="Relative strength vs market")
    sector_relative_performance: Decimal = Field(..., description="Performance vs sector")

    # Volume and liquidity
    volume_analysis: Dict[str, Any] = Field(default_factory=dict, description="Volume analysis")
    liquidity_score: Decimal = Field(..., description="Liquidity score")

    # Contextual factors
    sector_influence: str = Field(..., description="Sector influence on stock")
    global_influence: str = Field(..., description="Global market influence")

    # Trading recommendation
    trading_bias: str = Field(..., description="Overall trading bias")
    confidence_score: Decimal = Field(..., ge=0, le=100, description="Analysis confidence")


# =============================================================================
# MAIN RESPONSE MODEL
# =============================================================================


class MarketContextResponse(BaseModel):
    """
    Comprehensive market context response model.

    This is the unified response model that provides complete market intelligence
    for all trading decisions across different timeframes and strategies.
    """

    # Response metadata
    request_id: str = Field(..., description="Request identifier")
    timestamp: datetime = Field(..., description="Response timestamp")
    scope: ContextScope = Field(..., description="Context scope provided")
    data_freshness: str = Field(..., description="Actual data freshness achieved")

    # Core market snapshots
    global_context: GlobalMarketSnapshot = Field(..., description="Global market context")
    indian_context: IndianMarketSnapshot = Field(..., description="Indian market context")
    technical_context: TechnicalSnapshot = Field(..., description="Technical analysis context")
    volatility_context: VolatilitySnapshot = Field(..., description="Volatility and risk context")
    sentiment_context: SentimentSnapshot = Field(..., description="Market sentiment context")
    trading_environment: TradingEnvironmentSnapshot = Field(..., description="Trading environment")

    # Market intelligence
    market_insights: MarketInsights = Field(..., description="Market insights and analysis")
    trading_recommendations: TradingRecommendations = Field(
        ..., description="Trading recommendations"
    )

    # Symbol-specific analysis (if symbols provided)
    symbol_analysis: Dict[str, SymbolSpecificContext] = Field(
        default_factory=dict, description="Symbol-specific contextual analysis"
    )

    # Market regime summary
    overall_market_regime: MarketRegime = Field(..., description="Overall market regime")
    regime_confidence: Decimal = Field(
        ..., ge=0, le=100, description="Regime classification confidence"
    )
    regime_stability: str = Field(..., description="Regime stability assessment")

    # Global influence on Indian markets
    global_influence_score: Decimal = Field(
        ..., ge=0, le=100, description="Global influence on Indian markets (0-100)"
    )

    correlation_breakdown: Dict[str, Decimal] = Field(
        default_factory=dict, description="Correlation with different global regions"
    )

    # Session and timing context
    optimal_trading_windows: List[str] = Field(
        default_factory=list, description="Optimal trading time windows for current session"
    )

    session_bias: str = Field(..., description="Current session trading bias")
    time_decay_factors: Dict[str, Any] = Field(
        default_factory=dict, description="Time decay factors for different strategies"
    )

    # Risk and opportunity matrix
    risk_opportunity_matrix: Dict[str, Dict[str, str]] = Field(
        default_factory=dict, description="Risk vs opportunity assessment by strategy"
    )

    # Performance metrics
    context_quality_score: Decimal = Field(..., ge=0, le=100, description="Overall context quality")
    data_coverage_score: Decimal = Field(
        ..., ge=0, le=100, description="Data coverage completeness"
    )
    analysis_confidence: Decimal = Field(..., ge=0, le=100, description="Analysis confidence level")

    # Processing metadata
    processing_time_ms: int = Field(..., ge=0, description="Total processing time")
    data_sources_used: Dict[str, int] = Field(
        default_factory=dict, description="Data sources and data points used"
    )

    cache_status: str = Field(..., description="Cache hit/miss status")
    next_update_time: Optional[datetime] = Field(None, description="Next scheduled context update")

    # Alerts and warnings
    market_alerts: List[str] = Field(default_factory=list, description="Important market alerts")
    data_quality_warnings: List[str] = Field(
        default_factory=list, description="Data quality warnings"
    )

    system_health: Dict[str, str] = Field(
        default_factory=dict, description="System health indicators"
    )


# =============================================================================
# QUICK CONTEXT MODELS (Optimized for speed)
# =============================================================================


class QuickMarketContextRequest(BaseModel):
    """Quick market context request for immediate decisions."""

    symbols: Optional[List[str]] = Field(
        None, max_items=5, description="Max 5 symbols for quick analysis"
    )
    include_signals: bool = Field(default=False, description="Include trading signals")


class QuickMarketContextResponse(BaseModel):
    """Quick market context response optimized for speed."""

    timestamp: datetime = Field(..., description="Response timestamp")

    # Essential context
    market_regime: str = Field(..., description="Current market regime")
    global_sentiment: str = Field(..., description="Global market sentiment")
    indian_bias: str = Field(..., description="Indian market bias")

    # Key metrics
    vix_level: Decimal = Field(..., description="Current VIX")
    global_influence: Decimal = Field(..., description="Global influence %")

    # Session info
    trading_session: str = Field(..., description="Current session")
    session_bias: str = Field(..., description="Session trading bias")

    # Quick recommendations
    trading_bias: str = Field(..., description="Overall trading bias")
    risk_level: str = Field(..., description="Current risk level")

    # Symbol quick analysis
    symbols: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict, description="Quick symbol analysis"
    )

    # Performance
    processing_time_ms: int = Field(..., description="Processing time")


# =============================================================================
# VALIDATION AND HELPER FUNCTIONS
# =============================================================================


def create_default_context_request(**kwargs) -> MarketContextRequest:
    """Create default market context request with sensible defaults."""
    return MarketContextRequest(**kwargs)


def create_quick_context_request(symbols: List[str] = None) -> QuickMarketContextRequest:
    """Create quick context request."""
    return QuickMarketContextRequest(symbols=symbols or [])


# =============================================================================
# EXAMPLE USAGE AND DOCUMENTATION
# =============================================================================


class MarketContextExamples:
    """Examples of different context request patterns."""

    @staticmethod
    def intraday_trading_context():
        """Example: Comprehensive intraday trading context."""
        return MarketContextRequest(
            scope=ContextScope.INTRADAY,
            symbols=["RELIANCE", "TCS", "HDFC"],
            include_trading_signals=True,
            include_intraday_features=True,
            primary_timeframe="15min",
            secondary_timeframes=["5min", "1hour"],
            strategy_type="momentum",
            data_freshness=DataFreshness.REAL_TIME,
        )

    @staticmethod
    def swing_trading_context():
        """Example: Swing trading context."""
        return MarketContextRequest(
            scope=ContextScope.SWING,
            symbols=["RELIANCE", "TCS"],
            include_technical_analysis=True,
            include_sector_analysis=True,
            primary_timeframe="1hour",
            secondary_timeframes=["4hour", "daily"],
            historical_days=60,
            strategy_type="swing",
        )

    @staticmethod
    def quick_decision_context():
        """Example: Quick decision context."""
        return QuickMarketContextRequest(symbols=["NIFTY", "RELIANCE"], include_signals=True)


# Export key models
__all__ = [
    "MarketContextRequest",
    "MarketContextResponse",
    "QuickMarketContextRequest",
    "QuickMarketContextResponse",
    "ContextScope",
    "DataFreshness",
    "MarketRegime",
    "VolatilityRegime",
    "TradingSession",
    "GlobalSentiment",
]
