"""
Kite Connect Client
==================

Core client for Kite Connect API integration.
Provides unified interface for market data, orders, and portfolio management.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from kiteconnect import KiteConnect, KiteTicker

from config.settings import get_settings
from core.logging_config import get_logger


class KiteClient:
    """Core Kite Connect client."""
    
    def __init__(self):
        self.settings = get_settings()
        self.logger = get_logger(__name__)
        
        # Kite configuration
        self.kite_config = self.settings.kite
        
        # Kite instances
        self.kite: Optional[KiteConnect] = None
        self.kws: Optional[KiteTicker] = None
        
        # Connection state
        self.is_connected = False
        self.is_streaming = False
        
        # Data storage
        self.instruments_cache: Dict[str, Dict] = {}
        self.historical_data_cache: Dict[str, List[Dict]] = {}
        
    async def initialize(self):
        """Initialize Kite client."""
        self.logger.info("Initializing Kite Client...")
        
        try:
            # Load credentials
            await self._load_credentials()
            
            # Initialize Kite Connect
            if self.kite_config.api_key and self.kite_config.access_token:
                self.kite = KiteConnect(api_key=self.kite_config.api_key)
                self.kite.set_access_token(self.kite_config.access_token)
                
                # Initialize WebSocket
                self.kws = KiteTicker(
                    api_key=self.kite_config.api_key,
                    access_token=self.kite_config.access_token
                )
                
                # Test connection
                await self._test_connection()
                
                self.logger.info("✅ Kite Client initialized successfully")
            else:
                self.logger.warning("⚠️ Kite credentials not available - using mock mode")
                
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize Kite Client: {e}")
            raise
            
    async def cleanup(self):
        """Cleanup Kite client."""
        self.logger.info("Cleaning up Kite Client...")
        
        if self.kws and self.is_streaming:
            try:
                self.kws.close()
                self.is_streaming = False
            except Exception as e:
                self.logger.error(f"Error closing WebSocket: {e}")
        
        self.is_connected = False
        self.logger.info("✅ Kite Client cleaned up")
        
    async def get_instruments(self, exchange: str = "NSE") -> Dict[str, Dict]:
        """Get instruments list."""
        try:
            if not self.kite:
                return self._get_mock_instruments()
            
            # Check cache first
            cache_key = f"instruments_{exchange}"
            if cache_key in self.instruments_cache:
                return self.instruments_cache[cache_key]
            
            # Fetch from API
            instruments = self.kite.instruments(exchange)
            instrument_dict = {}
            
            for instrument in instruments:
                if instrument['instrument_type'] == 'EQ':  # Equity only
                    instrument_dict[instrument['tradingsymbol']] = {
                        'instrument_token': instrument['instrument_token'],
                        'name': instrument['name'],
                        'exchange': instrument['exchange'],
                        'lot_size': instrument['lot_size'],
                        'tick_size': instrument['tick_size']
                    }
            
            # Cache the result
            self.instruments_cache[cache_key] = instrument_dict
            
            self.logger.info(f"Retrieved {len(instrument_dict)} instruments from {exchange}")
            return instrument_dict
            
        except Exception as e:
            self.logger.error(f"Error getting instruments: {e}")
            return self._get_mock_instruments()
            
    async def get_instrument_data(self, symbol: str) -> Optional[Dict]:
        """Get real-time instrument data."""
        try:
            if not self.kite:
                return self._get_mock_instrument_data(symbol)
            
            # Get instrument token
            instruments = await self.get_instruments()
            if symbol not in instruments:
                self.logger.warning(f"Symbol {symbol} not found in instruments")
                return None
            
            instrument_token = instruments[symbol]['instrument_token']
            
            # Get quote
            quote = self.kite.quote([instrument_token])
            if not quote or instrument_token not in quote:
                return None
            
            data = quote[instrument_token]
            
            return {
                'symbol': symbol,
                'instrument_token': instrument_token,
                'last_price': data.get('last_price', 0),
                'change': data.get('net_change', 0),
                'change_percent': data.get('change', 0),
                'volume': data.get('volume', 0),
                'ohlc': data.get('ohlc', {}),
                'bid_ask': {
                    'bid_price': data.get('depth', {}).get('buy', [{}])[0].get('price', 0),
                    'ask_price': data.get('depth', {}).get('sell', [{}])[0].get('price', 0),
                    'bid_quantity': data.get('depth', {}).get('buy', [{}])[0].get('quantity', 0),
                    'ask_quantity': data.get('depth', {}).get('sell', [{}])[0].get('quantity', 0)
                },
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting instrument data for {symbol}: {e}")
            return self._get_mock_instrument_data(symbol)
            
    async def get_historical_data(self, symbol: str, days: int = 30) -> Optional[List[Dict]]:
        """Get historical data for a symbol."""
        try:
            if not self.kite:
                return self._get_mock_historical_data(symbol, days)
            
            # Check cache
            cache_key = f"{symbol}_{days}d"
            if cache_key in self.historical_data_cache:
                cached_data = self.historical_data_cache[cache_key]
                # Return cached data if recent (within 1 hour)
                if cached_data and len(cached_data) > 0:
                    last_timestamp = cached_data[-1].get('timestamp')
                    if last_timestamp and (datetime.now() - last_timestamp).total_seconds() < 3600:
                        return cached_data
            
            # Get instrument token
            instruments = await self.get_instruments()
            if symbol not in instruments:
                return None
            
            instrument_token = instruments[symbol]['instrument_token']
            
            # Calculate date range
            to_date = datetime.now()
            from_date = to_date - timedelta(days=days)
            
            # Get historical data
            historical_data = self.kite.historical_data(
                instrument_token=instrument_token,
                from_date=from_date.strftime("%Y-%m-%d"),
                to_date=to_date.strftime("%Y-%m-%d"),
                interval="day"
            )
            
            # Convert to standard format
            formatted_data = []
            for candle in historical_data:
                formatted_data.append({
                    'timestamp': candle['date'],
                    'open': candle['open'],
                    'high': candle['high'],
                    'low': candle['low'],
                    'close': candle['close'],
                    'volume': candle['volume']
                })
            
            # Cache the data
            self.historical_data_cache[cache_key] = formatted_data
            
            self.logger.info(f"Retrieved {len(formatted_data)} historical candles for {symbol}")
            return formatted_data
            
        except Exception as e:
            self.logger.error(f"Error getting historical data for {symbol}: {e}")
            return self._get_mock_historical_data(symbol, days)
            
    async def subscribe_to_instruments(self, symbols: List[str]):
        """Subscribe to real-time data for instruments."""
        try:
            if not self.kws:
                self.logger.warning("WebSocket not available for subscription")
                return
            
            # Get instrument tokens
            instruments = await self.get_instruments()
            tokens = []
            
            for symbol in symbols:
                if symbol in instruments:
                    tokens.append(instruments[symbol]['instrument_token'])
                else:
                    self.logger.warning(f"Symbol {symbol} not found for subscription")
            
            if tokens:
                # Subscribe to tokens
                self.kws.subscribe(tokens)
                self.kws.set_mode(self.kws.MODE_FULL, tokens)
                
                self.logger.info(f"Subscribed to {len(tokens)} instruments")
            
        except Exception as e:
            self.logger.error(f"Error subscribing to instruments: {e}")
            
    async def _load_credentials(self):
        """Load Kite credentials."""
        # Credentials are loaded from settings
        if not self.kite_config.api_key or not self.kite_config.access_token:
            self.logger.warning("Kite credentials not configured")
            
    async def _test_connection(self):
        """Test Kite API connection."""
        try:
            if self.kite:
                profile = self.kite.profile()
                if profile:
                    self.is_connected = True
                    self.logger.info(f"Connected to Kite API as {profile.get('user_name', 'Unknown')}")
                else:
                    self.logger.warning("Failed to get profile from Kite API")
        except Exception as e:
            self.logger.error(f"Kite API connection test failed: {e}")
            
    def _get_mock_instruments(self) -> Dict[str, Dict]:
        """Get mock instruments for testing."""
        return {
            "RELIANCE": {
                'instrument_token': 738561,
                'name': 'RELIANCE',
                'exchange': 'NSE',
                'lot_size': 1,
                'tick_size': 0.05
            },
            "TCS": {
                'instrument_token': 2953217,
                'name': 'TCS',
                'exchange': 'NSE',
                'lot_size': 1,
                'tick_size': 0.05
            },
            "HDFC": {
                'instrument_token': 341249,
                'name': 'HDFC',
                'exchange': 'NSE',
                'lot_size': 1,
                'tick_size': 0.05
            },
            "INFY": {
                'instrument_token': 408065,
                'name': 'INFY',
                'exchange': 'NSE',
                'lot_size': 1,
                'tick_size': 0.05
            },
            "WIPRO": {
                'instrument_token': 969473,
                'name': 'WIPRO',
                'exchange': 'NSE',
                'lot_size': 1,
                'tick_size': 0.05
            }
        }
        
    def _get_mock_instrument_data(self, symbol: str) -> Dict:
        """Get mock instrument data."""
        import random
        
        base_prices = {
            "RELIANCE": 2500,
            "TCS": 3500,
            "HDFC": 1500,
            "INFY": 1800,
            "WIPRO": 400
        }
        
        base_price = base_prices.get(symbol, 1000)
        change_percent = random.uniform(-2, 2)
        current_price = base_price * (1 + change_percent / 100)
        
        return {
            'symbol': symbol,
            'instrument_token': 123456,
            'last_price': current_price,
            'change': current_price - base_price,
            'change_percent': change_percent,
            'volume': random.randint(100000, 1000000),
            'ohlc': {
                'open': base_price * 0.99,
                'high': current_price * 1.01,
                'low': current_price * 0.98,
                'close': current_price
            },
            'bid_ask': {
                'bid_price': current_price - 0.05,
                'ask_price': current_price + 0.05,
                'bid_quantity': random.randint(100, 1000),
                'ask_quantity': random.randint(100, 1000)
            },
            'timestamp': datetime.now()
        }
        
    def _get_mock_historical_data(self, symbol: str, days: int) -> List[Dict]:
        """Get mock historical data."""
        import random
        
        base_prices = {
            "RELIANCE": 2500,
            "TCS": 3500,
            "HDFC": 1500,
            "INFY": 1800,
            "WIPRO": 400
        }
        
        base_price = base_prices.get(symbol, 1000)
        data = []
        current_price = base_price
        
        for i in range(days):
            date = datetime.now() - timedelta(days=days-i)
            
            # Generate random price movement
            change_percent = random.uniform(-2, 2)
            current_price = current_price * (1 + change_percent / 100)
            
            open_price = current_price * random.uniform(0.98, 1.02)
            high_price = max(open_price, current_price) * random.uniform(1.0, 1.02)
            low_price = min(open_price, current_price) * random.uniform(0.98, 1.0)
            
            data.append({
                'timestamp': date,
                'open': open_price,
                'high': high_price,
                'low': low_price,
                'close': current_price,
                'volume': random.randint(100000, 1000000)
            })
        
        return data
