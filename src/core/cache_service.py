"""
Redis Cache Service
===================

Intelligent caching service with hierarchical keys and smart TTL management.
"""

import json
import os
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Optional

try:
    import redis.asyncio as redis
    from redis.asyncio import ConnectionPool

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from config.cache_config import CacheConfig, CacheKeyPattern, CacheTTL
from core.logging_config import get_logger


class CacheService:
    """
    Intelligent caching service with:
    - Hierarchical cache keys
    - Smart TTL based on data volatility
    - Context-aware caching (reuse intraday for swing, etc.)
    - Automatic cleanup and expiration
    """

    def __init__(self, config: Optional[CacheConfig] = None):
        """Initialize cache service."""
        self.config = config or CacheConfig()
        self.logger = get_logger(__name__)
        self.redis: Optional[redis.Redis] = None
        self.pool: Optional[ConnectionPool] = None
        self.enabled = self.config.enabled and REDIS_AVAILABLE

        if not REDIS_AVAILABLE:
            self.logger.warning(
                "Redis not available - caching disabled. Install: pip install redis"
            )
            self.enabled = False

    async def initialize(self):
        """Initialize Redis connection pool."""
        if not self.enabled:
            self.logger.info("Cache service disabled")
            return

        try:
            # Prefer env vars (Docker/compose inject these; config may not pick nested)
            host = os.environ.get("REDIS_HOST", self.config.host)
            port = int(os.environ.get("REDIS_PORT", self.config.port))
            # Create connection pool
            self.pool = ConnectionPool(
                host=host,
                port=port,
                db=self.config.db,
                password=self.config.password,
                max_connections=self.config.max_connections,
                socket_timeout=self.config.socket_timeout,
                socket_connect_timeout=self.config.socket_connect_timeout,
                decode_responses=True,  # Auto-decode bytes to strings
            )

            # Create Redis client
            self.redis = redis.Redis(connection_pool=self.pool)

            # Test connection
            await self.redis.ping()

            self.logger.info(
                f"✅ Cache service initialized (Redis {self.config.host}:{self.config.port})"
            )

        except Exception as e:
            self.logger.error(f"Failed to initialize cache: {e}")
            self.enabled = False

    async def cleanup(self):
        """Cleanup Redis connections."""
        if self.redis:
            await self.redis.close()
        if self.pool:
            await self.pool.disconnect()
        self.logger.info("Cache service cleaned up")

    def _make_key(self, pattern: str, **kwargs) -> str:
        """
        Create cache key from pattern.

        Args:
            pattern: Key pattern (e.g., "kite:quote:{symbol}")
            **kwargs: Values to substitute

        Returns:
            Complete cache key with prefix
        """
        key = pattern.format(**kwargs)
        return f"{self.config.key_prefix}{key}"

    def _serialize(self, value: Any) -> str:
        """
        Serialize value for caching.

        Handles:
        - Pydantic models
        - Decimals
        - Datetime objects
        - Regular dicts/lists
        """

        def default_serializer(obj):
            if isinstance(obj, Decimal):
                return str(obj)
            elif isinstance(obj, datetime):
                return obj.isoformat()
            elif hasattr(obj, "dict"):  # Pydantic model
                return obj.dict()
            elif hasattr(obj, "__dict__"):
                return obj.__dict__
            raise TypeError(f"Cannot serialize {type(obj)}")

        return json.dumps(value, default=default_serializer)

    def _deserialize(self, value: str) -> Any:
        """Deserialize cached value."""
        if value is None:
            return None
        return json.loads(value)

    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        if not self.enabled or not self.redis:
            return None

        try:
            value = await self.redis.get(key)
            if value:
                self.logger.debug(f"Cache HIT: {key}")
                return self._deserialize(value)
            else:
                self.logger.debug(f"Cache MISS: {key}")
                return None
        except Exception as e:
            self.logger.error(f"Cache get error for {key}: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None, nx: bool = False) -> bool:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (None = default)
            nx: Only set if key doesn't exist

        Returns:
            True if successful
        """
        if not self.enabled or not self.redis:
            return False

        try:
            ttl = ttl or self.config.default_ttl
            serialized = self._serialize(value)

            await self.redis.set(key, serialized, ex=ttl, nx=nx)

            self.logger.debug(f"Cache SET: {key} (TTL={ttl}s)")
            return True

        except Exception as e:
            self.logger.error(f"Cache set error for {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if not self.enabled or not self.redis:
            return False

        try:
            await self.redis.delete(key)
            self.logger.debug(f"Cache DELETE: {key}")
            return True
        except Exception as e:
            self.logger.error(f"Cache delete error for {key}: {e}")
            return False

    async def delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching pattern.

        Args:
            pattern: Pattern to match (e.g., "context:intraday:*")

        Returns:
            Number of keys deleted
        """
        if not self.enabled or not self.redis:
            return 0

        try:
            full_pattern = f"{self.config.key_prefix}{pattern}"
            keys = []

            # Scan for matching keys
            async for key in self.redis.scan_iter(match=full_pattern):
                keys.append(key)

            if keys:
                deleted = await self.redis.delete(*keys)
                self.logger.info(f"Cache DELETE pattern '{pattern}': {deleted} keys")
                return deleted
            return 0

        except Exception as e:
            self.logger.error(f"Cache delete pattern error for {pattern}: {e}")
            return 0

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        if not self.enabled or not self.redis:
            return False

        try:
            return await self.redis.exists(key) > 0
        except Exception as e:
            self.logger.error(f"Cache exists error for {key}: {e}")
            return False

    async def get_ttl(self, key: str) -> int:
        """Get remaining TTL for key in seconds."""
        if not self.enabled or not self.redis:
            return -1

        try:
            return await self.redis.ttl(key)
        except Exception as e:
            self.logger.error(f"Cache TTL error for {key}: {e}")
            return -1

    # High-level cache methods for specific data types

    async def get_market_index(self, symbol: str) -> Optional[Dict]:
        """Get cached market index data."""
        key = self._make_key(CacheKeyPattern.MARKET_INDEX, symbol=symbol)
        return await self.get(key)

    async def set_market_index(self, symbol: str, data: Dict) -> bool:
        """Cache market index data."""
        key = self._make_key(CacheKeyPattern.MARKET_INDEX, symbol=symbol)
        return await self.set(key, data, ttl=CacheTTL.MARKET_INDEX)

    async def get_kite_quote(self, symbol: str) -> Optional[Dict]:
        """Get cached Kite quote."""
        key = self._make_key(CacheKeyPattern.KITE_QUOTE, symbol=symbol)
        return await self.get(key)

    async def set_kite_quote(self, symbol: str, data: Dict) -> bool:
        """Cache Kite quote."""
        key = self._make_key(CacheKeyPattern.KITE_QUOTE, symbol=symbol)
        return await self.set(key, data, ttl=CacheTTL.KITE_QUOTE)

    async def get_yahoo_sector(self, sector: str) -> Optional[Dict]:
        """Get cached Yahoo sector data."""
        key = self._make_key(CacheKeyPattern.YAHOO_SECTOR, sector=sector)
        return await self.get(key)

    async def set_yahoo_sector(self, sector: str, data: Dict) -> bool:
        """Cache Yahoo sector data."""
        key = self._make_key(CacheKeyPattern.YAHOO_SECTOR, sector=sector)
        return await self.set(key, data, ttl=CacheTTL.YAHOO_SECTOR)

    async def get_composite_intraday(self, timestamp_bucket: str) -> Optional[Dict]:
        """
        Get composite intraday data (can be reused by swing).

        Args:
            timestamp_bucket: Format "YYYYMMDD_HH_MM" (rounded to minute)
        """
        date, hour, minute = timestamp_bucket.split("_")
        key = self._make_key(
            CacheKeyPattern.COMPOSITE_INTRADAY, date=date, hour=hour, minute=minute
        )
        return await self.get(key)

    async def set_composite_intraday(self, timestamp_bucket: str, data: Dict) -> bool:
        """Cache composite intraday data."""
        date, hour, minute = timestamp_bucket.split("_")
        key = self._make_key(
            CacheKeyPattern.COMPOSITE_INTRADAY, date=date, hour=hour, minute=minute
        )
        return await self.set(key, data, ttl=CacheTTL.COMPOSITE_INTRADAY)

    async def get_composite_swing(self, timestamp_bucket: str) -> Optional[Dict]:
        """
        Get composite swing data (can be reused by long-term).

        Args:
            timestamp_bucket: Format "YYYYMMDD_HH" (rounded to hour)
        """
        date, hour = timestamp_bucket.split("_")
        key = self._make_key(CacheKeyPattern.COMPOSITE_SWING, date=date, hour=hour)
        return await self.get(key)

    async def set_composite_swing(self, timestamp_bucket: str, data: Dict) -> bool:
        """Cache composite swing data."""
        date, hour = timestamp_bucket.split("_")
        key = self._make_key(CacheKeyPattern.COMPOSITE_SWING, date=date, hour=hour)
        return await self.set(key, data, ttl=CacheTTL.COMPOSITE_SWING)

    # Utility methods

    @staticmethod
    def get_timestamp_bucket(level: str = "minute") -> str:
        """
        Get timestamp bucket for cache key.

        Args:
            level: "minute" for intraday, "hour" for swing, "day" for long-term

        Returns:
            Timestamp bucket string
        """
        now = datetime.now()

        if level == "minute":
            # Round to minute: YYYYMMDD_HH_MM
            return now.strftime("%Y%m%d_%H_%M")
        elif level == "hour":
            # Round to hour: YYYYMMDD_HH
            return now.strftime("%Y%m%d_%H")
        elif level == "day":
            # Round to day: YYYYMMDD
            return now.strftime("%Y%m%d")
        else:
            return now.strftime("%Y%m%d_%H_%M")

    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        if not self.enabled or not self.redis:
            return {"enabled": False}

        try:
            info = await self.redis.info("stats")
            memory = await self.redis.info("memory")

            return {
                "enabled": True,
                "total_keys": await self.redis.dbsize(),
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0),
                "hit_rate": self._calculate_hit_rate(info),
                "memory_used_mb": memory.get("used_memory", 0) / 1024 / 1024,
                "memory_peak_mb": memory.get("used_memory_peak", 0) / 1024 / 1024,
            }
        except Exception as e:
            self.logger.error(f"Error getting cache stats: {e}")
            return {"enabled": True, "error": str(e)}

    def _calculate_hit_rate(self, info: Dict) -> float:
        """Calculate cache hit rate."""
        hits = info.get("keyspace_hits", 0)
        misses = info.get("keyspace_misses", 0)
        total = hits + misses
        return (hits / total * 100) if total > 0 else 0.0

    async def cleanup_expired(self):
        """Cleanup expired keys (Redis handles this automatically, but we can trigger it)."""
        if not self.enabled or not self.redis:
            return

        try:
            # Get memory info
            memory = await self.redis.info("memory")
            used_memory_mb = memory.get("used_memory", 0) / 1024 / 1024

            self.logger.info(f"Cache cleanup check: {used_memory_mb:.2f}MB used")

            # If memory usage is high, could implement custom cleanup here
            # For now, rely on Redis LRU eviction

        except Exception as e:
            self.logger.error(f"Cleanup error: {e}")


# Global cache service instance
_cache_service: Optional[CacheService] = None


async def get_cache_service() -> CacheService:
    """Get global cache service instance."""
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
        await _cache_service.initialize()
    return _cache_service
