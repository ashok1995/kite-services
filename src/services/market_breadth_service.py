"""
Market Breadth Service
======================

Calculates market breadth metrics (advance/decline ratio, advancing/declining stocks).
Used for market context enrichment in Bayesian engine integration.

Following workspace rules:
- Stateless service logic
- Dependency injection
- Comprehensive logging
- 60-second caching for performance
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Dict, Optional

from common.constants import EXCHANGE_PREFIX, NIFTY_50_CONSTITUENTS
from config.settings import get_settings
from core.kite_client import KiteClient
from core.logging_config import get_logger


class MarketBreadthService:
    """Service for calculating market breadth metrics from Nifty 50 constituents."""

    def __init__(self, kite_client: KiteClient, logger: Optional[logging.Logger] = None):
        """Initialize market breadth service.

        Args:
            kite_client: Kite Connect client for fetching quotes
            logger: Optional logger instance
        """
        self.kite_client = kite_client
        self.logger = logger or get_logger(__name__)

        # Get settings
        settings = get_settings()
        self.enabled = settings.service.market_breadth_enabled
        self.cache_ttl_seconds = settings.service.market_breadth_cache_ttl

        # Cache
        self._cache: Optional[Dict] = None
        self._cache_timestamp: Optional[datetime] = None

        self.logger.info(
            "MarketBreadthService initialized",
            extra={
                "service": "market_breadth_service",
                "enabled": self.enabled,
                "cache_ttl": self.cache_ttl_seconds,
                "constituents_count": len(NIFTY_50_CONSTITUENTS),
            },
        )

    async def get_market_breadth(self, force_refresh: bool = False) -> Dict:
        """Get market breadth metrics.

        Calculates advance/decline ratio from Nifty 50 constituents.
        Results are cached for 60 seconds by default.

        Args:
            force_refresh: Force refresh cache (bypass TTL)

        Returns:
            Dict with breadth metrics:
            {
                "advance_decline_ratio": Decimal,
                "advancing_stocks": int,
                "declining_stocks": int,
                "unchanged_stocks": int,
                "total_stocks": int,
                "timestamp": datetime,
                "data_source": str
            }
        """
        if not self.enabled:
            self.logger.debug("Market breadth calculation disabled")
            return self._get_default_breadth(message="Market breadth disabled")

        # Check cache
        if not force_refresh and self._is_cache_valid():
            self.logger.debug(
                "Returning cached market breadth data",
                extra={
                    "cache_age_seconds": self._get_cache_age(),
                    "cache_ttl": self.cache_ttl_seconds,
                },
            )
            return self._cache

        try:
            # Fetch Nifty 50 quotes
            self.logger.info(
                "Fetching Nifty 50 quotes for breadth calculation",
                extra={"symbols_count": len(NIFTY_50_CONSTITUENTS)},
            )

            nse_prefix = EXCHANGE_PREFIX.get("NSE", "NSE:")
            nse_symbols = [f"{nse_prefix}{symbol}" for symbol in NIFTY_50_CONSTITUENTS]

            quotes = await self.kite_client.quote(nse_symbols)

            if not quotes:
                self.logger.warning(
                    "No quotes returned for Nifty 50 constituents",
                    extra={"requested_symbols": len(nse_symbols)},
                )
                return self._get_default_breadth(message="No quote data available")

            # Calculate breadth metrics
            advancing = 0
            declining = 0
            unchanged = 0
            failed = 0

            for symbol_key, quote_data in quotes.items():
                if not quote_data:
                    failed += 1
                    continue

                # Calculate change_percent from last_price and close (Kite doesn't provide net_change_percent)
                last_price = quote_data.get("last_price", 0)
                close_price = quote_data.get("ohlc", {}).get("close", 0)

                if not last_price or not close_price or close_price == 0:
                    failed += 1
                    continue

                change_percent = ((last_price - close_price) / close_price) * 100

                # Classify as advancing/declining/unchanged
                if change_percent > 0.01:  # >0.01% threshold to avoid noise
                    advancing += 1
                elif change_percent < -0.01:  # <-0.01% threshold
                    declining += 1
                else:
                    unchanged += 1

            total = advancing + declining + unchanged

            # Calculate advance/decline ratio (handle division by zero)
            if declining > 0:
                ad_ratio = Decimal(str(advancing / declining))
            elif advancing > 0:
                ad_ratio = Decimal(str(advancing))  # All advancing, no declining
            else:
                ad_ratio = Decimal("1.0")  # No movement

            breadth_data = {
                "advance_decline_ratio": round(ad_ratio, 2),
                "advancing_stocks": advancing,
                "declining_stocks": declining,
                "unchanged_stocks": unchanged,
                "total_stocks": total,
                "failed_symbols": failed,
                "timestamp": datetime.now(),
                "data_source": "nifty50_constituents",
            }

            # Update cache
            self._cache = breadth_data
            self._cache_timestamp = datetime.now()

            self.logger.info(
                "Market breadth calculated successfully",
                extra={
                    "advancing": advancing,
                    "declining": declining,
                    "unchanged": unchanged,
                    "failed": failed,
                    "total": total,
                    "ad_ratio": float(ad_ratio),
                    "cached": True,
                },
            )

            return breadth_data

        except Exception as e:
            self.logger.error(
                "Failed to calculate market breadth",
                extra={"error": str(e), "error_type": type(e).__name__},
                exc_info=True,
            )
            return self._get_default_breadth(message=f"Calculation error: {str(e)}")

    def _is_cache_valid(self) -> bool:
        """Check if cached data is still valid based on TTL.

        Returns:
            True if cache is valid, False otherwise
        """
        if not self._cache or not self._cache_timestamp:
            return False

        age_seconds = self._get_cache_age()
        return age_seconds < self.cache_ttl_seconds

    def _get_cache_age(self) -> float:
        """Get cache age in seconds.

        Returns:
            Cache age in seconds, or infinity if no cache
        """
        if not self._cache_timestamp:
            return float("inf")

        return (datetime.now() - self._cache_timestamp).total_seconds()

    def _get_default_breadth(self, message: str = "Data unavailable") -> Dict:
        """Return default breadth data when calculation fails or is disabled.

        Args:
            message: Reason for default data

        Returns:
            Default breadth data dictionary
        """
        self.logger.debug(f"Returning default breadth data: {message}")

        return {
            "advance_decline_ratio": Decimal("1.0"),
            "advancing_stocks": 0,
            "declining_stocks": 0,
            "unchanged_stocks": 0,
            "total_stocks": 0,
            "failed_symbols": 0,
            "timestamp": datetime.now(),
            "data_source": "default",
            "message": message,
        }

    def invalidate_cache(self):
        """Manually invalidate cache to force refresh on next call."""
        self._cache = None
        self._cache_timestamp = None
        self.logger.debug("Market breadth cache invalidated")

    async def cleanup(self):
        """Cleanup service resources."""
        self._cache = None
        self._cache_timestamp = None
        self.logger.info("MarketBreadthService cleanup complete")
