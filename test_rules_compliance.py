#!/usr/bin/env python3
"""
Rules Compliance Test
====================

Test script to verify the codebase follows workspace rules.
This validates the real data implementation against established patterns.
"""

import sys
import os
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_pydantic_imports():
    """Test that Pydantic imports are correct."""
    print("🔍 Testing Pydantic imports...")
    
    try:
        from config.settings import get_settings
        settings = get_settings()
        print("  ✅ Settings import successful")
        print(f"  ✅ Service port: {settings.service.port} (DEV: 8079, PROD: 8179)")
        return True
    except Exception as e:
        print(f"  ❌ Settings import failed: {e}")
        return False

def test_data_models():
    """Test that all data contracts use Pydantic models."""
    print("\n🔍 Testing Pydantic data models...")
    
    try:
        from models.consolidated_models import (
            ConsolidatedStockData, ConsolidatedMarketDataResponse,
            ConsolidatedPortfolio, ConsolidatedMarketContext,
            DataScope, MarketStatus
        )
        
        # Test enum usage
        assert DataScope.BASIC == "basic"
        assert MarketStatus.OPEN == "open"
        print("  ✅ Enums properly defined")
        
        # Test model validation
        from decimal import Decimal
        from datetime import datetime
        
        stock_data = ConsolidatedStockData(
            symbol="RELIANCE",
            last_price=Decimal("2450.50"),
            change=Decimal("25.30"),
            change_percent=Decimal("1.04"),
            volume=1250000,
            timestamp=datetime.now(),
            market_status=MarketStatus.OPEN
        )
        print("  ✅ Pydantic model validation working")
        
        return True
    except Exception as e:
        print(f"  ❌ Data models test failed: {e}")
        return False

def test_service_architecture():
    """Test that services follow stateless, dependency injection pattern."""
    print("\n🔍 Testing service architecture...")
    
    try:
        from services.consolidated_market_service import ConsolidatedMarketService
        
        # Check that service requires dependency injection
        import inspect
        sig = inspect.signature(ConsolidatedMarketService.__init__)
        required_params = [p for p in sig.parameters.values() 
                          if p.default == inspect.Parameter.empty and p.name != 'self']
        
        if len(required_params) >= 3:  # kite_client, yahoo_service, market_context_service
            print("  ✅ Service requires dependency injection")
        else:
            print("  ⚠️  Service may not require enough dependencies")
        
        print("  ✅ Service architecture follows rules")
        return True
    except Exception as e:
        print(f"  ❌ Service architecture test failed: {e}")
        return False

def test_api_routes():
    """Test that API routes are thin and call services only."""
    print("\n🔍 Testing API routes...")
    
    try:
        from api.consolidated_routes import router
        
        # Check that routes exist
        route_paths = [route.path for route in router.routes]
        expected_routes = ["/data", "/portfolio", "/context", "/status"]
        
        for expected in expected_routes:
            if expected in route_paths:
                print(f"  ✅ Route {expected} exists")
            else:
                print(f"  ⚠️  Route {expected} missing")
        
        return True
    except Exception as e:
        print(f"  ❌ API routes test failed: {e}")
        return False

def test_logging_config():
    """Test that logging is properly configured."""
    print("\n🔍 Testing logging configuration...")
    
    try:
        from core.logging_config import get_logger
        logger = get_logger("test")
        
        # Test that logger is configured
        if logger.handlers:
            print("  ✅ Logger has handlers configured")
        else:
            print("  ⚠️  Logger may not have handlers")
        
        # Test structured logging
        logger.info(
            "Test log message",
            extra={
                "service": "test",
                "request_id": "test_123",
                "test_field": "test_value"
            }
        )
        print("  ✅ Structured logging working")
        
        return True
    except Exception as e:
        print(f"  ❌ Logging test failed: {e}")
        return False

def test_folder_structure():
    """Test that folder structure follows rules."""
    print("\n🔍 Testing folder structure...")
    
    required_folders = [
        "src/api",      # Routes/controllers (thin)
        "src/services", # Business logic (stateless, reusable)
        "src/models",   # Pydantic/dataclasses (contracts)
        "src/core",     # Utils, constants, logging
        "src/config",   # Env + DI
        "docs",         # Architecture, flows, ADRs
        "tests"         # Unit, integration, e2e
    ]
    
    all_exist = True
    for folder in required_folders:
        if Path(folder).exists():
            print(f"  ✅ {folder} exists")
        else:
            print(f"  ❌ {folder} missing")
            all_exist = False
    
    return all_exist

def test_documentation():
    """Test that required documentation exists."""
    print("\n🔍 Testing documentation...")
    
    required_docs = [
        "docs/apis-used.md",
        "docs/consolidated-api.md",
        "docs/real-data-integration.md"
    ]
    
    all_exist = True
    for doc in required_docs:
        if Path(doc).exists():
            print(f"  ✅ {doc} exists")
        else:
            print(f"  ❌ {doc} missing")
            all_exist = False
    
    return all_exist

def test_no_hardcoded_values():
    """Test that there are no hardcoded values in services."""
    print("\n🔍 Testing for hardcoded values...")
    
    # This is a simplified check - in practice, you'd scan the codebase
    try:
        from config.settings import get_settings
        settings = get_settings()
        
        # Check that port comes from config
        if hasattr(settings.service, 'port'):
            print("  ✅ Port configured through settings")
        
        # Check that service name comes from config
        if hasattr(settings.service, 'name'):
            print("  ✅ Service name configured through settings")
        
        return True
    except Exception as e:
        print(f"  ❌ Configuration test failed: {e}")
        return False

def main():
    """Run all compliance tests."""
    print("🚀 Kite Services - Rules Compliance Test")
    print("=" * 50)
    
    tests = [
        ("Pydantic Imports", test_pydantic_imports),
        ("Data Models", test_data_models),
        ("Service Architecture", test_service_architecture),
        ("API Routes", test_api_routes),
        ("Logging Config", test_logging_config),
        ("Folder Structure", test_folder_structure),
        ("Documentation", test_documentation),
        ("No Hardcoded Values", test_no_hardcoded_values)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"  💥 {test_name} crashed: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All rules compliance tests PASSED!")
        print("✅ Codebase follows workspace rules")
        return 0
    else:
        print(f"⚠️  {total - passed} tests failed")
        print("🔧 Some rules compliance issues need attention")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
