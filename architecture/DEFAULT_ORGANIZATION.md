# Default Organization: AI Labs Ltd.

## Overview

All KasaAI applications that use the organization system automatically create a default organization named **"AI Labs Ltd."** on startup. This provides a consistent baseline for:

- Development and testing
- New user onboarding
- Demo and showcase environments
- Administrative access

## Organization Details

- **Name (Identifier)**: `ai-labs-ltd`
- **Display Name**: `AI Labs Ltd.`
- **Description**: `Default organization for AI Labs Africa`
- **Industry**: `Technology`
- **Website**: `https://ailabsafrica.com`

## Default Members

The following users are automatically added as **ADMIN** members:

### 1. Alfred Anyan (Primary Administrator)
- **Email**: `alfred.anyan@gmail.com`
- **Supabase UUID**: `65715ad2-bcfa-42aa-ab21-e0b06f19b3e4`
- **Role**: ADMIN
- **Universal Admin**: Yes

### 2. Admin User
- **Email**: `admin@ailabsafrica.com`
- **Supabase UUID**: `4a6252e7-3dc7-483a-92c3-59a0a814a169`
- **Role**: ADMIN
- **Universal Admin**: Yes

### 3. Regular User
- **Email**: `user@ailabsafrica.com`
- **Supabase UUID**: `a1d7c822-847f-40ec-9fed-cc3cd9155c06`
- **Role**: ADMIN
- **Universal Admin**: Yes

## Implementation

### Automatic Initialization

The default organization is created automatically during application startup via the shared startup module:

```python
# apps/shared/startup/default_organization.py
from apps.shared.startup import initialize_default_organization

# Called in app startup (main.py lifespan)
await initialize_default_organization()
```

### Idempotency

The initialization function is **idempotent** and safe to call on every startup:
- Checks if "AI Labs Ltd." already exists
- Creates it only if missing
- Ensures all default admins are members
- Updates roles if needed
- Logs success or skip status

### Applications Using Default Organization

The following applications automatically create the default organization:

- ✅ **ERP** - Enterprise Resource Planning
- 🔄 **ChurchFlow** - Church Management (pending)
- 🔄 **StudyFlow** - Educational Platform (pending)
- 🔄 **EventFlow** - Event Management (pending)
- 🔄 **InkWave** - Content Creation (pending)
- 🔄 **Core Backend** - Core API (pending)
- 🔄 **Developer Platform** - API Developer Portal (pending)

## Database Storage

The default organization is stored in each application's MongoDB database:

```javascript
// Collection: organizations
{
  "id": "<uuid>",
  "name": "ai-labs-ltd",
  "display_name": "AI Labs Ltd.",
  "description": "Default organization for AI Labs Africa",
  "industry": "Technology",
  "website": "https://ailabsafrica.com",
  "is_active": true,
  "created_at": "<timestamp>",
  "updated_at": "<timestamp>"
}

// Collection: organization_users (3 entries)
{
  "id": "<uuid>",
  "organization_id": "<org-id>",
  "user_id": "65715ad2-bcfa-42aa-ab21-e0b06f19b3e4",
  "email": "alfred.anyan@gmail.com",
  "role": "ADMIN",
  "is_active": true,
  "joined_at": "<timestamp>"
}
// ... similar for admin@ and user@
```

## Environment Configuration

All applications must have the default admin users configured in their `.env` files:

```bash
# Universal Admins
UNIVERSAL_ADMIN_EMAILS=admin@ailabsafrica.com,alfred.anyan@gmail.com,user@ailabsafrica.com
UNIVERSAL_ADMIN_USER_IDS=4a6252e7-3dc7-483a-92c3-59a0a814a169,65715ad2-bcfa-42aa-ab21-e0b06f19b3e4,a1d7c822-847f-40ec-9fed-cc3cd9155c06
```

## Verification

### Check if Default Organization Exists

```bash
# Dev server (85.214.12.174)
MONGODB_URI="mongodb://admin:aawwER4444%25@127.0.0.1:27017/erp?authSource=admin" python3 -c "
from pymongo import MongoClient
client = MongoClient('mongodb://admin:aawwER4444%25@127.0.0.1:27017/')
db = client['erp']
org = db['organizations'].find_one({'name': 'ai-labs-ltd'})
print('Found:', org)
"

# Production server (148.251.0.46)
ssh dev@148.251.0.46 "MONGODB_URI='mongodb://admin:aawwER4444%25@127.0.0.1:27017/erp?authSource=admin' python3 -c \"
from pymongo import MongoClient
client = MongoClient('mongodb://admin:aawwER4444%25@127.0.0.1:27017/')
db = client['erp']
org = db['organizations'].find_one({'name': 'ai-labs-ltd'})
print('Found:', org)
\""
```

### Check Organization Members

```bash
MONGODB_URI="mongodb://admin:aawwER4444%25@127.0.0.1:27017/erp?authSource=admin" python3 -c "
from pymongo import MongoClient
client = MongoClient('mongodb://admin:aawwER4444%25@127.0.0.1:27017/')
db = client['erp']
org = db['organizations'].find_one({'name': 'ai-labs-ltd'})
if org:
    members = list(db['organization_users'].find({'organization_id': org['id']}))
    for m in members:
        print(f\"{m['email']}: {m['role']}\")
"
```

## Benefits

### For Development
- Immediate access without manual setup
- Consistent test environment
- Pre-configured admin access

### For Production
- Quick onboarding for new deployments
- Guaranteed admin access
- Standard organizational structure

### For Users
- Clear starting point
- Automatic membership for authorized users
- No complex setup required

## Architecture Decision

This follows the **Convention over Configuration** principle:

1. **Sensible Defaults**: Every app starts with a working organization
2. **Zero Configuration**: No manual setup required
3. **Idempotent**: Safe to run repeatedly
4. **Extensible**: Users can create additional organizations
5. **Documented**: Clear ownership and purpose

## Security Considerations

⚠️ **Production Environments**:
- Default users should have strong passwords (already configured)
- Consider disabling default users after setting up production admins
- Monitor access logs for default accounts
- Rotate passwords periodically

✅ **Development Environments**:
- Default organization is safe and expected
- Credentials documented for team access
- No sensitive data should use default organization

## Troubleshooting

### Default Organization Not Created

Check startup logs:
```bash
sudo journalctl -u kasaai-erp-backend -n 100 | grep "default organization"
```

Expected output:
```
✅ Created default organization 'AI Labs Ltd.' (ID: <uuid>)
```

Or:
```
✅ Default organization 'AI Labs Ltd.' already exists (ID: <uuid>)
```

### Users Not Added to Default Organization

1. Verify users exist in Supabase
2. Check UNIVERSAL_ADMIN configuration in .env
3. Restart the service to re-run initialization
4. Check MongoDB for organization_users entries

### Cannot Access Default Organization

1. Verify user logged in successfully
2. Check user is in organization_users collection
3. Verify organization_id in API requests
4. Check universal admin configuration

## Future Enhancements

Potential improvements to the default organization system:

- [ ] Custom default organization name via environment variable
- [ ] Configurable default members list
- [ ] Default organization templates (industry-specific)
- [ ] Automatic data seeding (sample customers, projects, etc.)
- [ ] Multi-tenancy isolation improvements

## Related Documentation

- [ORGANIZATION_SYSTEM.md](../shared/ORGANIZATION_SYSTEM.md) - Complete organization system guide
- [DEFAULT_USERS.md](../shared/auth/DEFAULT_USERS.md) - Authentication and user setup
- [ORGANIZATION_IMPLEMENTATION_SUMMARY.md](../shared/ORGANIZATION_IMPLEMENTATION_SUMMARY.md) - Implementation details

## Changelog

### 2025-11-02
- ✅ Initial implementation
- ✅ Added alfred.anyan@gmail.com as primary admin
- ✅ Configured all three default users as universal admins
- ✅ Implemented in ERP application
- 🔄 Pending: Roll out to other applications

---

**Status**: ✅ Active
**Owner**: Alfred Anyan (alfred.anyan@gmail.com)
**Last Updated**: 2025-11-02
