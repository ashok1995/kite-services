# Code Refactoring Plan

## Overview

Several files currently exceed the 300 LOC limit defined in workspace rules. This document outlines the refactoring plan.

## Files Requiring Refactoring

### Critical (>1000 LOC)

1. **`src/api/market_routes.py`** (1281 lines)  
   - **Status**: Marked as DEPRECATED/LEGACY
   - **Registered as**: `/api/market/legacy`
   - **Plan**: Functionality already migrated to `market_context_routes.py` and `stock_data_routes.py`
   - **Action**: Schedule for deletion after verifying no dependencies

2. **`src/services/intraday_context_service.py`** (1285 lines)  
   - **Plan**: Split into:
     - `intraday_analysis_service.py` - Core analysis logic
     - `intraday_indicators_service.py` - Technical indicators
     - `intraday_signals_service.py` - Signal generation
   - **Priority**: Medium (currently working)

3. **`src/services/market_intelligence_service.py`** (1269 lines)  
   - **Plan**: Split into:
     - `market_intelligence_core.py` - Core intelligence
     - `market_regime_analyzer.py` - Regime detection
     - `sector_analyzer.py` - Sector rotation analysis
   - **Priority**: Medium (currently working)

4. **`src/services/kite_realtime_service.py`** (1019 lines)  
   - **Plan**: Split into:
     - `kite_websocket_client.py` - WebSocket connection
     - `kite_tick_processor.py` - Tick processing
     - `kite_subscription_manager.py` - Subscription management
   - **Priority**: Low (experimental feature)

### High Priority (700-1000 LOC)

5. **`src/models/market_context_models.py`** (732 lines)  
   - **Plan**: Split by domain:
     - `market_regime_models.py`
     - `market_breadth_models.py`
     - `sector_models.py`
   - **Priority**: Low (models are acceptable to be larger)

6. **`src/api/market_context_routes.py`** (721 lines)  
   - **Plan**: Already well-structured, acceptable for now
   - **Priority**: Low

7. **`src/api/intelligence_routes.py`** (673 lines)  
   - **Plan**: Consolidate with market_context_routes.py
   - **Priority**: Medium

8. **`src/services/consolidated_market_service.py`** (665 lines)  
   - **Plan**: Extract data aggregation logic into separate utilities
   - **Priority**: Medium

### Medium Priority (500-700 LOC)

9. **`src/api/intraday_routes.py`** (612 lines)  
   - **Plan**: Keep as-is, well-structured
   - **Priority**: Low

10. **`src/core/talib_technical_analysis.py`** (516 lines)  
    - **Plan**: Split by indicator type (trend, momentum, volatility)
    - **Priority**: Low

### Lower Priority (300-500 LOC)

Files in 300-500 LOC range are acceptable but should not grow larger:
- `src/models/intraday_context_models.py` (497)
- `src/services/stock_data_service.py` (484)
- `src/core/technical_analysis.py` (483)
- `src/api/consolidated_routes.py` (471)
- `src/api/auth_routes.py` (450)
- `src/services/yahoo_finance_service.py` (449)
- etc.

## Refactoring Strategy

### Phase 1: Mark Legacy Code
✅ COMPLETED
- Mark deprecated files with warnings
- Update routing to use /legacy prefix
- Document migration path

### Phase 2: Prevent Growth (Immediate)
- Add LOC check to CI/CD
- Require approval for files >300 LOC
- Document refactoring plan for existing violations

### Phase 3: Incremental Refactoring
- Refactor one file per sprint
- Start with files causing most maintenance issues
- Maintain backward compatibility during migration

### Phase 4: Remove Legacy
- Delete deprecated code after migration complete
- Update all documentation
- Remove legacy routes

## Refactoring Guidelines

### When Splitting Files

1. **By Responsibility**
   ```
   service.py (1000 LOC)
   → core_service.py (200 LOC)
   → data_fetcher.py (150 LOC)
   → analyzer.py (180 LOC)
   → formatter.py (100 LOC)
   ```

2. **By Domain**
   ```
   models.py (700 LOC)
   → request_models.py
   → response_models.py
   → internal_models.py
   ```

3. **By Feature**
   ```
   routes.py (600 LOC)
   → basic_routes.py
   → advanced_routes.py
   → admin_routes.py
   ```

### Testing During Refactoring

1. Ensure all tests pass before refactoring
2. Don't change logic during split
3. Verify tests pass after split
4. Add integration tests if needed

### Documentation During Refactoring

1. Update imports in all dependent files
2. Update API documentation
3. Update architecture diagrams
4. Add migration notes to CHANGELOG

## Timeline

- **Immediate**: Mark legacy code (DONE)
- **Q1 2025**: Refactor top 3 critical files
- **Q2 2025**: Refactor high priority files  
- **Q3 2025**: Remove all deprecated code
- **Q4 2025**: All files <300 LOC

## Monitoring

Track refactoring progress in:
- `/tests/results/code_quality_report.md`
- Sprint planning documents
- This file (update as refactoring completes)

## Notes

- Some files (like comprehensive model files) may be acceptable >300 LOC if well-structured
- Priority is on maintainability, not strict LOC count
- All new code must be <300 LOC
- Legacy code addressed incrementally

