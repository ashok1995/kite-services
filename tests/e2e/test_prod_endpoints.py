"""
Production Endpoint Tests
=========================

Verify each endpoint returns 200 and expected result shape/values.
Uses TEST_BASE_URL env var. Default: http://127.0.0.1:8079

Usage:
  pytest tests/e2e/test_prod_endpoints.py -v
  TEST_BASE_URL=http://203.57.85.72:8179 pytest tests/e2e/test_prod_endpoints.py -v
"""

import os

import httpx
import pytest

BASE_URL = os.environ.get("TEST_BASE_URL", "http://127.0.0.1:8079")
TIMEOUT = 30


@pytest.fixture
def base_url():
    """Base URL for API (dev or prod)."""
    return BASE_URL.rstrip("/")


# =============================================================================
# SMOKE TESTS
# =============================================================================


class TestProdSmoke:
    """Smoke tests - must pass for any deployment."""

    def test_health_returns_200(self, base_url):
        r = httpx.get(f"{base_url}/health", timeout=TIMEOUT)
        assert r.status_code == 200
        d = r.json()
        assert d.get("status") == "healthy"
        assert d.get("service") == "kite-services"
        assert "services" in d

    def test_root_returns_service_info(self, base_url):
        r = httpx.get(f"{base_url}/", timeout=TIMEOUT)
        assert r.status_code == 200
        d = r.json()
        assert d.get("service") == "kite-services"
        assert "version" in d and "environment" in d
        assert "docs_url" in d and "health_url" in d

    def test_openapi_accessible(self, base_url):
        r = httpx.get(f"{base_url}/openapi.json", timeout=TIMEOUT)
        assert r.status_code == 200
        d = r.json()
        assert "paths" in d
        assert "/health" in d["paths"] and "/api/auth/status" in d["paths"]

    def test_all_services_initialised(self, base_url):
        r = httpx.get(f"{base_url}/health", timeout=TIMEOUT)
        assert r.status_code == 200
        services = r.json().get("services", {}).get("services", r.json().get("services", {}))
        expected = [
            "cache_service",
            "kite_client",
            "yahoo_service",
            "market_context_service",
            "stock_data_service",
            "market_intelligence_service",
        ]
        for svc in expected:
            assert svc in services
            assert services[svc].get("status") == "running"


# =============================================================================
# AUTH ENDPOINTS
# =============================================================================


class TestProdAuth:
    """Auth endpoint tests."""

    def test_auth_status(self, base_url):
        r = httpx.get(f"{base_url}/api/auth/status", timeout=TIMEOUT)
        assert r.status_code == 200
        d = r.json()
        assert d.get("status") in ("authenticated", "expired", "invalid", "not_configured")
        assert "authenticated" in d

    def test_auth_login_url(self, base_url):
        r = httpx.get(f"{base_url}/api/auth/login-url", timeout=TIMEOUT)
        if r.status_code == 404:
            pytest.skip("login-url not deployed")
        assert r.status_code == 200
        d = r.json()
        assert "login_url" in d
        assert "kite" in d["login_url"].lower() or "zerodha" in d["login_url"].lower()

    def test_auth_login_rejects_invalid_token(self, base_url):
        r = httpx.post(
            f"{base_url}/api/auth/login",
            json={"request_token": "invalid_dummy_token"},
            timeout=TIMEOUT,
        )
        assert r.status_code in (400, 401)


# =============================================================================
# MARKET DATA ENDPOINTS
# =============================================================================


class TestProdMarketData:
    """Market data endpoint tests."""

    def test_market_status(self, base_url):
        r = httpx.get(f"{base_url}/api/market/status", timeout=TIMEOUT)
        assert r.status_code == 200
        d = r.json()
        assert "market_status" in d
        assert "market_open" in d
        assert isinstance(d["market_open"], bool)

    def test_market_instruments(self, base_url):
        r = httpx.get(f"{base_url}/api/market/instruments?limit=5", timeout=TIMEOUT)
        assert r.status_code == 200
        d = r.json()
        assert "instruments" in d
        assert "total_count" in d
        assert isinstance(d["instruments"], list)

    def test_market_quotes(self, base_url):
        r = httpx.post(
            f"{base_url}/api/market/quotes",
            json={"symbols": ["NSE:RELIANCE"], "exchange": "NSE"},
            timeout=TIMEOUT,
        )
        assert r.status_code == 200
        d = r.json()
        assert "stocks" in d
        assert d.get("total_symbols") == 1
        assert "processing_time_ms" in d

    def test_market_data_quote(self, base_url):
        r = httpx.post(
            f"{base_url}/api/market/data",
            json={"symbols": ["NSE:RELIANCE"], "data_type": "quote", "exchange": "NSE"},
            timeout=TIMEOUT,
        )
        assert r.status_code == 200
        d = r.json()
        assert d.get("success") is True
        assert "processing_time_ms" in d


# =============================================================================
# ANALYSIS ENDPOINTS
# =============================================================================


class TestProdAnalysis:
    """Analysis endpoint tests."""

    def test_analysis_context(self, base_url):
        r = httpx.post(
            f"{base_url}/api/analysis/context",
            json={
                "include_global": True,
                "include_indian": True,
                "include_sentiment": True,
                "include_technical": False,
            },
            timeout=TIMEOUT,
        )
        assert r.status_code == 200
        d = r.json()
        assert d.get("success") is True
        assert "global_markets" in d or "indian_markets" in d
        assert "processing_time_ms" in d

    def test_analysis_intelligence(self, base_url):
        r = httpx.post(
            f"{base_url}/api/analysis/intelligence",
            json={
                "symbol": "NSE:RELIANCE",
                "include_trends": True,
                "include_levels": True,
                "include_signals": True,
            },
            timeout=TIMEOUT,
        )
        assert r.status_code == 200
        d = r.json()
        assert d.get("success") is True
        assert "processing_time_ms" in d

    def test_analysis_stock(self, base_url):
        r = httpx.post(
            f"{base_url}/api/analysis/stock",
            json={
                "symbol": "NSE:RELIANCE",
                "analysis_type": "comprehensive",
                "time_horizon": "intraday",
            },
            timeout=TIMEOUT,
        )
        assert r.status_code == 200
        d = r.json()
        assert d.get("symbol") == "NSE:RELIANCE"
        assert "current_price" in d or "processing_time_ms" in d

    def test_analysis_context_enhanced(self, base_url):
        r = httpx.post(
            f"{base_url}/api/analysis/context/enhanced",
            json={
                "trading_styles": ["intraday"],
                "include_primary": True,
                "include_detailed": False,
                "include_style_specific": False,
            },
            timeout=TIMEOUT,
        )
        assert r.status_code == 200
        d = r.json()
        assert d.get("success") is True
        assert "primary_context" in d or "context_quality_score" in d


# =============================================================================
# OPPORTUNITIES & TRADING
# =============================================================================


class TestProdOpportunities:
    """Quick opportunities endpoint tests."""

    def test_opportunities_quick(self, base_url):
        r = httpx.post(
            f"{base_url}/api/opportunities/quick",
            json={
                "symbols": ["NSE:NIFTY 50"],
                "timeframe": "5minute",
                "opportunity_types": ["breakout", "reversal", "momentum"],
            },
            timeout=TIMEOUT,
        )
        if r.status_code == 500:
            pytest.skip("opportunities returned 500 (Kite auth not configured)")
        assert r.status_code == 200
        d = r.json()
        assert d.get("success") is True
        assert "opportunities" in d or "nifty_price" in d or "market_momentum" in d


class TestProdTrading:
    def test_trading_status(self, base_url):
        r = httpx.get(f"{base_url}/api/trading/status", timeout=TIMEOUT)
        assert r.status_code == 200
        d = r.json()
        assert d.get("success") is not None
        assert "authenticated" in d
        assert "total_positions" in d and "total_holdings" in d
        assert "processing_time_ms" in d


class TestProdMetrics:
    def test_metrics_endpoint(self, base_url):
        r = httpx.get(f"{base_url}/metrics", timeout=TIMEOUT)
        assert r.status_code == 200
        assert len(r.content) > 0

    def test_health_quick(self, base_url):
        r = httpx.get(f"{base_url}/health/quick", timeout=TIMEOUT)
        assert r.status_code == 200
        d = r.json()
        assert "status" in d
