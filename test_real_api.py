#!/usr/bin/env python3
"""
Test script for Real Data API Endpoints
=======================================

This script tests the consolidated API endpoints with real market data
from Kite Connect and Yahoo Finance services.

Note: This requires proper Kite Connect credentials and network access.
"""

import asyncio
import aiohttp
import json
from datetime import datetime

BASE_URL = "http://localhost:8080/api/market"

async def test_endpoint(session, endpoint, params=None, description=""):
    """Test an API endpoint and display results."""
    url = f"{BASE_URL}/{endpoint}"
    if params:
        url += "?" + "&".join([f"{k}={v}" for k, v in params.items()])
    
    print(f"\n{'='*60}")
    print(f"🔍 Testing: {description}")
    print(f"📡 URL: {url}")
    print(f"{'='*60}")
    
    try:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                print(f"✅ SUCCESS (Status: {response.status})")
                
                # Display key information based on endpoint
                if 'stocks' in data:
                    print(f"📊 Retrieved data for {data.get('successful_symbols', 0)} symbols")
                    for symbol, stock in data['stocks'].items():
                        print(f"   • {symbol}: ₹{stock['last_price']} ({stock['change_percent']:+.2f}%)")
                
                if 'historical' in data and data['historical']:
                    for symbol, hist in data['historical'].items():
                        print(f"📈 Historical data for {symbol}: {hist['total_candles']} candles")
                        print(f"   • Price change: {hist['price_change_percent']:+.2f}% over {hist['total_candles']} periods")
                
                if 'market_context' in data and data['market_context']:
                    ctx = data['market_context']
                    print(f"🌍 Market Context: {ctx['market_status']} ({ctx['trading_session']})")
                    if ctx.get('indices'):
                        print(f"   • {len(ctx['indices'])} indices retrieved")
                    if ctx.get('sector_performance'):
                        print(f"   • {len(ctx['sector_performance'])} sectors retrieved")
                
                if 'holdings' in data:
                    metrics = data.get('metrics', {})
                    print(f"💼 Portfolio: {data['name']}")
                    print(f"   • Total Value: ₹{metrics.get('total_value', 0):,.2f}")
                    print(f"   • P&L: ₹{metrics.get('total_change', 0):,.2f} ({metrics.get('total_change_percent', 0):+.2f}%)")
                
                if 'indices' in data:
                    print(f"📊 Market indices: {len(data['indices'])} retrieved")
                    for index in data['indices'][:3]:  # Show first 3
                        print(f"   • {index['name']}: {index['value']:,.2f} ({index['change_percent']:+.2f}%)")
                
                # Show response size
                response_text = json.dumps(data)
                print(f"📦 Response size: {len(response_text):,} characters")
                
            else:
                error_data = await response.text()
                print(f"❌ ERROR (Status: {response.status})")
                print(f"   Response: {error_data[:200]}...")
                
    except Exception as e:
        print(f"💥 EXCEPTION: {str(e)}")

async def main():
    """Run all API tests."""
    print("🚀 Testing Consolidated API with REAL DATA")
    print("=" * 60)
    print(f"⏰ Test started at: {datetime.now()}")
    print("🔗 Make sure the Kite Services API is running on localhost:8080")
    
    async with aiohttp.ClientSession() as session:
        
        # Test 1: Basic real data
        await test_endpoint(
            session, 
            "data", 
            {"symbols": "RELIANCE,TCS", "scope": "basic"},
            "Basic Real Market Data (Kite Connect only)"
        )
        
        # Test 2: Standard data with OHLC
        await test_endpoint(
            session, 
            "data", 
            {"symbols": "RELIANCE", "scope": "standard"},
            "Standard Real Market Data (Kite + OHLC)"
        )
        
        # Test 3: Comprehensive data with fundamentals
        await test_endpoint(
            session, 
            "data", 
            {"symbols": "RELIANCE", "scope": "comprehensive"},
            "Comprehensive Real Data (Kite + Yahoo Finance)"
        )
        
        # Test 4: Full data with historical and context
        await test_endpoint(
            session, 
            "data", 
            {
                "symbols": "RELIANCE", 
                "scope": "full", 
                "historical_days": "5",
                "include_context": "true"
            },
            "Full Real Data (Everything + Historical + Context)"
        )
        
        # Test 5: Portfolio with real data
        await test_endpoint(
            session, 
            "portfolio", 
            {
                "name": "Test Portfolio",
                "symbols": "RELIANCE,TCS",
                "quantities": "100,50",
                "avg_prices": "2400,3800",
                "scope": "standard"
            },
            "Real Portfolio Data with P&L"
        )
        
        # Test 6: Real market context
        await test_endpoint(
            session, 
            "real-context", 
            None,
            "Real Market Context (Yahoo Finance)"
        )
        
        # Test 7: Health check
        await test_endpoint(
            session, 
            "../status", 
            None,
            "API Health Status"
        )
    
    print(f"\n{'='*60}")
    print(f"✅ All tests completed at: {datetime.now()}")
    print(f"{'='*60}")

if __name__ == "__main__":
    print("📋 Real Data API Test Suite")
    print("🔧 Requirements:")
    print("   1. Kite Services running on localhost:8080")
    print("   2. Valid Kite Connect credentials configured")
    print("   3. Internet connection for Yahoo Finance data")
    print("   4. Virtual environment activated with aiohttp installed")
    print("\n⚠️  Note: Some endpoints may return errors if Kite credentials are not configured")
    print("   This is expected behavior - the test will show which data sources work")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted by user")
    except Exception as e:
        print(f"\n💥 Test suite failed: {e}")
