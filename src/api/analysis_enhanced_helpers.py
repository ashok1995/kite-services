"""
Enhanced Analysis Helper Functions
===================================

Scoring, quality assessment, and ML feature extraction for enhanced market context.
"""

from typing import List

from models.enhanced_context_models import (
    GlobalMarketPrimary,
    IndianMarketPrimary,
    MarketRegime,
    TradingStyle,
)


def calculate_market_score(global_ctx: GlobalMarketPrimary, indian_ctx: IndianMarketPrimary) -> int:
    """Calculate overall market score from -100 to +100."""
    score = 0

    # Global contribution (40%)
    if global_ctx.overall_trend == "bullish":
        score += 40
    elif global_ctx.overall_trend == "bearish":
        score -= 40

    # Indian contribution (60%)
    if indian_ctx.nifty_change:
        score += int(float(indian_ctx.nifty_change) * 10)

    # Adjust for market regime
    if indian_ctx.market_regime == MarketRegime.BULL_STRONG:
        score += 20
    elif indian_ctx.market_regime == MarketRegime.BEAR_STRONG:
        score -= 20

    return max(-100, min(100, score))


def determine_favorable_styles(market_score: int, regime: MarketRegime) -> List[TradingStyle]:
    """Determine which trading styles are favorable based on market conditions."""
    favorable = []

    if abs(market_score) > 30:
        favorable.append(TradingStyle.INTRADAY)

    if regime in [
        MarketRegime.BULL_WEAK,
        MarketRegime.BULL_STRONG,
        MarketRegime.BEAR_WEAK,
    ]:
        favorable.append(TradingStyle.SWING)

    if market_score > 20:
        favorable.append(TradingStyle.LONG_TERM)

    return favorable


def calculate_context_quality(primary, detailed, intraday, swing, long_term) -> float:
    """Calculate quality score of the context data."""
    quality = 0.0
    components = 0

    if primary:
        quality += 0.3
        components += 1

    if detailed:
        quality += 0.3
        components += 1

    if any([intraday, swing, long_term]):
        quality += 0.4
        components += 1

    return round(quality, 2) if components > 0 else 0.0


def get_data_quality_recommendations(
    real_count: int, approximated_count: int, fallback_count: int
) -> List[str]:
    """Get recommendations for improving data quality."""
    recommendations = []

    if fallback_count > 5:
        recommendations.append("HIGH FALLBACK RATE: Check API connectivity and credentials")

    if real_count < 3:
        recommendations.append("LOW REAL DATA: Verify Kite Connect token is valid")
        recommendations.append("Check if markets are open (Indian markets 9:15 AM - 3:30 PM IST)")

    if approximated_count > 10:
        recommendations.append(
            "MANY APPROXIMATIONS: Consider fetching historical data "
            "for better technical indicators"
        )

    if fallback_count == 0 and real_count > 5:
        recommendations.append("EXCELLENT DATA QUALITY: All major data sources working correctly")

    return recommendations
