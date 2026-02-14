"""
Market Data API Module

Consolidated market data endpoints for Kite Services.
Provides universal market data access with real-time, historical, and fundamental data.

Endpoints:
- POST /market/data - Universal market data endpoint
- GET /market/status - Market status and health check
- GET /market/instruments - Available instruments and exchanges
"""

import logging
import time
from datetime import datetime
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from core.service_manager import get_service_manager
from models.data_models import RealTimeRequest, RealTimeResponse
from models.unified_api_models import (
    InstrumentInfo,
    InstrumentsResponse,
    MarketDataRequest,
    MarketDataResponse,
    MarketStatus,
    MarketStatusResponse,
    StockData,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/market/data", response_model=MarketDataResponse)
async def get_market_data(request: MarketDataRequest):
    """
    Universal market data endpoint.

    Supports multiple data types:
    - Real-time quotes and OHLC data
    - Historical price data with various intervals
    - Fundamental data and market depth

    Args:
        symbols: List of stock symbols (max 50)
        exchange: Exchange (NSE, BSE, etc.)
        data_type: Type of data (quote, historical, fundamentals)
        from_date/to_date: Date range for historical data
        interval: Time interval for historical data
        include_depth: Include market depth data
        include_circuit_limits: Include circuit limit information
    """
    start_time = time.time()

    try:
        service_manager = await get_service_manager()
        kite_client = service_manager.kite_client
        stock_service = service_manager.stock_data_service

        logger.info(f"Fetching {request.data_type} data for {len(request.symbols)} symbols")

        data = {}
        failed_symbols = []

        # Handle different data types
        if request.data_type == "quote":
            # Real-time quotes — Kite expects EXCHANGE:SYMBOL format
            exchange_prefix = f"{request.exchange.value}:"
            for symbol in request.symbols:
                try:
                    full_symbol = symbol if ":" in symbol else f"{exchange_prefix}{symbol}"
                    quote = await kite_client.quote([full_symbol])
                    if quote and full_symbol in quote:
                        quote_data = quote[full_symbol]
                        data[symbol] = StockData(
                            symbol=symbol,
                            instrument_token=quote_data.get("instrument_token"),
                            last_price=quote_data.get("last_price"),
                            open=quote_data.get("ohlc", {}).get("open"),
                            high=quote_data.get("ohlc", {}).get("high"),
                            low=quote_data.get("ohlc", {}).get("low"),
                            close=quote_data.get("ohlc", {}).get("close"),
                            volume=quote_data.get("volume"),
                            average_price=quote_data.get("average_price"),
                            ohlc=quote_data.get("ohlc"),
                            net_change=quote_data.get("net_change"),
                            net_change_percent=quote_data.get("net_change_percent"),
                            oi=quote_data.get("oi"),
                            oi_day_high=quote_data.get("oi_day_high"),
                            oi_day_low=quote_data.get("oi_day_low"),
                            timestamp=quote_data.get("timestamp"),
                        )
                    else:
                        failed_symbols.append(symbol)
                except Exception as e:
                    logger.warning(f"Failed to get quote for {symbol}: {str(e)}")
                    failed_symbols.append(symbol)

        elif request.data_type == "historical":
            # Historical data
            if not request.from_date or not request.to_date or not request.interval:
                raise HTTPException(
                    status_code=400,
                    detail="from_date, to_date, and interval are required for historical data",
                )

            for symbol in request.symbols:
                try:
                    historical = await stock_service.get_historical_data(
                        symbol=symbol,
                        from_date=request.from_date,
                        to_date=request.to_date,
                        interval=request.interval.value,
                    )
                    if historical:
                        # Use the most recent candle as the current data
                        latest = historical[-1] if historical else None
                        if latest:
                            data[symbol] = StockData(
                                symbol=symbol,
                                last_price=latest.get("close"),
                                open=latest.get("open"),
                                high=latest.get("high"),
                                low=latest.get("low"),
                                close=latest.get("close"),
                                volume=latest.get("volume"),
                                timestamp=latest.get("timestamp"),
                            )
                    else:
                        failed_symbols.append(symbol)
                except Exception as e:
                    logger.warning(f"Failed to get historical data for {symbol}: {str(e)}")
                    failed_symbols.append(symbol)

        elif request.data_type == "fundamentals":
            # Fundamental data (using Yahoo Finance as fallback)
            for symbol in request.symbols:
                try:
                    fundamental = await stock_service.get_fundamental_data(symbol)
                    if fundamental:
                        data[symbol] = StockData(
                            symbol=symbol,
                            last_price=fundamental.get("current_price"),
                            timestamp=fundamental.get("timestamp"),
                        )
                    else:
                        failed_symbols.append(symbol)
                except Exception as e:
                    logger.warning(f"Failed to get fundamental data for {symbol}: {str(e)}")
                    failed_symbols.append(symbol)

        else:
            raise HTTPException(
                status_code=400, detail=f"Unsupported data type: {request.data_type}"
            )

        processing_time = (time.time() - start_time) * 1000

        return MarketDataResponse(
            success=True,
            data=data,
            total_symbols=len(request.symbols),
            successful_symbols=len(data),
            failed_symbols=len(failed_symbols),
            failed_symbols_list=failed_symbols,
            processing_time_ms=round(processing_time, 2),
            message=f"Successfully fetched {request.data_type} data for {len(data)} symbols",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Market data fetch failed: {str(e)}")
        processing_time = (time.time() - start_time) * 1000
        raise HTTPException(status_code=500, detail=f"Market data fetch failed: {str(e)}")


@router.get("/market/status", response_model=MarketStatusResponse)
async def get_market_status():
    """
    Get current market status and health information.

    Returns:
    - Current market status (open, closed, pre_market, post_market)
    - Exchange-specific status
    - Next market open/close times
    """
    try:
        service_manager = await get_service_manager()
        kite_client = service_manager.kite_client

        # Get market hours from Kite
        market_status = await kite_client.get_market_status()

        if market_status:
            # Parse market status
            overall_status = MarketStatus.CLOSED
            if market_status.get("market_open", False):
                overall_status = MarketStatus.OPEN

            exchanges = {}
            for exchange_data in market_status.get("exchanges", []):
                exchange_name = exchange_data.get("exchange", "unknown")
                exchanges[exchange_name] = {
                    "status": exchange_data.get("status", "closed"),
                    "session": exchange_data.get("session", "normal"),
                    "market_open": exchange_data.get("market_open", False),
                }

            return MarketStatusResponse(
                market_status=overall_status,
                market_open=market_status.get("market_open", False),
                exchanges=exchanges,
                message="Market status retrieved successfully",
            )
        else:
            # Fallback response
            return MarketStatusResponse(
                market_status=MarketStatus.CLOSED,
                market_open=False,
                message="Unable to determine market status",
            )

    except Exception as e:
        logger.error(f"Market status check failed: {str(e)}")
        return MarketStatusResponse(
            market_status=MarketStatus.CLOSED,
            market_open=False,
            message=f"Market status check failed: {str(e)}",
        )


@router.get("/market/instruments", response_model=InstrumentsResponse)
async def get_instruments(
    exchange: Optional[str] = Query(None, description="Filter by exchange"),
    instrument_type: Optional[str] = Query(None, description="Filter by instrument type"),
    limit: int = Query(1000, ge=1, le=5000, description="Maximum number of instruments to return"),
):
    """
    Get available instruments and exchanges.

    Args:
        exchange: Filter by specific exchange (NSE, BSE, etc.)
        instrument_type: Filter by instrument type (EQ, CE, PE, etc.)
        limit: Maximum number of instruments to return
    """
    try:
        service_manager = await get_service_manager()
        kite_client = service_manager.kite_client

        logger.info(f"Fetching instruments for exchange={exchange}, type={instrument_type}")

        # Get instruments from Kite
        instruments_data = await kite_client.get_instruments()

        if not instruments_data:
            return InstrumentsResponse(
                success=False,
                instruments=[],
                total_count=0,
                exchanges=[],
                message="Failed to fetch instruments",
            )

        # Filter instruments
        filtered_instruments = []
        exchanges_list = set()

        for tradingsymbol, instrument in instruments_data.items():
            # Apply filters
            if exchange and instrument.get("exchange") != exchange:
                continue
            if instrument_type and instrument.get("instrument_type") != instrument_type:
                continue

            exchanges_list.add(instrument.get("exchange", ""))

            filtered_instruments.append(
                InstrumentInfo(
                    instrument_token=instrument.get("instrument_token"),
                    tradingsymbol=tradingsymbol,  # Use the key as tradingsymbol
                    name=instrument.get("name"),
                    tick_size=Decimal(str(instrument.get("tick_size", 0))),
                    lot_size=instrument.get("lot_size", 1),
                    instrument_type=instrument.get("instrument_type", "EQ"),
                    segment=instrument.get("segment"),
                    exchange=instrument.get("exchange"),
                )
            )

            # Apply limit
            if len(filtered_instruments) >= limit:
                break

        return InstrumentsResponse(
            success=True,
            instruments=filtered_instruments,
            total_count=len(filtered_instruments),
            exchanges=list(exchanges_list),
            message=f"Successfully fetched {len(filtered_instruments)} instruments",
        )

    except Exception as e:
        logger.error(f"Instruments fetch failed: {str(e)}")
        return InstrumentsResponse(
            success=False,
            instruments=[],
            total_count=0,
            exchanges=[],
            message=f"Instruments fetch failed: {str(e)}",
        )


@router.post("/market/quotes", response_model=RealTimeResponse)
async def get_quotes(request: RealTimeRequest):
    """
    Get current market prices for multiple instruments.

    Minimal endpoint for fetching current LTP and basic OHLC for a list of stocks.
    Configurable max symbols limit from settings.

    Args:
        symbols: List of stock symbols (configurable max length)
        exchange: Exchange (default NSE)
        include_depth: Include market depth (optional)
        include_circuit_limits: Include circuit limits (optional)
    """
    from config.settings import get_settings

    start_time = time.time()

    # Enforce configurable max symbols limit
    settings = get_settings()
    max_symbols = settings.service.quotes_max_symbols

    if len(request.symbols) > max_symbols:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum {max_symbols} symbols allowed. Requested: {len(request.symbols)}",
        )

    try:
        service_manager = await get_service_manager()
        kite_client = service_manager.kite_client

        logger.info(f"Fetching quotes for {len(request.symbols)} symbols")

        # Get quotes from Kite - must use EXCHANGE:SYMBOL format
        exchange_prefix = f"{request.exchange.value}:"
        full_symbols = [f"{exchange_prefix}{symbol}" for symbol in request.symbols]
        quotes = await kite_client.quote(full_symbols)
        stocks_data = []
        failed_symbols = []

        for symbol in request.symbols:
            try:
                # Look for quote using full symbol with exchange prefix
                full_symbol = f"{exchange_prefix}{symbol}"
                if full_symbol in quotes and quotes[full_symbol]:
                    quote_data = quotes[full_symbol]

                    # Build stock data with all required fields
                    last_price = Decimal(str(quote_data.get("last_price", 0)))
                    close_price = quote_data.get("ohlc", {}).get("close", 0)

                    # Calculate change_percent from last_price and close (Kite doesn't provide it)
                    change_percent = None
                    if close_price and close_price > 0:
                        change_percent = (
                            (last_price - Decimal(str(close_price))) / Decimal(str(close_price))
                        ) * 100

                    stock_data = {
                        "symbol": symbol,
                        "exchange": (
                            request.exchange.value
                            if hasattr(request.exchange, "value")
                            else str(request.exchange)
                        ),
                        "instrument_token": quote_data.get("instrument_token"),
                        "last_price": last_price,
                        "open_price": Decimal(str(quote_data.get("ohlc", {}).get("open", 0))),
                        "high_price": Decimal(str(quote_data.get("ohlc", {}).get("high", 0))),
                        "low_price": Decimal(str(quote_data.get("ohlc", {}).get("low", 0))),
                        "close_price": Decimal(str(close_price)) if close_price else None,
                        "change": (
                            Decimal(str(quote_data.get("net_change", 0)))
                            if quote_data.get("net_change") is not None
                            else None
                        ),
                        "change_percent": change_percent,
                        "volume": quote_data.get("volume", 0),
                        "average_price": (
                            Decimal(str(quote_data.get("average_price", 0)))
                            if quote_data.get("average_price")
                            else None
                        ),
                        "turnover": None,  # Not available in basic quote
                        "timestamp": quote_data.get("timestamp"),
                    }

                    # Import RealTimeStockData model for proper response
                    from models.data_models import RealTimeStockData

                    stock = RealTimeStockData(**stock_data)
                    stocks_data.append(stock)
                else:
                    failed_symbols.append(symbol)

            except Exception as e:
                logger.warning(f"Failed to process quote for {symbol}: {str(e)}")
                failed_symbols.append(symbol)

        processing_time = (time.time() - start_time) * 1000

        return RealTimeResponse(
            success=True,
            timestamp=datetime.now(),
            request_id=f"quotes_{int(time.time())}",
            stocks=stocks_data,
            total_symbols=len(request.symbols),
            successful_symbols=len(stocks_data),
            failed_symbols=failed_symbols,
            processing_time_ms=int(processing_time),
            data_source="kite_connect",
            message=f"Successfully fetched quotes for {len(stocks_data)} symbols",
        )

    except Exception as e:
        logger.error(f"Quotes fetch failed: {str(e)}")
        processing_time = (time.time() - start_time) * 1000
        raise HTTPException(status_code=500, detail=f"Quotes fetch failed: {str(e)}")


@router.get("/market/historical/{symbol}")
async def get_historical_data(
    symbol: str,
    interval: str = "5minute",
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
):
    """
    Get historical OHLCV candles for a symbol.

    **Purpose:** Fetch historical price data for technical analysis and return calculations.

    **Args:**
    - symbol: Stock symbol (e.g., RELIANCE, TCS)
    - interval: Candle interval (minute, 5minute, 15minute, hour, day)
    - from_date: Start date (YYYY-MM-DD)
    - to_date: End date (YYYY-MM-DD)

    **Returns:**
    - List of OHLCV candles

    **Intervals:**
    - minute - 1 minute candles
    - 5minute - 5 minute candles
    - 15minute - 15 minute candles
    - hour - 1 hour candles
    - day - Daily candles

    **Example:**
    ```
    GET /api/market/historical/RELIANCE?interval=5minute&from_date=2026-02-10&to_date=2026-02-13
    ```
    """
    from datetime import datetime, timedelta

    start_time = time.time()

    try:
        # Default date range (last 7 days)
        if not to_date:
            to_date = datetime.now().strftime("%Y-%m-%d")
        if not from_date:
            from_dt = datetime.now() - timedelta(days=7)
            from_date = from_dt.strftime("%Y-%m-%d")

        service_manager = await get_service_manager()
        kite_client = service_manager.kite_client

        logger.info(f"Fetching historical data for {symbol} ({interval}, {from_date} to {to_date})")

        # Get instrument token first
        instruments = await kite_client.get_instruments()

        # Find instrument token for symbol
        instrument_token = None
        for inst_symbol, inst_data in instruments.items():
            if inst_symbol == symbol or inst_data.get("tradingsymbol") == symbol:
                instrument_token = inst_data.get("instrument_token")
                break

        if not instrument_token:
            raise HTTPException(
                status_code=404, detail=f"Instrument token not found for symbol: {symbol}"
            )

        # Fetch historical data
        candles = await kite_client.historical_data(
            instrument_token=instrument_token,
            from_date=from_date,
            to_date=to_date,
            interval=interval,
        )

        processing_time = (time.time() - start_time) * 1000

        return {
            "symbol": symbol,
            "instrument_token": instrument_token,
            "interval": interval,
            "from_date": from_date,
            "to_date": to_date,
            "candles": candles,
            "total_candles": len(candles),
            "processing_time_ms": int(processing_time),
            "timestamp": datetime.now(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Historical data fetch failed for {symbol}: {str(e)}")
        processing_time = (time.time() - start_time) * 1000
        raise HTTPException(status_code=500, detail=f"Historical data fetch failed: {str(e)}")
