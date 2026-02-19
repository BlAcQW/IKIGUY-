# KasaAI Drive - Authentication & Organization Integration

## Overview

KasaAI Drive is fully integrated with the centralized authentication and organization system used across all KasaAI applications.

## Authentication Integration

### Uses Shared Supabase Auth

Location: `@shared/auth/supabase_auth.py`

The Drive backend uses the centralized Supabase authentication system:

```python
from apps.shared.auth.supabase_auth import verify_supabase_token

# In dependencies.py
user_data = await verify_supabase_token(token)
```

### Default Users

All default users from `@shared/auth/DEFAULT_USERS.md` work automatically:

**Universal Admins** (have access to all organizations):
- `admin@ailabsafrica.com` / `Admin@2024!`
- `alfred.anyan@gmail.com` / `AlfredSecure2024!`
- `user@ailabsafrica.com` / `User@2024!`

These users can access Drive immediately without additional setup.

## Organization Integration

### Uses Shared Organization Service

Location: `@shared/services/organization_service.py`

The Drive integrates with the centralized organization system described in `@shared/ORGANIZATION_SYSTEM.md`:

```python
from apps.shared.services.organization_service import get_organization_service

# Check organization access
org_service = get_organization_service(db)
has_access = await org_service.has_access_to_organization(
    organization_id, user_id, email
)
```

### Default Organization: AI Labs Ltd.

**Organization ID**: `ai_labs_ltd`
**Display Name**: `AI Labs Ltd.`

When users don't specify an organization, they are automatically assigned to "AI Labs Ltd." This is the default organization for the entire KasaAI platform.

**Behavior**:
1. User logs in with Supabase credentials
2. If no `X-Organization-ID` header provided, defaults to `ai_labs_ltd`
3. If user doesn't belong to organization, they are auto-added (for AI Labs Ltd. only)
4. User can access Drive with their organization's files

### Organization Priority

The system determines organization ID in this order:

1. **X-Organization-ID header** (explicit selection by user)
2. **User metadata** (organization_id in Supabase user metadata)
3. **Default organization** (AI Labs Ltd. - `ai_labs_ltd`)

### Example API Request

```bash
# Using default organization (AI Labs Ltd.)
curl https://drive-api.ailabsafrica.com/api/folders/root/contents \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Using specific organization
curl https://drive-api.ailabsafrica.com/api/folders/root/contents \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "X-Organization-ID: some_other_org_id"
```

## Role-Based Access Control

### Three-Tier Role System

1. **Universal Admin** (`universal_admin`)
   - Access to ALL organizations
   - Defined in `UNIVERSAL_ADMIN_EMAILS` environment variable
   - Can view, edit, delete any files across all organizations
   - Examples: alfred.anyan@gmail.com, admin@ailabsafrica.com

2. **Organization Admin** (`admin`)
   - Full access within their organization
   - Can manage all files in their organization
   - Can share files with other users
   - Can create public share links

3. **Organization User** (`user`)
   - Standard access within their organization
   - Can upload, download, manage their own files
   - Can access shared files based on permissions
   - Cannot manage other users' files (unless shared)

### Permission Hierarchy

File permissions follow this hierarchy:

- **manage**: Full control (rename, move, delete, share)
- **edit**: Can modify file content
- **comment**: Can add comments (future feature)
- **view**: Can only view/download

## Environment Configuration

Required in `/opt/kasaai/.env`:

```bash
# Supabase Authentication
SUPABASE_URL=https://supabase.ailabsafrica.com
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# Organization System
DEFAULT_ORGANIZATION_ID=ai_labs_ltd
DEFAULT_ORGANIZATION_NAME=AI Labs Ltd.

# Universal Admins (comma-separated)
UNIVERSAL_ADMIN_EMAILS=admin@ailabsafrica.com,alfred.anyan@gmail.com,user@ailabsafrica.com
UNIVERSAL_ADMIN_USER_IDS=4a6252e7-3dc7-483a-92c3-59a0a814a169,65715ad2-bcfa-42aa-ab21-e0b06f19b3e4,a1d7c822-847f-40ec-9fed-cc3cd9155c06
```

## Testing Authentication

### 1. Test with Default User

```bash
# Login as admin (universal admin)
curl -X POST https://supabase.ailabsafrica.com/auth/v1/token?grant_type=password \
  -H "apikey: YOUR_ANON_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@ailabsafrica.com",
    "password": "Admin@2024!"
  }'

# Use the returned access_token
export TOKEN="<access_token_from_response>"

# Test Drive API
curl https://drive-api.ailabsafrica.com/api/folders/root/contents \
  -H "Authorization: Bearer $TOKEN"
```

### 2. Test Organization Access

```bash
# Alfred (universal admin) accessing AI Labs Ltd.
curl https://drive-api.ailabsafrica.com/api/folders/root/contents \
  -H "Authorization: Bearer $TOKEN"
  # Auto-uses ai_labs_ltd organization

# Alfred accessing a specific organization
curl https://drive-api.ailabsafrica.com/api/folders/root/contents \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Organization-ID: some_church_org"
```

### 3. Test File Upload

```bash
curl -X POST https://drive-api.ailabsafrica.com/api/files/upload \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Organization-ID: ai_labs_ltd" \
  -F "file=@test.pdf" \
  -F "parent_id=null" \
  -F "organization_id=ai_labs_ltd"
```

## Frontend Integration

### Setting Organization Context

```typescript
// src/lib/api.ts
import axios from 'axios';

const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
});

// Add auth token and organization ID to all requests
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('supabase_token');
  const orgId = localStorage.getItem('current_organization_id') || 'ai_labs_ltd';

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  if (orgId) {
    config.headers['X-Organization-ID'] = orgId;
  }

  return config;
});

export default apiClient;
```

### Organization Selector Component

```typescript
// src/components/OrganizationSelector.tsx
import { useState, useEffect } from 'react';
import { supabase } from '@/lib/supabase';
import api from '@/lib/api';

export function OrganizationSelector() {
  const [organizations, setOrganizations] = useState([]);
  const [currentOrgId, setCurrentOrgId] = useState(
    localStorage.getItem('current_organization_id') || 'ai_labs_ltd'
  );

  useEffect(() => {
    // Fetch user's organizations
    api.get('/api/v1/organizations')
      .then(res => {
        setOrganizations(res.data.organizations);

        // If no current org set, use AI Labs Ltd.
        if (!currentOrgId && res.data.organizations.length > 0) {
          const aiLabs = res.data.organizations.find(
            org => org.organization.id === 'ai_labs_ltd'
          );
          if (aiLabs) {
            setCurrentOrgId('ai_labs_ltd');
            localStorage.setItem('current_organization_id', 'ai_labs_ltd');
          }
        }
      })
      .catch(err => console.error('Failed to fetch organizations:', err));
  }, []);

  const handleOrgChange = (orgId: string) => {
    localStorage.setItem('current_organization_id', orgId);
    setCurrentOrgId(orgId);
    window.location.reload(); // Reload to fetch new org data
  };

  return (
    <select
      value={currentOrgId}
      onChange={(e) => handleOrgChange(e.target.value)}
      className="px-3 py-2 border rounded-lg"
    >
      <option value="ai_labs_ltd">AI Labs Ltd. (Default)</option>
      {organizations.filter(org => org.organization.id !== 'ai_labs_ltd')
        .map((org) => (
          <option key={org.organization.id} value={org.organization.id}>
            {org.organization.display_name} ({org.role})
          </option>
        ))}
    </select>
  );
}
```

## Security Features

### Token Verification

All requests verify JWT tokens with Supabase using the shared auth module.

### Organization Isolation

Files are strictly isolated by organization:
- Queries always filter by `organization_id`
- Users can only access files in organizations they belong to
- Universal admins can access all organizations

### Permission Checks

Every file operation checks:
1. User authentication (valid JWT token)
2. Organization membership
3. File-level permissions (owner, shared users, public links)

## Troubleshooting

### User Can't Access Drive

**Issue**: "User must belong to an organization to access drive"

**Solutions**:
1. Verify user is logged in with valid Supabase credentials
2. Check user belongs to at least one organization
3. For AI Labs Ltd., users are auto-added on first access
4. Verify `UNIVERSAL_ADMIN_EMAILS` includes user's email if they should be universal admin

### Organization Not Found

**Issue**: "User does not have access to organization {org_id}"

**Solutions**:
1. Verify organization exists in MongoDB `organizations` collection
2. Check user is member of organization in `organization_users` collection
3. Verify `X-Organization-ID` header matches an organization user belongs to
4. For default org, ensure `DEFAULT_ORGANIZATION_ID=ai_labs_ltd` in .env

### Authentication Failed

**Issue**: "Invalid or expired token"

**Solutions**:
1. Verify Supabase is running at https://supabase.ailabsafrica.com
2. Check `SUPABASE_ANON_KEY` is correct in .env
3. Ensure JWT token hasn't expired (check expiry in token)
4. Verify user exists in Supabase auth.users table

## Summary

KasaAI Drive is fully integrated with:

✅ **Shared Supabase Auth** - Uses `@shared/auth/supabase_auth`
✅ **Centralized Organizations** - Uses `@shared/services/organization_service`
✅ **Default Organization** - AI Labs Ltd. (`ai_labs_ltd`)
✅ **Universal Admins** - From `@shared/auth/DEFAULT_USERS.md`
✅ **Role-Based Access** - Three-tier system (universal_admin, admin, user)
✅ **Multi-Tenant** - Complete data isolation between organizations

No additional setup required - uses the same auth system as all other KasaAI applications!
