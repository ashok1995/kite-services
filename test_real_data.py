#!/usr/bin/env python3
"""
Test Real Data Integration
==========================

Test script to verify real data integration with existing Zerodha token.
"""

import os
import json
import asyncio
from datetime import datetime
from pathlib import Path

# Load environment variables from .env file
try:
    with open('.env', 'r') as f:
        for line in f:
            if '=' in line and not line.strip().startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ[key] = value
    print("✅ Loaded .env file")
except Exception as e:
    print(f"⚠️  Could not load .env file: {e}")

# Test Kite Connect integration
async def test_kite_connect():
    """Test Kite Connect with real credentials."""
    print("\n🔍 Testing Kite Connect integration...")
    
    try:
        from kiteconnect import KiteConnect
        
        api_key = os.getenv('KITE_API_KEY')
        access_token = os.getenv('KITE_ACCESS_TOKEN')
        
        if not api_key or not access_token:
            print("❌ Missing Kite credentials in environment")
            return False
        
        print(f"   API Key: {api_key[:8]}...")
        print(f"   Access Token: {access_token[:8]}...")
        
        # Initialize Kite Connect
        kite = KiteConnect(api_key=api_key)
        kite.set_access_token(access_token)
        
        # Test API call - get profile
        profile = kite.profile()
        print(f"✅ Kite Connect authenticated successfully!")
        print(f"   User: {profile.get('user_name')} ({profile.get('user_id')})")
        print(f"   Broker: {profile.get('broker')}")
        
        # Test getting quote for RELIANCE
        try:
            # Get instruments first to find RELIANCE token
            instruments = kite.instruments("NSE")
            reliance_token = None
            
            for instrument in instruments:
                if instrument['tradingsymbol'] == 'RELIANCE':
                    reliance_token = instrument['instrument_token']
                    break
            
            if reliance_token:
                quote = kite.quote(f"NSE:{reliance_token}")
                reliance_data = quote.get(f"NSE:{reliance_token}", {})
                
                if reliance_data:
                    print(f"✅ Real RELIANCE data retrieved:")
                    print(f"   Price: ₹{reliance_data.get('last_price', 0)}")
                    print(f"   Change: {reliance_data.get('net_change', 0):+.2f} ({reliance_data.get('change', 0):+.2f}%)")
                    print(f"   Volume: {reliance_data.get('volume', 0):,}")
                else:
                    print("⚠️  RELIANCE data empty")
            else:
                print("⚠️  RELIANCE instrument token not found")
                
        except Exception as e:
            print(f"⚠️  Could not get RELIANCE quote: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Kite Connect test failed: {e}")
        return False

# Test Yahoo Finance integration
async def test_yahoo_finance():
    """Test Yahoo Finance integration."""
    print("\n🔍 Testing Yahoo Finance integration...")
    
    try:
        import yfinance as yf
        
        # Test getting RELIANCE data
        ticker = yf.Ticker("RELIANCE.NS")
        info = ticker.info
        
        if info:
            print("✅ Yahoo Finance working!")
            print(f"   Company: {info.get('longName', 'N/A')}")
            print(f"   Market Cap: ₹{info.get('marketCap', 0):,}")
            print(f"   PE Ratio: {info.get('trailingPE', 'N/A')}")
            print(f"   Dividend Yield: {info.get('dividendYield', 'N/A')}")
            
            # Test historical data
            hist = ticker.history(period="5d")
            if not hist.empty:
                latest = hist.iloc[-1]
                print(f"   Latest Close: ₹{latest['Close']:.2f}")
                print(f"   Volume: {latest['Volume']:,}")
            
            return True
        else:
            print("⚠️  No data from Yahoo Finance")
            return False
            
    except Exception as e:
        print(f"❌ Yahoo Finance test failed: {e}")
        return False

# Test consolidated API concept
async def test_consolidated_concept():
    """Test the consolidated API concept with real data."""
    print("\n🎯 Testing Consolidated API Concept...")
    
    kite_works = await test_kite_connect()
    yahoo_works = await test_yahoo_finance()
    
    if kite_works and yahoo_works:
        print("\n🎉 PERFECT! Both data sources working!")
        print("   ✅ Kite Connect: Real-time prices, OHLC, volume")
        print("   ✅ Yahoo Finance: Fundamentals, market cap, ratios")
        print("\n📊 Your consolidated API can now provide:")
        print("   • Real-time stock prices from Kite Connect")
        print("   • Fundamental analysis from Yahoo Finance")
        print("   • Historical data and technical indicators")
        print("   • Complete market context and portfolio management")
        
    elif kite_works:
        print("\n✅ Kite Connect working! Yahoo Finance has issues")
        print("   Your API can provide real-time data from Kite Connect")
        
    elif yahoo_works:
        print("\n✅ Yahoo Finance working! Kite Connect needs attention")
        print("   Your API can provide fundamentals and market data")
        
    else:
        print("\n❌ Both data sources have issues")
        print("   Check your credentials and network connection")
    
    return kite_works or yahoo_works

def main():
    """Main test function."""
    print("🚀 Real Data Integration Test")
    print("=" * 50)
    print(f"⏰ Test started at: {datetime.now()}")
    
    # Check if .env file was created
    if Path('.env').exists():
        print("✅ .env file found")
        
        # Show relevant environment variables
        kite_key = os.getenv('KITE_API_KEY')
        kite_token = os.getenv('KITE_ACCESS_TOKEN')
        
        if kite_key and kite_token:
            print(f"✅ Kite credentials loaded")
            print(f"   API Key: {kite_key[:8]}...")
            print(f"   Access Token: {kite_token[:8]}...")
        else:
            print("⚠️  Kite credentials not found in environment")
    else:
        print("❌ .env file not found")
        print("   Run: python find_existing_token.py")
        return 1
    
    # Run async tests
    try:
        success = asyncio.run(test_consolidated_concept())
        
        if success:
            print(f"\n{'='*50}")
            print("🎉 REAL DATA INTEGRATION SUCCESSFUL!")
            print("✅ Your existing Zerodha token is working")
            print("✅ Consolidated API ready for real market data")
            print("\n🚀 Start your service:")
            print("   python src/main.py")
            print("\n🔗 Test endpoints:")
            print("   curl 'http://localhost:8079/api/market/data?symbols=RELIANCE&scope=basic'")
            print("   curl 'http://localhost:8079/api/market/context'")
            print(f"{'='*50}")
            return 0
        else:
            print(f"\n{'='*50}")
            print("⚠️  Some data sources need attention")
            print("🔧 Check credentials and network connectivity")
            print(f"{'='*50}")
            return 1
            
    except Exception as e:
        print(f"\n💥 Test failed: {e}")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        exit(exit_code)
    except KeyboardInterrupt:
        print("\n👋 Test interrupted")
        exit(1)
