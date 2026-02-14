# Changelog

All notable changes to Kite Services will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **VM checklist** in `docs/deployment/DEPLOY-PROD-VM.md` — kite-credentials path, resource checks (`df -h`, `free -m`, `docker stats`), branch/merge flow for deploy.
- **Market Breadth Calculation** — Real market breadth from Nifty 50 constituents (advance/decline ratio) for Bayesian engine integration
- **MarketBreadthService** — New service with 60-second caching for efficient breadth calculation
- **Nifty 50 Constants** — `src/common/constants.py` with Nifty 50 constituent symbols
- **Batch Quote Limit Increase** — `QUOTES_MAX_SYMBOLS` increased from 50 to 200 (Bayesian engine requirement)
- **Market Breadth Config** — `MARKET_BREADTH_ENABLED` and `MARKET_BREADTH_CACHE_TTL` settings
- **Integration Documentation** — Gap analysis, implementation plan, and complete integration guide for Bayesian engine
- **Comprehensive Testing** — 15 unit tests and 8 integration tests for market breadth service
- **Testing Guide** — Complete testing documentation with manual and automated test procedures
- **Integration Guide** — 680-line comprehensive guide with Python client and cURL examples
- **envs/** — single folder for env config: `development.env`, `staging.env`, `production.env` (no .env.example or scattered .env)
- **KITE_TOKEN_FILE** — store token outside project (`~/.kite-services/kite_token.json` by default) so it survives git pull
- **token_valid** in GET `/api/auth/status` — true only when token verified via Kite API (profile call)
- **Local staging** — staging runs strictly on this machine (port 8279). `scripts/run-staging.sh` and `docs/deployment/local-staging.md`. VM = prod only.
- Master rule: no docs at root of `/docs/` except README.md; all docs in subfolders (`api/`, `architecture/`, `integration/`, `deployment/`, `development/`)
- Integration docs: `docs/integration/INTEGRATION_GUIDE.md` (consolidated) and per-service guides
- Request/response Pydantic models for all endpoints (master rule compliance):
  - `LoginUrlResponse` for GET `/auth/login-url`
  - `UpdateTokenRequest` for PUT `/auth/token` (body-based)
  - `ContextExamplesResponse` for GET `/context/examples`
  - `StockAnalysisRequest` for POST `/analysis/stock` (body-based)
- Extracted `analysis_enhanced_cache.py` (cache keys) and `analysis_enhanced_helpers.py` (scoring, quality)

### Changed

- **Prod deploy** — Entrypoint recognizes token file (prod) vs `KITE_API_KEY`; health check wait extended to 60s with retry loop in `deploy_to_prod.sh`.
- **Dockerfile** — `poetry install --no-root` to avoid project install and README.md requirement in image.
- **Deploy doc** — Section 0 VM checklist, Section 5 branch/deploy flow (feature → develop → main → deploy).
- **Git workflow rule** — Main receives only from develop; staging = run locally with develop (same rigor as prod); merge develop → main via Git UI then deploy.
- **Market Context Breadth** — Market context now uses real Nifty 50 constituent data instead of sector-based approximation
- **Batch Quote Configuration** — Default `QUOTES_MAX_SYMBOLS` changed from 50 to 200 across all environments
- **Token file auto-create**: When missing, create template at `kite-credentials/kite_token.json`. No SCP; add api_key/api_secret via SSH edit after deploy.
- **Docker prod**: Mount `./kite-credentials` → `/root/.kite-services` for token persistence.
- **Kite credentials** in token file only — api_key, api_secret, access_token in `~/.kite-services/kite_token.json`, removed from env files.
- **Env config**: All env in `envs/` only. Removed `.env.example`, `config/production.env`. Settings loads `envs/{ENVIRONMENT}.env`.
- Token storage: default to `~/.kite-services/kite_token.json`; no longer writes to project `access_token.json` or `.env`
- GET `/api/auth/status` verifies token via Kite API; returns `token_valid: true` only when profile call succeeds
- PUT `/auth/token` now accepts JSON body instead of query params
- POST `/analysis/stock` now accepts JSON body (`StockAnalysisRequest`) instead of query params
- Refactored analysis_enhanced to use shared cache and helper modules
- Docs reorganized: all docs moved from `/docs/` root into subfolders (`api/`, `architecture/`, `integration/`, `deployment/`, `development/`). Only `docs/README.md` remains at root as navigation.

### Removed

- `docker-compose.staging.yml` — staging is local-only, no VM staging.
- Legacy docs: API_CONSOLIDATION_COMPLETE, CACHE_STRATEGY_DETAILED, CACHING_AUDIT_KITE_FIRST, CI_CD_PIPELINE, COMPLETE_STATUS, COMPLETE_TOKEN_FLOW, DATA_CONTRACT_V1, ENHANCED_MARKET_CONTEXT, GIT_SETUP, PRE_COMMIT_SETUP, PRE_PRODUCTION_TESTS, PRODUCTION_MONITORING, production-deployment, PROJECT_SUMMARY, QUICK_MONEY_OPPORTUNITIES, REAL_DATA_FEASIBILITY, refactoring-plan, SERVICE_ANALYSIS, stock-data-service, TEST_RELIABILITY, TOKEN_MANAGEMENT, TOKEN_STATUS_API, UNIFIED_API_GUIDE, V3_ML_MARKET_INTELLIGENCE_API_GUIDE, api-testing-guide, dev-server-curl-tests, endpoint-testing-results, market-context-*

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
