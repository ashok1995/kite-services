"""
Simple Service Startup Script
============================
Bypasses complex initialization for debugging
"""

import asyncio
import os
import sys

# Add src to path
sys.path.insert(0, ".")

# Set working directory to src
os.chdir("/Users/ashokkumar/Desktop/ashok-personal/stocks/kite-services/src")


async def main():
    print("🚀 Starting Kite Services (Debug Mode)")

    # Test imports
    try:
        from config.settings import get_settings

        settings = get_settings()
        print(f"✅ Settings loaded - API Key: {settings.kite.api_key[:10]}...")
        print(f"✅ Database URL: {settings.database.url}")
    except Exception as e:
        print(f"❌ Settings error: {e}")
        return

    # Test database
    try:
        from core.database import init_database

        await init_database()
        print("✅ Database initialized")
    except Exception as e:
        print(f"❌ Database error: {e}")
        return

    # Start FastAPI
    try:
        import uvicorn

        print("🌐 Starting FastAPI server...")
        uvicorn.run("main:app", host="0.0.0.0", port=8079, reload=False)  # nosec B104
    except Exception as e:
        print(f"❌ FastAPI error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
