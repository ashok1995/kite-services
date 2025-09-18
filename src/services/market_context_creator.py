#!/usr/bin/env python3
"""
Comprehensive Seed Service Integration Examples
==============================================

This module demonstrates how to integrate the optimized data model with real market data
to send high-quality contextual information to the Seed service for stock recommendations.
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import asdict

# Import our optimized data models
from optimized_seed_data_model import (
    OptimizedSeedServiceRequest,
    MarketContext,
    SectorContext, 
    TechnicalContext,
    UserPreferences,
    RiskContext,
    MarketRegime,
    VolatilityRegime,
    TrendStrength,
    SectorMomentum,
    create_seed_service_payload
)

# Import our data collection services
from multi_timeframe_contextual_service import MultiTimeframeContextualService
from progressive_kite_contextual_service import ProgressiveKiteContextualService

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/seed_service_integration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SeedServiceIntegration:
    """Comprehensive integration with Seed service using optimized data model"""
    
    def __init__(self):
        self.multi_timeframe_service = MultiTimeframeContextualService()
        self.progressive_service = ProgressiveKiteContextualService()
        
    def collect_real_market_context(self) -> MarketContext:
        """Collect real market context from multiple sources"""
        logger.info("Collecting real market context...")
        
        # Get progressive contextual features
        progressive_result = self.progressive_service.run_single_analysis()
        
        if not progressive_result['success']:
            logger.warning("Failed to get progressive context, using defaults")
            return self._create_default_market_context()
        
        features = progressive_result['contextual_features']
        
        # Determine market regime
        market_regime = self._determine_market_regime(features)
        volatility_regime = self._determine_volatility_regime(features)
        
        # Determine trend strength
        trend_strength = self._determine_trend_strength(features)
        
        return MarketContext(
            market_regime=market_regime,
            volatility_regime=volatility_regime,
            primary_trend_direction=features.market_trend_direction or "sideways",
            trend_strength=trend_strength,
            trend_acceleration=features.trend_acceleration or 0.0,
            advancing_stocks_ratio=self._estimate_advancing_stocks(),
            new_highs_lows_ratio=self._estimate_new_highs_lows(),
            vix_level=self._get_vix_level(),
            fear_greed_index=features.fear_greed_momentum,
            volume_trend=features.volume_trend or "stable",
            institutional_flow=self._estimate_institutional_flow()
        )
    
    def collect_real_sector_context(self) -> SectorContext:
        """Collect real sector context from market data"""
        logger.info("Collecting real sector context...")
        
        # Get progressive contextual features
        progressive_result = self.progressive_service.run_single_analysis()
        
        if not progressive_result['success']:
            logger.warning("Failed to get progressive context, using defaults")
            return self._create_default_sector_context()
        
        features = progressive_result['contextual_features']
        
        # Analyze sector momentum
        sector_momentum = {}
        for sector, momentum in features.sectoral_momentum.items():
            if momentum is not None:
                if momentum > 1.5:
                    sector_momentum[sector] = SectorMomentum.LEADING
                elif momentum > 0.5:
                    sector_momentum[sector] = SectorMomentum.STRONG
                elif momentum > -0.5:
                    sector_momentum[sector] = SectorMomentum.AVERAGE
                elif momentum > -1.5:
                    sector_momentum[sector] = SectorMomentum.WEAK
                else:
                    sector_momentum[sector] = SectorMomentum.LAGGING
            else:
                sector_momentum[sector] = SectorMomentum.AVERAGE
        
        # Determine sector rotation stage
        rotation_stage = self._determine_sector_rotation_stage(features)
        
        # Identify leading and lagging sectors
        leading_sectors = [sector for sector, momentum in sector_momentum.items() 
                          if momentum in [SectorMomentum.LEADING, SectorMomentum.STRONG]]
        lagging_sectors = [sector for sector, momentum in sector_momentum.items() 
                          if momentum in [SectorMomentum.WEAK, SectorMomentum.LAGGING]]
        
        return SectorContext(
            sector_momentum=sector_momentum,
            sector_rotation_stage=rotation_stage,
            leading_sectors=leading_sectors,
            lagging_sectors=lagging_sectors,
            sector_correlation_level=self._determine_sector_correlation(features),
            sector_diversification_opportunity=len(leading_sectors) > 2
        )
    
    def collect_real_technical_context(self) -> TechnicalContext:
        """Collect real technical context from multi-timeframe analysis"""
        logger.info("Collecting real technical context...")
        
        # Get multi-timeframe analysis
        multi_timeframe_result = self.multi_timeframe_service.run_multi_timeframe_analysis()
        
        if not multi_timeframe_result['success']:
            logger.warning("Failed to get multi-timeframe context, using defaults")
            return self._create_default_technical_context()
        
        features = multi_timeframe_result['features']
        
        # Analyze timeframe alignment
        timeframe_alignment = {}
        for timeframe_name in ['1min', '5min', '15min', '30min', '1hour', 'daily']:
            timeframe_attr = getattr(features, f'timeframe_{timeframe_name}', None)
            if timeframe_attr and timeframe_attr.trend_direction:
                timeframe_alignment[timeframe_name] = timeframe_attr.trend_direction
            else:
                timeframe_alignment[timeframe_name] = "sideways"
        
        # Get support/resistance levels from daily timeframe
        daily_features = features.timeframe_daily
        support_levels = []
        resistance_levels = []
        
        if daily_features:
            if daily_features.support_level:
                support_levels.append(daily_features.support_level)
            if daily_features.resistance_level:
                resistance_levels.append(daily_features.resistance_level)
        
        # Calculate breakout probability
        breakout_probability = self._calculate_breakout_probability(features)
        
        # Calculate momentum scores
        momentum_score = self._calculate_momentum_score(features)
        momentum_acceleration = self._calculate_momentum_acceleration(features)
        
        return TechnicalContext(
            timeframe_alignment=timeframe_alignment,
            dominant_timeframe=features.dominant_timeframe or "daily",
            key_support_levels=support_levels,
            key_resistance_levels=resistance_levels,
            breakout_probability=breakout_probability,
            momentum_score=momentum_score,
            momentum_acceleration=momentum_acceleration,
            volume_confirmation=self._determine_volume_confirmation(features),
            volume_surge_detected=self._detect_volume_surge(features)
        )
    
    def create_user_preferences(self, 
                              strategy: str = "momentum",
                              risk_tolerance: str = "moderate",
                              max_positions: int = 10,
                              preferred_sectors: List[str] = None,
                              excluded_sectors: List[str] = None) -> UserPreferences:
        """Create user preferences with customizable parameters"""
        
        if preferred_sectors is None:
            preferred_sectors = ["NIFTY BANK", "NIFTY IT", "NIFTY AUTO"]
        
        if excluded_sectors is None:
            excluded_sectors = ["NIFTY ENERGY", "NIFTY REALTY"]
        
        return UserPreferences(
            primary_strategy=strategy,
            risk_tolerance=risk_tolerance,
            max_portfolio_risk=0.15 if risk_tolerance == "moderate" else 0.10 if risk_tolerance == "conservative" else 0.20,
            investment_horizon="medium_term",
            max_positions=max_positions,
            preferred_sectors=preferred_sectors,
            excluded_sectors=excluded_sectors,
            max_position_size=0.12 if risk_tolerance == "moderate" else 0.08 if risk_tolerance == "conservative" else 0.15,
            min_position_size=0.02
        )
    
    def create_risk_context(self, market_context: MarketContext) -> RiskContext:
        """Create risk context based on market conditions"""
        
        # Determine market risk level
        if market_context.market_regime == MarketRegime.VOLATILE:
            market_risk_level = "high"
        elif market_context.market_regime == MarketRegime.TRENDING_BEAR:
            market_risk_level = "high"
        elif market_context.market_regime == MarketRegime.RANGING:
            market_risk_level = "medium"
        else:
            market_risk_level = "low"
        
        # Determine correlation risk
        if market_context.volatility_regime == VolatilityRegime.HIGH:
            correlation_risk = "high"
        elif market_context.volatility_regime == VolatilityRegime.MEDIUM:
            correlation_risk = "medium"
        else:
            correlation_risk = "low"
        
        # Calculate position sizing
        if market_context.volatility_regime == VolatilityRegime.HIGH:
            recommended_position_size = 0.05
            max_position_size = 0.08
        elif market_context.volatility_regime == VolatilityRegime.MEDIUM:
            recommended_position_size = 0.08
            max_position_size = 0.12
        else:
            recommended_position_size = 0.12
            max_position_size = 0.15
        
        return RiskContext(
            market_risk_level=market_risk_level,
            correlation_risk=correlation_risk,
            recommended_position_size=recommended_position_size,
            max_position_size=max_position_size,
            var_95=0.05 if market_risk_level == "high" else 0.03,
            max_drawdown_probability=0.20 if market_risk_level == "high" else 0.15
        )
    
    def create_optimized_seed_request(self, 
                                   strategy: str = "momentum",
                                   risk_tolerance: str = "moderate",
                                   max_positions: int = 10,
                                   preferred_sectors: List[str] = None,
                                   excluded_sectors: List[str] = None) -> OptimizedSeedServiceRequest:
        """Create optimized Seed service request with real data"""
        
        logger.info("Creating optimized Seed service request with real data...")
        
        # Collect real market data
        market_context = self.collect_real_market_context()
        sector_context = self.collect_real_sector_context()
        technical_context = self.collect_real_technical_context()
        
        # Create user preferences
        user_preferences = self.create_user_preferences(
            strategy=strategy,
            risk_tolerance=risk_tolerance,
            max_positions=max_positions,
            preferred_sectors=preferred_sectors,
            excluded_sectors=excluded_sectors
        )
        
        # Create risk context
        risk_context = self.create_risk_context(market_context)
        
        # Create optimized request
        request = OptimizedSeedServiceRequest(
            request_id=f"real_data_request_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            timestamp=datetime.now().isoformat(),
            market_context=market_context,
            sector_context=sector_context,
            technical_context=technical_context,
            user_preferences=user_preferences,
            risk_context=risk_context,
            market_sentiment={
                "overall_sentiment": "bullish" if market_context.primary_trend_direction == "bullish" else "bearish",
                "retail_sentiment": "neutral",
                "institutional_sentiment": "bullish" if market_context.institutional_flow == "buying" else "neutral",
                "news_sentiment": "positive"
            },
            macro_indicators={
                "interest_rates": "stable",
                "inflation_trend": "moderate",
                "currency_trend": "stable",
                "commodity_trend": "mixed"
            },
            time_context={
                "market_session": "regular_hours",
                "time_of_day": "afternoon",
                "day_of_week": datetime.now().strftime('%A').lower(),
                "month_end_effect": False
            }
        )
        
        logger.info("✅ Optimized Seed service request created successfully!")
        return request
    
    def send_to_seed_service(self, request: OptimizedSeedServiceRequest) -> Dict[str, Any]:
        """Send optimized request to Seed service"""
        
        logger.info("Sending optimized request to Seed service...")
        
        # Create payload
        payload = create_seed_service_payload(request)
        
        # Save request for debugging
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        with open(f'logs/seed_service_request_{timestamp}.json', 'w') as f:
            json.dump(payload, f, indent=2)
        
        logger.info(f"Request saved to logs/seed_service_request_{timestamp}.json")
        
        # TODO: Implement actual API call to Seed service
        # For now, return mock response
        mock_response = {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "request_id": request.request_id,
            "recommendations": [
                {
                    "symbol": "RELIANCE",
                    "name": "Reliance Industries Ltd",
                    "sector": "Energy",
                    "score": 85.5,
                    "recommendation": "BUY",
                    "target_price": 2850.0,
                    "stop_loss": 2650.0,
                    "position_size": 0.08,
                    "reasoning": "Strong momentum in energy sector with breakout potential"
                },
                {
                    "symbol": "TCS",
                    "name": "Tata Consultancy Services Ltd",
                    "sector": "IT",
                    "score": 82.3,
                    "recommendation": "BUY",
                    "target_price": 3850.0,
                    "stop_loss": 3650.0,
                    "position_size": 0.10,
                    "reasoning": "IT sector leading with strong technical setup"
                }
            ],
            "market_summary": {
                "overall_sentiment": "bullish",
                "sector_rotation": "mid_stage",
                "risk_level": "medium",
                "recommended_portfolio_size": 0.75
            }
        }
        
        logger.info("✅ Mock response received from Seed service")
        return mock_response
    
    # Helper methods for data analysis
    def _determine_market_regime(self, features) -> MarketRegime:
        """Determine market regime from features"""
        if features.market_trend_direction == "strengthening_bull":
            return MarketRegime.TRENDING_BULL
        elif features.market_trend_direction == "strengthening_bear":
            return MarketRegime.TRENDING_BEAR
        elif features.volatility_trend == "spiking":
            return MarketRegime.VOLATILE
        else:
            return MarketRegime.RANGING
    
    def _determine_volatility_regime(self, features) -> VolatilityRegime:
        """Determine volatility regime from features"""
        if features.volatility_momentum and features.volatility_momentum > 0.3:
            return VolatilityRegime.HIGH
        elif features.volatility_momentum and features.volatility_momentum < -0.1:
            return VolatilityRegime.LOW
        else:
            return VolatilityRegime.MEDIUM
    
    def _determine_trend_strength(self, features) -> TrendStrength:
        """Determine trend strength from features"""
        if features.trend_acceleration and features.trend_acceleration > 0.1:
            return TrendStrength.STRONG
        elif features.trend_acceleration and features.trend_acceleration > 0.05:
            return TrendStrength.MODERATE
        else:
            return TrendStrength.WEAK
    
    def _estimate_advancing_stocks(self) -> float:
        """Estimate advancing stocks ratio"""
        return 0.65  # Mock value - would be calculated from market data
    
    def _estimate_new_highs_lows(self) -> float:
        """Estimate new highs/lows ratio"""
        return 1.2  # Mock value - would be calculated from market data
    
    def _get_vix_level(self) -> float:
        """Get VIX level"""
        return 18.5  # Mock value - would be fetched from data
    
    def _estimate_institutional_flow(self) -> str:
        """Estimate institutional flow"""
        return "buying"  # Mock value - would be calculated from volume data
    
    def _determine_sector_rotation_stage(self, features) -> str:
        """Determine sector rotation stage"""
        if features.rotation_acceleration and features.rotation_acceleration > 1.0:
            return "early"
        elif features.rotation_acceleration and features.rotation_acceleration > 0.5:
            return "mid"
        else:
            return "late"
    
    def _determine_sector_correlation(self, features) -> str:
        """Determine sector correlation level"""
        if features.sector_correlation_trend == "increasing":
            return "high"
        elif features.sector_correlation_trend == "decreasing":
            return "low"
        else:
            return "medium"
    
    def _calculate_breakout_probability(self, features) -> float:
        """Calculate breakout probability"""
        return 0.65  # Mock value - would be calculated from technical analysis
    
    def _calculate_momentum_score(self, features) -> float:
        """Calculate momentum score"""
        return 0.3  # Mock value - would be calculated from price data
    
    def _calculate_momentum_acceleration(self, features) -> float:
        """Calculate momentum acceleration"""
        return 0.1  # Mock value - would be calculated from price data
    
    def _determine_volume_confirmation(self, features) -> str:
        """Determine volume confirmation"""
        return "bullish"  # Mock value - would be calculated from volume data
    
    def _detect_volume_surge(self, features) -> bool:
        """Detect volume surge"""
        return True  # Mock value - would be calculated from volume data
    
    def _create_default_market_context(self) -> MarketContext:
        """Create default market context"""
        return MarketContext(
            market_regime=MarketRegime.RANGING,
            volatility_regime=VolatilityRegime.MEDIUM,
            primary_trend_direction="sideways",
            trend_strength=TrendStrength.WEAK,
            trend_acceleration=0.0
        )
    
    def _create_default_sector_context(self) -> SectorContext:
        """Create default sector context"""
        return SectorContext(
            sector_momentum={},
            sector_rotation_stage="mid",
            leading_sectors=[],
            lagging_sectors=[],
            sector_correlation_level="medium",
            sector_diversification_opportunity=False
        )
    
    def _create_default_technical_context(self) -> TechnicalContext:
        """Create default technical context"""
        return TechnicalContext(
            timeframe_alignment={},
            dominant_timeframe="daily",
            key_support_levels=[],
            key_resistance_levels=[],
            breakout_probability=0.5,
            momentum_score=0.0,
            momentum_acceleration=0.0,
            volume_confirmation="neutral",
            volume_surge_detected=False
        )

def demonstrate_seed_service_integration():
    """Demonstrate comprehensive Seed service integration"""
    
    print("=" * 80)
    print("COMPREHENSIVE SEED SERVICE INTEGRATION DEMONSTRATION")
    print("=" * 80)
    
    # Initialize integration service
    integration = SeedServiceIntegration()
    
    # Create optimized request with real data
    print("\n📊 Creating optimized Seed service request with real data...")
    request = integration.create_optimized_seed_request(
        strategy="momentum",
        risk_tolerance="moderate",
        max_positions=10,
        preferred_sectors=["NIFTY BANK", "NIFTY IT", "NIFTY AUTO"],
        excluded_sectors=["NIFTY ENERGY", "NIFTY REALTY"]
    )
    
    print(f"✅ Request created: {request.request_id}")
    print(f"📅 Timestamp: {request.timestamp}")
    
    # Display key context information
    print(f"\n🎯 MARKET CONTEXT:")
    print(f"  • Market Regime: {request.market_context.market_regime.value}")
    print(f"  • Volatility Regime: {request.market_context.volatility_regime.value}")
    print(f"  • Primary Trend: {request.market_context.primary_trend_direction}")
    print(f"  • Trend Strength: {request.market_context.trend_strength.value}")
    print(f"  • VIX Level: {request.market_context.vix_level}")
    
    print(f"\n🏭 SECTOR CONTEXT:")
    print(f"  • Leading Sectors: {', '.join(request.sector_context.leading_sectors)}")
    print(f"  • Lagging Sectors: {', '.join(request.sector_context.lagging_sectors)}")
    print(f"  • Rotation Stage: {request.sector_context.sector_rotation_stage}")
    print(f"  • Correlation Level: {request.sector_context.sector_correlation_level}")
    
    print(f"\n📈 TECHNICAL CONTEXT:")
    print(f"  • Dominant Timeframe: {request.technical_context.dominant_timeframe}")
    print(f"  • Breakout Probability: {request.technical_context.breakout_probability:.1%}")
    print(f"  • Momentum Score: {request.technical_context.momentum_score:.2f}")
    print(f"  • Volume Confirmation: {request.technical_context.volume_confirmation}")
    
    print(f"\n👤 USER PREFERENCES:")
    print(f"  • Primary Strategy: {request.user_preferences.primary_strategy}")
    print(f"  • Risk Tolerance: {request.user_preferences.risk_tolerance}")
    print(f"  • Max Positions: {request.user_preferences.max_positions}")
    print(f"  • Preferred Sectors: {', '.join(request.user_preferences.preferred_sectors)}")
    print(f"  • Excluded Sectors: {', '.join(request.user_preferences.excluded_sectors)}")
    
    print(f"\n⚠️ RISK CONTEXT:")
    print(f"  • Market Risk Level: {request.risk_context.market_risk_level}")
    print(f"  • Correlation Risk: {request.risk_context.correlation_risk}")
    print(f"  • Recommended Position Size: {request.risk_context.recommended_position_size:.1%}")
    print(f"  • Max Position Size: {request.risk_context.max_position_size:.1%}")
    
    # Send to Seed service
    print(f"\n🚀 Sending request to Seed service...")
    response = integration.send_to_seed_service(request)
    
    if response['success']:
        print(f"✅ Successfully received response from Seed service!")
        print(f"📊 Recommendations received: {len(response['recommendations'])}")
        
        print(f"\n📋 STOCK RECOMMENDATIONS:")
        for i, rec in enumerate(response['recommendations'], 1):
            print(f"  {i}. {rec['symbol']} ({rec['name']})")
            print(f"     • Sector: {rec['sector']}")
            print(f"     • Score: {rec['score']}/100")
            print(f"     • Recommendation: {rec['recommendation']}")
            print(f"     • Target Price: ₹{rec['target_price']}")
            print(f"     • Stop Loss: ₹{rec['stop_loss']}")
            print(f"     • Position Size: {rec['position_size']:.1%}")
            print(f"     • Reasoning: {rec['reasoning']}")
            print()
        
        print(f"📊 MARKET SUMMARY:")
        summary = response['market_summary']
        print(f"  • Overall Sentiment: {summary['overall_sentiment']}")
        print(f"  • Sector Rotation: {summary['sector_rotation']}")
        print(f"  • Risk Level: {summary['risk_level']}")
        print(f"  • Recommended Portfolio Size: {summary['recommended_portfolio_size']:.1%}")
    
    else:
        print(f"❌ Failed to get response from Seed service")
    
    print("\n" + "=" * 80)
    print("This demonstrates how to send optimized contextual data")
    print("to the Seed service for high-quality stock recommendations!")
    print("=" * 80)

def main():
    """Main entry point"""
    demonstrate_seed_service_integration()

if __name__ == "__main__":
    main()
