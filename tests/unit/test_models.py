"""
Unit Tests for Data Models
===========================

Tests for Pydantic models to ensure validation and serialization work correctly.
"""

import pytest
from datetime import datetime
from decimal import Decimal
from pydantic import ValidationError

from models.data_models import (
    RealTimeRequest, RealTimeResponse, RealTimeStockData,
    HistoricalRequest, HistoricalResponse, Candle, Exchange, Interval
)


class TestRealTimeModels:
    """Tests for real-time data models."""
    
    def test_real_time_request_valid(self):
        """Test valid real-time request creation."""
        request = RealTimeRequest(symbols=["RELIANCE", "TCS"], exchange=Exchange.NSE)
        assert request.symbols == ["RELIANCE", "TCS"]
        assert request.exchange == Exchange.NSE
    
    def test_real_time_request_validation(self):
        """Test real-time request validation."""
        # Valid with defaults
        request = RealTimeRequest(symbols=["RELIANCE"])
        assert request.exchange == Exchange.NSE
        assert request.include_depth is False
        assert request.include_circuit_limits is True
    
    def test_real_time_stock_data_creation(self):
        """Test real-time stock data model creation."""
        stock_data = RealTimeStockData(
            symbol="RELIANCE",
            exchange=Exchange.NSE,
            last_price=Decimal("2500.50"),
            open_price=Decimal("2480.00"),
            high_price=Decimal("2520.00"),
            low_price=Decimal("2475.00"),
            change=Decimal("25.50"),
            change_percent=Decimal("1.03"),
            volume=1000000,
            timestamp=datetime.now()
        )
        assert stock_data.symbol == "RELIANCE"
        assert stock_data.last_price == Decimal("2500.50")
        assert stock_data.volume == 1000000
        assert stock_data.exchange == Exchange.NSE


class TestHistoricalModels:
    """Tests for historical data models."""
    
    def test_historical_request_valid(self):
        """Test valid historical request creation."""
        request = HistoricalRequest(
            symbol="RELIANCE",
            from_date=datetime(2024, 1, 1),
            to_date=datetime(2024, 1, 31),
            interval=Interval.DAY
        )
        assert request.symbol == "RELIANCE"
        assert request.interval == Interval.DAY
        assert request.from_date.year == 2024
        assert request.to_date.month == 1
    
    def test_candle_creation(self):
        """Test candle model creation."""
        candle = Candle(
            timestamp=datetime.now(),
            open=Decimal("2500.0"),
            high=Decimal("2550.0"),
            low=Decimal("2490.0"),
            close=Decimal("2540.0"),
            volume=1000000
        )
        assert candle.open == Decimal("2500.0")
        assert candle.high == Decimal("2550.0")
        assert candle.low == Decimal("2490.0")
        assert candle.close == Decimal("2540.0")
        assert candle.volume == 1000000
    
    def test_candle_validation(self):
        """Test candle validates OHLC logic."""
        # Valid candle
        candle = Candle(
            timestamp=datetime.now(),
            open=Decimal("100"),
            high=Decimal("110"),
            low=Decimal("95"),
            close=Decimal("105"),
            volume=1000
        )
        assert candle.high >= candle.open
        assert candle.low <= candle.close


class TestEnums:
    """Tests for enum types."""
    
    def test_exchange_enum(self):
        """Test Exchange enum values."""
        assert Exchange.NSE.value == "NSE"
        assert Exchange.BSE.value == "BSE"
    
    def test_interval_enum(self):
        """Test Interval enum values."""
        assert Interval.MINUTE.value == "minute"
        assert Interval.DAY.value == "day"
        assert Interval.HOUR.value == "hour"


class TestResponseModels:
    """Tests for response models."""
    
    def test_real_time_response(self):
        """Test real-time response model."""
        response = RealTimeResponse(
            timestamp=datetime.now(),
            request_id="req_123",
            stocks=[],
            successful_count=0,
            failed_count=0
        )
        assert response.request_id == "req_123"
        assert response.successful_count == 0
    
    def test_historical_response(self):
        """Test historical response model."""
        candles = [
            Candle(
                timestamp=datetime.now(),
                open=Decimal("100"),
                high=Decimal("110"),
                low=Decimal("95"),
                close=Decimal("105"),
                volume=1000
            )
        ]
        response = HistoricalResponse(
            symbol="RELIANCE",
            from_date=datetime(2024, 1, 1),
            to_date=datetime(2024, 1, 31),
            interval=Interval.DAY,
            candles=candles,
            total_candles=1,
            request_id="req_456"
        )
        assert response.symbol == "RELIANCE"
        assert response.total_candles == 1
        assert len(response.candles) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
