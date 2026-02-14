"""
Cache Configuration
===================

Intelligent caching configuration with TTL based on data volatility.

Cache Strategy:
- Intraday data: 30 seconds (changes rapidly during market hours)
- Swing data: 5 minutes (hourly changes)
- Long-term data: 15 minutes (daily changes)
- Market indices: 1 minute (frequent updates)
- Sector performance: 15 minutes (changes slowly)
- Fundamentals: 1 hour (daily updates)
"""

from enum import Enum
from typing import Dict

from pydantic import BaseModel, Field


class CacheLevel(str, Enum):
    """Cache levels based on data volatility."""

    REAL_TIME = "real_time"  # 30 seconds - Intraday prices, live quotes
    FAST = "fast"  # 1 minute - Market indices, basic quotes
    MEDIUM = "medium"  # 5 minutes - Swing data, OHLC
    SLOW = "slow"  # 15 minutes - Sector performance, long-term
    STATIC = "static"  # 1 hour - Fundamentals, P/E ratios
    DAILY = "daily"  # 24 hours - Historical patterns


class CacheTTL:
    """
    Time-to-live (TTL) values in seconds for different cache levels.

    Based on data volatility and trading style requirements:
    - Intraday: Needs fresh data (30s-1m)
    - Swing: Can use slightly older data (5m)
    - Long-term: Data changes daily (15m-1h)
    """

    # Market Data
    REAL_TIME_QUOTE = 30  # Live quotes (intraday)
    MARKET_INDEX = 60  # Nifty, Bank Nifty, etc.
    OHLC_DATA = 300  # 5 minutes - OHLC for swing

    # Context Data
    PRIMARY_CONTEXT = 60  # 1 minute - global + Indian markets
    DETAILED_CONTEXT = 300  # 5 minutes - technical indicators
    INTRADAY_CONTEXT = 30  # 30 seconds - intraday specific
    SWING_CONTEXT = 300  # 5 minutes - swing specific
    LONGTERM_CONTEXT = 900  # 15 minutes - long-term specific

    # External API Data
    YAHOO_INDEX = 60  # 1 minute - global indices
    YAHOO_SECTOR = 900  # 15 minutes - sector performance (slow changing)
    YAHOO_FUNDAMENTALS = 3600  # 1 hour - P/E, P/B ratios
    KITE_QUOTE = 30  # 30 seconds - Kite quotes

    # Calculated Data
    PIVOT_POINTS = 900  # 15 minutes - pivots (calc from OHLC)
    TECHNICAL_INDICATORS = 300  # 5 minutes - RSI, MACD, etc.
    MARKET_BREADTH = 300  # 5 minutes - advances/declines

    # Composite Data (reusable across contexts)
    COMPOSITE_INTRADAY = 30  # Base intraday data (reuse for swing)
    COMPOSITE_SWING = 300  # Base swing data (reuse for long-term)
    COMPOSITE_LONGTERM = 900  # Base long-term data


class CacheKeyPattern:
    """
    Hierarchical cache key patterns for easy invalidation and lookup.

    Format: {service}:{data_type}:{identifier}:{timestamp_bucket}

    This allows:
    1. Invalidate all keys for a service
    2. Invalidate all keys for a data type
    3. Find related keys easily
    """

    # Market Data Keys
    KITE_QUOTE = "kite:quote:{symbol}"
    MARKET_INDEX = "market:index:{symbol}"
    OHLC = "market:ohlc:{symbol}:{interval}"

    # Context Keys
    PRIMARY_CTX = "context:primary:{date}:{hour}"
    DETAILED_CTX = "context:detailed:{date}:{hour}"
    INTRADAY_CTX = "context:intraday:{date}:{hour}:{minute}"
    SWING_CTX = "context:swing:{date}:{hour}"
    LONGTERM_CTX = "context:longterm:{date}"

    # External API Keys
    YAHOO_INDEX = "yahoo:index:{symbol}"
    YAHOO_SECTOR = "yahoo:sector:{sector}"
    YAHOO_FUNDAMENTALS = "yahoo:fundamentals:{symbol}"

    # Calculated Data Keys
    PIVOT_POINTS = "calc:pivot:{symbol}:{date}"
    TECHNICAL_IND = "calc:technical:{symbol}:{indicator}:{period}"
    MARKET_BREADTH = "calc:breadth:{date}:{hour}"

    # Composite Keys (for reuse across contexts)
    COMPOSITE_INTRADAY = "composite:intraday:{date}:{hour}:{minute}"
    COMPOSITE_SWING = "composite:swing:{date}:{hour}"
    COMPOSITE_LONGTERM = "composite:longterm:{date}"


class CacheConfig(BaseModel):
    """Cache configuration settings."""

    # Redis connection
    enabled: bool = Field(True, description="Enable/disable caching")
    host: str = Field("localhost", env="REDIS_HOST")
    port: int = Field(6379, env="REDIS_PORT")
    db: int = Field(0, env="REDIS_DB")
    password: str = Field(None, env="REDIS_PASSWORD")

    # Connection pool
    max_connections: int = Field(10, env="REDIS_MAX_CONNECTIONS")
    socket_timeout: int = Field(5, env="REDIS_SOCKET_TIMEOUT")
    socket_connect_timeout: int = Field(5, env="REDIS_CONNECT_TIMEOUT")

    # Cache behavior
    default_ttl: int = Field(300, description="Default TTL in seconds")
    key_prefix: str = Field("kite_services:", description="Prefix for all keys")

    # Cleanup
    cleanup_interval: int = Field(3600, description="Cleanup interval in seconds")
    max_memory_policy: str = Field("allkeys-lru", description="Redis eviction policy")

    model_config = {"extra": "ignore"}


class CacheStrategy:
    """
    Smart caching strategy for different trading styles.

    Key Insight:
    - Intraday needs fresh data (recompute every 30s)
    - Swing can reuse intraday data (just add swing-specific analysis)
    - Long-term can reuse swing data (just add long-term analysis)

    This hierarchical approach reduces redundant API calls.
    """

    @staticmethod
    def get_required_data(trading_style: str) -> Dict[str, int]:
        """
        Get required data and TTLs for a trading style.

        Args:
            trading_style: "intraday", "swing", or "long_term"

        Returns:
            Dict mapping data type to TTL
        """

        if trading_style == "intraday":
            return {
                "market_index": CacheTTL.MARKET_INDEX,  # 1 min
                "kite_quote": CacheTTL.KITE_QUOTE,  # 30 sec
                "pivot_points": CacheTTL.PIVOT_POINTS,  # 15 min (calc from OHLC)
                "intraday_context": CacheTTL.INTRADAY_CONTEXT,  # 30 sec
            }

        elif trading_style == "swing":
            return {
                # Reuse intraday data (cached separately)
                "intraday_base": CacheTTL.COMPOSITE_INTRADAY,  # 30 sec (reused)
                "ohlc_data": CacheTTL.OHLC_DATA,  # 5 min
                "sector_performance": CacheTTL.YAHOO_SECTOR,  # 15 min
                "swing_context": CacheTTL.SWING_CONTEXT,  # 5 min
            }

        elif trading_style == "long_term":
            return {
                # Reuse swing data (cached separately)
                "swing_base": CacheTTL.COMPOSITE_SWING,  # 5 min (reused)
                "fundamentals": CacheTTL.YAHOO_FUNDAMENTALS,  # 1 hour
                "sector_allocation": CacheTTL.YAHOO_SECTOR,  # 15 min
                "longterm_context": CacheTTL.LONGTERM_CONTEXT,  # 15 min
            }

        else:
            return {}

    @staticmethod
    def should_compute_intraday(trading_style: str) -> bool:
        """Check if intraday data should be computed."""
        return trading_style in ["intraday", "swing", "long_term"]

    @staticmethod
    def should_reuse_intraday(trading_style: str) -> bool:
        """Check if intraday data can be reused from cache."""
        return trading_style in ["swing", "long_term"]

    @staticmethod
    def should_compute_swing(trading_style: str) -> bool:
        """Check if swing data should be computed."""
        return trading_style in ["swing", "long_term"]

    @staticmethod
    def should_reuse_swing(trading_style: str) -> bool:
        """Check if swing data can be reused from cache."""
        return trading_style == "long_term"


# Cleanup configuration
class CleanupConfig:
    """Configuration for cache cleanup."""

    # Memory thresholds
    MAX_MEMORY_MB = 512  # Max Redis memory
    CLEANUP_THRESHOLD = 0.8  # Cleanup when 80% full

    # Cleanup patterns (delete oldest first)
    PRIORITY = [
        "composite:*",  # Composite data (can be regenerated)
        "calc:*",  # Calculated data (can be regenerated)
        "context:intraday:*",  # Intraday contexts (expire quickly anyway)
        "yahoo:sector:*",  # Sector data (changes slowly, can refetch)
        "context:swing:*",  # Swing contexts
        "context:longterm:*",  # Long-term contexts (least critical for cleanup)
    ]


# Export configuration
def get_cache_config() -> CacheConfig:
    """Get cache configuration."""
    return CacheConfig()
