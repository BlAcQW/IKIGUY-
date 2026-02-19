# InkWave Organization Creation Guide

**Created**: 2025-11-03
**Status**: ✅ Working - Authentication Required

---

## Summary

Organization creation in InkWave is **working correctly** but requires authentication. The issue users experience is typically due to not being logged in when attempting to create an organization.

---

## How Organization Creation Works

### Backend Architecture

1. **Route**: `POST /api/v1/organizations` (`inkwave/backend/app/api/routes/organizations.py:20`)
2. **Authentication**: Requires valid Supabase JWT token via `get_current_user` dependency
3. **Service**: Uses shared `apps/shared/services/organization_service.py`
4. **Database**: MongoDB collection `organizations` and `organization_users`

### Authentication Flow

```python
@router.post("", response_model=Organization)
async def create_organization(
    org_data: OrganizationCreate,
    user: dict = Depends(get_current_user)  # ← Requires authentication
):
    """Create a new audiobook organization."""
    org_service = get_organization_service()
    organization = await org_service.create_organization(
        org_data, user.user_id, user.email
    )
    return organization
```

### Key Features

- **Auto-generated organization name**: If you don't provide a `name`, it's automatically generated from `display_name`
- **Unique name validation**: Prevents duplicate organization names
- **Creator becomes admin**: User who creates the organization is automatically assigned as admin
- **Universal admin support**: Universal admins (configured in `.env`) have access to all organizations

---

## Why "Unable to Create Organization"?

### Root Cause

The organization creation endpoint returns:
```json
{"detail":"Authorization header missing"}
```

This means the user is **not authenticated** when making the request.

### Common Scenarios

1. **User not logged in**: Frontend hasn't authenticated with Supabase
2. **Token expired**: JWT token has expired (tokens are valid for a limited time)
3. **Token not sent**: Frontend is not attaching the token to the request
4. **Supabase session issue**: Session lost due to browser refresh or local storage cleared

---

## How to Fix

### For End Users

1. **Log in to InkWave**:
   - Navigate to `/login`
   - Use valid credentials (e.g., `user@ailabsafrica.com` / `User@2024!`)
   - Wait for successful login

2. **Navigate to Organizations Page**:
   - Go to `/admin/organizations`
   - Ensure you see the "Create Organization" button

3. **Create Organization**:
   - Click "Create Organization"
   - Fill in the form:
     - **Display Name** (required): Human-readable name (e.g., "My Publisher")
     - **Organization Name** (optional): URL-safe name (auto-generated if empty)
     - **Description** (optional): Brief description
     - **Industry** (optional): E.g., "Publishing", "Education"
     - **Website** (optional): Company website
   - Click "Create"

### For Developers

#### 1. Verify Authentication State

Check if the frontend is properly getting the Supabase session:

```typescript
// In browser console or component
const { data: { session } } = await supabase.auth.getSession();
console.log('Session:', session);
console.log('Access Token:', session?.access_token);
```

#### 2. Check API Request

Ensure the frontend is sending the token:

```typescript
// In api.ts (already implemented correctly)
apiClient.interceptors.request.use(
  async (config) => {
    const { data: { session } } = await supabase.auth.getSession();
    if (session?.access_token) {
      config.headers.Authorization = `Bearer ${session.access_token}`;
    }
    return config;
  }
);
```

#### 3. Test with curl

Test the endpoint directly with a valid token:

```bash
# 1. Login and get token
curl -X POST https://supabase.ailabsafrica.com/auth/v1/token?grant_type=password \
  -H "Content-Type: application/json" \
  -H "apikey: YOUR_SUPABASE_ANON_KEY" \
  -d '{"email":"user@ailabsafrica.com","password":"User@2024!"}' \
  | jq -r '.access_token'

# 2. Create organization with token
curl -X POST https://inkwave-api.ailabsafrica.com/api/v1/organizations \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "display_name": "Test Organization",
    "description": "Test org",
    "industry": "Education"
  }'
```

---

## Test Page

A test page has been created at `/tmp/test_org_creation.html` to help diagnose issues:

### Features

1. **Login Test**: Log in with test credentials
2. **Organization Creation**: Create organizations with authentication
3. **List Organizations**: View all organizations for the current user
4. **Token Display**: Shows the JWT token for debugging

### Usage

```bash
# Open the test page in a browser
firefox /tmp/test_org_creation.html
# or
google-chrome /tmp/test_org_creation.html
```

### Default Test Credentials

- **Email**: `user@ailabsafrica.com`
- **Password**: `User@2024!`

---

## API Reference

### Create Organization

**Endpoint**: `POST /api/v1/organizations`

**Authentication**: Required (Bearer token)

**Request Body**:
```json
{
  "name": "optional-org-name",           // Optional: auto-generated if empty
  "display_name": "My Organization",     // Required
  "description": "Organization description",  // Optional
  "industry": "Publishing",              // Optional
  "website": "https://example.com"       // Optional
}
```

**Success Response** (201):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "my-organization",
  "display_name": "My Organization",
  "description": "Organization description",
  "industry": "Publishing",
  "website": "https://example.com",
  "is_active": true,
  "settings": {},
  "created_at": "2025-11-03T17:00:00",
  "updated_at": "2025-11-03T17:00:00"
}
```

**Error Responses**:

- **401 Unauthorized**:
  ```json
  {"detail": "Authorization header missing"}
  ```
  **Fix**: Login first, ensure token is sent

- **400 Bad Request**:
  ```json
  {"detail": "Organization name 'my-org' already exists. Please choose a different name."}
  ```
  **Fix**: Use a different name or leave it empty for auto-generation

- **500 Internal Server Error**:
  ```json
  {"detail": "Failed to create organization"}
  ```
  **Fix**: Check backend logs with `sudo journalctl -u kasaai-inkwave-backend -f`

---

## Default Users

InkWave uses centralized Supabase authentication. Three default users are available:

### Universal Admin - Alfred Anyan
- **Email**: `alfred.anyan@gmail.com`
- **Password**: `AlfredSecure2024!`
- **Supabase UUID**: `65715ad2-bcfa-42aa-ab21-e0b06f19b3e4`

### Admin User
- **Email**: `admin@ailabsafrica.com`
- **Password**: `Admin@2024!`
- **Supabase UUID**: `4a6252e7-3dc7-483a-92c3-59a0a814a169`

### Regular User
- **Email**: `user@ailabsafrica.com`
- **Password**: `User@2024!`
- **Supabase UUID**: `a1d7c822-847f-40ec-9fed-cc3cd9155c06`

All three users are configured as Universal Admins and can access all organizations.

See: `@shared/auth/DEFAULT_USERS.md`

---

## Environment Configuration

### Backend (.env)

```bash
# Supabase
SUPABASE_URL=https://supabase.ailabsafrica.com
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Universal Admins
UNIVERSAL_ADMIN_EMAILS=admin@ailabsafrica.com,alfred.anyan@gmail.com,user@ailabsafrica.com
UNIVERSAL_ADMIN_USER_IDS=4a6252e7-3dc7-483a-92c3-59a0a814a169,65715ad2-bcfa-42aa-ab21-e0b06f19b3e4,a1d7c822-847f-40ec-9fed-cc3cd9155c06

# MongoDB
MONGODB_URL=mongodb://admin:aawwER4444%@127.0.0.1:27017/
MONGODB_DB_NAME=inkwave
```

### Frontend (.env)

```bash
VITE_SUPABASE_URL=https://supabase.ailabsafrica.com
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
VITE_API_BASE_URL=https://inkwave-api.ailabsafrica.com/api/v1
```

---

## Troubleshooting

### Issue: "Authorization header missing"

**Cause**: User not logged in or token not sent

**Solution**:
1. Check if logged in: `await supabase.auth.getSession()`
2. Verify token in network request headers
3. Re-login if session expired

### Issue: "Organization name already exists"

**Cause**: Trying to create an organization with a duplicate name

**Solution**:
1. Leave the `name` field empty (it will auto-generate a unique name)
2. Or provide a different unique name

### Issue: "Failed to create organization" (500)

**Cause**: Backend error (database connection, service initialization, etc.)

**Solution**:
1. Check backend logs: `sudo journalctl -u kasaai-inkwave-backend -f`
2. Verify MongoDB is running: `sudo systemctl status mongodb`
3. Verify environment variables are set correctly
4. Restart the backend service: `sudo systemctl restart kasaai-inkwave-backend`

### Issue: Organizations not showing after creation

**Cause**: Frontend cache or need to refresh organization list

**Solution**:
1. Refresh the page
2. Call `loadOrganizations()` in the component
3. Check if the organization was actually created in MongoDB:
   ```bash
   mongosh mongodb://admin:aawwER4444%@127.0.0.1:27017/
   use inkwave
   db.organizations.find().pretty()
   ```

---

## Database Verification

### Check Organizations in MongoDB

```bash
# Connect to MongoDB
mongosh mongodb://admin:aawwER4444%@127.0.0.1:27017/

# Switch to inkwave database
use inkwave

# List all organizations
db.organizations.find().pretty()

# Check organization users (membership)
db.organization_users.find().pretty()

# Count organizations
db.organizations.countDocuments()
```

### Example Organization Document

```json
{
  "_id": ObjectId("..."),
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "test-organization",
  "display_name": "Test Organization",
  "description": "This is a test organization",
  "industry": "Education",
  "company_size": "",
  "website": "https://example.com",
  "phone": "",
  "address": "",
  "is_active": true,
  "settings": {},
  "created_at": ISODate("2025-11-03T17:00:00.000Z"),
  "updated_at": ISODate("2025-11-03T17:00:00.000Z")
}
```

---

## Service Status

### Check Backend Service

```bash
# Check if service is running
sudo systemctl status kasaai-inkwave-backend

# View recent logs
sudo journalctl -u kasaai-inkwave-backend -n 50

# Follow logs in real-time
sudo journalctl -u kasaai-inkwave-backend -f

# Restart service
sudo systemctl restart kasaai-inkwave-backend
```

### Verify Service Initialization

Look for these log messages on startup:

```
✅ Organization service initialized
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:30033
```

---

## Next Steps

1. ✅ **Authentication is required** - This is working as designed
2. ✅ **Frontend properly sends tokens** - Already implemented in `api.ts`
3. ✅ **Backend validates tokens** - Working correctly
4. ✅ **Organizations can be created** - Tested and working

### For Future Improvements

1. **Better error messages**: Frontend should detect authentication errors and redirect to login
2. **Token refresh**: Implement automatic token refresh when expired
3. **Loading states**: Show better loading indicators during organization creation
4. **Validation feedback**: Show real-time validation for organization name uniqueness

---

## Related Files

- Backend Route: `inkwave/backend/app/api/routes/organizations.py`
- Frontend Component: `inkwave/frontend/src/components/admin/OrganizationManagement.tsx`
- Frontend Page: `inkwave/frontend/src/pages/admin/OrganizationsPage.tsx`
- API Client: `inkwave/frontend/src/lib/api.ts`
- Auth Service: `inkwave/backend/app/core/auth.py`
- Shared Organization Service: `shared/services/organization_service.py`
- Shared Organization Models: `shared/models/organization.py`
- Default Users: `shared/auth/DEFAULT_USERS.md`

---

## Conclusion

Organization creation in InkWave is **fully functional**. The key requirement is that users must be authenticated before creating organizations. This is a security feature to ensure only authenticated users can create and manage organizations.

**If you encounter issues**:
1. Verify you're logged in
2. Check browser console for errors
3. Use the test page at `/tmp/test_org_creation.html`
4. Check backend logs
5. Verify environment configuration

For additional support, refer to the troubleshooting section above.
