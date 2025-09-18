"""
Kite Connect Credentials Manager
===============================

Manages Kite Connect API credentials with secure storage and validation.
Supports both file-based and environment variable credential sources.
"""

import json
import os
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from config.settings import get_settings

logger = logging.getLogger(__name__)


@dataclass
class KiteCredentials:
    """Kite Connect credentials container."""
    api_key: str
    api_secret: str
    access_token: str
    user_id: Optional[str] = None
    user_name: Optional[str] = None
    
    def is_valid(self) -> bool:
        """Check if credentials are valid."""
        return bool(self.api_key and self.api_secret and self.access_token)
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary."""
        return {
            "api_key": self.api_key,
            "api_secret": self.api_secret,
            "access_token": self.access_token,
            "user_id": self.user_id or "",
            "user_name": self.user_name or ""
        }


class KiteCredentialsManager:
    """Manages Kite Connect credentials with multiple sources."""
    
    def __init__(self):
        self.settings = get_settings()
        self.kite_config = self.settings.kite
        self._credentials: Optional[KiteCredentials] = None
        
    def load_credentials(self) -> KiteCredentials:
        """Load credentials from multiple sources in order of priority."""
        logger.info("Loading Kite Connect credentials...")
        
        # Try environment variables first
        env_credentials = self._load_from_environment()
        if env_credentials and env_credentials.is_valid():
            logger.info("✅ Credentials loaded from environment variables")
            self._credentials = env_credentials
            return env_credentials
        
        # Try credentials file
        file_credentials = self._load_from_file()
        if file_credentials and file_credentials.is_valid():
            logger.info("✅ Credentials loaded from file")
            self._credentials = file_credentials
            return file_credentials
        
        # Try settings configuration
        settings_credentials = self._load_from_settings()
        if settings_credentials and settings_credentials.is_valid():
            logger.info("✅ Credentials loaded from settings")
            self._credentials = settings_credentials
            return settings_credentials
        
        # Return empty credentials if none found
        logger.warning("⚠️ No valid Kite credentials found")
        self._credentials = KiteCredentials("", "", "")
        return self._credentials
    
    def _load_from_environment(self) -> Optional[KiteCredentials]:
        """Load credentials from environment variables."""
        try:
            api_key = os.getenv("KITE_API_KEY", "")
            api_secret = os.getenv("KITE_API_SECRET", "")
            access_token = os.getenv("KITE_ACCESS_TOKEN", "")
            
            if api_key and api_secret and access_token:
                return KiteCredentials(
                    api_key=api_key,
                    api_secret=api_secret,
                    access_token=access_token
                )
        except Exception as e:
            logger.error(f"Error loading credentials from environment: {e}")
        
        return None
    
    def _load_from_file(self) -> Optional[KiteCredentials]:
        """Load credentials from file."""
        try:
            credentials_file = Path(self.kite_config.credentials_file)
            
            if not credentials_file.exists():
                logger.debug(f"Credentials file not found: {credentials_file}")
                return None
            
            with open(credentials_file, 'r') as f:
                data = json.load(f)
            
            # Handle different file formats
            if isinstance(data, dict):
                # JSON object format
                api_key = data.get("api_key", "")
                api_secret = data.get("api_secret", "")
                access_token = data.get("access_token", "")
                user_id = data.get("user_id", "")
                user_name = data.get("user_name", "")
            else:
                # Simple string format (just access token)
                api_key = self.kite_config.api_key
                api_secret = self.kite_config.api_secret
                access_token = str(data).strip()
                user_id = None
                user_name = None
            
            if api_key and api_secret and access_token:
                return KiteCredentials(
                    api_key=api_key,
                    api_secret=api_secret,
                    access_token=access_token,
                    user_id=user_id,
                    user_name=user_name
                )
                
        except Exception as e:
            logger.error(f"Error loading credentials from file: {e}")
        
        return None
    
    def _load_from_settings(self) -> Optional[KiteCredentials]:
        """Load credentials from settings configuration."""
        try:
            api_key = self.kite_config.api_key
            api_secret = self.kite_config.api_secret
            access_token = self.kite_config.access_token
            
            if api_key and api_secret and access_token:
                return KiteCredentials(
                    api_key=api_key,
                    api_secret=api_secret,
                    access_token=access_token
                )
        except Exception as e:
            logger.error(f"Error loading credentials from settings: {e}")
        
        return None
    
    def save_credentials(self, credentials: KiteCredentials, file_path: Optional[str] = None) -> bool:
        """Save credentials to file."""
        try:
            if not file_path:
                file_path = self.kite_config.credentials_file
            
            credentials_file = Path(file_path)
            credentials_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(credentials_file, 'w') as f:
                json.dump(credentials.to_dict(), f, indent=2)
            
            logger.info(f"✅ Credentials saved to {credentials_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving credentials: {e}")
            return False
    
    def validate_credentials(self, credentials: Optional[KiteCredentials] = None) -> Tuple[bool, str]:
        """Validate credentials by making a test API call."""
        if not credentials:
            credentials = self._credentials
        
        if not credentials or not credentials.is_valid():
            return False, "Invalid or missing credentials"
        
        try:
            from kiteconnect import KiteConnect
            
            kite = KiteConnect(api_key=credentials.api_key)
            kite.set_access_token(credentials.access_token)
            
            # Test API call
            profile = kite.profile()
            
            if profile and profile.get("user_id"):
                logger.info(f"✅ Credentials validated for user: {profile.get('user_name', 'Unknown')}")
                return True, f"Valid credentials for user: {profile.get('user_name', 'Unknown')}"
            else:
                return False, "Invalid credentials - profile not accessible"
                
        except Exception as e:
            logger.error(f"Credentials validation failed: {e}")
            return False, f"Validation failed: {str(e)}"
    
    def get_credentials(self) -> Optional[KiteCredentials]:
        """Get current credentials."""
        if not self._credentials:
            self.load_credentials()
        return self._credentials
    
    def refresh_access_token(self, request_token: str) -> Tuple[bool, Optional[str]]:
        """Refresh access token using request token."""
        try:
            from kiteconnect import KiteConnect
            
            credentials = self.get_credentials()
            if not credentials or not credentials.api_key or not credentials.api_secret:
                return False, "API key and secret required for token refresh"
            
            kite = KiteConnect(api_key=credentials.api_key)
            data = kite.generate_session(request_token, api_secret=credentials.api_secret)
            
            if data and data.get("access_token"):
                # Update credentials
                credentials.access_token = data["access_token"]
                credentials.user_id = data.get("user_id")
                credentials.user_name = data.get("user_name")
                
                # Save updated credentials
                self.save_credentials(credentials)
                
                logger.info("✅ Access token refreshed successfully")
                return True, data["access_token"]
            else:
                return False, "Failed to generate session"
                
        except Exception as e:
            logger.error(f"Token refresh failed: {e}")
            return False, f"Token refresh failed: {str(e)}"
    
    def create_sample_credentials_file(self, file_path: str = "access_token.json") -> bool:
        """Create a sample credentials file template."""
        try:
            sample_credentials = KiteCredentials(
                api_key="your_api_key_here",
                api_secret="your_api_secret_here",
                access_token="your_access_token_here",
                user_id="your_user_id_here",
                user_name="your_user_name_here"
            )
            
            return self.save_credentials(sample_credentials, file_path)
            
        except Exception as e:
            logger.error(f"Error creating sample credentials file: {e}")
            return False


# Global credentials manager instance
_credentials_manager: Optional[KiteCredentialsManager] = None


def get_kite_credentials_manager() -> KiteCredentialsManager:
    """Get global credentials manager instance."""
    global _credentials_manager
    if _credentials_manager is None:
        _credentials_manager = KiteCredentialsManager()
    return _credentials_manager


def get_kite_credentials() -> Optional[KiteCredentials]:
    """Get current Kite credentials."""
    manager = get_kite_credentials_manager()
    return manager.get_credentials()


def validate_kite_credentials() -> Tuple[bool, str]:
    """Validate current Kite credentials."""
    manager = get_kite_credentials_manager()
    return manager.validate_credentials()


# Example usage
if __name__ == "__main__":
    # Initialize credentials manager
    manager = get_kite_credentials_manager()
    
    # Load credentials
    credentials = manager.load_credentials()
    
    if credentials.is_valid():
        print(f"✅ Credentials loaded: {credentials.api_key[:10]}...")
        
        # Validate credentials
        is_valid, message = manager.validate_credentials(credentials)
        print(f"Validation: {message}")
        
        if not is_valid:
            print("❌ Credentials are invalid. Please check your API key, secret, and access token.")
    else:
        print("❌ No valid credentials found.")
        print("Please set environment variables or create a credentials file.")
        
        # Create sample file
        if manager.create_sample_credentials_file():
            print("📝 Sample credentials file created: access_token.json")
            print("Please edit the file with your actual credentials.")
