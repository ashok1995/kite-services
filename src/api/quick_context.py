"""
Quick Market Context API
=========================

Fast endpoint for getting market context data.
Optimized for frequent polling by trading systems.
"""

from datetime import datetime
from typing import Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from core.logging_config import get_logger
from core.service_manager import get_service_manager

router = APIRouter()
logger = get_logger(__name__)


class QuickMarketContextResponse(BaseModel):
    """Quick market context response - optimized for speed."""

    # Market regime
    market_regime: Optional[str] = Field(
        None, description="Market regime (bullish/bearish/sideways)"
    )
    volatility_regime: Optional[str] = Field(
        None, description="Volatility regime (low/normal/high)"
    )

    # India VIX
    india_vix: Optional[float] = Field(None, description="India VIX value")
    vix_level: Optional[str] = Field(None, description="VIX level (low/normal/high/extreme)")

    # Market breadth
    market_breadth: Optional[Dict] = Field(None, description="Market breadth data")

    # Nifty 50
    nifty_50: Optional[Dict] = Field(None, description="Nifty 50 data")

    # Sectors
    sectors: Optional[Dict] = Field(None, description="Sector performance")

    # Sentiment
    institutional_sentiment: Optional[str] = Field(None, description="Institutional sentiment")

    # Metadata
    confidence_score: float = Field(0.85, description="Data confidence score")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")


@router.get("/market-context-data/quick-context", response_model=QuickMarketContextResponse)
async def get_quick_market_context():
    """
    Get quick market context for trading systems.

    **Purpose:** Fast endpoint for frequent polling by trading systems and dashboards.

    **Returns:**
    - Market regime (bullish/bearish/sideways)
    - India VIX and volatility level
    - Market breadth (advance/decline ratio from Nifty 50)
    - Nifty 50 index data
    - Sector performance
    - Institutional sentiment

    **Performance:** < 500ms response time
    **Cache:** 60 seconds TTL on market breadth
    **Call Frequency:** Every 5 minutes recommended
    """
    import time

    start_time = time.time()

    try:
        service_manager = await get_service_manager()
        market_context_service = service_manager.market_context_service

        logger.info("Generating quick market context")

        # Get Indian market data
        indian_data_raw = await market_context_service._get_indian_market_data("quick")

        # Get market breadth
        breadth_data = await market_context_service.get_market_breadth()

        # Get volatility data
        vol_data = await market_context_service._get_volatility_data("quick")

        # Extract Nifty 50 data
        nifty_50_data = None
        if indian_data_raw and indian_data_raw.indices:
            for symbol, data in indian_data_raw.indices.items():
                if "NIFTY 50" in symbol:
                    nifty_50_data = {
                        "price": float(data.get("value", 0)),
                        "change_percent": float(data.get("change_percent", 0)),
                    }
                    break

        # Determine market regime
        market_regime = None
        if indian_data_raw and indian_data_raw.market_regime:
            market_regime = indian_data_raw.market_regime.value

        # Determine volatility regime
        volatility_regime = None
        vix_level = None
        if vol_data and vol_data.volatility_level:
            volatility_regime = vol_data.volatility_level.value
            if vol_data.india_vix:
                vix = float(vol_data.india_vix)
                if vix < 12:
                    vix_level = "low"
                elif vix < 20:
                    vix_level = "normal"
                elif vix < 25:
                    vix_level = "high"
                else:
                    vix_level = "extreme"

        # Get sector data
        sector_data_raw = await market_context_service._get_sector_data("quick")
        sectors = {}
        if sector_data_raw and hasattr(sector_data_raw, "sector_performance"):
            for sector, perf in (sector_data_raw.sector_performance or {}).items():
                sectors[sector] = {
                    "change_percent": float(perf),
                    "leader": False,  # Can be enhanced later
                }

        # Institutional sentiment (simplified)
        institutional_sentiment = "neutral"
        if market_regime:
            if "bullish" in market_regime or "up" in market_regime:
                institutional_sentiment = "bullish"
            elif "bearish" in market_regime or "down" in market_regime:
                institutional_sentiment = "bearish"

        processing_time = (time.time() - start_time) * 1000

        return QuickMarketContextResponse(
            market_regime=market_regime,
            volatility_regime=volatility_regime,
            india_vix=float(vol_data.india_vix) if vol_data and vol_data.india_vix else None,
            vix_level=vix_level,
            market_breadth=breadth_data if breadth_data else None,
            nifty_50=nifty_50_data,
            sectors=sectors if sectors else None,
            institutional_sentiment=institutional_sentiment,
            confidence_score=0.85 if breadth_data and nifty_50_data else 0.50,
            processing_time_ms=round(processing_time, 2),
        )

    except Exception as e:
        logger.error(f"Quick market context failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get quick market context: {str(e)}")
