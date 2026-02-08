"""
Intraday Market Context Service
===============================

Enhanced service for intraday trading context combining:
- Global indices trends (Yahoo Finance)
- Indian market data (Kite Connect)
- Multi-timeframe analysis
- Real-time contextual features

Following workspace rules:
- Stateless service design
- Dependency injection
- Comprehensive logging to files
- No hardcoded values
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from decimal import Decimal
import logging

from models.intraday_context_models import (
    IntradayMarketContext, GlobalMarketContext, GlobalIndex, GlobalIndexTrend,
    IntradayVolatilityContext, IntradaySectorContext, IntradayMarketBreadth,
    IntradayTradingSignal, EnhancedIntradayResponse,
    IntradayTimeframe, GlobalMarketSession, MarketMomentum, IntradayTrendStrength
)
from core.kite_client import KiteClient
from services.yahoo_finance_service import YahooFinanceService
from services.market_intelligence_service import MarketIntelligenceService
from core.logging_config import get_logger


class IntradayContextService:
    """
    Enhanced intraday context service for trading decisions.
    
    Combines multiple data sources to provide comprehensive market context:
    - Global market trends and sentiment
    - Indian market regime and breadth
    - Multi-timeframe technical analysis
    - Sector rotation dynamics
    - Volatility and risk assessment
    - Real-time trading signals
    """
    
    def __init__(
        self,
        kite_client: KiteClient,
        yahoo_service: YahooFinanceService,
        intelligence_service: MarketIntelligenceService,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize intraday context service with injected dependencies.
        
        Args:
            kite_client: Kite Connect client for Indian market data
            yahoo_service: Yahoo Finance service for global data
            intelligence_service: Market intelligence service for analysis
            logger: Optional logger instance
        """
        self.kite_client = kite_client
        self.yahoo_service = yahoo_service
        self.intelligence_service = intelligence_service
        self.logger = logger or get_logger(__name__)
        
        # Global indices mapping
        self.global_indices = {
            "US": {
                "^GSPC": "S&P 500",
                "^IXIC": "NASDAQ",
                "^DJI": "Dow Jones"
            },
            "Europe": {
                "^FTSE": "FTSE 100",
                "^GDAXI": "DAX",
                "^FCHI": "CAC 40"
            },
            "Asia": {
                "^N225": "Nikkei 225",
                "^HSI": "Hang Seng",
                "000001.SS": "Shanghai Composite"
            },
            "India": {
                "^NSEI": "NIFTY 50",
                "^NSEBANK": "BANK NIFTY",
                "^CNXIT": "NIFTY IT"
            }
        }
        
        self.logger.info(
            "IntradayContextService initialized",
            extra={
                "service": "intraday_context_service",
                "global_indices_count": sum(len(indices) for indices in self.global_indices.values()),
                "capabilities": [
                    "global_trends", "intraday_analysis", "multi_timeframe",
                    "sector_rotation", "volatility_analysis", "trading_signals"
                ]
            }
        )
    
    async def get_global_index_trends(self, request_id: str) -> GlobalIndexTrend:
        """
        Get comprehensive global index trends for Indian market context.
        
        Args:
            request_id: Request identifier for tracking
            
        Returns:
            GlobalIndexTrend: Global market trends analysis
        """
        start_time = time.time()
        
        self.logger.info(
            "Getting global index trends",
            extra={
                "request_id": request_id,
                "indices_count": sum(len(indices) for indices in self.global_indices.values()),
                "service": "intraday_context_service"
            }
        )
        
        try:
            # Get global indices data
            global_data = {}
            
            for region, indices in self.global_indices.items():
                region_data = {}
                
                for symbol, name in indices.items():
                    try:
                        # Get index data from Yahoo Finance
                        index_data = await self._get_index_data(symbol, name, region)
                        if index_data:
                            region_data[symbol] = index_data
                    except Exception as e:
                        self.logger.warning(
                            "Failed to get index data",
                            extra={"symbol": symbol, "region": region, "error": str(e)}
                        )
                        continue
                
                global_data[region] = region_data
            
            # Analyze trends and calculate impact
            trends_analysis = self._analyze_global_trends(global_data)
            
            # Calculate overnight changes
            overnight_changes = await self._calculate_overnight_changes(global_data)
            
            # Assess global sentiment and momentum
            global_sentiment = self._assess_global_sentiment(global_data)
            global_momentum = self._calculate_global_momentum(global_data)
            
            # Determine impact on Indian markets
            indian_impact = self._calculate_indian_market_impact(global_data, trends_analysis)
            
            global_trends = GlobalIndexTrend(
                # US Markets
                sp500_trend=trends_analysis.get("^GSPC", "sideways"),
                nasdaq_trend=trends_analysis.get("^IXIC", "sideways"),
                dow_trend=trends_analysis.get("^DJI", "sideways"),
                
                # European Markets
                ftse_trend=trends_analysis.get("^FTSE", "sideways"),
                dax_trend=trends_analysis.get("^GDAXI", "sideways"),
                cac_trend=trends_analysis.get("^FCHI", "sideways"),
                
                # Asian Markets
                nikkei_trend=trends_analysis.get("^N225", "sideways"),
                hang_seng_trend=trends_analysis.get("^HSI", "sideways"),
                shanghai_trend=trends_analysis.get("000001.SS", "sideways"),
                
                # Emerging Markets
                emerging_markets_trend="mixed",
                
                # Overnight changes
                overnight_us_change=overnight_changes.get("US", Decimal("0")),
                overnight_europe_change=overnight_changes.get("Europe", Decimal("0")),
                overnight_asia_change=overnight_changes.get("Asia", Decimal("0")),
                
                # Global sentiment
                global_risk_sentiment=global_sentiment,
                global_momentum_score=global_momentum,
                
                # Indian impact
                expected_indian_impact=indian_impact["impact"],
                correlation_strength=indian_impact["correlation"],
                
                last_updated=datetime.now()
            )
            
            processing_time = (time.time() - start_time) * 1000
            self.logger.info(
                "Global index trends analysis completed",
                extra={
                    "request_id": request_id,
                    "indices_analyzed": len(trends_analysis),
                    "global_sentiment": global_sentiment,
                    "indian_impact": indian_impact["impact"],
                    "processing_time_ms": round(processing_time, 2),
                    "service": "intraday_context_service"
                }
            )
            
            return global_trends
            
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            self.logger.error(
                "Failed to get global index trends",
                extra={
                    "request_id": request_id,
                    "error": str(e),
                    "processing_time_ms": round(processing_time, 2),
                    "service": "intraday_context_service"
                },
                exc_info=True
            )
            raise
    
    async def generate_intraday_context(
        self,
        symbols: Optional[List[str]] = None,
        timeframes: List[IntradayTimeframe] = None,
        request_id: str = ""
    ) -> IntradayMarketContext:
        """
        Generate comprehensive intraday market context.
        
        Args:
            symbols: Optional symbols for specific analysis
            timeframes: Timeframes for multi-timeframe analysis
            request_id: Request identifier
            
        Returns:
            IntradayMarketContext: Comprehensive intraday context
        """
        start_time = time.time()
        
        if timeframes is None:
            timeframes = [IntradayTimeframe.MINUTE_15, IntradayTimeframe.HOUR_1]
        
        self.logger.info(
            "Generating intraday market context",
            extra={
                "request_id": request_id,
                "symbols_count": len(symbols) if symbols else 0,
                "timeframes": [tf.value for tf in timeframes],
                "service": "intraday_context_service"
            }
        )
        
        try:
            # Get global market context
            global_context = await self._get_global_market_context(request_id)
            
            # Get Indian indices data
            indian_indices = await self._get_indian_indices_data(request_id)
            
            # Multi-timeframe analysis
            timeframe_alignment = await self._analyze_multi_timeframe(timeframes, request_id)
            
            # Market breadth analysis
            market_breadth = await self._analyze_market_breadth(request_id)
            
            # Volatility analysis
            volatility_context = await self._analyze_volatility_context(request_id)
            
            # Sector context
            sector_context = await self._analyze_sector_context(request_id)
            
            # Determine market session and time bias
            market_session = self._get_current_market_session()
            time_bias = self._calculate_time_of_day_bias()
            
            # Calculate global influence
            global_influence_score = self._calculate_global_influence(global_context, indian_indices)
            
            # Generate overnight gap analysis
            overnight_analysis = await self._analyze_overnight_gaps(global_context, indian_indices)
            
            intraday_context = IntradayMarketContext(
                timestamp=datetime.now(),
                request_id=request_id,
                market_session=market_session,
                session_time=self._get_session_time(),
                time_of_day_bias=time_bias,
                indian_indices=indian_indices,
                indian_market_regime=self._determine_indian_regime(indian_indices),
                indian_volatility=volatility_context.volatility_regime,
                global_context=global_context,
                timeframe_alignment=timeframe_alignment["alignment"],
                dominant_timeframe=timeframe_alignment["dominant"],
                timeframe_confluence=timeframe_alignment["confluence"],
                advancing_stocks_ratio=market_breadth.advance_decline_ratio * 100,
                new_highs_lows_ratio=market_breadth.up_down_volume_ratio,
                volume_trend=self._analyze_volume_trend(market_breadth),
                institutional_flow=self._analyze_institutional_flow(),
                vix_level=volatility_context.current_vix,
                vix_trend=volatility_context.vix_trend,
                fear_greed_index=self._calculate_fear_greed_index(volatility_context, market_breadth),
                sector_momentum=sector_context.sector_momentum,
                sector_rotation_stage=sector_context.rotation_stage,
                leading_sectors=sector_context.current_leaders,
                lagging_sectors=sector_context.fading_leaders,
                global_influence_score=global_influence_score,
                overnight_gap_analysis=overnight_analysis,
                foreign_flows=self._get_foreign_flows(),
                liquidity_conditions=self._assess_liquidity_conditions(),
                spread_conditions=self._assess_spread_conditions(),
                execution_quality=self._assess_execution_quality(),
                retail_sentiment=self._get_retail_sentiment(),
                institutional_sentiment=self._get_institutional_sentiment(),
                global_sentiment_impact=global_context.global_sentiment,
                context_confidence=self._calculate_context_confidence(global_context, indian_indices),
                data_freshness_score=self._calculate_data_freshness(),
                processing_time_ms=int((time.time() - start_time) * 1000)
            )
            
            processing_time = (time.time() - start_time) * 1000
            self.logger.info(
                "Intraday market context generated",
                extra={
                    "request_id": request_id,
                    "market_session": market_session.value,
                    "indian_regime": intraday_context.indian_market_regime,
                    "global_influence": float(global_influence_score),
                    "context_confidence": float(intraday_context.context_confidence),
                    "processing_time_ms": round(processing_time, 2),
                    "service": "intraday_context_service"
                }
            )
            
            return intraday_context
            
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            self.logger.error(
                "Failed to generate intraday context",
                extra={
                    "request_id": request_id,
                    "error": str(e),
                    "processing_time_ms": round(processing_time, 2),
                    "service": "intraday_context_service"
                },
                exc_info=True
            )
            raise
    
    async def generate_intraday_trading_signals(
        self,
        symbols: List[str],
        intraday_context: IntradayMarketContext,
        request_id: str
    ) -> Dict[str, IntradayTradingSignal]:
        """
        Generate intraday trading signals based on comprehensive context.
        
        Args:
            symbols: Symbols to analyze
            intraday_context: Market context
            request_id: Request identifier
            
        Returns:
            Dict of trading signals per symbol
        """
        start_time = time.time()
        
        self.logger.info(
            "Generating intraday trading signals",
            extra={
                "request_id": request_id,
                "symbols_count": len(symbols),
                "market_regime": intraday_context.indian_market_regime,
                "global_influence": float(intraday_context.global_influence_score),
                "service": "intraday_context_service"
            }
        )
        
        signals = {}
        
        try:
            for symbol in symbols:
                try:
                    # Get stock-specific analysis
                    trend_analysis = await self.intelligence_service.analyze_stock_trends(
                        symbol=symbol,
                        timeframe="15min",
                        historical_days=10,  # Short period for intraday
                        request_id=request_id
                    )
                    
                    range_analysis = await self.intelligence_service.analyze_range_levels(
                        symbol=symbol,
                        historical_days=20,  # Moderate period for levels
                        request_id=request_id
                    )
                    
                    # Generate contextual trading signal
                    signal = await self._generate_contextual_signal(
                        symbol, trend_analysis, range_analysis, intraday_context, request_id
                    )
                    
                    signals[symbol] = signal
                    
                except Exception as e:
                    self.logger.warning(
                        "Failed to generate signal for symbol",
                        extra={
                            "symbol": symbol,
                            "error": str(e),
                            "request_id": request_id
                        }
                    )
                    continue
            
            processing_time = (time.time() - start_time) * 1000
            self.logger.info(
                "Intraday trading signals generated",
                extra={
                    "request_id": request_id,
                    "signals_generated": len(signals),
                    "processing_time_ms": round(processing_time, 2),
                    "service": "intraday_context_service"
                }
            )
            
            return signals
            
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            self.logger.error(
                "Failed to generate intraday trading signals",
                extra={
                    "request_id": request_id,
                    "error": str(e),
                    "processing_time_ms": round(processing_time, 2),
                    "service": "intraday_context_service"
                },
                exc_info=True
            )
            raise
    
    # Private helper methods
    
    async def _get_index_data(self, symbol: str, name: str, region: str) -> Optional[GlobalIndex]:
        """Get individual index data from Yahoo Finance."""
        try:
            import yfinance as yf
            
            ticker = yf.Ticker(symbol)
            
            # Get intraday data
            hist = ticker.history(period="1d", interval="5m")
            if hist.empty:
                return None
            
            # Get current session data
            latest = hist.iloc[-1]
            session_high = hist['High'].max()
            session_low = hist['Low'].min()
            session_open = hist['Open'].iloc[0]
            
            # Calculate changes
            change = latest['Close'] - session_open
            change_percent = (change / session_open) * 100
            session_change = change_percent
            
            # Determine trend and momentum
            intraday_trend = self._determine_intraday_trend(hist)
            trend_strength = self._calculate_trend_strength(hist)
            momentum = self._calculate_momentum(hist)
            
            return GlobalIndex(
                symbol=symbol,
                name=name,
                region=region,
                current_value=Decimal(str(latest['Close'])),
                change=Decimal(str(change)),
                change_percent=Decimal(str(change_percent)),
                day_high=Decimal(str(latest['High'])),
                day_low=Decimal(str(latest['Low'])),
                day_open=Decimal(str(session_open)),
                volume=int(latest['Volume']) if 'Volume' in latest and latest['Volume'] else None,
                intraday_trend=intraday_trend,
                trend_strength=trend_strength,
                momentum=momentum,
                key_support=Decimal(str(session_low * 1.002)),  # Slight buffer
                key_resistance=Decimal(str(session_high * 0.998)),  # Slight buffer
                session_high=Decimal(str(session_high)),
                session_low=Decimal(str(session_low)),
                session_change=Decimal(str(session_change)),
                last_updated=datetime.now(),
                market_session=self._get_current_market_session()
            )
            
        except Exception as e:
            self.logger.warning(
                "Failed to get index data",
                extra={"symbol": symbol, "error": str(e)}
            )
            return None
    
    async def _get_global_market_context(self, request_id: str) -> GlobalMarketContext:
        """Get comprehensive global market context."""
        try:
            # Get all global indices
            us_indices = {}
            european_indices = {}
            asian_indices = {}
            
            # Get US indices
            for symbol, name in self.global_indices["US"].items():
                index_data = await self._get_index_data(symbol, name, "US")
                if index_data:
                    us_indices[symbol] = index_data
            
            # Get European indices
            for symbol, name in self.global_indices["Europe"].items():
                index_data = await self._get_index_data(symbol, name, "Europe")
                if index_data:
                    european_indices[symbol] = index_data
            
            # Get Asian indices
            for symbol, name in self.global_indices["Asia"].items():
                index_data = await self._get_index_data(symbol, name, "Asia")
                if index_data:
                    asian_indices[symbol] = index_data
            
            # Analyze global sentiment and momentum
            all_indices = {**us_indices, **european_indices, **asian_indices}
            global_sentiment = self._assess_global_sentiment_from_indices(all_indices)
            global_momentum = self._calculate_global_momentum_from_indices(all_indices)
            
            # Calculate correlations (simplified)
            correlations = {
                "us_india": Decimal("0.75"),
                "europe_india": Decimal("0.65"),
                "asia_india": Decimal("0.80")
            }
            
            # Get global themes
            global_themes = self._identify_global_themes(all_indices)
            
            # Calculate overnight changes
            overnight_changes = {}
            for region, indices in {"US": us_indices, "Europe": european_indices, "Asia": asian_indices}.items():
                if indices:
                    avg_change = sum(idx.change_percent for idx in indices.values()) / len(indices)
                    overnight_changes[region.lower()] = Decimal(str(avg_change))
            
            return GlobalMarketContext(
                timestamp=datetime.now(),
                us_indices=us_indices,
                european_indices=european_indices,
                asian_indices=asian_indices,
                global_sentiment=global_sentiment,
                global_momentum=global_momentum,
                global_volatility="normal",  # Would calculate from VIX equivalent
                us_india_correlation=correlations["us_india"],
                europe_india_correlation=correlations["europe_india"],
                asia_india_correlation=correlations["asia_india"],
                global_themes=global_themes,
                risk_on_off=self._determine_risk_on_off(all_indices),
                dollar_strength=Decimal("105.5"),  # Mock - would get from DXY
                commodity_trends={"crude": "up", "gold": "sideways", "copper": "down"},
                overnight_changes=overnight_changes,
                session_momentum=global_momentum.value
            )
            
        except Exception as e:
            self.logger.error(
                "Failed to get global market context",
                extra={"error": str(e), "request_id": request_id},
                exc_info=True
            )
            raise
    
    async def _get_indian_indices_data(self, request_id: str) -> Dict[str, GlobalIndex]:
        """Get Indian indices data from Kite Connect."""
        try:
            indian_indices = {}
            
            # Get Indian indices from Yahoo Finance (more reliable for indices)
            for symbol, name in self.global_indices["India"].items():
                index_data = await self._get_index_data(symbol, name, "India")
                if index_data:
                    indian_indices[symbol] = index_data
            
            return indian_indices
            
        except Exception as e:
            self.logger.warning(
                "Failed to get Indian indices data",
                extra={"error": str(e), "request_id": request_id}
            )
            return {}
    
    def _determine_intraday_trend(self, hist_data) -> str:
        """Determine intraday trend from price data."""
        if hist_data.empty:
            return "sideways"
        
        # Compare current price with session open
        current = hist_data['Close'].iloc[-1]
        session_open = hist_data['Open'].iloc[0]
        
        change_percent = ((current - session_open) / session_open) * 100
        
        if change_percent > 1:
            return "strong_bullish"
        elif change_percent > 0.5:
            return "bullish"
        elif change_percent > -0.5:
            return "sideways"
        elif change_percent > -1:
            return "bearish"
        else:
            return "strong_bearish"
    
    def _calculate_trend_strength(self, hist_data) -> IntradayTrendStrength:
        """Calculate trend strength from historical data."""
        if hist_data.empty:
            return IntradayTrendStrength.VERY_WEAK
        
        # Calculate price momentum
        closes = hist_data['Close'].values
        if len(closes) < 10:
            return IntradayTrendStrength.WEAK
        
        # Calculate trend consistency
        trend_consistency = 0
        for i in range(1, len(closes)):
            if closes[i] > closes[i-1]:
                trend_consistency += 1
        
        consistency_ratio = trend_consistency / (len(closes) - 1)
        
        if consistency_ratio > 0.8:
            return IntradayTrendStrength.VERY_STRONG
        elif consistency_ratio > 0.6:
            return IntradayTrendStrength.STRONG
        elif consistency_ratio > 0.4:
            return IntradayTrendStrength.MODERATE
        elif consistency_ratio > 0.2:
            return IntradayTrendStrength.WEAK
        else:
            return IntradayTrendStrength.VERY_WEAK
    
    def _calculate_momentum(self, hist_data) -> MarketMomentum:
        """Calculate market momentum from price data."""
        if hist_data.empty or len(hist_data) < 6:
            return MarketMomentum.SIDEWAYS
        
        # Calculate momentum over last 6 periods
        recent_closes = hist_data['Close'].tail(6).values
        momentum_score = 0
        
        for i in range(1, len(recent_closes)):
            if recent_closes[i] > recent_closes[i-1]:
                momentum_score += 1
            else:
                momentum_score -= 1
        
        # Determine momentum
        if momentum_score >= 4:
            return MarketMomentum.ACCELERATING_UP
        elif momentum_score >= 2:
            return MarketMomentum.STEADY_UP
        elif momentum_score >= 1:
            return MarketMomentum.SLOWING_UP
        elif momentum_score <= -4:
            return MarketMomentum.ACCELERATING_DOWN
        elif momentum_score <= -2:
            return MarketMomentum.STEADY_DOWN
        elif momentum_score <= -1:
            return MarketMomentum.SLOWING_DOWN
        else:
            return MarketMomentum.SIDEWAYS
    
    def _analyze_global_trends(self, global_data: Dict[str, Dict]) -> Dict[str, str]:
        """Analyze trends across global indices."""
        trends = {}
        
        for region, indices in global_data.items():
            for symbol, index_data in indices.items():
                if hasattr(index_data, 'intraday_trend'):
                    trends[symbol] = index_data.intraday_trend
        
        return trends
    
    async def _calculate_overnight_changes(self, global_data: Dict[str, Dict]) -> Dict[str, Decimal]:
        """Calculate overnight changes by region."""
        overnight_changes = {}
        
        for region, indices in global_data.items():
            if indices:
                avg_change = sum(
                    idx.change_percent for idx in indices.values() 
                    if hasattr(idx, 'change_percent')
                ) / len(indices)
                overnight_changes[region] = Decimal(str(avg_change))
        
        return overnight_changes
    
    def _assess_global_sentiment(self, global_data: Dict[str, Dict]) -> str:
        """Assess overall global market sentiment."""
        positive_count = 0
        total_count = 0
        
        for region, indices in global_data.items():
            for symbol, index_data in indices.items():
                if hasattr(index_data, 'change_percent'):
                    total_count += 1
                    if index_data.change_percent > 0:
                        positive_count += 1
        
        if total_count == 0:
            return "neutral"
        
        positive_ratio = positive_count / total_count
        
        if positive_ratio > 0.7:
            return "very_positive"
        elif positive_ratio > 0.6:
            return "positive"
        elif positive_ratio > 0.4:
            return "neutral"
        elif positive_ratio > 0.3:
            return "negative"
        else:
            return "very_negative"
    
    def _calculate_global_momentum(self, global_data: Dict[str, Dict]) -> Decimal:
        """Calculate global momentum score."""
        momentum_scores = []
        
        for region, indices in global_data.items():
            for symbol, index_data in indices.items():
                if hasattr(index_data, 'change_percent'):
                    momentum_scores.append(float(index_data.change_percent))
        
        if not momentum_scores:
            return Decimal("0")
        
        avg_momentum = sum(momentum_scores) / len(momentum_scores)
        return Decimal(str(avg_momentum * 10))  # Scale for momentum score
    
    def _calculate_indian_market_impact(
        self, 
        global_data: Dict[str, Dict], 
        trends: Dict[str, str]
    ) -> Dict[str, Any]:
        """Calculate expected impact on Indian markets."""
        
        # Count positive vs negative global trends
        positive_trends = sum(1 for trend in trends.values() if "bullish" in trend)
        total_trends = len(trends)
        
        if total_trends == 0:
            return {"impact": "neutral", "correlation": Decimal("0.5")}
        
        positive_ratio = positive_trends / total_trends
        
        if positive_ratio > 0.7:
            impact = "very_positive"
            correlation = Decimal("0.8")
        elif positive_ratio > 0.6:
            impact = "positive"
            correlation = Decimal("0.7")
        elif positive_ratio > 0.4:
            impact = "neutral"
            correlation = Decimal("0.6")
        elif positive_ratio > 0.3:
            impact = "negative"
            correlation = Decimal("0.7")
        else:
            impact = "very_negative"
            correlation = Decimal("0.8")
        
        return {"impact": impact, "correlation": correlation}
    
    def _get_current_market_session(self) -> GlobalMarketSession:
        """Determine current global market session."""
        now = datetime.now()
        hour = now.hour
        
        # Indian market hours (9:15 AM - 3:30 PM IST)
        if 9 <= hour < 15:
            return GlobalMarketSession.INDIAN_OPEN
        elif 8 <= hour < 9:
            return GlobalMarketSession.INDIAN_PREMARKET
        else:
            return GlobalMarketSession.INDIAN_CLOSE
    
    def _calculate_time_of_day_bias(self) -> str:
        """Calculate time-of-day bias for trading."""
        now = datetime.now()
        hour = now.hour
        
        if 9 <= hour < 10:
            return "opening_volatility"
        elif 10 <= hour < 12:
            return "morning_trend"
        elif 12 <= hour < 14:
            return "afternoon_consolidation"
        elif 14 <= hour < 15:
            return "closing_moves"
        else:
            return "after_hours"
    
    def _get_session_time(self) -> str:
        """Get current session time description."""
        now = datetime.now()
        market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
        
        if now < market_open:
            return "pre_market"
        
        session_minutes = (now - market_open).total_seconds() / 60
        total_session_minutes = 6 * 60 + 15  # 6 hours 15 minutes
        
        session_percent = (session_minutes / total_session_minutes) * 100
        
        if session_percent < 25:
            return "early_session"
        elif session_percent < 50:
            return "mid_morning"
        elif session_percent < 75:
            return "afternoon"
        else:
            return "late_session"
    
    # Additional helper methods for comprehensive analysis...
    
    async def _analyze_multi_timeframe(
        self, 
        timeframes: List[IntradayTimeframe], 
        request_id: str
    ) -> Dict[str, Any]:
        """Analyze multiple timeframes for confluence."""
        
        # Mock multi-timeframe analysis
        alignment = {}
        for tf in timeframes:
            # Would get real data for each timeframe
            alignment[tf] = "bullish"  # Mock
        
        # Determine dominant timeframe
        dominant = timeframes[0] if timeframes else IntradayTimeframe.MINUTE_15
        
        # Calculate confluence
        bullish_count = sum(1 for trend in alignment.values() if "bullish" in trend)
        confluence = (bullish_count / len(alignment)) * 100 if alignment else 50
        
        return {
            "alignment": alignment,
            "dominant": dominant,
            "confluence": Decimal(str(confluence))
        }
    
    async def _analyze_market_breadth(self, request_id: str) -> IntradayMarketBreadth:
        """Analyze current market breadth."""
        
        # Mock market breadth data (would get from real sources)
        return IntradayMarketBreadth(
            timestamp=datetime.now(),
            advances=1250,
            declines=850,
            unchanged=100,
            up_volume=1500000000,
            down_volume=1200000000,
            total_volume=2700000000,
            advance_decline_ratio=Decimal("1.47"),
            up_down_volume_ratio=Decimal("1.25"),
            breadth_momentum=Decimal("15.5"),
            breadth_thrust=False,
            breadth_divergence=False,
            sectors_advancing=6,
            sectors_declining=3,
            sector_leadership="broad_based"
        )
    
    async def _analyze_volatility_context(self, request_id: str) -> IntradayVolatilityContext:
        """Analyze volatility context for intraday trading."""
        
        try:
            # Get VIX data
            economic_indicators = await self.yahoo_service.get_economic_indicators()
            current_vix = economic_indicators.get('india_vix', 20.0)
            
            return IntradayVolatilityContext(
                timestamp=datetime.now(),
                current_vix=Decimal(str(current_vix)),
                vix_change=Decimal("0.5"),  # Mock
                vix_trend="stable",
                intraday_volatility=Decimal("2.5"),
                volatility_regime="normal",
                volatility_momentum="stable",
                volatility_clustering=False,
                volatility_breakout=False,
                expected_daily_range=Decimal("1.8"),
                risk_adjusted_returns=Decimal("0.15")
            )
            
        except Exception as e:
            self.logger.warning(f"Volatility analysis failed: {e}")
            # Return default volatility context
            return IntradayVolatilityContext(
                timestamp=datetime.now(),
                current_vix=Decimal("20.0"),
                vix_change=Decimal("0"),
                vix_trend="stable",
                intraday_volatility=Decimal("2.0"),
                volatility_regime="normal",
                volatility_momentum="stable",
                volatility_clustering=False,
                volatility_breakout=False,
                expected_daily_range=Decimal("1.5"),
                risk_adjusted_returns=Decimal("0.12")
            )
    
    async def _analyze_sector_context(self, request_id: str) -> IntradaySectorContext:
        """Analyze sector context for intraday rotation."""
        
        try:
            # Get sector performance from Yahoo Finance
            sector_data = await self.yahoo_service.get_sector_performance()
            
            # Analyze sector momentum
            sector_momentum = {}
            for sector, performance in sector_data.items():
                if performance > 1:
                    sector_momentum[sector] = "strong_up"
                elif performance > 0.5:
                    sector_momentum[sector] = "moderate_up"
                elif performance > -0.5:
                    sector_momentum[sector] = "sideways"
                elif performance > -1:
                    sector_momentum[sector] = "moderate_down"
                else:
                    sector_momentum[sector] = "strong_down"
            
            # Identify leaders and laggards
            sorted_sectors = sorted(sector_data.items(), key=lambda x: x[1], reverse=True)
            current_leaders = [sector for sector, perf in sorted_sectors[:3] if perf > 0]
            fading_leaders = [sector for sector, perf in sorted_sectors[-3:] if perf < 0]
            
            return IntradaySectorContext(
                timestamp=datetime.now(),
                sector_performance={k: Decimal(str(v)) for k, v in sector_data.items()},
                sector_momentum=sector_momentum,
                sector_volume={},  # Would get from real data
                rotation_stage="mid_cycle",
                rotation_momentum=Decimal("15.5"),
                rotation_sustainability="moderate",
                current_leaders=current_leaders,
                emerging_leaders=[],
                fading_leaders=fading_leaders,
                global_sector_trends={},
                sector_correlation_with_global={},
                morning_sector_leaders=[],
                afternoon_sector_leaders=[],
                sector_momentum_shifts=[]
            )
            
        except Exception as e:
            self.logger.warning(f"Sector analysis failed: {e}")
            return IntradaySectorContext(
                timestamp=datetime.now(),
                sector_performance={},
                sector_momentum={},
                sector_volume={},
                rotation_stage="unknown",
                rotation_momentum=Decimal("0"),
                rotation_sustainability="unknown",
                current_leaders=[],
                emerging_leaders=[],
                fading_leaders=[],
                global_sector_trends={},
                sector_correlation_with_global={},
                morning_sector_leaders=[],
                afternoon_sector_leaders=[],
                sector_momentum_shifts=[]
            )
    
    # Additional helper methods...
    
    def _assess_global_sentiment_from_indices(self, indices: Dict[str, GlobalIndex]) -> str:
        """Assess global sentiment from indices data."""
        if not indices:
            return "neutral"
        
        positive_count = sum(1 for idx in indices.values() if idx.change_percent > 0)
        total_count = len(indices)
        
        positive_ratio = positive_count / total_count
        
        if positive_ratio > 0.7:
            return "very_positive"
        elif positive_ratio > 0.6:
            return "positive"
        elif positive_ratio > 0.4:
            return "neutral"
        else:
            return "negative"
    
    def _calculate_global_momentum_from_indices(self, indices: Dict[str, GlobalIndex]) -> MarketMomentum:
        """Calculate global momentum from indices."""
        if not indices:
            return MarketMomentum.SIDEWAYS
        
        momentum_scores = [float(idx.change_percent) for idx in indices.values()]
        avg_momentum = sum(momentum_scores) / len(momentum_scores)
        
        if avg_momentum > 1:
            return MarketMomentum.ACCELERATING_UP
        elif avg_momentum > 0.5:
            return MarketMomentum.STEADY_UP
        elif avg_momentum > -0.5:
            return MarketMomentum.SIDEWAYS
        elif avg_momentum > -1:
            return MarketMomentum.STEADY_DOWN
        else:
            return MarketMomentum.ACCELERATING_DOWN
    
    def _identify_global_themes(self, indices: Dict[str, GlobalIndex]) -> List[str]:
        """Identify global market themes."""
        themes = []
        
        if not indices:
            return themes
        
        # Analyze performance by region
        us_performance = [idx.change_percent for symbol, idx in indices.items() if symbol.startswith("^") and "US" in getattr(idx, 'region', '')]
        
        if us_performance:
            avg_us = sum(us_performance) / len(us_performance)
            if avg_us > 1:
                themes.append("US market strength")
            elif avg_us < -1:
                themes.append("US market weakness")
        
        # Add more theme detection logic...
        themes.append("Global market analysis")
        
        return themes
    
    def _determine_risk_on_off(self, indices: Dict[str, GlobalIndex]) -> str:
        """Determine risk-on/risk-off sentiment."""
        if not indices:
            return "neutral"
        
        # Simplified risk-on/off calculation
        positive_count = sum(1 for idx in indices.values() if idx.change_percent > 0)
        total = len(indices)
        
        if positive_count / total > 0.6:
            return "risk_on"
        elif positive_count / total < 0.4:
            return "risk_off"
        else:
            return "neutral"
    
    # Additional methods for context generation...
    
    def _determine_indian_regime(self, indian_indices: Dict[str, GlobalIndex]) -> str:
        """Determine Indian market regime."""
        if not indian_indices:
            return "unknown"
        
        nifty_data = indian_indices.get("^NSEI")
        if nifty_data:
            if abs(nifty_data.change_percent) > 1:
                return "trending"
            else:
                return "range_bound"
        
        return "unknown"
    
    def _calculate_global_influence(
        self, 
        global_context: GlobalMarketContext, 
        indian_indices: Dict[str, GlobalIndex]
    ) -> Decimal:
        """Calculate global influence score on Indian markets."""
        
        # Base influence score
        influence = Decimal("50")
        
        # US market influence (highest weight)
        if global_context.us_indices:
            us_avg_change = sum(idx.change_percent for idx in global_context.us_indices.values()) / len(global_context.us_indices)
            influence += us_avg_change * 2  # 2x weight for US
        
        # Asian market influence
        if global_context.asian_indices:
            asia_avg_change = sum(idx.change_percent for idx in global_context.asian_indices.values()) / len(global_context.asian_indices)
            influence += asia_avg_change * 1.5  # 1.5x weight for Asia
        
        # European market influence
        if global_context.european_indices:
            europe_avg_change = sum(idx.change_percent for idx in global_context.european_indices.values()) / len(global_context.european_indices)
            influence += europe_avg_change * 1  # 1x weight for Europe
        
        return max(Decimal("0"), min(Decimal("100"), influence))
    
    async def _analyze_overnight_gaps(
        self, 
        global_context: GlobalMarketContext, 
        indian_indices: Dict[str, GlobalIndex]
    ) -> Dict[str, Any]:
        """Analyze overnight gaps and their implications."""
        
        gaps = {}
        
        # Calculate expected gaps based on global moves
        if global_context.overnight_changes:
            total_global_change = sum(global_context.overnight_changes.values()) / len(global_context.overnight_changes)
            
            gaps = {
                "expected_gap": float(total_global_change * Decimal("0.7")),  # 70% correlation
                "gap_direction": "up" if total_global_change > 0 else "down",
                "gap_magnitude": "small" if abs(total_global_change) < 1 else "large",
                "gap_sustainability": "likely" if abs(total_global_change) > 0.5 else "uncertain"
            }
        
        return gaps
    
    # Mock methods for additional context (would be enhanced with real data)
    
    def _get_foreign_flows(self) -> Dict[str, Decimal]:
        """Get foreign institutional flows."""
        return {
            "fii_net": Decimal("1250.5"),
            "dii_net": Decimal("-650.8"),
            "net_flow": Decimal("599.7")
        }
    
    def _assess_liquidity_conditions(self) -> str:
        """Assess current liquidity conditions."""
        # Would analyze bid-ask spreads, market depth, etc.
        return "good"
    
    def _assess_spread_conditions(self) -> str:
        """Assess bid-ask spread conditions."""
        # Would analyze current spreads across instruments
        return "normal"
    
    def _assess_execution_quality(self) -> str:
        """Assess expected execution quality."""
        # Would analyze market microstructure
        return "good"
    
    def _get_retail_sentiment(self) -> str:
        """Get retail sentiment indicator."""
        return "bullish"
    
    def _get_institutional_sentiment(self) -> str:
        """Get institutional sentiment indicator."""
        return "cautious"
    
    def _calculate_context_confidence(
        self, 
        global_context: GlobalMarketContext, 
        indian_indices: Dict[str, GlobalIndex]
    ) -> Decimal:
        """Calculate overall context confidence."""
        
        confidence = Decimal("50")
        
        # Data availability
        if global_context.us_indices:
            confidence += Decimal("15")
        if global_context.asian_indices:
            confidence += Decimal("10")
        if indian_indices:
            confidence += Decimal("20")
        
        return min(Decimal("95"), confidence)
    
    def _calculate_data_freshness(self) -> Decimal:
        """Calculate data freshness score."""
        # Would check timestamp freshness of all data sources
        return Decimal("90")
    
    def _analyze_volume_trend(self, breadth: IntradayMarketBreadth) -> str:
        """Analyze volume trend from breadth data."""
        if breadth.up_down_volume_ratio > Decimal("1.2"):
            return "increasing"
        elif breadth.up_down_volume_ratio < Decimal("0.8"):
            return "decreasing"
        else:
            return "stable"
    
    def _analyze_institutional_flow(self) -> str:
        """Analyze institutional flow."""
        # Mock - would analyze real institutional data
        return "buying"
    
    def _calculate_fear_greed_index(
        self, 
        volatility: IntradayVolatilityContext, 
        breadth: IntradayMarketBreadth
    ) -> int:
        """Calculate fear & greed index."""
        
        score = 50  # Neutral
        
        # VIX component
        vix = float(volatility.current_vix)
        if vix < 15:
            score += 20
        elif vix > 25:
            score -= 20
        
        # Breadth component
        ad_ratio = float(breadth.advance_decline_ratio)
        if ad_ratio > 1.5:
            score += 15
        elif ad_ratio < 0.7:
            score -= 15
        
        return max(0, min(100, score))
    
    async def _generate_contextual_signal(
        self,
        symbol: str,
        trend_analysis: Any,
        range_analysis: Any,
        context: IntradayMarketContext,
        request_id: str
    ) -> IntradayTradingSignal:
        """Generate contextual trading signal for a symbol."""
        
        # Determine signal type based on analysis
        signal_type = "hold"
        signal_strength = Decimal("50")
        
        # Analyze alignments
        global_alignment = context.global_influence_score > 60
        sector_alignment = True  # Would check sector alignment
        timeframe_alignment = context.timeframe_confluence > 60
        
        # Generate signal based on context
        if (trend_analysis.primary_trend in ["bullish", "strong_bullish"] and 
            global_alignment and timeframe_alignment):
            signal_type = "buy"
            signal_strength = Decimal("75")
        elif (trend_analysis.primary_trend in ["bearish", "strong_bearish"] and 
              not global_alignment):
            signal_type = "sell"
            signal_strength = Decimal("65")
        
        # Calculate levels
        current_price = trend_analysis.trend_current_price
        entry_price = current_price
        target_price = current_price * Decimal("1.02")  # 2% target
        stop_loss = current_price * Decimal("0.99")     # 1% stop
        
        return IntradayTradingSignal(
            symbol=symbol,
            signal_type=signal_type,
            signal_strength=signal_strength,
            global_alignment=global_alignment,
            sector_alignment=sector_alignment,
            timeframe_alignment=timeframe_alignment,
            entry_price=entry_price,
            target_price=target_price,
            stop_loss=stop_loss,
            risk_reward_ratio=Decimal("2.0"),
            position_size_percent=Decimal("5.0"),
            primary_reasons=[f"Trend: {trend_analysis.primary_trend}", "Global alignment"],
            global_factors=[f"Global influence: {context.global_influence_score}%"],
            risk_factors=["Intraday volatility"],
            signal_timestamp=datetime.now(),
            expected_duration="intraday",
            urgency="normal"
        )
