"""
Market Context Service
=====================

Provides comprehensive market context using Kite Connect and Yahoo Finance APIs.
Combines real-time data with broader market analysis for intelligent trading decisions.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

import yfinance as yf
import pandas as pd
import numpy as np
from kiteconnect import KiteConnect, KiteTicker

from config.settings import get_settings
from core.logging_config import get_logger
from models.market_models import (
    MarketStatus, MarketContext, InstrumentData, 
    TechnicalIndicators, MarketSentiment
)
from core.kite_client import KiteClient
from services.yahoo_finance_service import YahooFinanceService as YahooClient


class MarketContextService:
    """Service for comprehensive market context analysis."""
    
    def __init__(self):
        self.settings = get_settings()
        self.logger = get_logger(__name__)
        
        # Initialize clients
        self.kite_client = KiteClient()
        self.yahoo_client = YahooClient()
        
        # Data storage
        self.market_data: Dict[str, InstrumentData] = {}
        self.technical_indicators: Dict[str, TechnicalIndicators] = {}
        self.market_sentiment: Optional[MarketSentiment] = None
        
        # Configuration
        self.update_interval = 30  # seconds
        self.sentiment_update_interval = 300  # 5 minutes
        
        # Background tasks
        self._market_data_task: Optional[asyncio.Task] = None
        self._sentiment_task: Optional[asyncio.Task] = None
        
    async def initialize(self):
        """Initialize the market context service."""
        self.logger.info("Initializing Market Context Service...")
        
        try:
            # Initialize clients
            await self.kite_client.initialize()
            await self.yahoo_client.initialize()
            
            # Start background tasks
            await self._start_background_tasks()
            
            self.logger.info("✅ Market Context Service initialized successfully")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize Market Context Service: {e}")
            raise
            
    async def cleanup(self):
        """Cleanup the market context service."""
        self.logger.info("Cleaning up Market Context Service...")
        
        # Stop background tasks
        await self._stop_background_tasks()
        
        # Cleanup clients
        await self.kite_client.cleanup()
        await self.yahoo_client.cleanup()
        
        self.logger.info("✅ Market Context Service cleaned up")
        
    async def get_market_context(self, symbols: Optional[List[str]] = None) -> MarketContext:
        """Get comprehensive market context."""
        try:
            # Default symbols if none provided
            if not symbols:
                symbols = ["NIFTY 50", "BANK NIFTY", "RELIANCE", "TCS", "HDFC", "INFY"]
            
            # Get market status
            market_status = await self._get_market_status()
            
            # Get instrument data
            instruments = {}
            for symbol in symbols:
                instrument_data = await self.get_instrument_data(symbol)
                if instrument_data:
                    instruments[symbol] = instrument_data
            
            # Get market sentiment
            sentiment = await self._get_market_sentiment()
            
            # Get broader market context
            market_indices = await self._get_market_indices()
            
            # Create market context
            context = MarketContext(
                timestamp=datetime.now(),
                market_status=market_status,
                instruments=instruments,
                sentiment=sentiment,
                indices=market_indices,
                volatility_index=await self._get_volatility_index(),
                sector_performance=await self._get_sector_performance()
            )
            
            self.logger.info(f"Market context generated for {len(symbols)} symbols")
            return context
            
        except Exception as e:
            self.logger.error(f"Error getting market context: {e}")
            raise
            
    async def get_instrument_data(self, symbol: str) -> Optional[InstrumentData]:
        """Get comprehensive instrument data."""
        try:
            # Get from cache if available
            if symbol in self.market_data:
                cached_data = self.market_data[symbol]
                # Return cached data if recent (within 1 minute)
                if (datetime.now() - cached_data.timestamp).total_seconds() < 60:
                    return cached_data
            
            # Get real-time data from Kite
            kite_data = await self.kite_client.get_instrument_data(symbol)
            
            # Get additional data from Yahoo Finance
            yahoo_data = await self.yahoo_client.get_stock_data(symbol)
            
            # Combine data
            if kite_data:
                instrument_data = InstrumentData(
                    symbol=symbol,
                    timestamp=datetime.now(),
                    last_price=kite_data.get('last_price', 0),
                    change=kite_data.get('change', 0),
                    change_percent=kite_data.get('change_percent', 0),
                    volume=kite_data.get('volume', 0),
                    ohlc=kite_data.get('ohlc', {}),
                    bid_ask=kite_data.get('bid_ask', {}),
                    technical_indicators=await self._calculate_technical_indicators(symbol, kite_data),
                    fundamentals=yahoo_data.get('fundamentals', {}) if yahoo_data else {},
                    news_sentiment=yahoo_data.get('news_sentiment', {}) if yahoo_data else {}
                )
                
                # Cache the data
                self.market_data[symbol] = instrument_data
                return instrument_data
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting instrument data for {symbol}: {e}")
            return None
            
    async def get_technical_indicators(self, symbol: str) -> Optional[TechnicalIndicators]:
        """Get technical indicators for a symbol."""
        try:
            # Check cache first
            if symbol in self.technical_indicators:
                cached_indicators = self.technical_indicators[symbol]
                # Return cached if recent
                if (datetime.now() - cached_indicators.timestamp).total_seconds() < 300:
                    return cached_indicators
            
            # Get historical data
            historical_data = await self.kite_client.get_historical_data(symbol, days=100)
            if not historical_data:
                return None
            
            # Calculate indicators
            indicators = await self._calculate_comprehensive_indicators(symbol, historical_data)
            
            # Cache the indicators
            self.technical_indicators[symbol] = indicators
            return indicators
            
        except Exception as e:
            self.logger.error(f"Error calculating technical indicators for {symbol}: {e}")
            return None
            
    async def subscribe_to_real_time_data(self, symbols: List[str]):
        """Subscribe to real-time data for symbols."""
        try:
            await self.kite_client.subscribe_to_instruments(symbols)
            self.logger.info(f"Subscribed to real-time data for {len(symbols)} symbols")
            
        except Exception as e:
            self.logger.error(f"Error subscribing to real-time data: {e}")
            raise
            
    async def _start_background_tasks(self):
        """Start background tasks for continuous data updates."""
        self._market_data_task = asyncio.create_task(self._market_data_updater())
        self._sentiment_task = asyncio.create_task(self._sentiment_updater())
        
    async def _stop_background_tasks(self):
        """Stop background tasks."""
        if self._market_data_task:
            self._market_data_task.cancel()
            try:
                await self._market_data_task
            except asyncio.CancelledError:
                pass
                
        if self._sentiment_task:
            self._sentiment_task.cancel()
            try:
                await self._sentiment_task
            except asyncio.CancelledError:
                pass
                
    async def _market_data_updater(self):
        """Background task to update market data."""
        while True:
            try:
                # Update market data for subscribed symbols
                for symbol in list(self.market_data.keys()):
                    await self.get_instrument_data(symbol)
                
                await asyncio.sleep(self.update_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in market data updater: {e}")
                await asyncio.sleep(self.update_interval)
                
    async def _sentiment_updater(self):
        """Background task to update market sentiment."""
        while True:
            try:
                self.market_sentiment = await self._calculate_market_sentiment()
                await asyncio.sleep(self.sentiment_update_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in sentiment updater: {e}")
                await asyncio.sleep(self.sentiment_update_interval)
                
    async def _get_market_status(self) -> MarketStatus:
        """Get current market status."""
        try:
            # Check if market is open based on time
            now = datetime.now()
            
            # NSE market hours: 9:15 AM to 3:30 PM
            market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
            market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
            
            if market_open <= now <= market_close:
                # Check if it's a weekday
                if now.weekday() < 5:  # Monday = 0, Friday = 4
                    return MarketStatus.OPEN
            
            return MarketStatus.CLOSED
            
        except Exception as e:
            self.logger.error(f"Error getting market status: {e}")
            return MarketStatus.UNKNOWN
            
    async def _get_market_sentiment(self) -> MarketSentiment:
        """Calculate overall market sentiment."""
        try:
            # Get sentiment from multiple sources
            nifty_sentiment = await self._calculate_index_sentiment("NIFTY 50")
            bank_nifty_sentiment = await self._calculate_index_sentiment("BANK NIFTY")
            
            # Get VIX for fear/greed index
            vix_data = await self.yahoo_client.get_stock_data("^INDIAVIX")
            vix_level = vix_data.get('last_price', 20) if vix_data else 20
            
            # Calculate overall sentiment
            sentiment_score = (nifty_sentiment + bank_nifty_sentiment) / 2
            
            # Adjust based on VIX
            if vix_level > 25:
                sentiment_score -= 0.2  # High volatility reduces sentiment
            elif vix_level < 15:
                sentiment_score += 0.1  # Low volatility improves sentiment
            
            # Determine sentiment level
            if sentiment_score > 0.6:
                sentiment_level = "BULLISH"
            elif sentiment_score > 0.4:
                sentiment_level = "NEUTRAL_POSITIVE"
            elif sentiment_score > -0.4:
                sentiment_level = "NEUTRAL"
            elif sentiment_score > -0.6:
                sentiment_level = "NEUTRAL_NEGATIVE"
            else:
                sentiment_level = "BEARISH"
            
            return MarketSentiment(
                timestamp=datetime.now(),
                overall_sentiment=sentiment_level,
                sentiment_score=sentiment_score,
                vix_level=vix_level,
                fear_greed_index=self._calculate_fear_greed_index(vix_level),
                sector_sentiments=await self._get_sector_sentiments()
            )
            
        except Exception as e:
            self.logger.error(f"Error calculating market sentiment: {e}")
            return MarketSentiment(
                timestamp=datetime.now(),
                overall_sentiment="NEUTRAL",
                sentiment_score=0.0,
                vix_level=20.0,
                fear_greed_index=50,
                sector_sentiments={}
            )
            
    async def _calculate_technical_indicators(self, symbol: str, data: Dict) -> TechnicalIndicators:
        """Calculate technical indicators for a symbol."""
        try:
            # Get historical data for calculations
            historical_data = await self.kite_client.get_historical_data(symbol, days=50)
            if not historical_data:
                return TechnicalIndicators.default()
            
            prices = [float(d['close']) for d in historical_data]
            volumes = [float(d['volume']) for d in historical_data]
            
            # Calculate indicators
            rsi = self._calculate_rsi(prices)
            sma_20 = np.mean(prices[-20:]) if len(prices) >= 20 else prices[-1]
            ema_12 = self._calculate_ema(prices, 12)
            ema_26 = self._calculate_ema(prices, 26)
            
            macd = ema_12 - ema_26
            macd_signal = self._calculate_ema([macd], 9)
            
            # Bollinger Bands
            bb_middle = sma_20
            bb_std = np.std(prices[-20:]) if len(prices) >= 20 else 0
            bb_upper = bb_middle + (2 * bb_std)
            bb_lower = bb_middle - (2 * bb_std)
            
            return TechnicalIndicators(
                symbol=symbol,
                timestamp=datetime.now(),
                rsi=rsi,
                sma_20=sma_20,
                ema_12=ema_12,
                ema_26=ema_26,
                macd=macd,
                macd_signal=macd_signal,
                bollinger_upper=bb_upper,
                bollinger_middle=bb_middle,
                bollinger_lower=bb_lower,
                volume_sma=np.mean(volumes[-20:]) if len(volumes) >= 20 else volumes[-1],
                atr=self._calculate_atr(historical_data)
            )
            
        except Exception as e:
            self.logger.error(f"Error calculating technical indicators: {e}")
            return TechnicalIndicators.default()
            
    def _calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """Calculate RSI indicator."""
        if len(prices) < period + 1:
            return 50.0
        
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))
        
    def _calculate_ema(self, prices: List[float], period: int) -> float:
        """Calculate EMA indicator."""
        if len(prices) < period:
            return prices[-1] if prices else 0
        
        multiplier = 2 / (period + 1)
        ema = prices[0]
        
        for price in prices[1:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
        
        return ema
        
    def _calculate_atr(self, historical_data: List[Dict], period: int = 14) -> float:
        """Calculate Average True Range."""
        if len(historical_data) < period + 1:
            return 0
        
        true_ranges = []
        for i in range(1, len(historical_data)):
            high = float(historical_data[i]['high'])
            low = float(historical_data[i]['low'])
            prev_close = float(historical_data[i-1]['close'])
            
            tr1 = high - low
            tr2 = abs(high - prev_close)
            tr3 = abs(low - prev_close)
            
            true_range = max(tr1, tr2, tr3)
            true_ranges.append(true_range)
        
        return np.mean(true_ranges[-period:]) if true_ranges else 0
        
    def _calculate_fear_greed_index(self, vix_level: float) -> int:
        """Calculate fear/greed index based on VIX."""
        # Invert VIX to create fear/greed index (0-100)
        # VIX 10 = Greed 90, VIX 30 = Fear 10
        if vix_level <= 10:
            return 90
        elif vix_level >= 30:
            return 10
        else:
            return int(90 - ((vix_level - 10) * 4))  # Linear interpolation
            
    # Additional helper methods for market indices, sector performance, etc.
    async def _get_market_indices(self) -> Dict[str, Any]:
        """Get major market indices data."""
        # Implementation for fetching index data
        return {}
        
    async def _get_volatility_index(self) -> float:
        """Get market volatility index."""
        # Implementation for VIX calculation
        return 20.0
        
    async def _get_sector_performance(self) -> Dict[str, float]:
        """Get sector-wise performance."""
        # Implementation for sector analysis
        return {}
        
    async def _calculate_index_sentiment(self, index_name: str) -> float:
        """Calculate sentiment for an index."""
        # Implementation for index sentiment calculation
        return 0.0
        
    async def _get_sector_sentiments(self) -> Dict[str, str]:
        """Get sector-wise sentiments."""
        # Implementation for sector sentiment analysis
        return {}
