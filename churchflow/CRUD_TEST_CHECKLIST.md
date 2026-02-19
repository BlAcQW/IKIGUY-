# ChurchFlow CRUD Operations Test Checklist

**Organization**: Action Chapel International
**Organization ID**: `8eac859d-9459-4bd2-a690-041ad2ba573d`
**Test User**: admin@ailabsafrica.com
**Date**: 2025-12-06

## Critical Points Verified

✅ **Organization Scoping Fixed**:
- Conference organization_id migrated from ObjectId string to UUID string
- 12,987 session attendance records migrated
- 11 bus routes migrated
- All data now uses correct organization_id: `8eac859d-9459-4bd2-a690-041ad2ba573d`

✅ **Organization Access**:
- admin@ailabsafrica.com has admin membership for Action Chapel International
- Organization memberships created with correct UUID organization_id
- Backend restarted to pick up changes

✅ **Frontend**:
- Organization switcher implemented for universal admins
- Login automatically sets Action Chapel International as default organization
- X-Organization-ID header added to all axios and fetch requests

## CRUD Operations to Test Manually

### 1. ✅ Conference Check-In (VERIFIED WORKING)
- **Endpoint**: `/api/v1/conferences/{conference_id}/sessions/{session_id}/check-in/manual`
- **Status**: FIXED - organization_id mismatch resolved
- **Action**: Log in as admin@ailabsafrica.com and check in attendees to IMPACT 2025

### 2. Visitors Management
**Create Visitor**:
- **Frontend**: Navigate to /visitors → Click "Add Visitor"
- **Backend**: POST `/api/v1/visitors`
- **Required Fields**: name, phone, visit_date
- **Organization Scoping**: Uses `require_organization_access` dependency
- **Test**: Create visitor → Verify it appears in list → Check organization_id in database

**Read Visitors**:
- **Frontend**: /visitors page
- **Backend**: GET `/api/v1/visitors`
- **Test**: Verify only visitors from Action Chapel International appear

**Update Visitor**:
- **Frontend**: Click visitor → Edit
- **Backend**: PATCH `/api/v1/visitors/{visitor_id}`
- **Test**: Update visitor details → Verify changes saved

**Delete Visitor**:
- **Frontend**: Click visitor → Delete
- **Backend**: DELETE `/api/v1/visitors/{visitor_id}`
- **Test**: Delete visitor → Verify removed from list

### 3. Giving Management
**Create Gift**:
- **Frontend**: Navigate to /giving → Record Gift
- **Backend**: POST `/api/v1/giving/gifts`
- **Required Fields**: donor info, amount, type, date
- **Test**: Record gift → Verify appears in giving reports

**Read Gifts**:
- **Frontend**: /giving page
- **Backend**: GET `/api/v1/giving/gifts`
- **Test**: Verify only gifts for Action Chapel International

**Analytics**:
- **Frontend**: /giving → Analytics tab
- **Backend**: GET `/api/v1/giving/analytics`
- **Test**: Check analytics shows correct totals for organization

### 4. Bus Management
**Create Bus Route**:
- **Frontend**: Navigate to /buses → Create Route
- **Backend**: POST `/api/v1/buses/routes`
- **Organization Scoping**: Uses `require_organization_access`
- **Note**: 11 bus routes already migrated to correct organization_id
- **Test**: Create new route → Verify organization_id is correct

**Public Access**:
- **Frontend**: Registration page (public)
- **Backend**: GET `/api/v1/buses/routes` (uses `get_optional_organization_id`)
- **Test**: Access /register → Verify bus routes load without authentication

**Update Bus Route**:
- **Backend**: PATCH `/api/v1/buses/routes/{route_id}`
- **Test**: Update route details → Verify changes saved

**Delete Bus Route**:
- **Backend**: DELETE `/api/v1/buses/routes/{route_id}`
- **Test**: Delete route → Verify removed

### 5. Cell Groups (if implemented)
- **Status**: Need to check if cell groups routes exist
- **Files to check**: `backend/app/api/routes/`

### 6. Conference Management
**Create Conference**:
- **Frontend**: /conferences → Create
- **Backend**: POST `/api/v1/conferences`
- **Critical**: Ensure organization_id is set to UUID string, not ObjectId
- **Test**: Create conference → Verify organization_id in database

**Create Sessions**:
- **Backend**: POST `/api/v1/conferences/{conference_id}/sessions`
- **Test**: Create session → Verify organization_id matches conference

**Registrations**:
- **Public**: POST `/api/v1/registrations`
- **Test**: Register for conference → Verify organization_id set correctly

### 7. User Management
**Frontend Endpoints** (if admin panel exists):
- List users in organization
- Invite users
- Update user roles
- Remove users

**Backend**: `/api/v1/organizations/{org_id}/users`

## Database Integrity Checks

Run after each CRUD operation:

```javascript
// Check organization_id consistency
db.visitors.find({organization_id: {$exists: true}}).forEach(doc => {
  if (doc.organization_id !== "8eac859d-9459-4bd2-a690-041ad2ba573d") {
    print("WARNING: Wrong org_id in visitors:", doc._id);
  }
});

db.giving.find({organization_id: {$exists: true}}).forEach(doc => {
  if (doc.organization_id !== "8eac859d-9459-4bd2-a690-041ad2ba573d") {
    print("WARNING: Wrong org_id in giving:", doc._id);
  }
});

db.bus_routes.find({organization_id: {$exists: true}}).forEach(doc => {
  if (doc.organization_id !== "8eac859d-9459-4bd2-a690-041ad2ba573d") {
    print("WARNING: Wrong org_id in bus_routes:", doc._id);
  }
});
```

## Known Issues Fixed

1. ✅ Conference organization_id mismatch - FIXED
2. ✅ Session attendance organization_id mismatch - FIXED (12,987 records)
3. ✅ Bus routes organization_id mismatch - FIXED (11 routes)
4. ✅ Missing organization memberships for admin@ailabsafrica.com - FIXED
5. ✅ Login not setting default organization - FIXED

## Testing Workflow

1. **Login as admin@ailabsafrica.com**
2. **Verify organization** is "Action Chapel International" in sidebar
3. **Test each CRUD operation** above in order
4. **Check database** after each create/update/delete
5. **Verify organization_id** is always `8eac859d-9459-4bd2-a690-041ad2ba573d`
6. **Document any failures** in this file

## Critical Backend Files

- **Dependencies**: `backend/app/api/dependencies.py` - `require_organization_access`, `get_optional_organization_id`
- **Visitors**: `backend/app/api/routes/visitors.py`
- **Giving**: `backend/app/api/routes/giving.py`
- **Buses**: `backend/app/api/routes/buses.py`
- **Conferences**: `backend/app/api/routes/conferences.py`
- **Organizations**: `backend/app/api/routes/organizations.py`

## Frontend Files

- **Axios Config**: `frontend/src/lib/axios-config.ts` - Adds X-Organization-ID header
- **API Config**: `frontend/src/lib/api.ts` - Adds X-Organization-ID to fetch
- **Organization Context**: `frontend/src/contexts/OrganizationContext.tsx`
- **Login**: `frontend/src/pages/Login.tsx` - Sets default organization

## Next Steps

1. Manually test each CRUD operation through the UI
2. Verify data in MongoDB after each operation
3. Document any issues found
4. Fix any remaining organization scoping issues
5. Create automated tests for critical paths
