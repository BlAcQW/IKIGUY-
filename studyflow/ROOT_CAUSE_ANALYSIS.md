# StudyFlow Materials Not Showing - Root Cause Analysis & Fix

## Problem Summary
- Users (including admins) cannot see previously uploaded materials
- Newly uploaded materials don't appear after upload
- No errors in console, but materials list returns empty

## Root Causes Identified

### 1. **Supabase User Metadata Not Synced with MongoDB** (CRITICAL)
**Issue:**
- MongoDB `organization_users` table contains user-organization mappings
- But Supabase JWT tokens had EMPTY `user_metadata` {}
- When users log in, their JWT doesn't contain `organization_id` or `role`

**Impact:**
- Backend can't determine user's organization
- Falls back to DEFAULT_ORGANIZATION_ID
- Users see materials from wrong organization (or none at all)

**Fix Applied:**
- Created sync script that copies organization data from MongoDB to Supabase
- All 4 organization users updated with proper `organization_id` and `role`
- Script location: see code execution above

### 2. **Universal Admins Not Bypassing Organization Filter** (MAJOR)
**Issue:**
- `user@ailabsafrica.com` is configured as UNIVERSAL_ADMIN
- But `MaterialService.list_materials()` still filtered by organization
- Universal admin privilege was ignored at service layer

**Impact:**
- Even admins only see materials from their assigned organization
- Admin user in org A cannot see materials from org B

**Fix Applied:**
- Updated `/opt/kasaai/apps/studyflow/backend/app/api/routes/materials.py`
  - Added check: `is_universal_admin = user_context.get("is_universal_admin", False)`
  - Set `organization_id = None` for universal admins

- Updated `/opt/kasaai/apps/studyflow/backend/app/services/material_service.py`
  - Changed `if organization_id:` to `if organization_id is not None:`
  - When `organization_id = None`, no organization filter applied (fetch ALL)

- Git commit: `95c0d8c3` - "fix(studyflow): Allow universal admins to see all materials across organizations"

## Current Status

### ✅ Fixed on DEV Server (85.214.12.174)
- Supabase metadata synced
- Code changes applied
- Service restarted
- Changes pushed to GitHub

### ❌ NOT Fixed on PRODUCTION Server (148.251.0.46)
- Supabase metadata synced (shared database)
- Code changes NOT YET applied
- Service needs restart

## Deployment to Production

### Option 1: Automatic Script
Run this on PRODUCTION server:
```bash
ssh root@148.251.0.46
cd /opt/kasaai/apps/studyflow
./DEPLOY_PROD_FIX.sh
```

### Option 2: Manual Steps
Run on PRODUCTION server:
```bash
ssh root@148.251.0.46
cd /opt/kasaai/apps
git pull origin dev
sudo systemctl restart kasaai-studyflow
```

## User Action Required

**CRITICAL:** Users must LOG OUT and LOG BACK IN to get fresh JWT tokens with updated metadata!

The old JWT tokens in browser still have empty metadata. New login will include:
- `user_metadata.organization_id`
- `user_metadata.role`

## Database State

### Organizations in StudyFlow
- `6908b8207818c25d26337406` - "ai-labs-ltd" - **9 materials** (Cambridge IGCSE, etc.)
- `9daf0254-96f8-4d80-a17d-5324673edc85` - "Unknown" - **1 material**

### Users
- `user@ailabsafrica.com` → org `9daf0254-96f8-4d80-a17d-5324673edc85`, role: admin, **UNIVERSAL ADMIN**
- `admin@ailabsafrica.com` → org `9daf0254-96f8-4d80-a17d-5324673edc85`, role: admin, **UNIVERSAL ADMIN**
- `alfred.anyan@gmail.com` → org `9daf0254-96f8-4d80-a17d-5324673edc85`, role: admin, **UNIVERSAL ADMIN**

## Expected Behavior After Fix

### For Universal Admins (user@ailabsafrica.com, admin@ailabsafrica.com)
- Should see **ALL 10 materials** across all organizations
- No organization filtering applied

### For Regular Users
- Should see materials from their assigned organization only
- Plus any materials with `organization_id = null` (legacy)

## Preventing Future Issues

### 1. Auto-sync Organization Data
Create a hook/trigger when users join organizations:
```python
# In organization_service.py - add_user_to_organization()
async def add_user_to_organization(...):
    # ... MongoDB insert ...

    # Sync to Supabase
    supabase.auth.admin.update_user_by_id(
        user_id,
        {'user_metadata': {'organization_id': org_id, 'role': role}}
    )
```

### 2. Frontend: Send X-Organization-Id Header
Update frontend API client to send organization header:
```javascript
headers: {
  'Authorization': `Bearer ${token}`,
  'X-Organization-Id': user.organization_id
}
```

### 3. Backend: Validate Metadata on Every Request
Add middleware to check if user has organization metadata, sync if missing.

## Testing Checklist

After deployment:
- [ ] User logs out
- [ ] User logs back in
- [ ] User can see all 10 materials (if universal admin)
- [ ] Upload new material
- [ ] New material appears immediately in list
- [ ] Verify in database: material has correct organization_id
- [ ] Regular user (non-admin) sees only their org's materials

## Files Changed
- `studyflow/backend/app/api/routes/materials.py`
- `studyflow/backend/app/services/material_service.py`

## Commits
- `95c0d8c3` - fix(studyflow): Allow universal admins to see all materials across organizations
