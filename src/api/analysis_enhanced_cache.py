"""
Enhanced Analysis Cache Keys
============================

Cache key generation for enhanced market context.
Uses time-based keys for primary (1min), detailed (5min), and style-specific contexts.
"""

from datetime import datetime


def get_cache_key_primary() -> str:
    """Get cache key for primary context (rounded to minute)."""
    now = datetime.now()
    return f"context:primary:{now.strftime('%Y%m%d_%H_%M')}"


def get_cache_key_detailed() -> str:
    """Get cache key for detailed context (rounded to 5 minutes)."""
    now = datetime.now()
    minute = (now.minute // 5) * 5
    return f"context:detailed:{now.strftime(f'%Y%m%d_%H_{minute:02d}')}"


def get_cache_key_intraday() -> str:
    """Get cache key for intraday composite (rounded to minute)."""
    now = datetime.now()
    return f"composite:intraday:{now.strftime('%Y%m%d_%H_%M')}"


def get_cache_key_swing() -> str:
    """Get cache key for swing composite (rounded to hour)."""
    now = datetime.now()
    return f"composite:swing:{now.strftime('%Y%m%d_%H')}"


def get_cache_key_longterm() -> str:
    """Get cache key for long-term composite (rounded to day)."""
    now = datetime.now()
    return f"composite:longterm:{now.strftime('%Y%m%d')}"
