"""
Consolidated API Data Models
============================

Pydantic models for consolidated API endpoints following workspace rules:
- All data contracts use Pydantic models
- Enums for all categorical data
- Comprehensive validation and documentation
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from pydantic import BaseModel, Field, validator
from decimal import Decimal


class DataScope(str, Enum):
    """Data scope for market data requests."""
    BASIC = "basic"
    STANDARD = "standard" 
    COMPREHENSIVE = "comprehensive"
    FULL = "full"


class TimeFrame(str, Enum):
    """Time frame for historical data."""
    INTRADAY = "intraday"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class MarketStatus(str, Enum):
    """Market status enumeration."""
    OPEN = "open"
    CLOSED = "closed"
    PRE_MARKET = "pre_market"
    POST_MARKET = "post_market"
    UNKNOWN = "unknown"


class TradingSession(str, Enum):
    """Trading session enumeration."""
    PRE_MARKET = "pre_market"
    REGULAR = "regular"
    POST_MARKET = "post_market"
    CLOSED = "closed"


class DataSource(str, Enum):
    """Data source enumeration."""
    KITE_CONNECT = "kite_connect"
    YAHOO_FINANCE = "yahoo_finance"
    MARKET_CONTEXT_SERVICE = "market_context_service"
    MOCK = "mock"


# Core Data Models

class ConsolidatedStockData(BaseModel):
    """Comprehensive stock data model with validation."""
    
    # Basic Info (always included)
    symbol: str = Field(..., description="Stock symbol")
    name: Optional[str] = Field(None, description="Company name")
    exchange: str = Field("NSE", description="Exchange")
    
    # Price Data (always included)
    last_price: Decimal = Field(..., description="Last traded price")
    change: Decimal = Field(..., description="Price change")
    change_percent: Decimal = Field(..., description="Percentage change")
    volume: int = Field(..., ge=0, description="Trading volume")
    
    # OHLC Data (Standard+)
    high: Optional[Decimal] = Field(None, description="Day high")
    low: Optional[Decimal] = Field(None, description="Day low")
    open: Optional[Decimal] = Field(None, description="Opening price")
    previous_close: Optional[Decimal] = Field(None, description="Previous close")
    
    # Market Data (Standard+)
    market_cap: Optional[Decimal] = Field(None, description="Market capitalization")
    avg_volume: Optional[int] = Field(None, ge=0, description="Average volume")
    
    # Technical Indicators (Comprehensive+)
    rsi: Optional[Decimal] = Field(None, ge=0, le=100, description="RSI (14 period)")
    sma_20: Optional[Decimal] = Field(None, description="SMA (20 period)")
    ema_12: Optional[Decimal] = Field(None, description="EMA (12 period)")
    bollinger_upper: Optional[Decimal] = Field(None, description="Bollinger upper band")
    bollinger_lower: Optional[Decimal] = Field(None, description="Bollinger lower band")
    
    # Fundamentals (Comprehensive+)
    pe_ratio: Optional[Decimal] = Field(None, description="Price to earnings ratio")
    pb_ratio: Optional[Decimal] = Field(None, description="Price to book ratio")
    dividend_yield: Optional[Decimal] = Field(None, ge=0, description="Dividend yield")
    
    # Sentiment & News (Full)
    news_sentiment: Optional[str] = Field(None, description="News sentiment")
    analyst_rating: Optional[str] = Field(None, description="Analyst rating")
    
    # Metadata
    timestamp: datetime = Field(..., description="Data timestamp")
    market_status: MarketStatus = Field(..., description="Market status")
    data_sources: Dict[str, DataSource] = Field(default_factory=dict, description="Data sources used")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            Decimal: lambda v: float(v),
            datetime: lambda v: v.isoformat()
        }
    
    @validator('change_percent')
    def validate_change_percent(cls, v):
        """Validate change percentage is reasonable."""
        if abs(v) > 50:  # More than 50% change is unusual
            raise ValueError('Change percentage seems unrealistic')
        return v


class HistoricalCandle(BaseModel):
    """Historical price candle with validation."""
    
    timestamp: datetime = Field(..., description="Candle timestamp")
    open: Decimal = Field(..., gt=0, description="Opening price")
    high: Decimal = Field(..., gt=0, description="High price")
    low: Decimal = Field(..., gt=0, description="Low price")
    close: Decimal = Field(..., gt=0, description="Closing price")
    volume: int = Field(..., ge=0, description="Volume")
    
    @validator('high')
    def validate_high(cls, v, values):
        """Validate high is highest price."""
        if 'low' in values and v < values['low']:
            raise ValueError('High must be >= low')
        return v
    
    @validator('low')
    def validate_low(cls, v, values):
        """Validate low is lowest price."""
        if 'high' in values and v > values['high']:
            raise ValueError('Low must be <= high')
        return v


class ConsolidatedHistoricalData(BaseModel):
    """Historical data with analytics and validation."""
    
    symbol: str = Field(..., description="Stock symbol")
    timeframe: TimeFrame = Field(..., description="Data timeframe")
    from_date: datetime = Field(..., description="Start date")
    to_date: datetime = Field(..., description="End date")
    candles: List[HistoricalCandle] = Field(..., description="Price candles")
    
    # Analytics
    total_candles: int = Field(..., ge=0, description="Total number of candles")
    price_change: Decimal = Field(..., description="Total price change")
    price_change_percent: Decimal = Field(..., description="Total percentage change")
    volume_avg: Decimal = Field(..., ge=0, description="Average volume")
    volatility: Decimal = Field(..., ge=0, description="Price volatility")
    high_period: Decimal = Field(..., gt=0, description="Period high")
    low_period: Decimal = Field(..., gt=0, description="Period low")
    
    @validator('total_candles')
    def validate_candle_count(cls, v, values):
        """Validate candle count matches actual candles."""
        if 'candles' in values and len(values['candles']) != v:
            raise ValueError('Total candles count does not match actual candles')
        return v


class MarketIndex(BaseModel):
    """Market index data with validation."""
    
    symbol: str = Field(..., description="Index symbol")
    name: str = Field(..., description="Index name")
    value: Decimal = Field(..., gt=0, description="Index value")
    change: Decimal = Field(..., description="Index change")
    change_percent: Decimal = Field(..., description="Percentage change")
    timestamp: datetime = Field(..., description="Data timestamp")
    data_source: DataSource = Field(default=DataSource.YAHOO_FINANCE, description="Data source")


class ConsolidatedMarketContext(BaseModel):
    """Comprehensive market context with validation."""
    
    timestamp: datetime = Field(..., description="Context timestamp")
    market_status: MarketStatus = Field(..., description="Market status")
    trading_session: TradingSession = Field(..., description="Trading session")
    
    # Major Indices
    indices: List[MarketIndex] = Field(default_factory=list, description="Market indices")
    
    # Market Metrics
    advances: int = Field(..., ge=0, description="Advancing stocks")
    declines: int = Field(..., ge=0, description="Declining stocks")
    unchanged: int = Field(..., ge=0, description="Unchanged stocks")
    new_highs: int = Field(..., ge=0, description="New highs")
    new_lows: int = Field(..., ge=0, description="New lows")
    
    # Sector Performance
    sector_performance: Dict[str, Decimal] = Field(default_factory=dict, description="Sector performance")
    
    # Market Indicators
    vix: Decimal = Field(..., ge=0, description="Volatility index")
    put_call_ratio: Optional[Decimal] = Field(None, ge=0, description="Put/Call ratio")
    
    # Institutional Activity
    fii_activity: Optional[Dict[str, Decimal]] = Field(None, description="FII activity")
    dii_activity: Optional[Dict[str, Decimal]] = Field(None, description="DII activity")
    
    # Economic Indicators
    usd_inr: Optional[Decimal] = Field(None, gt=0, description="USD/INR rate")
    crude_oil: Optional[Decimal] = Field(None, gt=0, description="Crude oil price")
    gold: Optional[Decimal] = Field(None, gt=0, description="Gold price")
    
    # Data Sources
    data_sources: Dict[str, DataSource] = Field(default_factory=dict, description="Data sources used")


class ConsolidatedPortfolioMetrics(BaseModel):
    """Portfolio/Watchlist metrics with validation."""
    
    total_value: Decimal = Field(..., ge=0, description="Total portfolio value")
    total_change: Decimal = Field(..., description="Total change")
    total_change_percent: Decimal = Field(..., description="Total percentage change")
    invested_value: Decimal = Field(..., ge=0, description="Total invested value")
    current_value: Decimal = Field(..., ge=0, description="Current market value")
    unrealized_pnl: Decimal = Field(..., description="Unrealized P&L")
    realized_pnl: Decimal = Field(default=Decimal('0'), description="Realized P&L")
    
    # Risk Metrics
    portfolio_beta: Optional[Decimal] = Field(None, description="Portfolio beta")
    sharpe_ratio: Optional[Decimal] = Field(None, description="Sharpe ratio")
    max_drawdown: Optional[Decimal] = Field(None, le=0, description="Maximum drawdown")
    
    @validator('total_value')
    def validate_total_value(cls, v, values):
        """Validate total value equals current value."""
        if 'current_value' in values and abs(v - values['current_value']) > Decimal('0.01'):
            raise ValueError('Total value should equal current value')
        return v


class ConsolidatedPortfolio(BaseModel):
    """Portfolio/Watchlist response with validation."""
    
    name: str = Field(..., min_length=1, description="Portfolio name")
    symbols: List[str] = Field(..., min_items=1, description="Stock symbols")
    holdings: Dict[str, ConsolidatedStockData] = Field(..., description="Stock holdings")
    metrics: ConsolidatedPortfolioMetrics = Field(..., description="Portfolio metrics")
    last_updated: datetime = Field(..., description="Last update timestamp")
    
    @validator('holdings')
    def validate_holdings(cls, v, values):
        """Validate holdings match symbols."""
        if 'symbols' in values:
            missing_symbols = set(values['symbols']) - set(v.keys())
            if missing_symbols:
                raise ValueError(f'Missing holdings for symbols: {missing_symbols}')
        return v


# Request/Response Models

class ConsolidatedMarketDataRequest(BaseModel):
    """Universal market data request with validation."""
    
    symbols: List[str] = Field(..., min_items=1, max_items=100, description="Stock symbols")
    scope: DataScope = Field(default=DataScope.STANDARD, description="Data richness level")
    historical_days: Optional[int] = Field(None, ge=1, le=365, description="Historical data days")
    timeframe: TimeFrame = Field(default=TimeFrame.DAILY, description="Historical timeframe")
    include_context: bool = Field(default=False, description="Include market context")
    
    @validator('symbols')
    def validate_symbols(cls, v):
        """Validate and clean symbols."""
        cleaned = [s.strip().upper() for s in v if s.strip()]
        if not cleaned:
            raise ValueError('At least one valid symbol is required')
        return cleaned


class ConsolidatedMarketDataResponse(BaseModel):
    """Universal market data response with validation."""
    
    request_id: str = Field(..., description="Request identifier")
    timestamp: datetime = Field(..., description="Response timestamp")
    scope: DataScope = Field(..., description="Data scope used")
    
    # Stock Data
    stocks: Dict[str, ConsolidatedStockData] = Field(default_factory=dict, description="Stock data")
    
    # Historical Data (optional)
    historical: Optional[Dict[str, ConsolidatedHistoricalData]] = Field(None, description="Historical data")
    
    # Market Context (optional)
    market_context: Optional[ConsolidatedMarketContext] = Field(None, description="Market context")
    
    # Request Summary
    total_symbols: int = Field(..., ge=0, description="Total symbols requested")
    successful_symbols: int = Field(..., ge=0, description="Successfully retrieved symbols")
    failed_symbols: List[str] = Field(default_factory=list, description="Failed symbols")
    
    # Performance Metrics
    response_time_ms: Optional[int] = Field(None, ge=0, description="Response time in milliseconds")
    data_sources_used: List[DataSource] = Field(default_factory=list, description="Data sources used")
    
    @validator('successful_symbols')
    def validate_success_count(cls, v, values):
        """Validate success count matches actual stocks."""
        if 'stocks' in values and len(values['stocks']) != v:
            raise ValueError('Successful symbols count does not match actual stocks')
        return v


class ConsolidatedPortfolioRequest(BaseModel):
    """Portfolio request with validation."""
    
    name: str = Field(default="My Portfolio", min_length=1, description="Portfolio name")
    symbols: List[str] = Field(..., min_items=1, max_items=50, description="Stock symbols")
    quantities: Optional[List[Decimal]] = Field(None, description="Stock quantities")
    avg_prices: Optional[List[Decimal]] = Field(None, description="Average purchase prices")
    scope: DataScope = Field(default=DataScope.STANDARD, description="Data richness level")
    
    @validator('quantities')
    def validate_quantities(cls, v, values):
        """Validate quantities match symbols."""
        if v is not None and 'symbols' in values:
            if len(v) != len(values['symbols']):
                raise ValueError('Quantities must match symbols count')
            if any(q <= 0 for q in v):
                raise ValueError('All quantities must be positive')
        return v
    
    @validator('avg_prices')
    def validate_avg_prices(cls, v, values):
        """Validate average prices match symbols."""
        if v is not None and 'symbols' in values:
            if len(v) != len(values['symbols']):
                raise ValueError('Average prices must match symbols count')
            if any(p <= 0 for p in v):
                raise ValueError('All average prices must be positive')
        return v


# Error Models

class ConsolidatedErrorResponse(BaseModel):
    """Standardized error response."""
    
    error_code: str = Field(..., description="Error code")
    error_message: str = Field(..., description="Human-readable error message")
    error_type: str = Field(..., description="Error type")
    timestamp: datetime = Field(..., description="Error timestamp")
    request_id: Optional[str] = Field(None, description="Request identifier")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# Health Check Models

class ServiceHealthResponse(BaseModel):
    """Service health check response."""
    
    service_name: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(..., description="Health check timestamp")
    environment: str = Field(..., description="Environment")
    
    # Service-specific health
    market_data_status: str = Field(..., description="Market data service status")
    database_status: str = Field(..., description="Database status")
    external_apis_status: Dict[str, str] = Field(default_factory=dict, description="External API status")
    
    # Performance metrics
    uptime_seconds: int = Field(..., ge=0, description="Service uptime in seconds")
    memory_usage_mb: Optional[int] = Field(None, ge=0, description="Memory usage in MB")
    cpu_usage_percent: Optional[Decimal] = Field(None, ge=0, le=100, description="CPU usage percentage")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }
