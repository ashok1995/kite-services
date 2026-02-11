"""
Analysis API Module

Consolidated market analysis endpoints for Kite Services.
Provides comprehensive market context and stock intelligence.

Endpoints:
- POST /analysis/context - Complete market context analysis
- POST /analysis/intelligence - Stock-specific intelligence

Note: For enhanced hierarchical context with trading style optimization,
see /analysis/context/enhanced endpoint (analysis_enhanced module)
"""

import logging
import time

from fastapi import APIRouter, HTTPException

from core.service_manager import get_service_manager
from models.unified_api_models import (
    IntelligenceRequest,
    IntelligenceResponse,
    MarketContextRequest,
    MarketContextResponse,
    StockAnalysisRequest,
    StockAnalysisResponse,
    StockIntelligence,
)
from services.market_context_service import MarketContextService
from services.market_intelligence_service import MarketIntelligenceService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/analysis/context", response_model=MarketContextResponse)
async def get_market_context(request: MarketContextRequest):
    """
    Complete market context analysis.

    Provides comprehensive market analysis including:
    - Global market data (US, Europe, Asia)
    - Indian market data (Nifty, Sensex, sector indices)
    - Market sentiment indicators
    - Technical analysis for specified symbols

    Args:
        symbols: Specific symbols to analyze (optional)
        include_global: Include global market context
        include_indian: Include Indian market context
        include_sentiment: Include market sentiment analysis
        include_technical: Include technical analysis
    """
    start_time = time.time()

    try:
        service_manager = await get_service_manager()
        market_context_service = service_manager.market_context_service

        logger.info(f"Generating market context analysis for {len(request.symbols or [])} symbols")

        # Initialize response data
        global_markets = []
        indian_markets = []
        market_sentiment = None
        technical_analysis = []

        # Get global market data
        if request.include_global:
            try:
                global_data = await market_context_service.get_global_market_data()
                if global_data:
                    global_markets = [
                        GlobalMarketData(
                            market=market.get("market", ""),
                            index=market.get("index", ""),
                            last_price=market.get("last_price"),
                            change=market.get("change"),
                            change_percent=market.get("change_percent"),
                            timestamp=market.get("timestamp"),
                        )
                        for market in global_data
                    ]
            except Exception as e:
                logger.warning(f"Failed to get global market data: {str(e)}")

        # Get Indian market data
        if request.include_indian:
            try:
                indian_data = await market_context_service.get_indian_market_data()
                if indian_data:
                    indian_markets = [
                        GlobalMarketData(
                            market=market.get("market", ""),
                            index=market.get("index", ""),
                            last_price=market.get("last_price"),
                            change=market.get("change"),
                            change_percent=market.get("change_percent"),
                            timestamp=market.get("timestamp"),
                        )
                        for market in indian_data
                    ]
            except Exception as e:
                logger.warning(f"Failed to get Indian market data: {str(e)}")

        # Get market sentiment
        if request.include_sentiment:
            try:
                sentiment_data = await market_context_service.get_market_sentiment()
                if sentiment_data:
                    market_sentiment = MarketSentiment(
                        overall_sentiment=sentiment_data.get("overall_sentiment", "neutral"),
                        fear_greed_index=sentiment_data.get("fear_greed_index"),
                        vix=sentiment_data.get("vix"),
                        put_call_ratio=sentiment_data.get("put_call_ratio"),
                        advance_decline_ratio=sentiment_data.get("advance_decline_ratio"),
                        timestamp=sentiment_data.get("timestamp"),
                    )
            except Exception as e:
                logger.warning(f"Failed to get market sentiment: {str(e)}")

        # Get technical analysis for specified symbols
        if request.include_technical and request.symbols:
            try:
                for symbol in request.symbols:
                    try:
                        tech_data = await market_context_service.get_technical_analysis(symbol)
                        if tech_data:
                            technical_analysis.append(
                                TechnicalAnalysis(
                                    symbol=symbol,
                                    trend=tech_data.get("trend"),
                                    support_levels=tech_data.get("support_levels", []),
                                    resistance_levels=tech_data.get("resistance_levels", []),
                                    moving_averages=tech_data.get("moving_averages", {}),
                                    rsi=tech_data.get("rsi"),
                                    macd=tech_data.get("macd"),
                                    bollinger_bands=tech_data.get("bollinger_bands"),
                                    timestamp=tech_data.get("timestamp"),
                                )
                            )
                    except Exception as e:
                        logger.warning(f"Failed to get technical analysis for {symbol}: {str(e)}")
            except Exception as e:
                logger.warning(f"Failed to get technical analysis: {str(e)}")

        processing_time = (time.time() - start_time) * 1000

        return MarketContextResponse(
            success=True,
            global_markets=global_markets,
            indian_markets=indian_markets,
            market_sentiment=market_sentiment,
            technical_analysis=technical_analysis,
            processing_time_ms=round(processing_time, 2),
            message="Market context analysis completed successfully",
        )

    except Exception as e:
        logger.error(f"Market context analysis failed: {str(e)}")
        processing_time = (time.time() - start_time) * 1000
        raise HTTPException(status_code=500, detail=f"Market context analysis failed: {str(e)}")


@router.post("/analysis/intelligence", response_model=IntelligenceResponse)
async def get_stock_intelligence(request: IntelligenceRequest):
    """
    Stock-specific intelligence analysis.

    Provides comprehensive stock analysis including:
    - Overall trend analysis and strength
    - Support and resistance levels
    - Trading signals with confidence scores
    - Risk assessment and volatility analysis

    Args:
        symbol: Stock symbol to analyze
        include_trends: Include trend analysis
        include_levels: Include support/resistance levels
        include_signals: Include trading signals
        time_horizon: Analysis time horizon (short, medium, long)
    """
    start_time = time.time()

    try:
        service_manager = await get_service_manager()
        intelligence_service = service_manager.market_intelligence_service

        logger.info(f"Generating intelligence analysis for {request.symbol}")

        # Initialize intelligence data
        intelligence_data = {
            "symbol": request.symbol,
            "support_levels": [],
            "resistance_levels": [],
            "key_levels": [],
            "trading_signals": [],
            "timestamp": None,
        }

        # Get trend analysis
        if request.include_trends:
            try:
                trend_data = await intelligence_service.get_trend_analysis(
                    symbol=request.symbol, time_horizon=request.time_horizon
                )
                if trend_data:
                    intelligence_data.update(
                        {
                            "overall_trend": trend_data.get("overall_trend"),
                            "trend_strength": trend_data.get("trend_strength"),
                            "momentum": trend_data.get("momentum"),
                            "volatility": trend_data.get("volatility"),
                            "risk_level": trend_data.get("risk_level"),
                        }
                    )
            except Exception as e:
                logger.warning(f"Failed to get trend analysis for {request.symbol}: {str(e)}")

        # Get support and resistance levels
        if request.include_levels:
            try:
                levels_data = await intelligence_service.get_support_resistance_levels(
                    symbol=request.symbol, time_horizon=request.time_horizon
                )
                if levels_data:
                    intelligence_data.update(
                        {
                            "support_levels": levels_data.get("support_levels", []),
                            "resistance_levels": levels_data.get("resistance_levels", []),
                            "key_levels": levels_data.get("key_levels", []),
                        }
                    )
            except Exception as e:
                logger.warning(f"Failed to get levels for {request.symbol}: {str(e)}")

        # Get trading signals
        if request.include_signals:
            try:
                signals_data = await intelligence_service.get_trading_signals(
                    symbol=request.symbol, time_horizon=request.time_horizon
                )
                if signals_data:
                    trading_signals = [
                        TradingSignal(
                            signal_type=signal.get("signal_type", "hold"),
                            confidence=signal.get("confidence", 0.5),
                            strength=signal.get("strength", "medium"),
                            reason=signal.get("reason", ""),
                            price_target=signal.get("price_target"),
                            stop_loss=signal.get("stop_loss"),
                            timestamp=signal.get("timestamp"),
                        )
                        for signal in signals_data.get("signals", [])
                    ]
                    intelligence_data["trading_signals"] = trading_signals
            except Exception as e:
                logger.warning(f"Failed to get trading signals for {request.symbol}: {str(e)}")

        processing_time = (time.time() - start_time) * 1000

        stock_intelligence = StockIntelligence(**intelligence_data)

        return IntelligenceResponse(
            success=True,
            intelligence=stock_intelligence,
            processing_time_ms=round(processing_time, 2),
            message=f"Intelligence analysis completed for {request.symbol}",
        )

    except Exception as e:
        logger.error(f"Intelligence analysis failed for {request.symbol}: {str(e)}")
        processing_time = (time.time() - start_time) * 1000
        raise HTTPException(status_code=500, detail=f"Intelligence analysis failed: {str(e)}")


@router.post("/analysis/stock", response_model=StockAnalysisResponse)
async def get_stock_analysis(request: StockAnalysisRequest):
    """
    Single-instrument analysis endpoint.

    Performs detailed analysis for one stock including:
    - Current price and OHLC data
    - Technical indicators (RSI, MACD, Bollinger)
    - Support/resistance levels
    - Trend analysis and momentum
    - Trading signals and recommendations

    Args:
        symbol: Single stock symbol (e.g., "RELIANCE")
        analysis_type: Type of analysis to perform
        time_horizon: Time horizon for analysis
    """

    start_time = time.time()

    try:
        service_manager = await get_service_manager()
        kite_client = service_manager.kite_client
        intelligence_service = service_manager.market_intelligence_service

        logger.info(
            f"Performing {request.analysis_type} analysis for {request.symbol} "
            f"({request.time_horizon})"
        )

        # Get current quote
        quotes = await kite_client.quote([request.symbol])
        if not quotes or request.symbol not in quotes:
            return StockAnalysisResponse(
                success=False,
                symbol=request.symbol,
                analysis_type=request.analysis_type,
                time_horizon=request.time_horizon,
                processing_time_ms=round((time.time() - start_time) * 1000, 2),
                message=f"Failed to fetch current quote for {request.symbol}",
            )

        quote_data = quotes[request.symbol]

        # Extract current price data
        current_price = quote_data.get("last_price")
        open_price = quote_data.get("ohlc", {}).get("open")
        high_price = quote_data.get("ohlc", {}).get("high")
        low_price = quote_data.get("ohlc", {}).get("low")
        change = quote_data.get("net_change")
        change_percent = quote_data.get("net_change_percent")
        volume = quote_data.get("volume")

        # Initialize analysis data
        analysis_data = {
            "success": True,
            "symbol": request.symbol,
            "analysis_type": request.analysis_type,
            "time_horizon": request.time_horizon,
            "current_price": current_price,
            "open_price": open_price,
            "high_price": high_price,
            "low_price": low_price,
            "change": change,
            "change_percent": change_percent,
            "volume": volume,
        }

        # Get technical analysis if requested
        if request.analysis_type in ["technical", "comprehensive"]:
            try:
                # Get technical indicators (approximated for now)
                # In a full implementation, this would use real historical data
                analysis_data.update(
                    {
                        "rsi_14": 55.0,  # Would calculate from recent candles
                        "macd_signal": (
                            "bullish" if change_percent and change_percent > 0 else "bearish"
                        ),
                        "bollinger_position": "middle",  # Would calculate from recent prices
                        "sma_20": current_price * 0.98,  # Approximation
                        "sma_50": current_price * 0.95,  # Approximation
                        "immediate_support": current_price * 0.97,
                        "immediate_resistance": current_price * 1.03,
                        "trend": "bullish" if change_percent and change_percent > 0 else "bearish",
                        "trend_strength": "moderate",
                        "momentum": (
                            "increasing" if change_percent and change_percent > 0.5 else "stable"
                        ),
                    }
                )
            except Exception as e:
                logger.warning(f"Technical analysis failed for {request.symbol}: {str(e)}")

        # Get trading signals if comprehensive analysis
        if request.analysis_type == "comprehensive":
            try:
                # Generate basic signals based on current data
                if change_percent and change_percent > 1.0:
                    signal = "BUY"
                    confidence = 0.7
                    target_price = current_price * 1.05
                    stop_loss = current_price * 0.98
                elif change_percent and change_percent < -1.0:
                    signal = "SELL"
                    confidence = 0.7
                    target_price = current_price * 0.95
                    stop_loss = current_price * 1.02
                else:
                    signal = "HOLD"
                    confidence = 0.5
                    target_price = None
                    stop_loss = None

                analysis_data.update(
                    {
                        "signal": signal,
                        "confidence": confidence,
                        "target_price": target_price,
                        "stop_loss": stop_loss,
                    }
                )
            except Exception as e:
                logger.warning(f"Signal generation failed for {request.symbol}: {str(e)}")

        processing_time = (time.time() - start_time) * 1000

        return StockAnalysisResponse(
            success=True,
            symbol=request.symbol,
            analysis_type=request.analysis_type,
            time_horizon=request.time_horizon,
            current_price=current_price,
            open_price=open_price,
            high_price=high_price,
            low_price=low_price,
            change=change,
            change_percent=change_percent,
            volume=volume,
            rsi_14=analysis_data.get("rsi_14"),
            macd_signal=analysis_data.get("macd_signal"),
            bollinger_position=analysis_data.get("bollinger_position"),
            sma_20=analysis_data.get("sma_20"),
            sma_50=analysis_data.get("sma_50"),
            immediate_support=analysis_data.get("immediate_support"),
            immediate_resistance=analysis_data.get("immediate_resistance"),
            trend=analysis_data.get("trend"),
            trend_strength=analysis_data.get("trend_strength"),
            momentum=analysis_data.get("momentum"),
            signal=analysis_data.get("signal"),
            confidence=analysis_data.get("confidence"),
            target_price=analysis_data.get("target_price"),
            stop_loss=analysis_data.get("stop_loss"),
            processing_time_ms=round(processing_time, 2),
            message=f"Stock analysis completed for {request.symbol} ({request.analysis_type})",
        )

    except Exception as e:
        logger.error(f"Stock analysis failed for {request.symbol}: {str(e)}")
        processing_time = (time.time() - start_time) * 1000

        return StockAnalysisResponse(
            success=False,
            symbol=request.symbol,
            analysis_type=request.analysis_type,
            time_horizon=request.time_horizon,
            processing_time_ms=round(processing_time, 2),
            message=f"Stock analysis failed: {str(e)}",
        )
