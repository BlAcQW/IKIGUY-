# Core Backend Testing Guide

**Purpose**: Comprehensive guide for testing in @apps/core_backend/ following TEST_SUITE_ANALYSIS.md recommendations.

**Standards**: All new features MUST follow this guide
**Target Coverage**: 80%+ with real database tests (not mocks)
**Last Updated**: 2025-10-26

---

## Table of Contents

1. [Testing Philosophy](#testing-philosophy)
2. [Test Types](#test-types)
3. [Running Tests](#running-tests)
4. [Writing Tests](#writing-tests)
5. [Test Database Setup](#test-database-setup)
6. [Coverage Requirements](#coverage-requirements)
7. [CI/CD Integration](#cicd-integration)
8. [Common Patterns](#common-patterns)
9. [Troubleshooting](#troubleshooting)

---

## Testing Philosophy

### Core Principles

1. **Real Database Tests** - Use actual MongoDB, not mocks
2. **Test Shared Library Integration** - Every import from @apps/shared/ must be tested
3. **High Coverage** - Target 80%+, measure with pytest-cov
4. **Fast Feedback** - Tests run on every commit via CI/CD
5. **Automatic Cleanup** - Tests clean up their own data

### Why This Matters

- **Breaking Changes Detection**: Shared library changes are caught immediately
- **Confidence**: Real database tests catch schema/index issues
- **Documentation**: Tests serve as usage examples
- **Regression Prevention**: High coverage prevents bugs from returning

---

## Test Types

### 1. Unit Tests

**Purpose**: Test individual functions/methods in isolation
**Marker**: `@pytest.mark.unit`
**Speed**: Fast (< 1 second per test)

```python
@pytest.mark.unit
def test_validation_logic():
    service = YourService()
    assert service.validate({"id": "123"}) is True
```

### 2. Integration Tests

**Purpose**: Test component interactions
**Marker**: `@pytest.mark.integration`
**Speed**: Medium (1-5 seconds per test)

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_service_with_dependencies():
    service = YourService()
    result = await service.execute_workflow(data)
    assert result["status"] == "success"
```

### 3. Database Tests

**Purpose**: Test actual CRUD operations against real MongoDB
**Marker**: `@pytest.mark.database`
**Speed**: Slow (2-10 seconds per test)
**CRITICAL**: Always use test database, always cleanup

```python
@pytest.mark.database
@pytest.mark.asyncio
async def test_crud_operations():
    service = YourService()

    # CREATE
    created = await service.create({"name": "Test"})
    assert created["id"] is not None

    # READ
    fetched = await service.get(created["id"])
    assert fetched["name"] == "Test"

    # UPDATE
    updated = await service.update(created["id"], {"name": "Updated"})
    assert updated["name"] == "Updated"

    # DELETE
    await service.delete(created["id"])

    # VERIFY DELETED
    deleted = await service.get(created["id"])
    assert deleted is None
```

### 4. Shared Library Integration Tests

**Purpose**: Verify @apps/shared/ imports work correctly
**Marker**: `@pytest.mark.integration`
**Location**: `tests/test_shared_library_integration.py`

```python
@pytest.mark.integration
def test_wallet_service_integration():
    from apps.shared.integration.wallet import WalletService

    # Verify expected interface
    assert hasattr(WalletService, 'create_wallet')
    assert hasattr(WalletService, 'get_balance')
```

### 5. API Endpoint Tests

**Purpose**: Test HTTP endpoints
**Marker**: `@pytest.mark.integration`

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_endpoint(client, auth_header):
    response = await client.post(
        "/api/endpoint",
        json={"name": "Test"},
        headers=auth_header
    )
    assert response.status_code == 201
```

---

## Running Tests

### Local Development

```bash
cd /opt/kasaai/apps/core_backend

# Run all tests
export PYTHONPATH=/opt/kasaai
POSTGRES_PASSWORD="aawwER444444" \
MONGODB_URL="mongodb://admin:aawwER444444@127.0.0.1:27017/kasaai_core_test?authSource=admin" \
/opt/kasaai/apps/venv/bin/python -m pytest tests/ -v

# Run specific test types
pytest tests/ -m unit -v           # Only unit tests
pytest tests/ -m integration -v    # Only integration tests
pytest tests/ -m database -v       # Only database tests

# Run specific file
pytest tests/test_wallet_service.py -v

# Run with coverage
pytest tests/ --cov=backend --cov-report=html --cov-report=term

# Run shared library integration tests
pytest tests/test_shared_library_integration.py -v
```

### Using Test Runner

```bash
# Run all tests
python test_runner.py

# Run specific types
python test_runner.py --unit
python test_runner.py --integration
python test_runner.py --e2e
```

### Quick Tests (Fast Feedback)

```bash
# Run only fast tests (unit + small integration)
pytest tests/ -m "not slow" -v

# Run tests for specific feature
pytest tests/ -k "wallet" -v
```

---

## Writing Tests

### Step 1: Use the Template

Copy `tests/TEST_TEMPLATE.md` and fill in your feature:

```bash
cp tests/TEST_TEMPLATE.md tests/test_your_feature.py
```

### Step 2: Write Tests BEFORE Code (TDD)

1. Write failing tests for your feature
2. Implement the feature
3. Tests should pass
4. Refactor with confidence

### Step 3: Follow the Pattern

```python
"""
Tests for [Your Feature].

Author: [Your Name]
Date: [Date]
Priority: [CRITICAL/HIGH/MEDIUM/LOW]

Test Coverage:
- Unit tests: [description]
- Integration tests: [description]
- Database tests: [description]
"""

import pytest
from backend.services.your_service import YourService

# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def sample_data():
    return {"id": "test_123", "name": "Test"}

# =============================================================================
# UNIT TESTS
# =============================================================================

class TestYourServiceUnit:
    @pytest.mark.unit
    def test_something(self, sample_data):
        service = YourService()
        result = service.process(sample_data)
        assert result is not None

# =============================================================================
# DATABASE TESTS
# =============================================================================

class TestYourServiceDatabase:
    @pytest.mark.database
    @pytest.mark.asyncio
    async def test_crud_create(self):
        service = YourService()

        # CREATE
        created = await service.create({"name": "Test"})

        # VERIFY
        assert created["id"] is not None

        # CLEANUP
        await service.delete(created["id"])
```

### Step 4: Test Shared Library Integration

If you use ANY import from `@apps/shared/`, add a test:

```python
@pytest.mark.integration
def test_shared_library_import():
    try:
        from apps.shared.integration.your_dependency import YourClass
        assert YourClass is not None
    except ImportError as e:
        pytest.fail(f"Failed to import from shared library: {e}")
```

---

## Test Database Setup

### CRITICAL: Always Use Test Database

```bash
# NEVER use production database for tests!
# ALWAYS use kasaai_core_test database

# Test database URL
MONGODB_URL="mongodb://admin:aawwER444444@127.0.0.1:27017/kasaai_core_test?authSource=admin"
```

### Setup Test Database

```bash
# Create test database (run once)
mongosh "mongodb://admin:aawwER444444@127.0.0.1:27017/kasaai_core_test?authSource=admin"

# Verify test database
mongosh "mongodb://admin:aawwER444444@127.0.0.1:27017/kasaai_core_test?authSource=admin" --eval "db.getName()"
```

### Cleanup Pattern (REQUIRED)

```python
@pytest.mark.database
@pytest.mark.asyncio
async def test_with_cleanup():
    service = YourService()

    # CREATE test data
    created = await service.create({"name": "Test"})
    created_id = created["id"]

    try:
        # RUN your test
        result = await service.do_something(created_id)
        assert result is not None

    finally:
        # ALWAYS cleanup (even if test fails)
        await service.delete(created_id)
```

---

## Coverage Requirements

### Minimum Thresholds

- **Overall**: 80%+ coverage required
- **New Features**: 90%+ coverage required
- **Critical Paths**: 100% coverage required

### Measuring Coverage

```bash
# Generate coverage report
pytest tests/ --cov=backend --cov-report=html --cov-report=term

# View HTML report
open htmlcov/index.html

# Fail if coverage < 80%
pytest tests/ --cov=backend --cov-fail-under=80
```

### Coverage Configuration

```ini
# pytest.ini
[pytest]
addopts =
    --cov=backend
    --cov=apps.shared
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=80
```

---

## CI/CD Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/test.yml
name: Test Suite
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    services:
      mongodb:
        image: mongo:7
        env:
          MONGO_INITDB_ROOT_USERNAME: admin
          MONGO_INITDB_ROOT_PASSWORD: aawwER444444
        ports:
          - 27017:27017
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.11
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run Unit Tests
        run: pytest tests/ -m unit -v
      - name: Run Integration Tests
        run: pytest tests/ -m integration -v
      - name: Run Shared Library Tests (CRITICAL)
        run: pytest tests/test_shared_library_integration.py -v
      - name: Check Coverage
        run: pytest tests/ --cov=backend --cov-fail-under=80
```

### Pre-Commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: pytest
        name: Run tests
        entry: pytest
        language: system
        pass_filenames: false
        args: [tests/, -v, --tb=short]
```

---

## Common Patterns

### Pattern 1: Testing Async Functions

```python
@pytest.mark.asyncio
async def test_async_function():
    result = await async_function()
    assert result is not None
```

### Pattern 2: Testing Exceptions

```python
def test_exception_handling():
    with pytest.raises(ValueError):
        service.invalid_operation()
```

### Pattern 3: Mocking External Services

```python
from unittest.mock import patch, AsyncMock

@pytest.mark.unit
async def test_with_mock():
    with patch('httpx.AsyncClient.post', new=AsyncMock(return_value=mock_response)):
        result = await service.call_external_api()
        assert result is not None
```

### Pattern 4: Parametrized Tests

```python
@pytest.mark.parametrize("input,expected", [
    ("test1", "result1"),
    ("test2", "result2"),
    ("test3", "result3"),
])
def test_multiple_cases(input, expected):
    assert function(input) == expected
```

### Pattern 5: Testing Database Transactions

```python
@pytest.mark.database
@pytest.mark.asyncio
async def test_transaction_rollback():
    service = YourService()

    # Start transaction
    async with service.start_transaction() as txn:
        await service.create({"name": "Test"}, txn=txn)

        # Rollback
        await txn.rollback()

    # Verify rollback worked
    items = await service.list()
    assert len(items) == 0
```

---

## Troubleshooting

### Issue: Tests fail with "No module named 'apps.shared'"

**Solution**:
```bash
export PYTHONPATH=/opt/kasaai
```

### Issue: Database tests interfere with each other

**Solution**: Ensure proper cleanup in each test
```python
try:
    # test code
finally:
    # ALWAYS cleanup
    await service.delete(created_id)
```

### Issue: Async tests not running

**Solution**: Add `@pytest.mark.asyncio` decorator
```python
@pytest.mark.asyncio
async def test_async():
    ...
```

### Issue: Coverage not tracking shared library

**Solution**: Add `--cov=apps.shared` flag
```bash
pytest tests/ --cov=backend --cov=apps.shared
```

### Issue: Tests are too slow

**Solution**: Run only fast tests in development
```bash
pytest tests/ -m "unit" -v  # Run only fast unit tests
```

---

## Quick Reference Card

```bash
# ============================================================
# TESTING QUICK REFERENCE
# ============================================================

# Run all tests
pytest tests/ -v

# Run by type
pytest tests/ -m unit -v
pytest tests/ -m integration -v
pytest tests/ -m database -v

# Run with coverage
pytest tests/ --cov=backend --cov-report=html

# Run shared library integration tests (CRITICAL!)
pytest tests/test_shared_library_integration.py -v

# Run specific file
pytest tests/test_your_feature.py -v

# Run specific test
pytest tests/test_your_feature.py::TestClass::test_method -v

# Run with test database
MONGODB_URL="mongodb://admin:aawwER444444@127.0.0.1:27017/kasaai_core_test?authSource=admin" \
pytest tests/ -v

# Fail if coverage < 80%
pytest tests/ --cov=backend --cov-fail-under=80
```

---

## Resources

- **TEST_SUITE_ANALYSIS.md** - Comprehensive test suite analysis
- **TEST_TEMPLATE.md** - Template for new test files
- **test_shared_library_integration.py** - Example of shared library tests
- **conftest.py** - Shared fixtures and configuration

---

**Remember**: Tests are not optional. Every new feature MUST have:
1. ✅ Unit tests
2. ✅ Integration tests
3. ✅ Real database CRUD tests (not mocks!)
4. ✅ Shared library integration tests (if applicable)
5. ✅ 80%+ coverage

**Enforce in CI/CD**: PRs are blocked if:
- ❌ Tests fail
- ❌ Coverage < 80%
- ❌ Shared library integration tests fail

---

**Last Updated**: 2025-10-26
**Next Review**: After implementing CI/CD pipeline (Phase 7.4)
