"""
Kite Connect Authentication Service
==================================

Service to handle Kite Connect OAuth flow and token management.
Follows workspace rules:
- Stateless service design
- Dependency injection
- Comprehensive logging to files
- Configuration-driven behavior
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional

from kiteconnect import KiteConnect

from config.settings import get_settings
from core.logging_config import get_logger


class KiteAuthService:
    """
    Service for Kite Connect authentication and token management.

    Handles:
    - Login URL generation
    - Access token generation from request token
    - Token storage and retrieval
    - Token validation and refresh
    """

    def __init__(self, logger: Optional[Any] = None):
        """Initialize Kite authentication service."""
        self.settings = get_settings()
        self.logger = logger or get_logger(__name__)

        # Initialize Kite Connect
        self.kite = KiteConnect(api_key=self.settings.kite.api_key)

        # Token storage path
        self.token_file = Path(self.settings.kite.credentials_file)

        self.logger.info(
            "KiteAuthService initialized",
            extra={
                "service": "kite_auth_service",
                "api_key": (
                    self.settings.kite.api_key[:8] + "..."
                    if self.settings.kite.api_key
                    else "not_set"
                ),
                "token_file": str(self.token_file),
            },
        )

    def get_login_url(self) -> str:
        """
        Generate Kite Connect login URL for OAuth flow.

        Returns:
            str: Login URL for user authentication
        """
        try:
            login_url = self.kite.login_url()

            self.logger.info(
                "Generated Kite login URL",
                extra={"service": "kite_auth_service", "login_url": login_url},
            )

            return login_url

        except Exception as e:
            self.logger.error(
                "Failed to generate login URL",
                extra={"service": "kite_auth_service", "error": str(e)},
                exc_info=True,
            )
            raise

    def generate_access_token(self, request_token: str) -> Dict[str, Any]:
        """
        Generate access token from request token.

        Args:
            request_token: Request token from Kite Connect callback

        Returns:
            Dict containing access token and user details
        """
        try:
            self.logger.info(
                "Generating access token",
                extra={
                    "service": "kite_auth_service",
                    "request_token": request_token[:8] + "..." if request_token else "empty",
                },
            )

            # Generate session
            data = self.kite.generate_session(
                request_token=request_token, api_secret=self.settings.kite.api_secret
            )

            # Store token data
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
                "generated_at": datetime.now().isoformat(),
                "expires_at": (
                    datetime.now() + timedelta(hours=24)
                ).isoformat(),  # Kite tokens expire daily
            }

            # Save to file
            self._save_token_data(token_data)

            # Set access token in kite instance
            self.kite.set_access_token(data["access_token"])

            self.logger.info(
                "Access token generated successfully",
                extra={
                    "service": "kite_auth_service",
                    "user_id": data["user_id"],
                    "user_name": data["user_name"],
                    "broker": data["broker"],
                    "expires_at": token_data["expires_at"],
                },
            )

            return token_data

        except Exception as e:
            self.logger.error(
                "Failed to generate access token",
                extra={
                    "service": "kite_auth_service",
                    "request_token": request_token[:8] + "..." if request_token else "empty",
                    "error": str(e),
                },
                exc_info=True,
            )
            raise

    def load_stored_token(self) -> Optional[Dict[str, Any]]:
        """
        Load stored access token from file.

        Returns:
            Dict containing token data if valid, None otherwise
        """
        try:
            if not self.token_file.exists():
                self.logger.warning(
                    "Token file does not exist",
                    extra={"service": "kite_auth_service", "token_file": str(self.token_file)},
                )
                return None

            with open(self.token_file, "r") as f:
                token_data = json.load(f)

            # Check if token is expired
            expires_at = datetime.fromisoformat(token_data.get("expires_at", ""))
            if datetime.now() >= expires_at:
                self.logger.warning(
                    "Stored token is expired",
                    extra={
                        "service": "kite_auth_service",
                        "expires_at": token_data["expires_at"],
                        "current_time": datetime.now().isoformat(),
                    },
                )
                return None

            # Set access token in kite instance
            self.kite.set_access_token(token_data["access_token"])

            self.logger.info(
                "Loaded stored token successfully",
                extra={
                    "service": "kite_auth_service",
                    "user_id": token_data.get("user_id"),
                    "expires_at": token_data["expires_at"],
                },
            )

            return token_data

        except Exception as e:
            self.logger.error(
                "Failed to load stored token",
                extra={
                    "service": "kite_auth_service",
                    "token_file": str(self.token_file),
                    "error": str(e),
                },
                exc_info=True,
            )
            return None

    def validate_token(self) -> bool:
        """
        Validate current access token by making a test API call.

        Returns:
            bool: True if token is valid, False otherwise
        """
        try:
            # Try to get user profile to validate token
            profile = self.kite.profile()

            self.logger.info(
                "Token validation successful",
                extra={
                    "service": "kite_auth_service",
                    "user_id": profile.get("user_id"),
                    "user_name": profile.get("user_name"),
                },
            )

            return True

        except Exception as e:
            self.logger.warning(
                "Token validation failed", extra={"service": "kite_auth_service", "error": str(e)}
            )
            return False

    def get_kite_instance(self) -> Optional[KiteConnect]:
        """
        Get authenticated Kite Connect instance.

        Returns:
            KiteConnect instance if authenticated, None otherwise
        """
        # Try to load stored token first
        token_data = self.load_stored_token()

        if token_data and self.validate_token():
            return self.kite

        self.logger.warning(
            "No valid Kite Connect instance available",
            extra={
                "service": "kite_auth_service",
                "message": "Need to authenticate with fresh token",
            },
        )
        return None

    def _save_token_data(self, token_data: Dict[str, Any]) -> None:
        """Save token data to file."""
        try:
            # Create directory if it doesn't exist
            self.token_file.parent.mkdir(parents=True, exist_ok=True)

            # Save token data
            with open(self.token_file, "w") as f:
                json.dump(token_data, f, indent=2)

            # Set file permissions (readable only by owner)
            self.token_file.chmod(0o600)

            self.logger.info(
                "Token data saved successfully",
                extra={
                    "service": "kite_auth_service",
                    "token_file": str(self.token_file),
                    "user_id": token_data.get("user_id"),
                },
            )

        except Exception as e:
            self.logger.error(
                "Failed to save token data",
                extra={
                    "service": "kite_auth_service",
                    "token_file": str(self.token_file),
                    "error": str(e),
                },
                exc_info=True,
            )
            raise

    def clear_stored_token(self) -> None:
        """Clear stored token data."""
        try:
            if self.token_file.exists():
                self.token_file.unlink()

            self.logger.info(
                "Stored token cleared",
                extra={"service": "kite_auth_service", "token_file": str(self.token_file)},
            )

        except Exception as e:
            self.logger.error(
                "Failed to clear stored token",
                extra={"service": "kite_auth_service", "error": str(e)},
                exc_info=True,
            )

    def get_auth_status(self) -> Dict[str, Any]:
        """
        Get current authentication status.

        Returns:
            Dict containing authentication status information
        """
        status = {
            "authenticated": False,
            "token_exists": self.token_file.exists(),
            "token_valid": False,
            "user_info": None,
            "expires_at": None,
            "login_url": None,
        }

        try:
            # Check if token file exists and load it
            token_data = self.load_stored_token()

            if token_data:
                status["expires_at"] = token_data.get("expires_at")
                status["user_info"] = {
                    "user_id": token_data.get("user_id"),
                    "user_name": token_data.get("user_name"),
                    "broker": token_data.get("broker"),
                }

                # Validate token
                if self.validate_token():
                    status["authenticated"] = True
                    status["token_valid"] = True
                else:
                    # Token exists but is invalid, provide login URL
                    status["login_url"] = self.get_login_url()
            else:
                # No token, provide login URL
                status["login_url"] = self.get_login_url()

        except Exception as e:
            self.logger.error(
                "Failed to get auth status",
                extra={"service": "kite_auth_service", "error": str(e)},
                exc_info=True,
            )
            status["error"] = str(e)

        return status
