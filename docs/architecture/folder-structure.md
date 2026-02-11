# Project Folder Structure

## Complete Directory Tree

```
kite-services/
├── src/                          # Source code
│   ├── api/                      # API routes (controllers)
│   │   ├── __init__.py
│   │   ├── auth_routes.py        # Authentication endpoints
│   │   ├── simple_token_routes.py # Token management
│   │   ├── stock_data_routes.py  # Stock data endpoints
│   │   ├── market_context_routes.py # Market context
│   │   ├── market_context_data_routes.py # Market data
│   │   ├── consolidated_routes.py # Consolidated API
│   │   ├── intelligence_routes.py # Market intelligence
│   │   ├── intraday_routes.py    # Intraday context
│   │   ├── market_routes.py      # Legacy market routes
│   │   ├── trading_routes.py     # Trading (placeholder)
│   │   ├── position_routes.py    # Position tracking (placeholder)
│   │   ├── websocket_routes.py   # WebSocket endpoints
│   │   └── ui_market_routes.py   # UI-optimized endpoints
│   │
│   ├── services/                 # Business logic layer
│   │   ├── __init__.py
│   │   ├── stock_data_service.py # Stock data operations
│   │   ├── market_context_service.py # Market analysis
│   │   ├── consolidated_market_service.py # Data aggregation
│   │   ├── market_intelligence_service.py # Intelligence
│   │   ├── intraday_context_service.py # Intraday analysis
│   │   ├── yahoo_finance_service.py # Yahoo Finance client
│   │   ├── kite_auth_service.py  # Kite authentication
│   │   ├── kite_credentials_manager.py # Credential management
│   │   ├── kite_realtime_service.py # Real-time data
│   │   ├── kite_ticker.py        # Ticker WebSocket
│   │   └── existing_token_loader.py # Token loading
│   │
│   ├── models/                   # Data models (Pydantic)
│   │   ├── __init__.py
│   │   ├── data_models.py        # Stock data models
│   │   ├── market_context_models.py # Market context models
│   │   ├── market_context_data_models.py # Market data models
│   │   ├── consolidated_models.py # Consolidated models
│   │   ├── market_intelligence_models.py # Intelligence models
│   │   ├── intraday_context_models.py # Intraday models
│   │   └── market_models.py      # General market models
│   │
│   ├── core/                     # Core utilities & infrastructure
│   │   ├── __init__.py
│   │   ├── kite_client.py        # Kite Connect client
│   │   ├── db_manager.py         # Database operations
│   │   ├── service_manager.py    # Service lifecycle
│   │   ├── logging_config.py     # Logging setup
│   │   ├── technical_analysis.py # Technical indicators
│   │   └── talib_technical_analysis.py # TA-Lib indicators
│   │
│   ├── config/                   # Configuration
│   │   ├── __init__.py
│   │   └── settings.py           # Settings management
│   │
│   ├── ui/                       # UI files
│   │   └── token/                # Token management UI
│   │       ├── complete_token_flow_ui.html
│   │       ├── production_token_ui.html
│   │       └── simple_token_ui.html
│   │
│   ├── utils/                    # Utility functions
│   │   └── (currently empty)
│   │
│   └── main.py                   # Application entry point
│
├── tests/                        # Test suite
│   ├── unit/                     # Unit tests
│   │   ├── test_models.py        # Model tests
│   │   └── test_services/        # Service tests
│   │       ├── test_yahoo_finance_service.py
│   │       ├── test_market_context_service.py
│   │       └── test_token_validation.py
│   │
│   ├── integration/              # Integration tests
│   │   ├── test_stock_data_service.py
│   │   ├── test_market_context_service.py
│   │   └── demo_market_context_calculations.py
│   │
│   ├── e2e/                      # End-to-end tests
│   │   └── test_complete_workflow.py
│   │
│   ├── results/                  # Test results
│   │   ├── test_results.json
│   │   └── coverage_report.md
│   │
│   ├── conftest.py               # Pytest fixtures
│   ├── __init__.py
│   └── README.md                 # Testing documentation
│
├── docs/                         # Documentation
│   ├── README.md                 # Documentation index
│   ├── architecture.md           # System architecture
│   ├── folder-structure.md       # This file
│   ├── information-flow.md       # Data flow diagrams
│   ├── api.md                    # Complete API reference
│   ├── services.md               # Services documentation
│   ├── config.md                 # Configuration guide
│   ├── apis-used.md              # External APIs
│   ├── stock-data-service.md     # Stock data guide
│   ├── market-context-service.md # Market context guide
│   ├── kite-connect-setup.md     # Kite setup guide
│   ├── production-deployment.md  # Deployment guide
│   └── examples/                 # Code examples
│       ├── token_refresh_ui_example.html
│       ├── ui_integration_example.html
│       ├── token_flow_integration.js
│       ├── simple_ui_integration.js
│       └── ui_integration_snippet.js
│
├── logs/                         # Application logs
│   └── kite_services.log         # Main log file
│
├── data/                         # Data storage
│   └── market_context.db         # SQLite database
│
├── debug/                        # Debug artifacts
│   └── (git-ignored)
│
├── .env.example                  # Environment template
├── .gitignore                    # Git ignore rules
├── requirements.txt              # Python dependencies
├── Dockerfile                    # Production Docker image
├── Dockerfile.dev                # Development Docker image
├── docker-compose.yml            # Development compose
├── docker-compose.prod.yml       # Production compose
├── deploy.sh                     # Deployment script
├── entrypoint.prod.sh            # Docker entrypoint
├── README.md                     # Project README
└── CHANGELOG.md                  # Change history
```

## Directory Descriptions

### `/src/` - Source Code

**Purpose**: All application source code  
**Rules**:

- Organized by layer (api, services, models, core)
- Max 300 LOC per file
- All modules have docstrings

### `/src/api/` - API Routes

**Purpose**: HTTP endpoint definitions  
**Pattern**: Thin controllers that delegate to services  
**Rules**:

- One router per domain/resource
- Use dependency injection for services
- Return Pydantic models

### `/src/services/` - Business Logic

**Purpose**: Stateless business logic  
**Pattern**: Service classes with dependency injection  
**Rules**:

- No hardcoded values
- Comprehensive logging
- Proper error handling
- Stateless design

### `/src/models/` - Data Models

**Purpose**: Data validation and serialization  
**Pattern**: Pydantic models  
**Rules**:

- Clear field descriptions
- Proper validation
- Example values in docstrings

### `/src/core/` - Core Infrastructure

**Purpose**: Low-level utilities and clients  
**Pattern**: Reusable infrastructure components  
**Rules**:

- Framework-agnostic where possible
- Well-tested
- Minimal dependencies

### `/src/config/` - Configuration

**Purpose**: Application configuration  
**Pattern**: Pydantic Settings  
**Rules**:

- All config from environment
- Type-safe
- Validation included

### `/tests/` - Test Suite

**Purpose**: All test code  
**Structure**:

- `unit/` - Fast, isolated tests
- `integration/` - Service interaction tests
- `e2e/` - Complete workflow tests
- `results/` - Test outputs

**Rules**:

- All tests under `/tests/`
- Naming: `test_*.py` or `*_test.py`
- Use fixtures from `conftest.py`

### `/docs/` - Documentation

**Purpose**: All project documentation  
**Rules**:

- Markdown format
- Linked from docs/README.md
- Keep updated with code changes

### `/logs/` - Application Logs

**Purpose**: Runtime logs  
**Pattern**: Rotating file logs  
**Rules**:

- Git-ignored
- JSON format in production
- Rotation enabled

### `/data/` - Data Storage

**Purpose**: Database and persistent data  
**Rules**:

- Git-ignored
- Backed up in production
- Migration scripts tracked

## File Naming Conventions

### Python Files

- **Services**: `*_service.py` (e.g., `stock_data_service.py`)
- **Routes**: `*_routes.py` (e.g., `auth_routes.py`)
- **Models**: `*_models.py` (e.g., `data_models.py`)
- **Tests**: `test_*.py` (e.g., `test_models.py`)
- **Config**: Descriptive names (e.g., `settings.py`)

### Documentation

- **Markdown**: Kebab-case (e.g., `api-reference.md`)
- **READMEs**: Always `README.md` (uppercase)

### Configuration

- **Environment**: `.env.example`, `.env` (git-ignored)
- **Docker**: `Dockerfile`, `docker-compose.yml`

## Import Conventions

### Absolute Imports

```python
from config.settings import get_settings
from models.data_models import StockQuote
from services.stock_data_service import StockDataService
```

### Relative Imports (within package)

```python
from .models import StockQuote
from ..core import KiteClient
```

## Adding New Components

### New API Route

1. Create file in `/src/api/`
2. Register in `/src/main.py`
3. Add tests in `/tests/integration/`
4. Document in `/docs/api/api-reference.md`

### New Service

1. Create file in `/src/services/`
2. Add models in `/src/models/`
3. Add unit tests in `/tests/unit/test_services/`
4. Document in `/docs/architecture/services.md`

### New Core Module

1. Create file in `/src/core/`
2. Add tests in `/tests/unit/`
3. Document usage in relevant docs

## Best Practices

1. **No files in root** except allowed: README, requirements, Docker, deploy scripts
2. **All tests in /tests/** with proper structure
3. **All docs in /docs/** and linked from README
4. **Max 300 LOC per file** - split if larger
5. **Use dependency injection** everywhere
6. **Comprehensive logging** to files
7. **No hardcoded values** - use config
