# Member Creation Flow Testing Guide

This document describes how to test the member creation flows in ChurchFlow.

## Test Script

A comprehensive test script has been created at:
```
apps/churchflow/scripts/test_member_creation_flows.py
```

## Prerequisites

1. **Admin Token**: You need a valid admin authentication token
   - Log in to the admin interface
   - Open browser DevTools → Application → Local Storage
   - Copy the `access_token` value

2. **API Base URL**: 
   - Production: `https://churchflow.ailabsafrica.com/api/v1`
   - Local: `http://localhost:30030/api/v1`

## Running the Tests

```bash
cd /opt/kasaai/apps/churchflow/scripts
python3 test_member_creation_flows.py
```

The script will:
1. Prompt for admin token (or set `ADMIN_TOKEN` in the script)
2. Get organization ID and branch ID automatically
3. Run all test scenarios
4. Display colored output with results
5. Provide a summary at the end

## Test Scenarios

### 1. Visitor CRUD Operations

Tests the visitor capture and management API:

- **CREATE Visitor**
  - Endpoint: `POST /api/v1/visitors`
  - Creates a visitor with `member_status: "visitor"`
  - Sets `current_spiritual_stage: "first_timer"`
  
- **READ Visitor**
  - Endpoint: `GET /api/v1/visitors/{user_id}`
  - Retrieves visitor details with journey history
  
- **UPDATE Visitor**
  - Endpoint: `PUT /api/v1/visitors/{user_id}`
  - Updates visitor information

**Expected Result**: Visitor created, retrieved, and updated successfully

### 2. First Timer CRUD Operations

Tests the first timer management API:

- **CREATE First Timer**
  - Endpoint: `POST /api/v1/first-timers`
  - Creates a FirstTimer record (separate collection)
  - Required fields: `first_name`, `last_name`, `phone`, `interest_type`
  
- **READ First Timer**
  - Endpoint: `GET /api/v1/first-timers/{first_timer_id}`
  - Retrieves first timer details
  
- **UPDATE First Timer**
  - Endpoint: `PUT /api/v1/first-timers/{first_timer_id}`
  - Updates first timer information
  
- **LIST First Timers**
  - Endpoint: `GET /api/v1/first-timers?page=1&page_size=10`
  - Lists paginated first timers

**Expected Result**: First timer created, retrieved, updated, and listed successfully

### 3. Visitor → Member Conversion

Tests converting a visitor to an active member:

- **Endpoint**: `POST /api/v1/users/{user_id}/transition-to-member`
- **Request Body**: `{"branch_id": "<branch_id>"}`
- **What it does**:
  - Updates `member_status` from "visitor" to "active_member"
  - Assigns `branch_id`
  - Updates `current_spiritual_stage` to "new_convert" if still first/second timer
  - Sets `transitioned_to_member_at` timestamp

**Expected Result**: Visitor successfully converted to member with branch assignment

### 4. First Timer → Member Conversion

Tests converting a first timer to a full member:

- **Endpoint**: `POST /api/v1/first-timers/{first_timer_id}/convert-to-member`
- **Request Body**: `{"role": "member"}`
- **What it does**:
  1. Checks if user exists by phone/email
  2. Creates new User if doesn't exist, or links to existing User
  3. Transfers first timer data to User profile
  4. Marks first timer as converted (`converted_to_member: true`)
  5. Sets `member_status: "active_member"`

**Expected Result**: First timer converted to member, User record created/linked

### 5. Direct Member Creation

Documents available methods for direct member creation:

- **POST /api/v1/users/me** (requires authenticated user)
  - Creates user profile after phone OTP verification
  - Requires: authenticated user with phone
  - Body: `{"name": "...", "branch_id": "...", "volunteer_roles": []}`

**Note**: There's no public admin endpoint for direct member creation. Members are typically created through:
1. Visitor capture → transition to member
2. First timer → convert to member
3. User profile creation (after authentication)

## API Endpoints Summary

### Visitors
- `POST /api/v1/visitors` - Capture visitor (admin, coordinator, cell_leader, zone_leader)
- `GET /api/v1/visitors` - List visitors
- `GET /api/v1/visitors/{user_id}` - Get visitor details
- `PUT /api/v1/visitors/{user_id}` - Update visitor

### First Timers
- `POST /api/v1/first-timers` - Create first timer (admin)
- `GET /api/v1/first-timers` - List first timers (admin)
- `GET /api/v1/first-timers/{first_timer_id}` - Get first timer (admin)
- `PUT /api/v1/first-timers/{first_timer_id}` - Update first timer (admin)
- `POST /api/v1/first-timers/{first_timer_id}/convert-to-member` - Convert to member (admin)

### Members
- `POST /api/v1/users/{user_id}/transition-to-member` - Convert visitor to member
- `POST /api/v1/users/me` - Create user profile (authenticated user)

## Expected Test Results

When running the test script, you should see:

```
✅ PASS - Visitor Crud
✅ PASS - First Timer Crud
✅ PASS - Visitor To Member
✅ PASS - First Timer To Member
✅ PASS - Direct Member

Total: 5/5 tests passed
✅ All tests passed! 🎉
```

## Common Issues

### Issue: "No branch_id available"
**Solution**: The conversion to member requires a branch_id. The script will try to get one automatically, but if none exist, you'll need to create a branch first or skip the conversion test.

### Issue: "401 Unauthorized"
**Solution**: Make sure your admin token is valid and hasn't expired. Get a new token from the browser.

### Issue: "403 Forbidden"
**Solution**: Ensure your user has the required role (admin for most operations).

### Issue: "404 Not Found"
**Solution**: Check that the IDs being used are correct and the resources exist.

## Manual Testing

If you prefer to test manually, you can use curl:

```bash
# 1. Create Visitor
curl -X POST "https://churchflow.ailabsafrica.com/api/v1/visitors" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "+233501234567",
    "name": "Test Visitor",
    "full_name": "Test Visitor User",
    "email": "visitor@test.com",
    "first_visit_source": "Friend invitation"
  }'

# 2. Create First Timer
curl -X POST "https://churchflow.ailabsafrica.com/api/v1/first-timers" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Test",
    "last_name": "FirstTimer",
    "phone": "+233502345678",
    "email": "firsttimer@test.com",
    "interest_type": "new_convert",
    "wants_membership": true
  }'

# 3. Convert Visitor to Member
curl -X POST "https://churchflow.ailabsafrica.com/api/v1/users/VISITOR_ID/transition-to-member" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"branch_id": "BRANCH_ID"}'

# 4. Convert First Timer to Member
curl -X POST "https://churchflow.ailabsafrica.com/api/v1/first-timers/FIRST_TIMER_ID/convert-to-member" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"role": "member"}'
```

## Next Steps

After running tests:
1. Review the test output
2. Document any issues found
3. Fix any bugs discovered
4. Update documentation if API behavior differs from expectations

