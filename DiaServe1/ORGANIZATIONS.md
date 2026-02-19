# EstateFlow Organizations

## Overview

EstateFlow supports multi-tenancy through organizations. All data (properties, bookings, contacts, campaigns, documents) is scoped to an organization. Users can be members of multiple organizations with different roles.

## Active Organizations

### 1. AI Labs Ltd

**Organization Details:**
- **ID**: `f1d1ad21-123d-48aa-a087-2125eca56c4c`
- **Name**: `ai-labs-ltd` (internal identifier)
- **Display Name**: AI Labs Ltd.
- **Industry**: Technology
- **Company Size**: 10-50 employees
- **Website**: https://ailabsafrica.com
- **Location**: Accra, Ghana

**Invoice Settings:**
- **Prefix**: AIL
- **Currency**: GHS (Ghana Cedi)
- **Tax Label**: VAT
- **Default Tax Rate**: 0%
- **Payment Terms**: Net 30

**Members:**
- admin@ailabsafrica.com (Admin)
- alfred.anyan@gmail.com (Admin)
- user@ailabsafrica.com (Admin)

**Purpose:** Primary organization for AI Labs Africa technology solutions and services.

---

### 2. Diaserve Ltd

**Organization Details:**
- **ID**: `b41ac840-782c-4598-8da9-286b0eac38c7`
- **Name**: `diaserve-ltd` (internal identifier)
- **Display Name**: Diaserve Ltd
- **Industry**: Real Estate
- **Company Size**: 10-50 employees
- **Website**: https://diaserve.com
- **Location**: Accra, Ghana

**Invoice Settings:**
- **Prefix**: DIA
- **Currency**: GHS (Ghana Cedi)
- **Tax Label**: VAT
- **Default Tax Rate**: 12.5%
- **Late Fee**: 2.5%
- **Payment Terms**: Net 30
- **Date Format**: DD/MM/YYYY
- **Header Text**: "Diaserve Ltd - Property Management Services"
- **Footer Text**: "Thank you for choosing Diaserve Ltd!"

**Members:**
- admin@ailabsafrica.com (Admin)
- alfred.anyan@gmail.com (Admin)
- user@ailabsafrica.com (Admin)

**Purpose:** Real estate and property management company focused on property listings, bookings, and client management.

---

## Organization Roles

### Admin
- Full access to organization data
- Can manage properties, bookings, contacts, campaigns
- Can view and manage all organization settings
- Can invite/remove users

### User
- Access to organization data based on permissions
- Can create and manage assigned properties
- Limited administrative capabilities

### Universal Admin
- Special role with access to ALL organizations
- Current universal admins:
  - admin@ailabsafrica.com
  - alfred.anyan@gmail.com
  - user@ailabsafrica.com

---

## Data Isolation

All EstateFlow data is organization-scoped:

### Properties
- Each property belongs to one organization
- Properties are filtered by organization_id automatically
- Cross-organization property access is not permitted

### Bookings
- Bookings are scoped to the organization of the property
- Clients/contacts are organization-specific

### Contacts
- Contact lists are separate per organization
- No contact sharing across organizations

### Campaigns
- Marketing campaigns are organization-specific
- Segment filters apply only to organization contacts

### Documents
- Document templates are organization-scoped
- Generated documents are private to organization

### Invoices
- Invoice numbering is per-organization
- Invoice settings (prefix, tax rate) are organization-specific

---

## Switching Organizations

Users who are members of multiple organizations can switch context:

### Backend API
- Organization context is determined from user's JWT token
- `user_metadata.organization_id` in Supabase JWT
- Backend extracts organization_id via `get_organization_context()` dependency

### Frontend (Future Enhancement)
- Organization switcher in UI (not yet implemented)
- User can select active organization from dropdown
- All API calls include organization context

---

## Adding New Organizations

### Via MongoDB Script

```python
from apps.shared.models.organization import Organization
from motor.motor_asyncio import AsyncIOMotorClient
from uuid import uuid4
from datetime import datetime

# Create organization
org = Organization(
    id=str(uuid4()),
    name="company-name",
    display_name="Company Name Ltd",
    description="Company description",
    industry="Industry",
    website="https://company.com",
    ...
)

# Insert to database
await db.organizations.insert_one(org.dict())
```

### Via API (Future Enhancement)
- POST `/api/v1/organizations` (not yet implemented)
- Requires admin authentication
- Auto-creates organization and adds creator as admin

---

## Organization Settings

Each organization has customizable settings:

### Branding
- Logo URL
- Primary color (hex)
- Secondary color (hex)
- Accent color (hex)

### Invoice Configuration
- Invoice number prefix
- Starting invoice number
- Default payment terms
- Tax ID/VAT number
- Tax label and rate
- Late fee percentage
- Header and footer text

### Banking Details
- Bank name
- Account number
- Routing number
- IBAN
- SWIFT/BIC code

### General Settings
- Custom settings stored in `settings` JSON field
- Application-specific configurations

---

## Multi-Organization User Access

Users can belong to multiple organizations with different roles:

```json
{
  "user_id": "4a6252e7-3dc7-483a-92c3-59a0a814a169",
  "organizations": [
    {
      "organization_id": "f1d1ad21-123d-48aa-a087-2125eca56c4c",
      "organization_name": "AI Labs Ltd.",
      "role": "admin"
    },
    {
      "organization_id": "b41ac840-782c-4598-8da9-286b0eac38c7",
      "organization_name": "Diaserve Ltd",
      "role": "admin"
    }
  ]
}
```

---

## Database Collections

### organizations
Stores organization master data:
- Organization profile
- Branding settings
- Invoice settings
- Banking details

### organization_users
Maps users to organizations:
- User membership
- Roles and permissions
- Join dates and activity

### organization_invitations
Manages pending invitations:
- Invitation tokens
- Expiry dates
- Acceptance status

---

## API Context Enforcement

All EstateFlow API endpoints enforce organization context:

```python
@router.get("/properties")
async def list_properties(
    org_context: Dict = Depends(get_organization_context)
):
    # org_context = {
    #   "organization_id": "b41ac840-782c-4598-8da9-286b0eac38c7",
    #   "user_id": "4a6252e7-3dc7-483a-92c3-59a0a814a169"
    # }

    # Only return properties for this organization
    properties = await property_service.list_properties(
        organization_id=org_context["organization_id"]
    )
    return properties
```

---

## Testing Organizations

### Login as Admin
```bash
# Get JWT token
curl -X POST 'http://localhost:8000/auth/v1/token?grant_type=password' \
  -H 'apikey: <SUPABASE_ANON_KEY>' \
  -H 'Content-Type: application/json' \
  -d @- << EOF
{
  "email": "admin@ailabsafrica.com",
  "password": "Admin@2024!"
}
EOF
```

### Test API with Organization Context
```bash
# List properties for user's organization
curl "http://localhost:30039/api/v1/properties" \
  -H "Authorization: Bearer <JWT_TOKEN>"

# Backend automatically filters by organization_id from JWT
```

---

## Organization Migration

If moving data between organizations:

1. **Export data** from source organization
2. **Update organization_id** on all records
3. **Import data** to target organization
4. **Verify data integrity**

**Warning:** This is a destructive operation. Always backup data first.

---

## Future Enhancements

- [ ] Organization switcher in frontend UI
- [ ] Organization creation API endpoint
- [ ] Organization settings page
- [ ] User invitation system
- [ ] Organization deletion (with data cascade)
- [ ] Organization transfer (change ownership)
- [ ] Organization analytics and reporting
- [ ] Sub-organizations (hierarchical structure)

---

**Last Updated**: December 7, 2025
**Organizations**: 2 active
**Total Members**: 6 (3 per organization)
