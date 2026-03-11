"""
Order Models for Kite Trading
==============================

Pydantic models for order management with validation and safety checks.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from common.time_utils import now_ist_naive


class OrderType(str, Enum):
    """Order types supported by Kite."""

    MARKET = "MARKET"
    LIMIT = "LIMIT"
    SL = "SL"  # Stop-loss limit order
    SL_M = "SL-M"  # Stop-loss market order


class TransactionType(str, Enum):
    """Transaction types."""

    BUY = "BUY"
    SELL = "SELL"


class ProductType(str, Enum):
    """Product types (delivery vs intraday)."""

    CNC = "CNC"  # Cash and Carry (delivery)
    MIS = "MIS"  # Margin Intraday Square-off
    NRML = "NRML"  # Normal (for F&O)


class ValidityType(str, Enum):
    """Order validity types."""

    DAY = "DAY"  # Valid for the day
    IOC = "IOC"  # Immediate or Cancel


class OrderStatus(str, Enum):
    """Order status."""

    PENDING = "PENDING"
    OPEN = "OPEN"
    COMPLETE = "COMPLETE"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"
    MODIFIED = "MODIFIED"


class ExchangeType(str, Enum):
    """Exchange types."""

    NSE = "NSE"
    BSE = "BSE"
    NFO = "NFO"  # NSE F&O
    CDS = "CDS"  # Currency derivatives
    BCD = "BCD"  # Commodity derivatives


class PlaceOrderRequest(BaseModel):
    """Request model for placing an order."""

    symbol: str = Field(..., description="Trading symbol (e.g., RELIANCE)")
    exchange: ExchangeType = Field(..., description="Exchange (NSE/BSE/NFO)")
    transaction_type: TransactionType = Field(..., description="BUY or SELL")
    quantity: int = Field(..., gt=0, description="Order quantity (must be positive)")
    order_type: OrderType = Field(..., description="Order type (MARKET/LIMIT/SL/SL-M)")
    product: ProductType = Field(ProductType.MIS, description="Product type (CNC/MIS/NRML)")

    # Price fields
    price: Optional[Decimal] = Field(
        None, ge=0, description="Limit price (required for LIMIT/SL orders)"
    )
    trigger_price: Optional[Decimal] = Field(
        None, ge=0, description="Trigger price (required for SL/SL-M orders)"
    )

    # Optional fields
    validity: ValidityType = Field(ValidityType.DAY, description="Order validity (DAY/IOC)")
    disclosed_quantity: Optional[int] = Field(
        None, ge=0, description="Disclosed quantity for iceberg orders"
    )
    tag: Optional[str] = Field(None, max_length=20, description="Order tag (max 20 chars)")

    @field_validator("price")
    @classmethod
    def validate_price(cls, v, info):
        """Validate price is provided for LIMIT and SL orders."""
        order_type = info.data.get("order_type")
        if order_type in [OrderType.LIMIT, OrderType.SL] and v is None:
            raise ValueError(f"Price is required for {order_type} orders")
        return v

    @field_validator("trigger_price")
    @classmethod
    def validate_trigger_price(cls, v, info):
        """Validate trigger price is provided for SL and SL-M orders."""
        order_type = info.data.get("order_type")
        if order_type in [OrderType.SL, OrderType.SL_M] and v is None:
            raise ValueError(f"Trigger price is required for {order_type} orders")
        return v


class ModifyOrderRequest(BaseModel):
    """Request model for modifying an order."""

    order_id: str = Field(..., description="Order ID to modify")

    # Optional fields (only modify what's provided)
    quantity: Optional[int] = Field(None, gt=0, description="New quantity")
    price: Optional[Decimal] = Field(None, ge=0, description="New limit price")
    trigger_price: Optional[Decimal] = Field(None, ge=0, description="New trigger price")
    order_type: Optional[OrderType] = Field(None, description="New order type")
    validity: Optional[ValidityType] = Field(None, description="New validity")


class CancelOrderRequest(BaseModel):
    """Request model for cancelling an order."""

    order_id: str = Field(..., description="Order ID to cancel")
    variety: str = Field("regular", description="Order variety (regular/amo/co/iceberg)")


class OrderResponse(BaseModel):
    """Response model for order operations."""

    success: bool = Field(..., description="Operation success status")
    order_id: Optional[str] = Field(None, description="Order ID")
    message: str = Field(..., description="Response message")

    # Paper trading indicator
    paper_trading: bool = Field(False, description="True if order was simulated (paper trading)")

    # Order details (if available)
    symbol: Optional[str] = None
    exchange: Optional[str] = None
    transaction_type: Optional[str] = None
    quantity: Optional[int] = None
    order_type: Optional[str] = None
    price: Optional[Decimal] = None
    status: Optional[OrderStatus] = None

    timestamp: datetime = Field(default_factory=now_ist_naive)


class OrderDetails(BaseModel):
    """Detailed order information."""

    order_id: str = Field(..., description="Order ID")
    exchange_order_id: Optional[str] = Field(None, description="Exchange order ID")
    parent_order_id: Optional[str] = Field(None, description="Parent order ID (for BO/CO)")

    # Order details
    symbol: str = Field(..., description="Trading symbol")
    exchange: str = Field(..., description="Exchange")
    instrument_token: Optional[int] = Field(None, description="Instrument token")

    # Transaction details
    transaction_type: str = Field(..., description="BUY/SELL")
    order_type: str = Field(..., description="Order type")
    product: str = Field(..., description="Product type")
    variety: str = Field("regular", description="Order variety")

    # Quantity and pricing
    quantity: int = Field(..., description="Order quantity")
    pending_quantity: int = Field(0, description="Pending quantity")
    filled_quantity: int = Field(0, description="Filled quantity")

    price: Optional[Decimal] = Field(None, description="Order price")
    trigger_price: Optional[Decimal] = Field(None, description="Trigger price")
    average_price: Optional[Decimal] = Field(None, description="Average execution price")

    # Status
    status: str = Field(..., description="Order status")
    status_message: Optional[str] = Field(None, description="Status message")

    # Timestamps
    order_timestamp: Optional[datetime] = Field(None, description="Order placed time")
    exchange_timestamp: Optional[datetime] = Field(None, description="Exchange update time")

    # Other fields
    validity: str = Field("DAY", description="Order validity")
    tag: Optional[str] = Field(None, description="Order tag")

    # Paper trading
    paper_trading: bool = Field(False, description="True if simulated order")


class OrderListResponse(BaseModel):
    """Response model for listing orders."""

    success: bool = Field(..., description="Operation success status")
    orders: List[OrderDetails] = Field(default_factory=list, description="List of orders")
    total_orders: int = Field(0, description="Total number of orders")
    paper_trading: bool = Field(False, description="True if in paper trading mode")
    timestamp: datetime = Field(default_factory=now_ist_naive)


class OrderHistoryItem(BaseModel):
    """Single item in order history."""

    order_id: str
    status: str
    status_message: Optional[str] = None
    filled_quantity: int = 0
    pending_quantity: int = 0
    average_price: Optional[Decimal] = None
    timestamp: Optional[datetime] = None


class OrderHistoryResponse(BaseModel):
    """Response model for order history."""

    success: bool = Field(..., description="Operation success status")
    order_id: str = Field(..., description="Order ID")
    history: List[OrderHistoryItem] = Field(default_factory=list, description="Order history")
    paper_trading: bool = Field(False, description="True if simulated order")
    timestamp: datetime = Field(default_factory=now_ist_naive)
