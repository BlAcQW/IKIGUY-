# Nginx CORS Configuration Update

**Date:** 2025-11-08
**File:** `/etc/nginx/sites-enabled/studyflow-api.ailabsafrica.com.conf`
**Purpose:** Allow X-Organization-Id header for organization-scoped API requests

## Change Made

Updated the `Access-Control-Allow-Headers` directive to include `X-Organization-Id`:

**Before:**
```nginx
add_header 'Access-Control-Allow-Headers' 'Content-Type, Authorization, Accept, Origin, X-Requested-With' always;
```

**After:**
```nginx
add_header 'Access-Control-Allow-Headers' 'Content-Type, Authorization, Accept, Origin, X-Requested-With, X-Organization-Id' always;
```

## Lines Changed
- Line 48: Main CORS headers
- Line 56: OPTIONS preflight CORS headers

## Deployment
```bash
# Test configuration
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx
```

## Impact
- Frontend can now send `X-Organization-Id` header with API requests
- Backend receives organization context from header
- Materials and other resources properly filtered by organization
- CORS errors resolved for organization-scoped requests

## Related Changes
- Backend: `app/core/auth.py` - Added `x_organization_id` header parameter
- Frontend: `lib/api.ts` - Added X-Organization-Id header to all requests
- Frontend: `lib/organization-context.tsx` - OrganizationContext manages current org
