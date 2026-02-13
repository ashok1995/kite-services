"""
Unit Tests for Market Breadth Service
======================================

Tests for market breadth calculation logic.
"""

import pytest
from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

from services.market_breadth_service import MarketBreadthService


class TestMarketBreadthService:
    """Tests for Market Breadth Service."""

    @pytest.fixture
    def mock_kite_client(self):
        """Create mock Kite client."""
        client = MagicMock()
        client.quote = AsyncMock()
        return client

    @pytest.fixture
    def service(self, mock_kite_client):
        """Create Market Breadth service with mock client."""
        return MarketBreadthService(mock_kite_client)

    @pytest.mark.asyncio
    async def test_service_initialization(self, service):
        """Test service initializes correctly."""
        assert service is not None
        assert service.enabled is True
        assert service.cache_ttl_seconds == 60
        assert service._cache is None
        assert service._cache_timestamp is None

    @pytest.mark.asyncio
    async def test_market_breadth_calculation_success(
        self, service, mock_kite_client
    ):
        """Test successful market breadth calculation."""
        # Mock quote response with advancing/declining stocks
        mock_kite_client.quote.return_value = {
            "NSE:RELIANCE": {"net_change_percent": 1.5},
            "NSE:TCS": {"net_change_percent": 0.8},
            "NSE:INFY": {"net_change_percent": 0.3},
            "NSE:HDFC": {"net_change_percent": -0.5},
            "NSE:SBIN": {"net_change_percent": -1.2},
            "NSE:ITC": {"net_change_percent": 0.005},  # Unchanged (< 0.01%)
        }

        breadth = await service.get_market_breadth()

        # Assertions
        assert breadth["advancing_stocks"] == 3
        assert breadth["declining_stocks"] == 2
        assert breadth["unchanged_stocks"] == 1
        assert breadth["total_stocks"] == 6
        assert breadth["advance_decline_ratio"] == Decimal("1.5")
        assert "timestamp" in breadth
        assert breadth["data_source"] == "nifty50_constituents"

    @pytest.mark.asyncio
    async def test_market_breadth_all_advancing(self, service, mock_kite_client):
        """Test breadth calculation when all stocks are advancing."""
        mock_kite_client.quote.return_value = {
            "NSE:RELIANCE": {"net_change_percent": 1.5},
            "NSE:TCS": {"net_change_percent": 2.0},
            "NSE:INFY": {"net_change_percent": 0.5},
        }

        breadth = await service.get_market_breadth()

        assert breadth["advancing_stocks"] == 3
        assert breadth["declining_stocks"] == 0
        assert breadth["unchanged_stocks"] == 0
        assert breadth["advance_decline_ratio"] == Decimal("3.0")  # All advancing

    @pytest.mark.asyncio
    async def test_market_breadth_all_declining(self, service, mock_kite_client):
        """Test breadth calculation when all stocks are declining."""
        mock_kite_client.quote.return_value = {
            "NSE:RELIANCE": {"net_change_percent": -1.5},
            "NSE:TCS": {"net_change_percent": -2.0},
            "NSE:INFY": {"net_change_percent": -0.5},
        }

        breadth = await service.get_market_breadth()

        assert breadth["advancing_stocks"] == 0
        assert breadth["declining_stocks"] == 3
        assert breadth["unchanged_stocks"] == 0
        assert breadth["advance_decline_ratio"] == Decimal("1.0")  # Default when 0/3

    @pytest.mark.asyncio
    async def test_market_breadth_caching(self, service, mock_kite_client):
        """Test that breadth data is cached correctly."""
        mock_kite_client.quote.return_value = {
            "NSE:RELIANCE": {"net_change_percent": 1.5},
            "NSE:TCS": {"net_change_percent": 0.8},
        }

        # First call - should fetch data
        breadth1 = await service.get_market_breadth()
        assert mock_kite_client.quote.call_count == 1

        # Second call - should use cache
        breadth2 = await service.get_market_breadth()
        assert mock_kite_client.quote.call_count == 1  # No additional call
        assert breadth1["timestamp"] == breadth2["timestamp"]

    @pytest.mark.asyncio
    async def test_market_breadth_force_refresh(self, service, mock_kite_client):
        """Test force refresh bypasses cache."""
        mock_kite_client.quote.return_value = {
            "NSE:RELIANCE": {"net_change_percent": 1.5},
        }

        # First call
        await service.get_market_breadth()
        assert mock_kite_client.quote.call_count == 1

        # Force refresh
        await service.get_market_breadth(force_refresh=True)
        assert mock_kite_client.quote.call_count == 2  # New call made

    @pytest.mark.asyncio
    async def test_market_breadth_no_quotes_returned(
        self, service, mock_kite_client
    ):
        """Test handling when no quotes are returned."""
        mock_kite_client.quote.return_value = None

        breadth = await service.get_market_breadth()

        # Should return default values
        assert breadth["advance_decline_ratio"] == Decimal("1.0")
        assert breadth["advancing_stocks"] == 0
        assert breadth["declining_stocks"] == 0
        assert breadth["data_source"] == "default"
        assert "message" in breadth

    @pytest.mark.asyncio
    async def test_market_breadth_api_error(self, service, mock_kite_client):
        """Test handling of API errors."""
        mock_kite_client.quote.side_effect = Exception("API Error")

        breadth = await service.get_market_breadth()

        # Should return default values with error message
        assert breadth["advance_decline_ratio"] == Decimal("1.0")
        assert breadth["data_source"] == "default"
        assert "message" in breadth
        assert "error" in breadth["message"].lower()

    @pytest.mark.asyncio
    async def test_market_breadth_missing_change_percent(
        self, service, mock_kite_client
    ):
        """Test handling of missing net_change_percent field."""
        mock_kite_client.quote.return_value = {
            "NSE:RELIANCE": {"last_price": 2500},  # No net_change_percent
            "NSE:TCS": {"net_change_percent": 1.5},
        }

        breadth = await service.get_market_breadth()

        # Should handle gracefully, counting failed symbol
        assert breadth["failed_symbols"] == 1
        assert breadth["advancing_stocks"] == 1
        assert breadth["total_stocks"] == 1

    @pytest.mark.asyncio
    async def test_market_breadth_threshold_boundaries(
        self, service, mock_kite_client
    ):
        """Test classification at threshold boundaries (0.01% threshold)."""
        mock_kite_client.quote.return_value = {
            "NSE:SYM1": {"net_change_percent": 0.011},  # Advancing
            "NSE:SYM2": {"net_change_percent": 0.009},  # Unchanged
            "NSE:SYM3": {"net_change_percent": -0.009},  # Unchanged
            "NSE:SYM4": {"net_change_percent": -0.011},  # Declining
        }

        breadth = await service.get_market_breadth()

        assert breadth["advancing_stocks"] == 1
        assert breadth["declining_stocks"] == 1
        assert breadth["unchanged_stocks"] == 2

    @pytest.mark.asyncio
    async def test_cache_invalidation(self, service, mock_kite_client):
        """Test manual cache invalidation."""
        mock_kite_client.quote.return_value = {
            "NSE:RELIANCE": {"net_change_percent": 1.5},
        }

        # Get data (caches it)
        await service.get_market_breadth()
        assert service._cache is not None

        # Invalidate cache
        service.invalidate_cache()
        assert service._cache is None
        assert service._cache_timestamp is None

        # Next call should fetch fresh data
        await service.get_market_breadth()
        assert mock_kite_client.quote.call_count == 2

    @pytest.mark.asyncio
    async def test_service_cleanup(self, service):
        """Test service cleanup."""
        service._cache = {"test": "data"}
        service._cache_timestamp = datetime.now()

        await service.cleanup()

        assert service._cache is None
        assert service._cache_timestamp is None

    @pytest.mark.asyncio
    async def test_breadth_disabled(self, mock_kite_client):
        """Test behavior when breadth calculation is disabled."""
        # Create service with mocked settings where enabled=False
        with patch("services.market_breadth_service.get_settings") as mock_settings:
            mock_settings.return_value.service.market_breadth_enabled = False
            mock_settings.return_value.service.market_breadth_cache_ttl = 60

            service = MarketBreadthService(mock_kite_client)
            breadth = await service.get_market_breadth()

            # Should return defaults without calling API
            assert breadth["data_source"] == "default"
            assert breadth["message"] == "Market breadth disabled"
            assert mock_kite_client.quote.call_count == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
