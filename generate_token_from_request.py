#!/usr/bin/env python3
"""
Generate Access Token from Request Token
========================================

Convert the request token from Kite Connect OAuth callback into a fresh access token.
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path

# Load environment variables
try:
    with open('.env', 'r') as f:
        for line in f:
            if '=' in line and not line.strip().startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ[key] = value
    print("✅ Loaded .env file")
except:
    print("⚠️  No .env file found")

def generate_access_token(request_token: str):
    """Generate access token from request token."""
    print("🔄 Generating Access Token")
    print("=" * 50)
    
    try:
        from kiteconnect import KiteConnect
        
        # Get credentials from environment
        api_key = os.getenv('KITE_API_KEY')
        api_secret = os.getenv('KITE_API_SECRET')
        
        if not api_key or not api_secret:
            print("❌ Missing API credentials")
            return None
        
        print(f"📊 Using credentials:")
        print(f"   API Key: {api_key[:8]}...")
        print(f"   API Secret: {api_secret[:8]}...")
        print(f"   Request Token: {request_token[:8]}...")
        
        # Initialize Kite Connect
        kite = KiteConnect(api_key=api_key)
        
        # Generate session with request token
        print(f"\n🔄 Exchanging request token for access token...")
        
        data = kite.generate_session(
            request_token=request_token,
            api_secret=api_secret
        )
        
        # Create comprehensive token data
        token_data = {
            "access_token": data["access_token"],
            "user_id": data["user_id"],
            "user_name": data["user_name"],
            "user_type": data["user_type"],
            "email": data["email"],
            "broker": data["broker"],
            "exchanges": data["exchanges"],
            "products": data["products"],
            "order_types": data["order_types"],
            "api_key": api_key,
            "api_secret": api_secret,
            "request_token": request_token,
            "generated_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(hours=24)).isoformat(),
            "status": "active",
            "generated_by": "kite_services_oauth"
        }
        
        print(f"✅ Access token generated successfully!")
        print(f"\n👤 User Information:")
        print(f"   Name: {data['user_name']}")
        print(f"   User ID: {data['user_id']}")
        print(f"   Email: {data['email']}")
        print(f"   Broker: {data['broker']}")
        print(f"   User Type: {data['user_type']}")
        
        print(f"\n📊 Token Details:")
        print(f"   Access Token: {data['access_token'][:8]}...")
        print(f"   Generated: {token_data['generated_at']}")
        print(f"   Expires: {token_data['expires_at']}")
        print(f"   Exchanges: {', '.join(data['exchanges'])}")
        print(f"   Products: {', '.join(data['products'])}")
        
        # Save token to file
        token_file = Path("access_token.json")
        with open(token_file, 'w') as f:
            json.dump(token_data, f, indent=2)
        
        # Set secure permissions
        token_file.chmod(0o600)
        
        print(f"\n💾 Token saved to: {token_file.absolute()}")
        
        # Update .env file with new access token
        try:
            env_lines = []
            updated = False
            
            with open('.env', 'r') as f:
                for line in f:
                    if line.startswith('KITE_ACCESS_TOKEN='):
                        env_lines.append(f'KITE_ACCESS_TOKEN={data["access_token"]}\n')
                        updated = True
                    else:
                        env_lines.append(line)
            
            if not updated:
                env_lines.append(f'KITE_ACCESS_TOKEN={data["access_token"]}\n')
            
            with open('.env', 'w') as f:
                f.writelines(env_lines)
            
            print(f"✅ Updated .env file with fresh access token")
            
        except Exception as e:
            print(f"⚠️  Could not update .env file: {e}")
        
        # Test the new token
        print(f"\n🧪 Testing new access token...")
        
        kite.set_access_token(data["access_token"])
        profile = kite.profile()
        
        print(f"✅ Token validation successful!")
        print(f"   Authenticated as: {profile.get('user_name')} ({profile.get('user_id')})")
        
        # Test market data access
        try:
            instruments = kite.instruments("NSE")
            print(f"✅ Market data access confirmed ({len(instruments)} instruments available)")
            
            # Try to get a quote for RELIANCE
            reliance_token = None
            for instrument in instruments[:100]:  # Check first 100 instruments
                if instrument['tradingsymbol'] == 'RELIANCE':
                    reliance_token = instrument['instrument_token']
                    break
            
            if reliance_token:
                quote = kite.quote(f"NSE:{reliance_token}")
                reliance_data = quote.get(f"NSE:{reliance_token}", {})
                
                if reliance_data:
                    print(f"✅ Real RELIANCE data retrieved:")
                    print(f"   Price: ₹{reliance_data.get('last_price', 0)}")
                    print(f"   Change: {reliance_data.get('net_change', 0):+.2f}")
                    print(f"   Volume: {reliance_data.get('volume', 0):,}")
        
        except Exception as e:
            print(f"⚠️  Market data test failed: {e}")
        
        return token_data
        
    except Exception as e:
        print(f"❌ Failed to generate access token: {e}")
        return None

def main():
    """Main function."""
    # Extract request token from the callback URL
    callback_url = "http://127.0.0.1:8081/api/redirect?action=login&type=login&status=success&request_token=frDZd793YkRRorr5GHwBVPUkufonXNqF"
    
    # Parse request token from URL
    from urllib.parse import parse_qs, urlparse
    parsed = urlparse(callback_url)
    params = parse_qs(parsed.query)
    request_token = params.get('request_token', [None])[0]
    
    if not request_token:
        print("❌ No request token found in callback URL")
        return 1
    
    print(f"🔍 Extracted request token: {request_token}")
    
    # Generate access token
    token_data = generate_access_token(request_token)
    
    if token_data:
        print(f"\n{'='*50}")
        print(f"🎉 SUCCESS! Fresh access token generated!")
        print(f"✅ Token valid until: {token_data['expires_at']}")
        print(f"✅ Saved to: access_token.json")
        print(f"✅ Updated .env file")
        
        print(f"\n🚀 **READY TO USE REAL DATA!**")
        print(f"   Your consolidated API now has access to live Kite Connect data!")
        
        print(f"\n🔗 **TEST YOUR SETUP:**")
        print(f"   # Start service")
        print(f"   python src/main.py")
        print(f"   ")
        print(f"   # Test real market data")
        print(f"   curl 'http://localhost:8079/api/market/data?symbols=RELIANCE&scope=basic'")
        print(f"   ")
        print(f"   # Test portfolio with real P&L")
        print(f"   curl 'http://localhost:8079/api/market/portfolio?symbols=RELIANCE,TCS&quantities=100,50&avg_prices=2400,3800'")
        
        print(f"\n📚 **API DOCUMENTATION:**")
        print(f"   http://localhost:8079/docs")
        
        print(f"{'='*50}")
        return 0
    else:
        print(f"\n❌ Failed to generate access token")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        exit(exit_code)
    except KeyboardInterrupt:
        print("\n👋 Token generation interrupted")
        exit(1)
    except Exception as e:
        print(f"\n💥 Token generation failed: {e}")
        exit(1)
