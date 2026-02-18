# Services Documentation

## Overview

All business logic is implemented in stateless services with dependency injection.

## Core Services

### StockDataService

**File**: `src/services/stock_data_service.py`  
**Purpose**: Real-time and historical stock data operations

**Methods**:

- `get_real_time_data(symbols, exchange)` - Get current quotes
- `get_historical_data(symbol, from_date, to_date, interval)` - Get candles

**Dependencies**: KiteClient

---

### MarketContextService

**File**: `src/services/market_context_service.py`  
**Purpose**: Indian market context only (Kite Connect). Global context is provided by a separate service.

**Methods**:

- `get_market_breadth()` - Nifty 50 advance/decline
- `get_indian_market_data()` - Indian indices, regime
- `_get_volatility_data()` - India VIX
- `_get_sector_data()` - Indian sector performance

**Dependencies**: KiteClient only (no Yahoo in this service)

---

### KiteAuthService

**File**: `src/services/kite_auth_service.py`  
**Purpose**: Kite Connect authentication flow

**Methods**:

- `generate_login_url()` - Get OAuth URL
- `generate_session(request_token)` - Exchange for access token
- `validate_token()` - Check token validity

---

## Service Pattern

All services follow this pattern:

```python
class MyService:
    def __init__(self, dependency1, dependency2, logger=None):
        self.dependency1 = dependency1
        self.dependency2 = dependency2
        self.logger = logger or get_logger(__name__)

    async def initialize(self):
        \"\"\"Service initialization.\"\"\"
        pass

    async def cleanup(self):
        \"\"\"Service cleanup.\"\"\"
        pass

    async def do_something(self, params):
        \"\"\"Business logic.\"\"\"
        self.logger.info("Operation started")
        # Implementation
        return result
```

## Using Services

### In API Routes

```python
from services.stock_data_service import StockDataService

async def get_service(request: Request) -> StockDataService:
    kite_client = request.app.state.service_manager.kite_client
    return StockDataService(kite_client=kite_client)

@router.post("/data")
async def get_data(
    service: StockDataService = Depends(get_service)
):
    return await service.get_real_time_data(["RELIANCE"])
```

For complete service details, see source code and inline documentation.
