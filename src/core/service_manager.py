"""
Service Manager
===============

Manages all services and their lifecycle.
"""

import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.logging_config import get_logger
from core.kite_client import KiteClient
from core.cache_service import CacheService
from services.yahoo_finance_service import YahooFinanceService
from services.market_context_service import MarketContextService
from services.stock_data_service import StockDataService
from services.market_intelligence_service import MarketIntelligenceService


class ServiceManager:
    """Manages all application services."""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        
        # Service instances
        self.cache_service: Optional[CacheService] = None
        self.kite_client: Optional[KiteClient] = None
        self.yahoo_service: Optional[YahooFinanceService] = None
        self.market_context_service: Optional[MarketContextService] = None
        self.stock_data_service: Optional[StockDataService] = None
        self.market_intelligence_service: Optional[MarketIntelligenceService] = None
        
        # Service status
        self.services_status: Dict[str, Dict[str, Any]] = {}
        
    async def initialize(self):
        """Initialize all services."""
        self.logger.info("Initializing Service Manager...")
        
        try:
            # Initialize Cache service FIRST (other services may use it)
            self.cache_service = CacheService()
            await self.cache_service.initialize()
            self.services_status["cache_service"] = {
                "status": "running" if self.cache_service.enabled else "disabled",
                "initialized_at": datetime.now()
            }
            
            # Initialize Kite client
            self.kite_client = KiteClient(cache_service=self.cache_service)
            await self.kite_client.initialize()
            self.services_status["kite_client"] = {
                "status": "running",
                "initialized_at": datetime.now()
            }
            
            # Initialize Yahoo Finance service
            self.yahoo_service = YahooFinanceService(cache_service=self.cache_service)
            await self.yahoo_service.initialize()
            self.services_status["yahoo_service"] = {
                "status": "running",
                "initialized_at": datetime.now()
            }
            
            # Initialize Market Context service with dependencies
            self.market_context_service = MarketContextService(
                kite_client=self.kite_client,
                yahoo_service=self.yahoo_service
            )
            # MarketContextService doesn't need async initialization
            self.services_status["market_context_service"] = {
                "status": "running",
                "initialized_at": datetime.now()
            }
            
            # Initialize Stock Data service
            self.stock_data_service = StockDataService(
                kite_client=self.kite_client
            )
            self.services_status["stock_data_service"] = {
                "status": "running",
                "initialized_at": datetime.now()
            }
            
            # Initialize Market Intelligence service
            self.market_intelligence_service = MarketIntelligenceService(
                kite_client=self.kite_client,
                yahoo_service=self.yahoo_service
            )
            self.services_status["market_intelligence_service"] = {
                "status": "running",
                "initialized_at": datetime.now()
            }
            
            self.logger.info("✅ All services initialized successfully")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize services: {e}")
            raise
            
    async def cleanup(self):
        """Cleanup all services."""
        self.logger.info("Cleaning up Service Manager...")
        
        # Cleanup services
        if self.market_context_service:
            await self.market_context_service.cleanup()
            
        if self.yahoo_service:
            await self.yahoo_service.cleanup()
            
        if self.kite_client:
            await self.kite_client.cleanup()
        
        self.logger.info("✅ Service Manager cleaned up")
        
    async def get_health_status(self) -> Dict[str, Any]:
        """Get health status of all services."""
        return {
            "services": self.services_status,
            "timestamp": datetime.now()
        }


# Global service manager instance
_service_manager: Optional[ServiceManager] = None


async def get_service_manager() -> ServiceManager:
    """Get the global service manager instance."""
    global _service_manager
    if _service_manager is None:
        raise RuntimeError("Service manager not initialized")
    return _service_manager


def set_service_manager(service_manager: ServiceManager):
    """Set the global service manager instance."""
    global _service_manager
    _service_manager = service_manager
