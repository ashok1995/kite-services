"""
Internal Market Context API
===========================

Single endpoint for Indian market context only (Kite Connect).
Global context is provided by a separate service.
"""

import time
from datetime import datetime
from typing import Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from core.logging_config import get_logger
from core.service_manager import get_service_manager
from src.common.time_utils import now_ist_naive

router = APIRouter()
logger = get_logger(__name__)


class InternalMarketContextResponse(BaseModel):
    """Indian market context response - Kite Connect only."""

    market_regime: Optional[str] = Field(
        None, description="Market regime (bullish/bearish/sideways)"
    )
    volatility_regime: Optional[str] = Field(
        None, description="Volatility regime (low/normal/high)"
    )
    india_vix: Optional[float] = Field(None, description="India VIX value")
    vix_level: Optional[str] = Field(None, description="VIX level (low/normal/high/extreme)")
    market_breadth: Optional[Dict] = Field(None, description="Nifty 50 advance/decline data")
    nifty_50: Optional[Dict] = Field(None, description="Nifty 50 index data")
    sectors: Optional[Dict] = Field(None, description="Indian sector performance")
    institutional_sentiment: Optional[str] = Field(None, description="Derived sentiment")
    confidence_score: float = Field(0.85, description="Data confidence score")
    timestamp: datetime = Field(
        default_factory=now_ist_naive,
        description="Response timestamp (IST)",
    )
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")


@router.get("/internal-market-context", response_model=InternalMarketContextResponse)
async def get_internal_market_context():
    """
    Indian market context only (Kite Connect).

    Returns: market regime, India VIX, Nifty 50 breadth, Nifty 50 index,
    sector performance. Global context is provided by a separate service.
    """
    start_time = time.time()

    try:
        service_manager = await get_service_manager()
        market_context_service = service_manager.market_context_service

        logger.info("Generating internal market context (Indian only)")

        indian_data_raw = await market_context_service._get_indian_market_data("internal")
        breadth_data = await market_context_service.get_market_breadth()
        vol_data = await market_context_service._get_volatility_data("internal")
        sector_data_raw = await market_context_service._get_sector_data("internal")

        nifty_50_data = None
        if indian_data_raw and indian_data_raw.indices:
            for symbol, data in indian_data_raw.indices.items():
                if "NIFTY 50" in symbol:
                    nifty_50_data = {
                        "price": float(data.get("value", 0)),
                        "change_percent": float(data.get("change_percent", 0)),
                    }
                    break

        market_regime = None
        if indian_data_raw and indian_data_raw.market_regime:
            market_regime = indian_data_raw.market_regime.value

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

        sectors = {}
        if sector_data_raw and hasattr(sector_data_raw, "sector_performance"):
            for sector, perf in (sector_data_raw.sector_performance or {}).items():
                sectors[sector] = {
                    "change_percent": float(perf),
                    "leader": False,
                }

        institutional_sentiment = "neutral"
        if market_regime:
            if "bullish" in market_regime or "up" in market_regime:
                institutional_sentiment = "bullish"
            elif "bearish" in market_regime or "down" in market_regime:
                institutional_sentiment = "bearish"

        processing_time = (time.time() - start_time) * 1000

        return InternalMarketContextResponse(
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
        logger.error(f"Internal market context failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal market context failed: {str(e)}")
