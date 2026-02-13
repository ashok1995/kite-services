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
**Purpose**: Market intelligence and analysis

**Methods**:

- `get_market_context()` - Comprehensive market analysis
- `get_quick_context()` - Fast market summary

**Dependencies**: KiteClient, YahooFinanceService

---

### ConsolidatedMarketService

**File**: `src/services/consolidated_market_service.py`  
**Purpose**: Aggregates data from multiple sources

**Methods**:

- `get_consolidated_data(symbol, scope)` - Multi-source data aggregation

**Dependencies**: KiteClient, YahooFinanceService, MarketContextService

---

### YahooFinanceService

**File**: `src/services/yahoo_finance_service.py`  
**Purpose**: Global market data via Yahoo Finance

**Methods**:

- `get_quote(symbol)` - Get current quote
- `get_historical_data(symbol, period, interval)` - Get history
- `get_fundamentals(symbol)` - Company fundamentals

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
