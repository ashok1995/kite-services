"""
Kite Connect Authentication Routes
=================================

Routes for handling Kite Connect OAuth flow and token management.
Following workspace rules:
- Thin routes (call services only)
- Proper error handling
- Request/response logging
- Dependency injection
"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel

from services.kite_auth_service import KiteAuthService
from core.logging_config import get_logger

# Initialize router
router = APIRouter()
logger = get_logger(__name__)


# Response models
class AuthStatusResponse(BaseModel):
    """Authentication status response."""
    authenticated: bool
    token_exists: bool
    token_valid: bool
    user_info: Optional[dict] = None
    expires_at: Optional[str] = None
    login_url: Optional[str] = None
    message: str


class LoginUrlResponse(BaseModel):
    """Login URL response."""
    login_url: str
    instructions: str


class CallbackResponse(BaseModel):
    """Callback response."""
    success: bool
    message: str
    user_info: Optional[dict] = None
    expires_at: Optional[str] = None


# Dependency injection
def get_auth_service() -> KiteAuthService:
    """Get Kite authentication service."""
    return KiteAuthService(logger=logger)


@router.get("/status", response_model=AuthStatusResponse)
async def get_auth_status(
    auth_service: KiteAuthService = Depends(get_auth_service)
):
    """
    🔐 Get Kite Connect Authentication Status
    
    Check if you're authenticated with Kite Connect and get login URL if needed.
    """
    try:
        logger.info(
            "Auth status request",
            extra={"endpoint": "/auth/status"}
        )
        
        status = auth_service.get_auth_status()
        
        # Determine message based on status
        if status["authenticated"]:
            message = f"✅ Authenticated as {status['user_info']['user_name']} ({status['user_info']['user_id']})"
        elif status["token_exists"] and not status["token_valid"]:
            message = "⚠️ Token expired. Please re-authenticate using the login URL."
        else:
            message = "❌ Not authenticated. Please use the login URL to authenticate."
        
        response = AuthStatusResponse(
            authenticated=status["authenticated"],
            token_exists=status["token_exists"],
            token_valid=status["token_valid"],
            user_info=status["user_info"],
            expires_at=status["expires_at"],
            login_url=status["login_url"],
            message=message
        )
        
        logger.info(
            "Auth status response",
            extra={
                "endpoint": "/auth/status",
                "authenticated": status["authenticated"],
                "token_valid": status["token_valid"]
            }
        )
        
        return response
        
    except Exception as e:
        logger.error(
            "Auth status error",
            extra={
                "endpoint": "/auth/status",
                "error": str(e)
            },
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="Failed to get authentication status")


@router.get("/login", response_model=LoginUrlResponse)
async def get_login_url(
    auth_service: KiteAuthService = Depends(get_auth_service)
):
    """
    🔗 Get Kite Connect Login URL
    
    Get the login URL to authenticate with Kite Connect.
    """
    try:
        logger.info(
            "Login URL request",
            extra={"endpoint": "/auth/login"}
        )
        
        login_url = auth_service.get_login_url()
        
        response = LoginUrlResponse(
            login_url=login_url,
            instructions=(
                "1. Click the login URL to authenticate with Kite Connect\n"
                "2. After successful login, you'll be redirected to the callback URL\n"
                "3. The access token will be automatically saved and used for API calls"
            )
        )
        
        logger.info(
            "Login URL generated",
            extra={
                "endpoint": "/auth/login",
                "login_url": login_url
            }
        )
        
        return response
        
    except Exception as e:
        logger.error(
            "Login URL error",
            extra={
                "endpoint": "/auth/login",
                "error": str(e)
            },
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="Failed to generate login URL")


@router.get("/callback")
async def auth_callback(
    request_token: str = Query(..., description="Request token from Kite Connect"),
    action: str = Query(..., description="Action parameter from Kite Connect"),
    status: str = Query(..., description="Status parameter from Kite Connect"),
    auth_service: KiteAuthService = Depends(get_auth_service)
):
    """
    🔄 Kite Connect OAuth Callback
    
    This is the callback URL that Kite Connect redirects to after authentication.
    Set this URL in your Kite Connect app settings:
    
    **Callback URL:** `http://localhost:8079/api/auth/callback`
    
    Or for production: `https://your-domain.com/api/auth/callback`
    """
    try:
        logger.info(
            "Auth callback received",
            extra={
                "endpoint": "/auth/callback",
                "request_token": request_token[:8] + "..." if request_token else "empty",
                "action": action,
                "status": status
            }
        )
        
        # Check if authentication was successful
        if status != "success":
            logger.warning(
                "Authentication failed",
                extra={
                    "endpoint": "/auth/callback",
                    "status": status,
                    "action": action
                }
            )
            
            return HTMLResponse(
                content=f"""
                <html>
                    <head><title>Kite Connect - Authentication Failed</title></head>
                    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px;">
                        <h1 style="color: #e74c3c;">❌ Authentication Failed</h1>
                        <p>Status: {status}</p>
                        <p>Action: {action}</p>
                        <p><a href="/api/auth/login">Try again</a></p>
                    </body>
                </html>
                """,
                status_code=400
            )
        
        # Generate access token
        token_data = auth_service.generate_access_token(request_token)
        
        logger.info(
            "Access token generated successfully",
            extra={
                "endpoint": "/auth/callback",
                "user_id": token_data["user_id"],
                "user_name": token_data["user_name"]
            }
        )
        
        # Return success page
        return HTMLResponse(
            content=f"""
            <html>
                <head>
                    <title>Kite Connect - Authentication Successful</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }}
                        .success {{ color: #27ae60; }}
                        .info {{ background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 10px 0; }}
                        .code {{ background: #2c3e50; color: #ecf0f1; padding: 10px; border-radius: 3px; font-family: monospace; }}
                    </style>
                </head>
                <body>
                    <h1 class="success">✅ Authentication Successful!</h1>
                    
                    <div class="info">
                        <h3>User Information:</h3>
                        <p><strong>User ID:</strong> {token_data['user_id']}</p>
                        <p><strong>Name:</strong> {token_data['user_name']}</p>
                        <p><strong>Broker:</strong> {token_data['broker']}</p>
                        <p><strong>Email:</strong> {token_data['email']}</p>
                        <p><strong>Expires:</strong> {token_data['expires_at']}</p>
                    </div>
                    
                    <div class="info">
                        <h3>🎉 You're all set!</h3>
                        <p>Your access token has been saved and will be used automatically for all API calls.</p>
                        <p>You can now use the market data endpoints:</p>
                        
                        <div class="code">
                            # Test the API<br>
                            curl "http://localhost:8079/api/market/data?symbols=RELIANCE&scope=basic"<br><br>
                            
                            # Check auth status<br>
                            curl "http://localhost:8079/api/auth/status"<br><br>
                            
                            # API Documentation<br>
                            <a href="/docs" style="color: #3498db;">http://localhost:8079/docs</a>
                        </div>
                    </div>
                    
                    <div class="info">
                        <h3>📋 Available Endpoints:</h3>
                        <ul>
                            <li><strong>GET /api/market/data</strong> - Universal market data</li>
                            <li><strong>GET /api/market/portfolio</strong> - Portfolio management</li>
                            <li><strong>GET /api/market/context</strong> - Market overview</li>
                            <li><strong>GET /api/market/status</strong> - Service health</li>
                        </ul>
                    </div>
                    
                    <p><em>Note: The access token expires daily and you'll need to re-authenticate.</em></p>
                </body>
            </html>
            """
        )
        
    except Exception as e:
        logger.error(
            "Auth callback error",
            extra={
                "endpoint": "/auth/callback",
                "request_token": request_token[:8] + "..." if request_token else "empty",
                "error": str(e)
            },
            exc_info=True
        )
        
        return HTMLResponse(
            content=f"""
            <html>
                <head><title>Kite Connect - Authentication Error</title></head>
                <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px;">
                    <h1 style="color: #e74c3c;">❌ Authentication Error</h1>
                    <p>Failed to generate access token: {str(e)}</p>
                    <p><a href="/api/auth/login">Try again</a></p>
                </body>
            </html>
            """,
            status_code=500
        )


@router.post("/logout")
async def logout(
    auth_service: KiteAuthService = Depends(get_auth_service)
):
    """
    🚪 Logout from Kite Connect
    
    Clear stored access token and logout.
    """
    try:
        logger.info(
            "Logout request",
            extra={"endpoint": "/auth/logout"}
        )
        
        auth_service.clear_stored_token()
        
        logger.info(
            "Logout successful",
            extra={"endpoint": "/auth/logout"}
        )
        
        return {"success": True, "message": "Logged out successfully"}
        
    except Exception as e:
        logger.error(
            "Logout error",
            extra={
                "endpoint": "/auth/logout",
                "error": str(e)
            },
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="Failed to logout")


@router.get("/setup-instructions", response_class=HTMLResponse)
async def setup_instructions():
    """
    📋 Kite Connect Setup Instructions
    
    Instructions for setting up Kite Connect authentication.
    """
    return HTMLResponse(
        content="""
        <html>
            <head>
                <title>Kite Connect Setup Instructions</title>
                <style>
                    body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
                    .step { background: #f8f9fa; padding: 15px; margin: 15px 0; border-radius: 5px; }
                    .code { background: #2c3e50; color: #ecf0f1; padding: 10px; border-radius: 3px; font-family: monospace; }
                    .warning { background: #fff3cd; border: 1px solid #ffeaa7; padding: 10px; border-radius: 3px; }
                </style>
            </head>
            <body>
                <h1>🔐 Kite Connect Setup Instructions</h1>
                
                <div class="step">
                    <h3>Step 1: Create Kite Connect App</h3>
                    <ol>
                        <li>Go to <a href="https://developers.kite.trade/" target="_blank">Kite Connect Developer Portal</a></li>
                        <li>Login with your Zerodha account</li>
                        <li>Create a new app or use existing app</li>
                        <li>Note down your <strong>API Key</strong> and <strong>API Secret</strong></li>
                    </ol>
                </div>
                
                <div class="step">
                    <h3>Step 2: Configure Callback URL</h3>
                    <p>In your Kite Connect app settings, set the <strong>Redirect URL</strong> to:</p>
                    <div class="code">
                        http://localhost:8079/api/auth/callback
                    </div>
                    <p>For production, use your domain:</p>
                    <div class="code">
                        https://your-domain.com/api/auth/callback
                    </div>
                </div>
                
                <div class="step">
                    <h3>Step 3: Set Environment Variables</h3>
                    <p>Create a <code>.env</code> file in your project root with:</p>
                    <div class="code">
                        KITE_API_KEY=your_api_key_here<br>
                        KITE_API_SECRET=your_api_secret_here<br>
                        SERVICE_PORT=8079
                    </div>
                </div>
                
                <div class="step">
                    <h3>Step 4: Start Authentication Flow</h3>
                    <ol>
                        <li>Start your Kite Services: <code>python src/main.py</code></li>
                        <li>Get login URL: <a href="/api/auth/login">GET /api/auth/login</a></li>
                        <li>Click the login URL to authenticate with Zerodha</li>
                        <li>You'll be redirected back to the callback URL</li>
                        <li>Access token will be saved automatically</li>
                    </ol>
                </div>
                
                <div class="step">
                    <h3>Step 5: Test Your Setup</h3>
                    <p>Once authenticated, test with:</p>
                    <div class="code">
                        # Check auth status<br>
                        curl "http://localhost:8079/api/auth/status"<br><br>
                        
                        # Test market data<br>
                        curl "http://localhost:8079/api/market/data?symbols=RELIANCE&scope=basic"
                    </div>
                </div>
                
                <div class="warning">
                    <h4>⚠️ Important Notes:</h4>
                    <ul>
                        <li>Access tokens expire daily - you'll need to re-authenticate</li>
                        <li>Keep your API credentials secure and never commit them to version control</li>
                        <li>The callback URL must match exactly what's configured in Kite Connect</li>
                        <li>Make sure your server is running on the correct port (8079 for dev)</li>
                    </ul>
                </div>
                
                <div class="step">
                    <h3>🔗 Quick Links</h3>
                    <ul>
                        <li><a href="/api/auth/status">Check Authentication Status</a></li>
                        <li><a href="/api/auth/login">Get Login URL</a></li>
                        <li><a href="/docs">API Documentation</a></li>
                        <li><a href="https://kite.trade/docs/connect/v3/" target="_blank">Kite Connect Documentation</a></li>
                    </ul>
                </div>
            </body>
        </html>
        """
    )
