#!/usr/bin/env python3
"""
Find Existing Zerodha Token
===========================

Simple script to locate existing Zerodha/Kite Connect access tokens
and integrate them with Kite Services.
"""

import json
import os
from datetime import datetime
from pathlib import Path


def find_token_files():
    """Find all potential token files."""
    search_paths = [
        "../access_token",
        "../access_tokens", 
        "../zerodha_token.json",
        "../access_tokens/zerodha_token.json",
        "../access_tokens/zerodha_credentials.json",
        "./access_token.json",
        "./zerodha_token.json",
        "./data/access_token.json"
    ]
    
    found_files = []
    
    print("🔍 Searching for existing token files...")
    
    for search_path in search_paths:
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
                print(f"  ✅ Found: {path} ({stat.st_size} bytes)")
                
            # Check if it's a directory
            elif path.is_dir():
                print(f"  📁 Checking directory: {path}")
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
                        print(f"    ✅ Found: {token_path} ({stat.st_size} bytes)")
                        
        except Exception as e:
            # Silently skip paths that don't exist
            continue
    
    return found_files


def load_and_analyze_token(file_path):
    """Load and analyze a token file."""
    try:
        print(f"\n📄 Analyzing: {file_path}")
        
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        print(f"  📊 File contains {len(data)} fields:")
        
        # Show available fields
        for key, value in data.items():
            if isinstance(value, str) and len(value) > 20:
                print(f"    • {key}: {value[:10]}...{value[-5:]}")
            else:
                print(f"    • {key}: {value}")
        
        # Check for Kite Connect fields
        kite_fields = {
            'api_key': ['api_key', 'apikey', 'key', 'client_id'],
            'access_token': ['access_token', 'accesstoken', 'token', 'auth_token'],
            'user_id': ['user_id', 'userid', 'user', 'client_code']
        }
        
        extracted = {}
        for field, possible_names in kite_fields.items():
            for name in possible_names:
                if name in data and data[name]:
                    extracted[field] = data[name]
                    print(f"  ✅ Found {field}: {name}")
                    break
        
        return extracted
        
    except Exception as e:
        print(f"  ❌ Error reading file: {e}")
        return None


def create_env_file(credentials):
    """Create .env file with credentials."""
    try:
        env_content = f"""# Kite Services Configuration
# Generated from existing token file on {datetime.now().isoformat()}

# Service Configuration
SERVICE_NAME=kite-services
SERVICE_VERSION=1.0.0
SERVICE_HOST=0.0.0.0
SERVICE_PORT=8079
ENVIRONMENT=development
DEBUG=true

# Kite Connect Configuration
KITE_API_KEY={credentials.get('api_key', '')}
KITE_ACCESS_TOKEN={credentials.get('access_token', '')}
KITE_RECONNECT_INTERVAL=30
KITE_MAX_RECONNECT_ATTEMPTS=5

# Yahoo Finance Configuration
YAHOO_TIMEOUT=30
YAHOO_RATE_LIMIT=100

# Logging Configuration
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_FILE_PATH=logs/kite_services.log

# Database Configuration
DATABASE_URL=sqlite:///data/kite_services.db

# CORS Configuration
CORS_ORIGINS=["*"]
CORS_METHODS=["*"]
CORS_HEADERS=["*"]
"""
        
        with open('.env', 'w') as f:
            f.write(env_content)
        
        print("✅ Created .env file with your credentials")
        return True
        
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return False


def main():
    """Main function."""
    print("🔐 Kite Connect Token Integration")
    print("=" * 50)
    
    # Find token files
    found_files = find_token_files()
    
    if not found_files:
        print("\n❌ No token files found")
        print("\n💡 Make sure you have a token file in one of these locations:")
        print("   • ../access_token (file or directory)")
        print("   • ../access_tokens/zerodha_token.json")
        print("   • ./zerodha_token.json")
        return 1
    
    print(f"\n📁 Found {len(found_files)} token file(s)")
    
    # Analyze each file
    best_credentials = None
    best_file = None
    
    for file_info in found_files:
        credentials = load_and_analyze_token(file_info["path"])
        if credentials and credentials.get('access_token'):
            best_credentials = credentials
            best_file = file_info["path"]
            break
    
    if best_credentials:
        print(f"\n🎉 Best token found in: {best_file}")
        print(f"   User ID: {best_credentials.get('user_id', 'unknown')}")
        print(f"   API Key: {best_credentials.get('api_key', 'unknown')[:8]}..." if best_credentials.get('api_key') else "   API Key: not found")
        print(f"   Access Token: ✅ Available")
        
        # Create .env file
        if create_env_file(best_credentials):
            print("\n✅ Integration complete!")
            print("\n🚀 Next steps:")
            print("   1. source venv/bin/activate")
            print("   2. python src/main.py")
            print("   3. curl 'http://localhost:8079/api/market/data?symbols=RELIANCE&scope=basic'")
            
            print("\n🔗 Your service will run on: http://localhost:8079")
            print("📚 API docs will be at: http://localhost:8079/docs")
        else:
            return 1
    else:
        print("\n❌ No valid access token found in any file")
        print("\n💡 Your token file should contain:")
        print("   • access_token (required)")
        print("   • api_key (recommended)")
        print("   • user_id (optional)")
        return 1
    
    return 0


if __name__ == "__main__":
    try:
        exit_code = main()
        exit(exit_code)
    except KeyboardInterrupt:
        print("\n👋 Search interrupted")
        exit(1)
    except Exception as e:
        print(f"\n💥 Search failed: {e}")
        exit(1)
