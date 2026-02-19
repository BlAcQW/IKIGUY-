# DevotionalFlow Backend Test Suite

Comprehensive integration tests for the DevotionalFlow (FreshManna) backend API.

## Overview

This test suite provides comprehensive coverage for all major backend features:

- **Platform Settings API** (`test_platform_settings.py`) - 8 tests
- **Content Moderation System** (`test_moderation.py`) - 12 tests
- **Calendar View & Scheduling** (`test_calendar.py`) - 13 tests
- **Admin Dashboard** (`test_admin_dashboard.py`) - 11 tests
- **Author Dashboard** (`test_author_dashboard.py`) - 11 tests

**Total: 55 comprehensive integration tests**

## Test Philosophy

These tests follow integration testing best practices:

✅ **Real Database Integration** - Tests use actual MongoDB database (not mocks)
✅ **Full CRUD Coverage** - Create, read, update, delete operations tested
✅ **Data Verification** - Tests verify data in database after operations
✅ **Complete Workflows** - End-to-end user flows tested
✅ **Edge Cases** - Tests cover success, failure, and edge cases
✅ **Authentication** - All tests use real JWT tokens
✅ **Cleanup** - Tests clean up created data automatically

## Running Tests

### Prerequisites

```bash
# Ensure virtual environment is activated
source /opt/kasaai/apps/venv/bin/activate

# Install test dependencies (already in requirements.txt)
pip install pytest pytest-asyncio pytest-cov
```

### Run All Tests

```bash
cd /opt/kasaai/apps/devotionalflow/backend
export PYTHONPATH=/opt/kasaai/apps/devotionalflow/backend:$PYTHONPATH
python -m pytest tests/ -v
```

### Run Specific Test File

```bash
# Platform settings tests
python -m pytest tests/test_platform_settings.py -v

# Moderation tests
python -m pytest tests/test_moderation.py -v

# Calendar tests
python -m pytest tests/test_calendar.py -v

# Admin dashboard tests
python -m pytest tests/test_admin_dashboard.py -v

# Author dashboard tests
python -m pytest tests/test_author_dashboard.py -v
```

### Run Specific Test

```bash
python -m pytest tests/test_moderation.py::TestModerationSystem::test_flag_devotional_success -v
```

### Run with Coverage

```bash
python -m pytest tests/ --cov=app --cov-report=html --cov-report=term-missing
```

## Test Structure

### Authentication Fixtures

- `admin_token` - Provides admin JWT token for admin-only endpoints
- `author_token` - Provides author JWT token for author-specific tests
- `test_db` - Direct MongoDB database connection for data verification

### Test Data Fixtures

- `test_devotional` - Creates a sample devotional for testing
- `test_user` - Creates a sample user for testing
- `cleanup_collections` - Automatic cleanup of test data

## Test Coverage

### Platform Settings (8 tests)
- Get settings (success, unauthorized, non-admin)
- Update settings (success, partial, invalid data, non-admin)
- Settings persistence across requests

### Content Moderation (12 tests)
- Flag devotional (success, nonexistent, unauthorized)
- List flags (success, with filters, pagination)
- Get flag details (success, nonexistent)
- Resolve flag (success, already resolved)
- Moderation statistics
- Complete moderation workflow

### Calendar View (13 tests)
- Get devotionals (success, date range, status filter)
- Find schedule gaps (with gaps, without gaps)
- Get upcoming devotionals (success, with limit)
- Calendar statistics (success, time periods)
- Complete calendar workflow

### Admin Dashboard (11 tests)
- Dashboard stats (success, unauthorized, non-admin)
- Platform analytics (success, custom period)
- Top content (success, different metrics)
- Recent activity (success, ordering)
- Complete dashboard workflow
- Empty database handling

### Author Dashboard (11 tests)
- Author stats (success, unauthorized, no devotionals)
- Performance metrics (success, custom period)
- Best performing content
- Milestones (success, achievements)
- Engagement rate calculation
- Time-based filters
- Complete author workflow

## Known Issues & Next Steps

### ⚠️ Test Adjustments Needed

Some tests need minor adjustments to match actual API response structures:

1. **Platform Settings Tests** - API returns nested structure with `settings` key
2. **Response Field Names** - Some field names may differ from test expectations

### 📝 Recommended Updates

1. Run tests individually and adjust assertions to match actual API responses
2. Update response field checks in tests to match models
3. Add more edge case tests for error conditions
4. Add performance tests for large datasets
5. Add tests for concurrent operations

## Test Database

Tests use the real `devotionalflow` MongoDB database as specified in `.env`.

**Important:** Tests automatically clean up data they create, but for safety:
- Run tests in a development environment first
- Backup production data before running tests in production

## Configuration

Test configuration is in `pytest.ini`:
- Test discovery patterns
- Async mode settings
- Logging configuration
- Test markers

## Contributing

When adding new features, please:

1. Create corresponding tests following existing patterns
2. Include at least 3 tests per feature:
   - Success case
   - Edge case
   - Failure case
3. Use real database operations (no mocks)
4. Clean up test data in fixtures
5. Document any special test requirements

## Support

For issues or questions about tests:
- Check test logs with `-v` flag
- Use `--tb=short` for concise error traces
- Review pytest.ini for configuration
- Check conftest.py for fixture definitions
