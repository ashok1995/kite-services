"""
Kite Connect Client
==================

Core client for Kite Connect API integration.
Provides unified interface for market data, orders, and portfolio management.
"""

import asyncio
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from kiteconnect import KiteConnect, KiteTicker

from config.settings import get_settings
from core.logging_config import get_logger
from core.token_manager import TokenManager


class KiteClient:
    """Core Kite Connect client."""

    def __init__(self, cache_service=None):
        self.settings = get_settings()
        self.logger = get_logger(__name__)
        self.cache_service = cache_service  # Redis cache service

        # Kite configuration
        self.kite_config = self.settings.kite

        # Token manager for file-based token updates
        self.token_manager = TokenManager()

        # Kite instances
        self.kite: Optional[KiteConnect] = None
        self.kws: Optional[KiteTicker] = None

        # Connection state
        self.is_connected = False
        self.is_streaming = False

        # Data storage (legacy, for backward compatibility)
        self.instruments_cache: Dict[str, Dict] = {}
        self.historical_data_cache: Dict[str, List[Dict]] = {}

    async def initialize(self):
        """Initialize Kite client."""
        self.logger.info("Initializing Kite Client...")

        try:
            # Load credentials
            await self._load_credentials()

            # Debug: Check what credentials are loaded
            self.logger.info(
                f"Debug - API Key: {self.kite_config.api_key[:10]}..."
                if self.kite_config.api_key
                else "Debug - API Key: None"
            )
            self.logger.info(
                f"Debug - Access Token: {self.kite_config.access_token[:10]}..."
                if self.kite_config.access_token
                else "Debug - Access Token: None"
            )

            # Initialize Kite Connect
            if self.kite_config.api_key and self.kite_config.access_token:
                self.kite = KiteConnect(api_key=self.kite_config.api_key)
                self.kite.set_access_token(self.kite_config.access_token)

                # Initialize WebSocket
                self.kws = KiteTicker(
                    api_key=self.kite_config.api_key, access_token=self.kite_config.access_token
                )

                # Test connection
                await self._test_connection()

                self.logger.info("✅ Kite Client initialized successfully")
            else:
                self.logger.warning("⚠️ Kite credentials not available - using mock mode")
                self.logger.warning(f"API Key present: {bool(self.kite_config.api_key)}")
                self.logger.warning(f"Access Token present: {bool(self.kite_config.access_token)}")

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
            if self.cache_service and self.cache_service.enabled:
                cached_data = await self.cache_service.get(cache_key)
                if cached_data:
                    self.logger.info(
                        f"Retrieved {len(cached_data)} instruments from cache for {exchange}"
                    )
                    return cached_data

            # Fetch from API (run in executor to avoid blocking)
            loop = asyncio.get_event_loop()
            instruments = await loop.run_in_executor(None, self.kite.instruments, exchange)
            instrument_dict = {}

            for instrument in instruments:
                if instrument["instrument_type"] == "EQ":  # Equity only
                    instrument_dict[instrument["tradingsymbol"]] = {
                        "instrument_token": instrument["instrument_token"],
                        "name": instrument["name"],
                        "exchange": instrument["exchange"],
                        "lot_size": instrument["lot_size"],
                        "tick_size": instrument["tick_size"],
                        "instrument_type": instrument["instrument_type"],
                        "segment": instrument.get("segment", "EQ"),
                    }

            # Cache the result for 24 hours (instruments don't change often)
            if self.cache_service and self.cache_service.enabled:
                await self.cache_service.set(cache_key, instrument_dict, ttl=86400)  # 24 hours

            self.logger.info(f"Retrieved {len(instrument_dict)} instruments from {exchange}")
            return instrument_dict

        except Exception as e:
            self.logger.error(f"Error getting instruments: {e}")
            return self._get_mock_instruments()

    async def quote(self, symbols: List[str]) -> Dict[str, Dict]:
        """
        Get real-time quotes for symbols.

        Works even when markets are closed - provides last traded prices.

        Args:
            symbols: List of symbols in format "EXCHANGE:SYMBOL" (e.g., "NSE:NIFTY 50")

        Returns:
            Dictionary mapping symbols to their quote data
        """
        try:
            if not self.kite:
                self.logger.warning("Kite client not initialized")
                return {}

            # Call kite.quote() in a thread pool since it's synchronous
            loop = asyncio.get_event_loop()
            quotes = await loop.run_in_executor(None, self.kite.quote, symbols)

            self.logger.info(f"Fetched quotes for {len(symbols)} symbols")
            return quotes or {}

        except Exception as e:
            self.logger.error(f"Error getting quotes for {symbols}: {e}")
            return {}

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

            instrument_token = instruments[symbol]["instrument_token"]

            # Get quote
            quote = self.kite.quote([instrument_token])
            if not quote or instrument_token not in quote:
                return None

            data = quote[instrument_token]

            return {
                "symbol": symbol,
                "instrument_token": instrument_token,
                "last_price": data.get("last_price", 0),
                "change": data.get("net_change", 0),
                "change_percent": data.get("change", 0),
                "volume": data.get("volume", 0),
                "ohlc": data.get("ohlc", {}),
                "bid_ask": {
                    "bid_price": data.get("depth", {}).get("buy", [{}])[0].get("price", 0),
                    "ask_price": data.get("depth", {}).get("sell", [{}])[0].get("price", 0),
                    "bid_quantity": data.get("depth", {}).get("buy", [{}])[0].get("quantity", 0),
                    "ask_quantity": data.get("depth", {}).get("sell", [{}])[0].get("quantity", 0),
                },
                "timestamp": datetime.now(),
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
                    last_timestamp = cached_data[-1].get("timestamp")
                    if last_timestamp and (datetime.now() - last_timestamp).total_seconds() < 3600:
                        return cached_data

            # Get instrument token
            instruments = await self.get_instruments()
            if symbol not in instruments:
                return None

            instrument_token = instruments[symbol]["instrument_token"]

            # Calculate date range
            to_date = datetime.now()
            from_date = to_date - timedelta(days=days)

            # Get historical data
            historical_data = self.kite.historical_data(
                instrument_token=instrument_token,
                from_date=from_date.strftime("%Y-%m-%d"),
                to_date=to_date.strftime("%Y-%m-%d"),
                interval="day",
            )

            # Convert to standard format
            formatted_data = []
            for candle in historical_data:
                formatted_data.append(
                    {
                        "timestamp": candle["date"],
                        "open": candle["open"],
                        "high": candle["high"],
                        "low": candle["low"],
                        "close": candle["close"],
                        "volume": candle["volume"],
                    }
                )

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
                    tokens.append(instruments[symbol]["instrument_token"])
                else:
                    self.logger.warning(f"Symbol {symbol} not found for subscription")

            if tokens:
                # Subscribe to tokens
                self.kws.subscribe(tokens)
                self.kws.set_mode(self.kws.MODE_FULL, tokens)

                self.logger.info(f"Subscribed to {len(tokens)} instruments")

        except Exception as e:
            self.logger.error(f"Error subscribing to instruments: {e}")

    def get_login_url(self) -> str:
        """
        Get Kite Connect login URL for OAuth flow.
        User logs in at this URL and gets redirected with request_token.
        """
        if not self.kite_config.api_key:
            raise ValueError("API key not configured")
        kite = self.kite or KiteConnect(api_key=self.kite_config.api_key)
        return kite.login_url()

    async def generate_access_token(self, request_token: str, api_secret: str) -> Optional[str]:
        """Generate access token from request token."""
        try:
            if not self.kite_config.api_key:
                raise ValueError("API key not configured")

            # Initialize temporary Kite instance if not exists
            if not self.kite:
                self.kite = KiteConnect(api_key=self.kite_config.api_key)

            # Generate session
            data = await asyncio.to_thread(
                self.kite.generate_session, request_token, api_secret=api_secret
            )

            access_token = data["access_token"]
            self.logger.info(
                f"✅ Access token generated successfully for user: {data.get('user_id')}"
            )

            # Save to token file (for daily updates)
            self.token_manager.save_token(
                access_token=access_token,
                user_id=data.get("user_id"),
                user_name=data.get("user_name"),
                user_type=data.get("user_type"),
                email=data.get("email"),
                broker=data.get("broker"),
                exchanges=data.get("exchanges", []),
                products=data.get("products", []),
                order_types=data.get("order_types", []),
            )

            # Also save to legacy access_token.json for backward compatibility
            import json

            token_data = {
                "access_token": access_token,
                "user_id": data.get("user_id"),
                "user_name": data.get("user_name"),
                "user_type": data.get("user_type"),
                "email": data.get("email"),
                "broker": data.get("broker"),
                "exchanges": data.get("exchanges", []),
                "products": data.get("products", []),
                "order_types": data.get("order_types", []),
                "api_key": self.kite_config.api_key,
                "api_secret": api_secret,
                "request_token": request_token,
                "generated_at": datetime.now().isoformat(),
                "expires_at": (datetime.now() + timedelta(days=1)).isoformat(),
                "status": "active",
                "generated_by": "kite_services_api",
            }

            with open("access_token.json", "w") as f:
                json.dump(token_data, f, indent=2)

            # Also update .env file so next restart picks up the new token
            try:
                env_path = Path(__file__).parent.parent.parent / ".env"
                if env_path.exists():
                    env_content = env_path.read_text()
                    env_content = re.sub(
                        r"KITE_ACCESS_TOKEN=.*", f"KITE_ACCESS_TOKEN={access_token}", env_content
                    )
                    env_path.write_text(env_content)
                    self.logger.info("✅ Token updated in .env file")
            except Exception as env_err:
                self.logger.warning(f"Could not update .env: {env_err}")

            self.logger.info("✅ Token saved to access_token.json")

            return access_token

        except Exception as e:
            self.logger.error(f"❌ Failed to generate access token: {e}")
            raise

    async def set_access_token(self, access_token: str):
        """Set access token and reinitialize Kite client."""
        try:
            if not self.kite_config.api_key:
                raise ValueError("API key not configured")

            # Initialize/reinitialize Kite with new token
            self.kite = KiteConnect(api_key=self.kite_config.api_key)
            self.kite.set_access_token(access_token)

            # Update config
            self.kite_config.access_token = access_token

            # Test connection
            await self._test_connection()

            self.logger.info("✅ Access token set successfully")

        except Exception as e:
            self.logger.error(f"❌ Failed to set access token: {e}")
            raise

    async def get_access_token(self) -> Optional[str]:
        """Get current access token."""
        return self.kite_config.access_token

    async def get_profile(self) -> Optional[Dict]:
        """Get user profile."""
        try:
            if not self.kite:
                return None

            profile = await asyncio.to_thread(self.kite.profile)
            return profile

        except Exception as e:
            self.logger.error(f"Failed to get profile: {e}")
            return None

    async def get_margins(self) -> Optional[Dict]:
        """Get user margins."""
        try:
            if not self.kite:
                return None

            margins = await asyncio.to_thread(self.kite.margins)
            return margins

        except Exception as e:
            self.logger.error(f"Failed to get margins: {e}")
            return None

    async def get_sector_performance(self) -> Dict[str, float]:
        """Get Indian sector performance from Nifty sector indices."""
        try:
            if not self.kite:
                self.logger.warning("Kite client not initialized - cannot get sector performance")
                return {}

            # Nifty sector indices (official NSE indices)
            sector_indices = {
                "NSE:NIFTY BANK": "Banking",
                "NSE:NIFTY IT": "IT",
                "NSE:NIFTY PHARMA": "Pharma",
                "NSE:NIFTY AUTO": "Auto",
                "NSE:NIFTY FMCG": "FMCG",
                "NSE:NIFTY METAL": "Metal",
                "NSE:NIFTY ENERGY": "Energy",
                "NSE:NIFTY REALTY": "Realty",
            }

            # Get quotes for all sector indices
            symbols = list(sector_indices.keys())
            quotes = await self.quote(symbols)

            sector_performance = {}
            for symbol, sector_name in sector_indices.items():
                if symbol in quotes:
                    quote_data = quotes[symbol]
                    # Calculate change percentage from net_change and close price
                    net_change = quote_data.get("net_change", 0)
                    close_price = quote_data.get("ohlc", {}).get("close", 0)

                    if close_price and close_price > 0:
                        change_percent = (net_change / close_price) * 100
                        sector_performance[sector_name] = round(change_percent, 2)
                        self.logger.info(f"Sector {sector_name}: {change_percent:.2f}%")

            return sector_performance

        except Exception as e:
            self.logger.error(f"Failed to get sector performance: {e}")
            return {}

    async def get_market_status(self) -> Optional[Dict]:
        """Get current market status from Kite or derive from time."""
        try:
            now = datetime.now()
            hour = now.hour
            minute = now.minute
            weekday = now.weekday()  # 0=Monday, 6=Sunday

            # Markets closed on weekends
            if weekday >= 5:
                return {
                    "market_open": False,
                    "exchanges": [
                        {
                            "exchange": "NSE",
                            "status": "closed",
                            "session": "weekend",
                            "market_open": False,
                        },
                        {
                            "exchange": "BSE",
                            "status": "closed",
                            "session": "weekend",
                            "market_open": False,
                        },
                    ],
                }

            # Pre-market: 9:00-9:15, Open: 9:15-15:30, Post-market: 15:30-16:00
            market_open = (
                (hour == 9 and minute >= 15) or (10 <= hour <= 14) or (hour == 15 and minute <= 30)
            )
            if hour == 9 and minute < 15:
                session = "pre_market"
            elif market_open:
                session = "normal"
            elif hour == 15 and minute > 30 or hour == 16:
                session = "post_market"
            else:
                session = "closed"

            return {
                "market_open": market_open,
                "exchanges": [
                    {
                        "exchange": "NSE",
                        "status": "open" if market_open else "closed",
                        "session": session,
                        "market_open": market_open,
                    },
                    {
                        "exchange": "BSE",
                        "status": "open" if market_open else "closed",
                        "session": session,
                        "market_open": market_open,
                    },
                ],
            }
        except Exception as e:
            self.logger.error(f"Failed to get market status: {e}")
            return None

    async def get_positions(self) -> Optional[Dict]:
        """Get user positions."""
        try:
            if not self.kite:
                return None
            positions = await asyncio.to_thread(self.kite.positions)
            return positions
        except Exception as e:
            self.logger.error(f"Failed to get positions: {e}")
            return None

    async def get_holdings(self) -> Optional[List]:
        """Get user holdings."""
        try:
            if not self.kite:
                return None
            holdings = await asyncio.to_thread(self.kite.holdings)
            return holdings
        except Exception as e:
            self.logger.error(f"Failed to get holdings: {e}")
            return None

    async def _load_credentials(self):
        """Load Kite credentials from multiple sources."""
        # First, try to load from token file (highest priority for daily updates)
        file_token = self.token_manager.load_token()
        if file_token:
            self.kite_config.access_token = file_token
            self.logger.info("✅ Loaded access token from token file")

        # Fallback to settings/env if file token not available
        if not self.kite_config.access_token:
            self.logger.info("Token file not available, using settings/env token")

        # Start watching token file for changes
        self.token_manager.start_watching(callback=self._on_token_updated)

        if not self.kite_config.api_key or not self.kite_config.access_token:
            self.logger.warning("Kite credentials not configured")

    def _on_token_updated(self, new_token: str):
        """Handle token file update - reload token without restart."""
        self.logger.info("🔄 Token file updated, reloading Kite client...")
        try:
            # Update config
            self.kite_config.access_token = new_token

            # Update existing Kite instance
            if self.kite:
                self.kite.set_access_token(new_token)
                self.logger.info("✅ Kite client token updated")

            # Update WebSocket if connected
            if self.kws and self.is_streaming:
                self.logger.info("⚠️ WebSocket is active, will reconnect with new token")
                # Note: WebSocket reconnection should be handled by the service

        except Exception as e:
            self.logger.error(f"❌ Failed to update token: {e}", exc_info=True)

    async def _test_connection(self):
        """Test Kite API connection."""
        try:
            if self.kite:
                profile = self.kite.profile()
                if profile:
                    self.is_connected = True
                    self.logger.info(
                        f"Connected to Kite API as {profile.get('user_name', 'Unknown')}"
                    )
                else:
                    self.logger.warning("Failed to get profile from Kite API")
        except Exception as e:
            self.logger.error(f"Kite API connection test failed: {e}")

    def _get_mock_instruments(self) -> Dict[str, Dict]:
        """Get mock instruments for testing."""
        return {
            "RELIANCE": {
                "instrument_token": 738561,
                "name": "RELIANCE",
                "exchange": "NSE",
                "lot_size": 1,
                "tick_size": 0.05,
                "instrument_type": "EQ",
                "segment": "EQ",
            },
            "TCS": {
                "instrument_token": 2953217,
                "name": "TCS",
                "exchange": "NSE",
                "lot_size": 1,
                "tick_size": 0.05,
                "instrument_type": "EQ",
                "segment": "EQ",
            },
            "HDFC": {
                "instrument_token": 341249,
                "name": "HDFC",
                "exchange": "NSE",
                "lot_size": 1,
                "tick_size": 0.05,
                "instrument_type": "EQ",
                "segment": "EQ",
            },
            "INFY": {
                "instrument_token": 408065,
                "name": "INFY",
                "exchange": "NSE",
                "lot_size": 1,
                "tick_size": 0.05,
                "instrument_type": "EQ",
                "segment": "EQ",
            },
            "WIPRO": {
                "instrument_token": 969473,
                "name": "WIPRO",
                "exchange": "NSE",
                "lot_size": 1,
                "tick_size": 0.05,
                "instrument_type": "EQ",
                "segment": "EQ",
            },
        }

    def _get_mock_instrument_data(self, symbol: str) -> Dict:
        """Get mock instrument data."""
        import random

        base_prices = {"RELIANCE": 2500, "TCS": 3500, "HDFC": 1500, "INFY": 1800, "WIPRO": 400}

        base_price = base_prices.get(symbol, 1000)
        change_percent = random.uniform(-2, 2)
        current_price = base_price * (1 + change_percent / 100)

        return {
            "symbol": symbol,
            "instrument_token": 123456,
            "last_price": current_price,
            "change": current_price - base_price,
            "change_percent": change_percent,
            "volume": random.randint(100000, 1000000),
            "ohlc": {
                "open": base_price * 0.99,
                "high": current_price * 1.01,
                "low": current_price * 0.98,
                "close": current_price,
            },
            "bid_ask": {
                "bid_price": current_price - 0.05,
                "ask_price": current_price + 0.05,
                "bid_quantity": random.randint(100, 1000),
                "ask_quantity": random.randint(100, 1000),
            },
            "timestamp": datetime.now(),
        }

    def _get_mock_historical_data(self, symbol: str, days: int) -> List[Dict]:
        """Get mock historical data."""
        import random

        base_prices = {"RELIANCE": 2500, "TCS": 3500, "HDFC": 1500, "INFY": 1800, "WIPRO": 400}

        base_price = base_prices.get(symbol, 1000)
        data = []
        current_price = base_price

        for i in range(days):
            date = datetime.now() - timedelta(days=days - i)

            # Generate random price movement
            change_percent = random.uniform(-2, 2)
            current_price = current_price * (1 + change_percent / 100)

            open_price = current_price * random.uniform(0.98, 1.02)
            high_price = max(open_price, current_price) * random.uniform(1.0, 1.02)
            low_price = min(open_price, current_price) * random.uniform(0.98, 1.0)

            data.append(
                {
                    "timestamp": date,
                    "open": open_price,
                    "high": high_price,
                    "low": low_price,
                    "close": current_price,
                    "volume": random.randint(100000, 1000000),
                }
            )

        return data
