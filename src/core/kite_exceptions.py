"""
Kite Exception Handling
========================

Centralized exception handling for Kite Connect API.
Provides graceful error responses and token expiry detection.
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from kiteconnect.exceptions import (
    InputException,
    KiteException,
    NetworkException,
    OrderException,
    PermissionException,
    TokenException,
)

logger = logging.getLogger(__name__)


class TokenExpiredException(Exception):
    """Raised when Kite access token has expired."""

    pass


class KiteErrorHandler:
    """Centralized error handler for Kite Connect exceptions."""

    @staticmethod
    def is_token_expired(error: Exception) -> bool:
        """
        Check if the error indicates an expired token.

        Args:
            error: Exception raised by Kite Connect

        Returns:
            bool: True if token is expired
        """
        if isinstance(error, TokenException):
            return True

        # Check error message for token-related errors
        error_msg = str(error).lower()
        token_indicators = [
            "token",
            "session",
            "expired",
            "invalid api_key or access_token",
            "unauthorized",
            "403",
            "401",
        ]

        return any(indicator in error_msg for indicator in token_indicators)

    @staticmethod
    def get_graceful_response(
        error: Exception, context: str = "API call", include_refresh_url: bool = True
    ) -> Dict[str, Any]:
        """
        Generate a graceful error response.

        Args:
            error: The exception that occurred
            context: Context of where the error occurred
            include_refresh_url: Whether to include token refresh URL

        Returns:
            Dict containing graceful error response
        """
        error_type = type(error).__name__
        error_msg = str(error)

        # Check if token expired
        if KiteErrorHandler.is_token_expired(error):
            logger.warning(f"🔑 Token expired during {context}: {error_msg}")

            response = {
                "success": False,
                "error": "token_expired",
                "error_type": "TokenExpired",
                "message": (
                    "Your Kite access token has expired. Please refresh your token to continue."
                ),  # noqa: E501
                "details": {
                    "context": context,
                    "error_message": error_msg,
                    "requires_action": "token_refresh",
                    "token_expiry_note": "Kite tokens expire daily at 6:00 AM IST",
                },
                "timestamp": datetime.now().isoformat(),
            }

            if include_refresh_url:
                response["action_required"] = {
                    "type": "token_refresh",
                    "steps": [
                        "1. Open Kite login URL",
                        "2. Complete login and get request_token",
                        "3. Call POST /api/auth/login with request_token",
                    ],
                    "endpoints": {
                        "check_status": "GET /api/auth/status",
                        "refresh_token": "POST /api/auth/login",
                    },
                    "docs": "See docs/integration/token-flow-setup.md for token flow",
                }

            return response

        # Handle other Kite exceptions
        elif isinstance(error, PermissionException):
            return {
                "success": False,
                "error": "permission_denied",
                "error_type": "PermissionDenied",
                "message": "You don't have permission to perform this action.",  # noqa: E501
                "details": {"context": context, "error_message": error_msg},
                "timestamp": datetime.now().isoformat(),
            }

        elif isinstance(error, NetworkException):
            return {
                "success": False,
                "error": "network_error",
                "error_type": "NetworkError",
                "message": "Unable to connect to Kite servers. Please check your internet connection.",  # noqa: E501
                "details": {
                    "context": context,
                    "error_message": error_msg,
                    "retry_after": "30 seconds",
                },
                "timestamp": datetime.now().isoformat(),
            }

        elif isinstance(error, InputException):
            return {
                "success": False,
                "error": "invalid_input",
                "error_type": "InvalidInput",
                "message": "Invalid input provided to the API.",
                "details": {"context": context, "error_message": error_msg},
                "timestamp": datetime.now().isoformat(),
            }

        elif isinstance(error, OrderException):
            return {
                "success": False,
                "error": "order_error",
                "error_type": "OrderError",
                "message": "Order placement or modification failed.",
                "details": {"context": context, "error_message": error_msg},
                "timestamp": datetime.now().isoformat(),
            }

        # Generic Kite exception
        elif isinstance(error, KiteException):
            return {
                "success": False,
                "error": "kite_api_error",
                "error_type": error_type,
                "message": f"Kite API error: {error_msg}",
                "details": {"context": context, "error_message": error_msg},
                "timestamp": datetime.now().isoformat(),
            }

        # Unknown error
        else:
            return {
                "success": False,
                "error": "unknown_error",
                "error_type": error_type,
                "message": "An unexpected error occurred.",
                "details": {"context": context, "error_message": error_msg},
                "timestamp": datetime.now().isoformat(),
            }

    @staticmethod
    def wrap_kite_call(func_name: str):
        """
        Decorator to wrap Kite API calls with graceful error handling.

        Usage:
            @KiteErrorHandler.wrap_kite_call("get_quote")
            async def get_quote(self, symbol):
                # ... Kite API call
        """

        def decorator(func):
            async def wrapper(*args, **kwargs):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    logger.error(f"Error in {func_name}: {e}")
                    if KiteErrorHandler.is_token_expired(e):
                        raise TokenExpiredException(
                            KiteErrorHandler.get_graceful_response(e, func_name)
                        )
                    raise

            return wrapper

        return decorator


def handle_kite_error(
    error: Exception,
    context: str = "API call",
    fallback_data: Optional[Dict[str, Any]] = None,
    include_fallback: bool = True,
) -> Dict[str, Any]:
    """
    Handle Kite errors with optional fallback data.

    Args:
        error: The exception that occurred
        context: Context of where the error occurred
        fallback_data: Optional fallback data to return
        include_fallback: Whether to include fallback data in response

    Returns:
        Dict containing error response and optional fallback data
    """
    error_response = KiteErrorHandler.get_graceful_response(error, context)

    if include_fallback and fallback_data:
        error_response["fallback_data"] = fallback_data
        error_response["using_fallback"] = True
        error_response["message"] += " Using fallback data."

    return error_response
