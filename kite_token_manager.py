#!/usr/bin/env python3
"""
Kite Connect Token Manager
==========================

Standalone service for Kite Connect access token generation and management.
Handles OAuth flow, token validation, and status checking.

Features:
- Generate login URLs
- Handle OAuth callback
- Validate token status
- Auto-refresh tokens
- Token storage and retrieval
"""

import json
import os
import time
import webbrowser
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional
from urllib.parse import parse_qs, urlparse

from kiteconnect import KiteConnect
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import HTMLResponse
import uvicorn


class KiteTokenManager:
    """Complete Kite Connect token management system."""
    
    def __init__(self, api_key: str, api_secret: str, token_file: str = "access_token.json"):
        """
        Initialize Kite Token Manager.
        
        Args:
            api_key: Kite Connect API key
            api_secret: Kite Connect API secret  
            token_file: Path to store access token
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.token_file = Path(token_file)
        
        # Initialize Kite Connect
        self.kite = KiteConnect(api_key=self.api_key)
        
        # Load existing token if available
        self.current_token = self._load_existing_token()
        if self.current_token:
            self.kite.set_access_token(self.current_token["access_token"])
    
    def get_login_url(self) -> str:
        """Generate Kite Connect login URL."""
        try:
            login_url = self.kite.login_url()
            print(f"🔗 Login URL generated: {login_url}")
            return login_url
        except Exception as e:
            print(f"❌ Error generating login URL: {e}")
            raise
    
    def generate_access_token(self, request_token: str) -> Dict[str, Any]:
        """
        Generate access token from request token.
        
        Args:
            request_token: Request token from Kite Connect callback
            
        Returns:
            Complete token data with user information
        """
        try:
            print(f"🔄 Generating access token from request token: {request_token[:10]}...")
            
            # Generate session
            data = self.kite.generate_session(
                request_token=request_token,
                api_secret=self.api_secret
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
                "api_key": self.api_key,
                "generated_at": datetime.now().isoformat(),
                "expires_at": (datetime.now() + timedelta(hours=24)).isoformat(),
                "status": "active"
            }
            
            # Save token data
            self._save_token_data(token_data)
            
            # Set access token in kite instance
            self.kite.set_access_token(data["access_token"])
            self.current_token = token_data
            
            print(f"✅ Access token generated successfully!")
            print(f"   User: {data['user_name']} ({data['user_id']})")
            print(f"   Broker: {data['broker']}")
            print(f"   Expires: {token_data['expires_at']}")
            
            return token_data
            
        except Exception as e:
            print(f"❌ Error generating access token: {e}")
            raise
    
    def get_token_status(self) -> Dict[str, Any]:
        """
        Get comprehensive token status.
        
        Returns:
            Token status with detailed information
        """
        status = {
            "timestamp": datetime.now().isoformat(),
            "token_file_exists": self.token_file.exists(),
            "token_loaded": bool(self.current_token),
            "token_valid": False,
            "token_expired": False,
            "user_info": None,
            "expires_at": None,
            "expires_in_hours": None,
            "login_url": None,
            "needs_refresh": False
        }
        
        try:
            # Check if token exists and is loaded
            if self.current_token:
                status["user_info"] = {
                    "user_id": self.current_token.get("user_id"),
                    "user_name": self.current_token.get("user_name"),
                    "email": self.current_token.get("email"),
                    "broker": self.current_token.get("broker")
                }
                status["expires_at"] = self.current_token.get("expires_at")
                
                # Check expiration
                expires_at = datetime.fromisoformat(self.current_token["expires_at"])
                now = datetime.now()
                
                if now >= expires_at:
                    status["token_expired"] = True
                    status["needs_refresh"] = True
                else:
                    hours_remaining = (expires_at - now).total_seconds() / 3600
                    status["expires_in_hours"] = round(hours_remaining, 2)
                    
                    # Check if token is still valid by making API call
                    try:
                        profile = self.kite.profile()
                        status["token_valid"] = True
                        print(f"✅ Token valid - User: {profile.get('user_name')}")
                    except Exception as e:
                        status["token_valid"] = False
                        status["needs_refresh"] = True
                        print(f"❌ Token validation failed: {e}")
            
            # Provide login URL if needed
            if not status["token_valid"] or status["needs_refresh"]:
                status["login_url"] = self.get_login_url()
            
        except Exception as e:
            print(f"❌ Error checking token status: {e}")
            status["error"] = str(e)
        
        return status
    
    def refresh_token_if_needed(self) -> bool:
        """
        Check if token needs refresh and provide guidance.
        
        Returns:
            True if token is valid, False if refresh needed
        """
        status = self.get_token_status()
        
        if status["token_valid"]:
            print(f"✅ Token is valid for {status['expires_in_hours']:.1f} more hours")
            return True
        elif status["token_expired"]:
            print("⚠️  Token has expired")
            print(f"🔗 Get fresh token: {status['login_url']}")
            return False
        elif not status["token_loaded"]:
            print("❌ No token found")
            print(f"🔗 Get new token: {status['login_url']}")
            return False
        else:
            print("⚠️  Token validation failed")
            print(f"🔗 Get fresh token: {status['login_url']}")
            return False
    
    def _load_existing_token(self) -> Optional[Dict[str, Any]]:
        """Load existing token from file."""
        try:
            if not self.token_file.exists():
                return None
            
            with open(self.token_file, 'r') as f:
                token_data = json.load(f)
            
            print(f"✅ Loaded existing token for user: {token_data.get('user_name', 'unknown')}")
            return token_data
            
        except Exception as e:
            print(f"⚠️  Could not load existing token: {e}")
            return None
    
    def _save_token_data(self, token_data: Dict[str, Any]) -> None:
        """Save token data to file."""
        try:
            # Create directory if needed
            self.token_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Save token data
            with open(self.token_file, 'w') as f:
                json.dump(token_data, f, indent=2)
            
            # Set secure permissions
            self.token_file.chmod(0o600)
            
            print(f"✅ Token saved to: {self.token_file}")
            
        except Exception as e:
            print(f"❌ Error saving token: {e}")
            raise


# FastAPI app for OAuth callback handling
def create_token_app(token_manager: KiteTokenManager) -> FastAPI:
    """Create FastAPI app for token management."""
    
    app = FastAPI(
        title="Kite Connect Token Manager",
        description="OAuth callback handler for Kite Connect authentication",
        version="1.0.0"
    )
    
    @app.get("/")
    async def root():
        """Root endpoint with instructions."""
        return {
            "service": "Kite Connect Token Manager",
            "status": "ready",
            "endpoints": {
                "auth_status": "/auth/status",
                "login_url": "/auth/login", 
                "callback": "/auth/callback",
                "instructions": "/auth/setup"
            },
            "callback_url": "http://localhost:8079/auth/callback"
        }
    
    @app.get("/auth/status")
    async def get_auth_status():
        """Get current authentication status."""
        status = token_manager.get_token_status()
        return status
    
    @app.get("/auth/login")
    async def get_login_url():
        """Get Kite Connect login URL."""
        try:
            login_url = token_manager.get_login_url()
            return {
                "login_url": login_url,
                "instructions": [
                    "1. Click the login URL to authenticate with Kite Connect",
                    "2. Login with your Zerodha credentials",
                    "3. You'll be redirected to the callback URL",
                    "4. Access token will be saved automatically"
                ],
                "callback_url": "http://localhost:8079/auth/callback"
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/auth/callback")
    async def auth_callback(
        request_token: str = Query(...),
        action: str = Query(...),
        status: str = Query(...)
    ):
        """Handle OAuth callback from Kite Connect."""
        try:
            if status != "success":
                return HTMLResponse(
                    content=f"""
                    <html>
                        <head><title>Authentication Failed</title></head>
                        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px;">
                            <h1 style="color: #e74c3c;">❌ Authentication Failed</h1>
                            <p>Status: {status}</p>
                            <p>Action: {action}</p>
                            <p><a href="/auth/login">Try Again</a></p>
                        </body>
                    </html>
                    """,
                    status_code=400
                )
            
            # Generate access token
            token_data = token_manager.generate_access_token(request_token)
            
            return HTMLResponse(
                content=f"""
                <html>
                    <head>
                        <title>Kite Connect - Success!</title>
                        <style>
                            body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }}
                            .success {{ color: #27ae60; }}
                            .info {{ background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 10px 0; }}
                            .code {{ background: #2c3e50; color: #ecf0f1; padding: 10px; border-radius: 3px; font-family: monospace; }}
                        </style>
                    </head>
                    <body>
                        <h1 class="success">🎉 Authentication Successful!</h1>
                        
                        <div class="info">
                            <h3>✅ Token Generated Successfully</h3>
                            <p><strong>User:</strong> {token_data['user_name']} ({token_data['user_id']})</p>
                            <p><strong>Broker:</strong> {token_data['broker']}</p>
                            <p><strong>Email:</strong> {token_data['email']}</p>
                            <p><strong>Expires:</strong> {token_data['expires_at']}</p>
                        </div>
                        
                        <div class="info">
                            <h3>🚀 Ready to Use!</h3>
                            <p>Your access token has been saved and is ready for use.</p>
                            
                            <h4>Test Your Setup:</h4>
                            <div class="code">
                                # Check token status<br>
                                curl "http://localhost:8079/auth/status"<br><br>
                                
                                # Test market data (when main service is running)<br>
                                curl "http://localhost:8079/api/market/data?symbols=RELIANCE&scope=basic"
                            </div>
                        </div>
                        
                        <div class="info">
                            <h3>📋 Next Steps:</h3>
                            <ol>
                                <li>Your token is saved in <code>access_token.json</code></li>
                                <li>Start your main Kite Services: <code>python src/main.py</code></li>
                                <li>Test real market data endpoints</li>
                                <li>Token expires daily - re-authenticate as needed</li>
                            </ol>
                        </div>
                        
                        <p><a href="/auth/status">Check Token Status</a> | <a href="/">Home</a></p>
                    </body>
                </html>
                """
            )
            
        except Exception as e:
            return HTMLResponse(
                content=f"""
                <html>
                    <head><title>Token Generation Failed</title></head>
                    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px;">
                        <h1 style="color: #e74c3c;">❌ Token Generation Failed</h1>
                        <p>Error: {str(e)}</p>
                        <p><a href="/auth/login">Try Again</a></p>
                    </body>
                </html>
                """,
                status_code=500
            )
    
    @app.get("/auth/setup", response_class=HTMLResponse)
    async def setup_instructions():
        """Complete setup instructions."""
        return HTMLResponse(
            content=f"""
            <html>
                <head>
                    <title>Kite Connect Setup Guide</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }}
                        .step {{ background: #f8f9fa; padding: 15px; margin: 15px 0; border-radius: 5px; }}
                        .code {{ background: #2c3e50; color: #ecf0f1; padding: 10px; border-radius: 3px; font-family: monospace; }}
                        .highlight {{ background: #fff3cd; padding: 10px; border-radius: 3px; border-left: 4px solid #ffc107; }}
                    </style>
                </head>
                <body>
                    <h1>🔐 Kite Connect Setup Guide</h1>
                    
                    <div class="highlight">
                        <h3>📍 Your Callback URL:</h3>
                        <div class="code">http://localhost:8079/auth/callback</div>
                        <p><strong>Set this exact URL in your Kite Connect app settings!</strong></p>
                    </div>
                    
                    <div class="step">
                        <h3>Step 1: Configure Kite Connect App</h3>
                        <ol>
                            <li>Go to <a href="https://developers.kite.trade/" target="_blank">developers.kite.trade</a></li>
                            <li>Login with your Zerodha account</li>
                            <li>Create new app or edit existing app</li>
                            <li>Set <strong>Redirect URL</strong> to: <code>http://localhost:8079/auth/callback</code></li>
                            <li>Save your app settings</li>
                        </ol>
                    </div>
                    
                    <div class="step">
                        <h3>Step 2: Set Your Credentials</h3>
                        <p>Set environment variables with your Kite Connect credentials:</p>
                        <div class="code">
                            export KITE_API_KEY="your_api_key_here"<br>
                            export KITE_API_SECRET="your_api_secret_here"
                        </div>
                    </div>
                    
                    <div class="step">
                        <h3>Step 3: Start Authentication</h3>
                        <ol>
                            <li><a href="/auth/login">Get Login URL</a></li>
                            <li>Click the login URL to authenticate</li>
                            <li>Login with your Zerodha credentials</li>
                            <li>You'll be redirected back here with success message</li>
                        </ol>
                    </div>
                    
                    <div class="step">
                        <h3>Step 4: Verify & Use</h3>
                        <ul>
                            <li><a href="/auth/status">Check Authentication Status</a></li>
                            <li>Start your main service: <code>python src/main.py</code></li>
                            <li>Test market data: <code>curl "http://localhost:8079/api/market/data?symbols=RELIANCE&scope=basic"</code></li>
                        </ul>
                    </div>
                    
                    <div class="highlight">
                        <h3>⚠️ Important Notes:</h3>
                        <ul>
                            <li>Access tokens expire daily (end of trading day)</li>
                            <li>You'll need to re-authenticate every day</li>
                            <li>Keep your API credentials secure</li>
                            <li>Callback URL must match exactly</li>
                        </ul>
                    </div>
                </body>
            </html>
            """
        )
    
    return app


def load_credentials_from_env() -> tuple[str, str]:
    """Load Kite Connect credentials from environment."""
    api_key = os.getenv('KITE_API_KEY')
    api_secret = os.getenv('KITE_API_SECRET')
    
    if not api_key or not api_secret:
        print("❌ Missing Kite Connect credentials")
        print("💡 Set environment variables:")
        print("   export KITE_API_KEY='your_api_key'")
        print("   export KITE_API_SECRET='your_api_secret'")
        print("\n   Or add to .env file:")
        print("   KITE_API_KEY=your_api_key")
        print("   KITE_API_SECRET=your_api_secret")
        raise ValueError("Missing Kite Connect credentials")
    
    return api_key, api_secret


def main():
    """Main function - can be used standalone or as part of larger service."""
    print("🔐 Kite Connect Token Manager")
    print("=" * 50)
    
    try:
        # Load credentials
        api_key, api_secret = load_credentials_from_env()
        print(f"✅ Loaded credentials - API Key: {api_key[:8]}...")
        
        # Initialize token manager
        token_manager = KiteTokenManager(api_key, api_secret)
        
        # Check current status
        print("\n🔍 Checking current token status...")
        status = token_manager.get_token_status()
        
        if status["token_valid"]:
            print("🎉 You're already authenticated and ready to go!")
            print(f"   User: {status['user_info']['user_name']} ({status['user_info']['user_id']})")
            print(f"   Expires in: {status['expires_in_hours']:.1f} hours")
            print("\n✅ Your consolidated API can now use real Kite Connect data!")
            return
        
        # Need authentication
        print("⚠️  Authentication needed")
        
        if status.get("login_url"):
            print(f"\n🔗 Login URL: {status['login_url']}")
            
            # Ask user what they want to do
            print("\n📋 Options:")
            print("1. Start OAuth server and open login URL")
            print("2. Just show login URL")
            print("3. Exit")
            
            try:
                choice = input("\nChoose option (1-3): ").strip()
                
                if choice == "1":
                    print("\n🚀 Starting OAuth callback server...")
                    print("📍 Callback URL: http://localhost:8079/auth/callback")
                    print("🌐 Setup instructions: http://localhost:8079/auth/setup")
                    print("\n⚠️  Make sure this callback URL is set in your Kite Connect app!")
                    
                    # Create and run FastAPI app
                    app = create_token_app(token_manager)
                    
                    # Open login URL in browser
                    print(f"\n🌐 Opening login URL in browser...")
                    webbrowser.open(status['login_url'])
                    
                    # Start server
                    uvicorn.run(app, host="0.0.0.0", port=8079, log_level="info")
                    
                elif choice == "2":
                    print(f"\n🔗 Login URL: {status['login_url']}")
                    print("\n📋 Manual steps:")
                    print("1. Set callback URL in Kite app: http://localhost:8079/auth/callback")
                    print("2. Start OAuth server: python kite_token_manager.py")
                    print("3. Open the login URL above")
                    print("4. Complete authentication")
                    
                else:
                    print("👋 Exiting...")
                    
            except KeyboardInterrupt:
                print("\n👋 Interrupted by user")
        
    except Exception as e:
        print(f"💥 Error: {e}")
        return 1


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Token manager stopped")
    except Exception as e:
        print(f"\n💥 Token manager failed: {e}")
