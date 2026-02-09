# Test Reliability & Mandatory Testing

## Overview

All tests are **MANDATORY** and **BLOCKING** for production deployments. No code can be deployed to production without passing all test suites.

## Test Requirements by Branch

### Main/Master Branch (Production)

**ALL tests must pass before deployment:**

1. ✅ **Unit Tests** - Component-level tests
2. ✅ **Integration Tests** - Service integration tests
3. ✅ **E2E Tests** - End-to-end workflow tests
4. ✅ **Production Config Tests** - Configuration validation
5. ✅ **Deployment Reliability Tests** - 27 comprehensive tests

**If ANY test fails → Deployment is BLOCKED**

### Develop Branch

**ALL tests must pass before image build:**

1. ✅ **Unit Tests**
2. ✅ **Integration Tests**
3. ✅ **E2E Tests**
4. ✅ **Production Config Tests**

**If ANY test fails → Image build is BLOCKED**

### Feature Branches

**Tests run but don't block (for development feedback):**

1. ✅ **Unit Tests**
2. ✅ **Integration Tests**
3. ✅ **E2E Tests**

## Test Coverage Requirements

### Minimum Coverage Threshold

- **Unit Tests**: Minimum 70% code coverage
- **Integration Tests**: All critical paths covered
- **E2E Tests**: All endpoints tested

### Coverage Reports

Coverage reports are generated and uploaded:
- XML format for CI/CD integration
- HTML format for detailed review
- Available as artifacts in GitHub Actions

## Test Stages in CI/CD

### Stage 1: Lint ✅
- Code quality checks
- Syntax validation
- **Blocks**: Next stages if fails

### Stage 2: Unit Tests ✅ (MANDATORY)
- Component tests
- Coverage reporting
- Coverage threshold check (70%)
- **Blocks**: Integration tests if fails

### Stage 3: Integration Tests ✅ (MANDATORY)
- Service integration
- Redis connectivity
- API interactions
- **Blocks**: E2E tests if fails

### Stage 4: E2E Tests ✅ (MANDATORY)
- End-to-end workflows
- Production config validation
- Deployment reliability (27 tests)
- **Blocks**: Image build if fails

### Stage 5: Build Image
- **Requires**: All tests passed
- Builds Docker image
- Pushes to registry

### Stage 6: Test Image (develop only)
- **Requires**: All tests passed + image built
- Runs container
- Tests health endpoint

### Stage 7: Deploy Production (main only)
- **Requires**: ALL tests passed + image built
- Verifies test results before deployment
- Deploys to production
- Runs post-deployment smoke tests

## Test Verification Before Deployment

The deployment stage explicitly verifies all test results:

```yaml
- name: Verify all tests passed before deployment
  run: |
    if [ "${{ needs.unit-tests.result }}" != "success" ] || \
       [ "${{ needs.integration-tests.result }}" != "success" ] || \
       [ "${{ needs.e2e-tests.result }}" != "success" ]; then
      echo "❌ One or more test stages failed. Deployment blocked."
      exit 1
    fi
```

## Test Suites

### 1. Unit Tests (`tests/unit/`)
- Component isolation
- Fast execution
- High coverage
- **Location**: `tests/unit/`

### 2. Integration Tests (`tests/integration/`)
- Service interactions
- Database operations
- External API mocking
- **Location**: `tests/integration/`

### 3. E2E Tests (`tests/e2e/`)
- Complete workflows
- API endpoint testing
- Production readiness
- **Location**: `tests/e2e/`

### 4. Production Config Tests
- Environment variable parsing
- Configuration validation
- Production-specific checks
- **File**: `tests/e2e/test_production_config.py`

### 5. Deployment Reliability Tests
- 27 comprehensive tests
- Smoke tests
- Data contract validation
- Error handling
- **File**: `tests/e2e/test_deployment_reliability.py`

## Running Tests Locally

### Run All Tests
```bash
poetry run pytest
```

### Run Specific Suite
```bash
# Unit tests
poetry run pytest tests/unit/

# Integration tests
poetry run pytest tests/integration/

# E2E tests
poetry run pytest tests/e2e/

# Production config tests
poetry run pytest tests/e2e/test_production_config.py

# Deployment reliability tests
poetry run pytest tests/e2e/test_deployment_reliability.py
```

### With Coverage
```bash
poetry run pytest --cov=src --cov-report=html --cov-report=term
```

## Test Failures

### If Tests Fail in CI/CD

1. **Pipeline stops** - No further stages run
2. **Deployment blocked** - Production deployment cancelled
3. **Notification sent** - GitHub sends failure notification
4. **Fix required** - Must fix tests before retry

### Fixing Test Failures

1. Check test logs in GitHub Actions
2. Run tests locally to reproduce
3. Fix the issue
4. Commit and push
5. Pipeline re-runs automatically

## Test Best Practices

### 1. Write Tests First (TDD)
- Write tests before implementation
- Ensures code meets requirements

### 2. Keep Tests Fast
- Unit tests: < 1 second each
- Integration tests: < 5 seconds each
- E2E tests: < 30 seconds each

### 3. Test Edge Cases
- Invalid inputs
- Error conditions
- Boundary values

### 4. Maintain Coverage
- Aim for > 80% coverage
- Minimum 70% required
- Focus on critical paths

### 5. Update Tests with Code
- Don't skip failing tests
- Fix tests when behavior changes
- Add tests for new features

## Monitoring Test Results

### GitHub Actions
- View test results in Actions tab
- See which tests failed
- Download coverage reports

### Coverage Reports
- HTML reports available as artifacts
- View detailed coverage by file
- Identify untested code

### Test Summary
Each pipeline run shows:
- Total tests run
- Tests passed
- Tests failed
- Coverage percentage

## Continuous Improvement

### Regular Test Reviews
- Review test coverage monthly
- Identify gaps
- Add missing tests

### Test Performance
- Monitor test execution time
- Optimize slow tests
- Parallelize where possible

### Test Quality
- Ensure tests are meaningful
- Remove flaky tests
- Update outdated tests

## Summary

✅ **All tests are mandatory for production**
✅ **Tests block deployment if they fail**
✅ **Coverage threshold enforced (70% minimum)**
✅ **Multiple test suites ensure reliability**
✅ **Production config tests catch deployment issues**

**No code reaches production without passing all tests! 🛡️**
