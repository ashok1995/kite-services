# System Architecture

## Overview

Kite Services is a production-grade stock market data and intelligence service built with FastAPI, following clean architecture principles.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    API Layer (FastAPI)                  │
│  ┌──────────┬─────────────┬──────────────┬──────────┐  │
│  │  Auth    │  Stock Data │ Market       │ WebSocket│  │
│  │  Routes  │  Routes     │ Context      │ Routes   │  │
│  └──────────┴─────────────┴──────────────┴──────────┘  │
└─────────────────────────────────────────────────────────┘
                           │
┌─────────────────────────────────────────────────────────┐
│                    Service Layer                        │
│  ┌──────────────────────────────────────────────────┐  │
│  │ StockDataService │ MarketContextService │ etc    │  │
│  │ (Business Logic - Stateless, Reusable)           │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                           │
┌─────────────────────────────────────────────────────────┐
│                     Core Layer                          │
│  ┌──────────────┬─────────────┬──────────────────────┐ │
│  │ KiteClient   │ DBManager   │  Logging/Validation  │ │
│  └──────────────┴─────────────┴──────────────────────┘ │
└─────────────────────────────────────────────────────────┘
                           │
┌─────────────────────────────────────────────────────────┐
│               External Dependencies                     │
│  ┌────────────────┬──────────────┬─────────────────┐   │
│  │ Kite Connect   │ Yahoo Finance│  Database       │   │
│  └────────────────┴──────────────┴─────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

## Key Components

### 1. API Layer (`src/api/`)
- **Responsibility**: HTTP endpoints, request/response handling
- **Pattern**: Thin controllers - delegate to services
- **Key Files**:
  - `auth_routes.py` - Authentication and token management
  - `stock_data_routes.py` - Real-time and historical stock data
  - `market_context_routes.py` - Market intelligence endpoints
  - `consolidated_routes.py` - Consolidated market data
  - `websocket_routes.py` - Real-time WebSocket streaming

### 2. Service Layer (`src/services/`)
- **Responsibility**: Business logic, data orchestration
- **Pattern**: Stateless services with dependency injection
- **Key Services**:
  - `StockDataService` - Stock quote and historical data
  - `MarketContextService` - Market analysis and intelligence
  - `ConsolidatedMarketService` - Multi-source data aggregation
  - `YahooFinanceService` - Yahoo Finance integration
  - `KiteAuthService` - Kite Connect authentication

### 3. Core Layer (`src/core/`)
- **Responsibility**: Low-level utilities, clients, infrastructure
- **Key Components**:
  - `KiteClient` - Kite Connect API client
  - `DBManager` - Database operations
  - `ServiceManager` - Service lifecycle management
  - `logging_config.py` - Centralized logging

### 4. Models Layer (`src/models/`)
- **Responsibility**: Data contracts, validation
- **Pattern**: Pydantic models for type safety
- **Key Models**:
  - `data_models.py` - Stock data models
  - `market_context_models.py` - Market context models
  - `consolidated_models.py` - Consolidated response models

### 5. Configuration (`src/config/`)
- **Responsibility**: Environment-based configuration
- **Pattern**: Pydantic Settings with env var support
- **Key Files**:
  - `settings.py` - All service configuration

## Design Principles

### 1. Separation of Concerns
- **Routes**: Handle HTTP, validate input, return responses
- **Services**: Implement business logic
- **Core**: Provide infrastructure and utilities

### 2. Dependency Injection
- Services receive dependencies via constructor
- No global state or singletons (except configuration)
- Easy to test and mock

### 3. Stateless Design
- Services don't maintain state between requests
- All state in database or external systems
- Horizontally scalable

### 4. Clean Error Handling
- Global exception handlers
- Structured error responses
- Comprehensive logging

### 5. Configuration-Driven
- No hardcoded values
- Environment-based configuration
- Easy deployment across environments

## Data Flow

### Example: Real-time Stock Data Request

```
1. Client Request
   ↓
2. API Route (stock_data_routes.py)
   - Validate request
   - Generate request ID
   ↓
3. Service (StockDataService)
   - Business logic
   - Call KiteClient
   ↓
4. Core (KiteClient)
   - API call to Kite Connect
   - Handle errors
   ↓
5. Response Path (reverse)
   - Transform data
   - Add metadata
   - Return to client
```

## Technology Stack

- **Framework**: FastAPI 0.104+
- **Python**: 3.11+
- **API Clients**: kiteconnect, yfinance
- **Database**: SQLite (dev), PostgreSQL (prod capable)
- **Logging**: structlog (JSON logging)
- **Validation**: Pydantic v2
- **ASGI Server**: Uvicorn
- **Containerization**: Docker

## Scalability Considerations

### Current Design
- Single process (development)
- In-memory caching
- SQLite database

### Production Scaling
- Multiple workers (Uvicorn)
- Redis for caching and sessions
- PostgreSQL for persistence
- Load balancer (nginx/traefik)
- Horizontal scaling via Docker/Kubernetes

## Security

### Authentication
- Kite Connect OAuth flow
- Token-based authentication
- Secure credential storage

### API Security
- CORS middleware
- Rate limiting (configured)
- Input validation (Pydantic)
- No sensitive data in logs

## Monitoring

### Logging
- Structured JSON logs
- Request/response logging
- Error tracking
- Performance metrics

### Health Checks
- `/health` endpoint
- Service status monitoring
- Dependency health checks

## Deployment

### Development
```bash
python src/main.py
```

### Production (Docker)
```bash
docker build -t kite-services .
docker run -p 8179:8179 kite-services
```

## Future Enhancements

1. **Caching Layer**: Redis integration
2. **Message Queue**: Celery for background tasks
3. **Database**: Full ORM with migrations
4. **Monitoring**: Prometheus metrics
5. **WebSocket**: Complete real-time streaming
6. **Authentication**: JWT tokens, API keys

