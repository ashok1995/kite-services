"""
Trading API Module

Consolidated trading endpoints for Kite Services.
Provides portfolio and position management information.

Endpoints:
- GET /trading/status - Portfolio and positions status
- POST /trading/orders/place - Place a new order
- PUT /trading/orders/{order_id}/modify - Modify an order
- DELETE /trading/orders/{order_id}/cancel - Cancel an order
- GET /trading/orders - Get all orders (today)
- GET /trading/orders/{order_id} - Get specific order details
- GET /trading/order-history/{order_id} - Get order execution history
"""

import logging
import time

from fastapi import APIRouter, HTTPException

from core.service_manager import get_service_manager
from models.order_models import (
    CancelOrderRequest,
    ModifyOrderRequest,
    OrderDetails,
    OrderHistoryItem,
    OrderHistoryResponse,
    OrderListResponse,
    OrderResponse,
    PlaceOrderRequest,
)
from models.unified_api_models import Holding, Position, TradingStatusResponse

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
                message="Not authenticated - trading status unavailable",
            )

        # Get positions
        try:
            positions_data = await kite_client.get_positions()
            if positions_data:
                for position_data in positions_data.get("day", []) + positions_data.get("net", []):
                    positions.append(
                        Position(
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
                            instrument_type=position_data.get("instrument_type", ""),
                        )
                    )
        except Exception as e:
            logger.warning(f"Failed to get positions: {str(e)}")

        # Get holdings
        try:
            holdings_data = await kite_client.get_holdings()
            if holdings_data:
                for holding_data in holdings_data:
                    holdings.append(
                        Holding(
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
                            instrument_type=holding_data.get("instrument_type", ""),
                        )
                    )
        except Exception as e:
            logger.warning(f"Failed to get holdings: {str(e)}")

        # Calculate total P&L
        try:
            total_pnl = sum((pos.pnl or 0) for pos in positions) + sum(
                (holding.pnl or 0) for holding in holdings
            )

            day_pnl = sum((pos.day_pnl or 0) for pos in positions) + sum(
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
            message="Trading status retrieved successfully",
        )

    except Exception as e:
        logger.error(f"Trading status fetch failed: {str(e)}")
        processing_time = (time.time() - start_time) * 1000
        raise HTTPException(status_code=500, detail=f"Trading status fetch failed: {str(e)}")


# ===================================================================
# ORDER MANAGEMENT ENDPOINTS (with Paper Trading Support)
# ===================================================================


@router.post("/trading/orders/place", response_model=OrderResponse)
async def place_order(request: PlaceOrderRequest):
    """
    Place a new order (real or simulated based on PAPER_TRADING_MODE).

    🚨 CRITICAL SAFETY:
    - Check KITE_PAPER_TRADING_MODE environment variable
    - true = Simulated orders (NO REAL MONEY) - SAFE for testing
    - false = Real orders (ACTUAL MONEY AT RISK) - Production only

    **Order Types:**
    - MARKET: Immediate execution at market price
    - LIMIT: Execute at specified price or better
    - SL: Stop-loss limit order (trigger + limit price)
    - SL-M: Stop-loss market order (trigger only)

    **Product Types:**
    - CNC: Cash and Carry (delivery)
    - MIS: Margin Intraday Squareoff (intraday)
    - NRML: Normal (for F&O)

    **Example (Paper Trading):**
    ```json
    {
      "symbol": "RELIANCE",
      "exchange": "NSE",
      "transaction_type": "BUY",
      "quantity": 10,
      "order_type": "LIMIT",
      "price": 1420.00,
      "product": "MIS"
    }
    ```
    """
    start_time = time.time()

    try:
        service_manager = await get_service_manager()
        kite_client = service_manager.kite_client

        # Check paper trading mode
        paper_trading = kite_client._is_paper_trading()

        if paper_trading:
            logger.warning(
                f"🧪 PAPER TRADING MODE: Placing simulated {request.transaction_type} order "
                f"for {request.symbol} (qty: {request.quantity})"
            )
        else:
            logger.critical(
                f"🚨 REAL TRADING MODE: Placing REAL {request.transaction_type} order "
                f"for {request.symbol} (qty: {request.quantity}) - REAL MONEY AT RISK!"
            )

        # Place order via Kite client
        result = await kite_client.place_order(
            symbol=request.symbol,
            exchange=request.exchange.value,
            transaction_type=request.transaction_type.value,
            quantity=request.quantity,
            order_type=request.order_type.value,
            product=request.product.value,
            price=float(request.price) if request.price else None,
            trigger_price=float(request.trigger_price) if request.trigger_price else None,
            validity=request.validity.value,
            disclosed_quantity=request.disclosed_quantity,
            tag=request.tag,
        )

        processing_time = (time.time() - start_time) * 1000

        return OrderResponse(
            success=True,
            order_id=result["order_id"],
            message=result["message"],
            paper_trading=result["paper_trading"],
            symbol=request.symbol,
            exchange=request.exchange.value,
            transaction_type=request.transaction_type.value,
            quantity=request.quantity,
            order_type=request.order_type.value,
            price=request.price,
            status=None,  # Status will be fetched separately if needed
        )

    except Exception as e:
        logger.error(f"Order placement failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Order placement failed: {str(e)}")


@router.put("/trading/orders/{order_id}/modify", response_model=OrderResponse)
async def modify_order(order_id: str, request: ModifyOrderRequest):
    """
    Modify an existing order (real or simulated).

    You can modify:
    - Quantity
    - Price
    - Trigger price
    - Order type
    - Validity

    **Note:** Only pending/open orders can be modified.
    """
    start_time = time.time()

    try:
        service_manager = await get_service_manager()
        kite_client = service_manager.kite_client

        # Modify order via Kite client
        result = await kite_client.modify_order(
            order_id=order_id,
            quantity=request.quantity,
            price=float(request.price) if request.price else None,
            trigger_price=float(request.trigger_price) if request.trigger_price else None,
            order_type=request.order_type.value if request.order_type else None,
            validity=request.validity.value if request.validity else None,
        )

        processing_time = (time.time() - start_time) * 1000

        return OrderResponse(
            success=True,
            order_id=result["order_id"],
            message=result["message"],
            paper_trading=result["paper_trading"],
        )

    except Exception as e:
        logger.error(f"Order modification failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Order modification failed: {str(e)}")


@router.delete("/trading/orders/{order_id}/cancel", response_model=OrderResponse)
async def cancel_order(order_id: str):
    """
    Cancel an existing order (real or simulated).

    **Note:** Only pending/open orders can be cancelled.
    """
    start_time = time.time()

    try:
        service_manager = await get_service_manager()
        kite_client = service_manager.kite_client

        # Cancel order via Kite client
        result = await kite_client.cancel_order(order_id=order_id)

        processing_time = (time.time() - start_time) * 1000

        return OrderResponse(
            success=True,
            order_id=result["order_id"],
            message=result["message"],
            paper_trading=result["paper_trading"],
        )

    except Exception as e:
        logger.error(f"Order cancellation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Order cancellation failed: {str(e)}")


@router.get("/trading/orders", response_model=OrderListResponse)
async def get_orders():
    """
    Get all orders for the day (real or simulated).

    Returns all orders placed today, including:
    - Pending orders
    - Executed orders
    - Cancelled orders
    - Rejected orders
    """
    start_time = time.time()

    try:
        service_manager = await get_service_manager()
        kite_client = service_manager.kite_client

        # Get orders via Kite client
        result = await kite_client.get_orders()

        # Convert to OrderDetails model
        orders = []
        for order_data in result.get("orders", []):
            orders.append(
                OrderDetails(
                    order_id=order_data.get("order_id", ""),
                    exchange_order_id=order_data.get("exchange_order_id"),
                    symbol=order_data.get("symbol", order_data.get("tradingsymbol", "")),
                    exchange=order_data.get("exchange", ""),
                    instrument_token=order_data.get("instrument_token"),
                    transaction_type=order_data.get("transaction_type", ""),
                    order_type=order_data.get("order_type", ""),
                    product=order_data.get("product", ""),
                    quantity=order_data.get("quantity", 0),
                    pending_quantity=order_data.get("pending_quantity", 0),
                    filled_quantity=order_data.get("filled_quantity", 0),
                    price=order_data.get("price"),
                    trigger_price=order_data.get("trigger_price"),
                    average_price=order_data.get("average_price"),
                    status=order_data.get("status", ""),
                    status_message=order_data.get("status_message"),
                    order_timestamp=order_data.get("order_timestamp"),
                    exchange_timestamp=order_data.get("exchange_timestamp"),
                    validity=order_data.get("validity", "DAY"),
                    tag=order_data.get("tag"),
                    paper_trading=order_data.get("paper_trading", False),
                )
            )

        processing_time = (time.time() - start_time) * 1000

        return OrderListResponse(
            success=True,
            orders=orders,
            total_orders=len(orders),
            paper_trading=result["paper_trading"],
        )

    except Exception as e:
        logger.error(f"Failed to fetch orders: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch orders: {str(e)}")


@router.get("/trading/orders/{order_id}", response_model=OrderDetails)
async def get_order_details(order_id: str):
    """
    Get details of a specific order.
    """
    start_time = time.time()

    try:
        service_manager = await get_service_manager()
        kite_client = service_manager.kite_client

        # Get all orders and find the specific one
        result = await kite_client.get_orders()

        for order_data in result.get("orders", []):
            if order_data.get("order_id") == order_id:
                return OrderDetails(
                    order_id=order_data.get("order_id", ""),
                    exchange_order_id=order_data.get("exchange_order_id"),
                    symbol=order_data.get("symbol", order_data.get("tradingsymbol", "")),
                    exchange=order_data.get("exchange", ""),
                    instrument_token=order_data.get("instrument_token"),
                    transaction_type=order_data.get("transaction_type", ""),
                    order_type=order_data.get("order_type", ""),
                    product=order_data.get("product", ""),
                    quantity=order_data.get("quantity", 0),
                    pending_quantity=order_data.get("pending_quantity", 0),
                    filled_quantity=order_data.get("filled_quantity", 0),
                    price=order_data.get("price"),
                    trigger_price=order_data.get("trigger_price"),
                    average_price=order_data.get("average_price"),
                    status=order_data.get("status", ""),
                    status_message=order_data.get("status_message"),
                    order_timestamp=order_data.get("order_timestamp"),
                    exchange_timestamp=order_data.get("exchange_timestamp"),
                    validity=order_data.get("validity", "DAY"),
                    tag=order_data.get("tag"),
                    paper_trading=order_data.get("paper_trading", False),
                )

        raise HTTPException(status_code=404, detail=f"Order {order_id} not found")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch order details: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch order details: {str(e)}")


@router.get("/trading/order-history/{order_id}", response_model=OrderHistoryResponse)
async def get_order_history(order_id: str):
    """
    Get execution history of a specific order.

    Returns the complete lifecycle of an order including all status changes.
    """
    start_time = time.time()

    try:
        service_manager = await get_service_manager()
        kite_client = service_manager.kite_client

        # Get order history via Kite client
        result = await kite_client.get_order_history(order_id=order_id)

        # Convert to OrderHistoryItem model
        history = []
        for item in result.get("history", []):
            history.append(
                OrderHistoryItem(
                    order_id=item.get("order_id", order_id),
                    status=item.get("status", ""),
                    status_message=item.get("status_message"),
                    filled_quantity=item.get("filled_quantity", 0),
                    pending_quantity=item.get("pending_quantity", 0),
                    average_price=item.get("average_price"),
                    timestamp=item.get("timestamp"),
                )
            )

        processing_time = (time.time() - start_time) * 1000

        return OrderHistoryResponse(
            success=True,
            order_id=order_id,
            history=history,
            paper_trading=result["paper_trading"],
        )

    except Exception as e:
        logger.error(f"Failed to fetch order history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch order history: {str(e)}")
