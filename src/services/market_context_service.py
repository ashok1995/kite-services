"""
Market Context Service - Market Level Intelligence Only
========================================================

Service that provides market-level context and intelligence.
NO stock-level recommendations - only market environment analysis.
"""

import logging
import time
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional

from core.kite_client import KiteClient
from core.logging_config import get_logger
from models.market_context_data_models import (
    CurrencyData,
    IndianMarketData,
    InstitutionalData,
    MarketContextData,
    MarketContextRequest,
    MarketContextResponse,
    MarketRegime,
    QuickMarketContextResponse,
    SectorData,
    TradingSession,
    VolatilityData,
    VolatilityLevel,
)
from services.market_breadth_service import MarketBreadthService


class MarketContextService:
    """Market context service - provides market-level intelligence only."""

    def __init__(
        self,
        kite_client: KiteClient,
        logger: Optional[logging.Logger] = None,
    ):
        self.kite_client = kite_client
        self.logger = logger or get_logger(__name__)

        # Initialize market breadth service for advance/decline data
        self.breadth_service = MarketBreadthService(kite_client, logger)

        self.logger.info(
            "MarketContextService initialized",
            extra={
                "service": "market_context_service",
                "scope": "market_level_only",
                "breadth_service": "enabled",
            },
        )

    async def cleanup(self):
        """Cleanup market context service resources."""
        await self.breadth_service.cleanup()
        self.logger.info("MarketContextService cleanup complete")

    # ========================================================================
    # PUBLIC API methods (used by api/analysis.py)
    # ========================================================================

    async def get_global_market_data(self) -> List[Dict]:
        """Get global market data as list of dicts for the analysis API."""
        try:
            data = await self._get_global_market_data("api")
            results = []
            for region_markets in [data.us_markets, data.european_markets, data.asian_markets]:
                for symbol, info in (region_markets or {}).items():
                    results.append(
                        {
                            "market": symbol,
                            "index": symbol,
                            "last_price": info.get("value"),
                            "change": None,
                            "change_percent": info.get("change_percent"),
                            "timestamp": data.timestamp.isoformat() if data.timestamp else None,
                        }
                    )
            return results
        except Exception as e:
            self.logger.warning(f"get_global_market_data failed: {e}")
            return []

    async def get_indian_market_data(self) -> List[Dict]:
        """Get Indian market data as list of dicts for the analysis API."""
        try:
            data = await self._get_indian_market_data("api")
            results = []
            for symbol, info in (data.indices or {}).items():
                results.append(
                    {
                        "market": "India",
                        "index": symbol,
                        "last_price": info.get("value"),
                        "change": None,
                        "change_percent": info.get("change_percent"),
                        "timestamp": data.timestamp.isoformat() if data.timestamp else None,
                    }
                )
            return results
        except Exception as e:
            self.logger.warning(f"get_indian_market_data failed: {e}")
            return []

    async def get_market_breadth(self) -> Optional[Dict]:
        """Get market breadth data for the analysis API."""
        try:
            # Get breadth from the breadth service
            breadth_data = await self.breadth_service.get_market_breadth()

            return {
                "advances": breadth_data.get("advancing_stocks", 0),
                "declines": breadth_data.get("declining_stocks", 0),
                "unchanged": breadth_data.get("unchanged_stocks", 0),
                "advance_decline_ratio": float(breadth_data.get("advance_decline_ratio", 1.0)),
                "total_stocks": breadth_data.get("total_stocks", 0),
                "data_source": breadth_data.get("data_source", "nifty50_constituents"),
                "timestamp": (
                    breadth_data.get("timestamp", datetime.now()).isoformat()
                    if isinstance(breadth_data.get("timestamp"), datetime)
                    else str(breadth_data.get("timestamp", datetime.now()))
                ),
            }
        except Exception as e:
            self.logger.warning(f"get_market_breadth failed: {e}")
            return None

    async def get_market_sentiment(self) -> Optional[Dict]:
        """Get market sentiment data for the analysis API."""
        try:
            vol = await self._get_volatility_data("api")
            indian = await self._get_indian_market_data("api")
            regime = indian.market_regime.value if indian.market_regime else "sideways"
            if "bullish" in regime or "up" in regime:
                sentiment = "bullish"
            elif "bearish" in regime or "down" in regime:
                sentiment = "bearish"
            else:
                sentiment = "neutral"
            return {
                "overall_sentiment": sentiment,
                "fear_greed_index": vol.fear_greed_index,
                "vix": float(vol.india_vix) if vol.india_vix else None,
                "put_call_ratio": float(vol.put_call_ratio) if vol.put_call_ratio else None,
                "advance_decline_ratio": (
                    float(indian.advance_decline_ratio) if indian.advance_decline_ratio else None
                ),
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            self.logger.warning(f"get_market_sentiment failed: {e}")
            return None

    async def get_technical_analysis(self, symbol: str) -> Optional[Dict]:
        """Get technical analysis for a symbol (placeholder)."""
        try:
            # This would require historical data — return basic info for now
            quotes = await self.kite_client.quote([symbol])
            if not quotes or symbol not in quotes:
                return None
            q = quotes[symbol]
            price = q.get("last_price", 0)
            return {
                "trend": "bullish" if q.get("net_change", 0) > 0 else "bearish",
                "support_levels": [round(price * 0.97, 2), round(price * 0.95, 2)],
                "resistance_levels": [round(price * 1.03, 2), round(price * 1.05, 2)],
                "moving_averages": {
                    "sma_20": round(price * 0.98, 2),
                    "sma_50": round(price * 0.95, 2),
                },
                "rsi": 55.0,
                "macd": {"signal": "bullish" if q.get("net_change", 0) > 0 else "bearish"},
                "bollinger_bands": {
                    "upper": round(price * 1.02, 2),
                    "lower": round(price * 0.98, 2),
                },
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            self.logger.warning(f"get_technical_analysis failed for {symbol}: {e}")
            return None

    async def get_market_context(
        self, request: MarketContextRequest, request_id: str
    ) -> MarketContextResponse:
        """Get comprehensive market context - market level only."""
        start_time = time.time()

        try:
            # Build market context components
            global_data = (
                await self._get_global_market_data(request_id)
                if request.include_global_data
                else None
            )
            indian_data = await self._get_indian_market_data(request_id)
            volatility_data = await self._get_volatility_data(request_id)
            sector_data = (
                await self._get_sector_data(request_id)
                if request.include_sector_data
                else self._create_empty_sector_data()
            )
            institutional_data = (
                await self._get_institutional_data(request_id)
                if request.include_institutional_data
                else self._create_empty_institutional_data()
            )
            currency_data = (
                await self._get_currency_data(request_id)
                if request.include_currency_data
                else self._create_empty_currency_data()
            )

            # Analyze overall market context
            overall_regime = self._determine_overall_regime(
                global_data, indian_data, volatility_data
            )
            market_strength = self._calculate_market_strength(indian_data, sector_data)
            global_influence = self._calculate_global_influence(global_data, indian_data)

            # Generate market insights
            key_observations = self._generate_market_observations(
                global_data, indian_data, volatility_data, sector_data
            )
            market_themes = self._identify_market_themes(
                global_data, indian_data, sector_data, institutional_data
            )
            risk_factors = self._identify_risk_factors(global_data, volatility_data, currency_data)

            # Build market context
            market_context = MarketContextData(
                timestamp=datetime.now(),
                request_id=request_id,
                global_data=global_data,
                indian_data=indian_data,
                volatility_data=volatility_data,
                sector_data=sector_data,
                institutional_data=institutional_data,
                currency_data=currency_data,
                overall_market_regime=overall_regime,
                market_strength=market_strength,
                global_influence=global_influence,
                trading_session=self._get_current_trading_session(),
                session_bias=self._determine_session_bias(indian_data),
                liquidity_conditions=self._assess_liquidity_conditions(),
                key_observations=key_observations,
                market_themes=market_themes,
                risk_factors=risk_factors,
                data_quality_score=Decimal("85.0"),
                processing_time_ms=int((time.time() - start_time) * 1000),
            )

            # Generate market summary
            market_summary = self._generate_market_summary(market_context)

            response = MarketContextResponse(
                timestamp=datetime.now(),
                request_id=request_id,
                market_context=market_context,
                market_summary=market_summary,
                processing_time_ms=int((time.time() - start_time) * 1000),
                data_sources=["kite_connect"],
            )

            return response

        except Exception as e:
            self.logger.error(f"Market context request failed: {e}")
            raise

    async def get_quick_market_context(self, request_id: str) -> QuickMarketContextResponse:
        """Get quick market context for immediate understanding."""
        start_time = time.time()

        try:
            # Get essential data only
            indian_data = await self._get_indian_market_data(request_id)
            volatility_data = await self._get_volatility_data(request_id)
            sector_data = await self._get_sector_data(request_id)
            global_data = await self._get_global_market_data(request_id)

            # Calculate key metrics
            global_influence = self._calculate_global_influence(global_data, indian_data)

            response = QuickMarketContextResponse(
                timestamp=datetime.now(),
                market_regime=indian_data.market_regime.value,
                global_sentiment=global_data.global_sentiment.value,
                volatility_level=volatility_data.volatility_level.value,
                india_vix=volatility_data.india_vix,
                advance_decline_ratio=indian_data.advance_decline_ratio,
                global_influence=global_influence,
                trading_session=self._get_current_trading_session().value,
                session_bias=self._determine_session_bias(indian_data),
                leading_sectors=sector_data.leading_sectors[:3],
                processing_time_ms=int((time.time() - start_time) * 1000),
            )

            return response

        except Exception as e:
            self.logger.error(f"Quick market context failed: {e}")
            raise

    # Helper methods (simplified for brevity)

    async def _get_global_market_data(self, request_id: str):
        """Global market data not supported - use separate global context service."""
        self.logger.debug("Global market data not provided by this service")
        return None

    async def _get_indian_market_data(self, request_id: str) -> IndianMarketData:
        """Get Indian market data from Kite Connect."""
        try:
            # Fetch Indian indices via Kite Connect quote API
            indian_symbols = ["NSE:NIFTY 50", "NSE:NIFTY BANK"]
            quotes = await self.kite_client.quote(indian_symbols)

            indices = {}
            nifty_change_pct = Decimal("0")

            for symbol, data in quotes.items():
                net_change = data.get("net_change", 0)
                close_price = data.get("ohlc", {}).get("close", 0)
                change_pct = round((net_change / close_price) * 100, 2) if close_price else 0
                indices[symbol] = {"value": data.get("last_price", 0), "change_percent": change_pct}
                if "NIFTY 50" in symbol:
                    nifty_change_pct = Decimal(str(change_pct))

            # If Kite returns no indices, log warning
            if not indices:
                self.logger.warning("No indices data from Kite Connect")

            # Determine market regime from Nifty change
            if nifty_change_pct > Decimal("1"):
                regime = MarketRegime.BULLISH
            elif nifty_change_pct > Decimal("0.3"):
                regime = MarketRegime.TRENDING_UP
            elif nifty_change_pct > Decimal("-0.3"):
                regime = MarketRegime.SIDEWAYS
            elif nifty_change_pct > Decimal("-1"):
                regime = MarketRegime.TRENDING_DOWN
            else:
                regime = MarketRegime.BEARISH

            # Get market breadth from Nifty 50 constituents
            breadth_data = await self.breadth_service.get_market_breadth()

            # Extract breadth metrics
            advances = breadth_data.get("advancing_stocks", 0)
            declines = breadth_data.get("declining_stocks", 0)
            unchanged = breadth_data.get("unchanged_stocks", 0)
            ad_ratio = breadth_data.get("advance_decline_ratio", Decimal("1.0"))

            return IndianMarketData(
                timestamp=datetime.now(),
                indices=indices,
                market_regime=regime,
                volatility_level=VolatilityLevel.NORMAL,
                advances=advances,
                declines=declines,
                unchanged=unchanged,
                advance_decline_ratio=ad_ratio,
                new_highs=0,
                new_lows=0,
                total_volume=None,
                volume_trend="stable",
            )
        except Exception as e:
            self.logger.warning(f"Failed to get Indian market data: {e}")
            return IndianMarketData(
                timestamp=datetime.now(),
                indices={},
                market_regime=MarketRegime.SIDEWAYS,
                volatility_level=VolatilityLevel.NORMAL,
                advances=0,
                declines=0,
                unchanged=0,
                advance_decline_ratio=Decimal("1.0"),
                new_highs=0,
                new_lows=0,
                volume_trend="unknown",
            )

    async def _get_volatility_data(self, request_id: str) -> VolatilityData:
        """Get volatility data - India VIX from Kite Connect."""
        try:
            # Get India VIX from Kite Connect
            quotes = await self.kite_client.quote(["NSE:INDIA VIX"])
            vix_data = quotes.get("NSE:INDIA VIX", {})
            vix_value = Decimal(str(vix_data.get("last_price", 18)))

            # Classify volatility level
            if vix_value < Decimal("12"):
                vol_level = VolatilityLevel.VERY_LOW
            elif vix_value < Decimal("16"):
                vol_level = VolatilityLevel.LOW
            elif vix_value < Decimal("20"):
                vol_level = VolatilityLevel.NORMAL
            elif vix_value < Decimal("25"):
                vol_level = VolatilityLevel.ELEVATED
            elif vix_value < Decimal("30"):
                vol_level = VolatilityLevel.HIGH
            else:
                vol_level = VolatilityLevel.VERY_HIGH

            # Calculate fear-greed from VIX (inverted)
            fear_greed = max(0, min(100, int(100 - float(vix_value) * 2.5)))

            return VolatilityData(
                timestamp=datetime.now(),
                india_vix=vix_value,
                vix_change=Decimal("0"),
                vix_trend="stable",
                volatility_level=vol_level,
                fear_greed_index=fear_greed,
                put_call_ratio=None,
                expected_daily_range=vix_value / Decimal("16"),
            )
        except Exception as e:
            self.logger.warning(f"Failed to get volatility data: {e}")
            return VolatilityData(
                timestamp=datetime.now(),
                india_vix=Decimal("18"),
                vix_change=Decimal("0"),
                vix_trend="unknown",
                volatility_level=VolatilityLevel.NORMAL,
                fear_greed_index=50,
                put_call_ratio=None,
                expected_daily_range=Decimal("1.5"),
            )

    async def _get_sector_data(self, request_id: str) -> SectorData:
        """Get sector data from Kite Connect (Indian sectors)."""
        try:
            # Primary: Use Kite Connect for Indian Nifty sector indices
            sector_performance = await self.kite_client.get_sector_performance()

            # If no sector data, log warning
            if not sector_performance:
                self.logger.warning("No sector performance data available from Kite")

            sorted_sectors = sorted(sector_performance.items(), key=lambda x: x[1], reverse=True)

            return SectorData(
                timestamp=datetime.now(),
                sector_performance={k: Decimal(str(v)) for k, v in sector_performance.items()},
                leading_sectors=[s[0] for s in sorted_sectors[:3] if s[1] > 0],
                lagging_sectors=[s[0] for s in sorted_sectors[-3:] if s[1] < 0],
                rotation_stage="mid_cycle",
                sector_breadth={},
            )
        except Exception as e:
            self.logger.warning(f"Failed to get sector data: {e}")
            return self._create_empty_sector_data()

    async def _get_institutional_data(self, request_id: str) -> InstitutionalData:
        """Get institutional data.

        Note: FII/DII real-time flow data requires NSDL/BSE scraping or paid APIs.
        Returns empty defaults when real data is not available.
        """
        self.logger.debug(
            "Institutional flow data requires external data source - returning defaults"
        )
        return InstitutionalData(
            timestamp=datetime.now(),
            fii_flow=None,
            dii_flow=None,
            net_institutional_flow=None,
            fii_trend="unavailable",
            dii_trend="unavailable",
            institutional_sentiment="unavailable",
        )

    async def _get_currency_data(self, request_id: str) -> CurrencyData:
        """Currency and commodity data not supported - use separate service."""
        self.logger.debug("Currency/commodity not provided by this service")
        return CurrencyData(
            timestamp=datetime.now(), currency_trend="unknown", commodity_impact="unknown"
        )

    # Analysis methods

    def _determine_overall_regime(self, global_data, indian_data, volatility_data) -> MarketRegime:
        """Determine overall market regime."""
        if volatility_data.volatility_level in [VolatilityLevel.HIGH, VolatilityLevel.VERY_HIGH]:
            return MarketRegime.VOLATILE
        return indian_data.market_regime

    def _calculate_market_strength(self, indian_data, sector_data) -> Decimal:
        """Calculate market strength score."""
        strength = Decimal("50")
        if indian_data.advance_decline_ratio > Decimal("1.5"):
            strength += Decimal("20")
        elif indian_data.advance_decline_ratio < Decimal("0.8"):
            strength -= Decimal("15")
        return max(Decimal("0"), min(Decimal("100"), strength))

    def _calculate_global_influence(self, global_data, indian_data) -> Decimal:
        """Calculate global influence score based on overnight changes."""
        try:
            if not global_data.overnight_changes:
                return Decimal("50")

            # Weight US markets more heavily
            us_change = abs(float(global_data.overnight_changes.get("us", 0)))
            eu_change = abs(float(global_data.overnight_changes.get("eu", 0)))
            asia_change = abs(float(global_data.overnight_changes.get("asia", 0)))

            # Larger global moves = higher influence on Indian markets
            weighted_change = us_change * 0.5 + eu_change * 0.2 + asia_change * 0.3
            influence = min(Decimal("100"), Decimal(str(round(50 + weighted_change * 15, 1))))
            return max(Decimal("0"), influence)
        except Exception:
            return Decimal("50")

    def _get_current_trading_session(self) -> TradingSession:
        """Get current trading session."""
        hour = datetime.now().hour
        if 9 <= hour < 10:
            return TradingSession.OPENING
        elif 10 <= hour < 14:
            return TradingSession.MORNING
        elif 14 <= hour < 15:
            return TradingSession.AFTERNOON
        else:
            return TradingSession.POST_MARKET

    def _determine_session_bias(self, indian_data) -> str:
        """Determine session bias."""
        if indian_data.advance_decline_ratio > Decimal("1.3"):
            return "bullish"
        elif indian_data.advance_decline_ratio < Decimal("0.7"):
            return "bearish"
        return "neutral"

    def _assess_liquidity_conditions(self) -> str:
        """Assess liquidity conditions."""
        return "normal"

    def _generate_market_observations(
        self, global_data, indian_data, volatility_data, sector_data
    ) -> List[str]:
        """Generate market observations."""
        observations = []
        observations.append(f"Market in {indian_data.market_regime.value} regime")
        if indian_data.advance_decline_ratio > Decimal("1.5"):
            observations.append("Strong market breadth")
        if sector_data.leading_sectors:
            observations.append(f"Sector leadership: {', '.join(sector_data.leading_sectors[:2])}")
        return observations

    def _identify_market_themes(
        self, global_data, indian_data, sector_data, institutional_data
    ) -> List[str]:
        """Identify market themes."""
        themes = []
        if institutional_data.fii_flow and institutional_data.fii_flow > 1000:
            themes.append("Strong FII buying")
        if sector_data.leading_sectors:
            themes.append(f"{sector_data.leading_sectors[0]} outperformance")
        return themes

    def _identify_risk_factors(self, global_data, volatility_data, currency_data) -> List[str]:
        """Identify risk factors."""
        risks = []
        if volatility_data.volatility_level in [VolatilityLevel.HIGH, VolatilityLevel.VERY_HIGH]:
            risks.append("Elevated volatility")
        if currency_data.usd_inr_change and abs(currency_data.usd_inr_change) > 0.5:
            risks.append("Currency volatility")
        return risks

    def _generate_market_summary(self, context) -> str:
        """Generate market summary."""
        regime = context.overall_market_regime.value
        vol = context.volatility_data.volatility_level.value
        return f"Market in {regime} regime with {vol} volatility."

    # Empty data creators

    # _create_empty_global_data removed - global data not supported

    def _create_empty_sector_data(self) -> SectorData:
        """Create empty sector data."""
        return SectorData(timestamp=datetime.now(), rotation_stage="unknown")

    def _create_empty_institutional_data(self) -> InstitutionalData:
        """Create empty institutional data."""
        return InstitutionalData(
            timestamp=datetime.now(),
            fii_trend="neutral",
            dii_trend="neutral",
            institutional_sentiment="neutral",
        )

    def _create_empty_currency_data(self) -> CurrencyData:
        """Create empty currency data."""
        return CurrencyData(
            timestamp=datetime.now(), currency_trend="stable", commodity_impact="neutral"
        )
