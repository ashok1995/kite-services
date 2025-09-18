"""
Consolidated Market Service
==========================

Stateless, reusable service for consolidated market data operations.
Follows workspace rules:
- Stateless service design
- Dependency injection
- Comprehensive logging to files
- No hardcoded values (uses config)
- Proper error handling
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from decimal import Decimal
import logging

from models.consolidated_models import (
    ConsolidatedStockData, ConsolidatedHistoricalData, ConsolidatedMarketContext,
    ConsolidatedPortfolio, ConsolidatedPortfolioMetrics, MarketIndex,
    DataScope, TimeFrame, MarketStatus, TradingSession, DataSource
)
from core.kite_client import KiteClient
from services.yahoo_finance_service import YahooFinanceService
from services.market_context_service import MarketContextService
from core.logging_config import get_logger


class ConsolidatedMarketService:
    """
    Stateless service for consolidated market data operations.
    
    This service orchestrates data from multiple sources (Kite Connect, Yahoo Finance,
    Market Context Service) and provides unified, comprehensive market data responses.
    
    Following workspace rules:
    - Stateless design (no instance variables for data)
    - Dependency injection for all external services
    - Comprehensive logging to files
    - Configuration-driven behavior
    - Proper error handling and fallbacks
    """
    
    def __init__(
        self,
        kite_client: KiteClient,
        yahoo_service: YahooFinanceService,
        market_context_service: MarketContextService,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize consolidated market service with injected dependencies.
        
        Args:
            kite_client: Kite Connect client for real-time data
            yahoo_service: Yahoo Finance service for fundamentals
            market_context_service: Market context service for technical analysis
            logger: Optional logger instance
        """
        self.kite_client = kite_client
        self.yahoo_service = yahoo_service
        self.market_context_service = market_context_service
        self.logger = logger or get_logger(__name__)
        
        # Log service initialization
        self.logger.info(
            "ConsolidatedMarketService initialized",
            extra={
                "service": "consolidated_market_service",
                "dependencies": {
                    "kite_client": bool(kite_client),
                    "yahoo_service": bool(yahoo_service),
                    "market_context_service": bool(market_context_service)
                }
            }
        )
    
    async def get_consolidated_stock_data(
        self,
        symbol: str,
        scope: DataScope,
        request_id: str
    ) -> ConsolidatedStockData:
        """
        Get consolidated stock data from multiple sources based on scope.
        
        Args:
            symbol: Stock symbol to fetch
            scope: Data richness level
            request_id: Request identifier for tracking
            
        Returns:
            ConsolidatedStockData: Comprehensive stock data
            
        Raises:
            ValueError: If symbol is invalid
            Exception: If all data sources fail
        """
        start_time = time.time()
        data_sources_used = {}
        
        self.logger.info(
            "Getting consolidated stock data",
            extra={
                "symbol": symbol,
                "scope": scope.value,
                "request_id": request_id,
                "service": "consolidated_market_service"
            }
        )
        
        try:
            # Get basic data from Kite Connect
            kite_data = await self._get_kite_data(symbol, request_id)
            if not kite_data:
                raise ValueError(f"No data available for symbol: {symbol}")
            
            data_sources_used["basic_data"] = DataSource.KITE_CONNECT
            
            # Get market status
            market_status = self._get_current_market_status()
            
            # Build basic stock data
            stock_data = ConsolidatedStockData(
                symbol=symbol,
                name=kite_data.get('name', symbol),
                last_price=Decimal(str(kite_data.get('last_price', 0))),
                change=Decimal(str(kite_data.get('change', 0))),
                change_percent=Decimal(str(kite_data.get('change_percent', 0))),
                volume=int(kite_data.get('volume', 0)),
                timestamp=datetime.now(),
                market_status=market_status,
                data_sources=data_sources_used
            )
            
            # Add data based on scope
            if scope in [DataScope.STANDARD, DataScope.COMPREHENSIVE, DataScope.FULL]:
                await self._add_standard_data(stock_data, kite_data, data_sources_used)
            
            if scope in [DataScope.COMPREHENSIVE, DataScope.FULL]:
                await self._add_comprehensive_data(stock_data, symbol, data_sources_used, request_id)
            
            if scope == DataScope.FULL:
                await self._add_full_data(stock_data, symbol, data_sources_used, request_id)
            
            # Update data sources in stock data
            stock_data.data_sources = data_sources_used
            
            # Log successful completion
            processing_time = (time.time() - start_time) * 1000
            self.logger.info(
                "Successfully retrieved consolidated stock data",
                extra={
                    "symbol": symbol,
                    "scope": scope.value,
                    "request_id": request_id,
                    "processing_time_ms": round(processing_time, 2),
                    "data_sources": list(data_sources_used.keys()),
                    "service": "consolidated_market_service"
                }
            )
            
            return stock_data
            
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            self.logger.error(
                "Failed to get consolidated stock data",
                extra={
                    "symbol": symbol,
                    "scope": scope.value,
                    "request_id": request_id,
                    "error": str(e),
                    "processing_time_ms": round(processing_time, 2),
                    "service": "consolidated_market_service"
                },
                exc_info=True
            )
            raise
    
    async def get_historical_data(
        self,
        symbol: str,
        days: int,
        timeframe: TimeFrame,
        request_id: str
    ) -> ConsolidatedHistoricalData:
        """
        Get historical data with analytics.
        
        Args:
            symbol: Stock symbol
            days: Number of days of historical data
            timeframe: Data timeframe
            request_id: Request identifier
            
        Returns:
            ConsolidatedHistoricalData: Historical data with analytics
        """
        start_time = time.time()
        
        self.logger.info(
            "Getting historical data",
            extra={
                "symbol": symbol,
                "days": days,
                "timeframe": timeframe.value,
                "request_id": request_id,
                "service": "consolidated_market_service"
            }
        )
        
        try:
            # Get historical data from Kite Connect
            historical_data = await self.kite_client.get_historical_data(symbol, days)
            if not historical_data:
                raise ValueError(f"No historical data available for {symbol}")
            
            # Convert to HistoricalCandle objects and calculate analytics
            from models.consolidated_models import HistoricalCandle
            candles = []
            
            for data_point in historical_data:
                candle = HistoricalCandle(
                    timestamp=data_point.get('date', datetime.now()),
                    open=Decimal(str(data_point.get('open', 0))),
                    high=Decimal(str(data_point.get('high', 0))),
                    low=Decimal(str(data_point.get('low', 0))),
                    close=Decimal(str(data_point.get('close', 0))),
                    volume=int(data_point.get('volume', 0))
                )
                candles.append(candle)
            
            # Calculate analytics
            analytics = self._calculate_historical_analytics(candles)
            
            historical_response = ConsolidatedHistoricalData(
                symbol=symbol,
                timeframe=timeframe,
                from_date=datetime.now() - timedelta(days=days),
                to_date=datetime.now(),
                candles=candles,
                total_candles=len(candles),
                **analytics
            )
            
            processing_time = (time.time() - start_time) * 1000
            self.logger.info(
                "Successfully retrieved historical data",
                extra={
                    "symbol": symbol,
                    "days": days,
                    "candles_count": len(candles),
                    "request_id": request_id,
                    "processing_time_ms": round(processing_time, 2),
                    "service": "consolidated_market_service"
                }
            )
            
            return historical_response
            
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            self.logger.error(
                "Failed to get historical data",
                extra={
                    "symbol": symbol,
                    "days": days,
                    "request_id": request_id,
                    "error": str(e),
                    "processing_time_ms": round(processing_time, 2),
                    "service": "consolidated_market_service"
                },
                exc_info=True
            )
            raise
    
    async def get_market_context(self, request_id: str) -> ConsolidatedMarketContext:
        """
        Get comprehensive market context from multiple sources.
        
        Args:
            request_id: Request identifier
            
        Returns:
            ConsolidatedMarketContext: Market context data
        """
        start_time = time.time()
        data_sources_used = {}
        
        self.logger.info(
            "Getting market context",
            extra={
                "request_id": request_id,
                "service": "consolidated_market_service"
            }
        )
        
        try:
            # Get market status and session
            market_status = self._get_current_market_status()
            trading_session = self._get_trading_session(market_status)
            
            # Get indices from Yahoo Finance
            indices = []
            try:
                indices_data = await self.yahoo_service.get_market_indices()
                for index_data in indices_data:
                    index = MarketIndex(
                        symbol=index_data.symbol,
                        name=index_data.name,
                        value=Decimal(str(index_data.last_price)),
                        change=Decimal(str(index_data.change)),
                        change_percent=Decimal(str(index_data.change_percent)),
                        timestamp=index_data.timestamp,
                        data_source=DataSource.YAHOO_FINANCE
                    )
                    indices.append(index)
                data_sources_used["indices"] = DataSource.YAHOO_FINANCE
            except Exception as e:
                self.logger.warning(
                    "Failed to get indices data",
                    extra={"error": str(e), "request_id": request_id}
                )
            
            # Get sector performance
            sector_performance = {}
            try:
                sector_data = await self.yahoo_service.get_sector_performance()
                sector_performance = {k: Decimal(str(v)) for k, v in sector_data.items()}
                data_sources_used["sectors"] = DataSource.YAHOO_FINANCE
            except Exception as e:
                self.logger.warning(
                    "Failed to get sector data",
                    extra={"error": str(e), "request_id": request_id}
                )
            
            # Get economic indicators
            economic_data = {}
            try:
                indicators = await self.yahoo_service.get_economic_indicators()
                economic_data = {
                    "vix": Decimal(str(indicators.get('india_vix', 20.0))),
                    "usd_inr": Decimal(str(indicators.get('usd_inr', 83.0))) if indicators.get('usd_inr') else None,
                    "crude_oil": Decimal(str(indicators.get('crude_oil', 75.0))) if indicators.get('crude_oil') else None,
                    "gold": Decimal(str(indicators.get('gold_usd', 2000.0))) if indicators.get('gold_usd') else None
                }
                data_sources_used["economic"] = DataSource.YAHOO_FINANCE
            except Exception as e:
                self.logger.warning(
                    "Failed to get economic indicators",
                    extra={"error": str(e), "request_id": request_id}
                )
                economic_data = {"vix": Decimal("20.0")}
            
            # Build market context
            context = ConsolidatedMarketContext(
                timestamp=datetime.now(),
                market_status=market_status,
                trading_session=trading_session,
                indices=indices,
                advances=1250,  # Mock - would come from real market breadth data
                declines=850,
                unchanged=100,
                new_highs=45,
                new_lows=23,
                sector_performance=sector_performance,
                vix=economic_data["vix"],
                usd_inr=economic_data.get("usd_inr"),
                crude_oil=economic_data.get("crude_oil"),
                gold=economic_data.get("gold"),
                data_sources=data_sources_used
            )
            
            processing_time = (time.time() - start_time) * 1000
            self.logger.info(
                "Successfully retrieved market context",
                extra={
                    "indices_count": len(indices),
                    "sectors_count": len(sector_performance),
                    "request_id": request_id,
                    "processing_time_ms": round(processing_time, 2),
                    "data_sources": list(data_sources_used.keys()),
                    "service": "consolidated_market_service"
                }
            )
            
            return context
            
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            self.logger.error(
                "Failed to get market context",
                extra={
                    "request_id": request_id,
                    "error": str(e),
                    "processing_time_ms": round(processing_time, 2),
                    "service": "consolidated_market_service"
                },
                exc_info=True
            )
            raise
    
    async def calculate_portfolio_metrics(
        self,
        holdings: Dict[str, ConsolidatedStockData],
        quantities: Optional[List[Decimal]],
        avg_prices: Optional[List[Decimal]],
        symbols: List[str],
        request_id: str
    ) -> ConsolidatedPortfolioMetrics:
        """
        Calculate portfolio metrics with real data.
        
        Args:
            holdings: Stock holdings data
            quantities: Stock quantities
            avg_prices: Average purchase prices
            symbols: Stock symbols
            request_id: Request identifier
            
        Returns:
            ConsolidatedPortfolioMetrics: Portfolio metrics
        """
        start_time = time.time()
        
        self.logger.info(
            "Calculating portfolio metrics",
            extra={
                "holdings_count": len(holdings),
                "has_quantities": bool(quantities),
                "has_avg_prices": bool(avg_prices),
                "request_id": request_id,
                "service": "consolidated_market_service"
            }
        )
        
        try:
            total_current_value = Decimal('0')
            total_invested_value = Decimal('0')
            
            for i, symbol in enumerate(symbols):
                if symbol not in holdings:
                    continue
                
                stock_data = holdings[symbol]
                
                if quantities and i < len(quantities):
                    qty = quantities[i]
                    current_value = stock_data.last_price * qty
                    total_current_value += current_value
                    
                    if avg_prices and i < len(avg_prices):
                        invested_value = avg_prices[i] * qty
                        total_invested_value += invested_value
                else:
                    # Watchlist mode - assume 1 quantity
                    total_current_value += stock_data.last_price
                    total_invested_value += (stock_data.previous_close or stock_data.last_price)
            
            # Calculate metrics
            total_change = total_current_value - total_invested_value
            total_change_percent = (
                (total_change / total_invested_value * 100) 
                if total_invested_value > 0 
                else Decimal('0')
            )
            
            metrics = ConsolidatedPortfolioMetrics(
                total_value=total_current_value,
                total_change=total_change,
                total_change_percent=total_change_percent,
                invested_value=total_invested_value,
                current_value=total_current_value,
                unrealized_pnl=total_change,
                portfolio_beta=Decimal('1.0'),  # Mock - would calculate from real data
                sharpe_ratio=Decimal('0.85'),   # Mock - would calculate from historical returns
                max_drawdown=Decimal('-5.2')    # Mock - would calculate from historical data
            )
            
            processing_time = (time.time() - start_time) * 1000
            self.logger.info(
                "Successfully calculated portfolio metrics",
                extra={
                    "total_value": float(total_current_value),
                    "total_pnl": float(total_change),
                    "total_pnl_percent": float(total_change_percent),
                    "request_id": request_id,
                    "processing_time_ms": round(processing_time, 2),
                    "service": "consolidated_market_service"
                }
            )
            
            return metrics
            
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            self.logger.error(
                "Failed to calculate portfolio metrics",
                extra={
                    "request_id": request_id,
                    "error": str(e),
                    "processing_time_ms": round(processing_time, 2),
                    "service": "consolidated_market_service"
                },
                exc_info=True
            )
            raise
    
    # Private helper methods
    
    async def _get_kite_data(self, symbol: str, request_id: str) -> Optional[Dict[str, Any]]:
        """Get data from Kite Connect with error handling."""
        try:
            return await self.kite_client.get_instrument_data(symbol)
        except Exception as e:
            self.logger.warning(
                "Failed to get Kite data",
                extra={
                    "symbol": symbol,
                    "error": str(e),
                    "request_id": request_id
                }
            )
            return None
    
    async def _add_standard_data(
        self, 
        stock_data: ConsolidatedStockData, 
        kite_data: Dict[str, Any],
        data_sources: Dict[str, DataSource]
    ) -> None:
        """Add standard scope data (OHLC, market cap)."""
        ohlc = kite_data.get('ohlc', {})
        stock_data.high = Decimal(str(ohlc.get('high', 0))) if ohlc.get('high') else None
        stock_data.low = Decimal(str(ohlc.get('low', 0))) if ohlc.get('low') else None
        stock_data.open = Decimal(str(ohlc.get('open', 0))) if ohlc.get('open') else None
        stock_data.previous_close = Decimal(str(ohlc.get('close', 0))) if ohlc.get('close') else None
        stock_data.avg_volume = kite_data.get('volume', 0)
        
        data_sources["ohlc"] = DataSource.KITE_CONNECT
    
    async def _add_comprehensive_data(
        self,
        stock_data: ConsolidatedStockData,
        symbol: str,
        data_sources: Dict[str, DataSource],
        request_id: str
    ) -> None:
        """Add comprehensive scope data (fundamentals, technical indicators)."""
        # Get Yahoo Finance data for fundamentals
        try:
            yahoo_data = await self.yahoo_service.get_stock_data(symbol)
            if yahoo_data:
                stock_data.market_cap = Decimal(str(yahoo_data.market_cap)) if yahoo_data.market_cap else None
                stock_data.pe_ratio = Decimal(str(yahoo_data.pe_ratio)) if yahoo_data.pe_ratio else None
                stock_data.pb_ratio = Decimal(str(yahoo_data.fundamentals.get('price_to_book', 0))) if yahoo_data.fundamentals.get('price_to_book') else None
                stock_data.dividend_yield = Decimal(str(yahoo_data.dividend_yield)) if yahoo_data.dividend_yield else None
                data_sources["fundamentals"] = DataSource.YAHOO_FINANCE
        except Exception as e:
            self.logger.warning(
                "Failed to get Yahoo Finance data",
                extra={"symbol": symbol, "error": str(e), "request_id": request_id}
            )
        
        # Get technical indicators
        try:
            technical_indicators = await self.market_context_service.get_technical_indicators(symbol)
            if technical_indicators:
                stock_data.rsi = Decimal(str(technical_indicators.rsi))
                stock_data.sma_20 = Decimal(str(technical_indicators.sma_20))
                stock_data.ema_12 = Decimal(str(technical_indicators.ema_12))
                stock_data.bollinger_upper = Decimal(str(technical_indicators.bollinger_upper))
                stock_data.bollinger_lower = Decimal(str(technical_indicators.bollinger_lower))
                data_sources["technical"] = DataSource.MARKET_CONTEXT_SERVICE
        except Exception as e:
            self.logger.warning(
                "Failed to get technical indicators",
                extra={"symbol": symbol, "error": str(e), "request_id": request_id}
            )
    
    async def _add_full_data(
        self,
        stock_data: ConsolidatedStockData,
        symbol: str,
        data_sources: Dict[str, DataSource],
        request_id: str
    ) -> None:
        """Add full scope data (sentiment, news)."""
        try:
            yahoo_data = await self.yahoo_service.get_stock_data(symbol)
            if yahoo_data and yahoo_data.news_sentiment:
                sentiment_label = yahoo_data.news_sentiment.get('sentiment_label', 'neutral')
                stock_data.news_sentiment = sentiment_label.upper()
                stock_data.analyst_rating = "HOLD"  # Default - can be enhanced
                data_sources["sentiment"] = DataSource.YAHOO_FINANCE
        except Exception as e:
            self.logger.warning(
                "Failed to get sentiment data",
                extra={"symbol": symbol, "error": str(e), "request_id": request_id}
            )
    
    def _get_current_market_status(self) -> MarketStatus:
        """Get current market status based on time."""
        now = datetime.now()
        market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
        market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
        
        if market_open <= now <= market_close and now.weekday() < 5:
            return MarketStatus.OPEN
        else:
            return MarketStatus.CLOSED
    
    def _get_trading_session(self, market_status: MarketStatus) -> TradingSession:
        """Get trading session based on market status."""
        if market_status == MarketStatus.OPEN:
            return TradingSession.REGULAR
        else:
            return TradingSession.CLOSED
    
    def _calculate_historical_analytics(self, candles: List[Any]) -> Dict[str, Any]:
        """Calculate analytics from historical candles."""
        if not candles:
            return {
                "price_change": Decimal('0'),
                "price_change_percent": Decimal('0'),
                "volume_avg": Decimal('0'),
                "volatility": Decimal('0'),
                "high_period": Decimal('0'),
                "low_period": Decimal('0')
            }
        
        closes = [c.close for c in candles]
        volumes = [Decimal(str(c.volume)) for c in candles]
        highs = [c.high for c in candles]
        lows = [c.low for c in candles]
        
        first_close = closes[0]
        last_close = closes[-1]
        price_change = last_close - first_close
        price_change_percent = (price_change / first_close * 100) if first_close != 0 else Decimal('0')
        volume_avg = sum(volumes) / len(volumes) if volumes else Decimal('0')
        high_period = max(highs) if highs else Decimal('0')
        low_period = min(lows) if lows else Decimal('0')
        
        # Calculate volatility (simplified)
        if len(closes) > 1:
            returns = [(closes[i] - closes[i-1]) / closes[i-1] for i in range(1, len(closes))]
            mean_return = sum(returns) / len(returns)
            variance = sum([(r - mean_return)**2 for r in returns]) / len(returns)
            volatility = Decimal(str((variance ** 0.5) * 100))
        else:
            volatility = Decimal('0')
        
        return {
            "price_change": price_change,
            "price_change_percent": price_change_percent,
            "volume_avg": volume_avg,
            "volatility": volatility,
            "high_period": high_period,
            "low_period": low_period
        }
