"""
Trend analyzer for market context endpoints.

Pure computation utilities: convert OHLC candles into short/medium/long trend metrics.
"""

from typing import Any, Dict, Optional

import numpy as np
import pandas as pd

# Regime thresholds tuned for daily candles
ROC_STRONG_THRESHOLD = 8.0
ROC_WEAK_THRESHOLD = 2.0
R2_CLEAN_TREND = 0.5

HORIZONS = {
    "short_term": 5,      # ~1 trading week
    "medium_term": 22,    # ~1 trading month
    "long_term": None,    # full lookback (we pass ~90d)
}


def _adaptive_period(window_size: int, default: int = 14) -> int:
    return max(2, min(default, window_size - 1))


def compute_rsi(close: pd.Series, period: int = 14) -> float:
    period = _adaptive_period(len(close), period)
    if len(close) < period + 1:
        return 50.0

    delta = close.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)

    avg_gain = gain.rolling(window=period, min_periods=period).mean().iloc[-1]
    avg_loss = loss.rolling(window=period, min_periods=period).mean().iloc[-1]

    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return round(100.0 - (100.0 / (1.0 + rs)), 2)


def compute_atr_pct(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> float:
    period = _adaptive_period(len(close), period)
    if len(close) < period + 1:
        base_range = (high - low).mean()
        current = close.iloc[-1]
        return round((base_range / current) * 100, 4) if current > 0 else 0.0

    hl = high - low
    hc = (high - close.shift()).abs()
    lc = (low - close.shift()).abs()
    tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
    atr = tr.rolling(window=period, min_periods=period).mean().iloc[-1]

    current = close.iloc[-1]
    if current == 0:
        return 0.0
    return round((atr / current) * 100, 4)


def compute_linear_regression(close: pd.Series) -> tuple[float, float]:
    """Returns (slope_pct_per_day, r_squared)."""
    if len(close) < 3:
        return 0.0, 0.0

    y = close.values.astype(float)
    x = np.arange(len(y), dtype=float)
    slope, intercept = np.polyfit(x, y, 1)

    y_pred = slope * x + intercept
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - y.mean()) ** 2)
    r_squared = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

    mean_price = y.mean()
    slope_pct = (slope / mean_price) * 100 if mean_price > 0 else 0.0

    return round(slope_pct, 4), round(max(0.0, r_squared), 4)


def classify_regime(roc: float, r_squared: float) -> str:
    abs_roc = abs(roc)
    if abs_roc < ROC_WEAK_THRESHOLD and r_squared < R2_CLEAN_TREND:
        return "consolidating"
    if roc >= 0:
        if abs_roc >= ROC_STRONG_THRESHOLD and r_squared >= R2_CLEAN_TREND:
            return "strong_bullish"
        if abs_roc >= ROC_WEAK_THRESHOLD:
            return "bullish"
        return "weak_bullish"
    if abs_roc >= ROC_STRONG_THRESHOLD and r_squared >= R2_CLEAN_TREND:
        return "strong_bearish"
    if abs_roc >= ROC_WEAK_THRESHOLD:
        return "bearish"
    return "weak_bearish"


def classify_volatility(annualized_vol: float) -> str:
    if annualized_vol < 10:
        return "low"
    if annualized_vol < 25:
        return "normal"
    if annualized_vol < 45:
        return "high"
    return "extreme"


def analyze_horizon(candles: pd.DataFrame, n_days: Optional[int], current_price: float) -> Dict[str, Any]:
    if n_days is not None and len(candles) > n_days:
        window = candles.tail(n_days).copy()
    else:
        window = candles.copy()

    if len(window) < 2:
        return {"error": "insufficient_data", "candles_used": len(window)}

    close = window["close"].astype(float)
    high = window["high"].astype(float)
    low = window["low"].astype(float)

    start_price = float(close.iloc[0])
    end_price = float(close.iloc[-1])
    if start_price == 0:
        return {"error": "invalid_start_price", "candles_used": len(window)}

    roc = ((end_price - start_price) / start_price) * 100
    slope_pct, r_squared = compute_linear_regression(close)

    daily_returns = close.pct_change().dropna()
    vol_daily = float(daily_returns.std()) if len(daily_returns) > 1 else 0.0
    vol_annualized = vol_daily * np.sqrt(252) * 100

    rsi = compute_rsi(close)
    atr_pct = compute_atr_pct(high, low, close)

    sma = float(close.mean())
    sma_distance_pct = ((current_price - sma) / sma) * 100 if sma > 0 else 0.0

    regime = classify_regime(roc, r_squared)
    vol_regime = classify_volatility(vol_annualized)

    return {
        "roc": round(roc, 2),
        "slope_per_day": slope_pct,
        "r_squared": r_squared,
        "rsi": rsi,
        "volatility_annualized": round(vol_annualized, 2),
        "atr_pct": atr_pct,
        "sma": round(sma, 2),
        "sma_distance_pct": round(sma_distance_pct, 2),
        "period_high": round(float(high.max()), 2),
        "period_low": round(float(low.min()), 2),
        "regime": regime,
        "volatility_regime": vol_regime,
        "candles_used": len(window),
    }


def analyze_candles(candles: pd.DataFrame, current_price: float) -> Optional[Dict[str, Dict[str, Any]]]:
    """
    Compute short/medium/long trend analysis from OHLCV candles.

    Expected columns: open, high, low, close, volume
    """
    if candles is None or candles.empty or len(candles) < 3:
        return None
    required = {"open", "high", "low", "close"}
    if not required.issubset(set(candles.columns)):
        return None

    result: Dict[str, Dict[str, Any]] = {}
    for horizon_name, n_days in HORIZONS.items():
        analysis = analyze_horizon(candles, n_days, current_price)
        result[horizon_name] = None if "error" in analysis else analysis
    return result

