# Multi-App Validation Tests

Multi-app validation tests ensure that the shared AI services integration works correctly across all consuming applications in the monorepo.

## Purpose

These tests validate:
- **Cross-App Compatibility**: Shared services work in each app's environment
- **Configuration Isolation**: Each app's config doesn't interfere with others
- **Import Consistency**: All apps can correctly import and use shared services
- **Breaking Change Detection**: Changes to shared services don't break consuming apps
- **Environment Compatibility**: Services work with different Python versions and dependencies

## Consuming Applications

The shared AI services are consumed by:

1. **@apps/core_backend/** - Main API backend
   - Service: kasaai-core-backend
   - Nginx: api.ailabsafrica.com
   - Frontend: @apps/b2c-portal/ (kasaai.ailabsafrica.com)

2. **@apps/developer_platform/backend/** - Developer platform API
   - Service: kasaai-dev-backend
   - Nginx: dev-api.ailabsafrica.com
   - Frontend: @apps/developer_platform/frontend/ (developer.ailabsafrica.com)

3. **@apps/community/backend/** - Language community API
   - Nginx: language-community-api.ailabsafrica.com
   - Frontend: @apps/community/frontend/ (language-community.ailabsafrica.com)

## Test Matrix

The test matrix runs validation tests across:

| Dimension | Values |
|-----------|--------|
| **Application** | core_backend, developer_platform, community |
| **Python Version** | 3.9, 3.10, 3.11 |
| **Test Type** | imports, initialization, basic_operations |

### Matrix Strategy

```yaml
strategy:
  matrix:
    app: [core_backend, developer_platform, community]
    python-version: ['3.9', '3.10', '3.11']
```

This creates 9 test combinations (3 apps × 3 Python versions).

## Test Structure

```
tests/multi_app/
├── README.md                          # This file
├── __init__.py                        # Module initialization
├── test_import_validation.py          # Import tests across apps
├── test_initialization_validation.py  # Initialization tests
├── test_basic_operations.py           # Basic operation tests
└── conftest.py                        # Shared fixtures
```

## Running Multi-App Tests

### Run All Multi-App Tests

```bash
pytest apps/shared/integration/ai_services/tests/multi_app/ -v
```

### Run for Specific App

```bash
pytest apps/shared/integration/ai_services/tests/multi_app/ -v -k "core_backend"
```

### Run Specific Test Type

```bash
# Import validation only
pytest apps/shared/integration/ai_services/tests/multi_app/test_import_validation.py -v

# Initialization validation only
pytest apps/shared/integration/ai_services/tests/multi_app/test_initialization_validation.py -v

# Basic operations only
pytest apps/shared/integration/ai_services/tests/multi_app/test_basic_operations.py -v
```

### Run with Matrix Locally

```bash
# Test with Python 3.9
python3.9 -m pytest apps/shared/integration/ai_services/tests/multi_app/ -v

# Test with Python 3.10
python3.10 -m pytest apps/shared/integration/ai_services/tests/multi_app/ -v

# Test with Python 3.11
python3.11 -m pytest apps/shared/integration/ai_services/tests/multi_app/ -v
```

## Test Coverage

### Import Validation Tests (`test_import_validation.py`)

Validate that all shared services can be imported in each app context:

- ✅ Import TTS service from core_backend
- ✅ Import LLM service from core_backend
- ✅ Import ASR service from core_backend
- ✅ Import Health Monitor from core_backend
- ✅ Import all services from developer_platform
- ✅ Import all services from community
- ✅ Import with different PYTHONPATH configurations

**Why Important**: Different apps may have different sys.path configurations. These tests ensure imports work consistently.

### Initialization Validation Tests (`test_initialization_validation.py`)

Validate that services can be initialized in each app context:

- ✅ Initialize TTS service with app-specific config
- ✅ Initialize LLM service with app-specific config
- ✅ Initialize ASR service with app-specific config
- ✅ Initialize Health Monitor with app-specific config
- ✅ Handle missing configuration gracefully
- ✅ Validate configuration isolation between apps

**Why Important**: Each app has its own configuration. Services must initialize correctly with app-specific settings.

### Basic Operations Tests (`test_basic_operations.py`)

Validate that basic service operations work in each app context:

- ✅ TTS synthesis request/response cycle
- ✅ LLM generation request/response cycle
- ✅ ASR transcription request/response cycle
- ✅ Health check operations
- ✅ Provider listing operations
- ✅ Error handling

**Why Important**: Services must function correctly in production app environments.

## CI/CD Integration

### GitHub Actions Matrix

The CI/CD pipeline uses a matrix strategy to test all combinations:

```yaml
multi-app-validation:
  name: Multi-App Validation
  runs-on: ubuntu-latest

  strategy:
    matrix:
      app: [core_backend, developer_platform, community]
      python-version: ['3.9', '3.10', '3.11']

  steps:
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install app dependencies
      run: |
        pip install -r apps/${{ matrix.app }}/requirements.txt
        pip install -r apps/shared/integration/ai_services/requirements.txt

    - name: Run multi-app validation
      env:
        TEST_APP: ${{ matrix.app }}
      run: |
        pytest apps/shared/integration/ai_services/tests/multi_app/ \
          -v \
          --app=${{ matrix.app }}
```

### Matrix Benefits

1. **Comprehensive Coverage**: Tests all app × Python version combinations
2. **Early Detection**: Catches compatibility issues before merge
3. **Parallel Execution**: Matrix runs in parallel for speed
4. **Clear Reporting**: Easy to identify which app/Python combo failed

## Test Patterns

### Pattern 1: Import Validation

Test that imports work in app context:

```python
def test_import_in_app_context(app_name):
    """Test imports work in specific app context."""
    # Set up app-specific PYTHONPATH
    app_path = f"/opt/kasaai/apps/{app_name}"
    sys.path.insert(0, app_path)

    try:
        # Import should work
        from apps.shared.integration.ai_services.tts_service import TTSService
        assert TTSService is not None
    finally:
        # Clean up
        sys.path.remove(app_path)
```

### Pattern 2: Configuration Isolation

Test that each app's config is isolated:

```python
def test_config_isolation(app_name):
    """Test that app configs don't interfere."""
    # Load app1 config
    config1 = load_config(app_name)
    service1 = TTSService(config1)

    # Load app2 config
    config2 = load_config("other_app")
    service2 = TTSService(config2)

    # Configs should be different
    assert config1 != config2
    # Services should be independent
    assert service1.config != service2.config
```

### Pattern 3: Basic Operations

Test that operations work in app context:

```python
@pytest.mark.asyncio
async def test_basic_operation(app_name):
    """Test basic operations work in app context."""
    # Initialize with app config
    service = TTSService(load_config(app_name))

    # Basic operation should work
    result = await service.synthesize(
        provider_id="coqui_xtts",
        text="Hello",
        language="en"
    )

    assert result["success"] is True
```

## Debugging Multi-App Tests

### View Detailed Output

```bash
pytest apps/shared/integration/ai_services/tests/multi_app/ -vv -s
```

### Run Single App Test

```bash
pytest apps/shared/integration/ai_services/tests/multi_app/ -v --app=core_backend
```

### Check Import Paths

```bash
pytest apps/shared/integration/ai_services/tests/multi_app/ -v --log-cli-level=DEBUG
```

### Test Specific Python Version

```bash
python3.9 -m pytest apps/shared/integration/ai_services/tests/multi_app/ -v
```

## Common Issues

### Issue 1: Import Errors

**Symptom**: `ModuleNotFoundError` when importing shared services

**Cause**: PYTHONPATH not set correctly for app context

**Solution**:
```python
import sys
sys.path.insert(0, "/opt/kasaai")
sys.path.insert(0, f"/opt/kasaai/apps/{app_name}")
```

### Issue 2: Configuration Conflicts

**Symptom**: Service uses wrong configuration for app

**Cause**: Configuration leaking between apps

**Solution**: Use configuration isolation and fixtures that clean up after each test

### Issue 3: Dependency Version Conflicts

**Symptom**: Tests pass for one app but fail for another

**Cause**: Different apps have different dependency versions

**Solution**: Use virtual environments per app or test with each app's requirements.txt

## Best Practices

### 1. Test in Realistic App Contexts

```python
# ✅ Good - Tests in actual app context
def test_in_app_context():
    with app_context("core_backend"):
        service = TTSService()
        assert service.is_available()
```

### 2. Clean Up After Tests

```python
# ✅ Good - Cleans up sys.path
@pytest.fixture
def app_context(app_name):
    app_path = f"/opt/kasaai/apps/{app_name}"
    sys.path.insert(0, app_path)

    yield app_name

    # Cleanup
    sys.path.remove(app_path)
```

### 3. Test Configuration Isolation

```python
# ✅ Good - Tests configs don't interfere
def test_config_isolation():
    config1 = load_config("app1")
    config2 = load_config("app2")

    # Modify config1
    config1["setting"] = "value"

    # config2 should be unaffected
    assert "setting" not in config2
```

### 4. Use Parametrization for Apps

```python
# ✅ Good - Tests all apps with one test function
@pytest.mark.parametrize("app_name", ["core_backend", "developer_platform", "community"])
def test_import_in_all_apps(app_name):
    with app_context(app_name):
        from apps.shared.integration.ai_services.tts_service import TTSService
        assert TTSService is not None
```

## Related Documentation

- [QA Strategy](../../../../../architecture/QA_STRATEGY.md) - Overall testing strategy
- [Integration Tests](../integration/README.md) - Component integration tests
- [Contract Tests](../contract/README.md) - API contract tests
- [E2E Tests](../e2e/README.md) - End-to-end user flow tests

## Summary

Multi-app validation tests ensure:
- ✅ **Compatibility**: Shared services work across all consuming apps
- ✅ **Isolation**: App configurations don't interfere with each other
- ✅ **Consistency**: Imports and operations work consistently
- ✅ **Early Detection**: Catch cross-app issues before production
- ✅ **Confidence**: Safe to deploy shared service changes

Run these tests before merging any changes to shared AI services to ensure all consuming applications continue to work correctly.

**Total Tests**: 25+ tests across 3 apps × 3 Python versions = 75+ test runs in CI/CD matrix.
