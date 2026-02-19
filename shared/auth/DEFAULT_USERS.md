# Default Supabase Authentication Users

All KasaAI applications use centralized Supabase authentication at `https://supabase.ailabsafrica.com`.

## Default Test Users

### Universal Admin - Alfred Anyan
- **Email**: `alfred.anyan@gmail.com`
- **Password**: `AlfredSecure2024!`
- **Role**: Universal Admin
- **Supabase UUID**: `65715ad2-bcfa-42aa-ab21-e0b06f19b3e4`
- **Permissions**: Full access to all organizations and features
- **Purpose**: Primary administrator account for AI Labs Ltd.

### Admin User
- **Email**: `admin@ailabsafrica.com`
- **Password**: `Admin@2024!`
- **Role**: Universal Admin
- **Supabase UUID**: `4a6252e7-3dc7-483a-92c3-59a0a814a169`
- **Permissions**: Full access to all organizations and features

### Regular User
- **Email**: `user@ailabsafrica.com`
- **Password**: `User@2024!`
- **Role**: Standard User / Universal Admin
- **Supabase UUID**: `a1d7c822-847f-40ec-9fed-cc3cd9155c06`
- **Permissions**: Access to organizations and universal admin features

## Environment Configuration

All applications should use these environment variables:

```bash
SUPABASE_URL=https://supabase.ailabsafrica.com
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_ROLE_KEY=<service-role-key>

# Universal Admin Configuration
UNIVERSAL_ADMIN_EMAILS=admin@ailabsafrica.com,alfred.anyan@gmail.com,user@ailabsafrica.com
UNIVERSAL_ADMIN_USER_IDS=4a6252e7-3dc7-483a-92c3-59a0a814a169,65715ad2-bcfa-42aa-ab21-e0b06f19b3e4,a1d7c822-847f-40ec-9fed-cc3cd9155c06
```

## Email Server Setup (iRedMail)

These users must also exist in the iRedMail server for email functionality:

### Creating Users in iRedMail

```bash
# SSH to mail server
ssh root@mail.ailabsafrica.com

# Create admin user
sudo bash /var/www/iredadmin/tools/create_user.sh admin@ailabsafrica.com Admin@2024!

# Create regular user
sudo bash /var/www/iredadmin/tools/create_user.sh user@ailabsafrica.com User@2024!

# Or via web interface:
# https://mail.ailabsafrica.com/iredadmin
# Login with postmaster credentials
# Navigate to: Domains > ailabsafrica.com > Users > Add
```

## Supabase User Setup

### Via Supabase Dashboard

1. Navigate to: https://supabase.ailabsafrica.com/project/_/auth/users
2. Click "Add User"
3. Enter email and password
4. Confirm email (or disable email confirmation in settings for dev)

### Via SQL (Supabase Database)

```sql
-- Get the user UUID after creation
SELECT id, email, created_at
FROM auth.users
WHERE email IN ('admin@ailabsafrica.com', 'user@ailabsafrica.com');

-- Update UNIVERSAL_ADMIN_USER_IDS with the admin UUID
```

## Application Integration

### Backend (.env)

```bash
# Supabase Configuration
SUPABASE_URL=https://supabase.ailabsafrica.com
SUPABASE_ANON_KEY=<your-anon-key>
SUPABASE_SERVICE_ROLE_KEY=<your-service-role-key>

# Universal Admins
UNIVERSAL_ADMIN_EMAILS=admin@ailabsafrica.com,alfred.anyan@gmail.com,user@ailabsafrica.com
UNIVERSAL_ADMIN_USER_IDS=4a6252e7-3dc7-483a-92c3-59a0a814a169,65715ad2-bcfa-42aa-ab21-e0b06f19b3e4,a1d7c822-847f-40ec-9fed-cc3cd9155c06
```

### Frontend (.env)

```bash
VITE_SUPABASE_URL=https://supabase.ailabsafrica.com
VITE_SUPABASE_ANON_KEY=<your-anon-key>
```

## First-Time Login Flow

1. User navigates to app login page
2. Enter email and password
3. Supabase validates credentials
4. JWT token issued
5. Application checks organization membership
6. If universal admin: access to all organizations
7. If regular user: access to assigned organizations only

## Testing Authentication

### Backend Test

```bash
# Test with curl
curl -X POST https://dev-erp-api.ailabsafrica.com/api/v1/auth/test \
  -H "Authorization: Bearer <jwt-token>" \
  -H "X-Organization-ID: <org-id>"
```

### Frontend Test

```typescript
// Login
const { data, error } = await supabase.auth.signInWithPassword({
  email: 'admin@ailabsafrica.com',
  password: 'Admin@2024!'
})

// Check session
const { data: { session } } = await supabase.auth.getSession()
```

## Security Notes

⚠️ **Production**: Change default passwords immediately
⚠️ **Production**: Use strong, unique passwords
⚠️ **Production**: Enable 2FA for admin accounts
⚠️ **Development**: These credentials are for dev/testing only

## Troubleshooting

### User Can't Log In
1. Verify user exists in Supabase
2. Check email is confirmed (or confirmation disabled)
3. Verify password is correct
4. Check Supabase service is running

### User Has No Organization Access
1. User must be added to at least one organization
2. Check organization_users collection in MongoDB
3. Verify organization_id in requests

### Universal Admin Not Working
1. Verify email in UNIVERSAL_ADMIN_EMAILS
2. Check user UUID in UNIVERSAL_ADMIN_USER_IDS
3. Restart application after .env changes
