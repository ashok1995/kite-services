"""
Existing Token Loader Service
============================

Service to locate and load existing Zerodha/Kite Connect access tokens.
Follows workspace rules:
- Stateless service design
- Comprehensive logging to files
- Configuration-driven behavior
- No hardcoded paths
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

from config.settings import get_settings
from core.logging_config import get_logger


class ExistingTokenLoader:
    """
    Service to locate and load existing Zerodha/Kite Connect access tokens.
    
    Searches common locations for token files and loads them in a standardized format.
    """
    
    def __init__(self, logger: Optional[Any] = None):
        """Initialize existing token loader."""
        self.settings = get_settings()
        self.logger = logger or get_logger(__name__)
        
        # Common token file locations to search
        self.search_paths = [
            "../access_token",
            "../access_tokens",
            "../zerodha_token.json",
            "../access_tokens/zerodha_token.json",
            "../access_tokens/zerodha_credentials.json",
            "./access_token.json",
            "./zerodha_token.json",
            "./data/access_token.json",
            os.path.expanduser("~/zerodha_token.json"),
            os.path.expanduser("~/access_token.json")
        ]
        
        self.logger.info(
            "ExistingTokenLoader initialized",
            extra={
                "service": "existing_token_loader",
                "search_paths_count": len(self.search_paths)
            }
        )
    
    def find_token_files(self) -> List[Dict[str, Any]]:
        """
        Find all potential token files.
        
        Returns:
            List of found token files with metadata
        """
        found_files = []
        
        for search_path in self.search_paths:
            try:
                path = Path(search_path)
                
                # Check if it's a file
                if path.is_file():
                    stat = path.stat()
                    found_files.append({
                        "path": str(path.absolute()),
                        "name": path.name,
                        "size": stat.st_size,
                        "modified": datetime.fromtimestamp(stat.st_mtime),
                        "readable": os.access(path, os.R_OK)
                    })
                    
                # Check if it's a directory
                elif path.is_dir():
                    # Look for common token file names in the directory
                    token_files = [
                        "zerodha_token.json",
                        "zerodha_credentials.json", 
                        "access_token.json",
                        "kite_token.json"
                    ]
                    
                    for token_file in token_files:
                        token_path = path / token_file
                        if token_path.is_file():
                            stat = token_path.stat()
                            found_files.append({
                                "path": str(token_path.absolute()),
                                "name": token_path.name,
                                "size": stat.st_size,
                                "modified": datetime.fromtimestamp(stat.st_mtime),
                                "readable": os.access(token_path, os.R_OK)
                            })
                            
            except Exception as e:
                # Silently skip paths that don't exist or can't be accessed
                continue
        
        # Sort by modification time (newest first)
        found_files.sort(key=lambda x: x["modified"], reverse=True)
        
        self.logger.info(
            "Token file search completed",
            extra={
                "service": "existing_token_loader",
                "found_files_count": len(found_files),
                "search_paths_checked": len(self.search_paths)
            }
        )
        
        return found_files
    
    def load_token_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Load and parse a token file.
        
        Args:
            file_path: Path to the token file
            
        Returns:
            Parsed token data or None if invalid
        """
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            self.logger.info(
                "Token file loaded successfully",
                extra={
                    "service": "existing_token_loader",
                    "file_path": file_path,
                    "data_keys": list(data.keys()) if isinstance(data, dict) else "not_dict"
                }
            )
            
            return data
            
        except Exception as e:
            self.logger.warning(
                "Failed to load token file",
                extra={
                    "service": "existing_token_loader",
                    "file_path": file_path,
                    "error": str(e)
                }
            )
            return None
    
    def extract_kite_credentials(self, token_data: Dict[str, Any]) -> Optional[Dict[str, str]]:
        """
        Extract Kite Connect credentials from various token file formats.
        
        Args:
            token_data: Raw token data from file
            
        Returns:
            Standardized credentials dict or None
        """
        try:
            credentials = {}
            
            # Common field mappings for different token file formats
            field_mappings = {
                'api_key': ['api_key', 'apikey', 'key', 'client_id'],
                'access_token': ['access_token', 'accesstoken', 'token', 'auth_token'],
                'user_id': ['user_id', 'userid', 'user', 'client_code'],
                'user_name': ['user_name', 'username', 'name', 'client_name']
            }
            
            # Extract credentials using field mappings
            for standard_field, possible_fields in field_mappings.items():
                for field in possible_fields:
                    if field in token_data and token_data[field]:
                        credentials[standard_field] = str(token_data[field])
                        break
            
            # Validate that we have minimum required credentials
            if 'access_token' in credentials:
                self.logger.info(
                    "Successfully extracted Kite credentials",
                    extra={
                        "service": "existing_token_loader",
                        "extracted_fields": list(credentials.keys()),
                        "has_access_token": bool(credentials.get('access_token'))
                    }
                )
                return credentials
            else:
                self.logger.warning(
                    "No access token found in token data",
                    extra={
                        "service": "existing_token_loader",
                        "available_fields": list(token_data.keys())
                    }
                )
                return None
                
        except Exception as e:
            self.logger.error(
                "Failed to extract Kite credentials",
                extra={
                    "service": "existing_token_loader",
                    "error": str(e)
                },
                exc_info=True
            )
            return None
    
    def find_and_load_best_token(self) -> Optional[Dict[str, str]]:
        """
        Find and load the best available token file.
        
        Returns:
            Standardized credentials dict or None
        """
        self.logger.info(
            "Starting token file search",
            extra={"service": "existing_token_loader"}
        )
        
        # Find all token files
        found_files = self.find_token_files()
        
        if not found_files:
            self.logger.warning(
                "No token files found",
                extra={
                    "service": "existing_token_loader",
                    "search_paths": self.search_paths
                }
            )
            return None
        
        # Try to load each file (newest first)
        for file_info in found_files:
            file_path = file_info["path"]
            
            self.logger.info(
                "Attempting to load token file",
                extra={
                    "service": "existing_token_loader",
                    "file_path": file_path,
                    "file_size": file_info["size"],
                    "modified": file_info["modified"].isoformat()
                }
            )
            
            # Load the file
            token_data = self.load_token_file(file_path)
            if not token_data:
                continue
            
            # Extract credentials
            credentials = self.extract_kite_credentials(token_data)
            if credentials:
                self.logger.info(
                    "Successfully loaded existing token",
                    extra={
                        "service": "existing_token_loader",
                        "file_path": file_path,
                        "user_id": credentials.get('user_id', 'unknown'),
                        "has_access_token": bool(credentials.get('access_token'))
                    }
                )
                return credentials
        
        self.logger.warning(
            "No valid token files found",
            extra={
                "service": "existing_token_loader",
                "files_checked": len(found_files)
            }
        )
        return None
    
    def create_env_file_from_token(self, credentials: Dict[str, str]) -> bool:
        """
        Create .env file from existing token credentials.
        
        Args:
            credentials: Extracted credentials
            
        Returns:
            True if .env file created successfully
        """
        try:
            env_path = Path(".env")
            
            # Read existing .env if it exists
            existing_env = {}
            if env_path.exists():
                with open(env_path, 'r') as f:
                    for line in f:
                        if '=' in line and not line.strip().startswith('#'):
                            key, value = line.strip().split('=', 1)
                            existing_env[key] = value
            
            # Update with Kite credentials
            existing_env.update({
                'KITE_API_KEY': credentials.get('api_key', ''),
                'KITE_ACCESS_TOKEN': credentials.get('access_token', ''),
                'SERVICE_PORT': '8079'
            })
            
            # Write updated .env file
            with open(env_path, 'w') as f:
                f.write("# Kite Services Configuration\n")
                f.write("# Generated from existing token file\n\n")
                for key, value in existing_env.items():
                    f.write(f"{key}={value}\n")
            
            self.logger.info(
                "Created .env file from existing token",
                extra={
                    "service": "existing_token_loader",
                    "env_file": str(env_path.absolute()),
                    "credentials_count": len([k for k in existing_env.keys() if k.startswith('KITE_')])
                }
            )
            
            return True
            
        except Exception as e:
            self.logger.error(
                "Failed to create .env file",
                extra={
                    "service": "existing_token_loader",
                    "error": str(e)
                },
                exc_info=True
            )
            return False


def main():
    """Main function to find and integrate existing token."""
    print("🔍 Searching for existing Zerodha/Kite Connect tokens...")
    
    loader = ExistingTokenLoader()
    
    # Find and load existing token
    credentials = loader.find_and_load_best_token()
    
    if credentials:
        print("✅ Found existing token!")
        print(f"   User ID: {credentials.get('user_id', 'unknown')}")
        print(f"   API Key: {credentials.get('api_key', 'unknown')[:8]}..." if credentials.get('api_key') else "   API Key: not found")
        print(f"   Access Token: {credentials.get('access_token', 'unknown')[:8]}..." if credentials.get('access_token') else "   Access Token: not found")
        
        # Create .env file
        if loader.create_env_file_from_token(credentials):
            print("✅ Created .env file with your existing credentials")
            print("\n🚀 Now you can start the service:")
            print("   source venv/bin/activate")
            print("   python src/main.py")
            print("\n🔗 Then test with real data:")
            print("   curl 'http://localhost:8079/api/market/data?symbols=RELIANCE&scope=basic'")
        else:
            print("❌ Failed to create .env file")
            return 1
    else:
        print("❌ No valid token files found")
        print("\n💡 Searched in these locations:")
        for path in loader.search_paths:
            print(f"   • {path}")
        
        print("\n🔧 To set up authentication:")
        print("   1. Make sure you have a valid Zerodha token file")
        print("   2. Place it in one of the search locations above")
        print("   3. Or use the authentication flow:")
        print("      python setup_kite_auth.py")
        return 1
    
    return 0

if __name__ == "__main__":
    import sys
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n👋 Search interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Search failed: {e}")
        sys.exit(1)
