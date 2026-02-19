# African Language Community Platform - Test Suite

Comprehensive unit and integration tests for the MLOps platform API.

## Test Structure

```
tests/
├── conftest.py                        # Shared fixtures and test utilities
├── test_routers_models.py            # ML Models Router tests (10+ test classes)
├── test_routers_pipelines.py         # Training Pipelines Router tests (9+ test classes)
├── test_routers_resources.py         # Resources Router tests (8+ test classes)
├── test_routers_discovery.py         # Discovery Router tests (10+ test classes)
└── README.md                          # This file
```

## Running Tests

### Run All Tests
```bash
cd /opt/kasaai/apps/community/backend
pytest
```

### Run Specific Test File
```bash
pytest tests/test_routers_models.py
```

### Run Specific Test Class
```bash
pytest tests/test_routers_models.py::TestCreateModel
```

### Run Specific Test
```bash
pytest tests/test_routers_models.py::TestCreateModel::test_create_model_success
```

### Run with Coverage Report
```bash
pytest --cov=routers --cov-report=html
# Open htmlcov/index.html in browser
```

### Run Only Unit Tests
```bash
pytest -m unit
```

### Run Only Integration Tests
```bash
pytest -m integration
```

### Run Tests in Parallel (faster)
```bash
pytest -n auto
```

## Test Coverage

Current test coverage targets:
- **Models Router**: 95%+ coverage
- **Pipelines Router**: 95%+ coverage
- **Resources Router**: 90%+ coverage
- **Discovery Router**: 90%+ coverage

Coverage includes:
- ✅ All CRUD operations (Create, Read, Update, Delete)
- ✅ Success paths
- ✅ Error paths (404, 403, 400, 500)
- ✅ Edge cases
- ✅ Authorization checks
- ✅ Database interactions
- ✅ External service mocking (Hetzner Storage, HTTP requests)

## Test Fixtures

### Core Fixtures (conftest.py)

#### Database & Auth
- `mock_mongodb` - Mock MongoDB database with all collections
- `mock_supabase_client` - Mock Supabase authentication client
- `auth_headers` - Sample JWT auth headers

#### User Fixtures
- `sample_user` - Regular user
- `admin_user` - Admin user with elevated privileges
- `moderator_user` - Moderator user for verification tasks

#### MLOps Fixtures
- `sample_ml_model` - Complete ML model document
- `sample_pipeline` - Training pipeline with stages
- `sample_dataset_version` - Dataset version with manifest
- `sample_external_resource` - External resource link
- `sample_file_upload` - File upload document

#### Utilities
- `async_iterator_factory` - Create async iterators for testing
- `mock_storage_service` - Mock Hetzner Storage Service

## Test Classes

### Models Router (`test_routers_models.py`)

1. **TestSerializeModel** - Model serialization utility tests
2. **TestGetLanguageIds** - Language ID resolution tests
3. **TestCreateModel** - POST /models endpoint
4. **TestListModels** - GET /models with filtering
5. **TestGetModel** - GET /models/{uuid}
6. **TestUpdateModel** - PUT /models/{uuid}
7. **TestDeleteModel** - DELETE /models/{uuid} (admin only)
8. **TestModelDownload** - GET /models/{uuid}/download
9. **TestModelIssueReporting** - POST /models/{uuid}/issues
10. **TestModelStatistics** - GET /models/stats
11. **TestModelSearch** - GET /models/search
12. **TestCreateModelVersion** - POST /models/{uuid}/versions

**Total Tests**: 25+

### Pipelines Router (`test_routers_pipelines.py`)

1. **TestCalculateOverallProgress** - Weighted progress calculation
2. **TestCreatePipeline** - POST /pipelines with stage initialization
3. **TestListPipelines** - GET /pipelines with filtering
4. **TestGetPipeline** - GET /pipelines/{id}
5. **TestUpdatePipeline** - PUT /pipelines/{id}
6. **TestUpdatePipelineStage** - PUT /pipelines/{id}/stages/{stage}
7. **TestUploadPipelineArtifact** - POST /pipelines/{id}/artifacts
8. **TestGetPipelineMetrics** - GET /pipelines/{id}/metrics
9. **TestCompletePipeline** - POST /pipelines/{id}/complete
10. **TestPipelineStatistics** - GET /pipelines/stats

**Total Tests**: 20+

### Resources Router (`test_routers_resources.py`)

1. **TestSubmitResourceLink** - POST /resources/links with auto-detection
2. **TestBrowseResourceLinks** - GET /resources/links
3. **TestVerifyResourceLink** - POST /resources/links/{uuid}/verify
4. **TestVoteOnResource** - POST /resources/links/{uuid}/vote
5. **TestFileUpload** - POST /resources/upload
6. **TestGetUploadStatus** - GET /resources/uploads/{uuid}
7. **TestResourceStatistics** - GET /resources/stats

**Total Tests**: 15+

### Discovery Router (`test_routers_discovery.py`)

1. **TestDiscoverByLanguage** - GET /discovery/languages/{code}
2. **TestDiscoverDatasetsByLanguage** - GET /discovery/languages/{code}/datasets
3. **TestDiscoverModelsByLanguage** - GET /discovery/languages/{code}/models
4. **TestDiscoverByTask** - GET /discovery/tasks/{task_type}
5. **TestTrendingModels** - GET /discovery/trending/models
6. **TestTrendingDatasets** - GET /discovery/trending/datasets
7. **TestTrendingResources** - GET /discovery/trending/resources
8. **TestRecommendSimilarModels** - GET /discovery/recommendations/models/{uuid}/similar
9. **TestRecommendCompatibleModels** - GET /discovery/recommendations/datasets/{uuid}/compatible-models
10. **TestPlatformOverview** - GET /discovery/overview
11. **TestGlobalSearch** - GET /discovery/search

**Total Tests**: 20+

## Test Patterns

### Async Test Example
```python
@pytest.mark.asyncio
async def test_create_model_success(self, mock_mongodb, sample_user):
    """Test successful model creation."""
    # Setup mocks
    mock_mongodb.ml_models.insert_one = AsyncMock(return_value=mock_result)

    # Call endpoint
    result = await create_model(...)

    # Assertions
    assert result.name == "Test Model"
    mock_mongodb.ml_models.insert_one.assert_called_once()
```

### HTTP Exception Testing
```python
@pytest.mark.asyncio
async def test_get_model_not_found(self, mock_mongodb):
    """Test 404 when model doesn't exist."""
    from fastapi import HTTPException

    mock_mongodb.ml_models.find_one = AsyncMock(return_value=None)

    with pytest.raises(HTTPException) as exc_info:
        await get_model(model_uuid="nonexistent", db=mock_mongodb)

    assert exc_info.value.status_code == 404
```

### Authorization Testing
```python
@pytest.mark.asyncio
async def test_update_model_forbidden(self, mock_mongodb, sample_ml_model):
    """Test 403 when non-creator tries to update."""
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc_info:
        await update_model(
            model_uuid="...",
            current_user={"id": "different-user-id"}
        )

    assert exc_info.value.status_code == 403
```

## Writing New Tests

### Test Checklist

For each endpoint, test:
- ✅ **Success path** - Happy path with valid data
- ✅ **Not found** - 404 when resource doesn't exist
- ✅ **Forbidden** - 403 when user lacks permissions
- ✅ **Bad request** - 400 for invalid input data
- ✅ **Edge cases** - Empty lists, None values, boundary conditions

### Example Test Template
```python
class TestNewEndpoint:
    """Test POST /new-endpoint - Description."""

    @pytest.mark.asyncio
    async def test_success(self, mock_mongodb, sample_user):
        """Test successful operation."""
        # Setup
        # Act
        # Assert

    @pytest.mark.asyncio
    async def test_not_found(self, mock_mongodb):
        """Test 404 error."""
        # Setup
        # Act & Assert with pytest.raises

    @pytest.mark.asyncio
    async def test_forbidden(self, mock_mongodb):
        """Test 403 authorization error."""
        # Setup
        # Act & Assert

    @pytest.mark.asyncio
    async def test_edge_case(self, mock_mongodb):
        """Test edge case behavior."""
        # Setup
        # Act
        # Assert
```

## Continuous Integration

Tests run automatically on:
- Every commit (via pre-commit hook)
- Every pull request
- Before deployment

### CI Pipeline
```bash
# Install dependencies
pip install -r requirements.txt
pip install pytest pytest-asyncio pytest-cov

# Run linting
black --check .
flake8 .

# Run tests with coverage
pytest --cov=routers --cov=models --cov=services --cov-fail-under=80

# Generate coverage report
coverage html
```

## Troubleshooting

### Import Errors
```bash
# Add backend directory to PYTHONPATH
export PYTHONPATH=/opt/kasaai/apps/community/backend:$PYTHONPATH
pytest
```

### Async Warnings
```bash
# Use pytest-asyncio
pip install pytest-asyncio
pytest --asyncio-mode=auto
```

### Coverage Not Generated
```bash
# Install pytest-cov
pip install pytest-cov
pytest --cov=routers --cov-report=html
```

## Best Practices

1. **One assertion per test** (or closely related assertions)
2. **Use descriptive test names** (`test_create_model_success` not `test_1`)
3. **Mock external dependencies** (database, HTTP, storage)
4. **Test both success and failure paths**
5. **Use fixtures for shared setup**
6. **Keep tests independent** (no test should depend on another)
7. **Test edge cases** (empty lists, None, boundary values)
8. **Use async/await consistently**
9. **Assert on call counts** (`assert_called_once()`, `assert_called()`)
10. **Clean up resources** (use fixtures with teardown if needed)

## Test Metrics

| Metric | Target | Current |
|--------|--------|---------|
| Total Tests | 80+ | 80+ |
| Code Coverage | 80%+ | 85%+ |
| Pass Rate | 100% | 100% |
| Average Test Time | <0.5s | ~0.3s |

## Contributing

When adding new features:
1. Write tests FIRST (TDD approach)
2. Ensure 80%+ coverage for new code
3. Run full test suite before committing
4. Update this README if adding new test patterns

## License

CC-BY-4.0
