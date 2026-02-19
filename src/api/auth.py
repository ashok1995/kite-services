"""
Authentication API Module

Consolidated authentication endpoints for Kite Services.
Provides complete authentication flow and status checking.

Endpoints:
- POST /auth/login - Complete authentication flow
- GET /auth/status - Authentication status
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from kiteconnect.exceptions import KiteException, TokenException

from common.time_utils import now_ist_naive
from config.settings import get_settings
from core.kite_exceptions import KiteErrorHandler
from core.service_manager import get_service_manager
from models.unified_api_models import (
    AuthRequest,
    AuthResponse,
    AuthStatus,
    AuthStatusResponse,
    LoginUrlResponse,
    UpdateTokenRequest,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/auth/login-url", response_model=LoginUrlResponse)
async def get_login_url():
    """
    Get Kite Connect login URL.
    Open this URL in browser, log in, and copy request_token from redirect URL.
    Then POST to /api/auth/login with that request_token.
    """
    try:
        service_manager = await get_service_manager()
        kite_client = service_manager.kite_client
        login_url = kite_client.get_login_url()
        return LoginUrlResponse(
            login_url=login_url,
            message="Open URL, login, copy request_token from redirect",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get login URL: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
            logger.info("Generating access token from request token")

            # Generate access token
            settings = get_settings()
            access_token = await kite_client.generate_access_token(
                request_token=request.request_token,
                api_secret=request.api_secret or settings.kite.api_secret,
            )

            if not access_token:
                raise HTTPException(status_code=400, detail="Failed to generate access token")

            # Set the access token
            await kite_client.set_access_token(access_token)

        # Handle direct access token
        elif request.access_token:
            logger.info("Validating provided access token")
            await kite_client.set_access_token(request.access_token)

        # Get user profile
        profile = await kite_client.get_profile()
        if not profile:
            raise HTTPException(
                status_code=401, detail="Failed to fetch user profile - invalid token"
            )

        # Validate margins/permissions (required for token validation)
        await kite_client.get_margins()

        token_info = kite_client.token_manager.get_token_info()
        token_refreshed_at = (
            token_info.get("updated_at") if token_info else now_ist_naive().isoformat()
        )
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
            message="Authentication successful",
            token_refreshed_at=token_refreshed_at,
        )

    except (TokenException, KiteException) as e:
        logger.error(f"Authentication failed: {str(e)}")
        error_response = KiteErrorHandler.get_graceful_response(e, "Authentication")
        raise HTTPException(status_code=401, detail=error_response)

    except Exception as e:
        logger.error(f"Authentication failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "authentication_failed",
                "message": f"Authentication failed: {str(e)}",
                "timestamp": now_ist_naive().isoformat(),
            },
        )


@router.put("/auth/token", response_model=AuthResponse)
async def update_token(request: UpdateTokenRequest):
    """
    Update access token in configured token file (e.g. ~/.kite-services/kite_token.json).

    Saves token outside project so it survives git pull. Automatically reloaded by service.
    """
    try:
        service_manager = await get_service_manager()
        kite_client = service_manager.kite_client

        # Save token to file
        success = kite_client.token_manager.update_token(
            access_token=request.access_token, user_id=request.user_id
        )

        if not success:
            raise HTTPException(status_code=500, detail="Failed to save token to file")

        # Update Kite client with new token
        await kite_client.set_access_token(request.access_token)

        # Get profile to verify token
        profile = await kite_client.get_profile()
        if not profile:
            raise HTTPException(
                status_code=401, detail="Token saved but validation failed - token may be invalid"
            )

        logger.info(f"✅ Token updated successfully for user: {profile.get('user_id')}")

        token_info = kite_client.token_manager.get_token_info()
        token_refreshed_at = (
            token_info.get("updated_at") if token_info else now_ist_naive().isoformat()
        )
        return AuthResponse(
            status=AuthStatus.AUTHENTICATED,
            access_token=request.access_token,
            user_id=profile.get("user_id"),
            user_name=profile.get("user_name"),
            email=profile.get("email"),
            broker=profile.get("broker"),
            exchanges=profile.get("exchanges", []),
            products=profile.get("products", []),
            order_types=profile.get("order_types", []),
            message="Token updated successfully",
            token_refreshed_at=token_refreshed_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token update failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Token update failed: {str(e)}")


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

        def _token_refreshed_at() -> Optional[str]:
            """Get token refreshed time in IST from token file."""
            token_info = kite_client.token_manager.get_token_info()
            return token_info.get("updated_at") if token_info else None

        # Check if we have credentials configured (api_key from token file)
        if not kite_client.kite_config.api_key:
            return AuthStatusResponse(
                status=AuthStatus.NOT_CONFIGURED,
                authenticated=False,
                token_valid=False,
                message="Kite credentials not configured (create ~/.kite-services/kite_token.json)",
            )

        # Check if we have an access token (load_token populates token_info)
        kite_client.token_manager.load_token()
        access_token = await kite_client.get_access_token()
        if not access_token:
            return AuthStatusResponse(
                status=AuthStatus.INVALID,
                authenticated=False,
                token_valid=False,
                message="No access token available",
                token_refreshed_at=_token_refreshed_at(),
            )

        # Verify token via Kite API - only return valid when profile call succeeds
        try:
            profile = await kite_client.get_profile()
            if profile:
                return AuthStatusResponse(
                    status=AuthStatus.AUTHENTICATED,
                    authenticated=True,
                    token_valid=True,
                    user_id=profile.get("user_id"),
                    user_name=profile.get("user_name"),
                    broker=profile.get("broker"),
                    message="Token verified via Kite API (profile)",
                    token_refreshed_at=_token_refreshed_at(),
                )
            return AuthStatusResponse(
                status=AuthStatus.INVALID,
                authenticated=False,
                token_valid=False,
                message="Invalid or expired token",
                token_refreshed_at=_token_refreshed_at(),
            )
        except Exception as e:
            logger.warning(f"Token validation failed: {str(e)}")
            return AuthStatusResponse(
                status=AuthStatus.EXPIRED,
                authenticated=False,
                token_valid=False,
                message=f"Token verification failed: {str(e)}",
                token_refreshed_at=_token_refreshed_at(),
            )

    except Exception as e:
        logger.error(f"Auth status check failed: {str(e)}")
        return AuthStatusResponse(
            status=AuthStatus.INVALID,
            authenticated=False,
            token_valid=False,
            message=f"Auth status check failed: {str(e)}",
            token_refreshed_at=None,
        )
