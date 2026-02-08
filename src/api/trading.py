"""
Trading API Module

Consolidated trading endpoints for Kite Services.
Provides portfolio and position management information.

Endpoints:
- GET /trading/status - Portfolio and positions status
"""

from fastapi import APIRouter, HTTPException
import logging
import time

from models.unified_api_models import (
    TradingStatusResponse, Position, Holding
)
from core.service_manager import get_service_manager

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/trading/status", response_model=TradingStatusResponse)
async def get_trading_status():
    """
    Get portfolio and trading status.
    
    Returns comprehensive trading information including:
    - Authentication status
    - Current positions (futures, options, etc.)
    - Holdings (equity, mutual funds, etc.)
    - Portfolio P&L summary
    - Trading permissions and account status
    """
    start_time = time.time()
    
    try:
        service_manager = await get_service_manager()
        kite_client = service_manager.kite_client
        
        logger.info("Fetching trading status and portfolio information")
        
        # Initialize response data
        authenticated = False
        user_id = None
        user_name = None
        broker = None
        enabled = False
        positions = []
        holdings = []
        total_pnl = None
        day_pnl = None
        
        # Check authentication
        try:
            profile = await kite_client.get_profile()
            if profile:
                authenticated = True
                user_id = profile.get("user_id")
                user_name = profile.get("user_name")
                broker = profile.get("broker")
                enabled = profile.get("enabled", False)
        except Exception as e:
            logger.warning(f"Failed to get user profile: {str(e)}")
        
        if not authenticated:
            processing_time = (time.time() - start_time) * 1000
            return TradingStatusResponse(
                success=True,
                authenticated=False,
                enabled=False,
                total_positions=0,
                total_holdings=0,
                processing_time_ms=round(processing_time, 2),
                message="Not authenticated - trading status unavailable"
            )
        
        # Get positions
        try:
            positions_data = await kite_client.get_positions()
            if positions_data:
                for position_data in positions_data.get("day", []) + positions_data.get("net", []):
                    positions.append(Position(
                        symbol=position_data.get("tradingsymbol", ""),
                        instrument_token=position_data.get("instrument_token"),
                        quantity=position_data.get("quantity", 0),
                        average_price=position_data.get("average_price"),
                        last_price=position_data.get("last_price"),
                        pnl=position_data.get("pnl"),
                        pnl_percent=position_data.get("pnl_percent"),
                        day_pnl=position_data.get("day_pnl"),
                        day_pnl_percent=position_data.get("day_pnl_percent"),
                        product=position_data.get("product", ""),
                        exchange=position_data.get("exchange", ""),
                        instrument_type=position_data.get("instrument_type", "")
                    ))
        except Exception as e:
            logger.warning(f"Failed to get positions: {str(e)}")
        
        # Get holdings
        try:
            holdings_data = await kite_client.get_holdings()
            if holdings_data:
                for holding_data in holdings_data:
                    holdings.append(Holding(
                        symbol=holding_data.get("tradingsymbol", ""),
                        instrument_token=holding_data.get("instrument_token"),
                        quantity=holding_data.get("quantity", 0),
                        average_price=holding_data.get("average_price"),
                        last_price=holding_data.get("last_price"),
                        pnl=holding_data.get("pnl"),
                        pnl_percent=holding_data.get("pnl_percent"),
                        day_pnl=holding_data.get("day_pnl"),
                        day_pnl_percent=holding_data.get("day_pnl_percent"),
                        product=holding_data.get("product", ""),
                        exchange=holding_data.get("exchange", ""),
                        instrument_type=holding_data.get("instrument_type", "")
                    ))
        except Exception as e:
            logger.warning(f"Failed to get holdings: {str(e)}")
        
        # Calculate total P&L
        try:
            total_pnl = sum(
                (pos.pnl or 0) for pos in positions
            ) + sum(
                (holding.pnl or 0) for holding in holdings
            )
            
            day_pnl = sum(
                (pos.day_pnl or 0) for pos in positions
            ) + sum(
                (holding.day_pnl or 0) for holding in holdings
            )
        except Exception as e:
            logger.warning(f"Failed to calculate P&L: {str(e)}")
        
        processing_time = (time.time() - start_time) * 1000
        
        return TradingStatusResponse(
            success=True,
            authenticated=authenticated,
            user_id=user_id,
            user_name=user_name,
            broker=broker,
            enabled=enabled,
            positions=positions,
            holdings=holdings,
            total_positions=len(positions),
            total_holdings=len(holdings),
            total_pnl=total_pnl,
            day_pnl=day_pnl,
            processing_time_ms=round(processing_time, 2),
            message="Trading status retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Trading status fetch failed: {str(e)}")
        processing_time = (time.time() - start_time) * 1000
        raise HTTPException(
            status_code=500,
            detail=f"Trading status fetch failed: {str(e)}"
        )
