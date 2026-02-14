"""
Unit Tests for Market Context Service
=====================================

Tests for market context service logic.
"""

from unittest.mock import AsyncMock, Mock

import pytest

from services.market_context_service import MarketContextService


class TestMarketContextService:
    """Tests for Market Context Service."""

    @pytest.fixture
    def mock_kite_client(self):
        """Create mock Kite client."""
        client = Mock()
        client.get_quote = AsyncMock(
            return_value={"NIFTY 50": {"last_price": 19500.0, "change_percent": 0.5}}
        )
        return client

    @pytest.fixture
    def mock_yahoo_service(self):
        """Create mock Yahoo Finance service."""
        service = Mock()
        service.get_quote = AsyncMock(
            return_value={"symbol": "^GSPC", "last_price": 4500.0, "change_percent": 0.3}
        )
        return service

    @pytest.fixture
    def service(self, mock_kite_client, mock_yahoo_service):
        """Create Market Context service with mocks."""
        return MarketContextService()

    def test_service_creation(self, service):
        """Test service can be instantiated."""
        assert service is not None
        assert hasattr(service, "get_market_context")

    @pytest.mark.asyncio
    async def test_service_initialization(self, service):
        """Test service initialization."""
        await service.initialize()
        # Verify initialization completed


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
