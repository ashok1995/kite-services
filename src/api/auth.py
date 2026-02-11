"""
Authentication API Module

Consolidated authentication endpoints for Kite Services.
Provides complete authentication flow and status checking.

Endpoints:
- POST /auth/login - Complete authentication flow
- GET /auth/status - Authentication status
"""

import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from kiteconnect.exceptions import KiteException, TokenException

from config.settings import get_settings
from core.kite_exceptions import KiteErrorHandler
from core.logging_config import get_logger
from core.service_manager import get_service_manager
from models.unified_api_models import (
    AuthRequest,
    AuthResponse,
    AuthStatus,
    AuthStatusResponse,
    CredentialsRequest,
    CredentialsStatusResponse,
    LoginUrlResponse,
    TokenStatusResponse,
    UpdateTokenRequest,
)

logger = logging.getLogger(__name__)
auth_logger = get_logger(__name__)
router = APIRouter()


def _mask(s: str, visible: int = 4) -> str:
    """Mask sensitive value for logging (show first N chars)."""
    if not s:
        return "<empty>"
    if len(s) <= visible:
        return "***"
    return s[:visible] + "*" * min(len(s) - visible, 4) + "..."


@router.get("/auth/credentials/status", response_model=CredentialsStatusResponse)
async def get_credentials_status():
    """
    Check if api_key is configured. Use before showing credential input.
    """
    try:
        sm = await get_service_manager()
        configured = bool(sm.kite_client.kite_config.api_key)
        return CredentialsStatusResponse(
            api_key_configured=configured,
            message=None if configured else "Add api_key via POST /api/auth/credentials",
        )
    except Exception:
        return CredentialsStatusResponse(api_key_configured=False, message="Service not ready")


@router.post("/auth/credentials")
async def save_credentials(request: CredentialsRequest):
    """
    Save api_key (and api_secret) from web. Required before login flow.
    api_secret needed to exchange request_token for access_token.
    """
    auth_logger.info(
        "save_credentials called",
        extra={
            "api_key_masked": _mask(request.api_key) if request.api_key else "<none>",
            "api_secret_provided": bool(request.api_secret and request.api_secret.strip()),
        },
    )
    try:
        sm = await get_service_manager()
        auth_logger.info(
            "save_credentials: got service_manager, calling token_manager.save_credentials"
        )
        success = sm.kite_client.token_manager.save_credentials(
            api_key=request.api_key, api_secret=request.api_secret or ""
        )
        if not success:
            auth_logger.error("save_credentials: token_manager.save_credentials returned False")
            raise HTTPException(status_code=500, detail="Failed to save credentials")
        auth_logger.info("save_credentials: file saved, reloading api_credentials")
        sm.kite_client.reload_api_credentials()
        auth_logger.info("save_credentials: success")
        return {"success": True, "message": "Credentials saved. Use callback URL for login."}
    except HTTPException:
        raise
    except Exception as e:
        auth_logger.error(
            "save_credentials failed",
            extra={"error": str(e), "error_type": type(e).__name__},
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/token/callback-url")
async def get_callback_url(request: Request):
    """
    Get callback URL for Kite app Redirect URL at developers.kite.trade.
    """
    settings = get_settings()
    base = (getattr(settings.service, "callback_base_url", None) or "").strip() or str(
        request.base_url
    ).rstrip("/")
    api_key_configured = False
    try:
        sm = await get_service_manager()
        api_key_configured = bool(sm.kite_client.kite_config.api_key)
    except Exception:
        pass
    callback_url = f"{base}/api/redirect"
    return {
        "callback_url": callback_url,
        "configured": api_key_configured,
        "message": (
            "Configure in Kite app. Add api_key/api_secret to token file if not done."
            if not api_key_configured
            else None
        ),
    }


@router.get(
    "/redirect",
    response_class=HTMLResponse,
    include_in_schema=False,
)
@router.get(
    "/auth/callback",
    response_class=HTMLResponse,
    include_in_schema=False,
)
async def auth_callback(
    request_token: str | None = Query(None),
    status: str | None = Query(None),
    action: str | None = Query(None),
    type: str | None = Query(None),
):
    """
    Kite OAuth callback. Kite redirects here after login with request_token.

    Supports both formats:
    - /api/redirect?action=login&type=login&status=success&request_token=XXX
    - /api/auth/callback?request_token=XXX&status=success

    Set Redirect URL in Kite app at developers.kite.trade to: {base}/api/redirect
    """
    if not request_token:
        return _callback_html(
            error="No request_token in URL. Ensure Kite app Redirect URL matches this endpoint.",
        )
    status_ok = (status or "").lower() == "success"
    return _callback_html(
        request_token=request_token,
        status_ok=status_ok,
    )


def _callback_html(
    request_token: str | None = None,
    status_ok: bool = True,
    error: str | None = None,
) -> str:
    """Return HTML page for auth callback."""
    if error:
        return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Kite Callback</title></head>
<body style="font-family:sans-serif;padding:40px;max-width:600px;margin:0 auto;">
<h2>Kite OAuth Callback</h2>
<p style="color:#c00;">{error}</p>
<p>Configure the Redirect URL in your <a href="https://developers.kite.trade">Kite Connect app</a>
to match this page's URL.</p>
</body></html>"""  # noqa: E501
    copy_instruction = (
        "Copy the request token below and paste it in your token flow UI, then use "
        "POST /api/auth/login to exchange for access token."  # noqa: E501
        if request_token
        else ""
    )
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Kite Callback</title></head>
<body style="font-family:sans-serif;padding:40px;max-width:600px;margin:0 auto;">
<h2>Kite Login Successful</h2>
<p>Request token received. {copy_instruction}</p>
<div style="background:#f0f0f0;padding:12px;border-radius:6px;word-break:break-all;">
<strong>request_token:</strong><br><code id="tok">{request_token or ''}</code>
</div>
<button onclick="navigator.clipboard.writeText(document.getElementById('tok').textContent)">
Copy to clipboard</button>
</body></html>"""  # noqa: E501


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
                "timestamp": datetime.now().isoformat(),
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
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token update failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Token update failed: {str(e)}")


@router.get("/auth/token-status", response_model=TokenStatusResponse)
async def get_token_status():
    """
    Diagnostic endpoint for access token status.

    Use when services (quotes, trading, opportunities) fail - helps identify
    if the issue is missing/invalid token. Works even when market is closed.
    """
    try:
        service_manager = await get_service_manager()
        kite_client = service_manager.kite_client
        token_manager = kite_client.token_manager

        api_key_ok = bool(kite_client.kite_config.api_key)
        token_str = await kite_client.get_access_token()
        access_token_ok = bool(token_str and len(token_str) >= 10)
        kite_ok = kite_client.kite is not None
        token_path = str(token_manager.token_file)

        profile_ok = False
        if kite_ok and access_token_ok:
            try:
                profile = await kite_client.get_profile()
                profile_ok = profile is not None and bool(profile)
            except Exception:
                pass

        if profile_ok:
            msg = "Token valid - all Kite APIs (quotes, trading) should work"
            action = None
        elif not api_key_ok:
            msg = "api_key not configured - add to token file via POST /api/auth/credentials"
            action = (
                "1. Add api_key and api_secret to token file\n"
                "2. Use GET /api/auth/login-url then POST /api/auth/login"
            )  # noqa: E501
        elif not access_token_ok:
            msg = "No access_token in file - complete login flow"
            action = (
                "1. GET /api/auth/login-url\n"
                "2. Open URL, login, copy request_token from redirect\n"
                "3. POST /api/auth/login with request_token"
            )  # noqa: E501
        else:
            msg = "Token invalid or expired (Kite tokens expire daily at 6 AM IST)"
            action = (
                "1. GET /api/auth/login-url\n"
                "2. Open URL, login, copy request_token\n"
                "3. POST /api/auth/login with request_token"
            )  # noqa: E501

        return TokenStatusResponse(
            api_key_configured=api_key_ok,
            access_token_present=access_token_ok,
            token_file_path=token_path,
            kite_client_initialized=kite_ok,
            profile_verified=profile_ok,
            message=msg,
            action_required=action,
        )
    except Exception as e:
        logger.error(f"Token status check failed: {str(e)}")
        return TokenStatusResponse(
            api_key_configured=False,
            access_token_present=False,
            token_file_path="unknown",
            kite_client_initialized=False,
            profile_verified=False,
            message=f"Token status check failed: {str(e)}",
            action_required="Ensure service is running and token file exists",
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

        # Check if we have credentials configured (api_key from token file)
        if not kite_client.kite_config.api_key:
            return AuthStatusResponse(
                status=AuthStatus.NOT_CONFIGURED,
                authenticated=False,
                token_valid=False,
                message="Kite credentials not configured (create ~/.kite-services/kite_token.json)",
            )

        # Check if we have an access token
        access_token = await kite_client.get_access_token()
        if not access_token:
            return AuthStatusResponse(
                status=AuthStatus.INVALID,
                authenticated=False,
                token_valid=False,
                message="No access token available",
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
                )
            return AuthStatusResponse(
                status=AuthStatus.INVALID,
                authenticated=False,
                token_valid=False,
                message="Invalid or expired token",
            )
        except Exception as e:
            logger.warning(f"Token validation failed: {str(e)}")
            return AuthStatusResponse(
                status=AuthStatus.EXPIRED,
                authenticated=False,
                token_valid=False,
                message=f"Token verification failed: {str(e)}",
            )

    except Exception as e:
        logger.error(f"Auth status check failed: {str(e)}")
        return AuthStatusResponse(
            status=AuthStatus.INVALID,
            authenticated=False,
            token_valid=False,
            message=f"Auth status check failed: {str(e)}",
        )
