# Organization Name Auto-Generation

**Date:** November 14, 2025
**Status:** ✅ Complete
**Build:** ✅ Successful (`index-DzM4P_62.js`)

---

## Summary

Updated the organization system to automatically generate the internal `name` field from the `display_name`, removing the need for users to manually enter a URL-safe name.

---

## Changes Made

### 1. Shared Models ✅
**File:** `/opt/kasaai/apps/shared/models/organization.py`

- `OrganizationCreate.name` is already **Optional** (line 233)
- Auto-generated from `display_name` if not provided

### 2. Shared Service ✅
**File:** `/opt/kasaai/apps/shared/services/organization_service.py`

Already has `_generate_org_name()` function (lines 85-119):
- Converts display_name to lowercase, URL-safe format
- Replaces spaces and special characters with hyphens
- Ensures uniqueness by appending numeric suffix if needed
- Example: "Action Chapel International" → "action-chapel-international"

### 3. ChurchFlow Frontend ✅
**File:** `/opt/kasaai/apps/churchflow/frontend/src/components/admin/OrganizationManagement.tsx`

**Removed:**
- Organization Name input field
- `name` from formData state
- `name` from form submission

**Form now only has:**
- Display Name * (required)
- Description
- Industry
- Website

### 4. ERP Frontend ✅
**File:** `/opt/kasaai/apps/erp/frontend/src/pages/AdminPage.tsx`

- Already only collects `display_name` and `description`
- No changes needed

---

## How It Works

### Backend Flow:

1. User enters: "Action Chapel International" (display_name)
2. Backend receives: `{ display_name: "Action Chapel International" }`
3. Service auto-generates: `name = "action-chapel-international"`
4. If name exists, appends counter: `"action-chapel-international-2"`
5. Organization created with both:
   - `name`: "action-chapel-international" (internal, used in URLs/APIs)
   - `display_name`: "Action Chapel International" (shown in UI)

### Name Generation Algorithm:

```python
def _generate_org_name(display_name):
    # Convert to lowercase
    name = display_name.lower()

    # Replace spaces/special chars with hyphens
    name = re.sub(r'[^a-z0-9]+', '-', name)

    # Remove leading/trailing hyphens
    name = name.strip('-')

    # Collapse multiple hyphens
    name = re.sub(r'-+', '-', name)

    # Ensure uniqueness
    counter = 1
    while exists(name):
        name = f"{base_name}-{counter}"
        counter += 1

    return name
```

### Examples:

| Display Name | Generated Name |
|--------------|----------------|
| Action Chapel International | action-chapel-international |
| Victory Bible Church | victory-bible-church |
| Lighthouse Chapel (Ghana) | lighthouse-chapel-ghana |
| Church of Pentecost | church-of-pentecost |
| Mega Church #1 | mega-church-1 |

If "action-chapel-international" exists:
- Next: "action-chapel-international-2"
- Then: "action-chapel-international-3"
- etc.

---

## UI Changes

### Before:
```
Create Organization
┌─────────────────────────────────┐
│ Organization Name *             │
│ my-organization                 │
│ Lowercase, no spaces (URLs)     │
├─────────────────────────────────┤
│ Display Name *                  │
│ My Organization                 │
├─────────────────────────────────┤
│ Description                     │
│ ...                             │
└─────────────────────────────────┘
```

### After:
```
Create Organization
┌─────────────────────────────────┐
│ Display Name *                  │
│ Action Chapel International     │
├─────────────────────────────────┤
│ Description                     │
│ ...                             │
├─────────────────────────────────┤
│ Industry                        │
│ ...                             │
├─────────────────────────────────┤
│ Website                         │
│ ...                             │
└─────────────────────────────────┘

(name auto-generated as: action-chapel-international)
```

---

## Benefits

1. **Simpler UX**: Users don't need to think about URL-safe naming
2. **Less Errors**: No more validation errors for invalid characters
3. **Automatic**: System handles uniqueness automatically
4. **Consistent**: All organizations follow same naming pattern
5. **Professional**: Generated names are clean and readable

---

## API Behavior

### Request (Before):
```json
POST /api/v1/organizations
{
  "name": "action-chapel-intl",
  "display_name": "Action Chapel International"
}
```

### Request (After):
```json
POST /api/v1/organizations
{
  "display_name": "Action Chapel International"
}
```

### Response (Same):
```json
{
  "id": "org_123abc",
  "name": "action-chapel-international",
  "display_name": "Action Chapel International",
  "description": "",
  "is_active": true,
  "created_at": "2025-11-14T20:00:00"
}
```

---

## Backwards Compatibility

✅ **Fully backwards compatible**

- `name` field is optional in `OrganizationCreate`
- If provided (old API clients), it's still validated and used
- If omitted (new API clients), it's auto-generated
- Existing organizations unchanged

---

## Testing

### Manual Test:

1. **Go to:** `/admin/organizations`
2. **Click:** "Create Organization"
3. **Enter:** Display Name: "Test Church"
4. **Submit**
5. **Verify:** Organization created with name: "test-church"

### API Test:

```bash
curl -X POST https://churchflow-api.ailabsafrica.com/api/v1/organizations \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "display_name": "My Amazing Church"
  }'
```

Expected response:
```json
{
  "id": "...",
  "name": "my-amazing-church",
  "display_name": "My Amazing Church",
  ...
}
```

---

## Files Modified

### Backend (Already Done):
- `/opt/kasaai/apps/shared/models/organization.py` - `name` already optional
- `/opt/kasaai/apps/shared/services/organization_service.py` - Auto-generation already implemented

### Frontend (Updated):
1. `/opt/kasaai/apps/churchflow/frontend/src/components/admin/OrganizationManagement.tsx`
   - Removed `name` field from form
   - Removed `name` from formData state
   - Added comment about auto-generation

2. `/opt/kasaai/apps/erp/frontend/src/pages/AdminPage.tsx`
   - Already only uses `display_name`
   - Added comment about auto-generation

---

## Build Status

```
✓ ChurchFlow Frontend Build: Success
  - Bundle: index-DzM4P_62.js
  - Size: 1.39 MB (373 KB gzipped)
  - Build Time: 3.24s
  - No Errors
```

---

**Status**: ✅ Complete
**Ready for**: Production Use
**Deployed**: https://churchflow.ailabsafrica.com

