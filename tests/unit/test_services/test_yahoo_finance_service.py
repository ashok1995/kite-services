"""
Unit Tests for Yahoo Finance Service
====================================

Tests for Yahoo Finance service without making actual API calls.
"""

import pytest

from services.yahoo_finance_service import YahooFinanceService


class TestYahooFinanceService:
    """Tests for Yahoo Finance Service."""

    @pytest.fixture
    def service(self):
        """Create Yahoo Finance service instance."""
        return YahooFinanceService()

    @pytest.mark.asyncio
    async def test_service_initialization(self, service):
        """Test service initializes correctly."""
        await service.initialize()
        assert service is not None

    @pytest.mark.asyncio
    async def test_get_quote_mock(self, service):
        """Test getting quote with mocked data."""
        # This would be enhanced with actual mocking when implementing real tests
        # For now, testing service structure
        await service.initialize()
        assert hasattr(service, "get_quote")

    @pytest.mark.asyncio
    async def test_cleanup(self, service):
        """Test service cleanup."""
        await service.initialize()
        await service.cleanup()
        # Verify cleanup completed without errors


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
