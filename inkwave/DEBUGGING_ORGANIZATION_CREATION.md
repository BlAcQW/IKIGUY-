# Debugging & Fixing Organization Creation in InkWave

**Date:** 2025-11-03
**Issue:** Create Organization feature not working
**Goal:** Make it work and teach you the debugging process

---

## 🎯 Learning Path

We'll follow this systematic debugging approach:

### 1. **Understand the Data Flow**
### 2. **Test Each Layer Independently**
### 3. **Identify the Broken Link**
### 4. **Fix and Verify**

---

## 📊 Architecture Overview

```
Frontend                API Client              Backend                 Database
┌────────────────┐     ┌─────────────┐         ┌──────────────┐        ┌─────────┐
│ Organization   │────▶│  api.ts      │────────▶│ organizations│───────▶│ MongoDB │
│ Management     │     │  organizations│        │ .py routes   │        │         │
│ Component      │     │  .create()   │        │              │        │         │
└────────────────┘     └─────────────┘         └──────────────┘        └─────────┘
     [User fills          [Makes HTTP            [Validates &            [Stores
      form]                POST request]          processes]              data]
```

---

## 🔍 Step 1: Understanding the Frontend Code

### Location
- File: `/opt/kasaai/apps/inkwave/frontend/src/components/admin/OrganizationManagement.tsx`
- Lines: 162-192 (CreateOrganizationModal)

### What It Does

```typescript
const handleSubmit = async (e: React.FormEvent) => {
  e.preventDefault();
  try {
    const token = localStorage.getItem('access_token');
    const response = await fetch(`${apiBaseUrl}/api/v1/organizations`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(formData)
    });

    if (!response.ok) throw new Error('Failed to create organization');

    await loadOrganizations();
    setShowCreateModal(false);
    // ...
  } catch (error) {
    onError?.('Failed to create organization');
  }
};
```

**Key Points:**
1. Gets JWT token from localStorage (`access_token`)
2. Makes POST request to `/api/v1/organizations`
3. Sends organization data as JSON
4. On success, reloads organization list
5. On error, shows generic error message

**Problem #1:** Error handling is too generic - doesn't show what actually went wrong!

---

## 🔍 Step 2: Check the API Client Configuration

### Location
- File: `/opt/kasaai/apps/inkwave/frontend/src/lib/api.ts`
- Lines: 142-147

### What It Does

```typescript
organizations: {
  list: () => apiClient.get('/organizations'),
  get: (id: string) => apiClient.get(`/organizations/${id}`),
  create: (data: any) => apiClient.post('/organizations', data),  // ← This is defined
  // ... other methods
}
```

**Key Points:**
1. API client is configured with axios
2. Base URL: `https://inkwave-api.ailabsafrica.com/api/v1` (from env)
3. Automatically adds JWT token via interceptor (lines 21-39)
4. The `create` method exists but **isn't being used** in the component!

**Problem #2:** Component uses raw `fetch()` instead of the configured API client that handles auth properly!

---

## 🔍 Step 3: Check the Backend Route

### Location
- File: `/opt/kasaai/apps/inkwave/backend/app/api/routes/organizations.py`
- Lines: 20-40

### What It Does

```python
@router.post("", response_model=Organization)
async def create_organization(
    org_data: OrganizationCreate,
    user: dict = Depends(get_current_user)
):
    """Create a new audiobook organization."""
    try:
        org_service = get_organization_service()
        user_id = user.user_id
        user_email = user.email

        organization = await org_service.create_organization(
            org_data, user_id, user_email
        )
        logger.info(f"Created organization {organization.id} by user {user_email}")
        return organization
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating organization: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create organization")
```

**Key Points:**
1. Endpoint: `POST /api/v1/organizations`
2. Requires authentication (`Depends(get_current_user)`)
3. Uses shared `OrganizationService` from `@apps/shared/services/`
4. Returns created organization or error

---

## 🔍 Step 4: Test the Backend Directly

### Manual Test Using curl

Let's test if the backend endpoint works:

```bash
# First, get an auth token by logging in
# (You'd normally do this through the UI or Supabase)

# Test without auth (should fail with 401)
curl -X POST http://localhost:30033/api/v1/organizations \
  -H "Content-Type: application/json" \
  -d '{
    "name": "test-org",
    "display_name": "Test Organization",
    "description": "Test",
    "industry": "Technology"
  }'

# Expected response: 401 Unauthorized
```

### With Valid Auth Token

```bash
# Get token from Supabase (you need to be logged in)
TOKEN="your_jwt_token_here"

curl -X POST http://localhost:30033/api/v1/organizations \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "test-org",
    "display_name": "Test Organization",
    "description": "A test organization",
    "industry": "Technology",
    "website": "https://test.com"
  }'

# Expected: Organization created successfully
```

---

## 🐛 Common Issues & Fixes

### Issue 1: 401 Unauthorized

**Symptoms:**
- Request fails with 401
- "Authorization header missing" or "Invalid token"

**Causes:**
1. No JWT token in localStorage
2. Token expired
3. Token not being sent in Authorization header
4. Supabase configuration issue

**How to Debug:**
```javascript
// In browser console
localStorage.getItem('access_token')  // Check if token exists

// Check if token is valid
const { data: { session } } = await supabase.auth.getSession();
console.log(session);  // Should show user and token
```

**Fix:**
1. Ensure user is logged in
2. Check token is stored correctly
3. Verify token is being sent in request headers

---

### Issue 2: 400 Bad Request

**Symptoms:**
- Request fails with 400
- "Validation error" messages

**Causes:**
1. Missing required fields (`name` or `display_name`)
2. Invalid field format (e.g., `name` has spaces or uppercase)
3. Field type mismatch

**How to Debug:**
```bash
# Check what the backend expects
curl http://localhost:30033/docs

# Look at the OrganizationCreate schema
```

**Fix:**
1. Ensure `name` is lowercase, no spaces (e.g., "my-org")
2. Ensure `display_name` is provided
3. Check schema in `@apps/shared/models/organization.py`

---

### Issue 3: 500 Internal Server Error

**Symptoms:**
- Request fails with 500
- "Failed to create organization"

**Causes:**
1. Database connection issue
2. Shared service not initialized
3. Bug in organization service logic

**How to Debug:**
```bash
# Check backend logs
sudo journalctl -u kasaai-inkwave-backend -f

# Or if running manually:
tail -f /path/to/log/file
```

**Fix:**
1. Check MongoDB is running: `sudo systemctl status mongod`
2. Verify database credentials in `.env`
3. Check organization service initialization

---

## 🔧 The Fix

### Problem Summary

The component uses raw `fetch()` instead of the configured API client, which:
1. Might not be getting the token correctly
2. Doesn't benefit from error interceptors
3. Duplicates code

### Solution: Use the API Client

**Current Code (OrganizationManagement.tsx:174-182):**
```typescript
const token = localStorage.getItem('access_token');
const response = await fetch(`${apiBaseUrl}/api/v1/organizations`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify(formData)
});

if (!response.ok) throw new Error('Failed to create organization');
```

**Fixed Code:**
```typescript
const response = await api.organizations.create(formData);
toast.success(`Organization "${formData.display_name}" created successfully!`);
```

**Benefits:**
1. ✅ Auth token handled automatically by interceptor
2. ✅ Error handling centralized
3. ✅ Less code, more maintainable
4. ✅ Consistent with rest of codebase

---

## 🧪 Testing the Fix

### Frontend Testing

1. **Login as Admin:**
   - Go to `/login`
   - Login with `admin@ailabsafrica.com`
   - Should redirect to home

2. **Navigate to Organizations:**
   - Go to `/admin/organizations`
   - Should see organization list (might be empty)

3. **Create Organization:**
   - Click "Create Organization"
   - Fill form:
     - Name: `my-test-org` (lowercase, no spaces)
     - Display Name: `My Test Organization`
     - Description: `Testing organization creation`
     - Industry: `Technology`
     - Website: `https://test.com`
   - Click "Create"

4. **Expected Results:**
   - Success toast message appears
   - Modal closes
   - New organization appears in list
   - Organization is selectable

5. **Verify in Database:**
```bash
mongosh mongodb://admin:aawwER4444%@127.0.0.1:27017/
use inkwave
db.organizations.find().pretty()
```

---

## 📝 Improved Error Handling

### Make Errors User-Friendly

**Before:**
```typescript
catch (error) {
  onError?.('Failed to create organization');
}
```

**After:**
```typescript
catch (error: any) {
  const errorMessage = error.response?.data?.detail ||
                      error.message ||
                      'Failed to create organization';
  toast.error(errorMessage);
  onError?.(errorMessage);
  console.error('Organization creation failed:', error);
}
```

This shows the actual error from the backend, helping you debug faster!

---

## 🎓 Debugging Process Summary

### Step-by-Step Approach

1. **Start Backend:**
   ```bash
   cd /opt/kasaai/apps/inkwave/backend
   source /opt/kasaai/apps/venv/bin/activate
   uvicorn app.main:app --reload --port 30033
   ```

2. **Test Backend Endpoint:**
   ```bash
   # Test with curl first
   curl -X POST http://localhost:30033/api/v1/organizations ...
   ```

3. **Check Logs:**
   ```bash
   # Watch backend logs
   tail -f logs/inkwave.log  # or wherever logs are
   ```

4. **Test Frontend:**
   - Open browser DevTools (F12)
   - Go to Network tab
   - Try creating organization
   - Check request/response in Network tab
   - Check Console for errors

5. **Debug Database:**
   ```bash
   # Check if data was created
   mongosh mongodb://admin:aawwER4444%@127.0.0.1:27017/inkwave
   db.organizations.find()
   ```

---

## 🚀 Next Steps

After fixing organization creation, you should test:

1. ✅ **Create organization** - We're fixing this now
2. ⬜ **List organizations** - Should work (already implemented)
3. ⬜ **Get organization details** - Should work
4. ⬜ **Invite members** - Needs backend endpoints
5. ⬜ **List members** - Needs backend endpoints
6. ⬜ **Update organization** - Needs implementation
7. ⬜ **Delete organization** - Needs implementation

---

## 🐛 Quick Reference: Common Error Codes

| Code | Meaning | Common Cause |
|------|---------|--------------|
| 400 | Bad Request | Invalid input data, validation error |
| 401 | Unauthorized | No auth token or invalid token |
| 403 | Forbidden | Valid token but no permission |
| 404 | Not Found | Route or resource doesn't exist |
| 500 | Server Error | Backend bug, database issue |

---

## 💡 Pro Tips

1. **Always check browser DevTools Network tab first**
   - Shows exact request/response
   - Shows status code
   - Shows headers

2. **Use backend logs**
   - Python stack traces show exact error location
   - Check for validation errors
   - Look for database connection issues

3. **Test backend endpoints independently**
   - Use curl or Postman
   - Isolates frontend vs backend issues
   - Faster than clicking through UI

4. **Check database directly**
   - Verify data is (or isn't) being created
   - Check field names match schema
   - Look for data type mismatches

5. **Use better error messages**
   - Log errors to console
   - Show backend error messages to user
   - Include error context (which organization, what operation)

---

**Last Updated:** 2025-11-03
**Status:** In Progress - Applying fixes
