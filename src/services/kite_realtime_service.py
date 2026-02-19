"""
Kite API Real-Time Data Streaming Service
=========================================

This module implements real-time data streaming from Kite API for stock analysis
and re-ranking. It includes WebSocket connection management, data processing,
and integration with the paper trading system.
"""

import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Callable, Dict, List, Optional

import numpy as np
from kiteconnect import KiteConnect, KiteTicker

from config.settings import get_settings
from core.logging_config import get_logger
from services.kite_credentials_manager import get_kite_credentials_manager

# Import configuration and credentials
from src.common.time_utils import now_ist_naive

# Configure logging
logger = get_logger(__name__)


class MarketStatus(Enum):
    PRE_MARKET = "pre_market"
    MARKET_OPEN = "market_open"
    MARKET_CLOSE = "market_close"
    POST_MARKET = "post_market"


@dataclass
class RealTimeData:
    """Real-time market data structure."""

    symbol: str
    instrument_token: int
    last_price: float
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: int
    change: float
    change_percent: float
    timestamp: datetime
    bid_price: float
    ask_price: float
    bid_quantity: int
    ask_quantity: int
    ohlc: Dict[str, float]
    last_quantity: int
    average_price: float
    oi: int
    oi_day_high: int
    oi_day_low: int
    total_buy_quantity: int
    total_sell_quantity: int


@dataclass
class TechnicalIndicators:
    """Technical indicators calculated from real-time data."""

    symbol: str
    timestamp: datetime
    rsi: float
    sma_5: float
    sma_20: float
    sma_50: float
    ema_12: float
    ema_26: float
    macd: float
    macd_signal: float
    macd_histogram: float
    bollinger_upper: float
    bollinger_middle: float
    bollinger_lower: float
    volume_sma: float
    price_momentum: float
    volatility: float
    atr: float


@dataclass
class StockRanking:
    """Stock ranking based on real-time analysis."""

    symbol: str
    rank: int
    score: float
    technical_score: float
    momentum_score: float
    volume_score: float
    volatility_score: float
    overall_signal: str  # "buy", "sell", "hold"
    confidence: float
    entry_price: float
    target_price: float
    stop_loss: float
    risk_reward_ratio: float
    timestamp: datetime


class KiteRealTimeService:
    """Real-time data streaming service using Kite API."""

    def __init__(self, api_key: str = "", access_token: str = ""):
        # Initialize settings and credentials manager
        self.settings = get_settings()
        self.kite_config = self.settings.kite
        self.credentials_manager = get_kite_credentials_manager()

        # Load credentials
        self.credentials = self.credentials_manager.load_credentials()

        # Use provided credentials or loaded credentials
        self.api_key = api_key or self.credentials.api_key
        self.access_token = access_token or self.credentials.access_token

        # Initialize Kite clients
        self.kite = None
        self.kws = None

        if self.api_key and self.access_token:
            try:
                self.kite = KiteConnect(api_key=self.api_key)
                self.kite.set_access_token(self.access_token)
                self.kws = KiteTicker(self.api_key, self.access_token)
                logger.info("✅ Kite clients initialized successfully")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Kite clients: {e}")
                self.kite = None
                self.kws = None
        else:
            logger.warning("⚠️ Kite credentials not available - service will use mock data")

        # Data storage
        self.realtime_data: Dict[str, RealTimeData] = {}
        self.historical_data: Dict[str, List[RealTimeData]] = {}
        self.technical_indicators: Dict[str, TechnicalIndicators] = {}
        self.stock_rankings: List[StockRanking] = []

        # Configuration
        self.subscribed_instruments: List[int] = []
        self.data_callbacks: List[Callable] = []
        self.analysis_callbacks: List[Callable] = []

        # State management
        self.is_connected = False
        self.is_streaming = False
        self.last_heartbeat = None

        # Analysis parameters
        self.rsi_period = 14
        self.sma_periods = [5, 20, 50]
        self.bollinger_period = 20
        self.bollinger_std = 2
        self.atr_period = 14

        logger.info("KiteRealTimeService initialized")

    def load_credentials(self, credentials_file: str = None):
        """Load credentials from file or environment."""
        try:
            # Update credentials file path if provided
            if credentials_file:
                self.kite_config.credentials_file = credentials_file

            # Reload credentials using the credentials manager
            self.credentials = self.credentials_manager.load_credentials()

            # Update API key and access token
            self.api_key = self.credentials.api_key
            self.access_token = self.credentials.access_token

            # Reinitialize Kite clients if credentials are available
            if self.api_key and self.access_token:
                self.kite = KiteConnect(api_key=self.api_key)
                self.kite.set_access_token(self.access_token)
                self.kws = KiteTicker(self.api_key, self.access_token)

                logger.info(
                    "Credentials loaded successfully",
                    extra={
                        "credentials_file": credentials_file or self.kite_config.credentials_file,
                        "api_key": self.api_key[:10] + "..." if self.api_key else None,
                        "has_access_token": bool(self.access_token),
                        "user_id": self.credentials.user_id,
                    },
                )
            else:
                logger.warning(
                    "No valid credentials found",
                    extra={
                        "credentials_file": credentials_file or self.kite_config.credentials_file
                    },
                )

        except Exception as e:
            logger.error(
                f"Failed to load credentials: {e}",
                extra={
                    "credentials_file": credentials_file or self.kite_config.credentials_file,
                    "error": str(e),
                },
            )
            raise

    def get_instruments(self, exchange: str = "NSE") -> Dict[str, Dict]:
        """Get list of instruments from Kite API."""
        try:
            if not self.kite:
                logger.warning("Kite client not available - returning mock instruments")
                return self._get_mock_instruments()

            instruments = self.kite.instruments(exchange)
            instrument_dict = {}

            for instrument in instruments:
                if instrument["instrument_type"] == "EQ":  # Equity only
                    instrument_dict[instrument["tradingsymbol"]] = {
                        "instrument_token": instrument["instrument_token"],
                        "name": instrument["name"],
                        "exchange": instrument["exchange"],
                        "lot_size": instrument["lot_size"],
                        "tick_size": instrument["tick_size"],
                    }

            logger.info(
                "Instruments fetched",
                extra={
                    "exchange": exchange,
                    "total_instruments": len(instruments),
                    "equity_instruments": len(instrument_dict),
                },
            )

            return instrument_dict

        except Exception as e:
            logger.warning(f"Failed to get instruments from Kite API: {e}")
            return self._get_mock_instruments()

    def _get_mock_instruments(self) -> Dict[str, Dict]:
        """Get mock instruments for testing."""
        return {
            "RELIANCE": {
                "instrument_token": 738561,
                "name": "RELIANCE",
                "exchange": "NSE",
                "lot_size": 1,
                "tick_size": 0.05,
            },
            "TCS": {
                "instrument_token": 2953217,
                "name": "TCS",
                "exchange": "NSE",
                "lot_size": 1,
                "tick_size": 0.05,
            },
            "HDFC": {
                "instrument_token": 341249,
                "name": "HDFC",
                "exchange": "NSE",
                "lot_size": 1,
                "tick_size": 0.05,
            },
            "INFY": {
                "instrument_token": 408065,
                "name": "INFY",
                "exchange": "NSE",
                "lot_size": 1,
                "tick_size": 0.05,
            },
            "WIPRO": {
                "instrument_token": 969473,
                "name": "WIPRO",
                "exchange": "NSE",
                "lot_size": 1,
                "tick_size": 0.05,
            },
        }

    def subscribe_to_instruments(self, symbols: List[str], exchange: str = "NSE"):
        """Subscribe to real-time data for specified instruments."""
        try:
            instruments = self.get_instruments(exchange)
            instrument_tokens = []

            for symbol in symbols:
                if symbol in instruments:
                    token = instruments[symbol]["instrument_token"]
                    instrument_tokens.append(token)
                    logger.info(f"Subscribed to {symbol} (token: {token})")
                else:
                    logger.warning(f"Instrument {symbol} not found in {exchange}")

            self.subscribed_instruments = instrument_tokens
            return instrument_tokens

        except Exception as e:
            logger.error(f"Failed to subscribe to instruments: {e}")
            return []

    def setup_callbacks(self):
        """Setup WebSocket callbacks for real-time data."""
        if not self.kws:
            logger.warning("Kite WebSocket not available - callbacks not set up")
            return

        def on_ticks(ws, ticks):
            """Handle incoming tick data."""
            try:
                for tick in ticks:
                    self._process_tick_data(tick)
                self._trigger_data_callbacks()
            except Exception as e:
                logger.error(f"Error processing ticks: {e}")

        def on_connect(ws, response):
            """Handle WebSocket connection."""
            logger.info("WebSocket connected")
            self.is_connected = True
            self.last_heartbeat = datetime.now()

            # Subscribe to instruments
            if self.subscribed_instruments:
                ws.subscribe(self.subscribed_instruments)
                ws.set_mode(ws.MODE_FULL, self.subscribed_instruments)
                logger.info(f"Subscribed to {len(self.subscribed_instruments)} instruments")

        def on_close(ws, code, reason):
            """Handle WebSocket disconnection."""
            logger.warning(f"WebSocket closed: {code} - {reason}")
            self.is_connected = False
            self.is_streaming = False

        def on_error(ws, code, reason):
            """Handle WebSocket errors."""
            logger.error(f"WebSocket error: {code} - {reason}")
            self.is_connected = False

        def on_reconnect(ws, attempts_count):
            """Handle WebSocket reconnection."""
            logger.info(f"WebSocket reconnecting... attempt {attempts_count}")

        def on_noreconnect(ws):
            """Handle failed reconnection."""
            logger.error("WebSocket reconnection failed")
            self.is_connected = False

        # Set callbacks
        self.kws.on_ticks = on_ticks
        self.kws.on_connect = on_connect
        self.kws.on_close = on_close
        self.kws.on_error = on_error
        self.kws.on_reconnect = on_reconnect
        self.kws.on_noreconnect = on_noreconnect

    def _process_tick_data(self, tick: Dict):
        """Process incoming tick data."""
        try:
            instrument_token = tick["instrument_token"]

            # Find symbol from instrument token
            symbol = self._get_symbol_from_token(instrument_token)
            if not symbol:
                return

            # Create RealTimeData object
            realtime_data = RealTimeData(
                symbol=symbol,
                instrument_token=instrument_token,
                last_price=tick.get("last_price", 0),
                open_price=tick.get("ohlc", {}).get("open", 0),
                high_price=tick.get("ohlc", {}).get("high", 0),
                low_price=tick.get("ohlc", {}).get("low", 0),
                close_price=tick.get("ohlc", {}).get("close", 0),
                volume=tick.get("volume", 0),
                change=tick.get("change", 0),
                change_percent=tick.get("change_percent", 0),
                timestamp=now_ist_naive(),
                bid_price=tick.get("best_bid_price", 0),
                ask_price=tick.get("best_ask_price", 0),
                bid_quantity=tick.get("best_bid_quantity", 0),
                ask_quantity=tick.get("best_ask_quantity", 0),
                ohlc=tick.get("ohlc", {}),
                last_quantity=tick.get("last_quantity", 0),
                average_price=tick.get("average_price", 0),
                oi=tick.get("oi", 0),
                oi_day_high=tick.get("oi_day_high", 0),
                oi_day_low=tick.get("oi_day_low", 0),
                total_buy_quantity=tick.get("total_buy_quantity", 0),
                total_sell_quantity=tick.get("total_sell_quantity", 0),
            )

            # Store real-time data
            self.realtime_data[symbol] = realtime_data

            # Store historical data (keep last 100 ticks)
            if symbol not in self.historical_data:
                self.historical_data[symbol] = []

            self.historical_data[symbol].append(realtime_data)
            if len(self.historical_data[symbol]) > 100:
                self.historical_data[symbol] = self.historical_data[symbol][-100:]

            # Log tick data processing
            logger.debug(
                "Tick processed",
                extra={
                    "symbol": symbol,
                    "last_price": realtime_data.last_price,
                    "change_percent": realtime_data.change_percent,
                    "volume": realtime_data.volume,
                    "historical_data_count": len(self.historical_data[symbol]),
                },
            )

            # Calculate technical indicators
            self._calculate_technical_indicators(symbol)

            logger.debug(f"Technical indicators calculated for {symbol}")

        except Exception as e:
            logger.error(
                f"Error processing tick data: {e}",
                extra={"tick_token": tick.get("instrument_token")},
            )

    def _get_symbol_from_token(self, instrument_token: int) -> Optional[str]:
        """Get symbol from instrument token."""
        # This would need to be implemented based on your instrument mapping
        # For now, we'll use a simple mapping
        token_to_symbol = {
            738561: "RELIANCE",
            2953217: "TCS",
            341249: "HDFC",
            1594: "INFY",
            969473: "WIPRO",
        }
        return token_to_symbol.get(instrument_token)

    def _calculate_technical_indicators(self, symbol: str):
        """Calculate technical indicators for a symbol."""
        try:
            if symbol not in self.historical_data or len(self.historical_data[symbol]) < 20:
                logger.debug(
                    f"Not enough historical data for {symbol}: "
                    f"{len(self.historical_data.get(symbol, []))}"
                )
                return

            data = self.historical_data[symbol]
            prices = [d.last_price for d in data]
            volumes = [d.volume for d in data]

            if len(prices) < max(self.sma_periods):
                return

            # Calculate RSI
            rsi = self._calculate_rsi(prices)

            # Calculate SMAs
            sma_5 = np.mean(prices[-5:]) if len(prices) >= 5 else prices[-1]
            sma_20 = np.mean(prices[-20:]) if len(prices) >= 20 else prices[-1]
            sma_50 = np.mean(prices[-50:]) if len(prices) >= 50 else prices[-1]

            # Calculate EMAs
            ema_12 = self._calculate_ema(prices, 12)
            ema_26 = self._calculate_ema(prices, 26)

            # Calculate MACD
            macd = ema_12 - ema_26
            macd_signal = self._calculate_ema([macd], 9) if len(prices) >= 26 else macd
            macd_histogram = macd - macd_signal

            # Calculate Bollinger Bands
            bb_middle = sma_20
            bb_std = np.std(prices[-20:]) if len(prices) >= 20 else 0
            bb_upper = bb_middle + (self.bollinger_std * bb_std)
            bb_lower = bb_middle - (self.bollinger_std * bb_std)

            # Calculate volume SMA
            volume_sma = np.mean(volumes[-20:]) if len(volumes) >= 20 else volumes[-1]

            # Calculate price momentum
            price_momentum = (
                ((prices[-1] - prices[-5]) / prices[-5] * 100) if len(prices) >= 5 else 0
            )

            # Calculate volatility (standard deviation of returns)
            returns = np.diff(prices) / prices[:-1]
            volatility = np.std(returns) * 100 if len(returns) > 1 else 0

            # Calculate ATR (Average True Range)
            atr = self._calculate_atr(data)

            # Create TechnicalIndicators object
            indicators = TechnicalIndicators(
                symbol=symbol,
                timestamp=now_ist_naive(),
                rsi=rsi,
                sma_5=sma_5,
                sma_20=sma_20,
                sma_50=sma_50,
                ema_12=ema_12,
                ema_26=ema_26,
                macd=macd,
                macd_signal=macd_signal,
                macd_histogram=macd_histogram,
                bollinger_upper=bb_upper,
                bollinger_middle=bb_middle,
                bollinger_lower=bb_lower,
                volume_sma=volume_sma,
                price_momentum=price_momentum,
                volatility=volatility,
                atr=atr,
            )

            self.technical_indicators[symbol] = indicators

        except Exception as e:
            logger.error(f"Error calculating technical indicators for {symbol}: {e}")

    def _calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """Calculate RSI indicator."""
        if len(prices) < period + 1:
            return 50.0

        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)

        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])

        if avg_loss == 0:
            return 100.0

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def _calculate_ema(self, prices: List[float], period: int) -> float:
        """Calculate EMA indicator."""
        if len(prices) < period:
            return prices[-1] if prices else 0

        multiplier = 2 / (period + 1)
        ema = prices[0]

        for price in prices[1:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))

        return ema

    def _calculate_atr(self, data: List[RealTimeData], period: int = 14) -> float:
        """Calculate Average True Range."""
        if len(data) < period + 1:
            return 0

        true_ranges = []
        for i in range(1, len(data)):
            high = data[i].high_price
            low = data[i].low_price
            prev_close = data[i - 1].close_price

            tr1 = high - low
            tr2 = abs(high - prev_close)
            tr3 = abs(low - prev_close)

            true_range = max(tr1, tr2, tr3)
            true_ranges.append(true_range)

        return np.mean(true_ranges[-period:]) if true_ranges else 0

    def analyze_and_rank_stocks(self) -> List[StockRanking]:
        """Analyze stocks and create rankings based on real-time data."""
        try:
            rankings = []

            for symbol, data in self.realtime_data.items():
                if symbol not in self.technical_indicators:
                    logger.debug(f"No technical indicators for {symbol}")
                    continue

                indicators = self.technical_indicators[symbol]

                # Calculate scores
                technical_score = self._calculate_technical_score(indicators)
                momentum_score = self._calculate_momentum_score(indicators)
                volume_score = self._calculate_volume_score(data, indicators)
                volatility_score = self._calculate_volatility_score(indicators)

                # Overall score
                overall_score = (
                    technical_score * 0.3
                    + momentum_score * 0.3
                    + volume_score * 0.2
                    + volatility_score * 0.2
                )

                # Determine signal
                signal, confidence = self._determine_signal(indicators, overall_score)

                # Calculate entry, target, and stop loss
                entry_price = data.last_price
                target_price, stop_loss = self._calculate_targets(entry_price, indicators, signal)
                risk_reward_ratio = (
                    abs(target_price - entry_price) / abs(entry_price - stop_loss)
                    if entry_price != stop_loss
                    else 0
                )

                ranking = StockRanking(
                    symbol=symbol,
                    rank=0,  # Will be set after sorting
                    score=overall_score,
                    technical_score=technical_score,
                    momentum_score=momentum_score,
                    volume_score=volume_score,
                    volatility_score=volatility_score,
                    overall_signal=signal,
                    confidence=confidence,
                    entry_price=entry_price,
                    target_price=target_price,
                    stop_loss=stop_loss,
                    risk_reward_ratio=risk_reward_ratio,
                    timestamp=now_ist_naive(),
                )

                rankings.append(ranking)

                logger.debug(
                    "Stock analyzed",
                    extra={
                        "symbol": symbol,
                        "overall_score": overall_score,
                        "signal": signal,
                        "confidence": confidence,
                    },
                )

            # Sort by score and assign ranks
            rankings.sort(key=lambda x: x.score, reverse=True)
            for i, ranking in enumerate(rankings):
                ranking.rank = i + 1

            self.stock_rankings = rankings

            logger.info(
                f"Analysis completed: {len(rankings)} stocks ranked",
                extra={"rankings_count": len(rankings)},
            )

            return rankings

        except Exception as e:
            logger.error(f"Error analyzing and ranking stocks: {e}")
            return []

    def _calculate_technical_score(self, indicators: TechnicalIndicators) -> float:
        """Calculate technical analysis score."""
        score = 0

        # RSI score (30-70 range is good)
        if 30 <= indicators.rsi <= 70:
            score += 25
        elif 20 <= indicators.rsi < 30 or 70 < indicators.rsi <= 80:
            score += 15

        # MACD score
        if indicators.macd > indicators.macd_signal and indicators.macd_histogram > 0:
            score += 25
        elif indicators.macd > indicators.macd_signal:
            score += 15

        # Bollinger Bands score
        current_price = indicators.bollinger_middle  # Assuming current price
        if indicators.bollinger_lower < current_price < indicators.bollinger_upper:
            score += 25
        elif current_price < indicators.bollinger_lower:
            score += 20  # Oversold, potential buy
        elif current_price > indicators.bollinger_upper:
            score += 10  # Overbought, potential sell

        # Moving averages score
        if indicators.sma_5 > indicators.sma_20 > indicators.sma_50:
            score += 25
        elif indicators.sma_5 > indicators.sma_20:
            score += 15

        return min(score, 100)

    def _calculate_momentum_score(self, indicators: TechnicalIndicators) -> float:
        """Calculate momentum score."""
        score = 0

        # Price momentum
        if indicators.price_momentum > 2:
            score += 40
        elif indicators.price_momentum > 0:
            score += 25
        elif indicators.price_momentum > -2:
            score += 15

        # RSI momentum
        if 40 <= indicators.rsi <= 60:
            score += 30
        elif 30 <= indicators.rsi < 40 or 60 < indicators.rsi <= 70:
            score += 20

        # MACD momentum
        if indicators.macd_histogram > 0:
            score += 30

        return min(score, 100)

    def _calculate_volume_score(self, data: RealTimeData, indicators: TechnicalIndicators) -> float:
        """Calculate volume analysis score."""
        if indicators.volume_sma == 0:
            return 50

        volume_ratio = data.volume / indicators.volume_sma

        if volume_ratio > 2:
            return 100
        elif volume_ratio > 1.5:
            return 80
        elif volume_ratio > 1:
            return 60
        elif volume_ratio > 0.5:
            return 40
        else:
            return 20

    def _calculate_volatility_score(self, indicators: TechnicalIndicators) -> float:
        """Calculate volatility score."""
        if indicators.volatility < 1:
            return 100  # Low volatility is good
        elif indicators.volatility < 2:
            return 80
        elif indicators.volatility < 3:
            return 60
        elif indicators.volatility < 5:
            return 40
        else:
            return 20

    def _determine_signal(self, indicators: TechnicalIndicators, overall_score: float) -> tuple:
        """Determine trading signal and confidence."""
        signal = "hold"
        confidence = 0.5

        # Strong buy signals
        if (
            overall_score > 80
            and indicators.rsi < 70
            and indicators.macd > indicators.macd_signal
            and indicators.price_momentum > 1
        ):
            signal = "buy"
            confidence = min(0.9, overall_score / 100)

        # Strong sell signals
        elif (
            overall_score < 30
            and indicators.rsi > 30
            and indicators.macd < indicators.macd_signal
            and indicators.price_momentum < -1
        ):
            signal = "sell"
            confidence = min(0.9, (100 - overall_score) / 100)

        # Weak buy signals
        elif (
            overall_score > 60 and indicators.rsi < 80 and indicators.macd > indicators.macd_signal
        ):
            signal = "buy"
            confidence = min(0.7, overall_score / 100)

        # Weak sell signals
        elif (
            overall_score < 40 and indicators.rsi > 20 and indicators.macd < indicators.macd_signal
        ):
            signal = "sell"
            confidence = min(0.7, (100 - overall_score) / 100)

        return signal, confidence

    def _calculate_targets(
        self, entry_price: float, indicators: TechnicalIndicators, signal: str
    ) -> tuple:
        """Calculate target price and stop loss."""
        atr = indicators.atr

        if signal == "buy":
            target_price = entry_price + (2 * atr)
            stop_loss = entry_price - (1 * atr)
        elif signal == "sell":
            target_price = entry_price - (2 * atr)
            stop_loss = entry_price + (1 * atr)
        else:
            target_price = entry_price
            stop_loss = entry_price

        return target_price, stop_loss

    def add_data_callback(self, callback: Callable):
        """Add callback for real-time data updates."""
        self.data_callbacks.append(callback)

    def add_analysis_callback(self, callback: Callable):
        """Add callback for analysis updates."""
        self.analysis_callbacks.append(callback)

    def _trigger_data_callbacks(self):
        """Trigger data update callbacks."""
        for callback in self.data_callbacks:
            try:
                callback(self.realtime_data)
            except Exception as e:
                logger.error(f"Error in data callback: {e}")

    def _trigger_analysis_callbacks(self):
        """Trigger analysis update callbacks."""
        for callback in self.analysis_callbacks:
            try:
                callback(self.stock_rankings)
            except Exception as e:
                logger.error(f"Error in analysis callback: {e}")

    def start_streaming(self):
        """Start real-time data streaming."""
        try:
            if not self.kws:
                logger.warning("Kite WebSocket not available - cannot start streaming")
                logger.info("Starting mock data streaming for testing...")
                self._start_mock_streaming()
                return

            self.setup_callbacks()
            self.kws.connect()
            self.is_streaming = True
            logger.info("Started real-time data streaming")
        except Exception as e:
            logger.error(f"Failed to start streaming: {e}")
            logger.info("Starting mock data streaming as fallback...")
            self._start_mock_streaming()

    def _start_mock_streaming(self):
        """Start mock data streaming for testing."""
        self.is_streaming = True
        logger.info("Started mock data streaming")

        # Generate mock data for subscribed instruments
        if self.subscribed_instruments:
            self._generate_mock_data()

    def _generate_mock_data(self):
        """Generate mock tick data for testing."""
        import random

        mock_symbols = ["RELIANCE", "TCS", "HDFC", "INFY", "WIPRO"]
        base_prices = {"RELIANCE": 2500, "TCS": 3500, "HDFC": 1500, "INFY": 1800, "WIPRO": 400}

        for symbol in mock_symbols:
            if symbol in base_prices:
                base_price = base_prices[symbol]

                # Generate multiple historical data points for analysis
                historical_data = []
                current_price = base_price

                for i in range(50):  # Generate 50 historical points
                    # Generate random price movement
                    change_percent = random.uniform(-1, 1)
                    current_price = current_price * (1 + change_percent / 100)

                    mock_tick = {
                        "instrument_token": self._get_mock_instruments()[symbol][
                            "instrument_token"
                        ],
                        "last_price": current_price,
                        "ohlc": {
                            "open": current_price * 0.99,
                            "high": current_price * 1.01,
                            "low": current_price * 0.98,
                            "close": current_price,
                        },
                        "volume": random.randint(100000, 1000000),
                        "change": current_price - base_price,
                        "change_percent": ((current_price - base_price) / base_price) * 100,
                        "last_quantity": random.randint(1, 100),
                        "average_price": current_price,
                        "best_bid_price": current_price - 0.05,
                        "best_ask_price": current_price + 0.05,
                        "best_bid_quantity": random.randint(100, 1000),
                        "best_ask_quantity": random.randint(100, 1000),
                        "oi": random.randint(10000, 100000),
                        "oi_day_high": random.randint(100000, 200000),
                        "oi_day_low": random.randint(50000, 100000),
                        "total_buy_quantity": random.randint(500000, 2000000),
                        "total_sell_quantity": random.randint(500000, 2000000),
                    }

                    historical_data.append(mock_tick)

                # Process the latest tick
                latest_tick = historical_data[-1]
                self._process_tick_data(latest_tick)

                # Add historical data to the service
                if symbol not in self.historical_data:
                    self.historical_data[symbol] = []

                # Convert to RealTimeData objects and add to historical data
                for tick in historical_data:
                    realtime_data = RealTimeData(
                        symbol=symbol,
                        instrument_token=tick["instrument_token"],
                        last_price=tick["last_price"],
                        open_price=tick["ohlc"]["open"],
                        high_price=tick["ohlc"]["high"],
                        low_price=tick["ohlc"]["low"],
                        close_price=tick["ohlc"]["close"],
                        volume=tick["volume"],
                        change=tick["change"],
                        change_percent=tick["change_percent"],
                        timestamp=now_ist_naive(),
                        bid_price=tick["best_bid_price"],
                        ask_price=tick["best_ask_price"],
                        bid_quantity=tick["best_bid_quantity"],
                        ask_quantity=tick["best_ask_quantity"],
                        ohlc=tick["ohlc"],
                        last_quantity=tick["last_quantity"],
                        average_price=tick["average_price"],
                        oi=tick["oi"],
                        oi_day_high=tick["oi_day_high"],
                        oi_day_low=tick["oi_day_low"],
                        total_buy_quantity=tick["total_buy_quantity"],
                        total_sell_quantity=tick["total_sell_quantity"],
                    )
                    self.historical_data[symbol].append(realtime_data)

                # Calculate technical indicators after adding historical data
                self._calculate_technical_indicators(symbol)

    def stop_streaming(self):
        """Stop real-time data streaming."""
        try:
            if self.kws:
                self.kws.close()
            self.is_streaming = False
            self.is_connected = False
            logger.info("Stopped real-time data streaming")
        except Exception as e:
            logger.error(f"Error stopping streaming: {e}")

    def get_market_status(self) -> MarketStatus:
        """Get current market status."""
        try:
            # This would need to be implemented based on market hours
            # For now, return a simple status
            now = datetime.now()
            hour = now.hour

            if 9 <= hour < 15:
                return MarketStatus.MARKET_OPEN
            elif 15 <= hour < 16:
                return MarketStatus.MARKET_CLOSE
            else:
                return MarketStatus.PRE_MARKET
        except Exception as e:
            logger.error(f"Error getting market status: {e}")
            return MarketStatus.PRE_MARKET

    def get_top_ranked_stocks(self, limit: int = 10) -> List[StockRanking]:
        """Get top ranked stocks."""
        return self.stock_rankings[:limit]

    def get_stock_data(self, symbol: str) -> Optional[RealTimeData]:
        """Get real-time data for a specific stock."""
        return self.realtime_data.get(symbol)

    def get_technical_indicators(self, symbol: str) -> Optional[TechnicalIndicators]:
        """Get technical indicators for a specific stock."""
        return self.technical_indicators.get(symbol)


# Example usage and testing
def main():
    """Example usage of KiteRealTimeService."""

    # Initialize service with new configuration system
    service = KiteRealTimeService()  # Will load credentials automatically

    # Subscribe to instruments
    symbols = ["RELIANCE", "TCS", "HDFC", "INFY", "WIPRO"]
    service.subscribe_to_instruments(symbols)

    # Add callbacks
    def on_data_update(data):
        print(f"Data updated for {len(data)} stocks")

    def on_analysis_update(rankings):
        print(f"Analysis updated: {len(rankings)} stocks ranked")
        for ranking in rankings[:5]:  # Top 5
            print(
                f"{ranking.rank}. {ranking.symbol}: {ranking.overall_signal} "
                f"(score: {ranking.score:.2f})"
            )

    service.add_data_callback(on_data_update)
    service.add_analysis_callback(on_analysis_update)

    # Start streaming
    service.start_streaming()

    try:
        # Run analysis every 30 seconds
        while True:
            time.sleep(30)
            service.analyze_and_rank_stocks()
    except KeyboardInterrupt:
        print("Stopping service...")
        service.stop_streaming()


if __name__ == "__main__":
    main()
