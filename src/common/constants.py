"""
Common Constants
================

Shared constants across the application.
Following workspace rules: minimal code, self-explanatory naming, proper documentation.
"""

from typing import Dict, List

# =============================================================================
# MARKET INDICES CONSTITUENTS
# =============================================================================

# Nifty 50 constituent symbols (as of 2026-02-13)
# Used for market breadth calculation (advance/decline ratio)
NIFTY_50_CONSTITUENTS: List[str] = [
    "RELIANCE",
    "TCS",
    "HDFCBANK",
    "INFY",
    "ICICIBANK",
    "HINDUNILVR",
    "BHARTIARTL",
    "KOTAKBANK",
    "ITC",
    "LT",
    "SBIN",
    "AXISBANK",
    "BAJFINANCE",
    "ASIANPAINT",
    "MARUTI",
    "HCLTECH",
    "WIPRO",
    "ULTRACEMCO",
    "TITAN",
    "NESTLEIND",
    "SUNPHARMA",
    "TECHM",
    "BAJAJFINSV",
    "ONGC",
    "NTPC",
    "POWERGRID",
    "M&M",
    "ADANIPORTS",
    "COALINDIA",
    "TATASTEEL",
    "TATAMOTORS",
    "DIVISLAB",
    "GRASIM",
    "JSWSTEEL",
    "HINDALCO",
    "INDUSINDBK",
    "DRREDDY",
    "BRITANNIA",
    "APOLLOHOSP",
    "CIPLA",
    "EICHERMOT",
    "BAJAJ-AUTO",
    "HEROMOTOCO",
    "BPCL",
    "SHREECEM",
    "SBILIFE",
    "UPL",
    "ADANIENT",
    "HDFCLIFE",
    "TATACONSUM",
]

# =============================================================================
# EXCHANGE PREFIXES
# =============================================================================

# Exchange prefixes for Kite Connect API
EXCHANGE_PREFIX: Dict[str, str] = {
    "NSE": "NSE:",
    "BSE": "BSE:",
    "NFO": "NFO:",  # NSE Futures & Options
    "CDS": "CDS:",  # Currency Derivatives
    "BFO": "BFO:",  # BSE Futures & Options
    "MCX": "MCX:",  # Multi Commodity Exchange
}

# =============================================================================
# DEFAULT EXCHANGE
# =============================================================================

DEFAULT_EXCHANGE = "NSE"

# =============================================================================
# MARKET BREADTH THRESHOLDS
# =============================================================================

# Market breadth interpretation thresholds
BREADTH_BULLISH_THRESHOLD = 2.0  # AD ratio > 2.0 = strong bullish
BREADTH_BEARISH_THRESHOLD = 0.5  # AD ratio < 0.5 = strong bearish
BREADTH_NEUTRAL_LOWER = 0.8  # AD ratio 0.8-1.2 = neutral
BREADTH_NEUTRAL_UPPER = 1.2
