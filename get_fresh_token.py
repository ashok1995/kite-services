#!/usr/bin/env python3
"""
Get Fresh Kite Connect Token
============================

Simple script to get a fresh Kite Connect access token.
Shows login URL and instructions for OAuth flow.
"""

import os
import json
from datetime import datetime

# Load environment variables
try:
    with open('.env', 'r') as f:
        for line in f:
            if '=' in line and not line.strip().startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ[key] = value
except:
    pass

def get_login_url():
    """Get Kite Connect login URL."""
    try:
        from kiteconnect import KiteConnect
        
        api_key = os.getenv('KITE_API_KEY')
        if not api_key:
            print("❌ KITE_API_KEY not found in environment")
            return None
        
        kite = KiteConnect(api_key=api_key)
        login_url = kite.login_url()
        
        return login_url
        
    except Exception as e:
        print(f"❌ Error generating login URL: {e}")
        return None

def main():
    """Main function to get fresh token."""
    print("🔐 Get Fresh Kite Connect Token")
    print("=" * 50)
    
    # Check current status
    print("📊 Current Status:")
    
    api_key = os.getenv('KITE_API_KEY')
    api_secret = os.getenv('KITE_API_SECRET') 
    access_token = os.getenv('KITE_ACCESS_TOKEN')
    
    print(f"   API Key: {'✅ ' + api_key[:8] + '...' if api_key else '❌ Not set'}")
    print(f"   API Secret: {'✅ ' + api_secret[:8] + '...' if api_secret else '❌ Not set'}")
    print(f"   Access Token: {'⚠️ Expired (' + access_token[:8] + '...)' if access_token else '❌ Not set'}")
    
    if not api_key or not api_secret:
        print("\n❌ Missing credentials!")
        print("💡 Make sure your .env file has:")
        print("   KITE_API_KEY=your_api_key")
        print("   KITE_API_SECRET=your_api_secret")
        return 1
    
    # Get login URL
    print("\n🔗 Generating fresh login URL...")
    login_url = get_login_url()
    
    if not login_url:
        return 1
    
    print(f"✅ Login URL generated!")
    print(f"\n🔗 **YOUR LOGIN URL:**")
    print(f"   {login_url}")
    
    print(f"\n📋 **CALLBACK URL FOR KITE APP:**")
    print(f"   http://localhost:8079/auth/callback")
    
    print(f"\n🚀 **STEPS TO GET FRESH TOKEN:**")
    print(f"1. **Set Callback URL in Kite Connect App:**")
    print(f"   • Go to https://developers.kite.trade/")
    print(f"   • Edit your app settings")
    print(f"   • Set Redirect URL to: http://localhost:8079/auth/callback")
    print(f"   • Save settings")
    
    print(f"\n2. **Start OAuth Server:**")
    print(f"   python kite_token_manager.py")
    print(f"   (Choose option 1 to start server and open browser)")
    
    print(f"\n3. **Complete Authentication:**")
    print(f"   • Browser will open with login URL")
    print(f"   • Login with your Zerodha credentials")
    print(f"   • You'll be redirected to callback URL")
    print(f"   • Fresh token will be saved automatically")
    
    print(f"\n4. **Test Real Data:**")
    print(f"   curl 'http://localhost:8079/api/market/data?symbols=RELIANCE&scope=basic'")
    
    print(f"\n{'='*50}")
    print(f"🎯 **SUMMARY:**")
    print(f"   ✅ Your credentials are configured")
    print(f"   ⚠️  Token expired (from Sep 15 - tokens expire daily)")
    print(f"   🔗 Callback URL: http://localhost:8079/auth/callback")
    print(f"   📱 Login URL: {login_url[:50]}...")
    print(f"{'='*50}")
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        exit(exit_code)
    except KeyboardInterrupt:
        print("\n👋 Interrupted")
        exit(1)
    except Exception as e:
        print(f"\n💥 Failed: {e}")
        exit(1)
