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
from services.yahoo_finance_service import YahooFinanceService
from services.market_context_service import MarketContextService


class ServiceManager:
    """Manages all application services."""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        
        # Service instances
        self.kite_client: Optional[KiteClient] = None
        self.yahoo_service: Optional[YahooFinanceService] = None
        self.market_context_service: Optional[MarketContextService] = None
        
        # Service status
        self.services_status: Dict[str, Dict[str, Any]] = {}
        
    async def initialize(self):
        """Initialize all services."""
        self.logger.info("Initializing Service Manager...")
        
        try:
            # Initialize Kite client
            self.kite_client = KiteClient()
            await self.kite_client.initialize()
            self.services_status["kite_client"] = {
                "status": "running",
                "initialized_at": datetime.now()
            }
            
            # Initialize Yahoo Finance service
            self.yahoo_service = YahooFinanceService()
            await self.yahoo_service.initialize()
            self.services_status["yahoo_service"] = {
                "status": "running",
                "initialized_at": datetime.now()
            }
            
            # Initialize Market Context service
            self.market_context_service = MarketContextService()
            await self.market_context_service.initialize()
            self.services_status["market_context_service"] = {
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
