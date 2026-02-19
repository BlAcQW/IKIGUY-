# Organization Switcher Enhancement

**Version:** 1.0
**Date:** 2025-10-26
**Status:** Implemented

---

## Overview

Enhanced organization switching functionality for universal admins, providing seamless access to all organizations in the KasaAI platform without page reloads.

### Key Features

✅ **Universal Admin Access** - View and switch to ANY organization (not just memberships)
✅ **Advanced Search** - Search across name, display_name, and description
✅ **Industry Filtering** - Filter organizations by industry
✅ **Status Filtering** - Filter by active/inactive status
✅ **No Page Reload** - Smooth state transition using React context
✅ **Sidebar Header Placement** - Prominent location for easy access
✅ **Shared Hook** - Reusable `useOrganizationSwitcher` for all apps

---

## Architecture

### Backend Enhancements

#### 1. Organization Service (@apps/shared/)

**File:** `/opt/kasaai/apps/shared/services/organization_service.py`

Added `list_all_organizations()` method with advanced search:

```python
async def list_all_organizations(
    self,
    search: Optional[str] = None,
    industry: Optional[str] = None,
    is_active: Optional[bool] = None,
    skip: int = 0,
    limit: int = 1000
) -> List[Organization]:
    """
    List all organizations with advanced search (universal_admin only).

    Supports:
    - Case-insensitive search across name, display_name, description
    - Industry filtering
    - Active/inactive status filtering
    - Pagination
    - Sorting by display_name
    """
```

#### 2. Core Backend API

**File:** `/opt/kasaai/apps/core_backend/backend/routes/organizations.py`

Enhanced `GET /organizations/all` endpoint:

```python
@router.get("/all", response_model=List[Organization])
def get_all_organizations(
    search: Optional[str] = Query(None),
    industry: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(1000, ge=1, le=1000),
    user: dict = Depends(get_current_user_mongo)
):
    """
    Get all organizations with advanced search.
    Universal admin only.
    """
```

**Example Usage:**
```bash
GET /organizations/all?search=church&industry=religious&is_active=true
```

---

### Frontend Enhancements

#### 1. Organization Context

**File:** `/opt/kasaai/apps/b2c-portal/src/contexts/OrganizationContext.tsx`

**New State:**
```typescript
const [allOrganizations, setAllOrganizations] = useState<Organization[]>([]);
const [isLoadingAll, setIsLoadingAll] = useState(false);
```

**New Methods:**
- `fetchAllOrganizations()` - Auto-fetches for universal admins
- `refreshAllOrganizations()` - Manual refresh trigger
- `switchOrganization(organizationId, forceReload?)` - Enhanced with fallback reload option

**Behavior:**
- Auto-fetches ALL organizations on mount for universal admins
- Searches both `organizations` and `allOrganizations` when switching
- Optional `forceReload` parameter for pages that need hard refresh
- Persists selection in localStorage

#### 2. Enhanced Organization Switcher

**File:** `/opt/kasaai/apps/b2c-portal/src/components/organization/OrganizationSwitcher.tsx`

**New Features:**
- Search input with real-time filtering
- Industry dropdown filter
- Active/inactive status filter
- Clear filters button
- Separate sections for "My Organizations" and "All Organizations"
- Visual distinction with purple styling for universal admin access
- Shows total organization count
- Loading states for both lists

**Variants:**
- `default` - Standard size (h-10)
- `compact` - Smaller size (h-9) for sidebar
- `prominent` - Larger size (h-12) for admin pages

**UI Structure:**
```
┌──────────────────────────────────────┐
│ Current Organization: KasaAI Inc     │
│ Role: Universal Admin 🛡️             │
├──────────────────────────────────────┤
│ [Search organizations...]           │
│ [Industry ▼] [Status ▼] [Clear]     │
├──────────────────────────────────────┤
│ 👥 MY ORGANIZATIONS (2)              │
│ ✓ KasaAI Inc (Admin)                │
│   EventFlow Demo (Owner)             │
├──────────────────────────────────────┤
│ 🛡️ ALL ORGANIZATIONS (15)           │
│   ChurchFlow Demo                    │
│   StudyFlow Academy                  │
│   InkWave Publishers                 │
│   ...                                │
└──────────────────────────────────────┘
```

#### 3. Sidebar Placement

**File:** `/opt/kasaai/apps/b2c-portal/src/components/dashboard/DashboardSidebar.tsx`

**Change:**
Moved organization switcher from footer to header for better visibility.

**Location:**
```tsx
{/* Logo, Organization Switcher, and Collapse Button */}
<div className="p-4 border-b border-gray-200 dark:border-gray-700 space-y-3">
  {/* Logo */}
  <div className="flex items-center justify-between">...</div>

  {/* Organization Switcher - Header Location */}
  {!isCollapsed && (
    <div>
      <OrganizationSwitcher variant="compact" />
    </div>
  )}
</div>
```

#### 4. Admin Page Integration

**File:** `/opt/kasaai/apps/b2c-portal/src/pages/admin/Organizations.tsx`

Added prominent organization switcher at top of page:

```tsx
<Card className="mb-6 bg-gradient-to-r from-indigo-50 to-purple-50">
  <CardHeader>
    <CardTitle>Switch Organization Context</CardTitle>
    <CardDescription>
      Change the organization you're viewing to manage organization-specific data
    </CardDescription>
  </CardHeader>
  <CardContent>
    <OrganizationSwitcher variant="prominent" showSearch={true} />
  </CardContent>
</Card>
```

---

### Shared Hook for All Apps

#### useOrganizationSwitcher Hook

**File:** `/opt/kasaai/apps/shared/ui-hooks/src/useOrganizationSwitcher.ts`

**Purpose:** Reusable organization switching logic for ChurchFlow, EventFlow, InkWave, StudyFlow, etc.

**Features:**
- Organization state management
- Universal admin support
- Auto-refresh capability
- LocalStorage persistence
- Error handling
- TypeScript support

**Usage:**
```tsx
import { useOrganizationSwitcher } from '@kasaai/ui-hooks';

function MyComponent() {
  const {
    currentOrg,
    organizations,
    allOrganizations,
    isUniversalAdmin,
    switchOrg,
    isLoading
  } = useOrganizationSwitcher({
    apiUrl: 'https://api.ailabsafrica.com',
    onSwitch: (org) => console.log('Switched to:', org.display_name)
  });

  return (
    <select value={currentOrg?.id} onChange={(e) => switchOrg(e.target.value)}>
      {organizations.map(({ organization }) => (
        <option key={organization.id} value={organization.id}>
          {organization.display_name}
        </option>
      ))}
    </select>
  );
}
```

**Options:**
- `apiUrl` - Base API URL (default: https://api.ailabsafrica.com)
- `onSwitch` - Callback when organization is switched
- `enableAllOrganizations` - Enable fetching all organizations for universal admins (default: true)
- `refreshInterval` - Auto-refresh interval in milliseconds (default: null)
- `getAccessToken` - Custom function to get access token
- `isUniversalAdmin` - Override universal admin check

**Returns:**
- `currentOrg` - Current active organization
- `organizations` - User's organization memberships
- `allOrganizations` - All organizations (universal admin only)
- `isLoading` - Loading state for user's organizations
- `isLoadingAll` - Loading state for all organizations
- `isUniversalAdmin` - Whether current user is universal admin
- `currentRole` - Current user's role in active organization
- `switchOrg` - Function to switch organizations
- `refreshOrganizations` - Function to refresh user's organizations
- `refreshAllOrganizations` - Function to refresh all organizations
- `error` - Error state

**Package:** `@kasaai/ui-hooks` v1.1.0

---

## Page Reload Strategy

### Current Behavior

**Page reload is kept as a FALLBACK option**, not the default:

```typescript
const switchOrganization = useCallback(async (
  organizationId: string,
  forceReload: boolean = false // Default: false
) => {
  // Update state
  setCurrentOrganization(targetOrg);
  localStorage.setItem(STORAGE_KEY, organizationId);

  // Force reload as fallback if requested
  if (forceReload) {
    setTimeout(() => window.location.reload(), 500);
  }
}, [organizations, allOrganizations, isUniversalAdmin, toast]);
```

### Why Keep Page Reload as Fallback?

1. **Complex Pages** - Some pages may have deeply nested state that doesn't react to org changes
2. **Legacy Components** - Older components that don't use React Query
3. **Explicit User Request** - User can trigger reload if needed
4. **Safety Net** - Ensures data consistency in edge cases

### When to Use `forceReload: true`?

```tsx
// Use case 1: Legacy page without React Query
await switchOrganization(orgId, true);

// Use case 2: Page with complex non-reactive state
await switchOrganization(orgId, true);

// Use case 3: After critical data operations
await updateOrganizationSettings(...);
await switchOrganization(orgId, true); // Ensure fresh data
```

### Recommended Approach for New Pages

Use React Query's cache invalidation instead of page reload:

```tsx
import { useQueryClient } from '@tanstack/react-query';

const queryClient = useQueryClient();

const handleOrgSwitch = async (orgId: string) => {
  await switchOrganization(orgId, false); // No reload

  // Invalidate all queries to refetch with new org context
  queryClient.invalidateQueries();
};
```

---

## Data Flow

```
┌─────────────────┐
│ User Actions    │
│ - Select Org    │
│ - Search        │
│ - Filter        │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────┐
│ OrganizationSwitcher        │
│ - Filter logic              │
│ - Display filtered results  │
│ - Handle user selection     │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│ OrganizationContext         │
│ - switchOrganization()      │
│ - Update currentOrg state   │
│ - Update localStorage       │
│ - Trigger onSwitch callback │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│ React Query (Optional)      │
│ - queryClient.invalidate    Queries()   │
│ - Refetch all data          │
│ - Or: forceReload fallback  │
└─────────────────────────────┘
```

---

## Security Considerations

### 1. Universal Admin Authorization

All `/organizations/all` endpoints enforce universal admin check:

```python
if not organization_service.is_universal_admin(user_id, user_email):
    raise HTTPException(
        status_code=403,
        detail="Only universal administrators can view all organizations"
    )
```

### 2. Organization Access Validation

When switching organizations, the system validates:
1. User is a member of the organization, OR
2. User is a universal admin

```typescript
if (!membership && !isUniversalAdmin) {
  throw new Error('Access denied to organization');
}
```

### 3. Data Isolation

All organization-scoped data includes `organization_id` filter:

```python
events = await db.events.find({
    "organization_id": org_id  # Always scoped
}).to_list(100)
```

---

## Testing Checklist

- [x] Universal admin can see all organizations
- [x] Regular admin only sees their organizations
- [x] Organization switch updates current organization
- [x] Search filters work correctly (name, display_name, description)
- [x] Industry filter works correctly
- [x] Status filter works correctly
- [x] Clear filters resets all filters
- [x] LocalStorage persists selection across sessions
- [x] Toast notifications show on switch
- [x] Sidebar header placement displays correctly
- [x] Admin page prominent display works
- [x] Shared hook exports correctly
- [x] Package version updated to 1.1.0
- [x] README documentation updated
- [x] TypeScript types exported

---

## Files Modified

### Backend
1. `/opt/kasaai/apps/shared/services/organization_service.py` - Added `list_all_organizations()`
2. `/opt/kasaai/apps/core_backend/backend/services/organization_service.py` - Enhanced search parameters
3. `/opt/kasaai/apps/core_backend/backend/routes/organizations.py` - Enhanced `/all` endpoint

### Frontend (b2c-portal)
4. `/opt/kasaai/apps/b2c-portal/src/contexts/OrganizationContext.tsx` - Enhanced with allOrganizations
5. `/opt/kasaai/apps/b2c-portal/src/components/organization/OrganizationSwitcher.tsx` - Complete rewrite with search/filters
6. `/opt/kasaai/apps/b2c-portal/src/components/dashboard/DashboardSidebar.tsx` - Moved to header
7. `/opt/kasaai/apps/b2c-portal/src/pages/admin/Organizations.tsx` - Added prominent switcher

### Shared UI Hooks
8. `/opt/kasaai/apps/shared/ui-hooks/src/useOrganizationSwitcher.ts` - New hook
9. `/opt/kasaai/apps/shared/ui-hooks/src/index.ts` - Export new hook
10. `/opt/kasaai/apps/shared/ui-hooks/package.json` - Version bump to 1.1.0
11. `/opt/kasaai/apps/shared/ui-hooks/README.md` - Documentation

### Documentation
12. `/opt/kasaai/apps/architecture/ORGANIZATION_SWITCHER_ENHANCEMENT.md` - This file

---

## Future Enhancements

### Potential Improvements

1. **Organization Quick Stats**
   - Show member count, active users, last activity
   - Display in switcher dropdown

2. **Recent Organizations**
   - Track recently accessed organizations
   - Show at top of dropdown for quick access

3. **Favorites**
   - Allow users to favorite organizations
   - Starred section in dropdown

4. **Keyboard Shortcuts**
   - `Cmd/Ctrl + K` to open org switcher
   - Arrow keys for navigation
   - Enter to switch

5. **Organization Groups**
   - Group organizations by industry, region, or custom tags
   - Collapsible sections in dropdown

6. **Organization Health Indicators**
   - Show status badges (healthy, warning, error)
   - Based on system metrics

7. **Bulk Operations**
   - Switch multiple organizations for comparison
   - Side-by-side view mode

---

## Related Documentation

- [Organization System](/opt/kasaai/apps/shared/ORGANIZATION_SYSTEM.md)
- [Shared UI Hooks](/opt/kasaai/apps/shared/ui-hooks/README.md)
- [Authentication Setup](/opt/kasaai/apps/architecture/AUTHENTICATION_SETUP.md)

---

## Version History

| Version | Date       | Changes                                      |
|---------|------------|----------------------------------------------|
| 1.0     | 2025-10-26 | Initial implementation - Universal admin access, advanced search, shared hook |

---

**Maintained by:** AI Labs Africa
**Contact:** alfred.anyan@gmail.com
