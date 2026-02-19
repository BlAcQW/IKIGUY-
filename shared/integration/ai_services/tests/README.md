# AI Services Unit Tests

Comprehensive unit tests for shared AI services infrastructure.

## Test Coverage

### 1. test_ai_provider_service.py
Tests for `AIProviderService` base class:
- Provider registration and validation
- Provider retrieval with filters
- Health checking (online, degraded, offline, timeout)
- Concurrent health checks
- Provider refresh with caching
- Auto-refresh functionality
- Utility methods

### 2. test_provider_registry.py
Tests for `ProviderRegistry`:
- Provider registration (single and bulk)
- Configuration loading from dicts
- Provider lookup by ID, type, status, capability
- Provider management (update, remove, clear)
- Registry statistics
- Global singleton registry
- Default provider configurations (TTS, LLM, ASR)

### 3. test_health_monitor_service.py
Tests for `HealthMonitorService`:
- Provider health checks
- Metrics tracking (uptime, response time, failures)
- Alert callback registration and triggering
- Background monitoring (start/stop)
- Health history management
- Comprehensive health reports

## Running Tests

### Run All Tests

```bash
# From project root
cd /opt/kasaai
PYTHONPATH=/opt/kasaai pytest apps/shared/integration/ai_services/tests/ -v
```

### Run Specific Test File

```bash
# Test AI Provider Service only
pytest apps/shared/integration/ai_services/tests/test_ai_provider_service.py -v

# Test Provider Registry only
pytest apps/shared/integration/ai_services/tests/test_provider_registry.py -v

# Test Health Monitor only
pytest apps/shared/integration/ai_services/tests/test_health_monitor_service.py -v
```

### Run Specific Test Class

```bash
pytest apps/shared/integration/ai_services/tests/test_ai_provider_service.py::TestProviderRegistration -v
```

### Run Specific Test

```bash
pytest apps/shared/integration/ai_services/tests/test_ai_provider_service.py::TestProviderRegistration::test_register_provider_success -v
```

### Run with Coverage

```bash
# Install pytest-cov if not already installed
pip install pytest-cov

# Run with coverage report
pytest apps/shared/integration/ai_services/tests/ --cov=apps.shared.integration.ai_services --cov-report=html

# Open coverage report
open htmlcov/index.html
```

### Run Only Async Tests

```bash
pytest apps/shared/integration/ai_services/tests/ -v -m asyncio
```

## Test Organization

```
tests/
├── __init__.py                          # Package marker
├── conftest.py                          # Pytest configuration & fixtures
├── README.md                            # This file
├── test_ai_provider_service.py          # AIProviderService tests
├── test_provider_registry.py            # ProviderRegistry tests
└── test_health_monitor_service.py       # HealthMonitorService tests
```

## Fixtures

### Common Fixtures (conftest.py)

- `event_loop`: Provides event loop for async tests
- `reset_global_state`: Resets global registry between tests

### Test-Specific Fixtures

#### test_ai_provider_service.py
- `sample_provider`: Sample AIProvider instance
- `tts_service`: AIProviderService for TTS

#### test_provider_registry.py
- `registry`: Fresh ProviderRegistry instance
- `sample_provider`: Sample AIProvider instance

#### test_health_monitor_service.py
- `registry`: ProviderRegistry with 2 sample providers
- `health_monitor`: HealthMonitorService instance

## Writing New Tests

### Template for New Test File

```python
"""
Unit tests for NewFeature.

Tests the new feature functionality including:
- Feature 1
- Feature 2
- Feature 3
"""

import pytest
from apps.shared.integration.ai_services import ...


@pytest.fixture
def sample_data():
    """Create sample data for testing."""
    return ...


class TestNewFeature:
    """Test new feature functionality."""

    def test_feature_works(self, sample_data):
        """Test that feature works correctly."""
        result = some_function(sample_data)
        assert result == expected_value

    @pytest.mark.asyncio
    async def test_async_feature(self):
        """Test async feature."""
        result = await some_async_function()
        assert result is not None
```

### Best Practices

1. **Test Structure**: Use class-based organization for related tests
2. **Naming**: Use descriptive test names (test_what_when_expected)
3. **Fixtures**: Create reusable fixtures in conftest.py
4. **Mocking**: Mock external dependencies (aiohttp, databases)
5. **Async**: Use `@pytest.mark.asyncio` for async tests
6. **Assertions**: Use clear, specific assertions
7. **Edge Cases**: Test success, failure, and edge cases

## Continuous Integration

### Pre-commit Hook

Add to `.git/hooks/pre-commit`:

```bash
#!/bin/bash
cd /opt/kasaai
PYTHONPATH=/opt/kasaai pytest apps/shared/integration/ai_services/tests/ -v
if [ $? -ne 0 ]; then
    echo "Tests failed. Commit aborted."
    exit 1
fi
```

### GitHub Actions

```yaml
# .github/workflows/test.yml
name: Run Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-cov
      - name: Run tests
        run: |
          PYTHONPATH=/opt/kasaai pytest apps/shared/integration/ai_services/tests/ -v --cov
```

## Troubleshooting

### Import Errors

**Problem**: `ModuleNotFoundError: No module named 'apps.shared'`

**Solution**:
```bash
export PYTHONPATH=/opt/kasaai:$PYTHONPATH
```

### Async Test Warnings

**Problem**: `DeprecationWarning: The loop argument is deprecated`

**Solution**: Ensure pytest-asyncio is up to date:
```bash
pip install --upgrade pytest-asyncio
```

### Test Isolation Issues

**Problem**: Tests pass individually but fail when run together

**Solution**: Check that fixtures properly reset state. Use `autouse=True` fixture for cleanup:
```python
@pytest.fixture(autouse=True)
def cleanup():
    yield
    # Cleanup code here
```

## Dependencies

Required packages:
- pytest>=7.0.0
- pytest-asyncio>=0.21.0
- pytest-cov>=4.0.0 (optional, for coverage)

Install all:
```bash
pip install pytest pytest-asyncio pytest-cov
```

## Test Statistics

As of 2025-10-24:
- **Total Tests**: 80+
- **Test Files**: 3
- **Coverage**: >90% of shared AI services code
- **Async Tests**: 40+

## Contributing

When adding new functionality to shared AI services:

1. Write tests first (TDD)
2. Ensure all tests pass
3. Aim for >90% coverage
4. Update this README if adding new test files

## Questions?

If you encounter issues not covered here:
1. Check existing test implementations for examples
2. Review pytest documentation
3. Update this README with your findings
