"""
Market Intelligence Models
==========================

Advanced Pydantic models for market intelligence, trends, and range analysis.
Following workspace rules:
- All data contracts use Pydantic models
- Enums for categorical data
- Comprehensive validation
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
from pydantic import BaseModel, Field, validator
from decimal import Decimal


class TrendDirection(str, Enum):
    """Trend direction enumeration."""
    STRONG_BULLISH = "strong_bullish"
    BULLISH = "bullish"
    WEAK_BULLISH = "weak_bullish"
    SIDEWAYS = "sideways"
    WEAK_BEARISH = "weak_bearish"
    BEARISH = "bearish"
    STRONG_BEARISH = "strong_bearish"


class TrendStrength(str, Enum):
    """Trend strength enumeration."""
    VERY_STRONG = "very_strong"
    STRONG = "strong"
    MODERATE = "moderate"
    WEAK = "weak"
    VERY_WEAK = "very_weak"


class RangeLevel(str, Enum):
    """Range level type enumeration."""
    STRONG_RESISTANCE = "strong_resistance"
    RESISTANCE = "resistance"
    WEAK_RESISTANCE = "weak_resistance"
    CURRENT_PRICE = "current_price"
    WEAK_SUPPORT = "weak_support"
    SUPPORT = "support"
    STRONG_SUPPORT = "strong_support"


class MarketRegime(str, Enum):
    """Market regime enumeration."""
    TRENDING_UP = "trending_up"
    TRENDING_DOWN = "trending_down"
    RANGE_BOUND = "range_bound"
    BREAKOUT = "breakout"
    BREAKDOWN = "breakdown"
    VOLATILE = "volatile"


class VolatilityLevel(str, Enum):
    """Volatility level enumeration."""
    VERY_LOW = "very_low"
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    VERY_HIGH = "very_high"
    EXTREME = "extreme"


# Core Intelligence Models

class TrendAnalysis(BaseModel):
    """Comprehensive trend analysis."""
    
    symbol: str = Field(..., description="Stock symbol")
    timeframe: str = Field(..., description="Analysis timeframe")
    
    # Primary trend
    primary_trend: TrendDirection = Field(..., description="Primary trend direction")
    trend_strength: TrendStrength = Field(..., description="Trend strength")
    trend_confidence: Decimal = Field(..., ge=0, le=100, description="Trend confidence %")
    
    # Trend metrics
    trend_duration_days: int = Field(..., ge=0, description="Trend duration in days")
    trend_start_price: Decimal = Field(..., gt=0, description="Trend starting price")
    trend_current_price: Decimal = Field(..., gt=0, description="Current price")
    trend_change_percent: Decimal = Field(..., description="Total trend change %")
    
    # Moving averages
    sma_20: Decimal = Field(..., description="20-period SMA")
    sma_50: Decimal = Field(..., description="50-period SMA")
    ema_12: Decimal = Field(..., description="12-period EMA")
    ema_26: Decimal = Field(..., description="26-period EMA")
    
    # Trend indicators
    macd: Decimal = Field(..., description="MACD value")
    macd_signal: Decimal = Field(..., description="MACD signal line")
    macd_histogram: Decimal = Field(..., description="MACD histogram")
    
    # Momentum
    rsi: Decimal = Field(..., ge=0, le=100, description="RSI (14 period)")
    momentum: Decimal = Field(..., description="Price momentum")
    
    # Meta
    last_updated: datetime = Field(..., description="Last update timestamp")
    analysis_confidence: Decimal = Field(..., ge=0, le=100, description="Overall analysis confidence")


class RangeLevelAnalysis(BaseModel):
    """Support and resistance range level analysis."""
    
    symbol: str = Field(..., description="Stock symbol")
    current_price: Decimal = Field(..., gt=0, description="Current price")
    
    # Key levels
    strong_resistance: List[Decimal] = Field(default_factory=list, description="Strong resistance levels")
    resistance: List[Decimal] = Field(default_factory=list, description="Resistance levels")
    weak_resistance: List[Decimal] = Field(default_factory=list, description="Weak resistance levels")
    
    strong_support: List[Decimal] = Field(default_factory=list, description="Strong support levels")
    support: List[Decimal] = Field(default_factory=list, description="Support levels")
    weak_support: List[Decimal] = Field(default_factory=list, description="Weak support levels")
    
    # Range analysis
    current_range_high: Decimal = Field(..., description="Current range high")
    current_range_low: Decimal = Field(..., description="Current range low")
    range_width: Decimal = Field(..., ge=0, description="Range width")
    range_position: Decimal = Field(..., ge=0, le=100, description="Position in range %")
    
    # Breakout analysis
    breakout_probability: Decimal = Field(..., ge=0, le=100, description="Breakout probability %")
    breakdown_probability: Decimal = Field(..., ge=0, le=100, description="Breakdown probability %")
    
    # Pivot points
    pivot_point: Decimal = Field(..., description="Pivot point")
    r1: Decimal = Field(..., description="Resistance 1")
    r2: Decimal = Field(..., description="Resistance 2")
    r3: Decimal = Field(..., description="Resistance 3")
    s1: Decimal = Field(..., description="Support 1")
    s2: Decimal = Field(..., description="Support 2")
    s3: Decimal = Field(..., description="Support 3")
    
    # Meta
    last_updated: datetime = Field(..., description="Last update timestamp")
    confidence_level: Decimal = Field(..., ge=0, le=100, description="Analysis confidence")


class MarketIntelligence(BaseModel):
    """Advanced market intelligence and context."""
    
    symbol: str = Field(..., description="Stock symbol")
    timestamp: datetime = Field(..., description="Analysis timestamp")
    
    # Market regime
    market_regime: MarketRegime = Field(..., description="Current market regime")
    volatility_level: VolatilityLevel = Field(..., description="Volatility level")
    
    # Price action
    price_action_score: Decimal = Field(..., ge=-100, le=100, description="Price action score")
    momentum_score: Decimal = Field(..., ge=-100, le=100, description="Momentum score")
    volume_profile: str = Field(..., description="Volume profile analysis")
    
    # Risk metrics
    beta: Decimal = Field(..., description="Beta coefficient")
    sharpe_ratio: Decimal = Field(..., description="Sharpe ratio")
    max_drawdown: Decimal = Field(..., le=0, description="Maximum drawdown %")
    value_at_risk: Decimal = Field(..., description="1-day VaR %")
    
    # Correlation analysis
    nifty_correlation: Decimal = Field(..., ge=-1, le=1, description="Correlation with NIFTY")
    sector_correlation: Decimal = Field(..., ge=-1, le=1, description="Correlation with sector")
    
    # Sentiment indicators
    put_call_ratio: Optional[Decimal] = Field(None, description="Put/Call ratio")
    options_sentiment: Optional[str] = Field(None, description="Options sentiment")
    news_sentiment: Optional[str] = Field(None, description="News sentiment")
    
    # Trading signals
    buy_signals: List[str] = Field(default_factory=list, description="Active buy signals")
    sell_signals: List[str] = Field(default_factory=list, description="Active sell signals")
    signal_strength: Decimal = Field(..., ge=0, le=100, description="Signal strength %")


class SectorContext(BaseModel):
    """Sector-specific market context."""
    
    sector_name: str = Field(..., description="Sector name")
    
    # Performance metrics
    day_change: Decimal = Field(..., description="Day change %")
    week_change: Decimal = Field(..., description="Week change %")
    month_change: Decimal = Field(..., description="Month change %")
    ytd_change: Decimal = Field(..., description="Year-to-date change %")
    
    # Sector trend
    trend: TrendDirection = Field(..., description="Sector trend")
    momentum: Decimal = Field(..., description="Sector momentum")
    
    # Top performers
    top_gainers: List[Dict[str, Any]] = Field(default_factory=list, description="Top gaining stocks")
    top_losers: List[Dict[str, Any]] = Field(default_factory=list, description="Top losing stocks")
    
    # Sector metrics
    avg_pe_ratio: Optional[Decimal] = Field(None, description="Average PE ratio")
    avg_market_cap: Optional[Decimal] = Field(None, description="Average market cap")
    total_volume: Optional[int] = Field(None, description="Total sector volume")
    
    last_updated: datetime = Field(..., description="Last update timestamp")


class MarketBreadth(BaseModel):
    """Market breadth analysis."""
    
    timestamp: datetime = Field(..., description="Analysis timestamp")
    
    # Basic breadth
    advances: int = Field(..., ge=0, description="Advancing stocks")
    declines: int = Field(..., ge=0, description="Declining stocks")
    unchanged: int = Field(..., ge=0, description="Unchanged stocks")
    
    # Advanced breadth
    new_highs: int = Field(..., ge=0, description="New 52-week highs")
    new_lows: int = Field(..., ge=0, description="New 52-week lows")
    up_volume: int = Field(..., ge=0, description="Up volume")
    down_volume: int = Field(..., ge=0, description="Down volume")
    
    # Breadth ratios
    advance_decline_ratio: Decimal = Field(..., description="Advance/Decline ratio")
    up_down_volume_ratio: Decimal = Field(..., description="Up/Down volume ratio")
    high_low_ratio: Decimal = Field(..., description="New High/Low ratio")
    
    # Breadth indicators
    mcclellan_oscillator: Decimal = Field(..., description="McClellan Oscillator")
    arms_index: Decimal = Field(..., description="Arms Index (TRIN)")
    breadth_momentum: Decimal = Field(..., description="Breadth momentum")


class EnhancedMarketContext(BaseModel):
    """Enhanced market context with comprehensive intelligence."""
    
    timestamp: datetime = Field(..., description="Context timestamp")
    request_id: str = Field(..., description="Request identifier")
    
    # Basic market info
    market_status: str = Field(..., description="Market status")
    trading_session: str = Field(..., description="Trading session")
    
    # Market regime
    overall_regime: MarketRegime = Field(..., description="Overall market regime")
    volatility_regime: VolatilityLevel = Field(..., description="Volatility regime")
    
    # Indices with trends
    indices: List[Dict[str, Any]] = Field(default_factory=list, description="Market indices with trends")
    
    # Market breadth
    market_breadth: MarketBreadth = Field(..., description="Market breadth analysis")
    
    # Sector analysis
    sector_context: Dict[str, SectorContext] = Field(default_factory=dict, description="Sector-wise context")
    
    # Economic indicators
    vix: Decimal = Field(..., description="Volatility index")
    put_call_ratio: Decimal = Field(..., description="Put/Call ratio")
    fear_greed_index: int = Field(..., ge=0, le=100, description="Fear & Greed index")
    
    # Currency and commodities
    usd_inr: Optional[Decimal] = Field(None, description="USD/INR rate")
    crude_oil: Optional[Decimal] = Field(None, description="Crude oil price")
    gold: Optional[Decimal] = Field(None, description="Gold price")
    
    # FII/DII activity
    fii_activity: Optional[Dict[str, Decimal]] = Field(None, description="FII activity")
    dii_activity: Optional[Dict[str, Decimal]] = Field(None, description="DII activity")
    
    # Market themes
    hot_sectors: List[str] = Field(default_factory=list, description="Hot sectors")
    cold_sectors: List[str] = Field(default_factory=list, description="Cold sectors")
    market_themes: List[str] = Field(default_factory=list, description="Current market themes")
    
    # Analysis metadata
    data_sources: Dict[str, str] = Field(default_factory=dict, description="Data sources used")
    analysis_confidence: Decimal = Field(..., ge=0, le=100, description="Overall analysis confidence")
    processing_time_ms: Optional[int] = Field(None, description="Processing time")


class StockContextRequest(BaseModel):
    """Request for stock-specific context."""
    
    symbol: str = Field(..., description="Stock symbol")
    include_trends: bool = Field(default=True, description="Include trend analysis")
    include_ranges: bool = Field(default=True, description="Include range levels")
    include_intelligence: bool = Field(default=True, description="Include market intelligence")
    historical_days: int = Field(default=50, ge=10, le=200, description="Historical data for analysis")


class StockContextResponse(BaseModel):
    """Comprehensive stock context response."""
    
    symbol: str = Field(..., description="Stock symbol")
    timestamp: datetime = Field(..., description="Response timestamp")
    request_id: str = Field(..., description="Request identifier")
    
    # Core analysis
    trend_analysis: Optional[TrendAnalysis] = Field(None, description="Trend analysis")
    range_analysis: Optional[RangeLevelAnalysis] = Field(None, description="Range level analysis")
    market_intelligence: Optional[MarketIntelligence] = Field(None, description="Market intelligence")
    
    # Context summary
    summary: str = Field(..., description="Context summary")
    key_insights: List[str] = Field(default_factory=list, description="Key insights")
    trading_suggestions: List[str] = Field(default_factory=list, description="Trading suggestions")
    
    # Risk assessment
    risk_level: str = Field(..., description="Risk level")
    risk_factors: List[str] = Field(default_factory=list, description="Risk factors")
    
    # Performance metrics
    analysis_confidence: Decimal = Field(..., ge=0, le=100, description="Analysis confidence")
    processing_time_ms: int = Field(..., ge=0, description="Processing time")


class MarketContextRequest(BaseModel):
    """Request for enhanced market context."""
    
    symbols: Optional[List[str]] = Field(None, description="Specific symbols to analyze")
    include_breadth: bool = Field(default=True, description="Include market breadth")
    include_sectors: bool = Field(default=True, description="Include sector analysis")
    include_trends: bool = Field(default=True, description="Include trend analysis")
    include_intelligence: bool = Field(default=True, description="Include market intelligence")
    analysis_depth: str = Field(default="standard", description="Analysis depth: basic, standard, comprehensive")


class MarketContextResponse(BaseModel):
    """Enhanced market context response."""
    
    timestamp: datetime = Field(..., description="Response timestamp")
    request_id: str = Field(..., description="Request identifier")
    
    # Enhanced context
    market_context: EnhancedMarketContext = Field(..., description="Enhanced market context")
    
    # Stock-specific contexts (if symbols provided)
    stock_contexts: Dict[str, StockContextResponse] = Field(default_factory=dict, description="Stock contexts")
    
    # Summary insights
    market_summary: str = Field(..., description="Market summary")
    key_themes: List[str] = Field(default_factory=list, description="Key market themes")
    trading_environment: str = Field(..., description="Trading environment assessment")
    
    # Performance
    total_symbols_analyzed: int = Field(..., ge=0, description="Total symbols analyzed")
    processing_time_ms: int = Field(..., ge=0, description="Total processing time")
    data_quality_score: Decimal = Field(..., ge=0, le=100, description="Data quality score")
