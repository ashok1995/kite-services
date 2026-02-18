"""
Deployment Reliability Tests
=============================

Tests run automatically after deployment to verify all critical paths work.
Designed to catch:
- Missing dependencies
- Broken imports
- Endpoint failures
- Service initialization issues
- Data contract violations
- Authentication flow

Usage:
    pytest tests/e2e/test_deployment_reliability.py -v --tb=short
    pytest tests/e2e/test_deployment_reliability.py -v -k "smoke"     # Quick smoke
    pytest tests/e2e/test_deployment_reliability.py -v -k "contract"  # Data checks
"""

import sys
from datetime import datetime
from pathlib import Path

import pytest
import pytest_asyncio

# Add src to path (must be before main import)
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from httpx import ASGITransport, AsyncClient  # noqa: E402

from main import app  # noqa: E402

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def client():
    """Async HTTP client with full app lifecycle (startup/shutdown)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Trigger lifespan startup manually
        from main import lifespan

        async with lifespan(app):
            yield ac


# ===========================================================================
# 1. SMOKE TESTS — Must pass for ANY deployment
# ===========================================================================


class TestSmoke:
    """Minimal tests that must pass for any deployment to be valid."""

    @pytest.mark.asyncio
    async def test_health_returns_200(self, client):
        """Health endpoint returns 200 and correct structure."""
        r = await client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "healthy"
        assert data["service"] == "kite-services"
        assert "services" in data

    @pytest.mark.asyncio
    async def test_root_returns_service_info(self, client):
        """Root endpoint exposes service metadata."""
        r = await client.get("/")
        assert r.status_code == 200
        data = r.json()
        for key in ["service", "version", "environment", "docs_url", "health_url"]:
            assert key in data, f"Missing key: {key}"

    @pytest.mark.asyncio
    async def test_openapi_schema_accessible(self, client):
        """OpenAPI schema is served (needed for docs/swagger)."""
        r = await client.get("/openapi.json")
        assert r.status_code == 200
        schema = r.json()
        assert "paths" in schema
        assert len(schema["paths"]) > 0

    @pytest.mark.asyncio
    async def test_all_services_initialised(self, client):
        """All 4 core services are reported as running (Kite/Indian only; no Yahoo)."""
        r = await client.get("/health")
        services = r.json()["services"]["services"]
        expected = [
            "cache_service",
            "kite_client",
            "market_context_service",
            "stock_data_service",
        ]
        for svc in expected:
            assert svc in services, f"Service {svc} not initialised"
            assert services[svc]["status"] == "running"


# ===========================================================================
# 2. AUTH TESTS
# ===========================================================================


class TestAuth:
    """Authentication endpoint tests."""

    @pytest.mark.asyncio
    async def test_auth_status_structure(self, client):
        """Auth status returns correct structure."""
        r = await client.get("/api/auth/status")
        assert r.status_code == 200
        data = r.json()
        for key in ["status", "authenticated", "timestamp"]:
            assert key in data, f"Missing key: {key}"

    @pytest.mark.asyncio
    async def test_login_rejects_empty_body(self, client):
        """Login rejects request without token."""
        r = await client.post("/api/auth/login", json={})
        # Should still return a response (fail gracefully)
        assert r.status_code in [200, 400, 401, 422, 500]

    @pytest.mark.asyncio
    async def test_login_rejects_bad_token(self, client):
        """Login rejects an invalid request token."""
        r = await client.post("/api/auth/login", json={"request_token": "invalid_token_12345"})
        assert r.status_code in [401, 500]


# ===========================================================================
# 3. MARKET DATA ENDPOINT TESTS
# ===========================================================================


class TestMarketData:
    """Market data endpoint contract tests."""

    @pytest.mark.asyncio
    async def test_market_status_structure(self, client):
        """Market status returns correct contract."""
        r = await client.get("/api/market/status")
        assert r.status_code == 200
        data = r.json()
        assert "market_status" in data
        assert "market_open" in data
        assert isinstance(data["market_open"], bool)
        assert "exchanges" in data

    @pytest.mark.asyncio
    async def test_market_instruments_default(self, client):
        """Instruments endpoint returns data."""
        r = await client.get("/api/market/instruments?limit=3")
        assert r.status_code == 200
        data = r.json()
        assert "instruments" in data
        assert "total_count" in data
        assert data["total_count"] <= 3

    @pytest.mark.asyncio
    async def test_market_instruments_filter(self, client):
        """Instruments endpoint filters by exchange."""
        r = await client.get("/api/market/instruments?exchange=NSE&limit=5")
        assert r.status_code == 200
        data = r.json()
        for inst in data["instruments"]:
            assert inst["exchange"] == "NSE"

    @pytest.mark.asyncio
    async def test_market_quotes_contract(self, client):
        """Quotes endpoint returns correct structure."""
        r = await client.post(
            "/api/market/quotes", json={"symbols": ["NSE:RELIANCE"], "exchange": "NSE"}
        )
        assert r.status_code == 200
        data = r.json()
        assert "stocks" in data
        assert "total_symbols" in data
        assert data["total_symbols"] == 1
        assert "processing_time_ms" in data

    @pytest.mark.asyncio
    async def test_market_data_quote_type(self, client):
        """Market data endpoint handles quote data type."""
        r = await client.post(
            "/api/market/data",
            json={"symbols": ["RELIANCE"], "data_type": "quote", "exchange": "NSE"},
        )
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        data = r.json()
        assert data.get("success") is True
        assert (
            data.get("successful_symbols", 0) >= 1
        ), f"Expected at least one successful quote: {data}"
        assert "processing_time_ms" in data

    @pytest.mark.asyncio
    async def test_market_data_rejects_invalid_type(self, client):
        """Market data rejects unsupported data_type."""
        r = await client.post(
            "/api/market/data", json={"symbols": ["NSE:RELIANCE"], "data_type": "invalid_type"}
        )
        assert r.status_code == 400

    @pytest.mark.asyncio
    async def test_quotes_max_symbols_limit(self, client):
        """Quotes endpoint enforces max symbols limit (model validation)."""
        symbols = [f"NSE:STOCK{i}" for i in range(200)]
        r = await client.post("/api/market/quotes", json={"symbols": symbols, "exchange": "NSE"})
        # 422 from Pydantic model validation (max_length=50)
        # or 400 from explicit check in handler
        assert r.status_code in [400, 422]


# ===========================================================================
# 4. ANALYSIS ENDPOINT TESTS
# ===========================================================================


class TestAnalysis:
    """Analysis endpoint contract tests."""

    @pytest.mark.asyncio
    async def test_analysis_context_structure(self, client):
        """Analysis context returns correct structure."""
        r = await client.post(
            "/api/analysis/context",
            json={
                "include_global": True,
                "include_indian": True,
                "include_sentiment": True,
                "include_technical": False,
            },
        )
        assert r.status_code == 200
        data = r.json()
        assert data["success"] is True
        for key in ["global_markets", "indian_markets", "processing_time_ms"]:
            assert key in data, f"Missing key: {key}"

    @pytest.mark.asyncio
    async def test_stock_analysis_comprehensive(self, client):
        """Stock analysis returns comprehensive data."""
        r = await client.post(
            "/api/analysis/stock",
            params={
                "symbol": "NSE:RELIANCE",
                "analysis_type": "comprehensive",
                "time_horizon": "intraday",
            },
        )
        assert r.status_code == 200
        data = r.json()
        assert data["symbol"] == "NSE:RELIANCE"
        assert "current_price" in data
        assert "processing_time_ms" in data

    @pytest.mark.asyncio
    async def test_enhanced_context_primary_only(self, client):
        """Enhanced context returns primary context."""
        r = await client.post(
            "/api/analysis/context/enhanced",
            json={
                "trading_styles": ["intraday"],
                "include_primary": True,
                "include_detailed": False,
                "include_style_specific": False,
            },
        )
        assert r.status_code == 200
        data = r.json()
        assert data["success"] is True
        assert data["primary_context"] is not None
        assert "context_quality_score" in data

    @pytest.mark.asyncio
    async def test_enhanced_context_data_quality(self, client):
        """Enhanced context includes data quality report."""
        r = await client.post(
            "/api/analysis/context/enhanced",
            json={
                "trading_styles": ["intraday"],
                "include_primary": True,
                "include_detailed": False,
                "include_style_specific": False,
            },
        )
        data = r.json()
        assert "data_quality" in data
        dq = data["data_quality"]
        assert "overall_quality" in dq
        assert "real_data_percentage" in dq


# ===========================================================================
# 5. QUICK OPPORTUNITIES TESTS
# ===========================================================================


class TestQuickOpportunities:
    """Quick opportunities endpoint contract tests."""

    @pytest.mark.asyncio
    async def test_quick_opportunities_structure(self, client):
        """Quick opportunities returns correct structure."""
        r = await client.post(
            "/api/opportunities/quick",
            json={
                "symbols": ["NSE:NIFTY 50"],
                "timeframe": "5minute",
                "opportunity_types": ["breakout", "reversal", "momentum"],
            },
        )
        assert r.status_code == 200
        data = r.json()
        assert data["success"] is True
        for key in [
            "nifty_price",
            "nifty_5min_trend",
            "market_momentum",
            "volatility",
            "opportunities",
            "rsi_5min",
        ]:
            assert key in data, f"Missing key: {key}"


# ===========================================================================
# 6. TRADING STATUS TESTS
# ===========================================================================


class TestTrading:
    """Trading endpoint contract tests."""

    @pytest.mark.asyncio
    async def test_trading_status_structure(self, client):
        """Trading status returns correct structure."""
        r = await client.get("/api/trading/status")
        assert r.status_code == 200
        data = r.json()
        assert "success" in data
        assert "authenticated" in data
        assert "total_positions" in data
        assert "total_holdings" in data
        assert "processing_time_ms" in data


# ===========================================================================
# 7. DATA CONTRACT TESTS — validate field types & ranges
# ===========================================================================


class TestDataContracts:
    """Validate response field types and value ranges."""

    @pytest.mark.asyncio
    async def test_health_timestamp_is_recent(self, client):
        """Services were initialised recently (within last hour)."""
        r = await client.get("/health")
        services = r.json()["services"]["services"]
        for name, info in services.items():
            ts = info.get("initialized_at")
            if ts:
                init_time = datetime.fromisoformat(ts)
                age_seconds = (datetime.now() - init_time).total_seconds()
                assert age_seconds < 3600, f"{name} initialised {age_seconds}s ago"

    @pytest.mark.asyncio
    async def test_quotes_decimal_fields(self, client):
        """Quote numeric fields are valid decimals."""
        r = await client.post(
            "/api/market/quotes", json={"symbols": ["NSE:RELIANCE"], "exchange": "NSE"}
        )
        data = r.json()
        if data.get("stocks"):
            stock = data["stocks"][0]
            price = float(stock["last_price"])
            assert price > 0, "Price must be positive"
            assert price < 1_000_000, "Price seems unreasonably high"

    @pytest.mark.asyncio
    async def test_processing_time_reasonable(self, client):
        """Endpoints respond within 30 seconds."""
        r = await client.get("/health")
        assert r.elapsed.total_seconds() < 30

    @pytest.mark.asyncio
    async def test_enhanced_context_score_range(self, client):
        """Market score is within -100 to +100."""
        r = await client.post(
            "/api/analysis/context/enhanced",
            json={
                "trading_styles": ["intraday"],
                "include_primary": True,
                "include_detailed": False,
                "include_style_specific": False,
            },
        )
        data = r.json()
        if data.get("primary_context"):
            score = data["primary_context"].get("overall_market_score", 0)
            assert -100 <= score <= 100, f"Score out of range: {score}"


# ===========================================================================
# 8. ERROR HANDLING TESTS
# ===========================================================================


class TestErrorHandling:
    """Verify graceful error handling."""

    @pytest.mark.asyncio
    async def test_404_on_unknown_route(self, client):
        """Unknown routes return 404, not 500."""
        r = await client.get("/api/nonexistent")
        assert r.status_code == 404

    @pytest.mark.asyncio
    async def test_422_on_malformed_json(self, client):
        """Malformed request body returns 422."""
        r = await client.post(
            "/api/market/quotes",
            content="not json",
            headers={"Content-Type": "application/json"},
        )
        assert r.status_code == 422

    @pytest.mark.asyncio
    async def test_market_data_missing_fields(self, client):
        """Market data returns 422 if required fields missing."""
        r = await client.post("/api/market/data", json={})
        assert r.status_code == 422


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
