"""
Unified API Models for Consolidated Kite Services

This module contains all Pydantic models for the consolidated API endpoints.
Consolidates functionality from 60+ endpoints into 8 focused endpoints.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field


# ============================================================================
# ENUMS
# ============================================================================

class Exchange(str, Enum):
    """Supported exchanges."""
    NSE = "NSE"
    BSE = "BSE"
    NFO = "NFO"
    BFO = "BFO"
    CDS = "CDS"
    MCX = "MCX"


class Interval(str, Enum):
    """Time intervals for historical data."""
    MINUTE = "minute"
    MINUTE_3 = "3minute"
    MINUTE_5 = "5minute"
    MINUTE_15 = "15minute"
    MINUTE_30 = "30minute"
    HOUR = "hour"
    DAY = "day"


class AuthStatus(str, Enum):
    """Authentication status."""
    AUTHENTICATED = "authenticated"
    EXPIRED = "expired"
    INVALID = "invalid"
    NOT_CONFIGURED = "not_configured"


class MarketStatus(str, Enum):
    """Market status."""
    OPEN = "open"
    CLOSED = "closed"
    PRE_MARKET = "pre_market"
    POST_MARKET = "post_market"


# ============================================================================
# AUTH MODULE MODELS
# ============================================================================

class AuthRequest(BaseModel):
    """Authentication request."""
    request_token: Optional[str] = Field(None, description="Request token from Kite login")
    access_token: Optional[str] = Field(None, description="Existing access token to validate")
    api_key: Optional[str] = Field(None, description="API key")
    api_secret: Optional[str] = Field(None, description="API secret")


class AuthResponse(BaseModel):
    """Authentication response."""
    status: AuthStatus
    access_token: Optional[str] = Field(None, description="Access token")
    user_id: Optional[str] = Field(None, description="User ID")
    user_name: Optional[str] = Field(None, description="User name")
    email: Optional[str] = Field(None, description="User email")
    broker: Optional[str] = Field(None, description="Broker")
    exchanges: Optional[List[str]] = Field(None, description="Enabled exchanges")
    products: Optional[List[str]] = Field(None, description="Enabled products")
    order_types: Optional[List[str]] = Field(None, description="Enabled order types")
    message: Optional[str] = Field(None, description="Status message")
    timestamp: datetime = Field(default_factory=datetime.now)


class AuthStatusResponse(BaseModel):
    """Authentication status response."""
    status: AuthStatus
    authenticated: bool
    user_id: Optional[str] = None
    user_name: Optional[str] = None
    broker: Optional[str] = None
    last_updated: Optional[datetime] = None
    token_expiry: Optional[datetime] = None
    message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


# ============================================================================
# MARKET DATA MODULE MODELS
# ============================================================================

class MarketDataRequest(BaseModel):
    """Universal market data request."""
    symbols: List[str] = Field(..., min_length=1, max_length=50, description="Stock symbols")
    exchange: Exchange = Field(default=Exchange.NSE, description="Exchange")
    data_type: str = Field(default="quote", description="Data type: quote, historical, fundamentals")
    
    # Historical data parameters
    from_date: Optional[datetime] = Field(None, description="From date for historical data")
    to_date: Optional[datetime] = Field(None, description="To date for historical data")
    interval: Optional[Interval] = Field(None, description="Time interval for historical data")
    
    # Additional options
    include_depth: bool = Field(default=False, description="Include market depth")
    include_circuit_limits: bool = Field(default=True, description="Include circuit limits")


class StockData(BaseModel):
    """Stock data model."""
    symbol: str
    instrument_token: Optional[int] = None
    last_price: Optional[Decimal] = None
    open: Optional[Decimal] = None
    high: Optional[Decimal] = None
    low: Optional[Decimal] = None
    close: Optional[Decimal] = None
    volume: Optional[int] = None
    average_price: Optional[Decimal] = None
    ohlc: Optional[Dict[str, Decimal]] = None
    net_change: Optional[Decimal] = None
    net_change_percent: Optional[Decimal] = None
    oi: Optional[int] = None
    oi_day_high: Optional[int] = None
    oi_day_low: Optional[int] = None
    timestamp: Optional[datetime] = None
    last_trade_time: Optional[datetime] = None


class MarketDataResponse(BaseModel):
    """Market data response."""
    success: bool
    data: Dict[str, StockData] = Field(default_factory=dict, description="Stock data by symbol")
    total_symbols: int
    successful_symbols: int
    failed_symbols: int
    failed_symbols_list: List[str] = Field(default_factory=list)
    processing_time_ms: float
    timestamp: datetime = Field(default_factory=datetime.now)
    message: Optional[str] = None


class MarketStatusResponse(BaseModel):
    """Market status response."""
    market_status: MarketStatus
    market_open: bool
    current_time: datetime = Field(default_factory=datetime.now)
    next_open: Optional[datetime] = None
    next_close: Optional[datetime] = None
    exchanges: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    message: Optional[str] = None


class InstrumentInfo(BaseModel):
    """Instrument information."""
    instrument_token: int
    exchange_token: Optional[int] = None  # Not available from Kite API
    tradingsymbol: str
    name: str
    last_price: Optional[Decimal] = None
    expiry: Optional[datetime] = None
    strike: Optional[Decimal] = None
    tick_size: Optional[Decimal] = None
    lot_size: int
    instrument_type: str
    segment: Optional[str] = None  # Not available from Kite API
    exchange: str


class InstrumentsResponse(BaseModel):
    """Instruments response."""
    success: bool
    instruments: List[InstrumentInfo] = Field(default_factory=list)
    total_count: int
    exchanges: List[str] = Field(default_factory=list)
    message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


# ============================================================================
# ANALYSIS MODULE MODELS
# ============================================================================

class MarketContextRequest(BaseModel):
    """Market context analysis request."""
    symbols: Optional[List[str]] = Field(None, max_length=20, description="Specific symbols to analyze")
    include_global: bool = Field(default=True, description="Include global market context")
    include_indian: bool = Field(default=True, description="Include Indian market context")
    include_sentiment: bool = Field(default=True, description="Include market sentiment")
    include_technical: bool = Field(default=True, description="Include technical analysis")


class GlobalMarketData(BaseModel):
    """Global market data."""
    market: str
    index: str
    last_price: Optional[Decimal] = None
    change: Optional[Decimal] = None
    change_percent: Optional[Decimal] = None
    timestamp: Optional[datetime] = None


class MarketSentiment(BaseModel):
    """Market sentiment data."""
    overall_sentiment: str  # bullish, bearish, neutral
    fear_greed_index: Optional[int] = None
    vix: Optional[Decimal] = None
    put_call_ratio: Optional[Decimal] = None
    advance_decline_ratio: Optional[Decimal] = None
    timestamp: Optional[datetime] = None


class TechnicalAnalysis(BaseModel):
    """Technical analysis data."""
    symbol: str
    trend: Optional[str] = None  # bullish, bearish, sideways
    support_levels: List[Decimal] = Field(default_factory=list)
    resistance_levels: List[Decimal] = Field(default_factory=list)
    moving_averages: Dict[str, Decimal] = Field(default_factory=dict)
    rsi: Optional[Decimal] = None
    macd: Optional[Dict[str, Decimal]] = None
    bollinger_bands: Optional[Dict[str, Decimal]] = None
    timestamp: Optional[datetime] = None


class MarketContextResponse(BaseModel):
    """Market context response."""
    success: bool
    global_markets: List[GlobalMarketData] = Field(default_factory=list)
    indian_markets: List[GlobalMarketData] = Field(default_factory=list)
    market_sentiment: Optional[MarketSentiment] = None
    technical_analysis: List[TechnicalAnalysis] = Field(default_factory=list)
    processing_time_ms: float
    timestamp: datetime = Field(default_factory=datetime.now)
    message: Optional[str] = None


class IntelligenceRequest(BaseModel):
    """Stock intelligence request."""
    symbol: str = Field(..., description="Stock symbol")
    include_trends: bool = Field(default=True, description="Include trend analysis")
    include_levels: bool = Field(default=True, description="Include support/resistance levels")
    include_signals: bool = Field(default=True, description="Include trading signals")
    time_horizon: str = Field(default="short", description="Analysis time horizon: short, medium, long")


class TradingSignal(BaseModel):
    """Trading signal."""
    signal_type: str  # buy, sell, hold
    confidence: float = Field(..., ge=0.0, le=1.0, description="Signal confidence (0-1)")
    strength: str = Field(..., description="Signal strength: weak, medium, strong")
    reason: str = Field(..., description="Signal reason")
    price_target: Optional[Decimal] = None
    stop_loss: Optional[Decimal] = None
    timestamp: Optional[datetime] = None


class StockIntelligence(BaseModel):
    """Stock intelligence data."""
    symbol: str
    overall_trend: Optional[str] = None
    trend_strength: Optional[str] = None
    support_levels: List[Decimal] = Field(default_factory=list)
    resistance_levels: List[Decimal] = Field(default_factory=list)
    key_levels: List[Decimal] = Field(default_factory=list)
    trading_signals: List[TradingSignal] = Field(default_factory=list)
    risk_level: Optional[str] = None  # low, medium, high
    volatility: Optional[Decimal] = None
    momentum: Optional[str] = None
    timestamp: Optional[datetime] = None


class IntelligenceResponse(BaseModel):
    """Stock intelligence response."""
    success: bool
    intelligence: Optional[StockIntelligence] = None
    processing_time_ms: float
    timestamp: datetime = Field(default_factory=datetime.now)
    message: Optional[str] = None


# ============================================================================
# TRADING MODULE MODELS
# ============================================================================

class Position(BaseModel):
    """Position information."""
    symbol: str
    instrument_token: Optional[int] = None
    quantity: int
    average_price: Optional[Decimal] = None
    last_price: Optional[Decimal] = None
    pnl: Optional[Decimal] = None
    pnl_percent: Optional[Decimal] = None
    day_pnl: Optional[Decimal] = None
    day_pnl_percent: Optional[Decimal] = None
    product: str
    exchange: str
    instrument_type: str


class Holding(BaseModel):
    """Holding information."""
    symbol: str
    instrument_token: Optional[int] = None
    quantity: int
    average_price: Optional[Decimal] = None
    last_price: Optional[Decimal] = None
    pnl: Optional[Decimal] = None
    pnl_percent: Optional[Decimal] = None
    day_pnl: Optional[Decimal] = None
    day_pnl_percent: Optional[Decimal] = None
    product: str
    exchange: str
    instrument_type: str


class TradingStatusResponse(BaseModel):
    """Trading status response."""
    success: bool
    authenticated: bool
    user_id: Optional[str] = None
    user_name: Optional[str] = None
    broker: Optional[str] = None
    enabled: bool = Field(default=False, description="Trading enabled")
    positions: List[Position] = Field(default_factory=list)
    holdings: List[Holding] = Field(default_factory=list)
    total_positions: int = Field(default=0)
    total_holdings: int = Field(default=0)
    total_pnl: Optional[Decimal] = None
    day_pnl: Optional[Decimal] = None
    processing_time_ms: float
    timestamp: datetime = Field(default_factory=datetime.now)
    message: Optional[str] = None


# ============================================================================
# ERROR MODELS
# ============================================================================

class ErrorResponse(BaseModel):
    """Error response."""
    success: bool = False
    error: str
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    service: str
    version: str
    environment: str
    timestamp: datetime = Field(default_factory=datetime.now)
    services: Optional[Dict[str, Any]] = None
