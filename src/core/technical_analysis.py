"""
Technical Analysis Engine for Enhanced Market Context
====================================================

This module provides comprehensive technical analysis capabilities using pandas-ta.
It calculates and interprets various technical indicators based on trading horizons.

Key Features:
- Multi-horizon technical analysis (intraday, swing, long-term)
- Trend indicators (Moving Averages, MACD, Bollinger Bands)
- Momentum/Sentiment indicators (RSI, Stochastic, Williams %R)
- Intelligent interpretation of indicator values
- Strict "No Mock Data" policy
"""

import pandas as pd
import numpy as np
# import pandas_ta as ta  # Commented out for Docker compatibility
from typing import List, Dict, Optional, Tuple
from models.enhanced_market_context_models import Trend, Sentiment, Horizon

class TechnicalAnalysisEngine:
    """
    Core engine for technical analysis calculations and interpretations.
    """
    
    def __init__(self):
        """Initialize the technical analysis engine."""
        self.horizon_periods = {
            Horizon.INTRADAY: {
                'sma_short': 5,
                'sma_long': 20,
                'ema_short': 8,
                'ema_long': 21,
                'rsi_period': 14,
                'macd_fast': 12,
                'macd_slow': 26,
                'macd_signal': 9,
                'bb_period': 20,
                'stoch_k': 14,
                'stoch_d': 3
            },
            Horizon.SWING: {
                'sma_short': 20,
                'sma_long': 50,
                'ema_short': 20,
                'ema_long': 50,
                'rsi_period': 14,
                'macd_fast': 12,
                'macd_slow': 26,
                'macd_signal': 9,
                'bb_period': 20,
                'stoch_k': 14,
                'stoch_d': 3
            },
            Horizon.LONG_TERM: {
                'sma_short': 50,
                'sma_long': 200,
                'ema_short': 50,
                'ema_long': 200,
                'rsi_period': 21,
                'macd_fast': 12,
                'macd_slow': 26,
                'macd_signal': 9,
                'bb_period': 20,
                'stoch_k': 21,
                'stoch_d': 5
            }
        }

    def analyze_price_data(self, df: pd.DataFrame, horizon: Horizon) -> Tuple[List[Trend], List[Sentiment]]:
        """
        Perform comprehensive technical analysis on price data.
        
        Args:
            df: DataFrame with OHLCV data (columns: Open, High, Low, Close, Volume)
            horizon: Trading horizon for analysis
            
        Returns:
            Tuple of (trend_indicators, sentiment_indicators) or ([], []) if insufficient data
        """
        # Define minimum data requirements per horizon
        min_data_requirements = {
            Horizon.INTRADAY: 20,    # Minimum for intraday analysis
            Horizon.SWING: 50,       # Standard for swing trading
            Horizon.LONG_TERM: 100   # More data for long-term analysis
        }
        
        min_required = min_data_requirements.get(horizon, 50)
        
        if df.empty or len(df) < min_required:
            print(f"❌ Insufficient data for {horizon.value} technical analysis (need {min_required}+ bars, got {len(df)}) - Returning null")
            return [], []  # Strict "no mock data" - return empty lists
        
        try:
            periods = self.horizon_periods[horizon]
            trend_indicators = []
            sentiment_indicators = []
            
            # Calculate trend indicators
            trend_indicators.extend(self._calculate_moving_averages(df, periods))
            trend_indicators.extend(self._calculate_macd(df, periods))
            trend_indicators.extend(self._calculate_bollinger_bands(df, periods))
            
            # Calculate momentum/sentiment indicators
            sentiment_indicators.extend(self._calculate_rsi(df, periods))
            sentiment_indicators.extend(self._calculate_stochastic(df, periods))
            sentiment_indicators.extend(self._calculate_williams_r(df, periods))
            
            return trend_indicators, sentiment_indicators
            
        except Exception as e:
            print(f"❌ Technical analysis error: {e}")
            return [], []

    def _calculate_moving_averages(self, df: pd.DataFrame, periods: Dict) -> List[Trend]:
        """Calculate and interpret moving averages with 5-category trend system."""
        indicators = []
        
        try:
            # Simple Moving Averages (custom calculation)
            sma_short = df['Close'].rolling(window=periods['sma_short']).mean()
            sma_long = df['Close'].rolling(window=periods['sma_long']).mean()
            
            # Check if indicators were calculated successfully
            if sma_short is None or sma_long is None:
                print(f"❌ SMA calculation returned None")
                return indicators
                
            if sma_short.empty or sma_long.empty:
                print(f"❌ SMA calculation returned empty series")
                return indicators
            
            current_price = df['Close'].iloc[-1]
            sma_short_val = sma_short.iloc[-1]
            sma_long_val = sma_long.iloc[-1]
            
            # 5-Category Trend System based on MA relationship and price position
            price_above_short = current_price > sma_short_val
            price_above_long = current_price > sma_long_val
            short_above_long = sma_short_val > sma_long_val
            
            # Calculate trend strength percentage
            ma_spread = abs(sma_short_val - sma_long_val) / sma_long_val * 100
            price_distance = abs(current_price - sma_short_val) / sma_short_val * 100
            
            if short_above_long and price_above_short and price_above_long and ma_spread > 2:
                interpretation = "Strong Bullish"
            elif short_above_long and price_above_short and price_above_long:
                interpretation = "Bullish"
            elif not short_above_long and not price_above_short and not price_above_long and ma_spread > 2:
                interpretation = "Strong Bearish"
            elif not short_above_long and not price_above_short and not price_above_long:
                interpretation = "Bearish"
            else:
                interpretation = "Neutral"
            
            indicators.append(Trend(
                indicator="Simple Moving Average",
                value={
                    f"SMA_{periods['sma_short']}": float(sma_short_val),
                    f"SMA_{periods['sma_long']}": float(sma_long_val),
                    "current_price": float(current_price),
                    "spread_percent": float(ma_spread)
                },
                interpretation=interpretation
            ))
            
            # Exponential Moving Averages with 5-category system (custom calculation)
            ema_short = df['Close'].ewm(span=periods['ema_short']).mean()
            ema_long = df['Close'].ewm(span=periods['ema_long']).mean()
            
            # Check if indicators were calculated successfully
            if ema_short is None or ema_long is None:
                print(f"❌ EMA calculation returned None")
                return indicators
                
            if ema_short.empty or ema_long.empty:
                print(f"❌ EMA calculation returned empty series")
                return indicators
            
            ema_short_val = ema_short.iloc[-1]
            ema_long_val = ema_long.iloc[-1]
            
            # Check for crossovers and implement 5-category system
            prev_ema_short = ema_short.iloc[-2] if len(ema_short) > 1 else ema_short_val
            prev_ema_long = ema_long.iloc[-2] if len(ema_long) > 1 else ema_long_val
            
            # Calculate EMA spread for trend strength
            ema_spread = abs(ema_short_val - ema_long_val) / ema_long_val * 100
            current_price = df['Close'].iloc[-1]
            
            # 5-Category EMA Trend System
            if prev_ema_short <= prev_ema_long and ema_short_val > ema_long_val:
                interpretation = "Bullish Crossover"  # Category 1: Fresh bullish signal
            elif prev_ema_short >= prev_ema_long and ema_short_val < ema_long_val:
                interpretation = "Bearish Crossover"  # Category 2: Fresh bearish signal
            elif ema_short_val > ema_long_val and current_price > ema_short_val and ema_spread > 1.5:
                interpretation = "Strong Bullish"     # Category 3: Strong uptrend
            elif ema_short_val < ema_long_val and current_price < ema_short_val and ema_spread > 1.5:
                interpretation = "Strong Bearish"     # Category 4: Strong downtrend
            elif ema_short_val > ema_long_val:
                interpretation = "Bullish"            # Category 5: Weak uptrend
            elif ema_short_val < ema_long_val:
                interpretation = "Bearish"            # Category 6: Weak downtrend
            else:
                interpretation = "Neutral"            # Category 7: No clear trend
            
            indicators.append(Trend(
                indicator="Exponential Moving Average",
                value={
                    f"EMA_{periods['ema_short']}": float(ema_short_val),
                    f"EMA_{periods['ema_long']}": float(ema_long_val),
                    "spread_percent": float(ema_spread),
                    "crossover_detected": prev_ema_short <= prev_ema_long and ema_short_val > ema_long_val or prev_ema_short >= prev_ema_long and ema_short_val < ema_long_val
                },
                interpretation=interpretation
            ))
                
        except Exception as e:
            print(f"❌ Moving averages calculation error: {e}")
        
        return indicators

    def _calculate_macd(self, df: pd.DataFrame, periods: Dict) -> List[Trend]:
        """Calculate and interpret MACD."""
        indicators = []
        
        try:
            # Custom MACD calculation
            ema_fast = df['Close'].ewm(span=periods['macd_fast']).mean()
            ema_slow = df['Close'].ewm(span=periods['macd_slow']).mean()
            macd_line = ema_fast - ema_slow
            signal_line = macd_line.ewm(span=periods['macd_signal']).mean()
            histogram = macd_line - signal_line
            
            # Create DataFrame similar to pandas-ta output
            macd_data = pd.DataFrame({
                'MACD': macd_line,
                'Signal': signal_line,
                'Histogram': histogram
            })
            
            if macd_data is not None and not macd_data.empty:
                macd_line = macd_data.iloc[:, 0]  # MACD line
                signal_line = macd_data.iloc[:, 1]  # Signal line
                histogram = macd_data.iloc[:, 2]  # Histogram
                
                if not macd_line.empty and not signal_line.empty:
                    macd_val = macd_line.iloc[-1]
                    signal_val = signal_line.iloc[-1]
                    hist_val = histogram.iloc[-1]
                    
                    # 5-Category MACD Trend System
                    # Check for crossovers
                    prev_macd = macd_line.iloc[-2] if len(macd_line) > 1 else macd_val
                    prev_signal = signal_line.iloc[-2] if len(signal_line) > 1 else signal_val
                    
                    # Calculate momentum strength
                    histogram_strength = abs(hist_val) if hist_val else 0
                    
                    if prev_macd <= prev_signal and macd_val > signal_val:
                        interpretation = "Bullish Crossover"  # Category 1: Fresh bullish signal
                    elif prev_macd >= prev_signal and macd_val < signal_val:
                        interpretation = "Bearish Crossover"  # Category 2: Fresh bearish signal
                    elif macd_val > signal_val and hist_val > 0 and histogram_strength > 0.5:
                        interpretation = "Strong Bullish"     # Category 3: Strong momentum up
                    elif macd_val < signal_val and hist_val < 0 and histogram_strength > 0.5:
                        interpretation = "Strong Bearish"     # Category 4: Strong momentum down
                    elif macd_val > signal_val:
                        interpretation = "Bullish"            # Category 5: Weak momentum up
                    elif macd_val < signal_val:
                        interpretation = "Bearish"            # Category 6: Weak momentum down
                    else:
                        interpretation = "Neutral"            # Category 7: No momentum
                    
                    indicators.append(Trend(
                        indicator="MACD",
                        value={
                            "macd": float(macd_val),
                            "signal": float(signal_val),
                            "histogram": float(hist_val)
                        },
                        interpretation=interpretation
                    ))
                    
        except Exception as e:
            print(f"❌ MACD calculation error: {e}")
        
        return indicators

    def _calculate_bollinger_bands(self, df: pd.DataFrame, periods: Dict) -> List[Trend]:
        """Calculate and interpret Bollinger Bands."""
        indicators = []
        
        try:
            # Custom Bollinger Bands calculation
            sma = df['Close'].rolling(window=periods['bb_period']).mean()
            std = df['Close'].rolling(window=periods['bb_period']).std()
            bb_upper = sma + (std * 2)
            bb_lower = sma - (std * 2)
            
            # Create DataFrame similar to pandas-ta output
            bb_data = pd.DataFrame({
                'BBL': bb_lower,
                'BBM': sma,
                'BBU': bb_upper
            })
            
            if bb_data is not None and not bb_data.empty:
                bb_lower = bb_data.iloc[:, 0]  # Lower band
                bb_middle = bb_data.iloc[:, 1]  # Middle band (SMA)
                bb_upper = bb_data.iloc[:, 2]  # Upper band
                
                if not bb_lower.empty and not bb_upper.empty:
                    current_price = df['Close'].iloc[-1]
                    lower_val = bb_lower.iloc[-1]
                    middle_val = bb_middle.iloc[-1]
                    upper_val = bb_upper.iloc[-1]
                    
                    # Interpret position relative to bands
                    if current_price > upper_val:
                        interpretation = "Overbought (Above Upper Band)"
                    elif current_price < lower_val:
                        interpretation = "Oversold (Below Lower Band)"
                    elif current_price > middle_val:
                        interpretation = "Bullish (Above Middle)"
                    elif current_price < middle_val:
                        interpretation = "Bearish (Below Middle)"
                    else:
                        interpretation = "Neutral"
                    
                    indicators.append(Trend(
                        indicator="Bollinger Bands",
                        value={
                            "upper": float(upper_val),
                            "middle": float(middle_val),
                            "lower": float(lower_val),
                            "current_price": float(current_price)
                        },
                        interpretation=interpretation
                    ))
                    
        except Exception as e:
            print(f"❌ Bollinger Bands calculation error: {e}")
        
        return indicators

    def _calculate_rsi(self, df: pd.DataFrame, periods: Dict) -> List[Sentiment]:
        """Calculate and interpret RSI."""
        indicators = []
        
        try:
            # Custom RSI calculation
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=periods['rsi_period']).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=periods['rsi_period']).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            if not rsi.empty:
                rsi_val = rsi.iloc[-1]
                
                # 5-Category RSI System
                if rsi_val >= 80:
                    interpretation = "Extreme Overbought"   # Category 1: Very overbought
                elif rsi_val >= 70:
                    interpretation = "Overbought"           # Category 2: Overbought
                elif rsi_val >= 60:
                    interpretation = "Bullish"              # Category 3: Bullish momentum
                elif rsi_val >= 40:
                    interpretation = "Neutral"              # Category 4: Neutral zone
                elif rsi_val >= 30:
                    interpretation = "Bearish"              # Category 5: Bearish momentum
                elif rsi_val >= 20:
                    interpretation = "Oversold"             # Category 6: Oversold
                else:
                    interpretation = "Extreme Oversold"     # Category 7: Very oversold
                
                indicators.append(Sentiment(
                    indicator="RSI",
                    value=float(rsi_val),
                    interpretation=interpretation
                ))
                
        except Exception as e:
            print(f"❌ RSI calculation error: {e}")
        
        return indicators

    def _calculate_stochastic(self, df: pd.DataFrame, periods: Dict) -> List[Sentiment]:
        """Calculate and interpret Stochastic Oscillator."""
        indicators = []
        
        try:
            # Custom Stochastic calculation
            k_period = periods['stoch_k']
            d_period = periods['stoch_d']
            
            # Calculate %K
            lowest_low = df['Low'].rolling(window=k_period).min()
            highest_high = df['High'].rolling(window=k_period).max()
            k_percent = 100 * ((df['Close'] - lowest_low) / (highest_high - lowest_low))
            
            # Calculate %D (moving average of %K)
            d_percent = k_percent.rolling(window=d_period).mean()
            
            # Create DataFrame similar to pandas-ta output
            stoch_data = pd.DataFrame({
                'STOCHk': k_percent,
                'STOCHd': d_percent
            })
            
            if stoch_data is not None and not stoch_data.empty:
                stoch_k = stoch_data.iloc[:, 0]  # %K
                stoch_d = stoch_data.iloc[:, 1]  # %D
                
                if not stoch_k.empty and not stoch_d.empty:
                    k_val = stoch_k.iloc[-1]
                    d_val = stoch_d.iloc[-1]
                    
                    # Interpret Stochastic levels
                    if k_val >= 80 and d_val >= 80:
                        interpretation = "Overbought"
                    elif k_val <= 20 and d_val <= 20:
                        interpretation = "Oversold"
                    elif k_val > d_val and k_val > 50:
                        interpretation = "Bullish"
                    elif k_val < d_val and k_val < 50:
                        interpretation = "Bearish"
                    else:
                        interpretation = "Neutral"
                    
                    indicators.append(Sentiment(
                        indicator="Stochastic Oscillator",
                        value=float((k_val + d_val) / 2),  # Average of %K and %D
                        interpretation=interpretation
                    ))
                    
        except Exception as e:
            print(f"❌ Stochastic calculation error: {e}")
        
        return indicators

    def _calculate_williams_r(self, df: pd.DataFrame, periods: Dict) -> List[Sentiment]:
        """Calculate and interpret Williams %R."""
        indicators = []
        
        try:
            # Custom Williams %R calculation
            period = 14
            highest_high = df['High'].rolling(window=period).max()
            lowest_low = df['Low'].rolling(window=period).min()
            williams_r = -100 * ((highest_high - df['Close']) / (highest_high - lowest_low))
            
            if not williams_r.empty:
                wr_val = williams_r.iloc[-1]
                
                # Interpret Williams %R levels (note: values are negative)
                if wr_val >= -20:
                    interpretation = "Overbought"
                elif wr_val <= -80:
                    interpretation = "Oversold"
                elif wr_val >= -40:
                    interpretation = "Bullish"
                elif wr_val <= -60:
                    interpretation = "Bearish"
                else:
                    interpretation = "Neutral"
                
                indicators.append(Sentiment(
                    indicator="Williams %R",
                    value=float(wr_val),
                    interpretation=interpretation
                ))
                
        except Exception as e:
            print(f"❌ Williams %R calculation error: {e}")
        
        return indicators

# Global instance for use by the service
technical_engine = TechnicalAnalysisEngine()
