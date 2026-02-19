# Supabase Authentication Setup for KasaAI Applications

**Last Updated**: 2025-02-11
**Supabase Instance**: https://supabase.ailabsafrica.com

---

## Overview

All KasaAI applications use centralized Supabase authentication. This document describes the complete setup process for authentication across all applications.

## Default Users

### Admin User (Universal Admin)
- **Email**: `admin@ailabsafrica.com`
- **Password**: `Admin@2024!`
- **Role**: Universal Admin
- **Permissions**: Full access to all organizations across all applications

### Regular User
- **Email**: `user@ailabsafrica.com`
- **Password**: `User@2024!`
- **Role**: Standard User
- **Permissions**: Access only to assigned organizations

## Setup Process

### 1. Supabase User Creation

#### Via Supabase Dashboard

1. Navigate to: https://supabase.ailabsafrica.com/project/_/auth/users
2. Click "Add User" or "Invite User"
3. For each user:
   - **Email**: admin@ailabsafrica.com / user@ailabsafrica.com
   - **Password**: Set strong password
   - **Auto Confirm User**: Yes (for dev environment)
   - **Email Confirm**: Optional (disable for dev)

4. After creation, note the User UUID from the users table

#### Via SQL

```sql
-- Check if users exist
SELECT id, email, created_at, email_confirmed_at
FROM auth.users
WHERE email IN ('admin@ailabsafrica.com', 'user@ailabsafrica.com');

-- Get user UUIDs for environment configuration
SELECT
    id as user_uuid,
    email,
    created_at
FROM auth.users
WHERE email = 'admin@ailabsafrica.com';
```

### 2. Email Server Setup (iRedMail)

These users must also exist in iRedMail for email functionality:

#### Access iRedMail Admin Panel

```
URL: https://mail.ailabsafrica.com/iredadmin
Login: postmaster@ailabsafrica.com
```

#### Create Users via Web Interface

1. Navigate to: **Domains** → **ailabsafrica.com** → **Users** → **Add User**
2. Create admin user:
   - Email: `admin@ailabsafrica.com`
   - Password: `Admin@2024!`
   - Display Name: `KasaAI Admin`
   - Quota: 1024 MB
3. Create regular user:
   - Email: `user@ailabsafrica.com`
   - Password: `User@2024!`
   - Display Name: `KasaAI User`
   - Quota: 512 MB

#### Create Users via CLI (Alternative)

```bash
# SSH to mail server
ssh root@mail.ailabsafrica.com

# Create admin user
cd /var/www/iredadmin/tools
sudo bash create_user.sh admin@ailabsafrica.com 'Admin@2024!'

# Create regular user
sudo bash create_user.sh user@ailabsafrica.com 'User@2024!'

# Verify users created
sudo bash list_users.sh ailabsafrica.com
```

### 3. Application Configuration

#### Backend Environment Variables

Every KasaAI application backend needs:

```bash
# .env file

# Supabase Configuration
SUPABASE_URL=https://supabase.ailabsafrica.com
SUPABASE_ANON_KEY=<your-anon-key>
SUPABASE_SERVICE_ROLE_KEY=<your-service-role-key>

# Universal Admin Configuration
UNIVERSAL_ADMIN_EMAILS=admin@ailabsafrica.com
UNIVERSAL_ADMIN_USER_IDS=<uuid-from-supabase>

# Example:
# UNIVERSAL_ADMIN_USER_IDS=550e8400-e29b-41d4-a716-446655440000
```

**Getting the UUIDs:**

1. Create users in Supabase
2. Run SQL query:
   ```sql
   SELECT id, email FROM auth.users WHERE email = 'admin@ailabsafrica.com';
   ```
3. Copy the UUID to UNIVERSAL_ADMIN_USER_IDS

#### Frontend Environment Variables

```bash
# .env

# Supabase Configuration
VITE_SUPABASE_URL=https://supabase.ailabsafrica.com
VITE_SUPABASE_ANON_KEY=<your-anon-key>

# API Base URL (varies per app)
VITE_API_BASE_URL=https://dev-erp-api.ailabsafrica.com/api/v1
```

### 4. Testing Authentication

#### Backend Test

```bash
# Get JWT token from Supabase
curl -X POST https://supabase.ailabsafrica.com/auth/v1/token?grant_type=password \
  -H "apikey: <SUPABASE_ANON_KEY>" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@ailabsafrica.com",
    "password": "Admin@2024!"
  }'

# Use token to test API
curl https://dev-erp-api.ailabsafrica.com/api/v1/organizations \
  -H "Authorization: Bearer <access_token>" \
  -H "X-Organization-ID: <org-id>"
```

#### Frontend Test

```typescript
import { supabase } from './lib/supabase'

// Test login
const { data, error } = await supabase.auth.signInWithPassword({
  email: 'admin@ailabsafrica.com',
  password: 'Admin@2024!'
})

if (error) {
  console.error('Login failed:', error.message)
} else {
  console.log('Login successful:', data.user.email)
  console.log('Access token:', data.session.access_token)
}
```

## Application Integration Checklist

For each new KasaAI application:

### Backend
- [ ] Install `supabase-py` package
- [ ] Import `apps.shared.auth.supabase_auth`
- [ ] Configure SUPABASE_URL and SUPABASE_ANON_KEY
- [ ] Set UNIVERSAL_ADMIN_EMAILS and UNIVERSAL_ADMIN_USER_IDS
- [ ] Use `get_current_user()` dependency in protected routes
- [ ] Test authentication with both users

### Frontend
- [ ] Install `@supabase/supabase-js`
- [ ] Configure VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY
- [ ] Create AuthContext using shared pattern
- [ ] Implement login/logout flows
- [ ] Add Authorization header to API client
- [ ] Test login with both users

### Database
- [ ] Ensure organization_users collection exists
- [ ] Add admin user to default organization
- [ ] Verify organization access control works

## Email Configuration (Optional)

### For Password Reset Emails

Configure Supabase to use your SMTP server:

1. Go to: Supabase Dashboard → Authentication → Settings → Email Templates
2. Configure SMTP:
   - **SMTP Host**: mail.ailabsafrica.com
   - **SMTP Port**: 587
   - **SMTP User**: noreply@ailabsafrica.com
   - **SMTP Password**: <smtp-password>
   - **Sender Email**: noreply@ailabsafrica.com
   - **Sender Name**: KasaAI

3. Customize email templates:
   - Confirmation Email
   - Password Reset
   - Magic Link
   - Invite User

## Security Best Practices

### Development
✅ Use default passwords for testing
✅ Disable email confirmation for faster development
✅ Keep service role key secret (never in frontend)

### Production
⚠️ **Change all default passwords immediately**
⚠️ **Enable email confirmation**
⚠️ **Enable 2FA for admin accounts**
⚠️ **Rotate service role key regularly**
⚠️ **Use strong, unique passwords**
⚠️ **Enable rate limiting on auth endpoints**
⚠️ **Monitor authentication logs**

## Troubleshooting

### User Can't Log In

1. **Check user exists in Supabase**
   ```sql
   SELECT * FROM auth.users WHERE email = 'admin@ailabsafrica.com';
   ```

2. **Check email confirmed**
   ```sql
   SELECT email_confirmed_at FROM auth.users WHERE email = 'admin@ailabsafrica.com';
   ```

3. **Disable email confirmation (dev only)**
   - Supabase Dashboard → Authentication → Settings
   - Uncheck "Enable email confirmations"

4. **Check password**
   - Try password reset flow
   - Ensure password meets requirements

### Token Invalid/Expired

1. **Check token format**: `Bearer <token>`
2. **Verify token expiry**: Default 1 hour
3. **Use refresh token** to get new access token
4. **Check Supabase URL** matches environment

### Organization Access Denied

1. **Check user in organization**
   ```javascript
   // MongoDB query
   db.organization_users.find({
     user_id: "<supabase-user-uuid>",
     is_active: true
   })
   ```

2. **Check X-Organization-ID header** is set
3. **Verify organization exists**
4. **Check UNIVERSAL_ADMIN_USER_IDS** for admin

## Monitoring

### Authentication Metrics to Track

- Login attempts (success/failure)
- Token refresh rate
- Password reset requests
- User creation rate
- Session duration
- API calls per user

### Logs to Monitor

```bash
# Application logs
sudo journalctl -u kasaai-erp-backend -f | grep -i auth

# Nginx access logs
sudo tail -f /var/log/nginx/dev-erp-api_access.log | grep Authorization
```

## References

- [Supabase Auth Documentation](https://supabase.com/docs/guides/auth)
- [DEFAULT_USERS.md](../shared/auth/DEFAULT_USERS.md)
- [Shared Auth README](../shared/auth/README.md)
- [Organization System](../shared/ORGANIZATION_SYSTEM.md)

---

**Need Help?**

Contact: dev@ailabsafrica.com
Slack: #kasaai-dev
