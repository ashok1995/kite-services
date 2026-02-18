"""
Unit Tests for Market Context Service
=====================================

Tests for market context service (Kite only; no Yahoo).
"""

from unittest.mock import AsyncMock, Mock

import pytest

from services.market_context_service import MarketContextService


class TestMarketContextService:
    """Tests for Market Context Service (Indian/Kite only)."""

    @pytest.fixture
    def mock_kite_client(self):
        """Create mock Kite client."""
        client = Mock()
        client.quote = AsyncMock(
            return_value={
                "NSE:NIFTY 50": {"last_price": 19500.0, "net_change": 100, "ohlc": {"close": 19400}}
            }
        )
        return client

    @pytest.fixture
    def service(self, mock_kite_client):
        """Create Market Context service with Kite mock only."""
        return MarketContextService(kite_client=mock_kite_client)

    def test_service_creation(self, service):
        """Test service can be instantiated."""
        assert service is not None
        assert hasattr(service, "get_market_breadth")
        assert hasattr(service, "get_indian_market_data")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
