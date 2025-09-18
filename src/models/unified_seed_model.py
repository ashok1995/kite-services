#!/usr/bin/env python3
"""
Unified Seed Service Data Model
===============================

This is the SINGLE, comprehensive data model for all Seed service communication.
It consolidates all previous models into one unified, well-structured model.

Features:
- Complete request/response models
- All contextual features
- User preferences
- Risk management
- Progressive features
- Bidirectional communication
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, asdict, field
from enum import Enum

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/unified_seed_model.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# =============================================================================
# ENUMS
# =============================================================================

class TradingStrategy(Enum):
    """Trading strategy types"""
    SCALPING = "scalping"           # Quick profits (0.5-1%)
    MOMENTUM = "momentum"          # Follow trends
    BREAKOUT = "breakout"          # Break resistance levels
    MEAN_REVERSION = "mean_reversion"  # Revert to mean
    SWING = "swing"                # Multi-day moves
    POSITION = "position"          # Long-term holds
    INDEX_FOLLOWING = "index_following"  # Follow sector indexes
    NEWS_MOMENTUM = "news_momentum"      # News-driven moves
    INTRADAY = "intraday"          # Same day trading
    LONG_TERM = "long_term"        # Long-term investment

class RiskLevel(Enum):
    """Risk tolerance levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"
    HIGH_RISK = "high_risk"

class InvestmentHorizon(Enum):
    """Investment horizon options"""
    INTRADAY = "intraday"           # Same day
    SHORT_TERM = "short_term"       # 1-7 days
    MEDIUM_TERM = "medium_term"     # 1-4 weeks
    LONG_TERM = "long_term"         # 1-3 months
    POSITION = "position"          # 3+ months
    SAME_DAY = "same_day"          # Same day trading
    WEEKS_TO_MONTHS = "weeks_to_months"  # Weeks to months

class MarketRegime(Enum):
    """Market regime types"""
    BULLISH = "bullish"
    BEARISH = "bearish"
    RANGING = "ranging"
    VOLATILE = "volatile"
    TRENDING_UP = "trending_up"
    TRENDING_DOWN = "trending_down"
    TRENDING_BULL = "trending_bull"
    TRENDING_BEAR = "trending_bear"
    BREAKOUT = "breakout"
    BREAKDOWN = "breakdown"

class VolatilityRegime(Enum):
    """Volatility regime types"""
    LOW = "low"           # < 15% annualized
    MEDIUM = "medium"     # 15-25% annualized
    HIGH = "high"         # > 25% annualized
    EXTREME = "extreme"   # > 40% annualized

class TrendStrength(Enum):
    """Trend strength classification"""
    VERY_WEAK = "very_weak"     # < 0.01
    WEAK = "weak"               # 0.01-0.03
    MODERATE = "moderate"       # 0.03-0.07
    STRONG = "strong"           # 0.07-0.15
    VERY_STRONG = "very_strong" # > 0.15

class SectorMomentum(Enum):
    """Sector momentum classification"""
    LEADING = "leading"         # Top 20% performers
    STRONG = "strong"          # Top 40% performers
    AVERAGE = "average"         # Middle 40% performers
    WEAK = "weak"              # Bottom 40% performers
    LAGGING = "lagging"        # Bottom 20% performers

class ProfitTarget(Enum):
    """Profit target types"""
    PERCENTAGE = "percentage"       # e.g., 1%, 2%, 5%
    ABSOLUTE = "absolute"          # e.g., ₹100, ₹500
    RISK_REWARD = "risk_reward"    # e.g., 2:1, 3:1

class DataSource(Enum):
    """Data source types"""
    SEED_SERVICE = "seed_service"
    KITE_API = "kite_api"
    YAHOO_FINANCE = "yahoo_finance"
    INTERNAL_CALCULATION = "internal_calculation"
    USER_INPUT = "user_input"

# =============================================================================
# CORE DATA CLASSES
# =============================================================================

@dataclass
class MarketContext:
    """Comprehensive market context information"""
    # Market Regime (Most Important)
    market_regime: MarketRegime
    volatility_regime: VolatilityRegime
    
    # Trend Analysis (Critical for stock selection)
    primary_trend_direction: str  # 'bullish', 'bearish', 'sideways'
    trend_strength: TrendStrength
    trend_acceleration: float  # -1 to 1
    
    # Market Breadth (Important for overall market health)
    advancing_stocks_ratio: Optional[float] = None  # % of stocks advancing
    new_highs_lows_ratio: Optional[float] = None   # new highs / new lows
    
    # Volatility Context (Risk management)
    vix_level: Optional[float] = None
    fear_greed_index: Optional[float] = None  # -1 to 1
    
    # Volume Analysis (Market participation)
    volume_trend: Optional[str] = None  # 'increasing', 'decreasing', 'stable'
    institutional_flow: Optional[str] = None  # 'buying', 'selling', 'neutral'
    
    # Market Sentiment
    market_sentiment: Optional[str] = None
    retail_sentiment: Optional[str] = None
    institutional_sentiment: Optional[str] = None
    
    # Macro Indicators
    macro_indicators: Optional[Dict[str, str]] = None

@dataclass
class SectorContext:
    """Sector rotation and momentum analysis"""
    # Sector Performance (Critical for sector selection)
    sector_momentum: Dict[str, SectorMomentum]  # sector -> momentum
    sector_rotation_stage: str  # 'early', 'mid', 'late', 'reversal'
    
    # Sector Leadership (Important for stock picking)
    leading_sectors: List[str]  # Top performing sectors
    lagging_sectors: List[str]  # Bottom performing sectors
    
    # Sector Correlation (Risk management)
    sector_correlation_level: str  # 'high', 'medium', 'low'
    sector_diversification_opportunity: bool
    
    # Sector Rotation Signals
    sector_rotation_signals: Optional[Dict[str, str]] = None

@dataclass
class TechnicalContext:
    """Technical analysis context for stock selection"""
    # Multi-timeframe Analysis (Critical)
    timeframe_alignment: Dict[str, str]  # timeframe -> trend direction
    dominant_timeframe: str  # Which timeframe is driving the trend
    
    # Support/Resistance (Important for entry/exit)
    key_support_levels: List[float]
    key_resistance_levels: List[float]
    breakout_probability: float  # 0-1
    
    # Momentum Analysis (Stock selection)
    momentum_score: float  # -1 to 1
    momentum_acceleration: float  # -1 to 1
    
    # Volume Analysis (Confirmation)
    volume_confirmation: str  # 'bullish', 'bearish', 'neutral'
    volume_surge_detected: bool
    
    # Technical Indicators
    technical_indicators: Optional[Dict[str, Any]] = None

@dataclass
class RiskContext:
    """Risk management context"""
    # Market Risk (Portfolio level)
    market_risk_level: str  # 'low', 'medium', 'high', 'extreme'
    correlation_risk: str  # 'low', 'medium', 'high'
    
    # Position Sizing (Individual stock level)
    recommended_position_size: float  # 0-1 (percentage of portfolio)
    max_position_size: float  # 0-1 (maximum allowed)
    
    # Risk Metrics
    var_95: Optional[float] = None  # Value at Risk 95%
    max_drawdown_probability: Optional[float] = None
    risk_appetite: Optional[str] = None
    volatility_forecast: Optional[str] = None

@dataclass
class UserPreferences:
    """User-specific preferences and constraints"""
    # 🔴 MANDATORY FIELDS (Required from UI)
    strategy: TradingStrategy
    risk_level: RiskLevel
    investment_horizon: InvestmentHorizon
    max_positions: int  # Maximum number of stocks to recommend (1-100)
    
    # 🟡 OPTIONAL STRATEGY PREFERENCES
    primary_strategy: Optional[str] = None  # 'momentum', 'mean_reversion', 'breakout', 'value', 'growth'
    secondary_strategy: Optional[str] = None
    risk_tolerance: Optional[str] = None  # 'conservative', 'moderate', 'aggressive'
    max_portfolio_risk: Optional[float] = None  # Maximum portfolio risk (0-1)
    
    # 🟡 OPTIONAL TRADING EXECUTION FIELDS
    profit_target_type: Optional[ProfitTarget] = None
    profit_target_value: Optional[float] = None  # e.g., 15.0 for 15% - Optional for trading execution
    max_loss_percent: Optional[float] = None
    stop_loss_percentage: Optional[float] = None  # Optional for trading execution
    take_profit_percentage: Optional[float] = None
    
    # Sector Preferences
    preferred_sectors: Optional[List[str]] = None
    excluded_sectors: Optional[List[str]] = None
    
    # Position Limits
    min_liquidity: Optional[float] = None  # Minimum daily volume
    max_position_size: Optional[float] = None  # 10% max per position
    min_position_size: Optional[float] = None  # 1% min per position
    max_position_size_percent: Optional[float] = None
    min_position_size_percent: Optional[float] = None
    
    # Execution Preferences
    execution_urgency: Optional[str] = None  # 'high', 'medium', 'low'
    time_constraints: Optional[Dict[str, Any]] = None

@dataclass
class ProgressiveContextualFeatures:
    """Progressive contextual features for enhanced analysis"""
    # Trend Analysis
    trend_analysis: Optional[Dict[str, Any]] = None
    trend_acceleration: Optional[float] = None
    trend_consistency: Optional[float] = None
    trend_duration_days: Optional[int] = None
    
    # Volatility Progression
    volatility_progression: Optional[Dict[str, Any]] = None
    volatility_trend: Optional[str] = None
    volatility_momentum: Optional[float] = None
    volatility_regime_change_probability: Optional[float] = None
    
    # Sectoral Progression
    sectoral_progression: Optional[Dict[str, Any]] = None
    sector_rotation_momentum: Optional[float] = None
    sector_leadership_stability: Optional[float] = None
    
    # Risk Progression
    risk_progression: Optional[Dict[str, Any]] = None
    risk_trend: Optional[str] = None
    risk_momentum: Optional[float] = None
    
    # Technical Progression
    technical_progression: Optional[Dict[str, Any]] = None
    technical_momentum: Optional[float] = None
    technical_consistency: Optional[float] = None
    
    # Macro Progression
    macro_progression: Optional[Dict[str, Any]] = None
    macro_trend: Optional[str] = None
    macro_momentum: Optional[float] = None
    
    # Time Progression
    time_progression: Optional[Dict[str, Any]] = None
    time_patterns: Optional[Dict[str, Any]] = None
    
    # Sentiment Progression
    sentiment_progression: Optional[Dict[str, Any]] = None
    sentiment_trend: Optional[str] = None
    sentiment_momentum: Optional[float] = None
    
    # Predictive Context
    predictive_context: Optional[Dict[str, Any]] = None
    prediction_confidence: Optional[float] = None

@dataclass
class ContextualFeatures:
    """Comprehensive contextual features"""
    market_context: MarketContext
    sector_context: SectorContext
    technical_context: TechnicalContext
    risk_context: RiskContext
    
    # Additional Context
    progressive_features: Optional[ProgressiveContextualFeatures] = None
    time_context: Optional[Dict[str, Any]] = None
    sentiment_context: Optional[Dict[str, Any]] = None
    macro_context: Optional[Dict[str, Any]] = None

# =============================================================================
# MAIN REQUEST/RESPONSE MODELS
# =============================================================================

@dataclass
class UnifiedSeedServiceRequest:
    """Unified Seed service request model - THE SINGLE MODEL TO USE"""
    # Request Metadata
    request_id: str
    timestamp: str
    
    # Core Context (Most Important for Stock Selection)
    market_context: MarketContext
    sector_context: SectorContext
    technical_context: TechnicalContext
    
    # User Preferences (Critical for Personalized Recommendations)
    user_preferences: UserPreferences
    
    # Risk Management (Important for Portfolio Construction)
    risk_context: RiskContext
    
    # Additional Features
    contextual_features: Optional[ContextualFeatures] = None
    progressive_features: Optional[ProgressiveContextualFeatures] = None
    
    # Request Configuration
    data_version: str = "13.0"
    request_source: str = "unified_recommendation_service"
    priority: str = "normal"
    response_format: str = "detailed"
    include_analysis: bool = True
    include_risk_metrics: bool = True
    include_technical_levels: bool = True
    
    # Additional Context
    market_sentiment: Optional[Dict[str, Any]] = None
    macro_indicators: Optional[Dict[str, Any]] = None
    time_context: Optional[Dict[str, Any]] = None

@dataclass
class TechnicalIndicator:
    """Single technical indicator from Seed service"""
    name: str
    value: float
    signal: str  # 'bullish', 'bearish', 'neutral'
    strength: float  # 0-1
    timeframe: str
    confidence: float  # 0-1
    timestamp: datetime

@dataclass
class PriceActionData:
    """Price action data from Seed service"""
    symbol: str
    current_price: float
    open_price: float
    high_price: float
    low_price: float
    volume: int
    change: float
    change_percent: float
    timestamp: datetime

@dataclass
class MarketAnalysisData:
    """Market analysis from Seed service"""
    overall_trend: str
    trend_strength: float
    market_sentiment: str
    volatility_outlook: str
    key_levels: Dict[str, float]
    sector_analysis: Dict[str, str]
    timestamp: datetime

@dataclass
class RecommendationData:
    """Stock recommendation from Seed service"""
    symbol: str
    action: str  # 'buy', 'sell', 'hold'
    confidence: float  # 0-1
    target_price: float
    stop_loss: float
    reasoning: str
    risk_level: str
    timeframe: str
    timestamp: datetime

@dataclass
class UnifiedSeedServiceResponse:
    """Unified Seed service response model"""
    # Response Metadata
    request_id: str
    timestamp: str
    success: bool
    message: str
    data_version: str
    
    # Core Response Data
    technical_indicators: Optional[List[TechnicalIndicator]] = None
    price_action_data: Optional[List[PriceActionData]] = None
    market_analysis: Optional[MarketAnalysisData] = None
    recommendations: Optional[List[RecommendationData]] = None
    
    # Analysis Results
    analysis_summary: Optional[Dict[str, Any]] = None
    risk_assessment: Optional[Dict[str, Any]] = None
    technical_levels: Optional[Dict[str, Any]] = None
    confidence_scores: Optional[Dict[str, float]] = None
    
    # Data Quality
    data_quality_score: Optional[float] = None
    processing_time_ms: Optional[int] = None

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def create_unified_seed_request(
    strategy: TradingStrategy = TradingStrategy.SWING,
    risk_level: RiskLevel = RiskLevel.MEDIUM,
    investment_horizon: InvestmentHorizon = InvestmentHorizon.MEDIUM_TERM,
    max_positions: int = 10,  # 🔴 MANDATORY - Maximum number of stocks to recommend
    **kwargs
) -> UnifiedSeedServiceRequest:
    """Create a unified Seed service request with sensible defaults"""
    
    # Create market context with defaults
    market_context = MarketContext(
        market_regime=MarketRegime.RANGING,
        volatility_regime=VolatilityRegime.MEDIUM,
        primary_trend_direction="bullish",
        trend_strength=TrendStrength.MODERATE,
        trend_acceleration=0.15,
        advancing_stocks_ratio=0.65,
        new_highs_lows_ratio=1.2,
        vix_level=18.5,
        fear_greed_index=0.3,
        volume_trend="increasing",
        institutional_flow="buying",
        market_sentiment="bullish"
    )
    
    # Create sector context with defaults
    sector_context = SectorContext(
        sector_momentum={
            "NIFTY BANK": SectorMomentum.LEADING,
            "NIFTY IT": SectorMomentum.STRONG,
            "NIFTY METAL": SectorMomentum.AVERAGE,
            "NIFTY FMCG": SectorMomentum.WEAK,
            "NIFTY AUTO": SectorMomentum.STRONG,
            "NIFTY PHARMA": SectorMomentum.AVERAGE,
            "NIFTY ENERGY": SectorMomentum.LAGGING,
            "NIFTY REALTY": SectorMomentum.WEAK
        },
        sector_rotation_stage="mid",
        leading_sectors=["NIFTY BANK", "NIFTY IT", "NIFTY AUTO"],
        lagging_sectors=["NIFTY ENERGY", "NIFTY REALTY"],
        sector_correlation_level="medium",
        sector_diversification_opportunity=True
    )
    
    # Create technical context with defaults
    technical_context = TechnicalContext(
        timeframe_alignment={
            "1min": "bullish",
            "5min": "bullish",
            "15min": "sideways",
            "30min": "bearish",
            "1hour": "sideways",
            "daily": "bullish"
        },
        dominant_timeframe="daily",
        key_support_levels=[25060.7, 25000.0, 24950.0],
        key_resistance_levels=[25074.05, 25100.0, 25150.0],
        breakout_probability=0.65,
        momentum_score=0.3,
        momentum_acceleration=0.1,
        volume_confirmation="bullish",
        volume_surge_detected=True
    )
    
    # Create user preferences
    user_preferences = UserPreferences(
        # 🔴 MANDATORY FIELDS
        strategy=strategy,
        risk_level=risk_level,
        investment_horizon=investment_horizon,
        max_positions=max_positions,
        
        # 🟡 OPTIONAL STRATEGY PREFERENCES
        primary_strategy=strategy.value,
        risk_tolerance=risk_level.value,
        max_portfolio_risk=0.15,
        
        # 🟡 OPTIONAL TRADING EXECUTION FIELDS
        profit_target_value=15.0,  # Optional - Trading execution
        stop_loss_percentage=5.0,  # Optional - Trading execution
        
        # 🟡 OPTIONAL USER PREFERENCES
        preferred_sectors=["NIFTY BANK", "NIFTY IT", "NIFTY AUTO"],
        excluded_sectors=["NIFTY ENERGY", "NIFTY REALTY"],
        max_position_size=0.12,
        min_position_size=0.02,
        execution_urgency="normal"
    )
    
    # Create risk context
    risk_context = RiskContext(
        market_risk_level="medium",
        correlation_risk="medium",
        recommended_position_size=0.08,
        max_position_size=0.12,
        var_95=0.05,
        max_drawdown_probability=0.15,
        risk_appetite="moderate",
        volatility_forecast="stable"
    )
    
    # Create contextual features
    contextual_features = ContextualFeatures(
        market_context=market_context,
        sector_context=sector_context,
        technical_context=technical_context,
        risk_context=risk_context,
        time_context={
            "market_session": "regular_hours",
            "time_of_day": "afternoon",
            "day_of_week": datetime.now().strftime('%A').lower(),
            "month_end_effect": False
        },
        sentiment_context={
            "overall_sentiment": "bullish",
            "retail_sentiment": "neutral",
            "institutional_sentiment": "bullish",
            "news_sentiment": "positive"
        },
        macro_context={
            "economic_indicators": "positive",
            "policy_environment": "supportive",
            "global_markets": "mixed"
        }
    )
    
    # Create main request
    request = UnifiedSeedServiceRequest(
        request_id=f"unified_request_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        timestamp=datetime.now().isoformat(),
        market_context=market_context,
        sector_context=sector_context,
        technical_context=technical_context,
        user_preferences=user_preferences,
        risk_context=risk_context,
        contextual_features=contextual_features,
        **kwargs
    )
    
    return request

def create_seed_service_payload(request: UnifiedSeedServiceRequest) -> Dict[str, Any]:
    """Create Seed service payload from unified request"""
    return {
        "request_id": request.request_id,
        "timestamp": request.timestamp,
        "data_version": request.data_version,
        "request_source": request.request_source,
        "priority": request.priority,
        "response_format": request.response_format,
        "include_analysis": request.include_analysis,
        "include_risk_metrics": request.include_risk_metrics,
        "include_technical_levels": request.include_technical_levels,
        
        "market_context": {
            "market_regime": request.market_context.market_regime.value,
            "volatility_regime": request.market_context.volatility_regime.value,
            "primary_trend_direction": request.market_context.primary_trend_direction,
            "trend_strength": request.market_context.trend_strength.value,
            "trend_acceleration": request.market_context.trend_acceleration,
            "advancing_stocks_ratio": request.market_context.advancing_stocks_ratio,
            "new_highs_lows_ratio": request.market_context.new_highs_lows_ratio,
            "vix_level": request.market_context.vix_level,
            "fear_greed_index": request.market_context.fear_greed_index,
            "volume_trend": request.market_context.volume_trend,
            "institutional_flow": request.market_context.institutional_flow,
            "market_sentiment": request.market_context.market_sentiment,
            "macro_indicators": request.market_context.macro_indicators
        },
        
        "sector_context": {
            "sector_momentum": {k: v.value for k, v in request.sector_context.sector_momentum.items()},
            "sector_rotation_stage": request.sector_context.sector_rotation_stage,
            "leading_sectors": request.sector_context.leading_sectors,
            "lagging_sectors": request.sector_context.lagging_sectors,
            "sector_correlation_level": request.sector_context.sector_correlation_level,
            "sector_diversification_opportunity": request.sector_context.sector_diversification_opportunity,
            "sector_rotation_signals": request.sector_context.sector_rotation_signals
        },
        
        "technical_context": {
            "timeframe_alignment": request.technical_context.timeframe_alignment,
            "dominant_timeframe": request.technical_context.dominant_timeframe,
            "key_support_levels": request.technical_context.key_support_levels,
            "key_resistance_levels": request.technical_context.key_resistance_levels,
            "breakout_probability": request.technical_context.breakout_probability,
            "momentum_score": request.technical_context.momentum_score,
            "momentum_acceleration": request.technical_context.momentum_acceleration,
            "volume_confirmation": request.technical_context.volume_confirmation,
            "volume_surge_detected": request.technical_context.volume_surge_detected,
            "technical_indicators": request.technical_context.technical_indicators
        },
        
        "user_preferences": {
            "strategy": request.user_preferences.strategy.value,
            "risk_level": request.user_preferences.risk_level.value,
            "investment_horizon": request.user_preferences.investment_horizon.value,
            "primary_strategy": request.user_preferences.primary_strategy,
            "secondary_strategy": request.user_preferences.secondary_strategy,
            "risk_tolerance": request.user_preferences.risk_tolerance,
            "max_portfolio_risk": request.user_preferences.max_portfolio_risk,
            "max_positions": request.user_preferences.max_positions,
            "profit_target_type": request.user_preferences.profit_target_type.value if request.user_preferences.profit_target_type else None,
            "profit_target_value": request.user_preferences.profit_target_value,
            "max_loss_percent": request.user_preferences.max_loss_percent,
            "stop_loss_percentage": request.user_preferences.stop_loss_percentage,
            "take_profit_percentage": request.user_preferences.take_profit_percentage,
            "preferred_sectors": request.user_preferences.preferred_sectors,
            "excluded_sectors": request.user_preferences.excluded_sectors,
            "min_liquidity": request.user_preferences.min_liquidity,
            "max_position_size": request.user_preferences.max_position_size,
            "min_position_size": request.user_preferences.min_position_size,
            "execution_urgency": request.user_preferences.execution_urgency,
            "time_constraints": request.user_preferences.time_constraints
        },
        
        "risk_context": {
            "market_risk_level": request.risk_context.market_risk_level,
            "correlation_risk": request.risk_context.correlation_risk,
            "recommended_position_size": request.risk_context.recommended_position_size,
            "max_position_size": request.risk_context.max_position_size,
            "var_95": request.risk_context.var_95,
            "max_drawdown_probability": request.risk_context.max_drawdown_probability,
            "risk_appetite": request.risk_context.risk_appetite,
            "volatility_forecast": request.risk_context.volatility_forecast
        },
        
        "progressive_features": asdict(request.progressive_features) if request.progressive_features else None,
        "market_sentiment": request.market_sentiment,
        "macro_indicators": request.macro_indicators,
        "time_context": request.time_context
    }

def parse_seed_response(response_data: Dict[str, Any]) -> UnifiedSeedServiceResponse:
    """Parse Seed service response into unified model"""
    return UnifiedSeedServiceResponse(
        request_id=response_data.get("request_id", ""),
        timestamp=response_data.get("timestamp", ""),
        success=response_data.get("success", False),
        message=response_data.get("message", ""),
        data_version=response_data.get("data_version", "13.0"),
        technical_indicators=response_data.get("technical_indicators", []),
        price_action_data=response_data.get("price_action_data", []),
        market_analysis=response_data.get("market_analysis"),
        recommendations=response_data.get("recommendations", []),
        analysis_summary=response_data.get("analysis_summary"),
        risk_assessment=response_data.get("risk_assessment"),
        technical_levels=response_data.get("technical_levels"),
        confidence_scores=response_data.get("confidence_scores"),
        data_quality_score=response_data.get("data_quality_score"),
        processing_time_ms=response_data.get("processing_time_ms")
    )

# =============================================================================
# DEMONSTRATION FUNCTIONS
# =============================================================================

def demonstrate_unified_model():
    """Demonstrate the unified Seed service model"""
    print("=" * 80)
    print("UNIFIED SEED SERVICE DATA MODEL")
    print("=" * 80)
    
    # Create unified request
    print("\n📊 Creating unified Seed service request...")
    request = create_unified_seed_request(
        strategy=TradingStrategy.SWING,
        risk_level=RiskLevel.MEDIUM,
        investment_horizon=InvestmentHorizon.MEDIUM_TERM
    )
    
    print(f"✅ Unified request created: {request.request_id}")
    print(f"📅 Timestamp: {request.timestamp}")
    print(f"📋 Data Version: {request.data_version}")
    
    # Display key information
    print(f"\n👤 USER PREFERENCES:")
    print(f"  • Strategy: {request.user_preferences.strategy.value}")
    print(f"  • Risk Level: {request.user_preferences.risk_level.value}")
    print(f"  • Investment Horizon: {request.user_preferences.investment_horizon.value}")
    print(f"  • Max Positions: {request.user_preferences.max_positions}")
    print(f"  • Preferred Sectors: {', '.join(request.user_preferences.preferred_sectors or [])}")
    
    print(f"\n📈 MARKET CONTEXT:")
    print(f"  • Market Regime: {request.market_context.market_regime.value}")
    print(f"  • Volatility Regime: {request.market_context.volatility_regime.value}")
    print(f"  • Primary Trend: {request.market_context.primary_trend_direction}")
    print(f"  • Trend Strength: {request.market_context.trend_strength.value}")
    print(f"  • VIX Level: {request.market_context.vix_level}")
    
    print(f"\n🏭 SECTOR CONTEXT:")
    print(f"  • Leading Sectors: {', '.join(request.sector_context.leading_sectors)}")
    print(f"  • Lagging Sectors: {', '.join(request.sector_context.lagging_sectors)}")
    print(f"  • Rotation Stage: {request.sector_context.sector_rotation_stage}")
    
    print(f"\n📊 TECHNICAL CONTEXT:")
    print(f"  • Dominant Timeframe: {request.technical_context.dominant_timeframe}")
    print(f"  • Breakout Probability: {request.technical_context.breakout_probability:.1%}")
    print(f"  • Momentum Score: {request.technical_context.momentum_score:.2f}")
    print(f"  • Volume Confirmation: {request.technical_context.volume_confirmation}")
    
    print(f"\n⚠️ RISK CONTEXT:")
    print(f"  • Market Risk Level: {request.risk_context.market_risk_level}")
    print(f"  • Correlation Risk: {request.risk_context.correlation_risk}")
    print(f"  • Recommended Position Size: {request.risk_context.recommended_position_size:.1%}")
    print(f"  • Max Position Size: {request.risk_context.max_position_size:.1%}")
    
    # Create payload
    print(f"\n🚀 Creating Seed service payload...")
    payload = create_seed_service_payload(request)
    
    # Save payload
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    with open(f'logs/unified_seed_payload_{timestamp}.json', 'w') as f:
        json.dump(payload, f, indent=2)
    
    print(f"✅ Unified Seed service payload saved to logs/unified_seed_payload_{timestamp}.json")
    
    # Display payload summary
    payload_size = len(json.dumps(payload))
    print(f"📏 Payload size: {payload_size:,} characters")
    
    print(f"\n📋 PAYLOAD STRUCTURE:")
    print(f"  • Request ID: {payload['request_id']}")
    print(f"  • Market Context: {len(payload['market_context'])} fields")
    print(f"  • Sector Context: {len(payload['sector_context'])} fields")
    print(f"  • Technical Context: {len(payload['technical_context'])} fields")
    print(f"  • User Preferences: {len(payload['user_preferences'])} fields")
    print(f"  • Risk Context: {len(payload['risk_context'])} fields")
    
    print("\n" + "=" * 80)
    print("This unified model consolidates ALL previous Seed models")
    print("into a single, comprehensive, and maintainable solution!")
    print("=" * 80)

def main():
    """Main entry point"""
    demonstrate_unified_model()

if __name__ == "__main__":
    main()
