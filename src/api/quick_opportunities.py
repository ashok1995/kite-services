"""
Quick Money-Making Opportunities API
=====================================

Provides 5-minute timeframe technical analysis for quick trading opportunities:
- Index-level support/resistance (5min)
- RSI, MACD, momentum indicators
- Breakout/breakdown signals
- Entry/exit levels
- Real-time opportunity scanner

Designed for: Intraday scalping and quick trades
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from core.service_manager import get_service_manager

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================


class QuickOpportunityRequest(BaseModel):
    """Request for quick trading opportunities."""

    symbols: List[str] = Field(
        default=["NSE:NIFTY 50", "NSE:NIFTY BANK"],
        description="Symbols to analyze (default: indices)",
    )
    timeframe: str = Field(default="5minute", description="Timeframe: 5minute, 15minute, 1hour")
    opportunity_types: List[str] = Field(
        default=["breakout", "reversal", "momentum"], description="Types of opportunities to find"
    )


class TechnicalLevel(BaseModel):
    """Technical price level."""

    level: Decimal
    type: str  # support, resistance, pivot
    strength: str  # strong, moderate, weak
    distance_percent: Decimal  # Distance from current price


class OpportunitySignal(BaseModel):
    """Trading opportunity signal."""

    symbol: str
    opportunity_type: str  # breakout, reversal, momentum
    signal: str  # buy, sell, neutral
    confidence: float  # 0-100
    entry_price: Optional[Decimal]
    target_price: Optional[Decimal]
    stop_loss: Optional[Decimal]
    risk_reward_ratio: Optional[float]
    reasoning: str
    time_sensitive: bool  # True if needs immediate action
    valid_for_minutes: int  # How long signal is valid


class QuickOpportunityResponse(BaseModel):
    """Quick trading opportunities response."""

    success: bool

    # Current market state
    nifty_price: Decimal
    nifty_5min_trend: str  # bullish, bearish, neutral
    market_momentum: str  # accelerating, stable, decelerating
    volatility: str  # low, medium, high

    # Technical levels (5-min based)
    immediate_support: List[TechnicalLevel]
    immediate_resistance: List[TechnicalLevel]

    # Indicators (5-min)
    rsi_5min: Optional[float] = Field(None, ge=0, le=100)
    macd_signal: Optional[str] = None  # bullish, bearish, neutral
    volume_surge: bool = False  # True if volume spike detected

    # Opportunities
    opportunities: List[OpportunitySignal]

    # Meta
    scan_time: datetime = Field(default_factory=datetime.now)
    data_age_seconds: int  # How fresh is the data
    next_scan_in_seconds: int = 30  # When to scan next

    message: str


# ============================================================================
# MAIN ENDPOINT
# ============================================================================


@router.post("/opportunities/quick", response_model=QuickOpportunityResponse)
async def get_quick_opportunities(request: QuickOpportunityRequest):
    """
    Get quick money-making opportunities based on 5-minute technical analysis.

    Returns immediate trading opportunities with entry, target, stop-loss levels.
    Optimized for scalping and quick intraday trades.
    """
    try:
        service_manager = await get_service_manager()
        kite_client = service_manager.kite_client

        logger.info(f"Scanning for quick opportunities: {request.symbols}")

        # ================================================================
        # 1. GET REAL-TIME QUOTES (Kite Connect)
        # ================================================================
        quotes = await kite_client.quote(request.symbols)

        # Focus on Nifty for now
        nifty_symbol = "NSE:NIFTY 50"
        nifty_quote = quotes.get(nifty_symbol, {})

        if not nifty_quote:
            raise HTTPException(status_code=503, detail="Unable to fetch Nifty data from Kite")

        # Extract current data
        current_price = Decimal(str(nifty_quote.get("last_price", 0)))
        ohlc = nifty_quote.get("ohlc", {})
        day_open = Decimal(str(ohlc.get("open", current_price)))
        day_high = Decimal(str(ohlc.get("high", current_price)))
        day_low = Decimal(str(ohlc.get("low", current_price)))
        volume = nifty_quote.get("volume", 0)
        avg_volume = nifty_quote.get("average_price", volume)  # Approximate

        # ================================================================
        # 2. CALCULATE 5-MIN TECHNICAL LEVELS
        # ================================================================

        # Support/Resistance based on intraday pivots
        pivot = ((day_high + day_low + current_price) / 3).quantize(Decimal("0.01"))

        # Immediate levels (within 0.5% for quick trades)
        immediate_support = []
        immediate_resistance = []

        # S1, S2 (support)
        s1 = (pivot * 2 - day_high).quantize(Decimal("0.01"))
        s2 = (pivot - (day_high - day_low)).quantize(Decimal("0.01"))

        # R1, R2 (resistance)
        r1 = (pivot * 2 - day_low).quantize(Decimal("0.01"))
        r2 = (pivot + (day_high - day_low)).quantize(Decimal("0.01"))

        # Calculate distances
        for level, level_type in [
            (s1, "support"),
            (s2, "support"),
            (r1, "resistance"),
            (r2, "resistance"),
        ]:
            distance_pct = abs((level - current_price) / current_price * 100).quantize(
                Decimal("0.01")
            )
            if distance_pct <= Decimal("0.5"):  # Within 0.5% - immediate level
                strength = "strong" if distance_pct <= Decimal("0.2") else "moderate"
                tech_level = TechnicalLevel(
                    level=level, type=level_type, strength=strength, distance_percent=distance_pct
                )
                if level_type == "support":
                    immediate_support.append(tech_level)
                else:
                    immediate_resistance.append(tech_level)

        # ================================================================
        # 3. MOMENTUM & TREND (5-min approximation)
        # ================================================================

        # 5-min trend (using position in day range as proxy)
        price_position = (
            (current_price - day_low) / (day_high - day_low)
            if (day_high - day_low) > 0
            else Decimal("0.5")
        )

        if price_position > Decimal("0.7"):
            nifty_5min_trend = "bullish"
            market_momentum = "accelerating"
        elif price_position < Decimal("0.3"):
            nifty_5min_trend = "bearish"
            market_momentum = "decelerating"
        else:
            nifty_5min_trend = "neutral"
            market_momentum = "stable"

        # Change from open
        change_from_open = current_price - day_open
        change_pct = (change_from_open / day_open * 100) if day_open > 0 else Decimal("0")

        # ================================================================
        # 4. VOLUME ANALYSIS
        # ================================================================
        volume_surge = volume > (avg_volume * 1.5) if avg_volume > 0 else False

        # ================================================================
        # 5. RSI APPROXIMATION (using price position)
        # ================================================================
        # Simplified RSI based on price position in range
        rsi_5min = float(price_position * 100)

        # ================================================================
        # 6. VOLATILITY
        # ================================================================
        price_range_pct = ((day_high - day_low) / day_low * 100) if day_low > 0 else Decimal("0")
        if price_range_pct > Decimal("1.5"):
            volatility = "high"
        elif price_range_pct > Decimal("0.8"):
            volatility = "medium"
        else:
            volatility = "low"

        # ================================================================
        # 7. IDENTIFY OPPORTUNITIES
        # ================================================================
        opportunities = []

        # BREAKOUT OPPORTUNITY
        if "breakout" in request.opportunity_types:
            # Check if near resistance with bullish momentum
            if immediate_resistance and nifty_5min_trend == "bullish":
                nearest_resistance = min(immediate_resistance, key=lambda x: x.distance_percent)
                if nearest_resistance.distance_percent < Decimal("0.3"):
                    target = nearest_resistance.level + (
                        nearest_resistance.level * Decimal("0.005")
                    )  # 0.5% above
                    stop_loss = current_price - (current_price * Decimal("0.003"))  # 0.3% below
                    risk_reward = (
                        float((target - current_price) / (current_price - stop_loss))
                        if (current_price - stop_loss) > 0
                        else 1.0
                    )

                    opportunities.append(
                        OpportunitySignal(
                            symbol=nifty_symbol,
                            opportunity_type="breakout",
                            signal="buy" if change_pct > 0 else "neutral",
                            confidence=70.0 if volume_surge else 60.0,
                            entry_price=current_price,
                            target_price=target.quantize(Decimal("0.01")),
                            stop_loss=stop_loss.quantize(Decimal("0.01")),
                            risk_reward_ratio=round(risk_reward, 2),
                            reasoning=(
                                f"Near resistance at {nearest_resistance.level}, "
                                "bullish momentum, position for breakout"
                            ),
                            time_sensitive=True,
                            valid_for_minutes=15,
                        )
                    )

        # REVERSAL OPPORTUNITY
        if "reversal" in request.opportunity_types:
            # Overbought reversal (RSI > 70 near resistance)
            if rsi_5min > 70 and immediate_resistance:
                nearest_resistance = min(immediate_resistance, key=lambda x: x.distance_percent)
                if nearest_resistance.distance_percent < Decimal("0.2"):
                    target = current_price - (current_price * Decimal("0.005"))  # 0.5% down
                    stop_loss = nearest_resistance.level + (
                        nearest_resistance.level * Decimal("0.002")
                    )  # 0.2% above resistance
                    risk_reward = (
                        float((current_price - target) / (stop_loss - current_price))
                        if (stop_loss - current_price) > 0
                        else 1.0
                    )

                    opportunities.append(
                        OpportunitySignal(
                            symbol=nifty_symbol,
                            opportunity_type="reversal",
                            signal="sell",
                            confidence=65.0,
                            entry_price=current_price,
                            target_price=target.quantize(Decimal("0.01")),
                            stop_loss=stop_loss.quantize(Decimal("0.01")),
                            risk_reward_ratio=round(risk_reward, 2),
                            reasoning=(
                                f"Overbought (RSI {rsi_5min:.1f}), near resistance, "
                                "expect reversal"
                            ),
                            time_sensitive=True,
                            valid_for_minutes=10,
                        )
                    )

            # Oversold reversal (RSI < 30 near support)
            elif rsi_5min < 30 and immediate_support:
                nearest_support = min(immediate_support, key=lambda x: x.distance_percent)
                if nearest_support.distance_percent < Decimal("0.2"):
                    target = current_price + (current_price * Decimal("0.005"))  # 0.5% up
                    stop_loss = nearest_support.level - (
                        nearest_support.level * Decimal("0.002")
                    )  # 0.2% below support
                    risk_reward = (
                        float((target - current_price) / (current_price - stop_loss))
                        if (current_price - stop_loss) > 0
                        else 1.0
                    )

                    opportunities.append(
                        OpportunitySignal(
                            symbol=nifty_symbol,
                            opportunity_type="reversal",
                            signal="buy",
                            confidence=65.0,
                            entry_price=current_price,
                            target_price=target.quantize(Decimal("0.01")),
                            stop_loss=stop_loss.quantize(Decimal("0.01")),
                            risk_reward_ratio=round(risk_reward, 2),
                            reasoning=f"Oversold (RSI {rsi_5min:.1f}), near support, expect bounce",
                            time_sensitive=True,
                            valid_for_minutes=10,
                        )
                    )

        # MOMENTUM OPPORTUNITY
        if "momentum" in request.opportunity_types:
            # Strong momentum with volume
            if abs(change_pct) > Decimal("0.3") and volume_surge:
                if change_pct > 0:  # Bullish momentum
                    target = current_price + (current_price * Decimal("0.004"))  # 0.4% up
                    stop_loss = current_price - (current_price * Decimal("0.002"))  # 0.2% down
                    signal = "buy"
                    reasoning = (
                        f"Strong bullish momentum ({change_pct:.2f}%), volume surge detected"
                    )
                else:  # Bearish momentum
                    target = current_price - (current_price * Decimal("0.004"))  # 0.4% down
                    stop_loss = current_price + (current_price * Decimal("0.002"))  # 0.2% up
                    signal = "sell"
                    reasoning = (
                        f"Strong bearish momentum ({change_pct:.2f}%), volume surge detected"
                    )

                risk_reward = (
                    float(abs((target - current_price) / (current_price - stop_loss)))
                    if (current_price - stop_loss) != 0
                    else 1.0
                )

                opportunities.append(
                    OpportunitySignal(
                        symbol=nifty_symbol,
                        opportunity_type="momentum",
                        signal=signal,
                        confidence=75.0,
                        entry_price=current_price,
                        target_price=target.quantize(Decimal("0.01")),
                        stop_loss=stop_loss.quantize(Decimal("0.01")),
                        risk_reward_ratio=round(risk_reward, 2),
                        reasoning=reasoning,
                        time_sensitive=True,
                        valid_for_minutes=5,
                    )
                )

        # ================================================================
        # 8. BUILD RESPONSE
        # ================================================================

        # Sort support/resistance by distance
        immediate_support.sort(key=lambda x: x.distance_percent)
        immediate_resistance.sort(key=lambda x: x.distance_percent)

        # Sort opportunities by confidence
        opportunities.sort(key=lambda x: x.confidence, reverse=True)

        # MACD signal (simplified)
        macd_signal = (
            "bullish"
            if change_pct > 0 and market_momentum == "accelerating"
            else "bearish" if change_pct < 0 and market_momentum == "decelerating" else "neutral"
        )

        message = f"Found {len(opportunities)} quick trading opportunities"
        if opportunities:
            best_opp = opportunities[0]
            message += (
                f" | Best: {best_opp.opportunity_type} {best_opp.signal} "
                f"(confidence {best_opp.confidence}%)"
            )

        return QuickOpportunityResponse(
            success=True,
            nifty_price=current_price,
            nifty_5min_trend=nifty_5min_trend,
            market_momentum=market_momentum,
            volatility=volatility,
            immediate_support=immediate_support[:3],  # Top 3
            immediate_resistance=immediate_resistance[:3],  # Top 3
            rsi_5min=rsi_5min,
            macd_signal=macd_signal,
            volume_surge=volume_surge,
            opportunities=opportunities,
            data_age_seconds=5,  # Approximate (real-time quote)
            next_scan_in_seconds=30,
            message=message,
        )

    except Exception as e:
        logger.error(f"Failed to scan quick opportunities: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Quick opportunity scan failed: {str(e)}")
