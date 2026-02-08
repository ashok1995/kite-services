"""
Yahoo Finance Service
====================

Service for fetching market data, fundamentals, and news from Yahoo Finance.
Provides broader market context to complement Kite Connect data.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import aiohttp
import yfinance as yf
import pandas as pd
from dataclasses import dataclass

from config.settings import get_settings
from core.logging_config import get_logger


@dataclass
class YahooStockData:
    """Yahoo Finance stock data structure."""
    symbol: str
    timestamp: datetime
    last_price: float
    change: float
    change_percent: float
    volume: int
    market_cap: Optional[float]
    pe_ratio: Optional[float]
    dividend_yield: Optional[float]
    fifty_two_week_high: Optional[float]
    fifty_two_week_low: Optional[float]
    beta: Optional[float]
    fundamentals: Dict[str, Any]
    news_sentiment: Dict[str, Any]


@dataclass
class MarketIndex:
    """Market index data."""
    symbol: str
    name: str
    last_price: float
    change: float
    change_percent: float
    timestamp: datetime


class YahooFinanceService:
    """Service for Yahoo Finance data integration."""
    
    def __init__(self, cache_service=None):
        self.settings = get_settings()
        self.logger = get_logger(__name__)
        self.cache_service = cache_service  # Redis cache service
        
        # Configuration
        self.yahoo_config = self.settings.yahoo
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Data cache (legacy, for backward compatibility)
        self.stock_cache: Dict[str, YahooStockData] = {}
        self.index_cache: Dict[str, MarketIndex] = {}
        self.cache_ttl = 300  # 5 minutes
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 60 / self.yahoo_config.rate_limit  # seconds between requests
        
    async def initialize(self):
        """Initialize Yahoo Finance service."""
        self.logger.info("Initializing Yahoo Finance Service...")
        
        try:
            # Create HTTP session
            timeout = aiohttp.ClientTimeout(total=self.yahoo_config.timeout)
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            )
            
            self.logger.info("✅ Yahoo Finance Service initialized successfully")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize Yahoo Finance Service: {e}")
            raise
            
    async def cleanup(self):
        """Cleanup Yahoo Finance service."""
        self.logger.info("Cleaning up Yahoo Finance Service...")
        
        if self.session:
            await self.session.close()
        
        self.logger.info("✅ Yahoo Finance Service cleaned up")
        
    async def get_stock_data(self, symbol: str) -> Optional[YahooStockData]:
        """Get comprehensive stock data from Yahoo Finance."""
        try:
            # Check cache first
            if symbol in self.stock_cache:
                cached_data = self.stock_cache[symbol]
                if (datetime.now() - cached_data.timestamp).total_seconds() < self.cache_ttl:
                    return cached_data
            
            # Rate limiting
            await self._rate_limit()
            
            # Convert symbol format if needed (NSE:RELIANCE -> RELIANCE.NS)
            yahoo_symbol = self._convert_symbol_format(symbol)
            
            # Get stock data using yfinance
            stock = yf.Ticker(yahoo_symbol)
            
            # Get current info
            info = stock.info
            
            # Get historical data for additional calculations
            hist = stock.history(period="1d", interval="1m")
            
            if hist.empty:
                self.logger.warning(f"No historical data found for {yahoo_symbol}")
                return None
            
            # Extract current price data
            current_price = info.get('currentPrice', hist['Close'].iloc[-1])
            previous_close = info.get('previousClose', hist['Close'].iloc[0])
            
            change = current_price - previous_close
            change_percent = (change / previous_close * 100) if previous_close != 0 else 0
            
            # Get fundamentals
            fundamentals = {
                'market_cap': info.get('marketCap'),
                'enterprise_value': info.get('enterpriseValue'),
                'pe_ratio': info.get('trailingPE'),
                'forward_pe': info.get('forwardPE'),
                'peg_ratio': info.get('pegRatio'),
                'price_to_book': info.get('priceToBook'),
                'price_to_sales': info.get('priceToSalesTrailing12Months'),
                'debt_to_equity': info.get('debtToEquity'),
                'return_on_equity': info.get('returnOnEquity'),
                'return_on_assets': info.get('returnOnAssets'),
                'revenue_growth': info.get('revenueGrowth'),
                'earnings_growth': info.get('earningsGrowth'),
                'profit_margins': info.get('profitMargins'),
                'operating_margins': info.get('operatingMargins'),
                'dividend_yield': info.get('dividendYield'),
                'payout_ratio': info.get('payoutRatio')
            }
            
            # Get news sentiment (simplified)
            news_sentiment = await self._get_news_sentiment(yahoo_symbol)
            
            stock_data = YahooStockData(
                symbol=symbol,
                timestamp=datetime.now(),
                last_price=current_price,
                change=change,
                change_percent=change_percent,
                volume=int(hist['Volume'].iloc[-1]) if not hist.empty else 0,
                market_cap=info.get('marketCap'),
                pe_ratio=info.get('trailingPE'),
                dividend_yield=info.get('dividendYield'),
                fifty_two_week_high=info.get('fiftyTwoWeekHigh'),
                fifty_two_week_low=info.get('fiftyTwoWeekLow'),
                beta=info.get('beta'),
                fundamentals=fundamentals,
                news_sentiment=news_sentiment
            )
            
            # Cache the data
            self.stock_cache[symbol] = stock_data
            
            self.logger.info(f"Retrieved Yahoo Finance data for {symbol}")
            return stock_data
            
        except Exception as e:
            self.logger.error(f"Error getting Yahoo Finance data for {symbol}: {e}")
            return None
            
    async def get_market_indices(self) -> List[MarketIndex]:
        """Get major market indices data."""
        try:
            indices_symbols = {
                '^NSEI': 'NIFTY 50',
                '^NSEBANK': 'BANK NIFTY',
                '^GSPC': 'S&P 500',
                '^IXIC': 'NASDAQ',
                '^DJI': 'Dow Jones',
                '^FTSE': 'FTSE 100'
            }
            
            indices = []
            
            for symbol, name in indices_symbols.items():
                try:
                    # Check cache
                    if symbol in self.index_cache:
                        cached_data = self.index_cache[symbol]
                        if (datetime.now() - cached_data.timestamp).total_seconds() < self.cache_ttl:
                            indices.append(cached_data)
                            continue
                    
                    # Rate limiting
                    await self._rate_limit()
                    
                    # Get index data
                    ticker = yf.Ticker(symbol)
                    hist = ticker.history(period="2d", interval="1d")
                    
                    if len(hist) >= 2:
                        current_price = hist['Close'].iloc[-1]
                        previous_price = hist['Close'].iloc[-2]
                        
                        change = current_price - previous_price
                        change_percent = (change / previous_price * 100) if previous_price != 0 else 0
                        
                        index_data = MarketIndex(
                            symbol=symbol,
                            name=name,
                            last_price=current_price,
                            change=change,
                            change_percent=change_percent,
                            timestamp=datetime.now()
                        )
                        
                        # Cache the data
                        self.index_cache[symbol] = index_data
                        indices.append(index_data)
                        
                except Exception as e:
                    self.logger.error(f"Error getting index data for {symbol}: {e}")
                    continue
            
            return indices
            
        except Exception as e:
            self.logger.error(f"Error getting market indices: {e}")
            return []
            
    async def get_sector_performance(self) -> Dict[str, float]:
        """Get sector-wise performance data."""
        try:
            # ⚠️ DEPRECATED: Yahoo Finance sector ETFs (many delisted)
            # Now using Kite Connect Nifty sector indices instead
            # This method is kept for backward compatibility but returns empty
            # Use KiteClient.get_sector_performance() for Indian sectors
            
            self.logger.warning("⚠️ Yahoo Finance sector data deprecated - use Kite Connect Nifty sector indices")
            sector_performance = {}
            
            # Return empty - caller should use Kite Connect for Indian sectors
            return sector_performance
            
            # OLD CODE (disabled - delisted symbols):
            # sector_etfs = {
            #     'BANKBEES.NS': 'Banking',  # May still work
            #     'ITBEES.NS': 'IT',  # May still work
            #     'PHARMBEES.NS': 'Pharma',  # DELISTED
            #     'AUTOBEES.NS': 'Auto',  # May still work
            #     'FMCGBEES.NS': 'FMCG',  # DELISTED
            #     'METALBEES.NS': 'Metals',  # DELISTED
            #     'ENERGYBEES.NS': 'Energy',  # DELISTED
            #     'REALTYBEES.NS': 'Realty'  # DELISTED
            # }
            
        except Exception as e:
            self.logger.error(f"Error getting sector performance: {e}")
            return {}
            
    async def get_economic_indicators(self) -> Dict[str, float]:
        """Get key economic indicators."""
        try:
            indicators = {}
            
            # VIX (Volatility Index)
            try:
                await self._rate_limit()
                vix = yf.Ticker('^INDIAVIX')
                vix_hist = vix.history(period="1d", interval="1m")
                if not vix_hist.empty:
                    indicators['india_vix'] = vix_hist['Close'].iloc[-1]
            except:
                pass
            
            # USD/INR
            try:
                await self._rate_limit()
                usdinr = yf.Ticker('USDINR=X')
                usdinr_hist = usdinr.history(period="1d", interval="1m")
                if not usdinr_hist.empty:
                    indicators['usd_inr'] = usdinr_hist['Close'].iloc[-1]
            except:
                pass
            
            # Gold prices
            try:
                await self._rate_limit()
                gold = yf.Ticker('GC=F')
                gold_hist = gold.history(period="1d", interval="1m")
                if not gold_hist.empty:
                    indicators['gold_usd'] = gold_hist['Close'].iloc[-1]
            except:
                pass
            
            # Oil prices
            try:
                await self._rate_limit()
                oil = yf.Ticker('CL=F')
                oil_hist = oil.history(period="1d", interval="1m")
                if not oil_hist.empty:
                    indicators['crude_oil'] = oil_hist['Close'].iloc[-1]
            except:
                pass
            
            return indicators
            
        except Exception as e:
            self.logger.error(f"Error getting economic indicators: {e}")
            return {}
            
    async def search_symbols(self, query: str) -> List[Dict[str, str]]:
        """Search for symbols matching the query."""
        try:
            # This is a simplified implementation
            # In production, you might use Yahoo Finance search API
            
            # Common Indian stocks mapping
            indian_stocks = {
                'reliance': 'RELIANCE.NS',
                'tcs': 'TCS.NS',
                'hdfc': 'HDFCBANK.NS',
                'infy': 'INFY.NS',
                'infosys': 'INFY.NS',
                'wipro': 'WIPRO.NS',
                'bharti': 'BHARTIARTL.NS',
                'airtel': 'BHARTIARTL.NS',
                'itc': 'ITC.NS',
                'sbi': 'SBIN.NS',
                'kotak': 'KOTAKBANK.NS',
                'lt': 'LT.NS',
                'larsen': 'LT.NS'
            }
            
            results = []
            query_lower = query.lower()
            
            for name, symbol in indian_stocks.items():
                if query_lower in name:
                    results.append({
                        'symbol': symbol,
                        'name': name.upper(),
                        'exchange': 'NSE'
                    })
            
            return results[:10]  # Limit to 10 results
            
        except Exception as e:
            self.logger.error(f"Error searching symbols: {e}")
            return []
            
    def _convert_symbol_format(self, symbol: str) -> str:
        """Convert symbol format for Yahoo Finance."""
        # Remove exchange prefix if present
        if ':' in symbol:
            symbol = symbol.split(':')[1]
        
        # Add .NS suffix for NSE stocks if not present
        if not symbol.endswith('.NS') and not symbol.startswith('^'):
            symbol = f"{symbol}.NS"
        
        return symbol
        
    async def _rate_limit(self):
        """Implement rate limiting."""
        current_time = asyncio.get_event_loop().time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last_request
            await asyncio.sleep(sleep_time)
        
        self.last_request_time = asyncio.get_event_loop().time()
        
    async def _get_news_sentiment(self, symbol: str) -> Dict[str, Any]:
        """Get news sentiment for a symbol (simplified implementation)."""
        try:
            # This is a placeholder implementation
            # In production, you might integrate with news APIs or sentiment analysis services
            
            return {
                'sentiment_score': 0.0,  # -1 to 1
                'sentiment_label': 'neutral',
                'news_count': 0,
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting news sentiment for {symbol}: {e}")
            return {
                'sentiment_score': 0.0,
                'sentiment_label': 'neutral',
                'news_count': 0,
                'last_updated': datetime.now().isoformat()
            }


# Example usage
if __name__ == "__main__":
    async def test_yahoo_service():
        service = YahooFinanceService()
        await service.initialize()
        
        try:
            # Test stock data
            stock_data = await service.get_stock_data("RELIANCE")
            if stock_data:
                print(f"RELIANCE: ₹{stock_data.last_price:.2f} ({stock_data.change_percent:+.2f}%)")
            
            # Test indices
            indices = await service.get_market_indices()
            for index in indices:
                print(f"{index.name}: {index.last_price:.2f} ({index.change_percent:+.2f}%)")
            
            # Test sector performance
            sectors = await service.get_sector_performance()
            for sector, performance in sectors.items():
                print(f"{sector}: {performance:+.2f}%")
                
        finally:
            await service.cleanup()
    
    asyncio.run(test_yahoo_service())
