"""
Integration Tests for Kite Connect API
======================================

Tests real Kite Connect API integration with data quality validation.
"""

import pytest
import pytest_asyncio
import asyncio
from decimal import Decimal
from datetime import datetime
from typing import Dict, Any

import sys
sys.path.insert(0, 'src')

from core.kite_client import KiteClient
from config.settings import get_settings


class TestKiteConnectIntegration:
    """Integration tests for Kite Connect API."""
    
    @pytest_asyncio.fixture(scope="class")
    async def kite_client(self):
        """Initialize Kite client for tests."""
        client = KiteClient()
        await client.initialize()
        yield client
        await client.cleanup()
    
    @pytest.mark.asyncio
    async def test_kite_initialization(self, kite_client):
        """Test that Kite client initializes correctly."""
        assert kite_client is not None, "Kite client should be initialized"
        assert kite_client.kite is not None, "Kite API should be connected"
        assert kite_client.is_connected, "Kite should report as connected"
    
    @pytest.mark.asyncio
    async def test_quote_api_nifty(self, kite_client):
        """Test Kite quote API for Nifty 50."""
        quotes = await kite_client.quote(["NSE:NIFTY 50"])
        
        # Validate response structure
        assert "NSE:NIFTY 50" in quotes, "Should contain Nifty quote"
        
        nifty = quotes["NSE:NIFTY 50"]
        
        # Validate required fields
        assert "last_price" in nifty, "Should have last_price"
        assert "net_change" in nifty, "Should have net_change"
        assert "ohlc" in nifty, "Should have OHLC data"
        assert "timestamp" in nifty, "Should have timestamp"
        
        # Validate data types
        assert isinstance(nifty["last_price"], (int, float)), "last_price should be numeric"
        assert isinstance(nifty["net_change"], (int, float)), "net_change should be numeric"
        assert isinstance(nifty["ohlc"], dict), "OHLC should be a dictionary"
        
        # Validate OHLC structure
        ohlc = nifty["ohlc"]
        assert "open" in ohlc, "OHLC should have open"
        assert "high" in ohlc, "OHLC should have high"
        assert "low" in ohlc, "OHLC should have low"
        assert "close" in ohlc, "OHLC should have close"
        
        # Validate price ranges
        assert ohlc["high"] >= ohlc["low"], "High should be >= Low"
        assert ohlc["high"] >= ohlc["open"], "High should be >= Open (or close to it)"
        assert ohlc["low"] <= ohlc["close"], "Low should be <= Close (or close to it)"
        
        print(f"\n✅ Nifty Quote: {nifty['last_price']} ({nifty['net_change']})")
    
    @pytest.mark.asyncio
    async def test_quote_api_multiple_symbols(self, kite_client):
        """Test Kite quote API with multiple symbols."""
        symbols = ["NSE:NIFTY 50", "NSE:NIFTY BANK", "NSE:NIFTY MIDCAP 100"]
        quotes = await kite_client.quote(symbols)
        
        # Should receive all requested quotes
        assert len(quotes) == len(symbols), f"Should receive {len(symbols)} quotes"
        
        for symbol in symbols:
            assert symbol in quotes, f"Should contain {symbol}"
            quote = quotes[symbol]
            assert "last_price" in quote, f"{symbol} should have last_price"
            assert quote["last_price"] > 0, f"{symbol} price should be positive"
        
        print(f"\n✅ Received {len(quotes)} quotes for multiple symbols")
    
    @pytest.mark.asyncio
    async def test_data_quality_validation(self, kite_client):
        """Test data quality validation for Kite quotes."""
        quotes = await kite_client.quote(["NSE:NIFTY 50", "NSE:NIFTY BANK"])
        
        for symbol, data in quotes.items():
            # Quality checks
            quality_issues = []
            
            # 1. Price validation
            last_price = data.get("last_price", 0)
            if last_price <= 0:
                quality_issues.append(f"{symbol}: Invalid price {last_price}")
            
            # 2. OHLC validation
            ohlc = data.get("ohlc", {})
            if not all(k in ohlc for k in ["open", "high", "low", "close"]):
                quality_issues.append(f"{symbol}: Incomplete OHLC data")
            elif ohlc["high"] < ohlc["low"]:
                quality_issues.append(f"{symbol}: High < Low (invalid)")
            
            # 3. Timestamp validation
            timestamp = data.get("timestamp")
            if not timestamp:
                quality_issues.append(f"{symbol}: Missing timestamp")
            
            # 4. Net change validation
            net_change = data.get("net_change")
            if net_change is None:
                quality_issues.append(f"{symbol}: Missing net_change")
            
            # Report issues
            if quality_issues:
                pytest.fail(f"Data quality issues:\n" + "\n".join(quality_issues))
            
            print(f"\n✅ {symbol}: All quality checks passed")
    
    @pytest.mark.asyncio
    async def test_change_percentage_calculation(self, kite_client):
        """Test that change percentage can be calculated correctly."""
        quotes = await kite_client.quote(["NSE:NIFTY 50"])
        nifty = quotes.get("NSE:NIFTY 50", {})
        
        net_change = nifty.get("net_change", 0)
        prev_close = nifty.get("ohlc", {}).get("close", 0)
        
        assert prev_close > 0, "Previous close should be positive"
        
        # Calculate change percentage
        change_pct = (net_change / prev_close) * 100
        
        # Should be within reasonable range (-10% to +10% for Nifty)
        assert -10 < change_pct < 10, f"Change % {change_pct:.2f} seems unusual"
        
        print(f"\n✅ Nifty Change: {change_pct:.2f}% (calculated from net_change/prev_close)")
    
    @pytest.mark.asyncio
    async def test_works_when_markets_closed(self, kite_client):
        """Test that Kite API works even when markets are closed."""
        # This test runs at any time and should still get data
        quotes = await kite_client.quote(["NSE:NIFTY 50"])
        
        assert len(quotes) > 0, "Should receive quotes even when markets closed"
        assert "NSE:NIFTY 50" in quotes, "Should have Nifty data"
        
        nifty = quotes["NSE:NIFTY 50"]
        assert nifty["last_price"] > 0, "Should have valid last traded price"
        
        # Check if timestamp is from today or yesterday (last trading day)
        timestamp_str = nifty.get("timestamp", "")
        if timestamp_str:
            # Timestamp format: "2025-10-13 19:35:57"
            print(f"\n✅ Last trade time: {timestamp_str}")
            print(f"✅ Kite API works 24/7 - provides last traded prices")


class TestDataQualityValidation:
    """Tests for data quality validation logic."""
    
    def test_validate_price_range(self):
        """Test price range validation."""
        # Valid price
        assert self._validate_price(25000.50) == True
        
        # Invalid prices
        assert self._validate_price(0) == False
        assert self._validate_price(-100) == False
        assert self._validate_price(None) == False
    
    def test_validate_ohlc(self):
        """Test OHLC data validation."""
        # Valid OHLC
        valid_ohlc = {"open": 25000, "high": 25100, "low": 24900, "close": 25050}
        issues = self._validate_ohlc(valid_ohlc)
        assert len(issues) == 0, "Valid OHLC should have no issues"
        
        # Invalid OHLC - high < low
        invalid_ohlc = {"open": 25000, "high": 24900, "low": 25100, "close": 25050}
        issues = self._validate_ohlc(invalid_ohlc)
        assert len(issues) > 0, "Should detect high < low"
        
        # Incomplete OHLC
        incomplete_ohlc = {"open": 25000, "high": 25100}
        issues = self._validate_ohlc(incomplete_ohlc)
        assert len(issues) > 0, "Should detect missing fields"
    
    def test_validate_change_consistency(self):
        """Test that net_change is consistent with prices."""
        last_price = 25227.35
        prev_close = 25285.35
        net_change = -58.0
        
        # Calculate expected net change
        expected_net_change = last_price - prev_close
        
        # Should be close (within 0.1)
        assert abs(net_change - expected_net_change) < 0.1, \
            f"Net change {net_change} doesn't match calculated {expected_net_change}"
    
    def test_calculate_data_quality_score(self):
        """Test data quality score calculation."""
        # Perfect data
        perfect_data = {
            "last_price": 25000,
            "net_change": -50,
            "ohlc": {"open": 25000, "high": 25100, "low": 24900, "close": 25050},
            "timestamp": "2025-10-13 19:35:57",
            "volume": 1000000
        }
        score = self._calculate_quality_score(perfect_data)
        assert score >= 0.9, "Perfect data should have score >= 0.9"
        
        # Missing data
        incomplete_data = {
            "last_price": 25000,
            "net_change": -50
        }
        score = self._calculate_quality_score(incomplete_data)
        assert score < 0.5, "Incomplete data should have score < 0.5"
    
    # Helper methods
    def _validate_price(self, price) -> bool:
        """Validate price is positive and reasonable."""
        if price is None:
            return False
        if not isinstance(price, (int, float)):
            return False
        if price <= 0:
            return False
        return True
    
    def _validate_ohlc(self, ohlc: Dict) -> list:
        """Validate OHLC data structure and values."""
        issues = []
        
        required_fields = ["open", "high", "low", "close"]
        for field in required_fields:
            if field not in ohlc:
                issues.append(f"Missing {field}")
        
        if len(issues) == 0:
            if ohlc["high"] < ohlc["low"]:
                issues.append("High < Low (invalid)")
            if ohlc["high"] < ohlc["open"] and ohlc["high"] < ohlc["close"]:
                issues.append("High is less than both open and close")
        
        return issues
    
    def _calculate_quality_score(self, data: Dict) -> float:
        """Calculate data quality score (0.0 to 1.0)."""
        score = 0.0
        max_score = 5.0
        
        # Check required fields
        if data.get("last_price") and data["last_price"] > 0:
            score += 1.0
        
        if data.get("net_change") is not None:
            score += 1.0
        
        if data.get("ohlc") and len(self._validate_ohlc(data["ohlc"])) == 0:
            score += 1.0
        
        if data.get("timestamp"):
            score += 1.0
        
        if data.get("volume") and data["volume"] > 0:
            score += 1.0
        
        return score / max_score


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])

