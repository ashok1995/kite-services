"""
Market Context Data Models - Market Level Only
===============================================

Clean models for market-level context without stock recommendations.
Provides market intelligence for understanding overall market environment.
"""

from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum
from pydantic import BaseModel, Field
from decimal import Decimal


# =============================================================================
# ENUMS
# =============================================================================

class MarketRegime(str, Enum):
    """Overall market regime."""
    BULLISH = "bullish"
    BEARISH = "bearish"
    SIDEWAYS = "sideways"
    VOLATILE = "volatile"
    TRENDING_UP = "trending_up"
    TRENDING_DOWN = "trending_down"


class VolatilityLevel(str, Enum):
    """Market volatility level."""
    VERY_LOW = "very_low"      # VIX < 12
    LOW = "low"                # VIX 12-16
    NORMAL = "normal"          # VIX 16-20
    ELEVATED = "elevated"      # VIX 20-25
    HIGH = "high"              # VIX 25-30
    VERY_HIGH = "very_high"    # VIX > 30


class TradingSession(str, Enum):
    """Current trading session."""
    PRE_MARKET = "pre_market"
    OPENING = "opening"
    MORNING = "morning"
    AFTERNOON = "afternoon"
    CLOSING = "closing"
    POST_MARKET = "post_market"


class GlobalSentiment(str, Enum):
    """Global market sentiment."""
    VERY_POSITIVE = "very_positive"
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    VERY_NEGATIVE = "very_negative"


# =============================================================================
# MARKET CONTEXT MODELS
# =============================================================================

class GlobalMarketData(BaseModel):
    """Global market indices and trends."""
    
    timestamp: datetime = Field(..., description="Data timestamp")
    
    # US Markets
    us_markets: Dict[str, Dict[str, float]] = Field(
        default_factory=dict, 
        description="US market indices (S&P 500, NASDAQ, Dow)"
    )
    
    # European Markets
    european_markets: Dict[str, Dict[str, float]] = Field(
        default_factory=dict,
        description="European market indices (FTSE, DAX, CAC)"
    )
    
    # Asian Markets
    asian_markets: Dict[str, Dict[str, float]] = Field(
        default_factory=dict,
        description="Asian market indices (Nikkei, Hang Seng, Shanghai)"
    )
    
    # Global sentiment
    global_sentiment: GlobalSentiment = Field(..., description="Overall global sentiment")
    global_momentum_score: Decimal = Field(..., ge=-100, le=100, description="Global momentum")
    
    # Overnight changes
    overnight_changes: Dict[str, Decimal] = Field(
        default_factory=dict,
        description="Overnight changes by region"
    )
    
    # Cross-market correlations
    correlations: Dict[str, Decimal] = Field(
        default_factory=dict,
        description="Cross-market correlations"
    )


class IndianMarketData(BaseModel):
    """Indian market indices and breadth."""
    
    timestamp: datetime = Field(..., description="Data timestamp")
    
    # Major indices
    indices: Dict[str, Dict[str, float]] = Field(
        default_factory=dict,
        description="Indian market indices (NIFTY, BANK NIFTY, etc.)"
    )
    
    # Market regime
    market_regime: MarketRegime = Field(..., description="Current market regime")
    volatility_level: VolatilityLevel = Field(..., description="Volatility level")
    
    # Market breadth
    advances: int = Field(..., ge=0, description="Advancing stocks")
    declines: int = Field(..., ge=0, description="Declining stocks")
    unchanged: int = Field(..., ge=0, description="Unchanged stocks")
    advance_decline_ratio: Decimal = Field(..., description="Advance/Decline ratio")
    
    # New highs/lows
    new_highs: int = Field(..., ge=0, description="New 52-week highs")
    new_lows: int = Field(..., ge=0, description="New 52-week lows")
    
    # Volume data
    total_volume: Optional[int] = Field(None, description="Total market volume")
    volume_trend: str = Field(..., description="Volume trend (increasing/decreasing/stable)")


class VolatilityData(BaseModel):
    """Market volatility and risk indicators."""
    
    timestamp: datetime = Field(..., description="Data timestamp")
    
    # VIX data
    india_vix: Decimal = Field(..., description="India VIX level")
    vix_change: Decimal = Field(..., description="VIX change from previous day")
    vix_trend: str = Field(..., description="VIX trend direction")
    
    # Volatility classification
    volatility_level: VolatilityLevel = Field(..., description="Current volatility level")
    
    # Risk indicators
    fear_greed_index: int = Field(..., ge=0, le=100, description="Fear & Greed index")
    put_call_ratio: Optional[Decimal] = Field(None, description="Put/Call ratio")
    
    # Expected ranges
    expected_daily_range: Decimal = Field(..., description="Expected daily range %")


class SectorData(BaseModel):
    """Sector performance and rotation."""
    
    timestamp: datetime = Field(..., description="Data timestamp")
    
    # Sector performance
    sector_performance: Dict[str, Decimal] = Field(
        default_factory=dict,
        description="Sector performance percentages"
    )
    
    # Sector classification
    leading_sectors: List[str] = Field(default_factory=list, description="Top performing sectors")
    lagging_sectors: List[str] = Field(default_factory=list, description="Worst performing sectors")
    
    # Rotation analysis
    rotation_stage: str = Field(..., description="Current sector rotation stage")
    sector_breadth: Dict[str, int] = Field(
        default_factory=dict,
        description="Sector breadth (advancing vs declining)"
    )


class InstitutionalData(BaseModel):
    """Institutional activity data."""
    
    timestamp: datetime = Field(..., description="Data timestamp")
    
    # FII/DII flows
    fii_flow: Optional[Decimal] = Field(None, description="FII net flow (crores)")
    dii_flow: Optional[Decimal] = Field(None, description="DII net flow (crores)")
    net_institutional_flow: Optional[Decimal] = Field(None, description="Net institutional flow")
    
    # Flow trends
    fii_trend: str = Field(..., description="FII flow trend (buying/selling/neutral)")
    dii_trend: str = Field(..., description="DII flow trend")
    
    # Institutional sentiment
    institutional_sentiment: str = Field(..., description="Overall institutional sentiment")


class CurrencyData(BaseModel):
    """Currency and commodity data."""
    
    timestamp: datetime = Field(..., description="Data timestamp")
    
    # Currency
    usd_inr: Optional[Decimal] = Field(None, description="USD/INR exchange rate")
    usd_inr_change: Optional[Decimal] = Field(None, description="USD/INR change %")
    
    # Commodities
    crude_oil: Optional[Decimal] = Field(None, description="Crude oil price")
    gold: Optional[Decimal] = Field(None, description="Gold price")
    
    # Trends
    currency_trend: str = Field(..., description="Currency trend impact")
    commodity_impact: str = Field(..., description="Commodity impact on markets")


# =============================================================================
# MAIN MARKET CONTEXT MODEL
# =============================================================================

class MarketContextData(BaseModel):
    """Comprehensive market context - market level only."""
    
    timestamp: datetime = Field(..., description="Context timestamp")
    request_id: str = Field(..., description="Request identifier")
    
    # Core market data
    global_data: GlobalMarketData = Field(..., description="Global market data")
    indian_data: IndianMarketData = Field(..., description="Indian market data")
    volatility_data: VolatilityData = Field(..., description="Volatility and risk data")
    sector_data: SectorData = Field(..., description="Sector performance data")
    institutional_data: InstitutionalData = Field(..., description="Institutional flow data")
    currency_data: CurrencyData = Field(..., description="Currency and commodity data")
    
    # Market summary
    overall_market_regime: MarketRegime = Field(..., description="Overall market regime")
    market_strength: Decimal = Field(..., ge=0, le=100, description="Market strength score")
    global_influence: Decimal = Field(..., ge=0, le=100, description="Global influence on Indian markets")
    
    # Trading environment
    trading_session: TradingSession = Field(..., description="Current trading session")
    session_bias: str = Field(..., description="Session trading bias")
    liquidity_conditions: str = Field(..., description="Market liquidity conditions")
    
    # Market insights (descriptive only)
    key_observations: List[str] = Field(default_factory=list, description="Key market observations")
    market_themes: List[str] = Field(default_factory=list, description="Current market themes")
    risk_factors: List[str] = Field(default_factory=list, description="Current risk factors")
    
    # Performance metrics
    data_quality_score: Decimal = Field(..., ge=0, le=100, description="Data quality score")
    processing_time_ms: int = Field(..., ge=0, description="Processing time")


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class MarketContextRequest(BaseModel):
    """Request for market context data."""
    
    # Context options
    include_global_data: bool = Field(default=True, description="Include global market data")
    include_sector_data: bool = Field(default=True, description="Include sector analysis")
    include_institutional_data: bool = Field(default=True, description="Include institutional flows")
    include_currency_data: bool = Field(default=True, description="Include currency/commodity data")
    
    # Data freshness
    real_time_priority: bool = Field(default=True, description="Prioritize real-time data")


class MarketContextResponse(BaseModel):
    """Response with market context data."""
    
    timestamp: datetime = Field(..., description="Response timestamp")
    request_id: str = Field(..., description="Request identifier")
    
    # Market context
    market_context: MarketContextData = Field(..., description="Market context data")
    
    # Summary
    market_summary: str = Field(..., description="Market summary description")
    
    # Performance
    processing_time_ms: int = Field(..., ge=0, description="Processing time")
    data_sources: List[str] = Field(default_factory=list, description="Data sources used")


class QuickMarketContextResponse(BaseModel):
    """Quick market context response."""
    
    timestamp: datetime = Field(..., description="Response timestamp")
    
    # Essential context
    market_regime: str = Field(..., description="Current market regime")
    global_sentiment: str = Field(..., description="Global sentiment")
    volatility_level: str = Field(..., description="Volatility level")
    
    # Key metrics
    india_vix: Decimal = Field(..., description="India VIX")
    advance_decline_ratio: Decimal = Field(..., description="A/D ratio")
    global_influence: Decimal = Field(..., description="Global influence %")
    
    # Session info
    trading_session: str = Field(..., description="Current session")
    session_bias: str = Field(..., description="Session bias")
    
    # Leading sectors
    leading_sectors: List[str] = Field(default_factory=list, description="Leading sectors")
    
    # Processing
    processing_time_ms: int = Field(..., ge=0, description="Processing time")


# Export models
__all__ = [
    "MarketContextRequest",
    "MarketContextResponse",
    "MarketContextData", 
    "QuickMarketContextResponse",
    "GlobalMarketData",
    "IndianMarketData",
    "VolatilityData",
    "SectorData",
    "InstitutionalData",
    "CurrencyData",
    "MarketRegime",
    "VolatilityLevel",
    "TradingSession",
    "GlobalSentiment"
]
