# Contract Tests for AI Services API

Contract tests ensure API compatibility and detect breaking changes. These tests validate that API request/response schemas remain stable and backwards-compatible.

## What are Contract Tests?

Contract tests verify:
- **API Structure**: Request and response formats match expected schemas
- **Field Types**: Data types remain consistent (string, int, bool, etc.)
- **Required Fields**: Required fields are always present
- **Optional Fields**: Optional fields can be omitted without breaking
- **Backwards Compatibility**: New fields don't break existing clients
- **Enum Values**: Enum values remain stable

## Test Coverage

### Provider API Contracts (`test_provider_api_contracts.py`)
Tests for provider listing endpoints:
- `GET /api/v1/tts/providers`
- `GET /api/v1/llm/providers`
- `GET /api/v1/asr/providers`

**Coverage:**
- 10+ tests
- Provider object structure
- Capabilities structure
- Backwards compatibility
- Required vs optional fields
- Status and provider type enums

### TTS API Contracts (`test_tts_api_contracts.py`)
Tests for TTS service endpoints:
- `POST /api/v1/tts/synthesize`
- `POST /api/v1/tts/clone`

**Coverage:**
- 10+ tests
- Synthesize request/response
- Voice cloning request/response
- Provider-specific parameters
- Error responses

### LLM & ASR API Contracts (`test_llm_asr_api_contracts.py`)
Tests for LLM and ASR service endpoints:
- `POST /api/v1/llm/generate`
- `POST /api/v1/asr/transcribe`

**Coverage:**
- 15+ tests
- Generate request/response
- Streaming responses
- Transcription request/response
- Word timestamps and diarization
- Cross-service consistency

## Running Contract Tests

### Run All Contract Tests

```bash
pytest apps/shared/integration/ai_services/tests/contract/ -v
```

### Run Specific Test Module

```bash
# Provider API contracts
pytest apps/shared/integration/ai_services/tests/contract/test_provider_api_contracts.py -v

# TTS API contracts
pytest apps/shared/integration/ai_services/tests/contract/test_tts_api_contracts.py -v

# LLM & ASR API contracts
pytest apps/shared/integration/ai_services/tests/contract/test_llm_asr_api_contracts.py -v
```

### Run Specific Test

```bash
pytest apps/shared/integration/ai_services/tests/contract/test_provider_api_contracts.py::TestProviderListingContracts::test_tts_providers_response_contract -v
```

## Contract Test Strategy

### 1. Define Pydantic Contracts

Contracts are defined using Pydantic models:

```python
class ProviderContract(BaseModel):
    """Contract for provider object."""

    id: str  # Required field
    name: str  # Required field
    status: str  # Required field
    metadata: Optional[Dict[str, Any]] = {}  # Optional field

    class Config:
        extra = "allow"  # Allow new fields for backwards compatibility
```

### 2. Test Valid Responses

```python
def test_provider_response_contract(self):
    """Test that response matches contract."""
    mock_response = {
        "success": True,
        "data": {
            "provider1": {
                "id": "provider1",
                "name": "Provider 1",
                "status": "online",
            }
        }
    }

    # Validate against contract
    response = ProviderResponseContract(**mock_response)
    assert response.success is True
```

### 3. Test Backwards Compatibility

```python
def test_backwards_compatibility(self):
    """Test that new fields don't break existing clients."""
    response_with_new_fields = {
        "success": True,
        "data": {
            "provider1": {
                "id": "provider1",
                "name": "Provider 1",
                "status": "online",
                "new_field": "new value"  # New field added
            }
        }
    }

    # Should NOT raise validation error
    response = ProviderResponseContract(**response_with_new_fields)
    assert response.success is True
```

### 4. Test Breaking Changes

```python
def test_missing_required_field_breaks(self):
    """Test that removing required fields causes validation error."""
    invalid_response = {
        "success": True,
        "data": {
            "provider1": {
                # Missing 'id' field - BREAKING CHANGE
                "name": "Provider 1",
                "status": "online",
            }
        }
    }

    # Should raise validation error
    with pytest.raises(ValidationError) as exc_info:
        ProviderResponseContract(**invalid_response)

    assert "id" in str(exc_info.value)
```

## Contract Test Patterns

### Pattern 1: Test All Required Fields

Every contract should test that all required fields are validated:

```python
def test_required_fields(self):
    """Test that all required fields must be present."""
    minimal_valid = {
        "field1": "value1",
        "field2": "value2",
        # Only required fields
    }

    Contract(**minimal_valid)  # Should pass

    invalid = {
        "field1": "value1",
        # Missing field2 - BREAKING
    }

    with pytest.raises(ValidationError):
        Contract(**invalid)
```

### Pattern 2: Test Optional Fields

Test that optional fields can be omitted:

```python
def test_optional_fields(self):
    """Test that optional fields can be omitted."""
    without_optional = {
        "required_field": "value",
        # Optional fields omitted
    }

    obj = Contract(**without_optional)
    assert obj.optional_field is None  # Default value
```

### Pattern 3: Test Enum Stability

Test that enum values haven't changed:

```python
def test_enum_values_stable(self):
    """Test that enum values are stable."""
    valid_statuses = ["online", "offline", "degraded"]

    for status in valid_statuses:
        data = {"status": status, ...}
        obj = Contract(**data)  # Should pass for all values
```

### Pattern 4: Test Field Types

Test that field types are enforced:

```python
def test_field_types(self):
    """Test that field types are validated."""
    # Valid types
    valid = {"count": 10, "active": True}
    Contract(**valid)

    # Invalid types - BREAKING
    invalid = {"count": "ten", "active": "yes"}
    with pytest.raises(ValidationError):
        Contract(**invalid)
```

## Breaking Change Detection

Contract tests detect these breaking changes:

### ❌ Breaking Changes (Will Fail Tests)

1. **Removing Required Fields**
   ```python
   # Before
   {"id": "abc", "name": "Test"}

   # After - BREAKS
   {"name": "Test"}  # Missing 'id'
   ```

2. **Changing Field Types**
   ```python
   # Before
   {"count": 10}

   # After - BREAKS
   {"count": "10"}  # Changed int → string
   ```

3. **Making Optional Fields Required**
   ```python
   # Before
   optional_field: Optional[str] = None

   # After - BREAKS
   required_field: str  # Now required
   ```

4. **Changing Enum Values**
   ```python
   # Before
   status: "online" | "offline"

   # After - BREAKS
   status: "active" | "inactive"  # Changed enum values
   ```

### ✅ Non-Breaking Changes (Will Pass Tests)

1. **Adding Optional Fields**
   ```python
   # Before
   {"id": "abc", "name": "Test"}

   # After - OK
   {"id": "abc", "name": "Test", "new_field": "value"}
   ```

2. **Adding to Enum Values**
   ```python
   # Before
   status: "online" | "offline"

   # After - OK
   status: "online" | "offline" | "maintenance"
   ```

3. **Making Required Fields Optional**
   ```python
   # Before
   field: str

   # After - OK
   field: Optional[str] = None
   ```

## CI/CD Integration

Contract tests should run:
- ✅ On every pull request
- ✅ Before merging to main
- ✅ Before releases
- ✅ On API changes

### Fail CI if Contract Tests Fail

```yaml
# .github/workflows/test.yml
- name: Run Contract Tests
  run: |
    pytest apps/shared/integration/ai_services/tests/contract/ -v
  # CI fails if tests fail
```

### Generate Contract Test Reports

```bash
# Generate HTML report
pytest apps/shared/integration/ai_services/tests/contract/ \
  --html=contract-test-report.html \
  --self-contained-html
```

## Versioning Strategy

When making API changes:

1. **Non-Breaking Changes**: Add new optional fields
   - Add tests for new fields
   - Ensure existing tests still pass

2. **Breaking Changes**: Create new API version
   - Create `/api/v2/` endpoints
   - Keep v1 contracts and tests
   - Add v2 contracts and tests

Example:
```
/api/v1/tts/synthesize  # Old version (stable)
/api/v2/tts/synthesize  # New version (breaking changes)
```

## Best Practices

1. **✅ Use Pydantic for Validation**
   - Type safety
   - Automatic validation
   - Clear error messages

2. **✅ Test Both Success and Error Cases**
   - Success responses
   - Error responses
   - Edge cases

3. **✅ Allow Extra Fields**
   ```python
   class Config:
       extra = "allow"  # Backwards compatibility
   ```

4. **✅ Use Optional for Non-Required Fields**
   ```python
   field: Optional[str] = None  # Can be omitted
   ```

5. **✅ Test Enum Stability**
   - Maintain list of valid enum values
   - Test all enum values work

6. **✅ Document Breaking Changes**
   - Clear error messages
   - Migration guides
   - Version bump required

## Debugging Contract Tests

### View Validation Errors

```bash
pytest apps/shared/integration/ai_services/tests/contract/ -v -s
```

### Debug Specific Contract

```python
# Add print statements to see validation errors
try:
    response = Contract(**data)
except ValidationError as e:
    print(e.json())  # Detailed error info
```

## Related Documentation

- [QA Strategy](../../../../../architecture/QA_STRATEGY.md) - Overall testing strategy
- [API Documentation](../../../../../architecture/API_DOCUMENTATION.md) - API specifications
- [Integration Guide](../../../../../architecture/INTEGRATION_GUIDE.md) - How to integrate
- [Integration Tests](../integration/README.md) - Integration testing docs

## Contract Test Checklist

When adding new API endpoints:

- [ ] Create Pydantic contract models for request/response
- [ ] Test all required fields
- [ ] Test all optional fields
- [ ] Test backwards compatibility (extra fields allowed)
- [ ] Test breaking changes (missing required fields)
- [ ] Test field types are enforced
- [ ] Test enum values are stable
- [ ] Test error response format
- [ ] Add to CI/CD pipeline
- [ ] Document breaking changes

## Summary

Contract tests are critical for:
- ✅ **API Stability**: Ensure APIs don't break unexpectedly
- ✅ **Backwards Compatibility**: New features don't break old clients
- ✅ **Breaking Change Detection**: Catch breaking changes before deploy
- ✅ **Documentation**: Contracts serve as API documentation
- ✅ **Confidence**: Safe to refactor backend without breaking frontend

Run contract tests frequently and treat failures as critical issues that block deployment.
