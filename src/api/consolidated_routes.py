"""
Consolidated API Routes
======================

Thin FastAPI routes for consolidated market data endpoints.
Following workspace rules:
- Routes are thin (call services only)
- All routes documented
- Proper error handling
- Request/response logging
- Dependency injection
"""

import time
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query, Request
from fastapi.responses import JSONResponse

from models.consolidated_models import (
    ConsolidatedMarketDataRequest, ConsolidatedMarketDataResponse,
    ConsolidatedPortfolioRequest, ConsolidatedPortfolio,
    ConsolidatedMarketContext, ServiceHealthResponse,
    ConsolidatedErrorResponse, DataScope, TimeFrame
)
from services.consolidated_market_service import ConsolidatedMarketService
from services.market_context_service import MarketContextService
from services.yahoo_finance_service import YahooFinanceService
from core.kite_client import KiteClient
from core.logging_config import get_logger
from config.settings import get_settings

# Initialize router
router = APIRouter()
logger = get_logger(__name__)
settings = get_settings()


# Dependency injection functions
async def get_consolidated_service(request: Request) -> ConsolidatedMarketService:
    """Get consolidated market service with dependency injection."""
    service_manager = getattr(request.app.state, 'service_manager', None)
    if not service_manager:
        raise HTTPException(status_code=503, detail="Service manager not available")
    
    # Get individual services
    kite_client = getattr(service_manager, 'kite_client', None)
    yahoo_service = getattr(service_manager, 'yahoo_service', None)
    market_context_service = getattr(service_manager, 'market_context_service', None)
    
    if not all([kite_client, yahoo_service, market_context_service]):
        raise HTTPException(status_code=503, detail="Required services not available")
    
    # Create consolidated service with dependency injection
    return ConsolidatedMarketService(
        kite_client=kite_client,
        yahoo_service=yahoo_service,
        market_context_service=market_context_service,
        logger=logger
    )


def generate_request_id() -> str:
    """Generate unique request ID."""
    return f"req_{int(time.time() * 1000)}"


# Consolidated API Endpoints

@router.get("/data", response_model=ConsolidatedMarketDataResponse)
async def get_consolidated_market_data(
    symbols: str = Query(..., description="Comma-separated symbols (RELIANCE,TCS,HDFC)"),
    scope: DataScope = Query(DataScope.STANDARD, description="Data richness level"),
    historical_days: Optional[int] = Query(None, ge=1, le=365, description="Include historical data (days)"),
    timeframe: TimeFrame = Query(TimeFrame.DAILY, description="Historical timeframe"),
    include_context: bool = Query(False, description="Include market context"),
    service: ConsolidatedMarketService = Depends(get_consolidated_service)
):
    """
    🎯 Universal Market Data Endpoint with REAL DATA
    
    One endpoint for all market data needs! Get stock prices, historical data, 
    and market context using real data from Kite Connect and Yahoo Finance.
    
    **Scope Levels:**
    - basic: Price, change, volume from Kite Connect
    - standard: + OHLC, market status  
    - comprehensive: + fundamentals from Yahoo Finance, technical indicators
    - full: + news sentiment, analyst ratings
    
    **Rate Limit:** 60 requests/minute
    """
    request_id = generate_request_id()
    start_time = time.time()
    
    logger.info(
        "Consolidated market data request",
        extra={
            "endpoint": "/data",
            "symbols": symbols,
            "scope": scope.value,
            "historical_days": historical_days,
            "include_context": include_context,
            "request_id": request_id
        }
    )
    
    try:
        # Parse and validate symbols
        symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
        if not symbol_list:
            raise HTTPException(status_code=400, detail="At least one valid symbol is required")
        
        if len(symbol_list) > 100:
            raise HTTPException(status_code=400, detail="Maximum 100 symbols allowed")
        
        # Get stock data
        stocks = {}
        failed_symbols = []
        
        for symbol in symbol_list:
            try:
                stock_data = await service.get_consolidated_stock_data(symbol, scope, request_id)
                stocks[symbol] = stock_data
            except Exception as e:
                logger.warning(
                    "Failed to get data for symbol",
                    extra={"symbol": symbol, "error": str(e), "request_id": request_id}
                )
                failed_symbols.append(symbol)
        
        # Build response
        response = ConsolidatedMarketDataResponse(
            request_id=request_id,
            timestamp=datetime.now(),
            scope=scope,
            stocks=stocks,
            total_symbols=len(symbol_list),
            successful_symbols=len(stocks),
            failed_symbols=failed_symbols,
            response_time_ms=int((time.time() - start_time) * 1000),
            data_sources_used=[]  # Will be populated by service
        )
        
        # Add historical data if requested
        if historical_days and stocks:
            response.historical = {}
            for symbol in stocks.keys():
                try:
                    historical_data = await service.get_historical_data(
                        symbol, historical_days, timeframe, request_id
                    )
                    response.historical[symbol] = historical_data
                except Exception as e:
                    logger.warning(
                        "Failed to get historical data",
                        extra={"symbol": symbol, "error": str(e), "request_id": request_id}
                    )
        
        # Add market context if requested
        if include_context:
            try:
                market_context = await service.get_market_context(request_id)
                response.market_context = market_context
            except Exception as e:
                logger.warning(
                    "Failed to get market context",
                    extra={"error": str(e), "request_id": request_id}
                )
        
        # Log successful response
        processing_time = (time.time() - start_time) * 1000
        logger.info(
            "Consolidated market data response",
            extra={
                "endpoint": "/data",
                "request_id": request_id,
                "successful_symbols": len(stocks),
                "failed_symbols": len(failed_symbols),
                "processing_time_ms": round(processing_time, 2),
                "response_size_kb": len(str(response)) / 1024
            }
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        processing_time = (time.time() - start_time) * 1000
        logger.error(
            "Consolidated market data error",
            extra={
                "endpoint": "/data",
                "request_id": request_id,
                "error": str(e),
                "processing_time_ms": round(processing_time, 2)
            },
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/portfolio", response_model=ConsolidatedPortfolio)
async def get_consolidated_portfolio(
    name: str = Query("My Portfolio", description="Portfolio name"),
    symbols: str = Query(..., description="Comma-separated symbols"),
    quantities: Optional[str] = Query(None, description="Comma-separated quantities (for P&L calc)"),
    avg_prices: Optional[str] = Query(None, description="Comma-separated average prices"),
    scope: DataScope = Query(DataScope.STANDARD, description="Data richness level"),
    service: ConsolidatedMarketService = Depends(get_consolidated_service)
):
    """
    💼 Portfolio/Watchlist Management with REAL DATA
    
    Get portfolio view with aggregated metrics, P&L, and risk analysis using real market data.
    Works as both watchlist (no quantities) and portfolio (with quantities).
    
    **Rate Limit:** 30 requests/minute
    """
    request_id = generate_request_id()
    start_time = time.time()
    
    logger.info(
        "Portfolio request",
        extra={
            "endpoint": "/portfolio",
            "name": name,
            "symbols": symbols,
            "has_quantities": bool(quantities),
            "has_avg_prices": bool(avg_prices),
            "request_id": request_id
        }
    )
    
    try:
        # Parse and validate input
        symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
        if not symbol_list:
            raise HTTPException(status_code=400, detail="At least one valid symbol is required")
        
        if len(symbol_list) > 50:
            raise HTTPException(status_code=400, detail="Maximum 50 symbols allowed for portfolio")
        
        # Parse quantities and avg prices
        qty_list = None
        avg_price_list = None
        
        if quantities:
            try:
                qty_list = [float(q.strip()) for q in quantities.split(",")]
                if len(qty_list) != len(symbol_list):
                    raise HTTPException(status_code=400, detail="Quantities must match symbols count")
                if any(q <= 0 for q in qty_list):
                    raise HTTPException(status_code=400, detail="All quantities must be positive")
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid quantities format")
        
        if avg_prices:
            try:
                avg_price_list = [float(p.strip()) for p in avg_prices.split(",")]
                if len(avg_price_list) != len(symbol_list):
                    raise HTTPException(status_code=400, detail="Average prices must match symbols count")
                if any(p <= 0 for p in avg_price_list):
                    raise HTTPException(status_code=400, detail="All average prices must be positive")
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid average prices format")
        
        # Get stock data for all holdings
        holdings = {}
        for symbol in symbol_list:
            try:
                stock_data = await service.get_consolidated_stock_data(symbol, scope, request_id)
                holdings[symbol] = stock_data
            except Exception as e:
                logger.warning(
                    "Failed to get stock data for portfolio",
                    extra={"symbol": symbol, "error": str(e), "request_id": request_id}
                )
                continue
        
        # Calculate portfolio metrics
        from decimal import Decimal
        qty_decimal = [Decimal(str(q)) for q in qty_list] if qty_list else None
        avg_price_decimal = [Decimal(str(p)) for p in avg_price_list] if avg_price_list else None
        
        metrics = await service.calculate_portfolio_metrics(
            holdings, qty_decimal, avg_price_decimal, symbol_list, request_id
        )
        
        # Build portfolio response
        portfolio = ConsolidatedPortfolio(
            name=name,
            symbols=symbol_list,
            holdings=holdings,
            metrics=metrics,
            last_updated=datetime.now()
        )
        
        # Log successful response
        processing_time = (time.time() - start_time) * 1000
        logger.info(
            "Portfolio response",
            extra={
                "endpoint": "/portfolio",
                "request_id": request_id,
                "holdings_count": len(holdings),
                "total_value": float(metrics.total_value),
                "total_pnl": float(metrics.total_change),
                "processing_time_ms": round(processing_time, 2)
            }
        )
        
        return portfolio
        
    except HTTPException:
        raise
    except Exception as e:
        processing_time = (time.time() - start_time) * 1000
        logger.error(
            "Portfolio error",
            extra={
                "endpoint": "/portfolio",
                "request_id": request_id,
                "error": str(e),
                "processing_time_ms": round(processing_time, 2)
            },
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/context", response_model=ConsolidatedMarketContext)
async def get_market_context(
    service: ConsolidatedMarketService = Depends(get_consolidated_service)
):
    """
    🌍 Complete Market Context & Overview with REAL DATA
    
    Everything you need to know about the market in one call using real data sources:
    indices, breadth, sectors, volatility, economic indicators.
    
    **Rate Limit:** 20 requests/minute
    """
    request_id = generate_request_id()
    start_time = time.time()
    
    logger.info(
        "Market context request",
        extra={
            "endpoint": "/context",
            "request_id": request_id
        }
    )
    
    try:
        # Get market context from service
        context = await service.get_market_context(request_id)
        
        # Log successful response
        processing_time = (time.time() - start_time) * 1000
        logger.info(
            "Market context response",
            extra={
                "endpoint": "/context",
                "request_id": request_id,
                "indices_count": len(context.indices),
                "sectors_count": len(context.sector_performance),
                "processing_time_ms": round(processing_time, 2)
            }
        )
        
        return context
        
    except Exception as e:
        processing_time = (time.time() - start_time) * 1000
        logger.error(
            "Market context error",
            extra={
                "endpoint": "/context",
                "request_id": request_id,
                "error": str(e),
                "processing_time_ms": round(processing_time, 2)
            },
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/status", response_model=ServiceHealthResponse)
async def get_service_status(request: Request):
    """
    ✅ Service Health Check & Market Status
    
    Lightweight endpoint for service health, market status, and performance metrics.
    
    **Rate Limit:** 120 requests/minute
    """
    request_id = generate_request_id()
    start_time = time.time()
    
    try:
        # Get service manager for health checks
        service_manager = getattr(request.app.state, 'service_manager', None)
        
        # Check service health
        health_status = {}
        if service_manager:
            try:
                health_status = await service_manager.get_health_status()
            except Exception as e:
                logger.warning(f"Failed to get health status: {e}")
        
        # Determine market status
        from models.consolidated_models import MarketStatus
        now = datetime.now()
        market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
        market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
        
        if market_open <= now <= market_close and now.weekday() < 5:
            market_status = "OPEN"
        else:
            market_status = "CLOSED"
        
        # Build health response
        response = ServiceHealthResponse(
            service_name=settings.service.name,
            version=settings.service.version,
            status="healthy",
            timestamp=datetime.now(),
            environment=settings.service.environment,
            market_data_status="available" if service_manager else "limited",
            database_status="not_configured",  # Would check actual DB
            external_apis_status={
                "kite_connect": health_status.get('kite_client', 'unknown'),
                "yahoo_finance": health_status.get('yahoo_service', 'unknown'),
                "market_context": health_status.get('market_context_service', 'unknown')
            },
            uptime_seconds=int(time.time()),  # Simplified - would track actual uptime
            memory_usage_mb=None,  # Would get from system metrics
            cpu_usage_percent=None  # Would get from system metrics
        )
        
        # Log health check
        processing_time = (time.time() - start_time) * 1000
        logger.info(
            "Health check",
            extra={
                "endpoint": "/status",
                "request_id": request_id,
                "status": response.status,
                "market_status": market_status,
                "processing_time_ms": round(processing_time, 2)
            }
        )
        
        return response
        
    except Exception as e:
        processing_time = (time.time() - start_time) * 1000
        logger.error(
            "Health check error",
            extra={
                "endpoint": "/status",
                "request_id": request_id,
                "error": str(e),
                "processing_time_ms": round(processing_time, 2)
            },
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="Health check failed")


# Error handlers
@router.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with proper logging."""
    request_id = getattr(request.state, 'request_id', 'unknown')
    
    logger.warning(
        "HTTP exception",
        extra={
            "request_id": request_id,
            "status_code": exc.status_code,
            "detail": exc.detail,
            "url": str(request.url)
        }
    )
    
    error_response = ConsolidatedErrorResponse(
        error_code=f"HTTP_{exc.status_code}",
        error_message=exc.detail,
        error_type="HTTPException",
        timestamp=datetime.now(),
        request_id=request_id
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.dict()
    )


@router.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions with proper logging."""
    request_id = getattr(request.state, 'request_id', 'unknown')
    
    logger.error(
        "Unhandled exception",
        extra={
            "request_id": request_id,
            "exception": str(exc),
            "exception_type": type(exc).__name__,
            "url": str(request.url)
        },
        exc_info=True
    )
    
    error_response = ConsolidatedErrorResponse(
        error_code="INTERNAL_ERROR",
        error_message="An unexpected error occurred",
        error_type=type(exc).__name__,
        timestamp=datetime.now(),
        request_id=request_id,
        details={"error": str(exc)} if settings.service.debug else None
    )
    
    return JSONResponse(
        status_code=500,
        content=error_response.dict()
    )
