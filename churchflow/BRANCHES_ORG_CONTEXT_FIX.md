# Branches Organization Context Fix

**Date:** November 14, 2025
**Status:** ✅ Complete

---

## Summary

Fixed the `/api/v1/branches` endpoint to properly implement organization context while allowing public access for registration forms.

---

## Problem

User reported error when accessing the landing page and registration form:

```
GET /api/v1/branches/ [401 Unauthorized]
Error: Request failed with status code 401
```

**Root Cause:**
1. Branches endpoint required authentication (added `get_current_user` dependency)
2. Registration form (`ConferenceRegistration.tsx`) loads branches on mount
3. Registration should be public (no auth required)
4. User requirement: "for registration, no auth should be required"
5. User requirement: "every data should have org context and api also"

---

## Solution

Implemented multi-tenant organization isolation for branches with public access fallback:

### 1. Updated Branches Route (`/opt/kasaai/apps/churchflow/backend/app/api/routes/branches.py`)

**Made endpoint public** - removed `get_current_user` dependency:

```python
@router.get("/", response_model=List[BranchResponse])
async def list_branches(request: Request):  # No auth dependency
    """
    List all branches for the organization.

    Public endpoint - no authentication required for registration.
    Uses organization context from middleware if available, otherwise uses default org.
    """
```

**Added organization context with default fallback:**

```python
# Get organization_id from request state (set by middleware)
organization_id = getattr(request.state, 'organization_id', None)

# If no organization context from middleware, get the default organization
if not organization_id:
    logger.info("No organization context from middleware, using default organization")
    db = get_database()
    default_org = await db.organizations.find_one({"is_default": True})
    if default_org:
        organization_id = default_org.get("id")
        logger.info(f"Using default organization: {organization_id}")

# Get branches for the organization
branches = await branch_service.list_branches(organization_id) if organization_id else []
```

### 2. Updated Branch Service (`/opt/kasaai/apps/churchflow/backend/app/services/branch_service.py`)

**Added organization filtering:**

```python
async def list_branches(self, organization_id: Optional[str] = None, limit: int = 100) -> List[Dict]:
    """
    List all branches for an organization.

    Args:
        organization_id: Organization ID for filtering (optional for backward compatibility)
        limit: Maximum number of results

    Returns:
        List of branch dictionaries
    """
    db = get_database()

    try:
        # Filter by organization if provided
        query = {"organization_id": organization_id} if organization_id else {}

        cursor = db.branches.find(query).limit(limit)
        branches = await cursor.to_list(length=limit)

        # Convert ObjectId to string for JSON serialization
        for branch in branches:
            branch["_id"] = str(branch["_id"])

        if organization_id:
            logger.info(f"Listed {len(branches)} branches for organization {organization_id}")
        else:
            logger.info(f"Listed {len(branches)} branches (no org filter)")
        return branches
```

### 3. Fixed Default Organization

Set the correct default organization in MongoDB:

```javascript
// Remove is_default from all organizations
db.organizations.updateMany({}, {$unset: {is_default: 1}});

// Set Action Chapel International as default
db.organizations.updateOne(
  {id: '8eac859d-9459-4bd2-a690-041ad2ba573d'},
  {$set: {is_default: true}}
);
```

**Default Organization:**
- ID: `8eac859d-9459-4bd2-a690-041ad2ba573d`
- Name: `action-chapel-international`
- Display Name: `Action Chapel International`
- Branches: 100+ branches

---

## How It Works

### For Authenticated Users (Admin/Dashboard):

```
User → /admin/conferences (with access_token)
  ↓
OrganizationContextMiddleware extracts organization_id from token
  ↓
request.state.organization_id = user's organization
  ↓
GET /api/v1/branches/
  ↓
Returns branches for user's organization
```

### For Unauthenticated Users (Public Registration):

```
User → /register (no access_token)
  ↓
OrganizationContextMiddleware sets no organization (no token)
  ↓
request.state.organization_id = None
  ↓
GET /api/v1/branches/
  ↓
Endpoint detects no organization context
  ↓
Queries default organization (is_default: true)
  ↓
Returns branches for default organization (Action Chapel International)
```

---

## Database Structure

### Branch Document:

```json
{
  "_id": ObjectId("690fb6b62d4b5ea09829e64b"),
  "name": "Adenta",
  "location": "Adenta, Greater Accra, Ghana",
  "address": "Adenta, Greater Accra, Ghana",
  "contact_person": null,
  "contact_phone": null,
  "capacity": 100,
  "status": "active",
  "region": "Greater Accra",
  "organization_id": "8eac859d-9459-4bd2-a690-041ad2ba573d",  ← Organization context
  "created_at": ISODate("2025-11-08T21:31:34.522Z"),
  "updated_at": ISODate("2025-11-14T11:41:38.103Z")
}
```

### Organization Document:

```json
{
  "_id": ObjectId("6917151c7ebf023dc2ba26b0"),
  "id": "8eac859d-9459-4bd2-a690-041ad2ba573d",
  "name": "action-chapel-international",
  "display_name": "Action Chapel International",
  "is_default": true,  ← Default organization flag
  "is_active": true,
  "created_at": ISODate("2025-11-14T10:55:08.654Z")
}
```

---

## Multi-Tenant Isolation

### Organization Context Flow:

1. **OrganizationContextMiddleware** (from `@apps/shared/middleware`)
   - Runs on every request
   - Extracts JWT token from Authorization header
   - Decodes token to get user's organization
   - Sets `request.state.organization_id`

2. **Branches Endpoint**
   - Reads `request.state.organization_id`
   - If present: Filter branches by organization (authenticated user)
   - If not present: Use default organization (public access)

3. **Branch Service**
   - Applies MongoDB filter: `{"organization_id": organization_id}`
   - Returns only branches belonging to the organization

### Security:

- ✅ Users can only see branches from their organization (when authenticated)
- ✅ Public users see branches from default organization only
- ✅ No cross-organization data leakage
- ✅ Organization ID is controlled by backend, not client

---

## Testing

### Test 1: Public Access (No Auth)

```bash
curl https://churchflow-api.ailabsafrica.com/api/v1/branches/
```

**Expected:**
- ✅ 200 OK
- ✅ Returns 100+ branches for default organization
- ✅ All branches have `organization_id: "8eac859d-9459-4bd2-a690-041ad2ba573d"`

### Test 2: Authenticated Access

```bash
curl -H "Authorization: Bearer $TOKEN" \
  https://churchflow-api.ailabsafrica.com/api/v1/branches/
```

**Expected:**
- ✅ 200 OK
- ✅ Returns branches for user's organization
- ✅ Organization determined from JWT token

### Test 3: Registration Form

1. Visit: https://churchflow.ailabsafrica.com/register
2. Form loads branches dropdown

**Expected:**
- ✅ No 401 errors
- ✅ Branches load successfully
- ✅ Shows all branches from default organization

---

## Benefits

1. **Multi-Tenant Isolation**: Each organization sees only their own branches
2. **Public Registration**: Unauthenticated users can register for events
3. **Secure by Default**: Organization context enforced at backend
4. **Seamless UX**: Registration forms work without requiring login
5. **Scalable**: Supports multiple organizations in the same database

---

## Files Modified

### Backend:

1. `/opt/kasaai/apps/churchflow/backend/app/api/routes/branches.py`
   - Removed `get_current_user` dependency
   - Added default organization fallback
   - Added organization context filtering

2. `/opt/kasaai/apps/churchflow/backend/app/services/branch_service.py`
   - Added `organization_id` parameter to `list_branches()`
   - Implemented MongoDB filtering by organization
   - Updated all logging to remove undefined `organization_id` references

### Database:

3. MongoDB `churchflow.organizations`
   - Set `is_default: true` on Action Chapel International
   - Removed `is_default` from other organizations

---

## Related Endpoints

Other endpoints that need similar treatment (already implemented or to be reviewed):

- ✅ `/api/v1/conferences` - Public access for listing conferences
- ✅ `/api/v1/buses/routes` - Public access for bus booking
- ⚠️ `/api/v1/registrations` - Should be public for event registration
- 🔒 `/api/v1/organizations` - Requires authentication (admin only)
- 🔒 `/admin/*` - All admin routes protected by ProtectedRoute component

---

## Next Steps

1. **Review all public endpoints** to ensure they:
   - Allow unauthenticated access where needed
   - Use default organization fallback
   - Implement proper organization filtering

2. **Add organization context to all data models**:
   - Conferences (already has organization_id)
   - Buses (needs organization_id)
   - Registrations (needs organization_id)
   - Users (needs organization memberships)

3. **Document organization context pattern** in `@apps/shared/`
   - Create reusable middleware utilities
   - Standardize across all apps (ChurchFlow, ERP, InkWave, etc.)

---

**Status**: ✅ Fixed and Tested
**Deployed**: https://churchflow.ailabsafrica.com
**Impact**: Registration forms now work without authentication, proper multi-tenant isolation implemented
