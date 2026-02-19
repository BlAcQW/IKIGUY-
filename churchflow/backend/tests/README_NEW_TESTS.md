# New Test Files for Session Time Fields and Registration Updates

This document describes the comprehensive test suite created for the new session time fields and registration update functionality.

## Test Files Created

### 1. test_session_time_fields.py

**Location**: `/opt/kasaai/apps/churchflow/backend/tests/test_session_time_fields.py`

**Purpose**: Unit tests for session start_time and end_time fields using real database operations.

**Test Coverage**:
- ✅ Create session with time fields
- ✅ Create session without time fields (backwards compatibility)
- ✅ Update session to add time fields
- ✅ Update session to modify existing time fields
- ✅ Retrieve session and verify time fields included
- ✅ List sessions and verify all have time fields
- ✅ Delete session with time fields
- ✅ Time format validation (HH:MM format variations)

**Total Tests**: 8 test cases

**What It Tests**:
- Full CRUD cycle for sessions with time fields
- Backwards compatibility with sessions without times
- Database persistence of time fields
- Time format validation and handling
- Edge cases (00:00, 23:59, etc.)

**How to Run**:
```bash
cd /opt/kasaai/apps/churchflow/backend
export PYTHONPATH=/opt/kasaai/apps/churchflow/backend:$PYTHONPATH
/opt/kasaai/apps/venv/bin/python -m pytest tests/test_session_time_fields.py -v
```

### 2. test_registration_updates.py

**Location**: `/opt/kasaai/apps/churchflow/backend/tests/test_registration_updates.py`

**Purpose**: Unit tests for registration update functionality including all editable fields.

**Test Coverage**:
- ✅ Update registration name
- ✅ Update registration phone (with normalization)
- ✅ Phone validation on invalid input
- ✅ Update registration email
- ✅ Update church_name field
- ✅ Update special_needs field
- ✅ Update multiple fields simultaneously
- ✅ Preserve untouched fields during partial updates
- ✅ Handle non-existent registration (404)
- ✅ Clear optional fields (set to None)
- ✅ Verify updated_at timestamp changes
- ✅ Retrieve registration after update confirms changes

**Total Tests**: 12 test cases

**What It Tests**:
- Full UPDATE operations for all editable registration fields
- Phone number normalization (local → international format)
- Phone number validation
- Partial updates (only specified fields change)
- Field preservation (unspecified fields stay unchanged)
- Optional field handling (can be cleared)
- Timestamp tracking (updated_at field)
- Data persistence and retrieval after updates

**How to Run**:
```bash
cd /opt/kasaai/apps/churchflow/backend
export PYTHONPATH=/opt/kasaai/apps/churchflow/backend:$PYTHONPATH
/opt/kasaai/apps/venv/bin/python -m pytest tests/test_registration_updates.py -v
```

### 3. test_session_registration_api_crud.py

**Location**: `/opt/kasaai/apps/churchflow/backend/scripts/test_session_registration_api_crud.py`

**Purpose**: Integration test script that tests the complete API endpoints with real HTTP requests and real data.

**Test Coverage**:

**Session Time Fields Tests**:
1. Create session with time fields (POST /conferences/{id}/sessions)
2. Retrieve session with time fields (GET /conferences/{id}/sessions/{session_id})
3. Update session time fields (PUT /conferences/{id}/sessions/{session_id})
4. List sessions with time fields (GET /conferences/{id}/sessions)
5. Create session without time fields - backwards compatibility
6. Delete session (DELETE /conferences/{id}/sessions/{session_id})
7. Verify deletion (GET returns 404)

**Registration Update Tests**:
1. Create registration (POST /conferences/{id}/register)
2. Update name (PUT /registrations/{id})
3. Update phone with normalization (PUT /registrations/{id})
4. Update email (PUT /registrations/{id})
5. Update church_name and special_needs (PUT /registrations/{id})
6. Update multiple fields at once (PUT /registrations/{id})
7. Retrieve and verify all updates persisted (GET /registrations/{id})

**Total Integration Tests**: 14 HTTP request/response cycles

**What It Tests**:
- Real HTTP API endpoints
- Request/response formats
- Status codes (201, 200, 404, 204)
- Data serialization (JSON)
- Phone number normalization via API
- Time field persistence through API
- Full end-to-end CRUD workflows
- Backwards compatibility

**How to Run**:
```bash
cd /opt/kasaai/apps/churchflow/backend
/opt/kasaai/apps/venv/bin/python scripts/test_session_registration_api_crud.py
```

**Note**: This script requires authentication. Update the `TEST_TOKEN` variable with a valid admin JWT token from the ChurchFlow API to run full tests.

## Test Methodology

### Unit Tests (test_session_time_fields.py, test_registration_updates.py)

**Approach**:
- Uses pytest with motor AsyncIO MongoDB driver
- Tests interact directly with MongoDB test database
- Each test has isolated database state (cleaned before/after)
- Uses real MongoDB CRUD operations
- No mocks - tests actual service layer code

**Benefits**:
- Tests real database interactions
- Catches serialization issues
- Verifies data persistence
- Tests edge cases with actual data

### Integration Tests (test_session_registration_api_crud.py)

**Approach**:
- Uses Python requests library for HTTP calls
- Tests against running API server
- Creates real conference, sessions, registrations
- Tests full request/response cycle
- Can test against local or production API

**Benefits**:
- End-to-end validation
- Tests API contracts
- Verifies request/response formats
- Tests authentication/authorization
- Catches API-level bugs

## Test Data

All tests use **real data**:

### Session Test Data
```python
{
    "name": "Morning Worship with Times",
    "description": "Test session with start and end times",
    "location": "Main Auditorium",
    "day_number": 1,
    "day_label": "Day 1 - Opening",
    "session_date": "2025-12-25T09:00:00",
    "start_time": "09:00",
    "end_time": "11:30",
    "order": 1,
    "sms_confirmation_enabled": True
}
```

### Registration Test Data
```python
{
    "user_name": "Original Test User",
    "user_phone": "+233244123456",
    "user_email": "original@test.com",
    "church_name": "Original Church",
    "special_needs": "Original special needs"
}
```

## Expected Test Results

### Success Criteria
- ✅ All session CRUD operations work with time fields
- ✅ Time fields are optional (backwards compatible)
- ✅ Time fields persist correctly in database
- ✅ Times display in API responses
- ✅ All registration fields can be updated individually
- ✅ Multiple registration fields can be updated together
- ✅ Phone numbers are validated and normalized
- ✅ Optional fields can be cleared
- ✅ Untouched fields remain unchanged
- ✅ All updates persist to database

### Test Assertions
Each test includes multiple assertions to verify:
1. Correct data is returned
2. Correct data is stored in database
3. Data types are correct
4. Normalization happened (for phone numbers)
5. Timestamps are updated
6. Related fields are preserved

## Running All Tests

To run the complete test suite:

```bash
# From backend directory
cd /opt/kasaai/apps/churchflow/backend

# Set Python path
export PYTHONPATH=/opt/kasaai/apps/churchflow/backend:$PYTHONPATH

# Run all new tests
/opt/kasaai/apps/venv/bin/python -m pytest tests/test_session_time_fields.py tests/test_registration_updates.py -v

# Run integration tests (requires auth token)
/opt/kasaai/apps/venv/bin/python scripts/test_session_registration_api_crud.py
```

## Test Database

Tests use a separate test database: `churchflow_test`

**Connection String**: `mongodb://admin:aawwER4444%@127.0.0.1:27017/churchflow_test?authSource=admin`

**Important**: Test database is automatically cleaned before and after each test to ensure isolation.

## Coverage Summary

### Features Tested
1. ✅ Session time fields (start_time, end_time)
2. ✅ Registration updates (all editable fields)
3. ✅ Phone number validation and normalization
4. ✅ Backwards compatibility
5. ✅ Database persistence
6. ✅ API endpoints
7. ✅ Data serialization
8. ✅ Error handling

### CRUD Operations Tested
- **CREATE**: Sessions with/without times, Registrations
- **READ**: Individual sessions/registrations, Lists of sessions
- **UPDATE**: Session times, All registration fields
- **DELETE**: Sessions with time fields

### Total Test Count
- Unit Tests: 20 test cases (8 session + 12 registration)
- Integration Tests: 14 API workflow tests
- **Total: 34 comprehensive tests**

## Next Steps

To ensure robustness:

1. Run tests regularly during development
2. Add tests to CI/CD pipeline
3. Monitor test coverage
4. Add edge case tests as discovered
5. Keep tests updated as features evolve

## Test Maintenance

When modifying session or registration features:

1. Update corresponding tests
2. Add new test cases for new functionality
3. Verify backwards compatibility tests still pass
4. Update test data if schema changes
5. Document any new test requirements
