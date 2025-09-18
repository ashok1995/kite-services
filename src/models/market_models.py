"""
Market Data Models
==================

Pydantic models for market data structures used throughout the Kite Services.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
from pydantic import BaseModel, Field


class MarketStatus(str, Enum):
    """Market status enumeration."""
    OPEN = "open"
    CLOSED = "closed"
    PRE_MARKET = "pre_market"
    POST_MARKET = "post_market"
    UNKNOWN = "unknown"


class TechnicalIndicators(BaseModel):
    """Technical indicators for a symbol."""
    symbol: str
    timestamp: datetime
    rsi: float = Field(default=50.0, description="RSI (14 period)")
    sma_20: float = Field(default=0.0, description="Simple Moving Average (20 period)")
    ema_12: float = Field(default=0.0, description="Exponential Moving Average (12 period)")
    ema_26: float = Field(default=0.0, description="Exponential Moving Average (26 period)")
    macd: float = Field(default=0.0, description="MACD")
    macd_signal: float = Field(default=0.0, description="MACD Signal Line")
    bollinger_upper: float = Field(default=0.0, description="Bollinger Band Upper")
    bollinger_middle: float = Field(default=0.0, description="Bollinger Band Middle")
    bollinger_lower: float = Field(default=0.0, description="Bollinger Band Lower")
    volume_sma: float = Field(default=0.0, description="Volume SMA (20 period)")
    atr: float = Field(default=0.0, description="Average True Range (14 period)")
    
    @classmethod
    def default(cls) -> 'TechnicalIndicators':
        """Create default technical indicators."""
        return cls(
            symbol="",
            timestamp=datetime.now(),
            rsi=50.0,
            sma_20=0.0,
            ema_12=0.0,
            ema_26=0.0,
            macd=0.0,
            macd_signal=0.0,
            bollinger_upper=0.0,
            bollinger_middle=0.0,
            bollinger_lower=0.0,
            volume_sma=0.0,
            atr=0.0
        )


class InstrumentData(BaseModel):
    """Real-time instrument data."""
    symbol: str
    timestamp: datetime
    last_price: float
    change: float
    change_percent: float
    volume: int
    ohlc: Dict[str, float] = Field(default_factory=dict)
    bid_ask: Dict[str, float] = Field(default_factory=dict)
    technical_indicators: Optional[TechnicalIndicators] = None
    fundamentals: Dict[str, Any] = Field(default_factory=dict)
    news_sentiment: Dict[str, Any] = Field(default_factory=dict)


class MarketSentiment(BaseModel):
    """Market sentiment analysis."""
    timestamp: datetime
    overall_sentiment: str = Field(description="BULLISH, BEARISH, NEUTRAL, etc.")
    sentiment_score: float = Field(description="Sentiment score (-1 to 1)")
    vix_level: float = Field(description="Volatility index level")
    fear_greed_index: int = Field(description="Fear & Greed index (0-100)")
    sector_sentiments: Dict[str, str] = Field(default_factory=dict)


class MarketIndex(BaseModel):
    """Market index data."""
    symbol: str
    name: str
    last_price: float
    change: float
    change_percent: float
    timestamp: datetime


class MarketContext(BaseModel):
    """Comprehensive market context."""
    timestamp: datetime
    market_status: MarketStatus
    instruments: Dict[str, InstrumentData] = Field(default_factory=dict)
    sentiment: Optional[MarketSentiment] = None
    indices: List[MarketIndex] = Field(default_factory=list)
    volatility_index: float = Field(default=20.0)
    sector_performance: Dict[str, float] = Field(default_factory=dict)


class SymbolSearchResult(BaseModel):
    """Symbol search result."""
    symbol: str
    name: str
    exchange: str
    instrument_type: str = "EQ"


class HistoricalCandle(BaseModel):
    """Historical price candle."""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int


class QuoteData(BaseModel):
    """Real-time quote data."""
    symbol: str
    instrument_token: int
    timestamp: datetime
    last_price: float
    last_quantity: int
    average_price: float
    volume: int
    buy_quantity: int
    sell_quantity: int
    ohlc: Dict[str, float]
    change: float
    change_percent: float
    last_trade_time: Optional[datetime] = None


class MarketDepth(BaseModel):
    """Market depth (order book) data."""
    symbol: str
    timestamp: datetime
    buy_orders: List[Dict[str, Any]] = Field(default_factory=list)
    sell_orders: List[Dict[str, Any]] = Field(default_factory=list)
    total_buy_quantity: int = 0
    total_sell_quantity: int = 0


# Request/Response models for API

class SymbolSearchRequest(BaseModel):
    """Symbol search request."""
    query: str = Field(min_length=2, max_length=50)
    exchange: str = Field(default="NSE")
    limit: int = Field(default=10, le=50)


class SymbolSearchResponse(BaseModel):
    """Symbol search response."""
    results: List[SymbolSearchResult]
    total_count: int
    query: str


class MarketContextRequest(BaseModel):
    """Market context request."""
    symbols: Optional[List[str]] = None
    include_sentiment: bool = True
    include_indices: bool = True
    include_sectors: bool = True


class MarketContextResponse(BaseModel):
    """Market context response."""
    context: MarketContext
    request_id: Optional[str] = None


class HistoricalDataRequest(BaseModel):
    """Historical data request."""
    symbol: str
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    interval: str = Field(default="day")  # minute, day, week, month
    continuous: bool = Field(default=True)


class HistoricalDataResponse(BaseModel):
    """Historical data response."""
    symbol: str
    interval: str
    data: List[HistoricalCandle]
    total_candles: int


class QuoteRequest(BaseModel):
    """Quote request."""
    symbols: List[str] = Field(min_items=1, max_items=100)


class QuoteResponse(BaseModel):
    """Quote response."""
    quotes: Dict[str, QuoteData]
    timestamp: datetime


class WebSocketMessage(BaseModel):
    """WebSocket message structure."""
    type: str  # tick, quote, order_update, etc.
    data: Dict[str, Any]
    timestamp: datetime


class HealthCheckResponse(BaseModel):
    """Health check response."""
    status: str
    service: str
    version: str
    environment: str
    timestamp: datetime
    services: Dict[str, Any] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    """Error response."""
    error: str
    message: str
    type: str
    timestamp: datetime
    request_id: Optional[str] = None


class StockPrice(BaseModel):
    """Current stock price data."""
    symbol: str
    name: Optional[str] = None
    last_price: float
    change: float
    change_percent: float
    volume: int
    high: float
    low: float
    open: float
    previous_close: float
    timestamp: datetime
    market_status: MarketStatus


class MultiStockPricesRequest(BaseModel):
    """Request for multiple stock prices."""
    symbols: List[str] = Field(min_items=1, max_items=100)
    include_fundamentals: bool = Field(default=False)
    include_technical_indicators: bool = Field(default=False)


class MultiStockPricesResponse(BaseModel):
    """Response for multiple stock prices."""
    prices: Dict[str, StockPrice]
    market_status: MarketStatus
    timestamp: datetime
    request_id: Optional[str] = None


class HistoricalPriceData(BaseModel):
    """Enhanced historical price data with additional metrics."""
    symbol: str
    interval: str
    from_date: datetime
    to_date: datetime
    data: List[HistoricalCandle]
    total_candles: int
    price_change: float
    price_change_percent: float
    volume_average: float
    high_52_week: float
    low_52_week: float
    timestamp: datetime


class MarketOverview(BaseModel):
    """Market overview with key metrics."""
    timestamp: datetime
    market_status: MarketStatus
    major_indices: List[MarketIndex]
    top_gainers: List[StockPrice]
    top_losers: List[StockPrice]
    most_active: List[StockPrice]
    sector_performance: Dict[str, float]
    market_breadth: Dict[str, int]  # advances, declines, unchanged
    volatility_index: float


class WatchlistRequest(BaseModel):
    """Watchlist request."""
    name: str
    symbols: List[str] = Field(min_items=1, max_items=50)
    
    
class WatchlistResponse(BaseModel):
    """Watchlist response with current prices."""
    name: str
    symbols: List[str]
    prices: Dict[str, StockPrice]
    total_value: float
    total_change: float
    total_change_percent: float
    timestamp: datetime
