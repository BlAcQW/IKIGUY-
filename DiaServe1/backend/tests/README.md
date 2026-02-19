# EstateFlow Test Suite

Comprehensive test suite for the EstateFlow booking system, covering agents, bookings, notifications, and reminder workflows.

## 📊 Test Coverage

### Test Files
- `test_agents.py` - Agent CRUD operations and auto-assignment (15 tests)
- `test_bookings.py` - Booking lifecycle and status transitions (33 tests)
- `test_notifications.py` - Email templates and delivery (10 tests)
- `test_reminders.py` - Reminder scheduling and processing (10 tests)
- `test_properties.py` - Property CRUD and search (existing tests)

**Total: 68+ test functions**

### Coverage Areas

#### Agent Tests (`test_agents.py`)
✅ CRUD Operations
- Create agent with full data
- Create agent with duplicate email (validation)
- Get, list, update, delete agents
- Update working hours
- Deactivate agent

✅ Availability & Working Hours
- Agent availability within working hours
- Agent availability outside working hours
- Weekend availability (no schedule)

✅ Organization Isolation
- Agents scoped to organizations

✅ Edge Cases
- Missing required fields
- Invalid working hours format

#### Booking Tests (`test_bookings.py`)
✅ CRUD Operations
- Create booking with full data
- Create booking with agent assignment
- Get, list, update, delete bookings
- Cancel booking
- Pagination

✅ Status Transitions
- Pending → Confirmed
- Confirmed → Completed
- Invalid transitions (error handling)

✅ Agent Auto-Assignment
- Assign available agent
- Prefer agent with fewer bookings
- Respect working hours
- No agent available (waitlist)

✅ Reminders
- Automatic reminder creation (24h, 1h)
- Reminders not created for past bookings

✅ Filtering & Search
- Filter by status
- Filter by date range

✅ Organization Isolation
- Bookings scoped to organizations

#### Notification Tests (`test_notifications.py`)
✅ Email Templates
- Booking confirmation template
- Booking reminder template
- Booking cancellation template
- Template variable replacement
- Special character handling

✅ Notification Delivery
- Send confirmation email
- Send reminder email
- Send cancellation email

✅ Error Handling
- Missing recipient email
- Invalid email format

#### Reminder Tests (`test_reminders.py`)
✅ Reminder Creation
- Auto-create reminders on booking
- Skip reminders for past bookings
- Correct reminder types (24h, 1h)

✅ Reminder Processing
- Fetch pending reminders
- Process reminders successfully
- Retry logic on failure
- Concurrent processing

✅ Status Updates
- Update to 'sent'
- Update to 'failed' with error
- Track sent timestamps

✅ Edge Cases
- Skip reminders for cancelled bookings
- Handle missing contact email
- Concurrent processing safety

## 🚀 Running Tests

### Prerequisites
```bash
# Install dependencies
pip install -r requirements.txt

# Ensure MongoDB is running
mongo --version

# Set up test environment variables
cp .env.example .env.test
```

### Run All Tests
```bash
# Run entire test suite
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run with verbose output
pytest -v
```

### Run Specific Test Files
```bash
# Agent tests only
pytest tests/test_agents.py -v

# Booking tests only
pytest tests/test_bookings.py -v

# Notification tests only
pytest tests/test_notifications.py -v

# Reminder tests only
pytest tests/test_reminders.py -v
```

### Run Specific Test Categories
```bash
# Unit tests only
pytest -m unit

# Integration tests only
pytest -m integration

# Skip slow tests
pytest -m "not slow"
```

### Run Individual Tests
```bash
# Run a specific test
pytest tests/test_agents.py::test_create_agent_success -v

# Run tests matching a pattern
pytest -k "agent_availability" -v
```

## 🔧 Test Configuration

### Test Database
- Tests use a separate `estateflow_test` database
- Database is cleaned after each test for isolation
- Indexes are created to mirror production

### Fixtures (`conftest.py`)
- `test_database` - Clean test database for each test
- `test_client` - HTTP client for API testing
- `auth_headers` - Authentication headers
- `organization_context` - Multi-tenant organization data
- `sample_agent` - Agent test data
- `sample_booking` - Booking test data
- `sample_property` - Property test data
- `sample_contact` - Contact test data

### Test Markers
- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.slow` - Slow-running tests

## 📝 Writing New Tests

### Test Structure
```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
@pytest.mark.unit
async def test_example(
    test_client: AsyncClient,
    auth_headers: Dict[str, str],
    test_database
):
    """
    Test description.

    Verifies:
    - What is being tested
    - Expected behavior
    - Edge cases covered
    """
    # Create test data
    response = await test_client.post(
        "/api/v1/endpoint",
        json=test_data,
        headers=auth_headers
    )

    # Assert response
    assert response.status_code == 201

    # Verify in database
    db_record = await test_database.collection.find_one({"id": record_id})
    assert db_record is not None
```

### Best Practices
1. **Test Real Database Operations**
   - Create → Read from DB
   - Update → Verify in DB
   - Delete → Confirm removal from DB

2. **Include 3 Test Cases**
   - ✅ Expected use case
   - ⚠️  Edge case
   - ❌ Failure case

3. **Use Descriptive Names**
   ```python
   # ✅ Good
   test_create_booking_with_agent_assignment

   # ❌ Bad
   test_booking_create
   ```

4. **Document What You're Testing**
   - Clear docstring
   - List what is verified
   - Explain edge cases

5. **Clean Up After Tests**
   - Use fixtures for setup/teardown
   - Database auto-cleaned by `test_database` fixture
   - Don't leave test data behind

## 🐛 Troubleshooting

### Tests Failing with "Database not connected"
The routers need to use dependency injection instead of calling `MongoDB.get_db()` directly.

**Solution**: Refactor routers to accept `db` as a dependency parameter.

### Tests Failing with "Authentication error"
The test client needs proper auth dependency overrides.

**Solution**: Check that `conftest.py` overrides `get_current_user` correctly.

### Tests Failing with "Not Found" (404)
The API endpoint may not exist yet.

**Solution**: Implement the router endpoint before testing it.

### SMTP/Email Errors
Email sending will fail in test environment without SMTP server.

**Expected**: Notification tests handle this gracefully and verify template rendering instead.

## 📈 Coverage Goals

- **Overall Coverage**: 80%+ (target)
- **Critical Paths**: 90%+ (booking flow, reminders)
- **Edge Cases**: Well covered
- **Error Handling**: Comprehensive

### Running Coverage Report
```bash
# Generate HTML coverage report
pytest --cov=app --cov-report=html

# Open report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

## 🔄 Continuous Integration

### Pre-commit Checks
```bash
# Run before committing
pytest -x --ff  # Stop on first failure, run previously failed first
```

### CI/CD Pipeline (Recommended)
```yaml
# .github/workflows/test.yml
- name: Run tests
  run: |
    pytest --cov=app --cov-report=xml

- name: Upload coverage
  uses: codecov/codecov-action@v3
```

## 📚 Related Documentation

- [Booking System Architecture](../docs/BOOKING_SYSTEM.md)
- [Agent Auto-Assignment](../docs/AGENT_ASSIGNMENT.md)
- [Notification Templates](../docs/NOTIFICATIONS.md)
- [Reminder Worker](../docs/REMINDERS.md)

## ✅ Test Suite Status

**Created**: December 11, 2025
**Status**: ⚠️  Requires router refactoring for full execution
**Coverage**: 68 comprehensive tests written
**Next Steps**:
1. Refactor routers to use dependency injection
2. Run full test suite and verify all pass
3. Set up CI/CD pipeline
4. Track coverage metrics over time
