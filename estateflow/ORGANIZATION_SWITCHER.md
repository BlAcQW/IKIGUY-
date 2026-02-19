# Organization Switcher Implementation

## Overview

Implemented universal admin organization switcher for EstateFlow, allowing admin@ailabsafrica.com to view and manage data across all organizations in the system.

## Implementation Date

December 8, 2025

## Features Implemented

### 1. Backend - Organizations API

**Created:**
- `/opt/kasaai/apps/estateflow/backend/app/api/organizations/router.py` - Organizations API endpoints
- `/opt/kasaai/apps/estateflow/backend/app/models/organization.py` - Organization model

**Endpoints:**
- `GET /api/v1/organizations` - List all organizations (admin only)
- `GET /api/v1/organizations/{id}` - Get organization by ID

**Authorization:**
- Admin users (`admin@ailabsafrica.com` or `role=admin`): See all organizations
- Regular users: See only their assigned organization

### 2. Frontend - Organization Context & Switcher

**Created:**
- `/opt/kasaai/apps/estateflow/frontend/src/contexts/OrganizationContext.tsx` - Organization state management
- `/opt/kasaai/apps/estateflow/frontend/src/components/OrganizationSwitcher.tsx` - Switcher UI component
- `/opt/kasaai/apps/estateflow/frontend/src/lib/api.ts` - API client with organization support

**Updated:**
- `/opt/kasaai/apps/estateflow/frontend/src/App.tsx` - Added OrganizationProvider
- `/opt/kasaai/apps/estateflow/frontend/src/components/layout/Header.tsx` - Added OrganizationSwitcher
- `/opt/kasaai/apps/estateflow/frontend/src/lib/api-config.ts` - Added organizations endpoints

**Features:**
- Auto-loads all organizations for admin users on login
- Shows organization switcher dropdown in header (admin only)
- Persists selected organization in localStorage
- Regular users see only their organization (no switcher)

### 3. API Client

The new API client (`lib/api.ts`) provides:
- Token-based authentication
- Organization context headers (`X-Organization-ID`)
- Type-safe request methods (GET, POST, PUT, DELETE)

**Usage:**
```typescript
import { api } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import { useOrganization } from '@/contexts/OrganizationContext';

const { getAccessToken } = useAuth();
const { selectedOrganizationId } = useOrganization();

// Make API call with organization context
const data = await api.get('/api/v1/properties', {
  token: getAccessToken(),
  organizationId: selectedOrganizationId
});
```

## How It Works

### Admin User Flow

1. **Login**: Admin user (admin@ailabsafrica.com) logs in
2. **Organization Loading**: OrganizationContext fetches all organizations via `/api/v1/organizations`
3. **UI Display**: Organization switcher appears in header with dropdown
4. **Selection**: Admin selects an organization from the dropdown
5. **Context Update**: Selected organization ID is stored in localStorage and context
6. **API Calls**: All subsequent API calls include the selected organization ID
7. **Data Filtering**: Backend filters data by the selected organization ID

### Regular User Flow

1. **Login**: Regular user logs in
2. **Organization Loading**: OrganizationContext uses their assigned organization ID
3. **UI Display**: No switcher shown (only one organization available)
4. **API Calls**: All API calls automatically use their organization ID
5. **Data Filtering**: User only sees data from their organization

## Database Organization IDs

Current organizations in the database:

| Organization ID | Name | Properties | Purpose |
|----------------|------|-----------|---------|
| `68cc21d968f3a4c4d6847bc0` | User Organization | 5 | Your manually created properties |
| `test_org_properties_001` | Ghana Premium Properties | 10 | Test script properties |
| `test_org_001` | Test Org 1 | 1 | Test data |
| `test_org_email_001` | Test Email Org | 1 | Email testing |
| `52c6ce95-7093-4071-84bd-6774149597bf` | Test Org 2 | 1 | Test data |

**Total:** 18 properties across 5 organizations

## Testing

### Backend Testing

```bash
# Test organizations endpoint (requires valid token)
curl -X GET "https://estateflow-api.ailabsafrica.com/api/v1/organizations" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Frontend Testing

1. Log in as `admin@ailabsafrica.com`
2. Look for organization switcher in the header (next to page title)
3. Click to see dropdown with all organizations
4. Select different organizations
5. Navigate to Properties page - properties should change based on selected organization

## Migration Script

A migration script was created to move test properties to your organization:

**Script:** `/tmp/migrate_test_properties.py`

**Usage:**
```bash
python3 /tmp/migrate_test_properties.py
```

**What it does:**
- Copies 10 test properties from `test_org_properties_001` to your organization
- Preserves all property data (name, type, price, amenities, etc.)
- Updates organization_id to your organization
- Prevents ID conflicts by prefixing with "migrated_"

**Note:** You can now use the organization switcher instead of migrating data!

## UI Components Used

- **Command**: Searchable command palette (shadcn/ui)
- **Popover**: Dropdown menu container (shadcn/ui)
- **Button**: Switcher trigger button (shadcn/ui)
- **lucide-react icons**: Building2, ChevronsUpDown, Check

## Security Considerations

1. **Authorization**: Backend validates user role before showing all organizations
2. **Organization Isolation**: Regular users cannot access other organizations' data
3. **Token Validation**: All API calls require valid Supabase authentication token
4. **Context Enforcement**: Backend `get_organization_context` ensures data isolation

## Future Enhancements

1. **Organization Management UI**:
   - Create new organizations
   - Edit organization details
   - Manage organization members

2. **Role-Based Access**:
   - Organization admins (not just universal admin)
   - Per-organization permissions

3. **Organization Branding**:
   - Custom logos in switcher
   - Organization-specific themes
   - Branded invoices and documents

4. **Analytics**:
   - Per-organization usage statistics
   - Cross-organization comparisons (admin view)

## Troubleshooting

### Issue: Organization switcher not showing

**Check:**
1. User is logged in as admin@ailabsafrica.com
2. User role is set to "admin" in Supabase user_metadata
3. OrganizationContext is loaded successfully (check browser console)

### Issue: Properties not changing when switching organizations

**Check:**
1. Properties API is using the organization context
2. Selected organization ID is being passed to API calls
3. Backend is filtering by organization_id correctly

### Issue: "Could not validate credentials" error

**Check:**
1. Token is not expired (tokens expire after some time)
2. User exists in Supabase
3. Supabase URL and key are correct in environment variables

## Related Files

### Backend
- `app/api/organizations/` - Organizations API
- `app/models/organization.py` - Organization model
- `app/core/auth.py` - Authentication and organization context
- `app/api/__init__.py` - API router registration

### Frontend
- `src/contexts/OrganizationContext.tsx` - Organization state
- `src/contexts/AuthContext.tsx` - Authentication state
- `src/components/OrganizationSwitcher.tsx` - Switcher UI
- `src/components/layout/Header.tsx` - Header with switcher
- `src/lib/api.ts` - API client
- `src/lib/api-config.ts` - API endpoints configuration

## Database Schema

**organizations collection:**
```json
{
  "id": "org_12345",
  "name": "Company Name",
  "description": "Optional description",
  "address": "Physical address",
  "phone": "+233 30 123 4567",
  "email": "info@company.com",
  "website": "www.company.com",
  "tax_id": "TIN-GH-12345",
  "payment_info": "Bank details",
  "logo_url": "https://...",
  "invoice_settings": {
    "invoice_prefix": "INV",
    "next_invoice_number": 1000
  },
  "created_at": "2025-12-08T...",
  "updated_at": "2025-12-08T..."
}
```

**All data collections include:**
- `organization_id`: Links data to organization
- Backend automatically filters by this field based on user context

## Deployment

### Backend
```bash
sudo systemctl restart kasaai-estateflow-backend
```

### Frontend
```bash
cd /opt/kasaai/apps/estateflow/frontend
npm run build
```

### Verification
```bash
# Check backend is running
sudo systemctl status kasaai-estateflow-backend

# Check organizations API
curl https://estateflow-api.ailabsafrica.com/api/v1/organizations
```

---

**Status:** ✅ Fully implemented and deployed

**Next Steps:**
1. Test organization switcher with fresh admin login
2. Verify properties change when switching organizations
3. Test that regular users don't see the switcher
4. (Optional) Run migration script if you want test properties in your organization
