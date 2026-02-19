# Integration Tests - Real Service Testing

This directory contains **real integration tests** that connect to actual services (not mocks).

## Overview

Unlike unit tests which use mocks, these tests:
- ✅ Connect to real MongoDB test database
- ✅ Upload/download files to real storage
- ✅ Make actual HTTP requests to running API
- ✅ Test real authentication flows

## Prerequisites

### 1. Test MongoDB Instance

Set up a dedicated test MongoDB database:

```bash
# Option A: Use existing MongoDB with test database
export TEST_MONGODB_URL="mongodb://admin:aawwER444444@127.0.0.1:27017/kasaai_test?authSource=admin"

# Option B: Use Docker for isolated test database
docker run -d --name mongodb-test \
  -p 27018:27017 \
  -e MONGO_INITDB_ROOT_USERNAME=test \
  -e MONGO_INITDB_ROOT_PASSWORD=testpass \
  mongo:latest
```

### 2. Test Storage Bucket

Configure test storage (MinIO or S3):

```bash
# For MinIO test instance
export TEST_STORAGE_ENDPOINT="localhost:9000"
export TEST_STORAGE_ACCESS_KEY="minioadmin"
export TEST_STORAGE_SECRET_KEY="minioadmin"
export TEST_STORAGE_BUCKET="test-kasaai-community"
```

### 3. Test Supabase Project

Use Supabase test project or local instance:

```bash
export TEST_SUPABASE_URL="https://test-project.supabase.co"
export TEST_SUPABASE_KEY="test-anon-key"
export TEST_SUPABASE_SERVICE_KEY="test-service-key"
```

### 4. Environment File

Create `.env.test` file:

```bash
# Database
TEST_MONGODB_URL=mongodb://admin:aawwER444444@127.0.0.1:27017/kasaai_test?authSource=admin

# Storage
TEST_STORAGE_ENDPOINT=localhost:9000
TEST_STORAGE_ACCESS_KEY=minioadmin
TEST_STORAGE_SECRET_KEY=minioadmin
TEST_STORAGE_BUCKET=test-kasaai-community

# Auth
TEST_SUPABASE_URL=https://test-project.supabase.co
TEST_SUPABASE_KEY=test-anon-key

# API
TEST_API_BASE_URL=http://localhost:8001
```

## Running Integration Tests

### Run All Integration Tests

```bash
# From backend directory
pytest tests/integration/ -v

# With verbose output
pytest tests/integration/ -vv -s

# Run specific test file
pytest tests/integration/test_mongodb_integration.py -v

# Run specific test
pytest tests/integration/test_mongodb_integration.py::TestMongoDBIntegration::test_create_user -v
```

### Run with Coverage

```bash
pytest tests/integration/ --cov=routers --cov=models --cov-report=html
```

### Skip Integration Tests

Integration tests are marked with `@pytest.mark.integration`:

```bash
# Run only unit tests (skip integration)
pytest tests/ -m "not integration"

# Run only integration tests
pytest tests/ -m integration
```

## Test Structure

```
tests/integration/
├── README.md                          # This file
├── conftest.py                        # Integration test fixtures
├── test_mongodb_integration.py        # Real MongoDB tests (15 tests)
├── test_storage_integration.py        # Real file storage tests (10 tests)
├── test_auth_integration.py           # Real authentication tests (10 tests)
└── test_api_e2e.py                    # End-to-end API tests (10 tests)
```

## Test Categories

### 1. MongoDB Integration Tests (15 tests)
- Database connection
- CRUD operations
- Transactions
- Indexes
- Query performance
- Data integrity

### 2. Storage Integration Tests (10 tests)
- File upload
- File download
- File deletion
- Storage quota
- File metadata
- Large file handling

### 3. Authentication Integration Tests (10 tests)
- User registration
- Login flow
- JWT validation
- Token refresh
- Session management
- Permission checks

### 4. End-to-End API Tests (10 tests)
- Multi-step workflows
- Error handling
- Rate limiting
- Data consistency
- Concurrent operations

## Safety Guidelines

⚠️ **Important:**
- These tests modify real data - use dedicated test databases
- Always clean up test data after tests
- Never run against production databases
- Use transaction rollbacks where possible
- Isolate test data with unique prefixes

## Cleanup

After tests complete:
- Test data is automatically cleaned up
- Test database is reset
- Uploaded files are deleted
- Test users are removed

## CI/CD Integration

Configure CI/CD to run integration tests:

```yaml
# .github/workflows/integration-tests.yml
name: Integration Tests
on: [push, pull_request]

jobs:
  integration:
    runs-on: ubuntu-latest
    services:
      mongodb:
        image: mongo:latest
        ports:
          - 27017:27017
    steps:
      - uses: actions/checkout@v2
      - name: Run Integration Tests
        run: pytest tests/integration/ -v
```

## Troubleshooting

### MongoDB Connection Issues
```bash
# Check MongoDB is running
mongosh "mongodb://admin:aawwER444444@127.0.0.1:27017/kasaai_test?authSource=admin"

# Verify test database exists
use kasaai_test
db.stats()
```

### Storage Connection Issues
```bash
# Test MinIO connection
mc alias set test-minio http://localhost:9000 minioadmin minioadmin
mc ls test-minio
```

### API Connection Issues
```bash
# Check API is running
curl http://localhost:8001/health

# Check test endpoint
curl http://localhost:8001/api/v1/health
```

## Next Steps

After Phase 2 completion:
- Phase 3: E2E User Journey Tests (42 tests)
- Phase 4: Performance Tests (41 tests)
- Phase 5: Security Tests (55 tests)
- Phase 6: Edge Case Tests (26 tests)
- Phase 7: CI/CD Integration

See `QA_TEST_PLAN.md` for complete testing roadmap.
