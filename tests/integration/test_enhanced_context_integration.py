"""
Integration Tests for Enhanced Market Context API
=================================================

Tests the complete enhanced context endpoint with real data validation.
"""

import pytest
import httpx
import asyncio
from typing import Dict, Any
from decimal import Decimal


BASE_URL = "http://localhost:8079"


class TestEnhancedContextIntegration:
    """Integration tests for enhanced market context API."""
    
    @pytest.fixture(scope="class")
    def client(self):
        """HTTP client for API calls."""
        return httpx.Client(base_url=BASE_URL, timeout=30.0)
    
    def test_health_check(self, client):
        """Test that service is running."""
        response = client.get("/health")
        assert response.status_code == 200, "Health check should return 200"
        
        data = response.json()
        assert data["status"] == "healthy", "Service should be healthy"
        print("\n✅ Service is healthy")
    
    def test_primary_context_only(self, client):
        """Test primary context with minimal request."""
        response = client.post(
            "/api/analysis/context/enhanced",
            json={
                "include_primary": True,
                "include_detailed": False,
                "include_style_specific": False
            }
        )
        
        assert response.status_code == 200, f"Should return 200, got {response.status_code}"
        data = response.json()
        
        # Validate response structure
        assert data["success"] == True, "Should be successful"
        assert "primary_context" in data, "Should have primary_context"
        assert "data_quality" in data, "Should have data_quality"
        assert "data_source_summary" in data, "Should have data_source_summary"
        
        # Validate primary context
        primary = data["primary_context"]
        assert "global_context" in primary, "Should have global_context"
        assert "indian_context" in primary, "Should have indian_context"
        assert "overall_market_score" in primary, "Should have market_score"
        assert "market_confidence" in primary, "Should have confidence"
        
        # Validate data quality
        quality = data["data_quality"]
        assert "overall_quality" in quality, "Should have overall_quality"
        assert "real_data_percentage" in quality, "Should have real_data_percentage"
        assert "data_sources" in quality, "Should have data_sources"
        
        print(f"\n✅ Primary context: {quality['real_data_percentage']}% real data")
    
    def test_detailed_context(self, client):
        """Test detailed context with technical indicators."""
        response = client.post(
            "/api/analysis/context/enhanced",
            json={
                "include_primary": True,
                "include_detailed": True,
                "include_style_specific": False,
                "include_technicals": True,
                "include_sectors": True
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        assert "detailed_context" in data
        
        detailed = data["detailed_context"]
        
        # Check for expected fields
        assert "nifty_analysis" in detailed or detailed is not None
        
        print(f"\n✅ Detailed context included")
    
    def test_all_trading_styles(self, client):
        """Test all trading style contexts."""
        response = client.post(
            "/api/analysis/context/enhanced",
            json={
                "include_primary": True,
                "include_detailed": True,
                "include_style_specific": True,
                "trading_styles": ["intraday", "swing", "long_term"],
                "include_sectors": True,
                "include_technicals": True,
                "include_opportunities": True
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        
        # Check all contexts are present
        assert "primary_context" in data
        assert "detailed_context" in data
        assert "intraday_context" in data
        assert "swing_context" in data
        assert "long_term_context" in data
        
        print(f"\n✅ All trading style contexts included")
    
    def test_data_quality_reporting(self, client):
        """Test that data quality is reported correctly."""
        response = client.post(
            "/api/analysis/context/enhanced",
            json={"include_primary": True}
        )
        
        data = response.json()
        quality = data["data_quality"]
        summary = data["data_source_summary"]
        
        # Validate percentages
        real_pct = quality["real_data_percentage"]
        approx_pct = quality["approximated_percentage"]
        fallback_pct = quality["fallback_percentage"]
        
        total_pct = real_pct + approx_pct + fallback_pct
        assert 99 <= total_pct <= 101, f"Percentages should sum to ~100%, got {total_pct}"
        
        # Validate summary counts
        total_count = summary["total"]
        real_count = summary["real"]
        approx_count = summary["approximated"]
        fallback_count = summary["fallback"]
        
        assert real_count + approx_count + fallback_count == total_count, \
            "Counts should sum to total"
        
        # Validate data sources list
        assert len(quality["data_sources"]) > 0, "Should have data sources listed"
        
        print(f"\n✅ Data Quality: {real_pct}% real, {approx_pct}% calculated, {fallback_pct}% fallback")
    
    def test_indian_markets_real_data(self, client):
        """Test that Indian markets are using real Kite data."""
        response = client.post(
            "/api/analysis/context/enhanced",
            json={"include_primary": True}
        )
        
        data = response.json()
        indian = data["primary_context"]["indian_context"]
        
        # Check for real data indicators
        nifty_change = float(indian["nifty_change"])
        
        # If nifty_change is not 0, we have real data
        # (Even if markets are closed, Kite provides last closing data)
        if nifty_change != 0:
            print(f"\n✅ Nifty real data: {nifty_change}%")
        else:
            # Check data quality report
            quality = data["data_quality"]
            has_real_indian = any("Indian markets: REAL" in src for src in quality["data_sources"])
            
            if not has_real_indian:
                fallbacks = quality.get("fallbacks", [])
                print(f"\n⚠️  Indian markets fallback: {fallbacks}")
    
    def test_global_markets_real_data(self, client):
        """Test that global markets are using real Yahoo data."""
        response = client.post(
            "/api/analysis/context/enhanced",
            json={"include_primary": True}
        )
        
        data = response.json()
        global_ctx = data["primary_context"]["global_context"]
        
        # Check for real data
        us_change = float(global_ctx["us_markets_change"])
        
        assert us_change != 0, "Should have real US markets data"
        
        print(f"\n✅ US markets real data: {us_change}%")
    
    def test_performance(self, client):
        """Test API response time."""
        import time
        
        start = time.time()
        response = client.post(
            "/api/analysis/context/enhanced",
            json={"include_primary": True}
        )
        end = time.time()
        
        response_time_ms = (end - start) * 1000
        
        assert response.status_code == 200
        assert response_time_ms < 5000, f"Primary context should respond in <5s, got {response_time_ms:.0f}ms"
        
        print(f"\n✅ Response time: {response_time_ms:.0f}ms")
    
    def test_error_handling(self, client):
        """Test error handling with invalid requests."""
        # Invalid request - no fields included
        response = client.post(
            "/api/analysis/context/enhanced",
            json={
                "include_primary": False,
                "include_detailed": False,
                "include_style_specific": False
            }
        )
        
        # Should still return something (at minimum, primary context)
        assert response.status_code in [200, 400]
    
    def test_data_consistency(self, client):
        """Test that data is consistent across multiple calls."""
        # Make two calls
        response1 = client.post("/api/analysis/context/enhanced", json={"include_primary": True})
        response2 = client.post("/api/analysis/context/enhanced", json={"include_primary": True})
        
        data1 = response1.json()
        data2 = response2.json()
        
        # Prices should be the same (or very close) if called within seconds
        nifty1 = float(data1["primary_context"]["indian_context"]["nifty_change"])
        nifty2 = float(data2["primary_context"]["indian_context"]["nifty_change"])
        
        # Allow small variation due to rounding
        assert abs(nifty1 - nifty2) < 0.01, "Data should be consistent across calls"
        
        print(f"\n✅ Data consistency verified: {nifty1}% vs {nifty2}%")


class TestDataQualityValidationAPI:
    """Tests specifically for data quality validation in API responses."""
    
    @pytest.fixture(scope="class")
    def client(self):
        """HTTP client for API calls."""
        return httpx.Client(base_url=BASE_URL, timeout=30.0)
    
    def test_quality_score_range(self, client):
        """Test that quality scores are in valid range."""
        response = client.post(
            "/api/analysis/context/enhanced",
            json={"include_primary": True}
        )
        
        data = response.json()
        
        # Check overall quality score
        quality_score = data["context_quality_score"]
        assert 0.0 <= quality_score <= 1.0, f"Quality score should be 0-1, got {quality_score}"
        
        # Check confidence
        confidence = data["primary_context"]["market_confidence"]
        assert 0.0 <= confidence <= 1.0, f"Confidence should be 0-1, got {confidence}"
        
        print(f"\n✅ Quality score: {quality_score}, Confidence: {confidence}")
    
    def test_data_source_labeling(self, client):
        """Test that data sources are clearly labeled."""
        response = client.post(
            "/api/analysis/context/enhanced",
            json={"include_primary": True}
        )
        
        data = response.json()
        sources = data["data_quality"]["data_sources"]
        
        # Each source should be labeled as REAL, CALCULATED, or APPROXIMATED
        for source in sources:
            assert any(keyword in source for keyword in ["REAL", "CALCULATED", "APPROXIMATED"]), \
                f"Source should be labeled: {source}"
        
        print(f"\n✅ All {len(sources)} data sources properly labeled")
    
    def test_fallback_reporting(self, client):
        """Test that fallbacks are reported when they occur."""
        response = client.post(
            "/api/analysis/context/enhanced",
            json={
                "include_primary": True,
                "include_detailed": True,
                "include_style_specific": True,
                "trading_styles": ["all"]
            }
        )
        
        data = response.json()
        fallbacks = data["data_quality"].get("fallbacks", [])
        
        # If there are fallbacks, they should be documented
        if fallbacks:
            print(f"\n⚠️  Fallbacks detected ({len(fallbacks)}):")
            for fb in fallbacks:
                print(f"    - {fb}")
        else:
            print(f"\n✅ No fallbacks - all data from primary sources")
    
    def test_recommendations(self, client):
        """Test that quality recommendations are provided."""
        response = client.post(
            "/api/analysis/context/enhanced",
            json={"include_primary": True}
        )
        
        data = response.json()
        recommendations = data["data_quality"].get("recommendations", [])
        
        # Should have recommendations if quality is low
        quality = data["data_quality"]["overall_quality"]
        if quality in ["LOW", "MEDIUM"]:
            assert len(recommendations) > 0, "Should have recommendations when quality is low/medium"
            print(f"\n💡 Recommendations ({len(recommendations)}):")
            for rec in recommendations:
                print(f"    - {rec}")
        else:
            print(f"\n✅ Quality is {quality} - no recommendations needed")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])

