# Test Template for New Features

**Purpose**: Ensure every new feature, component, service, and CRUD operation has comprehensive test coverage matching TEST_SUITE_ANALYSIS.md standards.

**Target Coverage**: 80%+ with real database tests (not mocks)

**Date Created**: 2025-10-26
**Last Updated**: 2025-10-26

---

## Quick Checklist

When adding a new feature, create tests for:

- [ ] **Unit Tests** - Test individual functions/methods in isolation
- [ ] **Integration Tests** - Test component interactions
- [ ] **Database Tests** - Test actual CRUD operations (not mocks)
- [ ] **Shared Library Tests** - If using @apps/shared/, add integration tests
- [ ] **API Endpoint Tests** - Test HTTP requests/responses
- [ ] **Error Handling Tests** - Test failure scenarios
- [ ] **Edge Cases** - Test boundary conditions

---

## Test File Structure

```python
"""
Tests for [Feature Name].

Author: [Your Name]
Date: [Date]
Priority: [CRITICAL/HIGH/MEDIUM/LOW]

Test Coverage:
- Unit tests: [description]
- Integration tests: [description]
- Database tests: [description]
- API tests: [description]
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import asyncio

# Import the code being tested
from backend.services.your_service import YourService
from backend.models.your_model import YourModel

# Import shared library dependencies (if any)
from apps.shared.integration.wallet import WalletService


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def sample_data():
    """Sample test data."""
    return {
        "id": "test_123",
        "name": "Test Item",
        "value": 100
    }


@pytest.fixture
async def service_instance():
    """Create service instance for testing."""
    service = YourService()
    await service.initialize()
    yield service
    await service.cleanup()


# =============================================================================
# UNIT TESTS
# =============================================================================

class TestYourServiceUnit:
    """Unit tests for YourService - test methods in isolation."""

    @pytest.mark.unit
    def test_validation_logic(self, sample_data):
        """Test input validation."""
        service = YourService()

        # Test valid input
        result = service.validate(sample_data)
        assert result is True

        # Test invalid input
        invalid_data = {"id": None}
        result = service.validate(invalid_data)
        assert result is False

    @pytest.mark.unit
    async def test_processing_logic(self, sample_data):
        """Test core processing logic."""
        service = YourService()

        result = await service.process(sample_data)

        assert result is not None
        assert result["status"] == "success"

    @pytest.mark.unit
    def test_error_handling(self):
        """Test error scenarios."""
        service = YourService()

        # Test with invalid data
        with pytest.raises(ValueError):
            service.process(None)


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestYourServiceIntegration:
    """Integration tests - test component interactions."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_service_with_dependencies(self, service_instance, sample_data):
        """Test service with real dependencies."""
        # Test interaction with other services
        result = await service_instance.execute_workflow(sample_data)

        assert result is not None
        assert result["dependencies_called"] is True

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_event_chain(self, service_instance):
        """Test event propagation through system."""
        # Create event
        event = await service_instance.create_event("test_event")

        # Verify event processing
        status = await service_instance.get_event_status(event["id"])
        assert status == "processed"


# =============================================================================
# DATABASE TESTS (REAL DATABASE - NOT MOCKS!)
# =============================================================================

class TestYourServiceDatabase:
    """Database tests - test actual CRUD operations."""

    @pytest.mark.database
    @pytest.mark.asyncio
    async def test_crud_create(self, sample_data):
        """Test CREATE operation with real database."""
        service = YourService()

        # CREATE
        created = await service.create(sample_data)
        assert created is not None
        assert created["id"] is not None

        # Verify in database
        db_record = await service.get(created["id"])
        assert db_record["name"] == sample_data["name"]

        # CLEANUP
        await service.delete(created["id"])

    @pytest.mark.database
    @pytest.mark.asyncio
    async def test_crud_read(self, sample_data):
        """Test READ operation with real database."""
        service = YourService()

        # Create test data
        created = await service.create(sample_data)

        # READ
        fetched = await service.get(created["id"])
        assert fetched is not None
        assert fetched["id"] == created["id"]
        assert fetched["name"] == sample_data["name"]

        # CLEANUP
        await service.delete(created["id"])

    @pytest.mark.database
    @pytest.mark.asyncio
    async def test_crud_update(self, sample_data):
        """Test UPDATE operation with real database."""
        service = YourService()

        # Create test data
        created = await service.create(sample_data)

        # UPDATE
        updated_data = {"name": "Updated Name"}
        updated = await service.update(created["id"], updated_data)
        assert updated["name"] == "Updated Name"

        # Verify in database
        db_record = await service.get(created["id"])
        assert db_record["name"] == "Updated Name"

        # CLEANUP
        await service.delete(created["id"])

    @pytest.mark.database
    @pytest.mark.asyncio
    async def test_crud_delete(self, sample_data):
        """Test DELETE operation with real database."""
        service = YourService()

        # Create test data
        created = await service.create(sample_data)
        created_id = created["id"]

        # DELETE
        await service.delete(created_id)

        # Verify deleted
        deleted_record = await service.get(created_id)
        assert deleted_record is None

    @pytest.mark.database
    @pytest.mark.asyncio
    async def test_database_constraints(self, sample_data):
        """Test database constraints (unique indexes, etc)."""
        service = YourService()

        # Create first record
        first = await service.create(sample_data)

        # Try to create duplicate (should fail)
        with pytest.raises(Exception):  # Adjust exception type
            await service.create(sample_data)

        # CLEANUP
        await service.delete(first["id"])


# =============================================================================
# SHARED LIBRARY INTEGRATION TESTS
# =============================================================================

class TestSharedLibraryIntegration:
    """Test integration with @apps/shared/ library."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_wallet_service_integration(self):
        """Test WalletService integration from shared library."""
        from apps.shared.integration.wallet import WalletService

        wallet_service = WalletService()

        # Test expected interface
        assert hasattr(wallet_service, 'create_wallet')
        assert hasattr(wallet_service, 'get_balance')
        assert hasattr(wallet_service, 'add_funds')
        assert hasattr(wallet_service, 'deduct_funds')

    @pytest.mark.integration
    def test_shared_library_import(self):
        """Verify shared library imports work."""
        try:
            from apps.shared.services.your_dependency import YourDependency
            assert YourDependency is not None
        except ImportError as e:
            pytest.fail(f"Failed to import from shared library: {e}")


# =============================================================================
# API ENDPOINT TESTS
# =============================================================================

class TestYourAPIEndpoints:
    """Test API endpoints."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_create_endpoint(self, client, sample_data, auth_header):
        """Test POST endpoint."""
        response = await client.post(
            "/api/your-endpoint",
            json=sample_data,
            headers=auth_header
        )

        assert response.status_code == 201
        data = response.json()
        assert data["id"] is not None

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_endpoint(self, client, auth_header):
        """Test GET endpoint."""
        response = await client.get(
            "/api/your-endpoint/123",
            headers=auth_header
        )

        assert response.status_code == 200
        data = response.json()
        assert data is not None

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_endpoint_authorization(self, client):
        """Test endpoint requires authentication."""
        response = await client.get("/api/your-endpoint/123")

        assert response.status_code == 401  # Unauthorized


# =============================================================================
# ERROR HANDLING TESTS
# =============================================================================

class TestErrorHandling:
    """Test error scenarios and edge cases."""

    @pytest.mark.unit
    def test_invalid_input(self):
        """Test handling of invalid input."""
        service = YourService()

        with pytest.raises(ValueError):
            service.process(None)

        with pytest.raises(ValueError):
            service.process({"invalid": "data"})

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_network_failure(self, service_instance):
        """Test handling of network failures."""
        # Mock network failure
        with patch('httpx.AsyncClient.post', side_effect=ConnectionError()):
            with pytest.raises(Exception):  # Adjust exception type
                await service_instance.call_external_service()

    @pytest.mark.database
    @pytest.mark.asyncio
    async def test_database_failure(self):
        """Test handling of database failures."""
        service = YourService()

        # Test with invalid connection
        with pytest.raises(Exception):
            await service.connect_to_invalid_db()


# =============================================================================
# EDGE CASES
# =============================================================================

class TestEdgeCases:
    """Test boundary conditions and edge cases."""

    @pytest.mark.unit
    def test_empty_input(self):
        """Test with empty input."""
        service = YourService()
        result = service.process([])
        assert result == []

    @pytest.mark.unit
    def test_large_input(self):
        """Test with very large input."""
        service = YourService()
        large_data = [{"id": i} for i in range(10000)]
        result = service.process(large_data)
        assert len(result) == 10000

    @pytest.mark.unit
    def test_unicode_characters(self):
        """Test with unicode/special characters."""
        service = YourService()
        data = {"name": "Test 测试 🎉"}
        result = service.process(data)
        assert result["name"] == "Test 测试 🎉"


# =============================================================================
# TEST SUMMARY
# =============================================================================

"""
Test Coverage Summary:
======================

1. Unit Tests (3 test classes, 10+ tests)
   - Validation logic
   - Processing logic
   - Error handling

2. Integration Tests (2 test classes, 5+ tests)
   - Service dependencies
   - Event propagation

3. Database Tests (1 test class, 5 tests)
   - CRUD operations (CREATE, READ, UPDATE, DELETE)
   - Database constraints

4. Shared Library Tests (1 test class, 2 tests)
   - Integration verification
   - Import checks

5. API Tests (1 test class, 3 tests)
   - Endpoint functionality
   - Authorization

6. Error Handling (1 test class, 3 tests)
   - Invalid input
   - Network failures
   - Database failures

7. Edge Cases (1 test class, 3 tests)
   - Empty input
   - Large input
   - Special characters

Total: 9 test classes, 30+ tests

Running these tests:
===================

# Run all tests for this feature
pytest tests/test_your_feature.py -v

# Run only unit tests
pytest tests/test_your_feature.py -m unit -v

# Run only integration tests
pytest tests/test_your_feature.py -m integration -v

# Run only database tests
pytest tests/test_your_feature.py -m database -v

# Run with coverage
pytest tests/test_your_feature.py --cov=backend.services.your_service -v

# Run in CI/CD
pytest tests/test_your_feature.py -v --tb=short
"""
