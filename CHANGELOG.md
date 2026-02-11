# Changelog

All notable changes to Kite Services will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Integration docs: `docs/INTEGRATION_GUIDE.md` (consolidated) and `docs/integration/` (per-service: auth, market-data, analysis, trading)
- Request/response Pydantic models for all endpoints (master rule compliance):
  - `LoginUrlResponse` for GET `/auth/login-url`
  - `UpdateTokenRequest` for PUT `/auth/token` (body-based)
  - `ContextExamplesResponse` for GET `/context/examples`
  - `StockAnalysisRequest` for POST `/analysis/stock` (body-based)
- Extracted `analysis_enhanced_cache.py` (cache keys) and `analysis_enhanced_helpers.py` (scoring, quality)

### Changed

- PUT `/auth/token` now accepts JSON body instead of query params
- POST `/analysis/stock` now accepts JSON body (`StockAnalysisRequest`) instead of query params
- Refactored analysis_enhanced to use shared cache and helper modules
- Updated `docs/api.md` for PUT `/auth/token` request body

### Removed

- `docs/PRODUCTION_DEPLOYMENT.md` (redundant)
- `docs/api-integration-doc.md`, `api-integration-guide.md`, `API_INTEGRATION_GUIDE_PRODUCTION.md`, `API_QUICK_REFERENCE.md` (replaced by INTEGRATION_GUIDE.md and integration/)

### Fixed

- Restored `StockIntelligence` import in `analysis.py` (broken by earlier refactor)
- Database: resolve relative SQLite paths (e.g. `./data/`) from project cwd; added `greenlet` for SQLAlchemy async
- **Production deployment (VM)**: Resolved SQLite "unable to open database file" crash loop
  - Use `DATABASE_URL` from `os.environ` (pydantic-settings nested models don't pass env in Docker)
  - Use `SERVICE_PORT` and `REDIS_HOST` from env for correct Docker networking
  - Added `*` to TrustedHostMiddleware for external access
  - Use `/tmp` for SQLite when `/app/data` has permission issues

### Added

- ✅ Comprehensive test infrastructure in `/tests/` directory
  - Unit tests for models and services
  - Integration tests for API endpoints
  - End-to-end workflow tests
  - Test fixtures and configuration
- ✅ Complete documentation suite in `/docs/`
  - `architecture.md` - System architecture and design
  - `folder-structure.md` - Project organization guide
  - `apis-used.md` - External API documentation
  - `api.md` - Complete API reference
  - `services.md` - Services documentation
  - `config.md` - Configuration guide
  - `refactoring-plan.md` - Code quality improvement plan
  - `/tests/README.md` - Testing documentation
- ✅ Database module implementation (`src/core/database.py`)
  - Async SQLAlchemy support
  - Connection pooling
  - Session management
- ✅ UI components organized in `/src/ui/token/`
- ✅ Example files organized in `/docs/examples/`
- ✅ Proper `.env.example` at project root

### Changed

- ✅ Reorganized file structure to comply with workspace rules
  - Moved test files from root to `/tests/` directory
  - Moved UI files to `/src/ui/` directory
  - Moved example files to `/docs/examples/`
  - Consolidated environment configuration
- ✅ Registered `ui_market_routes` in main application
- ✅ Updated `main.py` to use database initialization
- ✅ Marked oversized files with deprecation notices
- ✅ Improved import organization in `main.py`

### Removed

- ✅ Redundant deployment scripts (consolidated to single `deploy.sh`)
- ✅ Redundant startup scripts (using `main.py` as single entry point)
- ✅ Duplicate Dockerfiles (5 removed, kept 2: production and dev)
- ✅ Orphaned API routes (9 unregistered route files)
  - `market_sentiment_routes.py`
  - `unified_trading_api.py`
  - `intraday_demo_routes.py`
  - `intraday_trading_routes.py`
  - `swing_trading_routes.py`
  - `data_quality_routes.py`
  - `ml_market_intelligence_routes.py`
  - `enhanced_market_context_routes.py`
- ✅ Orphaned services (5 unused service files)
  - `enhanced_market_context_service.py`
  - `ml_market_intelligence_service.py`
  - `market_sentiment_service.py`
  - `simple_real_data_service.py`
  - `market_context_creator.py`
- ✅ Orphaned models (4 unused model files)
  - `enhanced_market_context_models.py`
  - `ml_friendly_market_models.py`
  - `unified_seed_model.py`
  - `unified_trading_models.py`
- ✅ Orphaned core modules (4 unused modules)
  - `optimized_data_collector.py`
  - `intraday_signal_engine.py`
  - `data_quality_validator.py`
  - `pipeline_stability.py`
- ✅ Redundant token management scripts (6 files consolidated into services)
  - `check_token_status.py`
  - `find_existing_token.py`
  - `generate_token_from_request.py`
  - `get_fresh_token.py`
  - `setup_kite_auth.py`
  - `kite_token_manager.py`
- ✅ Root-level status files
  - `FINAL_STATUS.md` (information consolidated into docs)
  - `env.prod.example` (using single `.env.example`)

### Deprecated

- ⚠️ `/api/market/legacy` routes (formerly `/api/market`)
  - File: `src/api/market_routes.py` (1281 LOC)
  - Use `market_context_routes.py` and `stock_data_routes.py` instead
  - Scheduled for removal after migration

### Fixed

- ✅ File placement compliance with workspace rules
  - All tests now in `/tests/` directory
  - All documentation in `/docs/` directory
  - Root directory cleaned of non-allowed files
- ✅ Import paths updated for reorganized files
- ✅ Database integration properly configured

## [1.0.0] - 2024-01-15

### Initial Release

**Core Features:**

- Real-time stock data API via Kite Connect
- Market context and intelligence service
- Global market data via Yahoo Finance
- Token management for Kite Connect OAuth
- WebSocket support for real-time streaming
- Docker containerization
- Production deployment ready

**API Endpoints:**

- `/health` - Health check
- `/api/stock-data/*` - Stock data operations
- `/api/market-context/*` - Market intelligence
- `/api/auth/*` - Authentication
- `/api/token/*` - Token management
- `/ws/*` - WebSocket endpoints

**Documentation:**

- Complete API documentation
- Kite Connect setup guide
- Production deployment guide
- Stock data service guide
- Market context service guide

---

## Migration Guide

### For Users of Deleted Routes

If you were using any of the following endpoints, please migrate:

#### Market Sentiment → Market Context

```python
# Old (Deleted)
GET /api/market-sentiment

# New
GET /api/market-context-data/quick-context
```

#### Enhanced Market Context → Unified Market Context

```python
# Old (Deleted)
GET /api/v2/market-context

# New
GET /api/market-context/full
```

#### ML Market Intelligence → Market Intelligence

```python
# Old (Deleted)
GET /api/v3/market-intelligence

# New
GET /api/intelligence/market-intelligence
```

### For Developers

#### Test Files

All tests moved to `/tests/`. Update your test runners:

```bash
# Old
python test_stock_data_service.py

# New
pytest tests/integration/test_stock_data_service.py
```

#### Import Paths

If you were importing from deleted modules, use these alternatives:

```python
# Deleted: services.enhanced_market_context_service
# Use: services.market_context_service

# Deleted: models.ml_friendly_market_models
# Use: models.market_intelligence_models

# Deleted: models.unified_trading_models
# Use: models.consolidated_models
```

---

## Code Quality Improvements

### Files Refactored

- None in this release (documented in refactoring plan)

### Files Scheduled for Refactoring

See `/docs/refactoring-plan.md` for:

- 4 files >1000 LOC
- 5 files 700-1000 LOC
- 8 files 500-700 LOC
- 10+ files 300-500 LOC

### Test Coverage

- Unit tests: 15+ test files
- Integration tests: 3 test files
- E2E tests: 1 test file
- Target coverage: >70%

---

## Breaking Changes

### Removed Endpoints

The following endpoints were removed (never documented or in production):

- All `/api/v2/*` endpoints
- All `/api/v3/*` endpoints
- `/api/market-sentiment`
- `/api/data-quality/*`
- `/api/swing-trading/*`
- `/api/intraday-trading/*` (use `/api/intraday` instead)

### File Relocations

- Test files: Root → `/tests/`
- UI files: Root → `/src/ui/`
- Example files: Root → `/docs/examples/`

**Impact**: None for end users. Developers need to update import paths and test commands.

---

## Security

### Fixed

- No hardcoded credentials in source code
- Proper .gitignore for sensitive files
- Database credentials via environment variables

### Added

- Security best practices documentation
- Environment variable validation

---

## Performance

### Improved

- Removed unused code (~5000 LOC deleted)
- Faster startup (fewer modules to load)
- Reduced Docker image size (fewer dependencies)

---

## Notes

This release represents a major cleanup and reorganization of the codebase to comply with workspace rules and best practices. All functionality remains intact through the new, properly organized endpoints.

For questions or issues, please refer to:

- `/docs/README.md` - Documentation index
- `/docs/architecture.md` - System architecture
- `/docs/api.md` - API reference
