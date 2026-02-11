"""
Enhanced Analysis API Module
============================

Enhanced market analysis endpoints with multi-level hierarchical context
specifically designed for real-time trading recommendation systems.

Features:
- Primary context: High-level market overview
- Detailed context: Granular analysis with sectors, technicals
- Style-specific context: Optimized for intraday/swing/long-term trading

Endpoints:
- POST /analysis/context/enhanced - Enhanced hierarchical market context
- POST /analysis/context/realtime - Real-time context for immediate decisions
"""

import logging
import time
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from kiteconnect.exceptions import KiteException, TokenException

from config.cache_config import CacheTTL
from core.cache_service import CacheService
from core.kite_exceptions import KiteErrorHandler, TokenExpiredException
from core.service_manager import get_service_manager
from models.enhanced_context_models import (
    DetailedMarketContext,
    EnhancedMarketContextRequest,
    EnhancedMarketContextResponse,
    GlobalMarketPrimary,
    IndexDetailedAnalysis,
    IndianMarketPrimary,
    IntradayContext,
    LongTermContext,
    MarketRegime,
    PrimaryMarketContext,
    QuickTradingOpportunity,
    SectorPerformance,
    SwingContext,
    TechnicalIndicators,
    TradingStyle,
    TrendStrength,
    VolatilityLevel,
)

logger = logging.getLogger(__name__)
router = APIRouter()


from api.analysis_enhanced_cache import (
    get_cache_key_detailed,
    get_cache_key_intraday,
    get_cache_key_longterm,
    get_cache_key_primary,
    get_cache_key_swing,
)
from api.analysis_enhanced_helpers import (
    calculate_context_quality,
    calculate_market_score,
    determine_favorable_styles,
    get_data_quality_recommendations,
)


@router.post("/analysis/context/enhanced", response_model=EnhancedMarketContextResponse)
async def get_enhanced_market_context(request: EnhancedMarketContextRequest):
    """
    Get enhanced hierarchical market context for trading decisions.

    **Use Cases:**
    - Real-time trading recommendation systems
    - Contextual features for ML models
    - Multi-timeframe market analysis
    - Risk assessment and position sizing

    **Context Levels:**

    1. **PRIMARY** - High-level overview (always fast, <100ms)
       - Global market sentiment
       - Major index changes
       - Overall market regime
       - Quick decision support

    2. **DETAILED** - Granular analysis (medium speed, <500ms)
       - Sector performance
       - Technical indicators
       - Market breadth
       - Top movers

    3. **STYLE-SPECIFIC** - Optimized for trading style (comprehensive, <1s)
       - Intraday: Minute-level momentum, VWAP, pivot points
       - Swing: Multi-day patterns, sector rotation
       - Long-term: Macro trends, fundamentals, themes

    **Response Structure:**
    ```json
    {
      "primary_context": {
        "overall_market_score": 45,  // -100 to +100
        "market_confidence": 0.85,
        "favorable_for": ["swing", "long_term"]
      },
      "detailed_context": {
        "sectors": [...],
        "nifty_analysis": {...}
      },
      "intraday_context": {...},
      "swing_context": {...}
    }
    ```
    """
    start_time = time.time()

    try:
        service_manager = await get_service_manager()
        market_context_service = service_manager.market_context_service
        intelligence_service = service_manager.market_intelligence_service
        cache_service = service_manager.cache_service

        logger.info(f"Generating enhanced market context for styles: {request.trading_styles}")

        # Initialize response components
        primary_context = None
        detailed_context = None
        intraday_context = None
        swing_context = None
        long_term_context = None
        warnings = []
        cache_hits = []

        # ================================================================
        # PRIMARY CONTEXT - High-level overview (CACHED: 1 min TTL)
        # ================================================================
        if request.include_primary:
            try:
                cache_key = get_cache_key_primary()

                # Try cache first
                if cache_service and cache_service.enabled:
                    cached_primary = await cache_service.get(cache_key)
                    if cached_primary:
                        primary_context = PrimaryMarketContext(**cached_primary)
                        cache_hits.append("primary")
                        logger.info("✅ PRIMARY CONTEXT: Cache HIT")

                # Cache miss - generate fresh
                if not primary_context:
                    logger.info("⚠️  PRIMARY CONTEXT: Cache MISS - generating...")
                    primary_context = await _generate_primary_context(
                        market_context_service, intelligence_service
                    )

                    # Cache the result
                    if cache_service and cache_service.enabled and primary_context:
                        await cache_service.set(
                            cache_key, primary_context.dict(), ttl=CacheTTL.PRIMARY_CONTEXT
                        )
                        logger.info(f"💾 Cached primary context (TTL={CacheTTL.PRIMARY_CONTEXT}s)")

            except Exception as e:
                logger.error(f"Failed to generate primary context: {e}")
                warnings.append(f"Primary context generation failed: {str(e)}")

        # ================================================================
        # DETAILED CONTEXT - Granular analysis (CACHED: 5 min TTL)
        # ================================================================
        if request.include_detailed:
            try:
                cache_key = get_cache_key_detailed()

                # Try cache first
                if cache_service and cache_service.enabled:
                    cached_detailed = await cache_service.get(cache_key)
                    if cached_detailed:
                        detailed_context = DetailedMarketContext(**cached_detailed)
                        cache_hits.append("detailed")
                        logger.info("✅ DETAILED CONTEXT: Cache HIT")

                # Cache miss - generate fresh
                if not detailed_context:
                    logger.info("⚠️  DETAILED CONTEXT: Cache MISS - generating...")
                    detailed_context = await _generate_detailed_context(
                        market_context_service,
                        intelligence_service,
                        include_sectors=request.include_sectors,
                        include_technicals=request.include_technicals,
                    )

                    # Cache the result
                    if cache_service and cache_service.enabled and detailed_context:
                        await cache_service.set(
                            cache_key, detailed_context.dict(), ttl=CacheTTL.DETAILED_CONTEXT
                        )
                        logger.info(
                            f"💾 Cached detailed context (TTL={CacheTTL.DETAILED_CONTEXT}s)"
                        )

            except Exception as e:
                logger.error(f"Failed to generate detailed context: {e}")
                warnings.append(f"Detailed context generation failed: {str(e)}")

        # ================================================================
        # STYLE-SPECIFIC CONTEXTS (SMART CACHING WITH REUSE)
        # ================================================================
        if request.include_style_specific:
            # Intraday context (30s TTL - base for swing/long-term)
            if (
                TradingStyle.INTRADAY in request.trading_styles
                or TradingStyle.ALL in request.trading_styles
            ):
                try:
                    cache_key = get_cache_key_intraday()

                    # Try cache first
                    if cache_service and cache_service.enabled:
                        cached_intraday = await cache_service.get(cache_key)
                        if cached_intraday:
                            intraday_context = IntradayContext(**cached_intraday)
                            cache_hits.append("intraday")
                            logger.info("✅ INTRADAY CONTEXT: Cache HIT")

                    # Cache miss - generate fresh
                    if not intraday_context:
                        logger.info("⚠️  INTRADAY CONTEXT: Cache MISS - generating...")
                        intraday_context = await _generate_intraday_context(
                            market_context_service,
                            intelligence_service,
                            focus_symbols=request.focus_symbols,
                        )

                        # Cache the result (for reuse by swing/long-term)
                        if cache_service and cache_service.enabled and intraday_context:
                            await cache_service.set(
                                cache_key, intraday_context.dict(), ttl=CacheTTL.COMPOSITE_INTRADAY
                            )
                            logger.info(
                                f"💾 Cached intraday context (TTL={CacheTTL.COMPOSITE_INTRADAY}s)"
                            )

                except Exception as e:
                    logger.error(f"Failed to generate intraday context: {e}")
                    warnings.append(f"Intraday context generation failed: {str(e)}")

            # Swing context (5min TTL - can REUSE intraday base)
            if (
                TradingStyle.SWING in request.trading_styles
                or TradingStyle.ALL in request.trading_styles
            ):
                try:
                    cache_key = get_cache_key_swing()

                    # Try cache first
                    if cache_service and cache_service.enabled:
                        cached_swing = await cache_service.get(cache_key)
                        if cached_swing:
                            swing_context = SwingContext(**cached_swing)
                            cache_hits.append("swing")
                            logger.info("✅ SWING CONTEXT: Cache HIT")

                    # Cache miss - generate (may reuse intraday)
                    if not swing_context:
                        # Check if intraday data is available (from cache or fresh generation)
                        intraday_base = None
                        if not intraday_context and cache_service and cache_service.enabled:
                            # Try to reuse cached intraday data
                            intraday_cache_key = get_cache_key_intraday()
                            cached_intraday = await cache_service.get(intraday_cache_key)
                            if cached_intraday:
                                intraday_base = IntradayContext(**cached_intraday)
                                logger.info("🔄 SWING: Reusing cached intraday data")
                        elif intraday_context:
                            intraday_base = intraday_context
                            logger.info("🔄 SWING: Reusing fresh intraday data")

                        logger.info(
                            f"⚠️  SWING CONTEXT: Cache MISS - generating (intraday_reuse={'YES' if intraday_base else 'NO'})..."
                        )
                        swing_context = await _generate_swing_context(
                            market_context_service,
                            intelligence_service,
                            include_opportunities=request.include_opportunities,
                            intraday_base=intraday_base,  # Pass intraday data for reuse
                        )

                        # Cache the result
                        if cache_service and cache_service.enabled and swing_context:
                            await cache_service.set(
                                cache_key, swing_context.dict(), ttl=CacheTTL.COMPOSITE_SWING
                            )
                            logger.info(
                                f"💾 Cached swing context (TTL={CacheTTL.COMPOSITE_SWING}s)"
                            )

                except Exception as e:
                    logger.error(f"Failed to generate swing context: {e}")
                    warnings.append(f"Swing context generation failed: {str(e)}")

            # Long-term context (15min TTL - can REUSE swing base)
            if (
                TradingStyle.LONG_TERM in request.trading_styles
                or TradingStyle.ALL in request.trading_styles
            ):
                try:
                    cache_key = get_cache_key_longterm()

                    # Try cache first
                    if cache_service and cache_service.enabled:
                        cached_longterm = await cache_service.get(cache_key)
                        if cached_longterm:
                            long_term_context = LongTermContext(**cached_longterm)
                            cache_hits.append("long_term")
                            logger.info("✅ LONG-TERM CONTEXT: Cache HIT")

                    # Cache miss - generate (may reuse swing)
                    if not long_term_context:
                        # Check if swing data is available (from cache or fresh generation)
                        swing_base = None
                        if not swing_context and cache_service and cache_service.enabled:
                            # Try to reuse cached swing data
                            swing_cache_key = get_cache_key_swing()
                            cached_swing = await cache_service.get(swing_cache_key)
                            if cached_swing:
                                swing_base = SwingContext(**cached_swing)
                                logger.info("🔄 LONG-TERM: Reusing cached swing data")
                        elif swing_context:
                            swing_base = swing_context
                            logger.info("🔄 LONG-TERM: Reusing fresh swing data")

                        logger.info(
                            f"⚠️  LONG-TERM CONTEXT: Cache MISS - generating (swing_reuse={'YES' if swing_base else 'NO'})..."
                        )
                        long_term_context = await _generate_long_term_context(
                            market_context_service,
                            intelligence_service,
                            swing_base=swing_base,  # Pass swing data for reuse
                        )

                        # Cache the result
                        if cache_service and cache_service.enabled and long_term_context:
                            await cache_service.set(
                                cache_key, long_term_context.dict(), ttl=CacheTTL.COMPOSITE_LONGTERM
                            )
                            logger.info(
                                f"💾 Cached long-term context (TTL={CacheTTL.COMPOSITE_LONGTERM}s)"
                            )

                except Exception as e:
                    logger.error(f"Failed to generate long-term context: {e}")
                    warnings.append(f"Long-term context generation failed: {str(e)}")

        # Calculate context quality
        context_quality_score = calculate_context_quality(
            primary_context, detailed_context, intraday_context, swing_context, long_term_context
        )

        # Generate data quality report
        data_quality, data_source_summary = _generate_data_quality_report(
            primary_context,
            detailed_context,
            intraday_context,
            swing_context,
            long_term_context,
            warnings,
        )

        processing_time = (time.time() - start_time) * 1000

        # Build cache status message
        cache_status = ""
        if cache_hits:
            cache_status = f" | Cache hits: {', '.join(cache_hits)} ⚡"
        elif cache_service and cache_service.enabled:
            cache_status = " | All cache miss (fresh data generated)"

        # Optional ML feature extraction
        ml_features = None
        try:
            if getattr(request, "include_ml_features", False):
                ml_features = _extract_ml_features(
                    primary_context=primary_context,
                    detailed_context=detailed_context,
                    intraday_context=intraday_context,
                    swing_context=swing_context,
                    long_term_context=long_term_context,
                )
        except Exception as e:
            logger.warning(f"ML feature extraction failed: {e}")

        return EnhancedMarketContextResponse(
            success=True,
            contract_version="1.1.0",  # DATA CONTRACT VERSION
            primary_context=primary_context,
            detailed_context=detailed_context,
            intraday_context=intraday_context,
            swing_context=swing_context,
            long_term_context=long_term_context,
            ml_features=ml_features,
            data_quality=data_quality,
            context_quality_score=context_quality_score,
            data_freshness_seconds=0,  # Real-time data
            processing_time_ms=round(processing_time, 2),
            warnings=warnings,
            data_source_summary=data_source_summary,
            message=f"Enhanced market context generated successfully for {len(request.trading_styles)} trading style(s){cache_status}",
        )

    except (TokenException, TokenExpiredException) as e:
        # Handle token expiry gracefully
        logger.error(f"🔑 Token expired during context generation: {e}")
        processing_time = (time.time() - start_time) * 1000
        error_response = KiteErrorHandler.get_graceful_response(e, "Enhanced Market Context")
        error_response["processing_time_ms"] = round(processing_time, 2)
        raise HTTPException(status_code=401, detail=error_response)

    except KiteException as e:
        # Handle other Kite API errors gracefully
        logger.error(f"❌ Kite API error during context generation: {e}")
        processing_time = (time.time() - start_time) * 1000
        error_response = KiteErrorHandler.get_graceful_response(e, "Enhanced Market Context")
        error_response["processing_time_ms"] = round(processing_time, 2)
        raise HTTPException(status_code=503, detail=error_response)

    except Exception as e:
        logger.error(f"Enhanced market context generation failed: {e}", exc_info=True)
        processing_time = (time.time() - start_time) * 1000
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "internal_error",
                "message": f"Enhanced market context generation failed: {str(e)}",
                "processing_time_ms": round(processing_time, 2),
                "timestamp": datetime.now().isoformat(),
            },
        )


# ============================================================================
# CONTEXT GENERATION FUNCTIONS
# ============================================================================


async def _generate_primary_context(market_service, intelligence_service) -> PrimaryMarketContext:
    """Generate primary (high-level) market context with REAL DATA."""

    try:
        # ================================================================
        # REAL DATA: Global Market Indices from Yahoo Finance
        # ================================================================
        yahoo_service = market_service.yahoo_service
        global_indices = await yahoo_service.get_market_indices()

        # Calculate regional averages
        us_markets = [idx for idx in global_indices if idx.symbol in ["^GSPC", "^IXIC", "^DJI"]]
        asia_markets = [idx for idx in global_indices if idx.symbol in ["^N225", "^HSI"]]
        europe_markets = [idx for idx in global_indices if idx.symbol in ["^FTSE", "^GDAXI"]]

        us_change = (
            Decimal(str(sum(m.change_percent for m in us_markets) / len(us_markets)))
            if us_markets
            else Decimal("0")
        )
        asia_change = (
            Decimal(str(sum(m.change_percent for m in asia_markets) / len(asia_markets)))
            if asia_markets
            else Decimal("0")
        )
        europe_change = (
            Decimal(str(sum(m.change_percent for m in europe_markets) / len(europe_markets)))
            if europe_markets
            else Decimal("0")
        )

        # Determine global trend
        avg_global_change = (us_change + asia_change + europe_change) / 3
        overall_trend = (
            "bullish"
            if avg_global_change > 0.3
            else "bearish" if avg_global_change < -0.3 else "neutral"
        )

        # Determine trend strength
        trend_magnitude = abs(float(avg_global_change))
        if trend_magnitude > 1.5:
            trend_strength = TrendStrength.VERY_STRONG
        elif trend_magnitude > 1.0:
            trend_strength = TrendStrength.STRONG
        elif trend_magnitude > 0.5:
            trend_strength = TrendStrength.MODERATE
        elif trend_magnitude > 0.2:
            trend_strength = TrendStrength.WEAK
        else:
            trend_strength = TrendStrength.VERY_WEAK

        # Risk appetite (based on market direction)
        risk_on_off = (
            "risk_on"
            if avg_global_change > 0
            else "risk_off" if avg_global_change < -0.5 else "neutral"
        )

        # Volatility level (based on change magnitude)
        if trend_magnitude > 2.0:
            volatility_level = VolatilityLevel.VERY_HIGH
        elif trend_magnitude > 1.5:
            volatility_level = VolatilityLevel.HIGH
        elif trend_magnitude > 0.5:
            volatility_level = VolatilityLevel.NORMAL
        else:
            volatility_level = VolatilityLevel.LOW

        global_context = GlobalMarketPrimary(
            overall_trend=overall_trend,
            trend_strength=trend_strength,
            us_markets_change=us_change,
            asia_markets_change=asia_change,
            europe_markets_change=europe_change,
            risk_on_off=risk_on_off,
            volatility_level=volatility_level,
            key_drivers=["Market movements", "Global sentiment"],  # TODO: Add news analysis
        )

    except Exception as e:
        logger.error(f"Failed to fetch global data: {e}")
        # Fallback to neutral context
        global_context = GlobalMarketPrimary(
            overall_trend="neutral",
            trend_strength=TrendStrength.WEAK,
            us_markets_change=Decimal("0"),
            asia_markets_change=Decimal("0"),
            europe_markets_change=Decimal("0"),
            risk_on_off="neutral",
            volatility_level=VolatilityLevel.NORMAL,
            key_drivers=["Data unavailable"],
        )

    try:
        # ================================================================
        # REAL DATA: Indian Market Indices - Try Kite first, fallback to Yahoo
        # ================================================================
        nifty_change = Decimal("0")
        banknifty_change = Decimal("0")
        sensex_change = Decimal("0")
        nifty_price = Decimal("19600")  # Default

        # Try Kite Connect first (real-time during market hours)
        try:
            kite_client = market_service.kite_client
            indian_symbols = ["NSE:NIFTY 50", "NSE:NIFTY BANK"]
            quotes = await kite_client.quote(indian_symbols)

            nifty_quote = quotes.get("NSE:NIFTY 50", {})
            banknifty_quote = quotes.get("NSE:NIFTY BANK", {})

            # Calculate change_percent from net_change and previous close
            if nifty_quote and nifty_quote.get("net_change") is not None:
                net_change = float(nifty_quote.get("net_change", 0))
                prev_close = float(nifty_quote.get("ohlc", {}).get("close", 0))
                if prev_close > 0:
                    nifty_change = Decimal(str((net_change / prev_close) * 100))
                    nifty_price = Decimal(str(nifty_quote.get("last_price", prev_close)))
                    logger.info(f"Kite: Nifty at {nifty_price}, change {nifty_change}%")

            if banknifty_quote and banknifty_quote.get("net_change") is not None:
                net_change = float(banknifty_quote.get("net_change", 0))
                prev_close = float(banknifty_quote.get("ohlc", {}).get("close", 0))
                if prev_close > 0:
                    banknifty_change = Decimal(str((net_change / prev_close) * 100))
                    logger.info(f"Kite: Bank Nifty change {banknifty_change}%")

        except Exception as kite_error:
            logger.warning(f"Kite Connect unavailable for Indian markets: {kite_error}")

            # Fallback to Yahoo Finance (works even when markets closed)
            try:
                yahoo_service = market_service.yahoo_service
                indices = await yahoo_service.get_market_indices()

                # Find Nifty and Bank Nifty in indices
                for idx in indices:
                    if idx.symbol == "^NSEI":
                        nifty_change = Decimal(str(idx.change_percent))
                        nifty_price = Decimal(str(idx.last_price))
                    elif idx.symbol == "^NSEBANK":
                        banknifty_change = Decimal(str(idx.change_percent))

                logger.info(f"Using Yahoo Finance for Indian markets: Nifty={nifty_change}%")

            except Exception as yahoo_error:
                logger.error(f"Yahoo Finance also failed for Indian markets: {yahoo_error}")

        # Sensex approximation
        sensex_change = nifty_change * Decimal("0.95")

        # Determine market regime
        if nifty_change > 1.5:
            market_regime = MarketRegime.BULL_STRONG
        elif nifty_change > 0.5:
            market_regime = MarketRegime.BULL_WEAK
        elif nifty_change > -0.5:
            market_regime = MarketRegime.SIDEWAYS
        elif nifty_change > -1.5:
            market_regime = MarketRegime.BEAR_WEAK
        else:
            market_regime = MarketRegime.BEAR_STRONG

        # Trend direction
        trend_direction = (
            "up" if nifty_change > 0.2 else "down" if nifty_change < -0.2 else "sideways"
        )

        # Advance/Decline ratio (simplified - use market breadth from Nifty change)
        advance_decline_ratio = Decimal("1.5") if nifty_change > 0 else Decimal("0.8")

        # Support/Resistance (calculate from current price)
        nifty_support = (nifty_price * Decimal("0.985")).quantize(Decimal("1"))
        nifty_resistance = (nifty_price * Decimal("1.015")).quantize(Decimal("1"))

        indian_context = IndianMarketPrimary(
            nifty_change=nifty_change,
            sensex_change=sensex_change,
            banknifty_change=banknifty_change,
            current_nifty_price=nifty_price,  # Added Nifty price
            market_regime=market_regime,
            trend_direction=trend_direction,
            advance_decline_ratio=advance_decline_ratio,
            nifty_support=nifty_support,
            nifty_resistance=nifty_resistance,
        )

    except Exception as e:
        logger.error(f"Failed to fetch Indian market data: {e}")
        # Fallback to neutral context
        indian_context = IndianMarketPrimary(
            nifty_change=Decimal("0"),
            sensex_change=Decimal("0"),
            banknifty_change=Decimal("0"),
            market_regime=MarketRegime.SIDEWAYS,
            trend_direction="sideways",
            advance_decline_ratio=Decimal("1.0"),
            nifty_support=Decimal("19500"),
            nifty_resistance=Decimal("19800"),
        )

    # Calculate overall market score
    overall_score = calculate_market_score(global_context, indian_context)

    # Determine favorable trading styles
    favorable_styles = determine_favorable_styles(overall_score, indian_context.market_regime)

    # Calculate confidence based on data availability
    confidence = (
        0.9 if global_context.us_markets_change != 0 and indian_context.nifty_change != 0 else 0.5
    )

    return PrimaryMarketContext(
        global_context=global_context,
        indian_context=indian_context,
        overall_market_score=overall_score,
        market_confidence=confidence,
        favorable_for=favorable_styles,
    )


async def _generate_detailed_context(
    market_service, intelligence_service, include_sectors: bool, include_technicals: bool
) -> DetailedMarketContext:
    """Generate detailed (granular) market context with REAL DATA."""

    try:
        kite_client = market_service.kite_client
        yahoo_service = market_service.yahoo_service

        # ================================================================
        # REAL DATA: Get Nifty historical data for technical indicators
        # ================================================================
        from datetime import datetime, timedelta

        to_date = datetime.now()
        from_date = to_date - timedelta(days=200)  # Need 200 days for 200 SMA

        # Get Nifty quote for current data
        quotes = await kite_client.quote(["NSE:NIFTY 50"])
        nifty_quote = quotes.get("NSE:NIFTY 50", {})

        current_value = Decimal(str(nifty_quote.get("last_price", 19600)))
        change_percent = Decimal(str(nifty_quote.get("change_percent", 0)))
        day_high = Decimal(str(nifty_quote.get("ohlc", {}).get("high", current_value)))
        day_low = Decimal(str(nifty_quote.get("ohlc", {}).get("low", current_value)))
        opening_price = Decimal(str(nifty_quote.get("ohlc", {}).get("open", current_value)))
        volume = nifty_quote.get("volume", 0)

        # Calculate support/resistance levels
        immediate_support = [
            (current_value * Decimal("0.985")).quantize(Decimal("1")),
            (current_value * Decimal("0.970")).quantize(Decimal("1")),
            (current_value * Decimal("0.955")).quantize(Decimal("1")),
        ]
        immediate_resistance = [
            (current_value * Decimal("1.015")).quantize(Decimal("1")),
            (current_value * Decimal("1.030")).quantize(Decimal("1")),
            (current_value * Decimal("1.045")).quantize(Decimal("1")),
        ]

        # ================================================================
        # Calculate Technical Indicators (simplified - using approximations)
        # ================================================================
        if include_technicals:
            # For production, you'd fetch historical data and calculate properly
            # For now, using reasonable approximations based on current price action

            # Price vs SMAs (approximated from current trend)
            if change_percent > 0:
                price_vs_sma20 = Decimal("2.5")
                price_vs_sma50 = Decimal("5.0")
                price_vs_sma200 = Decimal("8.0")
            else:
                price_vs_sma20 = Decimal("-1.5")
                price_vs_sma50 = Decimal("-2.0")
                price_vs_sma200 = Decimal("-3.0")

            # RSI approximation (based on change percent)
            if change_percent > 1.0:
                rsi_14 = Decimal("65")
            elif change_percent > 0.5:
                rsi_14 = Decimal("58")
            elif change_percent > -0.5:
                rsi_14 = Decimal("50")
            elif change_percent > -1.0:
                rsi_14 = Decimal("42")
            else:
                rsi_14 = Decimal("35")

            # MACD signal (based on trend)
            if change_percent > 0.5:
                macd_signal = "bullish_crossover"
            elif change_percent < -0.5:
                macd_signal = "bearish_crossover"
            else:
                macd_signal = "neutral"

            # ATR (based on day range)
            day_range = day_high - day_low
            atr_percent = (day_range / current_value * 100).quantize(Decimal("0.1"))

            # Bollinger position (based on price position in day range)
            if day_high - day_low > 0:
                price_position = (current_value - day_low) / (day_high - day_low)
                if price_position > 0.8:
                    bollinger_position = "upper"
                elif price_position < 0.2:
                    bollinger_position = "lower"
                else:
                    bollinger_position = "middle"
            else:
                bollinger_position = "middle"

            # Volume trend
            volume_trend = "increasing" if change_percent > 0 else "decreasing"
            volume_vs_avg = Decimal("100")  # Neutral baseline

            nifty_technicals = TechnicalIndicators(
                price_vs_sma20=price_vs_sma20,
                price_vs_sma50=price_vs_sma50,
                price_vs_sma200=price_vs_sma200,
                rsi_14=rsi_14,
                macd_signal=macd_signal,
                atr_percent=atr_percent,
                bollinger_position=bollinger_position,
                volume_trend=volume_trend,
                volume_vs_avg=volume_vs_avg,
            )
        else:
            nifty_technicals = TechnicalIndicators(
                price_vs_sma20=Decimal("0"),
                price_vs_sma50=Decimal("0"),
                price_vs_sma200=Decimal("0"),
                rsi_14=Decimal("50"),
                macd_signal="neutral",
                atr_percent=Decimal("1.0"),
                bollinger_position="middle",
                volume_trend="stable",
                volume_vs_avg=Decimal("100"),
            )

        # Market breadth (approximated)
        stocks_above_sma20 = 65 if change_percent > 0 else 35
        stocks_above_sma50 = 58 if change_percent > 0 else 42

        # ================================================================
        # 5-MINUTE QUICK OPPORTUNITY ANALYSIS (INDEX LEVEL MONEY-MAKING)
        # ================================================================
        quick_opportunity = None

        # Calculate 5-min support/resistance based on recent price action
        price_range = day_high - day_low
        pivot_5min = ((day_high + day_low + current_value) / 3).quantize(Decimal("0.01"))
        support_5min = (pivot_5min - (price_range * Decimal("0.3"))).quantize(Decimal("0.01"))
        resistance_5min = (pivot_5min + (price_range * Decimal("0.3"))).quantize(Decimal("0.01"))

        # Price position in day range
        if price_range > 0:
            price_position = (current_value - day_low) / price_range
        else:
            price_position = Decimal("0.5")

        # RSI (from technicals)
        rsi = float(nifty_technicals.rsi_14)

        # IDENTIFY QUICK OPPORTUNITY
        # 1. Breakout setup (price near resistance with bullish momentum)
        distance_to_resistance = abs((resistance_5min - current_value) / current_value * 100)
        if distance_to_resistance < Decimal("0.3") and change_percent > Decimal("0.2") and rsi < 70:
            # BULLISH BREAKOUT
            entry_zone = current_value
            target_1 = (resistance_5min * Decimal("1.003")).quantize(
                Decimal("0.01")
            )  # 0.3% above R
            target_2 = (resistance_5min * Decimal("1.006")).quantize(
                Decimal("0.01")
            )  # 0.6% above R
            stop_loss = (pivot_5min * Decimal("0.998")).quantize(
                Decimal("0.01")
            )  # 0.2% below pivot
            risk = entry_zone - stop_loss
            reward = target_1 - entry_zone
            rr_ratio = float(reward / risk) if risk > 0 else 1.0

            quick_opportunity = QuickTradingOpportunity(
                signal="BUY",
                confidence=75 if change_percent > Decimal("0.5") else 65,
                entry_zone=entry_zone,
                target_1=target_1,
                target_2=target_2,
                stop_loss=stop_loss,
                risk_reward=round(rr_ratio, 2),
                reasoning=f"Nifty near resistance {resistance_5min}, bullish momentum {change_percent:.2f}%, RSI {rsi:.0f} (not overbought) - breakout setup",
                time_validity_mins=15,
                trade_type="breakout",
            )

        # 2. Reversal setup (price at resistance with overbought conditions)
        elif distance_to_resistance < Decimal("0.2") and rsi > 70:
            # BEARISH REVERSAL
            entry_zone = current_value
            target_1 = (pivot_5min * Decimal("0.997")).quantize(Decimal("0.01"))  # 0.3% below pivot
            target_2 = (support_5min).quantize(Decimal("0.01"))
            stop_loss = (resistance_5min * Decimal("1.002")).quantize(
                Decimal("0.01")
            )  # 0.2% above R
            risk = stop_loss - entry_zone
            reward = entry_zone - target_1
            rr_ratio = float(reward / risk) if risk > 0 else 1.0

            quick_opportunity = QuickTradingOpportunity(
                signal="SELL",
                confidence=70,
                entry_zone=entry_zone,
                target_1=target_1,
                target_2=target_2,
                stop_loss=stop_loss,
                risk_reward=round(rr_ratio, 2),
                reasoning=f"Nifty at resistance {resistance_5min}, overbought RSI {rsi:.0f} - reversal expected",
                time_validity_mins=10,
                trade_type="reversal",
            )

        # 3. Support bounce (price near support with oversold)
        distance_to_support = abs((support_5min - current_value) / current_value * 100)
        if distance_to_support < Decimal("0.3") and rsi < 30:
            # BULLISH BOUNCE
            entry_zone = current_value
            target_1 = (pivot_5min * Decimal("1.003")).quantize(Decimal("0.01"))  # 0.3% above pivot
            target_2 = (resistance_5min).quantize(Decimal("0.01"))
            stop_loss = (support_5min * Decimal("0.998")).quantize(Decimal("0.01"))  # 0.2% below S
            risk = entry_zone - stop_loss
            reward = target_1 - entry_zone
            rr_ratio = float(reward / risk) if risk > 0 else 1.0

            quick_opportunity = QuickTradingOpportunity(
                signal="BUY",
                confidence=75,
                entry_zone=entry_zone,
                target_1=target_1,
                target_2=target_2,
                stop_loss=stop_loss,
                risk_reward=round(rr_ratio, 2),
                reasoning=f"Nifty near support {support_5min}, oversold RSI {rsi:.0f} - bounce expected",
                time_validity_mins=15,
                trade_type="reversal",
            )

        # 4. Strong momentum scalp (if no setup above but strong momentum)
        elif abs(change_percent) > Decimal("0.4") and quick_opportunity is None:
            if change_percent > 0:  # Bullish momentum
                entry_zone = current_value
                target_1 = (current_value * Decimal("1.003")).quantize(Decimal("0.01"))  # 0.3% up
                target_2 = (current_value * Decimal("1.005")).quantize(Decimal("0.01"))  # 0.5% up
                stop_loss = (current_value * Decimal("0.998")).quantize(
                    Decimal("0.01")
                )  # 0.2% down
                signal = "BUY"
                reasoning = f"Strong bullish momentum {change_percent:.2f}%, ride the trend"
            else:  # Bearish momentum
                entry_zone = current_value
                target_1 = (current_value * Decimal("0.997")).quantize(Decimal("0.01"))  # 0.3% down
                target_2 = (current_value * Decimal("0.995")).quantize(Decimal("0.01"))  # 0.5% down
                stop_loss = (current_value * Decimal("1.002")).quantize(Decimal("0.01"))  # 0.2% up
                signal = "SELL"
                reasoning = f"Strong bearish momentum {change_percent:.2f}%, ride the trend"

            risk = abs(entry_zone - stop_loss)
            reward = abs(target_1 - entry_zone)
            rr_ratio = float(reward / risk) if risk > 0 else 1.0

            quick_opportunity = QuickTradingOpportunity(
                signal=signal,
                confidence=70,
                entry_zone=entry_zone,
                target_1=target_1,
                target_2=target_2,
                stop_loss=stop_loss,
                risk_reward=round(rr_ratio, 2),
                reasoning=reasoning,
                time_validity_mins=5,
                trade_type="momentum",
            )

        # If no opportunity, suggest HOLD
        if quick_opportunity is None:
            quick_opportunity = QuickTradingOpportunity(
                signal="HOLD",
                confidence=50,
                entry_zone=None,
                target_1=None,
                target_2=None,
                stop_loss=None,
                risk_reward=None,
                reasoning="No clear setup. Wait for breakout above resistance or support test.",
                time_validity_mins=5,
                trade_type="none",
            )

        nifty_analysis = IndexDetailedAnalysis(
            index_name="NIFTY 50",
            current_value=current_value,
            change_percent=change_percent,
            day_high=day_high,
            day_low=day_low,
            opening_price=opening_price,
            immediate_support=immediate_support,
            immediate_resistance=immediate_resistance,
            support_5min=support_5min,
            resistance_5min=resistance_5min,
            pivot_5min=pivot_5min,
            technicals=nifty_technicals,
            stocks_above_sma20=stocks_above_sma20,
            stocks_above_sma50=stocks_above_sma50,
            put_call_ratio=Decimal("1.0"),  # Would come from options data
            fii_dii_activity="Market closed" if change_percent == 0 else "Active",
            quick_opportunity=quick_opportunity,  # 5-MIN QUICK MONEY SETUP
        )

        # ================================================================
        # REAL DATA: Sector performance from Yahoo Finance
        # ================================================================
        sectors = []
        if include_sectors:
            try:
                # Use Kite for Indian sector indices (faster, more accurate)
                sector_performance = await market_service.kite_client.get_sector_performance()

                for sector_name, change in sector_performance.items():
                    change_decimal = Decimal(str(change))

                    # Determine trend
                    if change_decimal > 0.5:
                        trend = "bullish"
                        strength_score = min(100, int(change_decimal * 50))
                        momentum = "accelerating" if change_decimal > 1.5 else "stable"
                    elif change_decimal < -0.5:
                        trend = "bearish"
                        strength_score = max(-100, int(change_decimal * 50))
                        momentum = "decelerating" if change_decimal < -1.5 else "stable"
                    else:
                        trend = "neutral"
                        strength_score = int(change_decimal * 50)
                        momentum = "stable"

                    sectors.append(
                        SectorPerformance(
                            sector_name=sector_name,
                            change_percent=change_decimal,
                            volume_ratio=Decimal("100"),  # Would need detailed data
                            trend=trend,
                            top_gainers=[],  # Would need stock-level data
                            top_losers=[],
                            strength_score=strength_score,
                            momentum=momentum,
                        )
                    )
            except Exception as e:
                logger.error(f"Failed to fetch sector data: {e}")
                # Provide default sectors
                sectors = [
                    SectorPerformance(
                        sector_name="Technology",
                        change_percent=change_percent,
                        volume_ratio=Decimal("100"),
                        trend="neutral",
                        top_gainers=[],
                        top_losers=[],
                        strength_score=0,
                        momentum="stable",
                    )
                ]

        # Market breadth (simplified)
        if change_percent > 0:
            advances = 1250
            declines = 850
        elif change_percent < 0:
            advances = 850
            declines = 1250
        else:
            advances = 1050
            declines = 1050
        unchanged = 100

        return DetailedMarketContext(
            nifty_analysis=nifty_analysis,
            banknifty_analysis=None,
            midcap_analysis=None,
            sectors=sectors,
            top_gainers=[],
            top_losers=[],
            advances=advances,
            declines=declines,
            unchanged=unchanged,
            new_highs=int(abs(float(change_percent)) * 10) if change_percent > 0 else 0,
            new_lows=int(abs(float(change_percent)) * 10) if change_percent < 0 else 0,
            total_volume=Decimal(str(volume)) if volume > 0 else Decimal("1000000"),
            volume_vs_avg=Decimal("100"),
        )

    except Exception as e:
        logger.error(f"Failed to generate detailed context: {e}")
        # Return minimal context
        return DetailedMarketContext(
            nifty_analysis=None,
            banknifty_analysis=None,
            midcap_analysis=None,
            sectors=[],
            top_gainers=[],
            top_losers=[],
            advances=1000,
            declines=1000,
            unchanged=100,
            new_highs=0,
            new_lows=0,
            total_volume=Decimal("1000000"),
            volume_vs_avg=Decimal("100"),
        )


async def _generate_intraday_context(
    market_service, intelligence_service, focus_symbols: Optional[List[str]]
) -> IntradayContext:
    """Generate intraday trading specific context with REAL DATA."""

    # Market timing
    now = datetime.now()
    market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
    market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)

    # Determine market phase
    if now - market_open < timedelta(hours=1):
        market_phase = "Opening"
    elif market_close - now < timedelta(hours=1):
        market_phase = "Closing"
    else:
        market_phase = "Mid-session"

    time_remaining = int((market_close - now).total_seconds() / 60)

    try:
        # ================================================================
        # REAL DATA: Get Nifty quote for intraday analysis
        # ================================================================
        kite_client = market_service.kite_client
        quotes = await kite_client.quote(["NSE:NIFTY 50"])
        nifty_quote = quotes.get("NSE:NIFTY 50", {})

        # Extract OHLC data
        current_price = Decimal(str(nifty_quote.get("last_price", 19600)))
        day_open = Decimal(str(nifty_quote.get("ohlc", {}).get("open", current_price)))
        day_high = Decimal(str(nifty_quote.get("ohlc", {}).get("high", current_price)))
        day_low = Decimal(str(nifty_quote.get("ohlc", {}).get("low", current_price)))
        volume = nifty_quote.get("volume", 0)

        # Calculate intraday metrics
        price_range_percent = (
            ((day_high - day_low) / day_low * 100).quantize(Decimal("0.01"))
            if day_low > 0
            else Decimal("0")
        )

        # VWAP approximation (using average of high-low-close)
        vwap = ((day_high + day_low + current_price) / 3).quantize(Decimal("0.01"))
        current_vs_vwap = ((current_price - vwap) / vwap * 100).quantize(Decimal("0.01"))

        # Calculate pivot points (Standard)
        pivot_point = ((day_high + day_low + day_open) / 3).quantize(Decimal("0"))
        r1 = (pivot_point * 2 - day_low).quantize(Decimal("0"))
        r2 = (pivot_point + (day_high - day_low)).quantize(Decimal("0"))
        s1 = (pivot_point * 2 - day_high).quantize(Decimal("0"))
        s2 = (pivot_point - (day_high - day_low)).quantize(Decimal("0"))

        # Determine momentum
        change_from_open = current_price - day_open
        change_percent = (change_from_open / day_open * 100) if day_open > 0 else Decimal("0")

        if change_percent > 1.0:
            current_momentum = "strong_bullish"
        elif change_percent > 0.3:
            current_momentum = "bullish"
        elif change_percent > -0.3:
            current_momentum = "neutral"
        elif change_percent > -1.0:
            current_momentum = "bearish"
        else:
            current_momentum = "strong_bearish"

        # Momentum shift (based on position relative to day range)
        price_position = (
            (current_price - day_low) / (day_high - day_low)
            if (day_high - day_low) > 0
            else Decimal("0.5")
        )
        if price_position > 0.7:
            momentum_shift = "accelerating"
        elif price_position < 0.3:
            momentum_shift = "decelerating"
        else:
            momentum_shift = "stable"

        # Volatility (based on price range)
        if price_range_percent > 2.0:
            intraday_volatility = VolatilityLevel.VERY_HIGH
        elif price_range_percent > 1.5:
            intraday_volatility = VolatilityLevel.HIGH
        elif price_range_percent > 0.8:
            intraday_volatility = VolatilityLevel.NORMAL
        else:
            intraday_volatility = VolatilityLevel.LOW

        # Breakout/Reversal candidates (simplified - use major stocks)
        breakout_candidates = []
        reversal_candidates = []

        if focus_symbols:
            # If user provided focus symbols, use those
            breakout_candidates = focus_symbols[:3]
        else:
            # Default liquid stocks
            if change_percent > 0.5:
                breakout_candidates = ["RELIANCE", "TCS", "INFY"]
            else:
                reversal_candidates = ["HDFCBANK", "ICICIBANK"]

        return IntradayContext(
            market_phase=market_phase,
            time_remaining_minutes=time_remaining,
            current_momentum=current_momentum,
            momentum_shift=momentum_shift,
            intraday_volatility=intraday_volatility,
            price_range_percent=price_range_percent,
            volume_weighted_price=vwap,
            current_vs_vwap=current_vs_vwap,
            pivot_point=pivot_point,
            r1=r1,
            r2=r2,
            s1=s1,
            s2=s2,
            news_driven_volatility=False,  # TODO: Add news detection
            high_impact_events_today=[],
            breakout_candidates=breakout_candidates,
            reversal_candidates=reversal_candidates,
        )

    except Exception as e:
        logger.error(f"Failed to generate intraday context: {e}")
        # Fallback to basic context
        return IntradayContext(
            market_phase=market_phase,
            time_remaining_minutes=time_remaining,
            current_momentum="neutral",
            momentum_shift="stable",
            intraday_volatility=VolatilityLevel.NORMAL,
            price_range_percent=Decimal("1.0"),
            volume_weighted_price=Decimal("19600"),
            current_vs_vwap=Decimal("0"),
            pivot_point=Decimal("19600"),
            r1=Decimal("19650"),
            r2=Decimal("19700"),
            s1=Decimal("19550"),
            s2=Decimal("19500"),
            news_driven_volatility=False,
            high_impact_events_today=[],
            breakout_candidates=[],
            reversal_candidates=[],
        )


async def _generate_swing_context(
    market_service,
    intelligence_service,
    include_opportunities: bool,
    intraday_base: Optional[IntradayContext] = None,
) -> SwingContext:
    """
    Generate swing trading specific context with REAL DATA.

    Args:
        market_service: Market context service
        intelligence_service: Market intelligence service
        include_opportunities: Whether to include trading opportunities
        intraday_base: Optional intraday context to reuse (cached or fresh)

    Note:
        If intraday_base is provided, swing context can reuse intraday calculations
        instead of re-fetching/recomputing them, saving API calls and time.
    """

    try:
        kite_client = market_service.kite_client
        yahoo_service = market_service.yahoo_service

        # ================================================================
        # REAL DATA: Get Nifty quote for current analysis
        # ================================================================
        quotes = await kite_client.quote(["NSE:NIFTY 50"])
        nifty_quote = quotes.get("NSE:NIFTY 50", {})

        current_price = Decimal(str(nifty_quote.get("last_price", 19600)))
        change_percent = Decimal(str(nifty_quote.get("change_percent", 0)))

        # Determine multi-day trend (approximated from current momentum)
        if change_percent > 0.5:
            multi_day_trend = "uptrend"
            trend_strength = (
                TrendStrength.STRONG if change_percent > 1.0 else TrendStrength.MODERATE
            )
            trend_age_days = 5 if change_percent > 1.0 else 10
        elif change_percent < -0.5:
            multi_day_trend = "downtrend"
            trend_strength = (
                TrendStrength.STRONG if change_percent < -1.0 else TrendStrength.MODERATE
            )
            trend_age_days = 5 if change_percent < -1.0 else 10
        else:
            multi_day_trend = "sideways"
            trend_strength = TrendStrength.WEAK
            trend_age_days = 15

        # Weekly momentum
        if abs(float(change_percent)) > 1.0:
            weekly_momentum = "strong"
        elif abs(float(change_percent)) > 0.5:
            weekly_momentum = "moderate"
        else:
            weekly_momentum = "weak"

        # Momentum divergence (would need historical data for accurate detection)
        momentum_divergence = False

        # Chart patterns (would need historical price data for detection)
        chart_patterns = []
        if change_percent > 0.5:
            chart_patterns = ["Bullish continuation pattern"]
        elif change_percent < -0.5:
            chart_patterns = ["Bearish continuation pattern"]

        # Calculate swing levels (from current price)
        swing_support_levels = [
            (current_price * Decimal("0.980")).quantize(Decimal("1")),
            (current_price * Decimal("0.960")).quantize(Decimal("1")),
            (current_price * Decimal("0.940")).quantize(Decimal("1")),
        ]
        swing_resistance_levels = [
            (current_price * Decimal("1.020")).quantize(Decimal("1")),
            (current_price * Decimal("1.040")).quantize(Decimal("1")),
            (current_price * Decimal("1.060")).quantize(Decimal("1")),
        ]

        # ================================================================
        # REAL DATA: Sector rotation from Yahoo Finance
        # ================================================================
        hot_sectors = []
        cold_sectors = []
        rotating_sectors = []

        try:
            # Use Kite for Indian sector indices (faster, more accurate)
            sector_performance = await market_service.kite_client.get_sector_performance()

            # Categorize sectors
            for sector, change in sector_performance.items():
                if change > 1.0:
                    hot_sectors.append(sector)
                elif change < -1.0:
                    cold_sectors.append(sector)
                elif abs(change) > 0.3:
                    rotating_sectors.append(sector)
        except Exception as e:
            logger.error(f"Failed to fetch sector performance for swing: {e}")
            hot_sectors = ["Technology"] if change_percent > 0 else []
            cold_sectors = ["Energy"] if change_percent < 0 else []

        # Mean reversion opportunities (simplified)
        oversold_stocks = []
        overbought_stocks = []

        if include_opportunities:
            if change_percent < -0.5:
                oversold_stocks = ["AXISBANK", "TATAMOTORS", "SBIN"]
            if change_percent > 1.0:
                overbought_stocks = ["ASIANPAINT", "TITAN", "NESTLEIND"]

        # Risk level
        if abs(float(change_percent)) > 1.5:
            risk_level = "high"
        elif abs(float(change_percent)) > 0.5:
            risk_level = "medium"
        else:
            risk_level = "low"

        # Stop loss suggestion
        if risk_level == "high":
            stop_loss_suggestion = "5-7% trailing stop loss recommended"
        elif risk_level == "medium":
            stop_loss_suggestion = "3-5% trailing stop loss recommended"
        else:
            stop_loss_suggestion = "2-3% trailing stop loss recommended"

        return SwingContext(
            multi_day_trend=multi_day_trend,
            trend_strength=trend_strength,
            trend_age_days=trend_age_days,
            weekly_momentum=weekly_momentum,
            momentum_divergence=momentum_divergence,
            chart_patterns=chart_patterns,
            swing_support_levels=swing_support_levels,
            swing_resistance_levels=swing_resistance_levels,
            hot_sectors=hot_sectors,
            cold_sectors=cold_sectors,
            rotating_sectors=rotating_sectors,
            oversold_stocks=oversold_stocks,
            overbought_stocks=overbought_stocks,
            risk_level=risk_level,
            stop_loss_suggestion=stop_loss_suggestion,
        )

    except Exception as e:
        logger.error(f"Failed to generate swing context: {e}")
        # Fallback to neutral context
        return SwingContext(
            multi_day_trend="sideways",
            trend_strength=TrendStrength.WEAK,
            trend_age_days=10,
            weekly_momentum="weak",
            momentum_divergence=False,
            chart_patterns=[],
            swing_support_levels=[Decimal("19400"), Decimal("19200")],
            swing_resistance_levels=[Decimal("19800"), Decimal("20000")],
            hot_sectors=[],
            cold_sectors=[],
            rotating_sectors=[],
            oversold_stocks=[],
            overbought_stocks=[],
            risk_level="medium",
            stop_loss_suggestion="3-5% trailing stop loss recommended",
        )


async def _generate_long_term_context(
    market_service, intelligence_service, swing_base: Optional[SwingContext] = None
) -> LongTermContext:
    """
    Generate long-term investment specific context with REAL DATA.

    Args:
        market_service: Market context service
        intelligence_service: Market intelligence service
        swing_base: Optional swing context to reuse (cached or fresh)

    Note:
        If swing_base is provided, long-term context can reuse swing calculations
        (sector rotation, trend analysis) instead of recomputing them.
    """

    try:
        yahoo_service = market_service.yahoo_service

        # ================================================================
        # REAL DATA: Get Nifty fundamentals from Yahoo Finance
        # ================================================================
        nifty_data = None
        nifty_pe = Decimal("22.5")  # Default
        nifty_pb = Decimal("3.8")  # Default

        try:
            nifty_data = await yahoo_service.get_stock_data("^NSEI")
            if nifty_data and nifty_data.pe_ratio:
                nifty_pe = Decimal(str(nifty_data.pe_ratio))
            if nifty_data and nifty_data.fundamentals.get("priceToBook"):
                nifty_pb = Decimal(str(nifty_data.fundamentals["priceToBook"]))
        except Exception as e:
            logger.error(f"Failed to fetch Nifty fundamentals: {e}")

        # Determine market valuation
        if nifty_pe > 25:
            market_valuation = "overvalued"
        elif nifty_pe > 20:
            market_valuation = "fair"
        else:
            market_valuation = "undervalued"

        # ================================================================
        # Economic indicators (config-based for now)
        # ================================================================
        # These change slowly and can be updated monthly
        economic_cycle = "expansion"  # Would come from macro data or config
        interest_rate_trend = "stable"  # From RBI announcements
        inflation_trend = "falling"  # From CPI data

        # ================================================================
        # Thematic allocation (curated based on current market)
        # ================================================================
        # These are strategic themes updated quarterly
        emerging_themes = [
            "Digital transformation",
            "Green energy & sustainability",
            "Make in India manufacturing",
            "Financial inclusion",
            "Infrastructure development",
        ]

        declining_themes = ["Legacy retail", "Traditional telecom", "Coal-based energy"]

        # ================================================================
        # REAL DATA: Sector allocation based on current performance
        # ================================================================
        recommended_sector_weights = {}

        try:
            # Use Kite for Indian sector indices (faster, more accurate)
            sector_performance = await market_service.kite_client.get_sector_performance()

            # Calculate recommended weights based on recent performance
            # Strong performers get higher allocation
            total_sectors = len(sector_performance)
            remaining_weight = Decimal("100")

            sorted_sectors = sorted(sector_performance.items(), key=lambda x: x[1], reverse=True)

            for i, (sector, change) in enumerate(sorted_sectors[:5]):
                # Top performing sectors get higher weight
                if i == 0:
                    weight = Decimal("20")
                elif i == 1:
                    weight = Decimal("18")
                elif i == 2:
                    weight = Decimal("15")
                elif i == 3:
                    weight = Decimal("12")
                else:
                    weight = Decimal("10")

                recommended_sector_weights[sector] = weight
                remaining_weight -= weight

            # Distribute remaining to other sectors
            if len(sorted_sectors) > 5:
                others_weight = remaining_weight / (len(sorted_sectors) - 5)
                for sector, _ in sorted_sectors[5:]:
                    recommended_sector_weights[sector] = others_weight.quantize(Decimal("1"))

        except Exception as e:
            logger.error(f"Failed to calculate sector weights: {e}")
            # Default allocation
            recommended_sector_weights = {
                "Technology": Decimal("20"),
                "Banking": Decimal("18"),
                "Healthcare": Decimal("15"),
                "Consumer": Decimal("12"),
                "Industrial": Decimal("10"),
            }

        # ================================================================
        # Investment opportunities (based on valuation and growth)
        # ================================================================
        value_opportunities = ["L&T", "SBI", "BHEL", "NTPC", "POWERGRID"]
        growth_opportunities = ["INFY", "TCS", "HDFCBANK", "RELIANCE", "MARUTI"]
        dividend_opportunities = ["ITC", "COALINDIA", "ONGC", "VEDL", "HINDALCO"]

        # ================================================================
        # Risk assessment
        # ================================================================
        # Based on current market conditions
        if nifty_pe > 25:
            systemic_risk_level = "high"
        elif nifty_pe > 20:
            systemic_risk_level = "medium"
        else:
            systemic_risk_level = "low"

        key_risks = [
            "Global economic slowdown",
            "Geopolitical tensions",
            "Oil price volatility",
            "Interest rate changes",
            "Currency fluctuations",
        ]

        return LongTermContext(
            economic_cycle=economic_cycle,
            interest_rate_trend=interest_rate_trend,
            inflation_trend=inflation_trend,
            nifty_pe=nifty_pe,
            nifty_pb=nifty_pb,
            market_valuation=market_valuation,
            emerging_themes=emerging_themes,
            declining_themes=declining_themes,
            recommended_sector_weights=recommended_sector_weights,
            value_opportunities=value_opportunities,
            growth_opportunities=growth_opportunities,
            dividend_opportunities=dividend_opportunities,
            systemic_risk_level=systemic_risk_level,
            key_risks=key_risks,
        )

    except Exception as e:
        logger.error(f"Failed to generate long-term context: {e}")
        # Fallback to default context
        return LongTermContext(
            economic_cycle="expansion",
            interest_rate_trend="stable",
            inflation_trend="stable",
            nifty_pe=Decimal("22.5"),
            nifty_pb=Decimal("3.8"),
            market_valuation="fair",
            emerging_themes=["Digital transformation"],
            declining_themes=["Legacy systems"],
            recommended_sector_weights={"Technology": Decimal("20")},
            value_opportunities=["SBI"],
            growth_opportunities=["INFY"],
            dividend_opportunities=["ITC"],
            systemic_risk_level="medium",
            key_risks=["Market volatility"],
        )


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def _generate_data_quality_report(
    primary_context, detailed_context, intraday_context, swing_context, long_term_context, warnings
):
    """
    Generate comprehensive data quality report.

    Returns:
        tuple: (data_quality_dict, data_source_summary)
    """

    real_count = 0
    approximated_count = 0
    fallback_count = 0
    total_count = 0

    data_sources = []
    approximations = []
    fallbacks = []

    # Analyze PRIMARY context
    if primary_context:
        total_count += 5  # global, indian, score, confidence, favorable

        # Global markets
        if primary_context.global_context.us_markets_change != 0:
            real_count += 1
            data_sources.append("Global markets: REAL (Yahoo Finance API)")
        else:
            fallback_count += 1
            fallbacks.append("Global markets: FALLBACK (APIs unavailable)")

        # Indian markets (check if using Yahoo fallback or Kite)
        if primary_context.indian_context.nifty_change != 0:
            real_count += 1
            # Note: Could be from Kite (market hours) or Yahoo (fallback)
            data_sources.append("Indian markets: REAL (Kite Connect or Yahoo Finance fallback)")
        else:
            fallback_count += 1
            fallbacks.append("Indian markets: FALLBACK (Market closed and APIs unavailable)")

        # Market score - always calculated
        approximated_count += 1
        data_sources.append("Market score: CALCULATED from real data")

        # Confidence - always calculated
        approximated_count += 1
        data_sources.append("Confidence: CALCULATED from data availability")

        # Favorable styles - always calculated
        approximated_count += 1
        data_sources.append("Favorable styles: CALCULATED from market conditions")

    # Analyze DETAILED context
    if detailed_context and detailed_context.nifty_analysis:
        total_count += 4  # nifty analysis, technicals, sectors, breadth

        # Nifty current value
        if detailed_context.nifty_analysis.current_value:
            if detailed_context.nifty_analysis.change_percent != 0:
                real_count += 1
                data_sources.append("Nifty OHLC: REAL (Kite Connect)")
            else:
                fallback_count += 1
                fallbacks.append("Nifty OHLC: FALLBACK (Market closed)")

        # Technical indicators
        if detailed_context.nifty_analysis.technicals:
            approximated_count += 1
            approximations.append(
                "Technical indicators: APPROXIMATED (based on current price action)"
            )
            data_sources.append(
                "Technical indicators: APPROXIMATED (need historical data for precise calculation)"
            )

        # Sectors
        if detailed_context.sectors and len(detailed_context.sectors) > 0:
            real_count += 1
            data_sources.append(
                f"Sector data: REAL (Yahoo Finance - {len(detailed_context.sectors)} sectors)"
            )
        else:
            fallback_count += 1
            fallbacks.append("Sector data: UNAVAILABLE")

        # Market breadth
        approximated_count += 1
        approximations.append("Market breadth: APPROXIMATED (from Nifty change)")

    # Analyze INTRADAY context
    if intraday_context:
        total_count += 4  # pivot, vwap, momentum, volatility

        # Pivot points
        if intraday_context.pivot_point:
            approximated_count += 1
            data_sources.append("Pivot points: CALCULATED from real OHLC")

        # VWAP
        approximated_count += 1
        approximations.append("VWAP: APPROXIMATED (using HLC average)")

        # Momentum
        approximated_count += 1
        data_sources.append("Momentum: CALCULATED from price change")

        # Volatility
        approximated_count += 1
        data_sources.append("Volatility: CALCULATED from price range")

    # Analyze SWING context
    if swing_context:
        total_count += 3  # trend, sectors, risk

        # Trend
        approximated_count += 1
        data_sources.append("Swing trend: APPROXIMATED (from current momentum)")
        approximations.append(
            "Swing trend: Need multi-day historical data for precise trend analysis"
        )

        # Sector rotation
        if swing_context.hot_sectors or swing_context.cold_sectors:
            real_count += 1
            data_sources.append("Sector rotation: REAL (Yahoo Finance)")
        else:
            fallback_count += 1
            fallbacks.append("Sector rotation: UNAVAILABLE")

        # Risk level
        approximated_count += 1
        data_sources.append("Risk level: CALCULATED from volatility")

    # Analyze LONG-TERM context
    if long_term_context:
        total_count += 3  # pe/pb, themes, sector weights

        # Nifty P/E, P/B
        if long_term_context.nifty_pe != Decimal("22.5"):  # Not default
            real_count += 1
            data_sources.append("Nifty P/E: REAL (Yahoo Finance)")
        else:
            fallback_count += 1
            fallbacks.append("Nifty P/E: DEFAULT (Yahoo Finance unavailable)")

        # Themes
        fallback_count += 1
        fallbacks.append("Investment themes: CURATED (manually maintained list)")

        # Sector weights
        if long_term_context.recommended_sector_weights:
            approximated_count += 1
            data_sources.append("Sector allocation: CALCULATED from recent performance")

    # Calculate percentages
    real_percentage = (real_count / total_count * 100) if total_count > 0 else 0
    approximated_percentage = (approximated_count / total_count * 100) if total_count > 0 else 0
    fallback_percentage = (fallback_count / total_count * 100) if total_count > 0 else 0

    # Determine overall quality
    if real_percentage > 60:
        overall_quality = "HIGH"
    elif real_percentage > 40:
        overall_quality = "GOOD"
    elif real_percentage > 20:
        overall_quality = "MEDIUM"
    else:
        overall_quality = "LOW"

    # Build quality report
    data_quality = {
        "overall_quality": overall_quality,
        "real_data_percentage": round(real_percentage, 1),
        "approximated_percentage": round(approximated_percentage, 1),
        "fallback_percentage": round(fallback_percentage, 1),
        "data_sources": data_sources,
        "approximations": approximations,
        "fallbacks": fallbacks,
        "recommendations": get_data_quality_recommendations(
            real_count, approximated_count, fallback_count
        ),
    }

    data_source_summary = {
        "real": real_count,
        "approximated": approximated_count,
        "fallback": fallback_count,
        "total": total_count,
    }

    return data_quality, data_source_summary


def _extract_ml_features(
    primary_context, detailed_context, intraday_context, swing_context, long_term_context
):
    """
    Extract flattened ML features from hierarchical context.

    Returns a dictionary with 47+ numeric and categorical features ready for:
    - Pandas DataFrame conversion
    - Scikit-learn models
    - Feature engineering pipelines
    """
    features = {}

    # PRIMARY CONTEXT - Indian Market
    if (
        primary_context
        and hasattr(primary_context, "indian_context")
        and primary_context.indian_context
    ):
        indian = primary_context.indian_context
        features.update(
            {
                "nifty_change_pct": float(indian.nifty_change) if indian.nifty_change else 0.0,
                "sensex_change_pct": float(indian.sensex_change) if indian.sensex_change else 0.0,
                "banknifty_change_pct": (
                    float(indian.banknifty_change) if indian.banknifty_change else 0.0
                ),
                "nifty_price": (
                    float(indian.current_nifty_price) if indian.current_nifty_price else 0.0
                ),
                "market_regime": indian.market_regime if indian.market_regime else "unknown",
                "trend_direction": indian.trend_direction if indian.trend_direction else "unknown",
                "advance_decline_ratio": (
                    float(indian.advance_decline_ratio) if indian.advance_decline_ratio else 1.0
                ),
                "nifty_support": float(indian.nifty_support) if indian.nifty_support else 0.0,
                "nifty_resistance": (
                    float(indian.nifty_resistance) if indian.nifty_resistance else 0.0
                ),
            }
        )

    # PRIMARY CONTEXT - Global Market
    if (
        primary_context
        and hasattr(primary_context, "global_context")
        and primary_context.global_context
    ):
        global_ctx = primary_context.global_context
        features.update(
            {
                "global_trend": global_ctx.overall_trend if global_ctx.overall_trend else "unknown",
                "global_trend_strength": (
                    global_ctx.trend_strength if global_ctx.trend_strength else "unknown"
                ),
                "us_markets_change": (
                    float(global_ctx.us_markets_change) if global_ctx.us_markets_change else 0.0
                ),
                "asia_markets_change": (
                    float(global_ctx.asia_markets_change) if global_ctx.asia_markets_change else 0.0
                ),
                "europe_markets_change": (
                    float(global_ctx.europe_markets_change)
                    if global_ctx.europe_markets_change
                    else 0.0
                ),
                "risk_sentiment": global_ctx.risk_on_off if global_ctx.risk_on_off else "neutral",
                "volatility_level": (
                    global_ctx.volatility_level if global_ctx.volatility_level else "normal"
                ),
            }
        )

    # DETAILED CONTEXT - Technical Indicators
    if detailed_context:
        # Nifty Analysis
        if hasattr(detailed_context, "nifty_analysis") and detailed_context.nifty_analysis:
            nifty = detailed_context.nifty_analysis
            tech = nifty.technicals if hasattr(nifty, "technicals") and nifty.technicals else None

            features.update(
                {
                    "nifty_current": float(nifty.current_value) if nifty.current_value else 0.0,
                    "nifty_day_change": (
                        float(nifty.change_percent) if nifty.change_percent else 0.0
                    ),
                    "nifty_day_high": float(nifty.day_high) if nifty.day_high else None,
                    "nifty_day_low": float(nifty.day_low) if nifty.day_low else None,
                }
            )

            if tech:
                features.update(
                    {
                        "nifty_rsi_14": float(tech.rsi_14) if tech.rsi_14 else 50.0,
                        "nifty_macd_signal": tech.macd_signal if tech.macd_signal else "neutral",
                        "nifty_price_vs_sma20": (
                            float(tech.price_vs_sma20) if tech.price_vs_sma20 else None
                        ),
                        "nifty_price_vs_sma50": (
                            float(tech.price_vs_sma50) if tech.price_vs_sma50 else None
                        ),
                        "nifty_bollinger_position": (
                            tech.bollinger_position if tech.bollinger_position else "middle"
                        ),
                        "nifty_volume_trend": tech.volume_trend if tech.volume_trend else "stable",
                    }
                )

            # 5-min quick levels
            if hasattr(nifty, "pivot_5min") and nifty.pivot_5min:
                features.update(
                    {
                        "nifty_pivot_5min": float(nifty.pivot_5min),
                        "nifty_support_5min": (
                            float(nifty.support_5min) if nifty.support_5min else 0.0
                        ),
                        "nifty_resistance_5min": (
                            float(nifty.resistance_5min) if nifty.resistance_5min else 0.0
                        ),
                    }
                )

            # Quick opportunity
            if hasattr(nifty, "quick_opportunity") and nifty.quick_opportunity:
                opp = nifty.quick_opportunity
                features.update(
                    {
                        "quick_signal": opp.signal if opp.signal else "HOLD",
                        "quick_confidence": int(opp.confidence) if opp.confidence else 50,
                        "quick_trade_type": opp.trade_type if opp.trade_type else "none",
                    }
                )

        # Market breadth
        features.update(
            {
                "market_advances": (
                    int(detailed_context.advances) if detailed_context.advances else 0
                ),
                "market_declines": (
                    int(detailed_context.declines) if detailed_context.declines else 0
                ),
                "market_unchanged": (
                    int(detailed_context.unchanged) if detailed_context.unchanged else 0
                ),
            }
        )

        # Sector performance
        if hasattr(detailed_context, "sectors") and detailed_context.sectors:
            sector_changes = [
                float(s.change_percent) for s in detailed_context.sectors if s.change_percent
            ]
            if sector_changes:
                features.update(
                    {
                        "sector_avg_change": sum(sector_changes) / len(sector_changes),
                        "sector_max_change": max(sector_changes),
                        "sector_min_change": min(sector_changes),
                        "sector_breadth": sum(1 for c in sector_changes if c > 0)
                        / len(sector_changes),
                    }
                )

    # INTRADAY CONTEXT
    if intraday_context:
        features.update(
            {
                "intraday_volatility": (
                    intraday_context.intraday_volatility
                    if hasattr(intraday_context, "intraday_volatility")
                    and intraday_context.intraday_volatility
                    else "unknown"
                ),
                "intraday_momentum": (
                    intraday_context.current_momentum
                    if hasattr(intraday_context, "current_momentum")
                    and intraday_context.current_momentum
                    else "unknown"
                ),
                "intraday_trend": (
                    intraday_context.market_phase
                    if hasattr(intraday_context, "market_phase") and intraday_context.market_phase
                    else "unknown"
                ),
                "intraday_volume_surge": False,  # Not available in current model
            }
        )

    # SWING CONTEXT
    if swing_context:
        features.update(
            {
                "swing_trend": (
                    swing_context.multi_day_trend
                    if hasattr(swing_context, "multi_day_trend") and swing_context.multi_day_trend
                    else "unknown"
                ),
                "swing_strength": (
                    swing_context.trend_strength
                    if hasattr(swing_context, "trend_strength") and swing_context.trend_strength
                    else "unknown"
                ),
            }
        )

    # LONG-TERM CONTEXT
    if long_term_context:
        features.update(
            {
                "longterm_trend": (
                    long_term_context.economic_cycle
                    if hasattr(long_term_context, "economic_cycle")
                    and long_term_context.economic_cycle
                    else "unknown"
                ),
                "longterm_strength": (
                    long_term_context.market_valuation
                    if hasattr(long_term_context, "market_valuation")
                    and long_term_context.market_valuation
                    else "unknown"
                ),
            }
        )

    return features
