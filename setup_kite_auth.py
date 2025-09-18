#!/usr/bin/env python3
"""
Kite Connect Authentication Setup
=================================

Simple script to help set up Kite Connect authentication.
This script will guide you through the authentication process.
"""

import os
import sys
import time
import webbrowser
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def print_header():
    """Print setup header."""
    print("🔐 Kite Connect Authentication Setup")
    print("=" * 50)

def check_environment():
    """Check if environment variables are set."""
    print("🔍 Checking environment variables...")
    
    api_key = os.getenv('KITE_API_KEY')
    api_secret = os.getenv('KITE_API_SECRET')
    
    if not api_key:
        print("❌ KITE_API_KEY not set")
        return False
    else:
        print(f"✅ KITE_API_KEY: {api_key[:8]}...")
    
    if not api_secret:
        print("❌ KITE_API_SECRET not set")
        return False
    else:
        print(f"✅ KITE_API_SECRET: {api_secret[:8]}...")
    
    return True

def check_dependencies():
    """Check if required dependencies are installed."""
    print("\n🔍 Checking dependencies...")
    
    try:
        import kiteconnect
        print("✅ kiteconnect package available")
    except ImportError:
        print("❌ kiteconnect package not installed")
        print("   Run: pip install kiteconnect")
        return False
    
    try:
        import fastapi
        print("✅ fastapi package available")
    except ImportError:
        print("❌ fastapi package not installed")
        print("   Run: pip install fastapi")
        return False
    
    try:
        import uvicorn
        print("✅ uvicorn package available")
    except ImportError:
        print("❌ uvicorn package not installed")
        print("   Run: pip install uvicorn")
        return False
    
    return True

def get_auth_status():
    """Get current authentication status."""
    try:
        from services.kite_auth_service import KiteAuthService
        auth_service = KiteAuthService()
        return auth_service.get_auth_status()
    except Exception as e:
        print(f"❌ Error checking auth status: {e}")
        return None

def main():
    """Main setup function."""
    print_header()
    
    # Check environment
    if not check_environment():
        print("\n💡 To set environment variables:")
        print("   export KITE_API_KEY='your_api_key'")
        print("   export KITE_API_SECRET='your_api_secret'")
        print("\n   Or create a .env file with:")
        print("   KITE_API_KEY=your_api_key")
        print("   KITE_API_SECRET=your_api_secret")
        return 1
    
    # Check dependencies
    if not check_dependencies():
        print("\n💡 Install missing dependencies:")
        print("   pip install kiteconnect fastapi uvicorn pydantic pydantic-settings")
        return 1
    
    # Check authentication status
    print("\n🔍 Checking authentication status...")
    auth_status = get_auth_status()
    
    if not auth_status:
        print("❌ Could not check authentication status")
        return 1
    
    if auth_status.get("authenticated"):
        user_info = auth_status.get("user_info", {})
        print(f"✅ Already authenticated as {user_info.get('user_name')} ({user_info.get('user_id')})")
        print(f"   Token expires: {auth_status.get('expires_at')}")
        
        print("\n🎉 You're all set! You can now use the market data API:")
        print("   curl 'http://localhost:8079/api/market/data?symbols=RELIANCE&scope=basic'")
        return 0
    
    # Need to authenticate
    print("❌ Not authenticated")
    
    if auth_status.get("login_url"):
        print(f"\n🔗 Login URL: {auth_status['login_url']}")
        
        print("\n📋 Authentication Steps:")
        print("1. Make sure your Kite Connect app has callback URL set to:")
        print("   http://localhost:8079/api/auth/callback")
        print("\n2. Start the Kite Services server:")
        print("   python src/main.py")
        print("\n3. Open the login URL in your browser (or we can do it now)")
        print("4. Login with your Zerodha credentials")
        print("5. You'll be redirected to the callback URL")
        print("6. Access token will be saved automatically")
        
        # Ask if user wants to open URL
        try:
            response = input("\n🌐 Open login URL in browser now? (y/n): ").strip().lower()
            if response in ['y', 'yes']:
                print("🚀 Opening login URL...")
                webbrowser.open(auth_status['login_url'])
                print("\n✅ Login URL opened in browser")
                print("   After authentication, run this script again to verify")
        except KeyboardInterrupt:
            print("\n👋 Setup interrupted")
            return 1
    
    print("\n📚 For detailed instructions, visit:")
    print("   http://localhost:8079/api/auth/setup-instructions")
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n👋 Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Setup failed: {e}")
        sys.exit(1)
