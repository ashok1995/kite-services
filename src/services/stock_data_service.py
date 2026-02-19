"""
Stock Data Service - Pure Data Provision
=========================================

Clean service that provides real-time and historical stock data.
No analysis, no intelligence - just rich market data from Kite Connect.

Following workspace rules:
- Stateless service design
- Dependency injection
- Comprehensive logging to files
- No hardcoded values
"""

import logging
import time
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional

from common.time_utils import now_ist_naive
from core.kite_client import KiteClient
from core.logging_config import get_logger
from models.data_models import (
    Candle,
    Exchange,
    HistoricalRequest,
    HistoricalResponse,
    HistoricalStockData,
    Interval,
    RealTimeRequest,
    RealTimeResponse,
    RealTimeStockData,
)


class StockDataService:
    """
    Pure stock data service - no analysis, just data provision.

    Provides:
    - Real-time stock prices, volume, and order book data
    - Historical candlestick data with multiple intervals
    - Rich market data from Kite Connect
    - Clean, structured responses
    """

    def __init__(self, kite_client: KiteClient, logger: Optional[logging.Logger] = None):
        """
        Initialize stock data service.

        Args:
            kite_client: Kite Connect client for market data
            logger: Optional logger instance
        """
        self.kite_client = kite_client
        self.logger = logger or get_logger(__name__)

        # Interval mapping for Kite Connect
        self.interval_mapping = {
            Interval.MINUTE: "minute",
            Interval.MINUTE_3: "3minute",
            Interval.MINUTE_5: "5minute",
            Interval.MINUTE_10: "10minute",
            Interval.MINUTE_15: "15minute",
            Interval.MINUTE_30: "30minute",
            Interval.HOUR: "60minute",
            Interval.DAY: "day",
        }

        self.logger.info(
            "StockDataService initialized",
            extra={
                "service": "stock_data_service",
                "capabilities": ["real_time_data", "historical_data", "market_depth"],
                "data_source": "kite_connect",
            },
        )

    async def get_real_time_data(
        self, request: RealTimeRequest, request_id: str
    ) -> RealTimeResponse:
        """
        Get real-time stock data for multiple symbols.

        Args:
            request: Real-time data request
            request_id: Request identifier

        Returns:
            RealTimeResponse: Real-time stock data
        """
        start_time = time.time()

        self.logger.info(
            "Real-time data request",
            extra={
                "request_id": request_id,
                "symbols_count": len(request.symbols),
                "exchange": request.exchange.value,
                "include_depth": request.include_depth,
                "service": "stock_data_service",
            },
        )

        stocks_data = []
        failed_symbols = []

        try:
            # Get instrument tokens for symbols
            instruments = await self._get_instrument_tokens(request.symbols, request.exchange)

            # Get quotes for all symbols
            quotes_data = await self._fetch_quotes(instruments, request_id)

            # Process each symbol
            for symbol in request.symbols:
                try:
                    instrument_token = instruments.get(symbol)
                    if not instrument_token:
                        failed_symbols.append(symbol)
                        continue

                    quote = quotes_data.get(str(instrument_token))
                    if not quote:
                        failed_symbols.append(symbol)
                        continue

                    # Build real-time stock data
                    stock_data = self._build_real_time_stock_data(
                        symbol, quote, request.exchange, instrument_token, request.include_depth
                    )

                    stocks_data.append(stock_data)

                except Exception as e:
                    self.logger.warning(
                        "Failed to process symbol",
                        extra={"symbol": symbol, "error": str(e), "request_id": request_id},
                    )
                    failed_symbols.append(symbol)

            processing_time = int((time.time() - start_time) * 1000)

            response = RealTimeResponse(
                timestamp=now_ist_naive(),
                request_id=request_id,
                stocks=stocks_data,
                total_symbols=len(request.symbols),
                successful_symbols=len(stocks_data),
                failed_symbols=failed_symbols,
                processing_time_ms=processing_time,
                data_source="kite_connect",
            )

            self.logger.info(
                "Real-time data response",
                extra={
                    "request_id": request_id,
                    "successful_symbols": len(stocks_data),
                    "failed_symbols": len(failed_symbols),
                    "processing_time_ms": processing_time,
                    "service": "stock_data_service",
                },
            )

            return response

        except Exception as e:
            processing_time = int((time.time() - start_time) * 1000)
            self.logger.error(
                "Real-time data request failed",
                extra={
                    "request_id": request_id,
                    "error": str(e),
                    "processing_time_ms": processing_time,
                    "service": "stock_data_service",
                },
                exc_info=True,
            )
            raise

    async def get_historical_data(
        self, request: HistoricalRequest, request_id: str
    ) -> HistoricalResponse:
        """
        Get historical candlestick data for multiple symbols.

        Args:
            request: Historical data request
            request_id: Request identifier

        Returns:
            HistoricalResponse: Historical candlestick data
        """
        start_time = time.time()

        # Calculate date range
        to_date = request.to_date or datetime.now().date()
        if request.from_date:
            from_date = request.from_date.date()
        elif request.days:
            from_date = (datetime.now() - timedelta(days=request.days)).date()
        else:
            from_date = (datetime.now() - timedelta(days=30)).date()

        self.logger.info(
            "Historical data request",
            extra={
                "request_id": request_id,
                "symbols_count": len(request.symbols),
                "exchange": request.exchange.value,
                "interval": request.interval.value,
                "from_date": str(from_date),
                "to_date": str(to_date),
                "service": "stock_data_service",
            },
        )

        stocks_data = []
        failed_symbols = []

        try:
            # Get instrument tokens for symbols
            instruments = await self._get_instrument_tokens(request.symbols, request.exchange)

            # Get historical data for each symbol
            for symbol in request.symbols:
                try:
                    instrument_token = instruments.get(symbol)
                    if not instrument_token:
                        failed_symbols.append(symbol)
                        continue

                    # Fetch historical data
                    historical_data = await self._fetch_historical_data(
                        instrument_token, from_date, to_date, request.interval, request_id
                    )

                    if not historical_data:
                        failed_symbols.append(symbol)
                        continue

                    # Build historical stock data
                    stock_data = self._build_historical_stock_data(
                        symbol,
                        request.exchange,
                        instrument_token,
                        request.interval,
                        from_date,
                        to_date,
                        historical_data,
                    )

                    stocks_data.append(stock_data)

                except Exception as e:
                    self.logger.warning(
                        "Failed to process historical data for symbol",
                        extra={"symbol": symbol, "error": str(e), "request_id": request_id},
                    )
                    failed_symbols.append(symbol)

            processing_time = int((time.time() - start_time) * 1000)

            response = HistoricalResponse(
                timestamp=now_ist_naive(),
                request_id=request_id,
                stocks=stocks_data,
                total_symbols=len(request.symbols),
                successful_symbols=len(stocks_data),
                failed_symbols=failed_symbols,
                processing_time_ms=processing_time,
                data_source="kite_connect",
            )

            self.logger.info(
                "Historical data response",
                extra={
                    "request_id": request_id,
                    "successful_symbols": len(stocks_data),
                    "failed_symbols": len(failed_symbols),
                    "total_candles": sum(len(stock.candles) for stock in stocks_data),
                    "processing_time_ms": processing_time,
                    "service": "stock_data_service",
                },
            )

            return response

        except Exception as e:
            processing_time = int((time.time() - start_time) * 1000)
            self.logger.error(
                "Historical data request failed",
                extra={
                    "request_id": request_id,
                    "error": str(e),
                    "processing_time_ms": processing_time,
                    "service": "stock_data_service",
                },
                exc_info=True,
            )
            raise

    # Private helper methods

    async def _get_instrument_tokens(
        self, symbols: List[str], exchange: Exchange
    ) -> Dict[str, int]:
        """Get instrument tokens for symbols."""
        try:
            instruments = self.kite_client.kite.instruments(exchange.value)

            token_map = {}
            for instrument in instruments:
                if instrument["tradingsymbol"] in symbols:
                    token_map[instrument["tradingsymbol"]] = instrument["instrument_token"]

            return token_map

        except Exception as e:
            self.logger.error(
                "Failed to get instrument tokens",
                extra={"error": str(e), "exchange": exchange.value},
                exc_info=True,
            )
            return {}

    async def _fetch_quotes(self, instruments: Dict[str, int], request_id: str) -> Dict[str, Dict]:
        """Fetch quotes for instruments."""
        try:
            if not instruments:
                return {}

            # Get quotes for all instrument tokens
            instrument_tokens = list(instruments.values())
            quotes = self.kite_client.kite.quote(instrument_tokens)

            return quotes

        except Exception as e:
            self.logger.error(
                "Failed to fetch quotes",
                extra={"error": str(e), "request_id": request_id},
                exc_info=True,
            )
            return {}

    def _build_real_time_stock_data(
        self,
        symbol: str,
        quote: Dict,
        exchange: Exchange,
        instrument_token: int,
        include_depth: bool,
    ) -> RealTimeStockData:
        """Build real-time stock data from Kite quote."""

        # Extract basic price data
        ohlc = quote.get("ohlc", {})
        last_price = Decimal(str(quote.get("last_price", 0)))

        # Calculate change
        close_price = Decimal(str(ohlc.get("close", 0))) if ohlc.get("close") else None
        change = Decimal(str(quote.get("net_change", 0)))
        change_percent = (
            Decimal(str(change / close_price * 100))
            if close_price and close_price > 0
            else Decimal("0")
        )

        # Build depth data if requested
        depth_buy = None
        depth_sell = None
        if include_depth and "depth" in quote:
            depth = quote["depth"]
            depth_buy = [
                {"price": Decimal(str(level["price"])), "quantity": level["quantity"]}
                for level in depth.get("buy", [])
            ]
            depth_sell = [
                {"price": Decimal(str(level["price"])), "quantity": level["quantity"]}
                for level in depth.get("sell", [])
            ]

        return RealTimeStockData(
            symbol=symbol,
            exchange=exchange,
            instrument_token=instrument_token,
            last_price=last_price,
            open_price=Decimal(str(ohlc.get("open", 0))),
            high_price=Decimal(str(ohlc.get("high", 0))),
            low_price=Decimal(str(ohlc.get("low", 0))),
            close_price=close_price,
            change=change,
            change_percent=change_percent,
            volume=quote.get("volume", 0),
            average_price=(
                Decimal(str(quote.get("average_price", 0))) if quote.get("average_price") else None
            ),
            turnover=Decimal(str(quote.get("turnover", 0))) if quote.get("turnover") else None,
            bid_price=Decimal(str(quote.get("bid_price", 0))) if quote.get("bid_price") else None,
            ask_price=Decimal(str(quote.get("ask_price", 0))) if quote.get("ask_price") else None,
            bid_quantity=quote.get("bid_quantity"),
            ask_quantity=quote.get("ask_quantity"),
            depth_buy=depth_buy,
            depth_sell=depth_sell,
            upper_circuit=(
                Decimal(str(quote.get("upper_circuit_limit", 0)))
                if quote.get("upper_circuit_limit")
                else None
            ),
            lower_circuit=(
                Decimal(str(quote.get("lower_circuit_limit", 0)))
                if quote.get("lower_circuit_limit")
                else None
            ),
            last_trade_time=quote.get("last_trade_time"),
            timestamp=now_ist_naive(),
        )

    async def _fetch_historical_data(
        self, instrument_token: int, from_date, to_date, interval: Interval, request_id: str
    ) -> List[Dict]:
        """Fetch historical data from Kite Connect."""
        try:
            kite_interval = self.interval_mapping.get(interval, "day")

            historical_data = self.kite_client.kite.historical_data(
                instrument_token=instrument_token,
                from_date=from_date,
                to_date=to_date,
                interval=kite_interval,
                continuous=True,
            )

            return historical_data or []

        except Exception as e:
            self.logger.error(
                "Failed to fetch historical data",
                extra={
                    "instrument_token": instrument_token,
                    "interval": interval.value,
                    "error": str(e),
                    "request_id": request_id,
                },
                exc_info=True,
            )
            return []

    def _build_historical_stock_data(
        self,
        symbol: str,
        exchange: Exchange,
        instrument_token: int,
        interval: Interval,
        from_date,
        to_date,
        historical_data: List[Dict],
    ) -> HistoricalStockData:
        """Build historical stock data from Kite historical data."""

        # Convert to candle objects
        candles = []
        for data_point in historical_data:
            candle = Candle(
                timestamp=data_point["date"],
                open=Decimal(str(data_point["open"])),
                high=Decimal(str(data_point["high"])),
                low=Decimal(str(data_point["low"])),
                close=Decimal(str(data_point["close"])),
                volume=data_point["volume"],
            )
            candles.append(candle)

        return HistoricalStockData(
            symbol=symbol,
            exchange=exchange,
            instrument_token=instrument_token,
            interval=interval,
            from_date=datetime.combine(from_date, datetime.min.time()),
            to_date=datetime.combine(to_date, datetime.min.time()),
            candles=candles,
            total_candles=len(candles),
            timestamp=now_ist_naive(),
        )
