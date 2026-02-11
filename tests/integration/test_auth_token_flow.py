"""
Integration tests for auth/token flow.

Run against a live service (dev on 8079 or prod on 8179):
  pytest tests/integration/test_auth_token_flow.py -v -k "test_auth_status"
  pytest tests/integration/test_auth_token_flow.py -v --base-url http://127.0.0.1:8079

For full token generation test, pass a valid request_token:
  REQUEST_TOKEN=xxx pytest tests/integration/test_auth_token_flow.py -v -k "test_generate_token"
"""

import os

import httpx
import pytest

BASE_URL = os.environ.get("TEST_BASE_URL", "http://127.0.0.1:8079")


@pytest.fixture
def base_url():
    """Base URL for API (dev or prod)."""
    return BASE_URL


class TestAuthTokenFlow:
    """Test authentication and token generation endpoints."""

    def test_health(self, base_url):
        r = httpx.get(f"{base_url}/health", timeout=10)
        assert r.status_code == 200
        d = r.json()
        assert d.get("status") == "healthy"
        assert d.get("service") == "kite-services"

    def test_auth_status(self, base_url):
        r = httpx.get(f"{base_url}/api/auth/status", timeout=10)
        assert r.status_code == 200
        d = r.json()
        assert d.get("status") in ("authenticated", "expired", "invalid", "not_configured")
        assert "authenticated" in d

    def test_login_url(self, base_url):
        r = httpx.get(f"{base_url}/api/auth/login-url", timeout=10)
        if r.status_code == 404:
            pytest.skip("login-url not deployed")
        assert r.status_code == 200
        d = r.json()
        assert "login_url" in d
        assert "kite" in d["login_url"].lower() or "zerodha" in d["login_url"].lower()

    def test_login_with_invalid_token(self, base_url):
        r = httpx.post(
            f"{base_url}/api/auth/login",
            json={"request_token": "invalid_dummy_token"},
            timeout=10,
        )
        assert r.status_code in (400, 401)
        assert "detail" in r.json()

    @pytest.mark.skipif(
        not os.environ.get("REQUEST_TOKEN"),
        reason="REQUEST_TOKEN not set",
    )
    def test_generate_access_token(self, base_url):
        r = httpx.post(
            f"{base_url}/api/auth/login",
            json={"request_token": os.environ["REQUEST_TOKEN"]},
            timeout=15,
        )
        assert r.status_code == 200
        d = r.json()
        assert d.get("status") == "authenticated"
        assert d.get("access_token")
        assert d.get("user_id")
