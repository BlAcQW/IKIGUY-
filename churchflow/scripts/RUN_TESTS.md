# How to Run Member Creation Flow Tests

## Quick Start

The test script requires an admin authentication token. Choose one of these methods:

### Method 1: Extract Token from Browser (Easiest)

1. **Log in to the application**:
   - Go to https://churchflow.ailabsafrica.com (or your local instance)
   - Log in with admin credentials

2. **Get the token**:
   - Open browser DevTools (Press F12)
   - Go to **Application** tab (Chrome) or **Storage** tab (Firefox)
   - Select **Local Storage** → `https://churchflow.ailabsafrica.com`
   - Find `access_token` in the list
   - Copy its value

3. **Run the tests**:
   ```bash
   cd /opt/kasaai/apps/churchflow/scripts
   export ADMIN_TOKEN='your_token_here'
   python3 test_member_creation_flows.py
   ```

### Method 2: Use Helper Script (If you have admin credentials)

If you have admin email and password, use the helper script:

```bash
cd /opt/kasaai/apps/churchflow/scripts
python3 get_admin_token.py admin@example.com your_password
```

This will output a token. Then run:

```bash
export ADMIN_TOKEN='token_from_helper_script'
python3 test_member_creation_flows.py
```

### Method 3: Pass Token as Command-Line Argument

```bash
cd /opt/kasaai/apps/churchflow/scripts
python3 test_member_creation_flows.py 'your_token_here'
```

## What the Tests Do

The test script will:

1. ✅ **Test Visitor CRUD**: Create, read, update a visitor
2. ✅ **Test First Timer CRUD**: Create, read, update, list first timers
3. ✅ **Test Visitor → Member**: Convert a visitor to an active member
4. ✅ **Test First Timer → Member**: Convert a first timer to a member
5. ✅ **Test Direct Member Creation**: Document available methods

## Expected Output

You should see colored output like:

```
🧪 Testing Visitor CRUD Operations
✅ Visitor created: 60d5ec49f8c7a4b8c8e8e8e8
✅ Visitor retrieved: Test Visitor
✅ Visitor updated: Updated Test Visitor

🧪 Testing First Timer CRUD Operations
✅ First timer created: 60d5ec49f8c7a4b8c8e8e8e9
...

============================================================
Test Summary
============================================================
✅ PASS - Visitor Crud
✅ PASS - First Timer Crud
✅ PASS - Visitor To Member
✅ PASS - First Timer To Member
✅ PASS - Direct Member

Total: 5/5 tests passed
✅ All tests passed! 🎉
```

## Troubleshooting

### "No token provided"
- Make sure you set the `ADMIN_TOKEN` environment variable or pass it as an argument

### "401 Unauthorized"
- Your token may have expired. Get a fresh token from the browser.

### "403 Forbidden"
- Your user may not have admin role. Use an admin account.

### "No branch_id available"
- The visitor-to-member conversion requires a branch_id. Create a branch first or the test will skip this conversion.

## Notes

- Tests use unique phone numbers with timestamps to avoid conflicts
- Visitor welcome messages are disabled during testing to avoid SMS costs
- All created test data can be cleaned up manually from the admin interface

