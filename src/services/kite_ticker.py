"""
Kite Ticker Integration Service
===============================

Real-time price data integration using Kite Connect ticker.
Provides live market data for continuous analysis and trading decisions.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

from kiteconnect import KiteTicker
from modules.core import BaseModule, ModuleStatus, ModuleHealth
from services.logging.logger_factory import get_logger
from config.settings import get_settings
from services.kite_credentials_manager import get_kite_credentials_manager, KiteCredentials


class TickType(str, Enum):
    """Tick data types."""
    FULL = "full"
    LTP = "ltp"
    QUOTE = "quote"


@dataclass
class TickData:
    """Tick data structure."""
    instrument_token: int
    symbol: str
    last_price: float
    last_quantity: int
    average_price: float
    volume: int
    buy_quantity: int
    sell_quantity: int
    ohlc: Dict[str, float]  # open, high, low, close
    change: float
    change_percent: float
    last_trade_time: datetime
    timestamp: datetime


class KiteTickerConfig:
    """Kite ticker configuration."""
    
    def __init__(self):
        self.api_key: str = ""
        self.access_token: str = ""
        self.reconnect_interval: int = 30
        self.max_reconnect_attempts: int = 5
        self.tick_mode: TickType = TickType.FULL
        self.subscription_mode: str = "mode_quote"  # mode_ltp, mode_quote, mode_full


class KiteTickerService(BaseModule):
    """Kite ticker service for real-time price data."""
    
    def __init__(self):
        super().__init__("kite_ticker")
        
        # Initialize settings and credentials manager
        self.settings = get_settings()
        self.kite_config = self.settings.kite
        self.credentials_manager = get_kite_credentials_manager()
        
        # Load credentials
        self.credentials = self.credentials_manager.load_credentials()
        
        # Initialize configuration
        self.config = KiteTickerConfig()
        self.config.api_key = self.credentials.api_key
        self.config.access_token = self.credentials.access_token
        self.config.reconnect_interval = self.kite_config.reconnect_interval
        self.config.max_reconnect_attempts = self.kite_config.max_reconnect_attempts
        self.config.tick_mode = TickType(self.kite_config.tick_mode)
        self.config.subscription_mode = self.kite_config.subscription_mode
        
        self.logger = get_logger(__name__)
        
        # Kite ticker instance
        self.kite_ticker: Optional[KiteTicker] = None
        
        # Subscription management
        self.subscribed_tokens: List[int] = []
        self.tick_data: Dict[int, TickData] = {}
        self.price_callbacks: List[Callable[[str, TickData], None]] = []
        
        # Connection management
        self.is_connected: bool = False
        self.reconnect_attempts: int = 0
        self.reconnect_task: Optional[asyncio.Task] = None
        
    async def initialize(self) -> None:
        """Initialize Kite ticker service."""
        self.logger.info("Initializing Kite ticker service...")
        
        try:
            # Load credentials
            await self._load_credentials()
            
            # Initialize Kite ticker
            await self._initialize_ticker()
            
            # Set up event handlers
            self._setup_event_handlers()
            
            self.set_status(ModuleStatus.READY)
            self.logger.info("Kite ticker service initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Kite ticker service: {e}")
            self.set_status(ModuleStatus.ERROR)
            raise
            
    async def cleanup(self) -> None:
        """Cleanup Kite ticker service."""
        self.logger.info("Cleaning up Kite ticker service...")
        
        # Disconnect ticker
        if self.kite_ticker:
            try:
                self.kite_ticker.disconnect()
            except Exception as e:
                self.logger.error(f"Error disconnecting ticker: {e}")
        
        # Cancel reconnect task
        if self.reconnect_task:
            self.reconnect_task.cancel()
            try:
                await self.reconnect_task
            except asyncio.CancelledError:
                pass
        
        self.set_status(ModuleStatus.STOPPED)
        self.logger.info("Kite ticker service cleaned up successfully")
        
    async def health_check(self) -> ModuleHealth:
        """Check Kite ticker service health."""
        dependencies = {
            "kite_ticker": self.kite_ticker is not None,
            "is_connected": self.is_connected,
            "subscribed_tokens": len(self.subscribed_tokens),
            "tick_data_count": len(self.tick_data),
            "reconnect_attempts": self.reconnect_attempts
        }
        
        return ModuleHealth(
            module_name=self.module_name,
            status=self.status,
            dependencies=dependencies,
            last_check=datetime.now().isoformat()
        )
        
    async def _load_credentials(self) -> None:
        """Load Kite API credentials."""
        try:
            # Reload credentials using the credentials manager
            self.credentials = self.credentials_manager.load_credentials()
            
            # Update configuration
            self.config.api_key = self.credentials.api_key
            self.config.access_token = self.credentials.access_token
            
            if not self.config.api_key or not self.config.access_token:
                self.logger.warning("API key or access token not found - service will use mock data")
                return
            
            self.logger.info("Kite credentials loaded successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to load Kite credentials: {e}")
            self.logger.warning("Service will use mock data")
            
    async def _initialize_ticker(self) -> None:
        """Initialize Kite ticker instance."""
        try:
            if not self.config.api_key or not self.config.access_token:
                self.logger.warning("Kite credentials not available - ticker will use mock data")
                self.kite_ticker = None
                return
            
            self.kite_ticker = KiteTicker(
                api_key=self.config.api_key,
                access_token=self.config.access_token
            )
            
            self.logger.info("Kite ticker instance created successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to create Kite ticker instance: {e}")
            self.logger.warning("Ticker will use mock data")
            self.kite_ticker = None
            
    def _setup_event_handlers(self) -> None:
        """Set up Kite ticker event handlers."""
        if not self.kite_ticker:
            return
            
        # Connection events
        self.kite_ticker.on_connect = self._on_connect
        self.kite_ticker.on_disconnect = self._on_disconnect
        self.kite_ticker.on_reconnect = self._on_reconnect
        self.kite_ticker.on_error = self._on_error
        
        # Data events
        self.kite_ticker.on_ticks = self._on_ticks
        self.kite_ticker.on_order_update = self._on_order_update
        
    def _on_connect(self) -> None:
        """Handle ticker connection."""
        self.logger.info("Kite ticker connected successfully")
        self.is_connected = True
        self.reconnect_attempts = 0
        
        # Resubscribe to tokens if any
        if self.subscribed_tokens:
            asyncio.create_task(self._resubscribe_tokens())
            
    def _on_disconnect(self) -> None:
        """Handle ticker disconnection."""
        self.logger.warning("Kite ticker disconnected")
        self.is_connected = False
        
        # Start reconnection process
        if self.reconnect_attempts < self.config.max_reconnect_attempts:
            asyncio.create_task(self._reconnect())
            
    def _on_reconnect(self, attempts: int, interval: int) -> None:
        """Handle ticker reconnection."""
        self.logger.info(f"Kite ticker reconnecting... Attempt {attempts}, Interval {interval}")
        
    def _on_error(self, code: int, message: str) -> None:
        """Handle ticker errors."""
        self.logger.error(f"Kite ticker error: {code} - {message}")
        
    def _on_ticks(self, ws, ticks: List[Dict]) -> None:
        """Handle incoming tick data."""
        try:
            for tick in ticks:
                asyncio.create_task(self._process_tick(tick))
                
        except Exception as e:
            self.logger.error(f"Error processing ticks: {e}")
            
    def _on_order_update(self, ws, order: Dict) -> None:
        """Handle order updates."""
        try:
            self.logger.info(f"Order update received: {order}")
            
        except Exception as e:
            self.logger.error(f"Error processing order update: {e}")
            
    async def _process_tick(self, tick: Dict) -> None:
        """Process individual tick data."""
        try:
            instrument_token = tick.get("instrument_token")
            if not instrument_token:
                return
            
            # Extract tick data
            tick_data = TickData(
                instrument_token=instrument_token,
                symbol=tick.get("tradingsymbol", ""),
                last_price=tick.get("last_price", 0.0),
                last_quantity=tick.get("last_quantity", 0),
                average_price=tick.get("average_price", 0.0),
                volume=tick.get("volume", 0),
                buy_quantity=tick.get("buy_quantity", 0),
                sell_quantity=tick.get("sell_quantity", 0),
                ohlc={
                    "open": tick.get("ohlc", {}).get("open", 0.0),
                    "high": tick.get("ohlc", {}).get("high", 0.0),
                    "low": tick.get("ohlc", {}).get("low", 0.0),
                    "close": tick.get("ohlc", {}).get("close", 0.0)
                },
                change=tick.get("change", 0.0),
                change_percent=tick.get("change_percent", 0.0),
                last_trade_time=datetime.fromtimestamp(tick.get("last_trade_time", 0)),
                timestamp=datetime.now()
            )
            
            # Store tick data
            self.tick_data[instrument_token] = tick_data
            
            # Notify callbacks
            for callback in self.price_callbacks:
                try:
                    callback(tick_data.symbol, tick_data)
                except Exception as e:
                    self.logger.error(f"Error in price callback: {e}")
                    
        except Exception as e:
            self.logger.error(f"Error processing tick: {e}")
            
    async def _reconnect(self) -> None:
        """Handle ticker reconnection."""
        self.reconnect_attempts += 1
        
        if self.reconnect_attempts > self.config.max_reconnect_attempts:
            self.logger.error("Max reconnection attempts reached")
            return
        
        self.logger.info(f"Attempting to reconnect... Attempt {self.reconnect_attempts}")
        
        try:
            await asyncio.sleep(self.config.reconnect_interval)
            
            if self.kite_ticker:
                self.kite_ticker.connect()
                
        except Exception as e:
            self.logger.error(f"Error during reconnection: {e}")
            
    async def _resubscribe_tokens(self) -> None:
        """Resubscribe to tokens after reconnection."""
        try:
            if self.subscribed_tokens:
                self.kite_ticker.subscribe(self.subscribed_tokens)
                self.kite_ticker.set_mode(
                    self.kite_ticker.MODE_QUOTE, 
                    self.subscribed_tokens
                )
                
        except Exception as e:
            self.logger.error(f"Error resubscribing to tokens: {e}")
            
    # Public API methods
    async def connect(self) -> None:
        """Connect to Kite ticker."""
        try:
            if not self.kite_ticker:
                self.logger.warning("Kite ticker not available - cannot connect")
                return
            
            if not self.is_connected:
                self.kite_ticker.connect()
                
        except Exception as e:
            self.logger.error(f"Error connecting to ticker: {e}")
            raise
            
    async def disconnect(self) -> None:
        """Disconnect from Kite ticker."""
        try:
            if self.kite_ticker and self.is_connected:
                self.kite_ticker.disconnect()
                
        except Exception as e:
            self.logger.error(f"Error disconnecting from ticker: {e}")
            
    async def subscribe(self, instrument_tokens: List[int]) -> None:
        """Subscribe to instrument tokens."""
        try:
            if not self.kite_ticker:
                self.logger.warning("Kite ticker not available - storing tokens for later subscription")
                # Store tokens for when ticker becomes available
                self.subscribed_tokens.extend(instrument_tokens)
                self.subscribed_tokens = list(set(self.subscribed_tokens))  # Remove duplicates
                return
            
            # Add to subscribed tokens
            self.subscribed_tokens.extend(instrument_tokens)
            self.subscribed_tokens = list(set(self.subscribed_tokens))  # Remove duplicates
            
            # Subscribe to tokens
            self.kite_ticker.subscribe(instrument_tokens)
            self.kite_ticker.set_mode(
                self.kite_ticker.MODE_QUOTE, 
                instrument_tokens
            )
            
            self.logger.info(f"Subscribed to {len(instrument_tokens)} tokens")
            
        except Exception as e:
            self.logger.error(f"Error subscribing to tokens: {e}")
            raise
            
    async def unsubscribe(self, instrument_tokens: List[int]) -> None:
        """Unsubscribe from instrument tokens."""
        try:
            if not self.kite_ticker:
                self.logger.warning("Kite ticker not available - removing tokens from local list")
                # Remove from subscribed tokens
                self.subscribed_tokens = [
                    token for token in self.subscribed_tokens 
                    if token not in instrument_tokens
                ]
                return
            
            # Remove from subscribed tokens
            self.subscribed_tokens = [
                token for token in self.subscribed_tokens 
                if token not in instrument_tokens
            ]
            
            # Unsubscribe from tokens
            self.kite_ticker.unsubscribe(instrument_tokens)
            
            self.logger.info(f"Unsubscribed from {len(instrument_tokens)} tokens")
            
        except Exception as e:
            self.logger.error(f"Error unsubscribing from tokens: {e}")
            raise
            
    async def get_tick_data(self, instrument_token: int) -> Optional[TickData]:
        """Get tick data for an instrument."""
        return self.tick_data.get(instrument_token)
        
    async def get_all_tick_data(self) -> Dict[int, TickData]:
        """Get all tick data."""
        return self.tick_data.copy()
        
    def register_price_callback(self, callback: Callable[[str, TickData], None]) -> None:
        """Register a callback for price updates."""
        self.price_callbacks.append(callback)
        
    def unregister_price_callback(self, callback: Callable[[str, TickData], None]) -> None:
        """Unregister a price callback."""
        if callback in self.price_callbacks:
            self.price_callbacks.remove(callback)
            
    async def get_instrument_token(self, symbol: str) -> Optional[int]:
        """Get instrument token for a symbol."""
        # This would typically query Kite API for instrument details
        # For now, return mock tokens
        mock_tokens = {
            "RELIANCE": 738561,
            "TCS": 2953217,
            "HDFC": 341249,
            "INFY": 408065,
            "WIPRO": 969473
        }
        return mock_tokens.get(symbol)
        
    async def get_symbol_from_token(self, instrument_token: int) -> Optional[str]:
        """Get symbol from instrument token."""
        # Reverse lookup for symbol
        for token, tick_data in self.tick_data.items():
            if token == instrument_token:
                return tick_data.symbol
        return None

