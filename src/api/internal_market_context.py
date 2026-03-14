"""
Internal Market Context API
===========================

Single endpoint for Indian market context only (Kite Connect).
Global indices (Gift Nifty, S&P 500, etc.) are provided by a separate global service.
"""

import time
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional, Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
import pandas as pd

from common.time_utils import now_ist_naive
from core.logging_config import get_logger
from core.service_manager import get_service_manager
from services.trend_analyzer import analyze_candles, analyze_horizon

router = APIRouter()
logger = get_logger(__name__)


# Trend cache TTLs (seconds): intraday changes fastest, long-term slowest.
TREND_TTL_INTRADAY = 60
TREND_TTL_SHORT_MEDIUM = 300
TREND_TTL_LONG = 3600


class InternalMarketContextResponse(BaseModel):
    """Indian market context response - Kite Connect only."""

    market_regime: Optional[str] = Field(
        None, description="Market regime (bullish/bearish/sideways)"
    )
    volatility_regime: Optional[str] = Field(
        None, description="Volatility regime (low/normal/high)"
    )
    market_breadth: Optional[Dict] = Field(None, description="Nifty 50 advance/decline data")
    nifty_50: Optional[Dict] = Field(None, description="Nifty 50 index data with trend")
    bank_nifty: Optional[Dict] = Field(None, description="Bank Nifty index data with trend")
    india_vix: Optional[Dict] = Field(None, description="India VIX data with trend")
    sectors: Optional[Dict] = Field(None, description="Indian sector performance")
    institutional_sentiment: Optional[str] = Field(None, description="Derived sentiment")
    confidence_score: float = Field(0.85, description="Data confidence score")
    timestamp: datetime = Field(
        default_factory=now_ist_naive,
        description="Response timestamp (IST)",
    )
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")


class TrendData(BaseModel):
    """Trend metrics for one horizon."""

    roc: float
    slope_per_day: float
    r_squared: float
    rsi: float
    volatility_annualized: float
    atr_pct: float
    sma: float
    sma_distance_pct: float
    period_high: float
    period_low: float
    regime: str
    volatility_regime: str
    candles_used: int


class TrendInfo(BaseModel):
    """Multi-timeframe trend block."""

    intraday: Optional[TrendData] = None
    short_term: Optional[TrendData] = None
    medium_term: Optional[TrendData] = None
    long_term: Optional[TrendData] = None


def _build_trend_info(raw: Optional[Dict[str, Any]]) -> Optional[TrendInfo]:
    """Convert raw dict from trend_analyzer into a typed response model."""
    if not raw:
        return None
    try:
        return TrendInfo(
            intraday=TrendData(**raw["intraday"]) if raw.get("intraday") else None,
            short_term=TrendData(**raw["short_term"]) if raw.get("short_term") else None,
            medium_term=TrendData(**raw["medium_term"]) if raw.get("medium_term") else None,
            long_term=TrendData(**raw["long_term"]) if raw.get("long_term") else None,
        )
    except Exception as exc:
        logger.warning(f"Failed to parse trend payload: {exc}")
        return None


async def _fetch_symbol_trend(
    service_manager: Any,
    symbol: str,
    current_price: float,
) -> Optional[TrendInfo]:
    """
    Fetch 3-month daily candles from Kite and compute trend block.
    Returns None on any failure (non-critical).
    """
    try:
        cache = getattr(service_manager, "cache_service", None)
        cache_key_base = symbol.replace(":", "_")
        key_fast = f"kite:internal_trend:fast:{cache_key_base}"      # short+medium
        key_long = f"kite:internal_trend:long:{cache_key_base}"      # long
        key_intraday = f"kite:internal_trend:intraday:{cache_key_base}"

        cached_fast = await cache.get(key_fast) if cache else None
        cached_long = await cache.get(key_long) if cache else None
        cached_intraday = await cache.get(key_intraday) if cache else None

        # Compute daily horizons if either fast or long cache is missing.
        if cached_fast is None or cached_long is None:
            daily_df = await _fetch_candles_for_symbol(
                service_manager=service_manager, symbol=symbol, lookback_days=90, interval="day"
            )
            daily = analyze_candles(daily_df, float(current_price)) if daily_df is not None else None
            if daily:
                cached_fast = {
                    "short_term": daily.get("short_term"),
                    "medium_term": daily.get("medium_term"),
                }
                cached_long = {"long_term": daily.get("long_term")}
                if cache:
                    await cache.set(key_fast, cached_fast, ttl=TREND_TTL_SHORT_MEDIUM)
                    await cache.set(key_long, cached_long, ttl=TREND_TTL_LONG)

        # Compute intraday trend separately on 5-minute candles.
        if cached_intraday is None:
            intraday_df = await _fetch_candles_for_symbol(
                service_manager=service_manager, symbol=symbol, lookback_days=2, interval="5minute"
            )
            intraday = None
            if intraday_df is not None:
                intraday = analyze_horizon(intraday_df, n_days=21, current_price=float(current_price))
                if "error" in intraday:
                    intraday = None
            cached_intraday = {"intraday": intraday}
            if cache:
                await cache.set(key_intraday, cached_intraday, ttl=TREND_TTL_INTRADAY)

        merged = {
            "intraday": (cached_intraday or {}).get("intraday"),
            "short_term": (cached_fast or {}).get("short_term"),
            "medium_term": (cached_fast or {}).get("medium_term"),
            "long_term": (cached_long or {}).get("long_term"),
        }
        return _build_trend_info(merged)
    except Exception as exc:
        logger.warning(f"Trend fetch failed for {symbol}: {exc}")
        return None


async def _fetch_candles_for_symbol(
    service_manager: Any,
    symbol: str,
    lookback_days: int,
    interval: str,
) -> Optional[pd.DataFrame]:
    """
    Fetch candles for indices/instruments using instrument token route first.
    Falls back to get_historical_data() for daily candles.
    """
    kite_client = service_manager.kite_client
    from_date = (datetime.now() - timedelta(days=lookback_days)).strftime("%Y-%m-%d")
    to_date = datetime.now().strftime("%Y-%m-%d")

    # Preferred path: quote -> instrument_token -> historical_data(interval)
    token = None
    try:
        quote_data = await kite_client.quote([symbol])
        payload = quote_data.get(symbol, {}) if isinstance(quote_data, dict) else {}
        token = payload.get("instrument_token")
    except Exception as exc:
        logger.debug(f"Token lookup failed for {symbol}: {exc}")

    rows = None
    if token:
        rows = await kite_client.historical_data(int(token), from_date, to_date, interval)

    # Fallback for daily only (legacy helper needs tradingsymbol keys).
    if not rows and interval == "day":
        candidates = [symbol]
        if ":" in symbol:
            candidates.append(symbol.split(":", 1)[1])
        for candidate in dict.fromkeys(candidates):
            hist = await kite_client.get_historical_data(candidate, days=lookback_days)
            if hist:
                rows = hist
                break

    if not rows:
        return None

    normalized = []
    for r in rows:
        normalized.append(
            {
                "open": float(r.get("open", 0)),
                "high": float(r.get("high", 0)),
                "low": float(r.get("low", 0)),
                "close": float(r.get("close", 0)),
                "volume": float(r.get("volume", 0)),
            }
        )
    df = pd.DataFrame(normalized)
    required = {"open", "high", "low", "close"}
    if df.empty or not required.issubset(df.columns):
        return None
    return df


@router.get("/internal-market-context", response_model=InternalMarketContextResponse)
async def get_internal_market_context():
    """
    Indian market context only (Kite Connect).

    Returns: market regime, India VIX, Nifty 50 breadth, Nifty 50 index,
    sector performance. Global indices (Gift Nifty, S&P 500, etc.) are
    provided by a separate global service.
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
        bank_nifty_data = None
        trend_payload: Dict[str, Dict] = {}

        if indian_data_raw and indian_data_raw.indices:
            for symbol, data in indian_data_raw.indices.items():
                if "NIFTY 50" in symbol:
                    nifty_50_data = {
                        "price": float(data.get("value", 0)),
                        "change_percent": float(data.get("change_percent", 0)),
                    }
                elif "NIFTY BANK" in symbol:
                    bank_nifty_data = {
                        "price": float(data.get("value", 0)),
                        "change_percent": float(data.get("change_percent", 0)),
                    }

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

        # Fetch trends concurrently (non-critical)
        trend_tasks = []
        trend_keys = []

        if nifty_50_data:
            trend_tasks.append(
                _fetch_symbol_trend(service_manager, "NSE:NIFTY 50", nifty_50_data["price"])
            )
            trend_keys.append("nifty_50")

        if bank_nifty_data:
            trend_tasks.append(
                _fetch_symbol_trend(service_manager, "NSE:NIFTY BANK", bank_nifty_data["price"])
            )
            trend_keys.append("bank_nifty")

        if vol_data and vol_data.india_vix:
            trend_tasks.append(
                _fetch_symbol_trend(service_manager, "NSE:INDIA VIX", float(vol_data.india_vix))
            )
            trend_keys.append("india_vix")

        if trend_tasks:
            trend_results = await asyncio.gather(*trend_tasks)
            for key, trend in zip(trend_keys, trend_results):
                if trend:
                    trend_payload[key] = trend.model_dump()

        if nifty_50_data and trend_payload.get("nifty_50"):
            nifty_50_data["trend"] = trend_payload["nifty_50"]
        if bank_nifty_data and trend_payload.get("bank_nifty"):
            bank_nifty_data["trend"] = trend_payload["bank_nifty"]

        india_vix_block = None
        if vol_data and vol_data.india_vix:
            india_vix_block = {
                "value": float(vol_data.india_vix),
                "change_percent": float(vol_data.india_vix_change_percent) if hasattr(vol_data, "india_vix_change_percent") and vol_data.india_vix_change_percent else None,
                "level": vix_level,
                "trend": trend_payload.get("india_vix"),
            }

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
            market_breadth=breadth_data if breadth_data else None,
            nifty_50=nifty_50_data,
            bank_nifty=bank_nifty_data,
            india_vix=india_vix_block,
            sectors=sectors if sectors else None,
            institutional_sentiment=institutional_sentiment,
            confidence_score=0.90 if breadth_data and nifty_50_data and trend_payload else 0.50,
            processing_time_ms=round(processing_time, 2),
        )

    except Exception as e:
        logger.error(f"Internal market context failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal market context failed: {str(e)}")
