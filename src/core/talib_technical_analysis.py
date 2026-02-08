"""
Professional Technical Analysis Engine using TA-Lib
===================================================

This module provides comprehensive technical analysis using the industry-standard
TA-Lib library. TA-Lib is more stable and reliable than pandas-ta, especially
in containerized environments.

Key Features:
- Industry-standard TA-Lib calculations
- Multi-horizon technical analysis (intraday, swing, long-term)
- Professional-grade indicators (RSI, MACD, Bollinger Bands, Stochastic, etc.)
- Intelligent interpretation with 5-category system
- Docker-compatible and production-ready
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple

try:
    import talib
    TALIB_AVAILABLE = True
    print("✅ TA-Lib imported successfully")
except ImportError:
    TALIB_AVAILABLE = False
    print("⚠️ TA-Lib not available - falling back to custom calculations")

from models.enhanced_market_context_models import Trend, Sentiment, Horizon

class TALibTechnicalAnalysisEngine:
    """
    Professional technical analysis engine using TA-Lib.
    """
    
    def __init__(self):
        """Initialize the TA-Lib technical analysis engine."""
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
                'stoch_d': 3,
                'willr_period': 14
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
                'stoch_d': 3,
                'willr_period': 14
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
                'stoch_d': 5,
                'willr_period': 21
            }
        }

    def analyze_price_data(self, df: pd.DataFrame, horizon: Horizon) -> Tuple[List[Trend], List[Sentiment]]:
        """
        Perform comprehensive technical analysis using TA-Lib.
        
        Args:
            df: DataFrame with OHLCV data
            horizon: Trading horizon for analysis
            
        Returns:
            Tuple of (trend_indicators, sentiment_indicators)
        """
        # Define minimum data requirements per horizon
        min_data_requirements = {
            Horizon.INTRADAY: 25,    # Reduced for intraday
            Horizon.SWING: 60,       # Increased for better swing analysis
            Horizon.LONG_TERM: 200   # Full data for long-term
        }
        
        min_required = min_data_requirements.get(horizon, 60)
        
        if df.empty or len(df) < min_required:
            print(f"❌ Insufficient data for {horizon.value} TA-Lib analysis (need {min_required}+ bars, got {len(df)}) - Returning null")
            return [], []
        
        if not TALIB_AVAILABLE:
            print("❌ TA-Lib not available - using fallback calculations")
            return self._fallback_analysis(df, horizon)
        
        try:
            periods = self.horizon_periods[horizon]
            trend_indicators = []
            sentiment_indicators = []
            
            # Prepare data for TA-Lib (requires numpy arrays)
            high = df['High'].values
            low = df['Low'].values
            close = df['Close'].values
            volume = df['Volume'].values if 'Volume' in df.columns else None
            
            # Calculate trend indicators
            trend_indicators.extend(self._calculate_talib_moving_averages(close, periods))
            trend_indicators.extend(self._calculate_talib_macd(close, periods))
            trend_indicators.extend(self._calculate_talib_bollinger_bands(close, periods))
            
            # Calculate momentum/sentiment indicators
            sentiment_indicators.extend(self._calculate_talib_rsi(close, periods))
            sentiment_indicators.extend(self._calculate_talib_stochastic(high, low, close, periods))
            sentiment_indicators.extend(self._calculate_talib_williams_r(high, low, close, periods))
            
            print(f"✅ TA-Lib analysis complete: {len(trend_indicators)} trend, {len(sentiment_indicators)} sentiment")
            return trend_indicators, sentiment_indicators
            
        except Exception as e:
            print(f"❌ TA-Lib technical analysis error: {e}")
            return [], []

    def _calculate_talib_moving_averages(self, close: np.ndarray, periods: Dict) -> List[Trend]:
        """Calculate moving averages using TA-Lib."""
        indicators = []
        
        try:
            # Simple Moving Averages
            sma_short = talib.SMA(close, timeperiod=periods['sma_short'])
            sma_long = talib.SMA(close, timeperiod=periods['sma_long'])
            
            if not np.isnan(sma_short[-1]) and not np.isnan(sma_long[-1]):
                current_price = close[-1]
                sma_short_val = sma_short[-1]
                sma_long_val = sma_long[-1]
                
                # 5-Category Trend System
                price_above_short = current_price > sma_short_val
                price_above_long = current_price > sma_long_val
                short_above_long = sma_short_val > sma_long_val
                ma_spread = abs(sma_short_val - sma_long_val) / sma_long_val * 100
                
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
                    indicator="TA-Lib Simple Moving Average",
                    value={
                        f"SMA_{periods['sma_short']}": float(sma_short_val),
                        f"SMA_{periods['sma_long']}": float(sma_long_val),
                        "current_price": float(current_price),
                        "spread_percent": float(ma_spread)
                    },
                    interpretation=interpretation
                ))
            
            # Exponential Moving Averages
            ema_short = talib.EMA(close, timeperiod=periods['ema_short'])
            ema_long = talib.EMA(close, timeperiod=periods['ema_long'])
            
            if not np.isnan(ema_short[-1]) and not np.isnan(ema_long[-1]):
                ema_short_val = ema_short[-1]
                ema_long_val = ema_long[-1]
                current_price = close[-1]
                
                # Check for crossovers
                prev_ema_short = ema_short[-2] if len(ema_short) > 1 else ema_short_val
                prev_ema_long = ema_long[-2] if len(ema_long) > 1 else ema_long_val
                
                ema_spread = abs(ema_short_val - ema_long_val) / ema_long_val * 100
                
                # 5-Category EMA System
                if prev_ema_short <= prev_ema_long and ema_short_val > ema_long_val:
                    interpretation = "Bullish Crossover"
                elif prev_ema_short >= prev_ema_long and ema_short_val < ema_long_val:
                    interpretation = "Bearish Crossover"
                elif ema_short_val > ema_long_val and current_price > ema_short_val and ema_spread > 1.5:
                    interpretation = "Strong Bullish"
                elif ema_short_val < ema_long_val and current_price < ema_short_val and ema_spread > 1.5:
                    interpretation = "Strong Bearish"
                elif ema_short_val > ema_long_val:
                    interpretation = "Bullish"
                elif ema_short_val < ema_long_val:
                    interpretation = "Bearish"
                else:
                    interpretation = "Neutral"
                
                indicators.append(Trend(
                    indicator="TA-Lib Exponential Moving Average",
                    value={
                        f"EMA_{periods['ema_short']}": float(ema_short_val),
                        f"EMA_{periods['ema_long']}": float(ema_long_val),
                        "spread_percent": float(ema_spread),
                        "crossover_detected": bool(prev_ema_short <= prev_ema_long and ema_short_val > ema_long_val or prev_ema_short >= prev_ema_long and ema_short_val < ema_long_val)
                    },
                    interpretation=interpretation
                ))
                
        except Exception as e:
            print(f"❌ TA-Lib moving averages error: {e}")
        
        return indicators

    def _calculate_talib_macd(self, close: np.ndarray, periods: Dict) -> List[Trend]:
        """Calculate MACD using TA-Lib."""
        indicators = []
        
        try:
            macd_line, signal_line, histogram = talib.MACD(
                close,
                fastperiod=periods['macd_fast'],
                slowperiod=periods['macd_slow'],
                signalperiod=periods['macd_signal']
            )
            
            if not np.isnan(macd_line[-1]) and not np.isnan(signal_line[-1]):
                macd_val = macd_line[-1]
                signal_val = signal_line[-1]
                hist_val = histogram[-1]
                
                # Check for crossovers
                prev_macd = macd_line[-2] if len(macd_line) > 1 else macd_val
                prev_signal = signal_line[-2] if len(signal_line) > 1 else signal_val
                
                histogram_strength = abs(hist_val) if not np.isnan(hist_val) else 0
                
                # 5-Category MACD System
                if prev_macd <= prev_signal and macd_val > signal_val:
                    interpretation = "Bullish Crossover"
                elif prev_macd >= prev_signal and macd_val < signal_val:
                    interpretation = "Bearish Crossover"
                elif macd_val > signal_val and hist_val > 0 and histogram_strength > 0.5:
                    interpretation = "Strong Bullish"
                elif macd_val < signal_val and hist_val < 0 and histogram_strength > 0.5:
                    interpretation = "Strong Bearish"
                elif macd_val > signal_val:
                    interpretation = "Bullish"
                elif macd_val < signal_val:
                    interpretation = "Bearish"
                else:
                    interpretation = "Neutral"
                
                indicators.append(Trend(
                    indicator="TA-Lib MACD",
                    value={
                        "macd": float(macd_val),
                        "signal": float(signal_val),
                        "histogram": float(hist_val) if not np.isnan(hist_val) else None,
                        "crossover_detected": bool(prev_macd <= prev_signal and macd_val > signal_val or prev_macd >= prev_signal and macd_val < signal_val)
                    },
                    interpretation=interpretation
                ))
                
        except Exception as e:
            print(f"❌ TA-Lib MACD error: {e}")
        
        return indicators

    def _calculate_talib_bollinger_bands(self, close: np.ndarray, periods: Dict) -> List[Trend]:
        """Calculate Bollinger Bands using TA-Lib."""
        indicators = []
        
        try:
            bb_upper, bb_middle, bb_lower = talib.BBANDS(
                close,
                timeperiod=periods['bb_period'],
                nbdevup=2,
                nbdevdn=2,
                matype=0
            )
            
            if not np.isnan(bb_upper[-1]) and not np.isnan(bb_lower[-1]):
                current_price = close[-1]
                upper_val = bb_upper[-1]
                middle_val = bb_middle[-1]
                lower_val = bb_lower[-1]
                
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
                    indicator="TA-Lib Bollinger Bands",
                    value={
                        "upper": float(upper_val),
                        "middle": float(middle_val),
                        "lower": float(lower_val),
                        "current_price": float(current_price),
                        "band_width": float((upper_val - lower_val) / middle_val * 100)
                    },
                    interpretation=interpretation
                ))
                
        except Exception as e:
            print(f"❌ TA-Lib Bollinger Bands error: {e}")
        
        return indicators

    def _calculate_talib_rsi(self, close: np.ndarray, periods: Dict) -> List[Sentiment]:
        """Calculate RSI using TA-Lib."""
        indicators = []
        
        try:
            rsi = talib.RSI(close, timeperiod=periods['rsi_period'])
            
            if not np.isnan(rsi[-1]):
                rsi_val = rsi[-1]
                
                # 7-Category RSI System (enhanced from 5-category)
                if rsi_val >= 80:
                    interpretation = "Extreme Overbought"
                elif rsi_val >= 70:
                    interpretation = "Overbought"
                elif rsi_val >= 60:
                    interpretation = "Bullish"
                elif rsi_val >= 40:
                    interpretation = "Neutral"
                elif rsi_val >= 30:
                    interpretation = "Bearish"
                elif rsi_val >= 20:
                    interpretation = "Oversold"
                else:
                    interpretation = "Extreme Oversold"
                
                indicators.append(Sentiment(
                    indicator="TA-Lib RSI",
                    value=float(rsi_val),
                    interpretation=interpretation
                ))
                
        except Exception as e:
            print(f"❌ TA-Lib RSI error: {e}")
        
        return indicators

    def _calculate_talib_stochastic(self, high: np.ndarray, low: np.ndarray, close: np.ndarray, periods: Dict) -> List[Sentiment]:
        """Calculate Stochastic Oscillator using TA-Lib."""
        indicators = []
        
        try:
            slowk, slowd = talib.STOCH(
                high, low, close,
                fastk_period=periods['stoch_k'],
                slowk_period=periods['stoch_d'],
                slowk_matype=0,
                slowd_period=periods['stoch_d'],
                slowd_matype=0
            )
            
            if not np.isnan(slowk[-1]) and not np.isnan(slowd[-1]):
                k_val = slowk[-1]
                d_val = slowd[-1]
                
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
                    indicator="TA-Lib Stochastic Oscillator",
                    value=float((k_val + d_val) / 2),
                    interpretation=interpretation
                ))
                
        except Exception as e:
            print(f"❌ TA-Lib Stochastic error: {e}")
        
        return indicators

    def _calculate_talib_williams_r(self, high: np.ndarray, low: np.ndarray, close: np.ndarray, periods: Dict) -> List[Sentiment]:
        """Calculate Williams %R using TA-Lib."""
        indicators = []
        
        try:
            williams_r = talib.WILLR(high, low, close, timeperiod=periods['willr_period'])
            
            if not np.isnan(williams_r[-1]):
                wr_val = williams_r[-1]
                
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
                    indicator="TA-Lib Williams %R",
                    value=float(wr_val),
                    interpretation=interpretation
                ))
                
        except Exception as e:
            print(f"❌ TA-Lib Williams %R error: {e}")
        
        return indicators

    def _fallback_analysis(self, df: pd.DataFrame, horizon: Horizon) -> Tuple[List[Trend], List[Sentiment]]:
        """Fallback analysis using pandas when TA-Lib is not available."""
        print("🔄 Using fallback technical analysis calculations...")
        
        try:
            periods = self.horizon_periods[horizon]
            trend_indicators = []
            sentiment_indicators = []
            
            # Simple trend analysis using moving averages
            if len(df) >= periods['sma_long']:
                sma_short = df['Close'].rolling(window=periods['sma_short']).mean()
                sma_long = df['Close'].rolling(window=periods['sma_long']).mean()
                
                if not sma_short.empty and not sma_long.empty:
                    current_price = df['Close'].iloc[-1]
                    sma_short_val = sma_short.iloc[-1]
                    sma_long_val = sma_long.iloc[-1]
                    
                    if pd.notna(sma_short_val) and pd.notna(sma_long_val):
                        # Simple trend classification
                        if sma_short_val > sma_long_val and current_price > sma_short_val:
                            interpretation = "Bullish"
                        elif sma_short_val < sma_long_val and current_price < sma_short_val:
                            interpretation = "Bearish"
                        else:
                            interpretation = "Neutral"
                        
                        trend_indicators.append(Trend(
                            indicator="Fallback Moving Average",
                            value={
                                f"SMA_{periods['sma_short']}": float(sma_short_val),
                                f"SMA_{periods['sma_long']}": float(sma_long_val),
                                "current_price": float(current_price)
                            },
                            interpretation=interpretation
                        ))
            
            # Simple RSI calculation
            if len(df) >= periods['rsi_period']:
                delta = df['Close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=periods['rsi_period']).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=periods['rsi_period']).mean()
                rs = gain / loss
                rsi = 100 - (100 / (1 + rs))
                
                if not rsi.empty and pd.notna(rsi.iloc[-1]):
                    rsi_val = rsi.iloc[-1]
                    
                    if rsi_val >= 70:
                        interpretation = "Overbought"
                    elif rsi_val <= 30:
                        interpretation = "Oversold"
                    elif rsi_val >= 60:
                        interpretation = "Bullish"
                    elif rsi_val <= 40:
                        interpretation = "Bearish"
                    else:
                        interpretation = "Neutral"
                    
                    sentiment_indicators.append(Sentiment(
                        indicator="Fallback RSI",
                        value=float(rsi_val),
                        interpretation=interpretation
                    ))
            
            return trend_indicators, sentiment_indicators
            
        except Exception as e:
            print(f"❌ Fallback analysis error: {e}")
            return [], []

# Global TA-Lib engine instance
talib_engine = TALibTechnicalAnalysisEngine()

