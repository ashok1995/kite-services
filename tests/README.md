# Test Suite Documentation

## Overview

Comprehensive test suite for Kite Services following industry best practices.

## Structure

```
tests/
├── unit/           # Unit tests for individual components
│   ├── test_models.py
│   └── test_services/
│       ├── test_yahoo_finance_service.py
│       └── test_market_context_service.py
├── integration/    # Integration tests for API endpoints
│   ├── test_stock_data_service.py
│   ├── test_market_context_service.py
│   └── demo_market_context_calculations.py
├── e2e/           # End-to-end workflow tests
│   ├── test_complete_workflow.py
│   ├── test_deployment_reliability.py   # In-process, full lifecycle
│   ├── test_prod_endpoints.py          # Live URL, all endpoints
│   └── test_production_config.py
├── results/       # Test results and coverage reports
├── conftest.py    # Shared fixtures
└── README.md      # This file
```

## Running Tests

### Run All Tests

```bash
pytest tests/ -v
```

### Run Unit Tests Only

```bash
pytest tests/unit/ -v
```

### Run Integration Tests Only

```bash
pytest tests/integration/ -v
```

### Run E2E Tests Only

```bash
pytest tests/e2e/ -v
```

### Run Production Endpoint Tests (against live URL)

```bash
# Local dev (default: http://127.0.0.1:8079)
pytest tests/e2e/test_prod_endpoints.py -v

# Production VM
TEST_BASE_URL=http://203.57.85.72:8179 pytest tests/e2e/test_prod_endpoints.py -v

# Smoke only
TEST_BASE_URL=http://203.57.85.72:8179 pytest tests/e2e/test_prod_endpoints.py -v -k smoke
```

### Run All Functional + E2E (local + prod endpoint tests)

```bash
# Full suite against dev
TEST_BASE_URL=http://127.0.0.1:8079 poetry run pytest tests/integration/ tests/e2e/test_prod_endpoints.py tests/e2e/test_deployment_reliability.py -v
```

### Run with Coverage

```bash
pytest tests/ --cov=src --cov-report=html --cov-report=term
```

## Test Results

Test results are stored in `/tests/results/`:

- `test_results.json` - JSON format results
- `coverage_report.md` - Coverage summary

## Writing Tests

### Unit Tests

- Test individual functions/classes in isolation
- Use mocks for external dependencies
- Fast execution (<100ms each)

### Integration Tests

- Test service interactions
- May use real services in test environment
- Moderate execution time (<5s each)

### E2E Tests

- Test complete workflows
- Simulate real user scenarios
- Slower execution (<30s each)

## Requirements

All test dependencies are in `requirements.txt`:

- pytest
- pytest-asyncio
- pytest-cov
- httpx (for API testing)

## Best Practices

1. Each test should be independent
2. Use fixtures for common setup
3. Clean up resources in teardown
4. Use descriptive test names
5. Test both success and failure cases
6. Maintain >70% code coverage
