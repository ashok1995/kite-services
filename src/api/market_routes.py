"""
Market Data API Routes
======================

FastAPI routes for market data, quotes, and context information.
"""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query, Request
from fastapi.responses import JSONResponse

from models.market_models import (
    MarketContextRequest, MarketContextResponse,
    SymbolSearchRequest, SymbolSearchResponse,
    HistoricalDataRequest, HistoricalDataResponse,
    QuoteRequest, QuoteResponse,
    HealthCheckResponse, ErrorResponse
)
from services.market_context_service import MarketContextService
from services.yahoo_finance_service import YahooFinanceService
from core.kite_client import KiteClient
from core.logging_config import get_logger

# Initialize router
router = APIRouter()
logger = get_logger(__name__)


# Dependency to get services
async def get_market_context_service(request: Request) -> MarketContextService:
    """Get market context service from app state."""
    service_manager = getattr(request.app.state, 'service_manager', None)
    if not service_manager:
        raise HTTPException(status_code=503, detail="Service manager not available")
    
    market_service = getattr(service_manager, 'market_context_service', None)
    if not market_service:
        raise HTTPException(status_code=503, detail="Market context service not available")
    
    return market_service


async def get_yahoo_service(request: Request) -> YahooFinanceService:
    """Get Yahoo Finance service from app state."""
    service_manager = getattr(request.app.state, 'service_manager', None)
    if not service_manager:
        raise HTTPException(status_code=503, detail="Service manager not available")
    
    yahoo_service = getattr(service_manager, 'yahoo_service', None)
    if not yahoo_service:
        raise HTTPException(status_code=503, detail="Yahoo Finance service not available")
    
    return yahoo_service


async def get_kite_client(request: Request) -> KiteClient:
    """Get Kite client from app state."""
    service_manager = getattr(request.app.state, 'service_manager', None)
    if not service_manager:
        raise HTTPException(status_code=503, detail="Service manager not available")
    
    kite_client = getattr(service_manager, 'kite_client', None)
    if not kite_client:
        raise HTTPException(status_code=503, detail="Kite client not available")
    
    return kite_client


@router.get("/status", response_model=dict)
async def get_market_status():
    """Get current market status."""
    try:
        # Simple market status based on time
        now = datetime.now()
        market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
        market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
        
        if market_open <= now <= market_close and now.weekday() < 5:
            status = "OPEN"
        else:
            status = "CLOSED"
        
        return {
            "status": status,
            "timestamp": now,
            "market_hours": {
                "open": "09:15",
                "close": "15:30",
                "timezone": "IST"
            },
            "is_trading_day": now.weekday() < 5
        }
        
    except Exception as e:
        logger.error(f"Error getting market status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/context", response_model=MarketContextResponse)
async def get_market_context(
    request: MarketContextRequest,
    market_service: MarketContextService = Depends(get_market_context_service)
):
    """Get comprehensive market context."""
    try:
        logger.info(f"Getting market context for symbols: {request.symbols}")
        
        context = await market_service.get_market_context(request.symbols)
        
        return MarketContextResponse(
            context=context,
            request_id=f"mc_{int(datetime.now().timestamp())}"
        )
        
    except Exception as e:
        logger.error(f"Error getting market context: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/context", response_model=MarketContextResponse)
async def get_market_context_get(
    symbols: Optional[str] = Query(None, description="Comma-separated list of symbols"),
    include_sentiment: bool = Query(True, description="Include sentiment analysis"),
    include_indices: bool = Query(True, description="Include market indices"),
    include_sectors: bool = Query(True, description="Include sector performance"),
    market_service: MarketContextService = Depends(get_market_context_service)
):
    """Get market context via GET request."""
    try:
        symbol_list = symbols.split(",") if symbols else None
        
        context = await market_service.get_market_context(symbol_list)
        
        return MarketContextResponse(
            context=context,
            request_id=f"mc_{int(datetime.now().timestamp())}"
        )
        
    except Exception as e:
        logger.error(f"Error getting market context: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search", response_model=SymbolSearchResponse)
async def search_symbols(
    request: SymbolSearchRequest,
    yahoo_service: YahooFinanceService = Depends(get_yahoo_service)
):
    """Search for symbols."""
    try:
        logger.info(f"Searching symbols for query: {request.query}")
        
        results = await yahoo_service.search_symbols(request.query)
        
        return SymbolSearchResponse(
            results=results[:request.limit],
            total_count=len(results),
            query=request.query
        )
        
    except Exception as e:
        logger.error(f"Error searching symbols: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search", response_model=SymbolSearchResponse)
async def search_symbols_get(
    q: str = Query(..., min_length=2, description="Search query"),
    exchange: str = Query("NSE", description="Exchange"),
    limit: int = Query(10, le=50, description="Maximum results"),
    yahoo_service: YahooFinanceService = Depends(get_yahoo_service)
):
    """Search symbols via GET request."""
    try:
        results = await yahoo_service.search_symbols(q)
        
        return SymbolSearchResponse(
            results=results[:limit],
            total_count=len(results),
            query=q
        )
        
    except Exception as e:
        logger.error(f"Error searching symbols: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/quotes", response_model=QuoteResponse)
async def get_quotes(
    request: QuoteRequest,
    kite_client: KiteClient = Depends(get_kite_client)
):
    """Get real-time quotes for symbols."""
    try:
        logger.info(f"Getting quotes for {len(request.symbols)} symbols")
        
        quotes = {}
        for symbol in request.symbols:
            instrument_data = await kite_client.get_instrument_data(symbol)
            if instrument_data:
                quotes[symbol] = instrument_data
        
        return QuoteResponse(
            quotes=quotes,
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Error getting quotes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/quote/{symbol}")
async def get_quote(
    symbol: str,
    kite_client: KiteClient = Depends(get_kite_client)
):
    """Get real-time quote for a single symbol."""
    try:
        logger.info(f"Getting quote for symbol: {symbol}")
        
        quote_data = await kite_client.get_instrument_data(symbol)
        if not quote_data:
            raise HTTPException(status_code=404, detail=f"Symbol {symbol} not found")
        
        return {
            "symbol": symbol,
            "data": quote_data,
            "timestamp": datetime.now()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting quote for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/historical", response_model=HistoricalDataResponse)
async def get_historical_data(
    request: HistoricalDataRequest,
    kite_client: KiteClient = Depends(get_kite_client)
):
    """Get historical data for a symbol."""
    try:
        logger.info(f"Getting historical data for {request.symbol}")
        
        # Calculate days if dates not provided
        days = 30
        if request.from_date and request.to_date:
            days = (request.to_date - request.from_date).days
        
        historical_data = await kite_client.get_historical_data(request.symbol, days)
        
        if not historical_data:
            raise HTTPException(status_code=404, detail=f"No historical data found for {request.symbol}")
        
        return HistoricalDataResponse(
            symbol=request.symbol,
            interval=request.interval,
            data=historical_data,
            total_candles=len(historical_data)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting historical data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/historical/{symbol}")
async def get_historical_data_get(
    symbol: str,
    days: int = Query(30, ge=1, le=365, description="Number of days"),
    interval: str = Query("day", description="Data interval"),
    kite_client: KiteClient = Depends(get_kite_client)
):
    """Get historical data via GET request."""
    try:
        logger.info(f"Getting {days} days of historical data for {symbol}")
        
        historical_data = await kite_client.get_historical_data(symbol, days)
        
        if not historical_data:
            raise HTTPException(status_code=404, detail=f"No historical data found for {symbol}")
        
        return {
            "symbol": symbol,
            "interval": interval,
            "data": historical_data,
            "total_candles": len(historical_data),
            "timestamp": datetime.now()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting historical data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/instruments")
async def get_instruments(
    exchange: str = Query("NSE", description="Exchange"),
    kite_client: KiteClient = Depends(get_kite_client)
):
    """Get list of available instruments."""
    try:
        logger.info(f"Getting instruments for exchange: {exchange}")
        
        instruments = await kite_client.get_instruments(exchange)
        
        return {
            "exchange": exchange,
            "instruments": instruments,
            "count": len(instruments),
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"Error getting instruments: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/instruments/{symbol}")
async def get_instrument_details(
    symbol: str,
    kite_client: KiteClient = Depends(get_kite_client)
):
    """Get details for a specific instrument."""
    try:
        logger.info(f"Getting instrument details for: {symbol}")
        
        instruments = await kite_client.get_instruments()
        
        if symbol not in instruments:
            raise HTTPException(status_code=404, detail=f"Instrument {symbol} not found")
        
        return {
            "symbol": symbol,
            "details": instruments[symbol],
            "timestamp": datetime.now()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting instrument details: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/indices")
async def get_market_indices(
    yahoo_service: YahooFinanceService = Depends(get_yahoo_service)
):
    """Get major market indices."""
    try:
        logger.info("Getting market indices")
        
        indices = await yahoo_service.get_market_indices()
        
        return {
            "indices": [index.dict() for index in indices],
            "count": len(indices),
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"Error getting market indices: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sectors")
async def get_sector_performance(
    yahoo_service: YahooFinanceService = Depends(get_yahoo_service)
):
    """Get sector performance data."""
    try:
        logger.info("Getting sector performance")
        
        sectors = await yahoo_service.get_sector_performance()
        
        return {
            "sectors": sectors,
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"Error getting sector performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/economic-indicators")
async def get_economic_indicators(
    yahoo_service: YahooFinanceService = Depends(get_yahoo_service)
):
    """Get key economic indicators."""
    try:
        logger.info("Getting economic indicators")
        
        indicators = await yahoo_service.get_economic_indicators()
        
        return {
            "indicators": indicators,
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"Error getting economic indicators: {e}")
        raise HTTPException(status_code=500, detail=str(e))
