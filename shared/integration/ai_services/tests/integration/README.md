# Integration Tests for AI Services

Integration tests for the shared AI services infrastructure. These tests verify that different components work together correctly.

## Test Coverage

### Backend Integration (`test_backend_integration.py`)
Tests integration between shared services and backend implementations:
- Backend service initialization with shared services
- Provider selection and filtering
- Health check integration
- Error handling across service boundaries
- Global registry sharing between services

**Coverage:**
- 15+ tests
- TTS, LLM, ASR service integration
- Health monitor integration
- Multi-service scenarios

### Database Integration (`test_database_integration.py`)
Tests integration between backend services and databases:
- Provider configuration persistence (MongoDB)
- Health metrics persistence (PostgreSQL)
- Usage data tracking (MongoDB)
- Transaction integrity
- Query and aggregation operations

**Coverage:**
- 12+ tests
- MongoDB operations (save, load, update, bulk operations)
- PostgreSQL operations (metrics, health history, uptime)
- Transaction management
- Data integrity

### External Services Integration (`test_external_services_integration.py`)
Tests integration with external AI services:
- TTS service calls (Coqui, MeloTTS)
- LLM service calls (Ollama)
- ASR service calls (Whisper)
- Service resilience (timeouts, retries, error handling)
- Health monitoring

**Coverage:**
- 15+ tests
- Synthesis, voice cloning, generation, transcription
- Streaming responses
- Error handling and resilience
- Retry logic

### API Integration (`test_api_integration.py`)
Tests complete API request/response cycles:
- Provider listing endpoints
- TTS synthesize endpoints
- LLM generate endpoints
- ASR transcribe endpoints
- Health check endpoints
- Authentication and rate limiting

**Coverage:**
- 15+ tests
- Complete request/response cycles
- API error handling
- Validation errors
- Authentication flows

## Running Integration Tests

### Run All Integration Tests

```bash
pytest apps/shared/integration/ai_services/tests/integration/ -v
```

### Run Specific Test Module

```bash
# Backend integration tests
pytest apps/shared/integration/ai_services/tests/integration/test_backend_integration.py -v

# Database integration tests
pytest apps/shared/integration/ai_services/tests/integration/test_database_integration.py -v

# External services integration tests
pytest apps/shared/integration/ai_services/tests/integration/test_external_services_integration.py -v

# API integration tests
pytest apps/shared/integration/ai_services/tests/integration/test_api_integration.py -v
```

### Run Specific Test Class

```bash
pytest apps/shared/integration/ai_services/tests/integration/test_backend_integration.py::TestBackendTTSServiceIntegration -v
```

### Run with Coverage

```bash
pytest apps/shared/integration/ai_services/tests/integration/ --cov=apps.shared.integration.ai_services --cov-report=html
```

## Test Structure

### Backend Integration Tests

```
TestBackendTTSServiceIntegration
├── test_backend_service_initialization
├── test_backend_service_provider_selection
├── test_backend_service_health_check_integration
├── test_backend_service_capability_filtering
└── test_backend_service_error_handling

TestBackendLLMServiceIntegration
├── test_backend_llm_service_initialization
└── test_backend_llm_service_model_selection

TestBackendASRServiceIntegration
├── test_backend_asr_service_initialization
└── test_backend_asr_service_capability_check

TestHealthMonitorIntegration
├── test_health_monitor_checks_all_services
├── test_health_monitor_tracks_metrics_per_service
└── test_health_monitor_alerts_on_service_degradation

TestGlobalRegistryIntegration
└── test_multiple_backend_services_share_registry
```

### Database Integration Tests

```
TestProviderConfigPersistence
├── test_save_provider_config_to_mongodb
├── test_load_provider_config_from_mongodb
├── test_update_provider_config_in_mongodb
└── test_bulk_load_providers_from_mongodb

TestHealthMetricsPersistence
├── test_save_health_check_result_to_postgres
├── test_query_health_history_from_postgres
├── test_calculate_uptime_from_postgres
└── test_get_provider_metrics_from_postgres

TestUsageDataPersistence
├── test_save_usage_record_to_mongodb
├── test_query_user_usage_from_mongodb
└── test_aggregate_usage_stats_from_mongodb

TestDatabaseTransactionIntegrity
├── test_atomic_provider_update_with_usage
└── test_rollback_on_database_error
```

### External Services Integration Tests

```
TestTTSServiceIntegration
├── test_synthesize_request_to_coqui
├── test_voice_cloning_request_to_coqui
├── test_health_check_to_tts_providers
└── test_handle_tts_service_error

TestLLMServiceIntegration
├── test_generate_request_to_ollama
├── test_streaming_request_to_ollama
└── test_health_check_to_ollama

TestASRServiceIntegration
├── test_transcribe_request_to_whisper
└── test_transcribe_with_timestamps

TestServiceResilience
├── test_handle_timeout
├── test_handle_connection_error
└── test_retry_on_transient_failure
```

### API Integration Tests

```
TestProviderListingAPI
├── test_get_tts_providers_api
├── test_get_providers_with_status_filter
├── test_get_providers_with_capability_filter
├── test_get_providers_with_force_refresh
└── test_api_error_response_format

TestTTSSynthesizeAPI
├── test_synthesize_api_success
├── test_synthesize_api_validation_error
└── test_synthesize_api_provider_offline

TestLLMGenerateAPI
├── test_generate_api_success
└── test_generate_api_streaming

TestASRTranscribeAPI
└── test_transcribe_api_success

TestHealthCheckAPI
├── test_health_check_api
└── test_health_check_by_type_api

TestAPIRateLimiting
└── test_rate_limit_exceeded

TestAPIAuthentication
├── test_missing_auth_token
└── test_invalid_auth_token
```

## Test Fixtures

Shared fixtures are defined in `conftest.py`:

- `reset_global_state`: Auto-used fixture that resets global registry state
- `mock_mongodb_connection`: Mock MongoDB client, database, and collection
- `mock_postgres_connection`: Mock PostgreSQL connection and cursor
- `mock_redis_connection`: Mock Redis client for caching
- `test_auth_token`: Test authentication token
- `test_user_id`: Test user ID

## Mocking Strategy

Integration tests use mocking to avoid dependencies on external services:

### HTTP Client Mocking
```python
with patch("aiohttp.ClientSession") as mock_session:
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={"data": "test"})
    # ... test code
```

### Database Mocking
```python
def test_with_mongodb(self, mock_mongodb_connection):
    mock_client, mock_db, mock_collection = mock_mongodb_connection
    # ... test code
```

### Service Mocking
```python
with patch("apps.shared.integration.ai_services.AIProviderService") as mock_service:
    # ... test code
```

## Best Practices

1. **Use Appropriate Mocking**: Mock external dependencies (HTTP, databases) but test actual service logic
2. **Test Error Paths**: Ensure error handling works correctly
3. **Test Integration Points**: Focus on boundaries between components
4. **Use Realistic Data**: Use data that matches production scenarios
5. **Independent Tests**: Each test should be independent and not rely on other tests
6. **Clean Up**: Use fixtures to ensure clean state between tests

## Integration Test Checklist

When adding new integration tests:

- [ ] Test happy path (success scenario)
- [ ] Test error scenarios
- [ ] Test edge cases
- [ ] Test timeout/retry logic
- [ ] Test data persistence
- [ ] Test API request/response format
- [ ] Mock external dependencies
- [ ] Use shared fixtures where appropriate
- [ ] Add docstrings explaining what is tested
- [ ] Update this README if adding new test modules

## Debugging Integration Tests

### Run in Verbose Mode
```bash
pytest apps/shared/integration/ai_services/tests/integration/ -vv
```

### Run with Detailed Output
```bash
pytest apps/shared/integration/ai_services/tests/integration/ -vv -s
```

### Run Specific Test with Debugging
```bash
pytest apps/shared/integration/ai_services/tests/integration/test_backend_integration.py::TestBackendTTSServiceIntegration::test_backend_service_initialization -vv --pdb
```

### Show Test Output
```bash
pytest apps/shared/integration/ai_services/tests/integration/ -rA
```

## CI/CD Integration

These integration tests should run:
- On every pull request
- Before merging to main
- On nightly builds
- Before releases

See `@apps/architecture/QA_STRATEGY.md` for CI/CD pipeline configuration.

## Related Documentation

- [QA Strategy](../../../../../architecture/QA_STRATEGY.md) - Overall testing strategy
- [Architecture](../../../../../architecture/ARCHITECTURE.md) - Platform architecture
- [Integration Guide](../../../../../architecture/INTEGRATION_GUIDE.md) - How to integrate shared services
- [Unit Tests](../README.md) - Unit testing documentation
