"""
Authentication API Module

Consolidated authentication endpoints for Kite Services.
Provides complete authentication flow and status checking.

Endpoints:
- POST /auth/login - Complete authentication flow
- GET /auth/status - Authentication status
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from datetime import datetime
import logging

from models.unified_api_models import (
    AuthRequest, AuthResponse, AuthStatusResponse, AuthStatus,
    ErrorResponse
)
from core.kite_client import KiteClient
from core.service_manager import get_service_manager
from core.kite_exceptions import KiteErrorHandler
from kiteconnect.exceptions import TokenException, KiteException
from config.settings import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/auth/login", response_model=AuthResponse)
async def authenticate(request: AuthRequest):
    """
    Complete authentication flow for Kite Connect.
    
    Handles both token generation and validation:
    - If request_token provided: Generate access token
    - If access_token provided: Validate existing token
    - Returns user profile and trading permissions
    """
    try:
        service_manager = await get_service_manager()
        kite_client = service_manager.kite_client
        
        # Handle token generation
        if request.request_token:
            logger.info(f"Generating access token from request token")
            
            # Generate access token
            settings = get_settings()
            access_token = await kite_client.generate_access_token(
                request_token=request.request_token,
                api_secret=request.api_secret or settings.kite.api_secret
            )
            
            if not access_token:
                raise HTTPException(
                    status_code=400,
                    detail="Failed to generate access token"
                )
            
            # Set the access token
            await kite_client.set_access_token(access_token)
        
        # Handle direct access token
        elif request.access_token:
            logger.info(f"Validating provided access token")
            await kite_client.set_access_token(request.access_token)
        
        # Get user profile
        profile = await kite_client.get_profile()
        if not profile:
            raise HTTPException(
                status_code=401,
                detail="Failed to fetch user profile - invalid token"
            )
        
        # Get user margins and permissions
        margins = await kite_client.get_margins()
        
        return AuthResponse(
            status=AuthStatus.AUTHENTICATED,
            access_token=await kite_client.get_access_token(),
            user_id=profile.get("user_id"),
            user_name=profile.get("user_name"),
            email=profile.get("email"),
            broker=profile.get("broker"),
            exchanges=profile.get("exchanges", []),
            products=profile.get("products", []),
            order_types=profile.get("order_types", []),
            message="Authentication successful"
        )
        
    except (TokenException, KiteException) as e:
        logger.error(f"Authentication failed: {str(e)}")
        error_response = KiteErrorHandler.get_graceful_response(e, "Authentication")
        raise HTTPException(
            status_code=401,
            detail=error_response
        )
    
    except Exception as e:
        logger.error(f"Authentication failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "authentication_failed",
                "message": f"Authentication failed: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
        )


@router.put("/auth/token", response_model=AuthResponse)
async def update_token(access_token: str, user_id: Optional[str] = None):
    """
    Update access token in token file.
    
    This endpoint allows updating the access token without restarting the service.
    The token is saved to kite_token.json and automatically reloaded by the service.
    
    Args:
        access_token: The new access token
        user_id: Optional user ID for metadata
    
    Returns:
        AuthResponse with updated token information
    """
    try:
        service_manager = await get_service_manager()
        kite_client = service_manager.kite_client
        
        # Save token to file
        success = kite_client.token_manager.update_token(
            access_token=access_token,
            user_id=user_id
        )
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to save token to file"
            )
        
        # Update Kite client with new token
        await kite_client.set_access_token(access_token)
        
        # Get profile to verify token
        profile = await kite_client.get_profile()
        if not profile:
            raise HTTPException(
                status_code=401,
                detail="Token saved but validation failed - token may be invalid"
            )
        
        logger.info(f"✅ Token updated successfully for user: {profile.get('user_id')}")
        
        return AuthResponse(
            status=AuthStatus.AUTHENTICATED,
            access_token=access_token,
            user_id=profile.get("user_id"),
            user_name=profile.get("user_name"),
            email=profile.get("email"),
            broker=profile.get("broker"),
            exchanges=profile.get("exchanges", []),
            products=profile.get("products", []),
            order_types=profile.get("order_types", []),
            message="Token updated successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token update failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Token update failed: {str(e)}"
        )


@router.get("/auth/status", response_model=AuthStatusResponse)
async def get_auth_status():
    """
    Get current authentication status and user information.
    
    Returns:
    - Authentication status (authenticated, expired, invalid, not_configured)
    - User information if authenticated
    - Token expiry information
    """
    try:
        service_manager = await get_service_manager()
        kite_client = service_manager.kite_client
        
        # Check if we have credentials configured
        if not kite_client.kite_config.api_key or not kite_client.kite_config.api_secret:
            return AuthStatusResponse(
                status=AuthStatus.NOT_CONFIGURED,
                authenticated=False,
                message="Kite credentials not configured"
            )

        # Check if we have an access token
        access_token = await kite_client.get_access_token()
        if not access_token:
            return AuthStatusResponse(
                status=AuthStatus.INVALID,
                authenticated=False,
                message="No access token available"
            )
        
        # Test the token by getting profile
        try:
            profile = await kite_client.get_profile()
            if profile:
                return AuthStatusResponse(
                    status=AuthStatus.AUTHENTICATED,
                    authenticated=True,
                    user_id=profile.get("user_id"),
                    user_name=profile.get("user_name"),
                    broker=profile.get("broker"),
                    message="Token is valid and active"
                )
            else:
                return AuthStatusResponse(
                    status=AuthStatus.INVALID,
                    authenticated=False,
                    message="Invalid or expired token"
                )
                
        except Exception as e:
            logger.warning(f"Token validation failed: {str(e)}")
            return AuthStatusResponse(
                status=AuthStatus.EXPIRED,
                authenticated=False,
                message=f"Token validation failed: {str(e)}"
            )
            
    except Exception as e:
        logger.error(f"Auth status check failed: {str(e)}")
        return AuthStatusResponse(
            status=AuthStatus.INVALID,
            authenticated=False,
            message=f"Auth status check failed: {str(e)}"
        )
