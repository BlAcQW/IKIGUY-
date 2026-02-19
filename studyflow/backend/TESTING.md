# StudyFlow Backend - Testing Guide

## Overview

This document provides comprehensive guidance on testing the StudyFlow backend application. Our testing strategy ensures code quality, reliability, and maintainability through automated testing with coverage tracking.

## Table of Contents

1. [Testing Philosophy](#testing-philosophy)
2. [Quick Start](#quick-start)
3. [Test Structure](#test-structure)
4. [Coverage Requirements](#coverage-requirements)
5. [Running Tests](#running-tests)
6. [Writing Tests](#writing-tests)
7. [CI/CD Integration](#cicd-integration)
8. [Coverage Reports](#coverage-reports)
9. [Best Practices](#best-practices)
10. [Troubleshooting](#troubleshooting)

---

## Testing Philosophy

Our testing approach follows these principles:

1. **Quality over Quantity**: Aim for meaningful tests, not just coverage numbers
2. **Fast Feedback**: Unit tests should be fast; integration tests can be slower
3. **Test Pyramid**: More unit tests, fewer integration tests, minimal E2E tests
4. **Real Tests**: No mock implementations - tests should validate actual functionality
5. **Coverage Enforcement**: Minimum 80% code coverage required for all PRs

---

## Quick Start

### Install Dependencies

```bash
cd /opt/kasaai/apps/studyflow/backend
pip install -r requirements.txt
```

### Run All Tests with Coverage

```bash
# Set up environment variables
export PYTHONPATH=/opt/kasaai
export MONGODB_URL="mongodb://admin:password@localhost:27017/studyflow_test?authSource=admin"
export POSTGRES_HOST="localhost"
export POSTGRES_PORT="5432"
export POSTGRES_USER="postgres"
export POSTGRES_PASSWORD="password"
export POSTGRES_DB="studyflow_test"

# Run tests with coverage
pytest tests/ --cov=app --cov-report=term-missing --cov-report=html
```

### View Coverage Report

```bash
# Open HTML coverage report in browser
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

---

## Test Structure

```
backend/
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Shared fixtures and configuration
│   ├── test_analytics.py        # Analytics service tests
│   ├── test_auth.py             # Authentication tests
│   ├── test_materials.py        # Materials CRUD tests
│   ├── test_progress.py         # Progress tracking tests
│   ├── test_tutoring.py         # Tutoring service tests
│   ├── test_usage.py            # Usage tracking tests
│   └── test_wallet.py           # Wallet service tests
├── .coveragerc                  # Coverage configuration
├── pyproject.toml               # Pytest & coverage settings
└── TESTING.md                   # This file
```

### Test Categories

Tests are marked using pytest markers:

- `@pytest.mark.unit` - Fast, isolated unit tests
- `@pytest.mark.integration` - Tests requiring external services (DB, APIs)
- `@pytest.mark.e2e` - Full end-to-end tests
- `@pytest.mark.database` - Tests requiring database connection
- `@pytest.mark.slow` - Slow-running tests
- `@pytest.mark.auth` - Authentication/authorization tests
- `@pytest.mark.api` - API endpoint tests

---

## Coverage Requirements

### Minimum Thresholds

- **Overall Coverage**: 80% minimum (enforced in CI/CD)
- **Branch Coverage**: Enabled (both if/else paths must be tested)
- **Line Coverage**: Shows which specific lines are missing tests

### Coverage Configuration

Coverage is configured in two places:

1. **`.coveragerc`** - Coverage.py configuration
2. **`pyproject.toml`** - Pytest integration settings

### What's Excluded from Coverage

- Test files (`test_*.py`, `*/tests/*`)
- `__pycache__` directories
- Virtual environments
- `__init__.py` files (usually empty)
- Migration scripts
- Scripts directory

### Enforcing Coverage

The `--cov-fail-under=80` flag ensures tests fail if coverage drops below 80%:

```bash
pytest tests/ --cov=app --cov-fail-under=80
```

---

## Running Tests

### Run All Tests

```bash
pytest tests/ -v
```

### Run with Coverage

```bash
pytest tests/ --cov=app --cov-report=term-missing
```

### Run Specific Test Categories

```bash
# Unit tests only (fast)
pytest tests/ -m unit -v

# Integration tests only
pytest tests/ -m integration -v

# Database tests only
pytest tests/ -m database -v
```

### Run Specific Test File

```bash
pytest tests/test_analytics.py -v
```

### Run Specific Test Class or Function

```bash
# Run specific test class
pytest tests/test_analytics.py::TestAnalyticsService -v

# Run specific test function
pytest tests/test_analytics.py::TestAnalyticsService::test_get_dashboard_stats -v
```

### Run Tests in Parallel (Faster)

```bash
pip install pytest-xdist
pytest tests/ -n auto
```

### Stop on First Failure

```bash
pytest tests/ -x
```

### Show Local Variables on Failure

```bash
pytest tests/ -l
```

---

## Writing Tests

### Test File Structure

Every test file should follow this structure:

```python
"""
Tests for [module/feature name].

Coverage areas:
- Feature 1
- Feature 2
- Edge cases
"""

import pytest
from app.main import app
from fastapi.testclient import TestClient


class TestFeatureName:
    """Test suite for [Feature]."""

    def test_success_case(self, client):
        """
        Test successful [operation].

        Given: [preconditions]
        When: [action]
        Then: [expected result]
        """
        # Arrange
        data = {"key": "value"}

        # Act
        response = client.post("/api/endpoint", json=data)

        # Assert
        assert response.status_code == 200
        assert response.json()["key"] == "expected"

    def test_edge_case(self, client):
        """Test edge case with [condition]."""
        # Test implementation
        pass

    def test_failure_case(self, client):
        """Test failure when [condition]."""
        # Test implementation
        pass
```

### Test Naming Convention

- **Test files**: `test_*.py` (e.g., `test_analytics.py`)
- **Test classes**: `Test*` (e.g., `TestAnalyticsService`)
- **Test functions**: `test_*` (e.g., `test_get_dashboard_stats`)

### Required Test Coverage for New Features

For every new feature, you must create:

1. **At least 1 test for expected/successful use case**
2. **At least 1 test for edge case**
3. **At least 1 test for failure/error case**

### Using Fixtures

Fixtures are defined in `tests/conftest.py`:

```python
def test_with_fixtures(client, auth_headers_student, mock_mongodb):
    """Test using multiple fixtures."""
    response = client.get("/api/endpoint", headers=auth_headers_student)
    assert response.status_code == 200
```

Available fixtures:
- `client` - FastAPI TestClient
- `auth_headers_student` - Student authorization headers
- `auth_headers_teacher` - Teacher authorization headers
- `auth_headers_admin` - Admin authorization headers
- `mock_supabase_auth` - Mocked Supabase authentication
- `mock_mongodb` - Mocked MongoDB collection
- `sample_material_data` - Sample material data
- `sample_session_data` - Sample session data
- `sample_question_data` - Sample question data

---

## CI/CD Integration

### GitHub Actions Workflow

Tests run automatically on:
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop`
- Changes to `apps/studyflow/backend/**` or `apps/shared/**`

### Workflow Jobs

1. **Test Job**
   - Runs all tests with coverage
   - Fails if coverage < 80%
   - Uploads coverage reports to Codecov
   - Generates HTML/XML/JSON coverage reports

2. **Lint Job**
   - Runs Black (code formatter)
   - Runs isort (import sorter)
   - Runs Flake8 (linter)
   - Runs MyPy (type checker)

3. **Security Job**
   - Runs Bandit (security linter)
   - Runs Safety (dependency vulnerability check)

### Workflow File

`.github/workflows/studyflow-backend-tests.yml`

### Required Checks

The following checks must pass before merging:
- ✅ All tests passing
- ✅ Coverage >= 80%
- ⚠️ Linting (warning only)
- ⚠️ Security scan (warning only)

---

## Coverage Reports

### HTML Report

The most detailed coverage report:

```bash
pytest tests/ --cov=app --cov-report=html
open htmlcov/index.html
```

Features:
- Interactive file browser
- Line-by-line coverage visualization
- Branch coverage indicators
- Missing lines highlighted in red

### Terminal Report

Quick overview in terminal:

```bash
pytest tests/ --cov=app --cov-report=term-missing
```

Shows:
- Coverage percentage per file
- Missing line numbers
- Overall coverage summary

### XML Report

For CI/CD integration (Codecov, SonarQube):

```bash
pytest tests/ --cov=app --cov-report=xml
```

Generates `coverage.xml`

### JSON Report

Programmatic access to coverage data:

```bash
pytest tests/ --cov=app --cov-report=json
```

Generates `coverage.json` with detailed context information

---

## Best Practices

### 1. Test Independence

Each test should be independent and not rely on other tests:

```python
# ❌ BAD - Tests depend on each other
def test_create_user(client):
    global user_id
    response = client.post("/users", json={"name": "John"})
    user_id = response.json()["id"]

def test_get_user(client):
    response = client.get(f"/users/{user_id}")  # Relies on previous test
    assert response.status_code == 200

# ✅ GOOD - Tests are independent
@pytest.fixture
def created_user(client):
    response = client.post("/users", json={"name": "John"})
    return response.json()

def test_get_user(client, created_user):
    response = client.get(f"/users/{created_user['id']}")
    assert response.status_code == 200
```

### 2. Arrange-Act-Assert Pattern

Structure tests using the AAA pattern:

```python
def test_create_session(client, auth_headers_student):
    # Arrange
    session_data = {
        "subject": "Mathematics",
        "topics": ["algebra"]
    }

    # Act
    response = client.post(
        "/api/tutoring/sessions",
        json=session_data,
        headers=auth_headers_student
    )

    # Assert
    assert response.status_code == 201
    assert response.json()["subject"] == "Mathematics"
```

### 3. Test Real Functionality

Never create mock implementations or fake tests:

```python
# ❌ BAD - Fake test
def test_calculation():
    assert True  # This doesn't test anything

# ✅ GOOD - Real test
def test_calculate_rag_cost():
    from app.services.usage_service import calculate_rag_cost
    cost = calculate_rag_cost(input_tokens=1000, output_tokens=500)
    assert cost > 0
    assert isinstance(cost, Decimal)
```

### 4. Descriptive Test Names

Test names should describe what they test:

```python
# ❌ BAD
def test_1(client):
    pass

# ✅ GOOD
def test_create_session_success_with_valid_data(client):
    pass

def test_create_session_fails_with_missing_subject(client):
    pass
```

### 5. Test Edge Cases

Don't just test the happy path:

```python
def test_get_progress_with_zero_questions(client, auth_headers_student):
    """Test progress calculation when no questions answered."""
    # Test implementation
    pass

def test_get_progress_with_exact_100_percent(client, auth_headers_student):
    """Test progress when all topics fully mastered."""
    # Test implementation
    pass
```

### 6. Use Parametrize for Similar Tests

Avoid duplicating test code:

```python
import pytest

@pytest.mark.parametrize("role,expected_status", [
    ("student", 403),
    ("teacher", 403),
    ("admin", 200),
])
def test_admin_only_endpoint(client, role, expected_status):
    """Test that only admins can access admin endpoints."""
    headers = get_auth_headers(role)
    response = client.get("/api/admin/stats", headers=headers)
    assert response.status_code == expected_status
```

### 7. Clean Up Resources

Use fixtures to ensure cleanup:

```python
@pytest.fixture
def temp_file():
    """Create temporary file and clean up after test."""
    file_path = "/tmp/test_file.txt"
    with open(file_path, "w") as f:
        f.write("test content")

    yield file_path

    # Cleanup
    if os.path.exists(file_path):
        os.remove(file_path)
```

---

## Troubleshooting

### Coverage Below 80%

**Problem**: Tests fail with "Required test coverage of 80% not reached"

**Solutions**:
1. Identify uncovered code:
   ```bash
   pytest tests/ --cov=app --cov-report=term-missing
   ```
2. Check the HTML report to see which lines are missing:
   ```bash
   pytest tests/ --cov=app --cov-report=html
   open htmlcov/index.html
   ```
3. Write tests for the missing lines
4. Focus on files with lowest coverage first

### Event Loop Errors

**Problem**: `RuntimeError: Event loop is closed`

**Solutions**:
1. Ensure `pytest-asyncio` is installed
2. Check that async tests use `async def` and are properly awaited
3. Verify `asyncio_mode = "auto"` in `pyproject.toml`

### Import Errors

**Problem**: `ModuleNotFoundError: No module named 'app'`

**Solutions**:
1. Set PYTHONPATH:
   ```bash
   export PYTHONPATH=/opt/kasaai
   ```
2. Or run from project root:
   ```bash
   cd /opt/kasaai/apps/studyflow/backend
   pytest tests/
   ```

### Database Connection Errors

**Problem**: Tests fail with MongoDB/PostgreSQL connection errors

**Solutions**:
1. Ensure databases are running
2. Check environment variables:
   ```bash
   echo $MONGODB_URL
   echo $POSTGRES_HOST
   ```
3. Verify database credentials
4. Use separate test databases (not production!)

### Slow Tests

**Problem**: Tests take too long to run

**Solutions**:
1. Run only unit tests during development:
   ```bash
   pytest tests/ -m unit
   ```
2. Use pytest-xdist for parallel execution:
   ```bash
   pip install pytest-xdist
   pytest tests/ -n auto
   ```
3. Profile slow tests:
   ```bash
   pytest tests/ --durations=10
   ```

### Coverage Report Not Generated

**Problem**: No `htmlcov/` directory or coverage.xml

**Solutions**:
1. Ensure pytest-cov is installed:
   ```bash
   pip install pytest-cov
   ```
2. Run with explicit coverage reports:
   ```bash
   pytest tests/ --cov=app --cov-report=html --cov-report=xml
   ```

---

## Additional Resources

### Documentation
- [Pytest Documentation](https://docs.pytest.org/)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)
- [FastAPI Testing Guide](https://fastapi.tiangolo.com/tutorial/testing/)

### Related Files
- `.coveragerc` - Coverage configuration
- `pyproject.toml` - Pytest & tool configuration
- `conftest.py` - Shared test fixtures
- `.github/workflows/studyflow-backend-tests.yml` - CI/CD workflow

### Commands Reference

```bash
# Install dependencies
pip install -r requirements.txt

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=term-missing --cov-report=html

# Run specific category
pytest tests/ -m unit -v
pytest tests/ -m integration -v

# Run specific file
pytest tests/test_analytics.py -v

# Run specific test
pytest tests/test_analytics.py::TestAnalyticsService::test_get_dashboard_stats -v

# Generate coverage reports
pytest tests/ --cov=app --cov-report=html --cov-report=xml --cov-report=json

# View coverage
coverage report
coverage html
open htmlcov/index.html

# Check coverage threshold
coverage report --fail-under=80
```

---

## Summary

✅ **Coverage tracking is configured and enforced**
✅ **Minimum 80% coverage required for all PRs**
✅ **Multiple coverage report formats available (HTML, XML, JSON, terminal)**
✅ **CI/CD pipeline enforces coverage thresholds**
✅ **Comprehensive test fixtures and utilities provided**

For questions or issues, refer to this document or check the GitHub Actions logs for detailed test output.

**Last Updated**: 2025-11-13
