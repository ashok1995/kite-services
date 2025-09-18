#!/usr/bin/env python3
"""
Kite Token Status Checker
=========================

Simple script to check Kite Connect token status and provide next steps.
"""

import json
import os
from datetime import datetime
from pathlib import Path

# Load environment variables from .env
try:
    with open('.env', 'r') as f:
        for line in f:
            if '=' in line and not line.strip().startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ[key] = value
    print("✅ Loaded .env file")
except:
    print("⚠️  No .env file found")

def check_token_status():
    """Check current Kite Connect token status."""
    print("🔍 Checking Kite Connect Token Status")
    print("=" * 50)
    
    # Check environment variables
    api_key = os.getenv('KITE_API_KEY')
    access_token = os.getenv('KITE_ACCESS_TOKEN')
    
    print(f"📊 Environment Status:")
    print(f"   API Key: {'✅ Set (' + api_key[:8] + '...)' if api_key else '❌ Not set'}")
    print(f"   Access Token: {'✅ Set (' + access_token[:8] + '...)' if access_token else '❌ Not set'}")
    
    # Check token file
    token_files = [
        "access_token.json",
        "../access_tokens/zerodha_token.json",
        "../access_tokens/zerodha_credentials.json"
    ]
    
    print(f"\n📁 Token Files Status:")
    latest_token = None
    latest_file = None
    
    for token_file in token_files:
        path = Path(token_file)
        if path.exists():
            try:
                with open(path, 'r') as f:
                    data = json.load(f)
                
                size = path.stat().st_size
                modified = datetime.fromtimestamp(path.stat().st_mtime)
                
                print(f"   ✅ {token_file}: {size} bytes, modified {modified}")
                
                # Check if this is the latest token
                if not latest_token or modified > datetime.fromtimestamp(Path(latest_file).stat().st_mtime):
                    latest_token = data
                    latest_file = token_file
                    
            except Exception as e:
                print(f"   ❌ {token_file}: Error reading - {e}")
        else:
            print(f"   ❌ {token_file}: Not found")
    
    # Analyze latest token
    if latest_token:
        print(f"\n🔍 Latest Token Analysis ({latest_file}):")
        
        # Extract token info
        token_info = {}
        
        # Handle different token file formats
        if 'access_token' in latest_token:
            token_info['access_token'] = latest_token['access_token']
        if 'api_key' in latest_token:
            token_info['api_key'] = latest_token['api_key']
        if 'user_info' in latest_token:
            user_info = latest_token['user_info']
            if isinstance(user_info, dict):
                token_info.update(user_info)
        
        # Display token info
        for key, value in token_info.items():
            if key in ['access_token', 'api_key', 'api_secret']:
                print(f"   • {key}: {str(value)[:8]}..." if value else f"   • {key}: Not found")
            else:
                print(f"   • {key}: {value}")
        
        # Test token validity
        print(f"\n🧪 Testing Token Validity:")
        
        try:
            from kiteconnect import KiteConnect
            
            kite_api_key = token_info.get('api_key') or api_key
            kite_access_token = token_info.get('access_token') or access_token
            
            if kite_api_key and kite_access_token:
                kite = KiteConnect(api_key=kite_api_key)
                kite.set_access_token(kite_access_token)
                
                # Test API call
                profile = kite.profile()
                print(f"   ✅ Token is VALID!")
                print(f"   👤 User: {profile.get('user_name')} ({profile.get('user_id')})")
                print(f"   🏢 Broker: {profile.get('broker')}")
                
                # Test market data call
                try:
                    instruments = kite.instruments("NSE")
                    print(f"   📊 Market data access: ✅ ({len(instruments)} instruments available)")
                except Exception as e:
                    print(f"   📊 Market data access: ⚠️  Limited - {e}")
                
                return True
                
            else:
                print(f"   ❌ Missing API key or access token")
                
        except Exception as e:
            print(f"   ❌ Token INVALID: {e}")
            
            if "Incorrect" in str(e) or "Invalid" in str(e):
                print(f"   💡 Token likely expired (Kite tokens expire daily)")
            
        return False
    
    else:
        print(f"\n❌ No token files found")
        return False

def provide_next_steps(token_valid: bool):
    """Provide next steps based on token status."""
    print(f"\n{'='*50}")
    
    if token_valid:
        print("🎉 TOKEN IS VALID - YOU'RE READY!")
        print("✅ Your Kite Connect integration is working")
        print("\n🚀 Start your consolidated API:")
        print("   cd /Users/ashokkumar/Desktop/ashok-personal/stocks/kite-services")
        print("   source venv/bin/activate")
        print("   python src/main.py")
        print("\n🔗 Test real market data:")
        print("   curl 'http://localhost:8079/api/market/data?symbols=RELIANCE&scope=basic'")
        
    else:
        print("⚠️  TOKEN NEEDS REFRESH")
        print("🔄 Get fresh access token:")
        print("\n📋 Option 1 - Use Token Manager:")
        print("   python kite_token_manager.py")
        print("   (Will open browser and handle OAuth flow)")
        
        print("\n📋 Option 2 - Manual Setup:")
        print("   1. Set callback URL in Kite app: http://localhost:8079/auth/callback")
        print("   2. Start token server: python kite_token_manager.py")
        print("   3. Complete OAuth flow in browser")
        
        print("\n🔗 Your callback URL: http://localhost:8079/auth/callback")
        print("   (Set this in your Kite Connect app at developers.kite.trade)")
    
    print(f"{'='*50}")

def main():
    """Main status check function."""
    try:
        token_valid = check_token_status()
        provide_next_steps(token_valid)
        return 0 if token_valid else 1
        
    except Exception as e:
        print(f"\n💥 Status check failed: {e}")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        exit(exit_code)
    except KeyboardInterrupt:
        print("\n👋 Status check interrupted")
        exit(1)
