"""
Enhanced Market Context Models for Trading Decision Making
===========================================================

Multi-level market context specifically designed for real-time trading recommendations.
Provides hierarchical context: Primary (high-level) → Detailed (granular) → Style-specific

Trading Styles Supported:
- Intraday: High-frequency features, minute-level trends
- Swing: Multi-day patterns, momentum indicators
- Long-term: Macro trends, fundamental context
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


# ============================================================================
# ENUMS
# ============================================================================

class TradingStyle(str, Enum):
    """Trading style for context optimization."""
    INTRADAY = "intraday"
    SWING = "swing"
    LONG_TERM = "long_term"
    ALL = "all"  # Return features for all styles


class MarketRegime(str, Enum):
    """Overall market regime."""
    BULL_STRONG = "bull_strong"
    BULL_WEAK = "bull_weak"
    SIDEWAYS = "sideways"
    BEAR_WEAK = "bear_weak"
    BEAR_STRONG = "bear_strong"


class TrendStrength(str, Enum):
    """Trend strength indicator."""
    VERY_STRONG = "very_strong"
    STRONG = "strong"
    MODERATE = "moderate"
    WEAK = "weak"
    VERY_WEAK = "very_weak"


class VolatilityLevel(str, Enum):
    """Market volatility level."""
    VERY_HIGH = "very_high"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"
    VERY_LOW = "very_low"


# ============================================================================
# PRIMARY LEVEL - HIGH-LEVEL CONTEXT
# ============================================================================

class GlobalMarketPrimary(BaseModel):
    """Primary global market context - high-level overview."""
    
    # Overall sentiment
    overall_trend: str = Field(..., description="Overall global market trend: bullish/bearish/neutral")
    trend_strength: TrendStrength = Field(..., description="Strength of the trend")
    
    # Major indices changes (%)
    us_markets_change: Optional[Decimal] = Field(None, description="US markets avg change %")
    asia_markets_change: Optional[Decimal] = Field(None, description="Asian markets avg change %")
    europe_markets_change: Optional[Decimal] = Field(None, description="European markets avg change %")
    
    # Risk indicators
    risk_on_off: str = Field(..., description="Risk appetite: risk_on/risk_off/neutral")
    volatility_level: VolatilityLevel = Field(..., description="Global volatility level")
    
    # Key drivers
    key_drivers: List[str] = Field(default_factory=list, description="Key market drivers today")
    
    timestamp: datetime = Field(default_factory=datetime.now)


class IndianMarketPrimary(BaseModel):
    """Primary Indian market context - high-level overview."""
    
    # Main indices
    nifty_change: Optional[Decimal] = Field(None, description="Nifty 50 change %")
    sensex_change: Optional[Decimal] = Field(None, description="Sensex change %")
    banknifty_change: Optional[Decimal] = Field(None, description="Bank Nifty change %")
    current_nifty_price: Optional[Decimal] = Field(None, description="Current Nifty 50 price")
    
    # Market regime
    market_regime: MarketRegime = Field(..., description="Current market regime")
    trend_direction: str = Field(..., description="Trend: up/down/sideways")
    
    # Breadth
    advance_decline_ratio: Optional[Decimal] = Field(None, description="Advancing vs declining stocks")
    
    # Key levels
    nifty_support: Optional[Decimal] = Field(None, description="Nifty immediate support")
    nifty_resistance: Optional[Decimal] = Field(None, description="Nifty immediate resistance")
    
    timestamp: datetime = Field(default_factory=datetime.now)


class PrimaryMarketContext(BaseModel):
    """
    PRIMARY LEVEL - High-level market overview
    
    Use case: Quick sentiment check, overall market direction
    Suitable for: All trading styles as baseline context
    """
    
    # Global context
    global_context: GlobalMarketPrimary = Field(..., description="Global market overview")
    
    # Indian context
    indian_context: IndianMarketPrimary = Field(..., description="Indian market overview")
    
    # Combined signals
    overall_market_score: int = Field(..., ge=-100, le=100, description="Overall market score -100 (very bearish) to +100 (very bullish)")
    market_confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in market assessment")
    
    # Trading recommendations
    favorable_for: List[TradingStyle] = Field(default_factory=list, description="Market favorable for which trading styles")
    
    timestamp: datetime = Field(default_factory=datetime.now)


# ============================================================================
# DETAILED LEVEL - GRANULAR ANALYSIS
# ============================================================================

class SectorPerformance(BaseModel):
    """Sector-wise performance details."""
    
    sector_name: str
    change_percent: Decimal
    volume_ratio: Optional[Decimal] = Field(None, description="Volume vs avg volume")
    trend: str = Field(..., description="Sector trend: bullish/bearish/neutral")
    top_gainers: List[str] = Field(default_factory=list, description="Top 3 gainers in sector")
    top_losers: List[str] = Field(default_factory=list, description="Top 3 losers in sector")
    
    # Trading signals
    strength_score: int = Field(..., ge=-100, le=100, description="Sector strength score")
    momentum: str = Field(..., description="accelerating/decelerating/stable")


class TechnicalIndicators(BaseModel):
    """Technical indicators for detailed analysis."""
    
    # Moving averages
    price_vs_sma20: Optional[Decimal] = Field(None, description="Price vs 20 SMA %")
    price_vs_sma50: Optional[Decimal] = Field(None, description="Price vs 50 SMA %")
    price_vs_sma200: Optional[Decimal] = Field(None, description="Price vs 200 SMA %")
    
    # Momentum
    rsi_14: Optional[Decimal] = Field(None, ge=0, le=100, description="14-period RSI")
    macd_signal: str = Field(..., description="MACD signal: bullish_crossover/bearish_crossover/neutral")
    
    # Volatility
    atr_percent: Optional[Decimal] = Field(None, description="ATR as % of price")
    bollinger_position: str = Field(..., description="Price position in Bollinger Bands: upper/middle/lower")
    
    # Volume
    volume_trend: str = Field(..., description="Volume trend: increasing/decreasing/stable")
    volume_vs_avg: Optional[Decimal] = Field(None, description="Current volume vs 20-day avg")


class QuickTradingOpportunity(BaseModel):
    """5-minute quick trading opportunity for index."""
    
    signal: str = Field(..., description="BUY/SELL/HOLD")
    confidence: int = Field(..., ge=0, le=100, description="Signal confidence %")
    entry_zone: Optional[Decimal] = Field(None, description="Suggested entry price")
    target_1: Optional[Decimal] = Field(None, description="First target (quick profit)")
    target_2: Optional[Decimal] = Field(None, description="Second target (extended)")
    stop_loss: Optional[Decimal] = Field(None, description="Stop loss level")
    risk_reward: Optional[float] = Field(None, description="Risk:Reward ratio")
    reasoning: str = Field(..., description="Why this opportunity exists")
    time_validity_mins: int = Field(..., description="Valid for X minutes")
    trade_type: str = Field(..., description="scalp/momentum/breakout/reversal")


class IndexDetailedAnalysis(BaseModel):
    """Detailed analysis for major indices."""
    
    index_name: str
    current_value: Decimal
    change_percent: Decimal
    
    # Intraday levels
    day_high: Optional[Decimal] = None
    day_low: Optional[Decimal] = None
    opening_price: Optional[Decimal] = None
    
    # Support/Resistance (IMMEDIATE - within 0.5%)
    immediate_support: List[Decimal] = Field(default_factory=list, description="3 support levels")
    immediate_resistance: List[Decimal] = Field(default_factory=list, description="3 resistance levels")
    
    # 5-minute technical levels (QUICK MONEY)
    support_5min: Optional[Decimal] = Field(None, description="5-min support level")
    resistance_5min: Optional[Decimal] = Field(None, description="5-min resistance level")
    pivot_5min: Optional[Decimal] = Field(None, description="5-min pivot point")
    
    # Technical indicators
    technicals: TechnicalIndicators
    
    # Market breadth
    stocks_above_sma20: Optional[int] = Field(None, description="% of stocks above 20 SMA")
    stocks_above_sma50: Optional[int] = Field(None, description="% of stocks above 50 SMA")
    
    # Sentiment
    put_call_ratio: Optional[Decimal] = Field(None, description="PCR for options")
    fii_dii_activity: Optional[str] = Field(None, description="FII/DII buying/selling")
    
    # 5-MINUTE QUICK OPPORTUNITY (NEW!)
    quick_opportunity: Optional[QuickTradingOpportunity] = Field(None, description="Quick trading setup for next 5-15 mins")


class DetailedMarketContext(BaseModel):
    """
    DETAILED LEVEL - Granular market analysis
    
    Use case: Deep market understanding, sector rotation, technical levels
    Suitable for: Swing and long-term traders
    """
    
    # Indian indices detailed analysis
    nifty_analysis: Optional[IndexDetailedAnalysis] = None
    banknifty_analysis: Optional[IndexDetailedAnalysis] = None
    midcap_analysis: Optional[IndexDetailedAnalysis] = None
    
    # Sector performance
    sectors: List[SectorPerformance] = Field(default_factory=list, description="All sector performances")
    
    # Top movers
    top_gainers: List[Dict[str, Any]] = Field(default_factory=list, description="Top 10 gainers with reasons")
    top_losers: List[Dict[str, Any]] = Field(default_factory=list, description="Top 10 losers with reasons")
    
    # Market internals
    advances: int = Field(..., description="Number of advancing stocks")
    declines: int = Field(..., description="Number of declining stocks")
    unchanged: int = Field(..., description="Number of unchanged stocks")
    new_highs: int = Field(..., description="52-week new highs")
    new_lows: int = Field(..., description="52-week new lows")
    
    # Volume analysis
    total_volume: Optional[Decimal] = Field(None, description="Total market volume")
    volume_vs_avg: Optional[Decimal] = Field(None, description="Volume vs 20-day average %")
    
    timestamp: datetime = Field(default_factory=datetime.now)


# ============================================================================
# STYLE-SPECIFIC CONTEXT
# ============================================================================

class IntradayContext(BaseModel):
    """
    Intraday trading specific context
    
    Focus: Real-time momentum, minute-level trends, volatility
    """
    
    # Time-based context
    market_phase: str = Field(..., description="Opening/Mid-session/Closing")
    time_remaining_minutes: int = Field(..., description="Minutes until market close")
    
    # Momentum indicators
    current_momentum: str = Field(..., description="Strong_bullish/bullish/neutral/bearish/strong_bearish")
    momentum_shift: str = Field(..., description="accelerating/stable/decelerating")
    
    # Volatility
    intraday_volatility: VolatilityLevel = Field(..., description="Intraday volatility level")
    price_range_percent: Optional[Decimal] = Field(None, description="Day high-low range %")
    
    # Volume profile
    volume_weighted_price: Optional[Decimal] = Field(None, description="VWAP")
    current_vs_vwap: Optional[Decimal] = Field(None, description="Current price vs VWAP %")
    
    # Key levels for scalping
    pivot_point: Optional[Decimal] = None
    r1: Optional[Decimal] = Field(None, description="Resistance 1")
    r2: Optional[Decimal] = Field(None, description="Resistance 2")
    s1: Optional[Decimal] = Field(None, description="Support 1")
    s2: Optional[Decimal] = Field(None, description="Support 2")
    
    # News/events impact
    news_driven_volatility: bool = Field(False, description="Is volatility news-driven?")
    high_impact_events_today: List[str] = Field(default_factory=list)
    
    # Trading opportunities
    breakout_candidates: List[str] = Field(default_factory=list, description="Stocks near breakout")
    reversal_candidates: List[str] = Field(default_factory=list, description="Stocks showing reversal")
    
    timestamp: datetime = Field(default_factory=datetime.now)


class SwingContext(BaseModel):
    """
    Swing trading specific context
    
    Focus: Multi-day patterns, momentum, sector rotation
    """
    
    # Trend analysis
    multi_day_trend: str = Field(..., description="5-day trend: uptrend/downtrend/sideways")
    trend_strength: TrendStrength
    trend_age_days: int = Field(..., description="How long current trend has been running")
    
    # Momentum
    weekly_momentum: str = Field(..., description="Strong/moderate/weak")
    momentum_divergence: bool = Field(False, description="Price-momentum divergence detected")
    
    # Pattern recognition
    chart_patterns: List[str] = Field(default_factory=list, description="Detected chart patterns")
    
    # Support/Resistance
    swing_support_levels: List[Decimal] = Field(default_factory=list, description="Key swing support levels")
    swing_resistance_levels: List[Decimal] = Field(default_factory=list, description="Key swing resistance levels")
    
    # Sector rotation
    hot_sectors: List[str] = Field(default_factory=list, description="Sectors showing strength")
    cold_sectors: List[str] = Field(default_factory=list, description="Sectors showing weakness")
    rotating_sectors: List[str] = Field(default_factory=list, description="Sectors in rotation")
    
    # Mean reversion opportunities
    oversold_stocks: List[str] = Field(default_factory=list, description="Quality stocks oversold")
    overbought_stocks: List[str] = Field(default_factory=list, description="Stocks overbought")
    
    # Risk factors
    risk_level: str = Field(..., description="low/medium/high")
    stop_loss_suggestion: str = Field(..., description="Suggested stop loss strategy")
    
    timestamp: datetime = Field(default_factory=datetime.now)


class LongTermContext(BaseModel):
    """
    Long-term investment specific context
    
    Focus: Macro trends, fundamentals, structural changes
    """
    
    # Macro environment
    economic_cycle: str = Field(..., description="Expansion/peak/contraction/trough")
    interest_rate_trend: str = Field(..., description="rising/falling/stable")
    inflation_trend: str = Field(..., description="rising/falling/stable")
    
    # Market valuation
    nifty_pe: Optional[Decimal] = Field(None, description="Nifty P/E ratio")
    nifty_pb: Optional[Decimal] = Field(None, description="Nifty P/B ratio")
    market_valuation: str = Field(..., description="overvalued/fair/undervalued")
    
    # Structural themes
    emerging_themes: List[str] = Field(default_factory=list, description="Emerging investment themes")
    declining_themes: List[str] = Field(default_factory=list, description="Declining themes")
    
    # Sector allocation
    recommended_sector_weights: Dict[str, Decimal] = Field(default_factory=dict, description="Sector allocation %")
    
    # Long-term opportunities
    value_opportunities: List[str] = Field(default_factory=list, description="Value stocks")
    growth_opportunities: List[str] = Field(default_factory=list, description="Growth stocks")
    dividend_opportunities: List[str] = Field(default_factory=list, description="High dividend yield")
    
    # Risk assessment
    systemic_risk_level: str = Field(..., description="low/medium/high")
    key_risks: List[str] = Field(default_factory=list, description="Key risks to watch")
    
    timestamp: datetime = Field(default_factory=datetime.now)


# ============================================================================
# UNIFIED ENHANCED CONTEXT RESPONSE
# ============================================================================

class EnhancedMarketContextRequest(BaseModel):
    """Request for enhanced hierarchical market context."""
    
    # Context levels to include
    include_primary: bool = Field(default=True, description="Include primary (high-level) context")
    include_detailed: bool = Field(default=True, description="Include detailed analysis")
    include_style_specific: bool = Field(default=True, description="Include trading style specific context")
    
    # Trading style preferences
    trading_styles: List[TradingStyle] = Field(
        default=[TradingStyle.ALL],
        description="Trading styles to optimize for"
    )
    
    # Specific symbols for detailed analysis
    focus_symbols: Optional[List[str]] = Field(None, max_length=10, description="Specific stocks for detailed analysis")
    
    # Feature flags
    include_sectors: bool = Field(default=True, description="Include sector analysis")
    include_technicals: bool = Field(default=True, description="Include technical indicators")
    include_opportunities: bool = Field(default=True, description="Include trading opportunities")
    
    # ML Integration (NEW!)
    include_ml_features: bool = Field(default=False, description="Include flattened ML-ready features (47+ features)")


class EnhancedMarketContextResponse(BaseModel):
    """
    Enhanced hierarchical market context response
    
    Designed for: Real-time trading recommendation systems
    Structure: Primary → Detailed → Style-specific
    """
    
    success: bool
    contract_version: Optional[str] = Field(
        None,
        description="Data contract version (e.g., '1.0.0')"
    )
    
    # PRIMARY LEVEL - Always included for quick overview
    primary_context: Optional[PrimaryMarketContext] = None
    
    # DETAILED LEVEL - Granular analysis
    detailed_context: Optional[DetailedMarketContext] = None
    
    # STYLE-SPECIFIC CONTEXT
    intraday_context: Optional[IntradayContext] = None
    swing_context: Optional[SwingContext] = None
    long_term_context: Optional[LongTermContext] = None
    
    # ML-READY FEATURE EXTRACTION (NEW!)
    ml_features: Optional[Dict[str, Any]] = Field(
        None,
        description="Flattened ML features ready for pandas/sklearn (47+ numeric & categorical features)"
    )
    
    # DATA QUALITY INFORMATION
    data_quality: Optional[Dict[str, Any]] = Field(
        None,
        description="Data quality report showing what is real vs approximated vs fallback"
    )
    
    # Meta information
    context_quality_score: float = Field(..., ge=0.0, le=1.0, description="Quality of context data")
    data_freshness_seconds: int = Field(..., description="Age of data in seconds")
    
    # Processing info
    processing_time_ms: float
    timestamp: datetime = Field(default_factory=datetime.now)
    
    # Messages/Warnings
    message: Optional[str] = None
    warnings: List[str] = Field(default_factory=list, description="Data quality warnings")
    
    # Data source breakdown - NEW
    data_source_summary: Optional[Dict[str, int]] = Field(
        None,
        description="Summary: {real: N, approximated: N, fallback: N}"
    )

