"""
Pure Data Models - No Intelligence/Analysis
===========================================

Simple, clean data models for stock data provision service.
No analysis, no intelligence - just rich market data.
"""

from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum
from pydantic import BaseModel, Field
from decimal import Decimal


# =============================================================================
# ENUMS
# =============================================================================

class Exchange(str, Enum):
    """Stock exchanges."""
    NSE = "NSE"
    BSE = "BSE"


class Interval(str, Enum):
    """Historical data intervals."""
    MINUTE = "minute"
    MINUTE_3 = "3minute"
    MINUTE_5 = "5minute"
    MINUTE_10 = "10minute"
    MINUTE_15 = "15minute"
    MINUTE_30 = "30minute"
    HOUR = "hour"
    DAY = "day"


# =============================================================================
# REAL-TIME DATA MODELS
# =============================================================================

class RealTimeStockData(BaseModel):
    """Real-time stock data - no analysis, just data."""
    
    # Basic identification
    symbol: str = Field(..., description="Stock symbol")
    exchange: Exchange = Field(..., description="Exchange")
    instrument_token: Optional[int] = Field(None, description="Kite instrument token")
    
    # Price data
    last_price: Decimal = Field(..., description="Last traded price")
    open_price: Decimal = Field(..., description="Opening price")
    high_price: Decimal = Field(..., description="Day high")
    low_price: Decimal = Field(..., description="Day low")
    close_price: Optional[Decimal] = Field(None, description="Previous close")
    
    # Change data
    change: Optional[Decimal] = Field(None, description="Absolute change")
    change_percent: Optional[Decimal] = Field(None, description="Percentage change")
    
    # Volume data
    volume: int = Field(..., ge=0, description="Total volume traded")
    average_price: Optional[Decimal] = Field(None, description="Average traded price")
    turnover: Optional[Decimal] = Field(None, description="Total turnover")
    
    # Order book data
    bid_price: Optional[Decimal] = Field(None, description="Best bid price")
    ask_price: Optional[Decimal] = Field(None, description="Best ask price")
    bid_quantity: Optional[int] = Field(None, description="Best bid quantity")
    ask_quantity: Optional[int] = Field(None, description="Best ask quantity")
    
    # Market depth (top 5 levels)
    depth_buy: Optional[List[Dict[str, Decimal]]] = Field(None, description="Buy depth")
    depth_sell: Optional[List[Dict[str, Decimal]]] = Field(None, description="Sell depth")
    
    # Circuit limits
    upper_circuit: Optional[Decimal] = Field(None, description="Upper circuit limit")
    lower_circuit: Optional[Decimal] = Field(None, description="Lower circuit limit")
    
    # Timestamps
    last_trade_time: Optional[datetime] = Field(None, description="Last trade timestamp")
    timestamp: datetime = Field(..., description="Data timestamp")


class RealTimeRequest(BaseModel):
    """Request for real-time stock data."""
    
    symbols: List[str] = Field(..., min_length=1, max_length=50, description="Stock symbols")
    exchange: Exchange = Field(default=Exchange.NSE, description="Exchange")
    include_depth: bool = Field(default=False, description="Include market depth")
    include_circuit_limits: bool = Field(default=True, description="Include circuit limits")


class RealTimeResponse(BaseModel):
    """Response with real-time stock data."""
    
    timestamp: datetime = Field(..., description="Response timestamp")
    request_id: str = Field(..., description="Request identifier")
    
    # Data
    stocks: List[RealTimeStockData] = Field(..., description="Stock data")
    
    # Metadata
    total_symbols: int = Field(..., description="Total symbols requested")
    successful_symbols: int = Field(..., description="Successfully fetched symbols")
    failed_symbols: List[str] = Field(default_factory=list, description="Failed symbols")
    
    # Performance
    processing_time_ms: int = Field(..., description="Processing time in milliseconds")
    data_source: str = Field(default="kite_connect", description="Data source")


# =============================================================================
# HISTORICAL DATA MODELS
# =============================================================================

class Candle(BaseModel):
    """Single candlestick data."""
    
    timestamp: datetime = Field(..., description="Candle timestamp")
    open: Decimal = Field(..., description="Opening price")
    high: Decimal = Field(..., description="High price")
    low: Decimal = Field(..., description="Low price")
    close: Decimal = Field(..., description="Closing price")
    volume: int = Field(..., ge=0, description="Volume")


class HistoricalStockData(BaseModel):
    """Historical stock data - no analysis, just candles."""
    
    # Basic identification
    symbol: str = Field(..., description="Stock symbol")
    exchange: Exchange = Field(..., description="Exchange")
    instrument_token: Optional[int] = Field(None, description="Kite instrument token")
    
    # Request parameters
    interval: Interval = Field(..., description="Data interval")
    from_date: datetime = Field(..., description="Start date")
    to_date: datetime = Field(..., description="End date")
    
    # Candle data
    candles: List[Candle] = Field(..., description="Candlestick data")
    
    # Metadata
    total_candles: int = Field(..., description="Total candles returned")
    
    # Timestamps
    timestamp: datetime = Field(..., description="Data timestamp")


class HistoricalRequest(BaseModel):
    """Request for historical stock data."""
    
    symbols: List[str] = Field(..., min_items=1, max_items=20, description="Stock symbols")
    exchange: Exchange = Field(default=Exchange.NSE, description="Exchange")
    interval: Interval = Field(default=Interval.DAY, description="Data interval")
    
    # Date range
    from_date: Optional[datetime] = Field(None, description="Start date (default: 30 days ago)")
    to_date: Optional[datetime] = Field(None, description="End date (default: today)")
    days: Optional[int] = Field(None, ge=1, le=365, description="Number of days from today")
    
    # Options
    continuous: bool = Field(default=True, description="Continuous data")
    oi: bool = Field(default=False, description="Include Open Interest (for F&O)")


class HistoricalResponse(BaseModel):
    """Response with historical stock data."""
    
    timestamp: datetime = Field(..., description="Response timestamp")
    request_id: str = Field(..., description="Request identifier")
    
    # Data
    stocks: List[HistoricalStockData] = Field(..., description="Historical stock data")
    
    # Metadata
    total_symbols: int = Field(..., description="Total symbols requested")
    successful_symbols: int = Field(..., description="Successfully fetched symbols")
    failed_symbols: List[str] = Field(default_factory=list, description="Failed symbols")
    
    # Performance
    processing_time_ms: int = Field(..., description="Processing time in milliseconds")
    data_source: str = Field(default="kite_connect", description="Data source")


# =============================================================================
# ERROR MODELS
# =============================================================================

class DataError(BaseModel):
    """Data error information."""
    
    symbol: str = Field(..., description="Symbol that failed")
    error_code: str = Field(..., description="Error code")
    error_message: str = Field(..., description="Error message")
    timestamp: datetime = Field(..., description="Error timestamp")


class ErrorResponse(BaseModel):
    """Error response model."""
    
    timestamp: datetime = Field(..., description="Error timestamp")
    request_id: str = Field(..., description="Request identifier")
    error: str = Field(..., description="Error message")
    details: Optional[List[DataError]] = Field(None, description="Detailed errors")


# =============================================================================
# VALIDATION AND EXAMPLES
# =============================================================================

class DataExamples:
    """Example requests and responses."""
    
    @staticmethod
    def real_time_request():
        """Example real-time data request."""
        return RealTimeRequest(
            symbols=["RELIANCE", "TCS", "HDFC"],
            exchange=Exchange.NSE,
            include_depth=True,
            include_circuit_limits=True
        )
    
    @staticmethod
    def historical_request():
        """Example historical data request."""
        return HistoricalRequest(
            symbols=["RELIANCE", "TCS"],
            exchange=Exchange.NSE,
            interval=Interval.MINUTE_15,
            days=7,
            continuous=True
        )


# Export main models
__all__ = [
    "RealTimeRequest",
    "RealTimeResponse", 
    "RealTimeStockData",
    "HistoricalRequest",
    "HistoricalResponse",
    "HistoricalStockData",
    "Candle",
    "Exchange",
    "Interval",
    "DataError",
    "ErrorResponse"
]
