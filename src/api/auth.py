"""
Authentication API Module

Endpoints:
- POST /auth/credentials - Save api_key and api_secret only (first-time)
- GET /auth/login-url - Return Kite login URL (open in browser; Kite redirects to callback)
- GET /auth/callback - Kite redirects here with ?request_token=xxx; we exchange and save
- PUT /auth/token - Exchange request_token and save (body: request_token only)
- GET /auth/status - Authentication status
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse
from kiteconnect.exceptions import KiteException, TokenException

from common.time_utils import now_ist_naive
from config.settings import get_settings
from core.kite_exceptions import KiteErrorHandler
from core.service_manager import get_service_manager
from models.unified_api_models import (
    AuthResponse,
    AuthStatus,
    AuthStatusResponse,
    CredentialsRequest,
    CredentialsResponse,
    LoginUrlResponse,
    UpdateTokenRequest,
)

logger = logging.getLogger(__name__)
router = APIRouter()


async def _exchange_and_save_token(request_token: str, kite_client, settings) -> AuthResponse:
    """Exchange request_token for access_token and save. Shared by callback and PUT /auth/token."""
    api_key = kite_client.kite_config.api_key
    api_secret = kite_client.kite_config.api_secret
    if not api_key:
        raise HTTPException(
            status_code=400,
            detail="api_key not configured. Call POST /api/auth/credentials first.",
        )
    access_token = await kite_client.generate_access_token(
        request_token=request_token,
        api_secret=api_secret or settings.kite.api_secret,
    )
    if not access_token:
        raise HTTPException(status_code=401, detail="Failed to exchange request_token")
    success = kite_client.token_manager.update_token(
        access_token=access_token,
        api_key=api_key,
        api_secret=api_secret or "",
    )
    if not success:
        raise HTTPException(status_code=500, detail="Failed to save token")
    await kite_client.set_access_token(access_token)
    profile = await kite_client.get_profile_or_raise()
    token_info = kite_client.token_manager.get_token_info()
    token_refreshed_at = token_info.get("updated_at") if token_info else now_ist_naive().isoformat()
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
        message="Token saved successfully",
        token_refreshed_at=token_refreshed_at,
    )


@router.get("/auth/login-url", response_model=LoginUrlResponse)
async def get_login_url():
    """
    Return Kite Connect login URL. Open this URL in browser to log in;
    Kite redirects to callback with request_token, or copy request_token and call PUT /auth/token.
    """
    try:
        service_manager = await get_service_manager()
        kite_client = service_manager.kite_client
        login_url = kite_client.get_login_url()
        return LoginUrlResponse(login_url=login_url)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail="api_key not configured. Call POST /api/auth/credentials first.",
        ) from e
    except Exception as e:
        logger.error(f"Login URL failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/auth/callback", response_class=HTMLResponse)
async def auth_callback(
    request_token: str = Query(..., description="From Kite redirect after login"),
):
    """
    Callback URL for Kite redirect. Set in Kite app (e.g. https://your-host:8179/api/auth/callback).
    After login, Kite redirects here with request_token; we exchange and save.
    """
    try:
        service_manager = await get_service_manager()
        kite_client = service_manager.kite_client
        settings = get_settings()
        resp = await _exchange_and_save_token(request_token, kite_client, settings)
        logger.info(f"Callback: token saved for user {resp.user_id}")
        html = (
            f"<html><body><h1>Login successful</h1>"
            f"<p>User: {resp.user_name or resp.user_id}</p><p>Token saved.</p></body></html>"
        )
        return HTMLResponse(content=html, status_code=200)
    except HTTPException:
        raise
    except (TokenException, KiteException) as e:
        logger.error(f"Callback auth failed: {str(e)}")
        raise HTTPException(
            status_code=401, detail=KiteErrorHandler.get_graceful_response(e, "Callback")
        )
    except Exception as e:
        logger.error(f"Callback failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/auth/token", response_model=AuthResponse)
async def update_token(request: UpdateTokenRequest):
    """
    Exchange request_token for access_token and save. Body: {"request_token": "..."}.
    Use after opening login-url and getting request_token from Kite redirect.
    """
    try:
        service_manager = await get_service_manager()
        kite_client = service_manager.kite_client
        settings = get_settings()
        return await _exchange_and_save_token(request.request_token, kite_client, settings)
    except HTTPException:
        raise
    except (TokenException, KiteException) as e:
        logger.error(f"Token update failed: {str(e)}")
        raise HTTPException(
            status_code=401, detail=KiteErrorHandler.get_graceful_response(e, "Token")
        )
    except Exception as e:
        logger.error(f"Token update failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/auth/credentials", response_model=CredentialsResponse)
async def save_credentials(request: CredentialsRequest):
    """
    Save Kite API key and secret only (first-time use).

    Then set redirect URL in Kite app to https://your-api-host:8179/api/auth/callback.
    After login on Kite, callback receives request_token and saves the token automatically.
    Or call PUT /api/auth/token with request_token.
    """
    try:
        service_manager = await get_service_manager()
        kite_client = service_manager.kite_client
        success = kite_client.token_manager.save_credentials(
            api_key=request.api_key.strip(),
            api_secret=request.api_secret.strip(),
        )
        if not success:
            raise HTTPException(status_code=500, detail="Failed to save credentials")
        kite_client.reload_credentials_from_file()
        msg = (
            "Credentials saved. Set redirect URL in Kite app to .../api/auth/callback; "
            "after login token is saved. Or use PUT /api/auth/token with request_token."
        )
        return CredentialsResponse(success=True, message=msg)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Save credentials failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


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
