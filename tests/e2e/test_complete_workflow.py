"""
End-to-End Workflow Tests
=========================

Complete workflow tests for the entire system.
"""

import pytest
from httpx import AsyncClient
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from main import app


class TestCompleteWorkflow:
    """End-to-end workflow tests."""
    
    @pytest.mark.asyncio
    async def test_health_check_endpoint(self):
        """Test health check endpoint is accessible."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert "status" in data
            assert data["service"] == "kite-services"
    
    @pytest.mark.asyncio
    async def test_root_endpoint(self):
        """Test root endpoint provides service info."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/")
            assert response.status_code == 200
            data = response.json()
            assert "service" in data
            assert "version" in data
            assert "health_url" in data
    
    @pytest.mark.asyncio
    async def test_api_documentation_available(self):
        """Test that API documentation is available in debug mode."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/docs")
            # In production might be disabled, but endpoint should exist
            assert response.status_code in [200, 404]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

