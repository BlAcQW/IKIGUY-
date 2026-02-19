# Default Users - DevotionalFlow (FreshManna)

This document lists the default user accounts created for testing and administration of the DevotionalFlow platform.

## Default User Accounts

### 1. Universal Admin (KasaAI Admin)
**Purpose**: Administrative account consistent across all KasaAI platforms

```
Email:    admin@ailabsafrica.com
Password: Admin@2024!
Role:     pastor
Ministry: Fresh Manna
```

**Capabilities**:
- Full admin dashboard access
- User management
- Content moderation
- Platform settings configuration
- System analytics
- Create and publish devotionals

---

### 2. Test User (Regular Reader)
**Purpose**: Standard user account for testing reader features

```
Email:    user@ailabsafrica.com
Password: User@123
Role:     reader
```

**Capabilities**:
- Read devotionals
- Like and comment
- Bookmark content
- Track reading progress
- Personalize reading preferences

---

### 3. Platform Admin (FreshManna Admin)
**Purpose**: Platform-specific administrator account

```
Email:    admin@freshmanna.com
Password: Admin@123
Role:     admin
```

**Capabilities**:
- Same as Universal Admin
- Platform-specific administration
- Content oversight
- Moderation tasks

---

### 4. Test Pastor (Content Creator)
**Purpose**: Pastor account for testing author/content creation features

```
Email:    pastor@freshmanna.com
Password: Pastor@123
Role:     pastor
Ministry: Test Ministry
```

**Capabilities**:
- Create and publish devotionals
- Author dashboard access
- Performance analytics
- Milestone tracking
- Content management

---

## API Endpoints

### Signup
```bash
POST /api/v1/auth/signup
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "Password123",
  "name": "User Name",
  "role": "reader" | "pastor"
}
```

### Login
```bash
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "Password123"
}
```

**Response**:
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "user": { ... }
}
```

---

## Creating Additional Default Users

To recreate or add more default users, run:

```bash
cd /opt/kasaai/apps/devotionalflow/backend
/opt/kasaai/apps/venv/bin/python scripts/create_default_users.py
```

The script:
- Checks if users already exist (won't duplicate)
- Creates missing default users
- Uses consistent passwords across environments
- Sets up role-specific fields

---

## Security Notes

⚠️ **PRODUCTION DEPLOYMENT**:
- Change all default passwords before production deployment
- Use environment variables for admin credentials
- Enable Supabase OAuth for social login
- Implement rate limiting for auth endpoints
- Set up proper CORS origins

---

## Testing Scenarios

### Admin Testing
```bash
# Login as admin
curl -X POST http://localhost:30042/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@ailabsafrica.com","password":"Admin@2024!"}'

# Access admin dashboard
GET /api/v1/admin/dashboard/stats
Authorization: Bearer {access_token}
```

### Pastor Testing
```bash
# Login as pastor
curl -X POST http://localhost:30042/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"pastor@freshmanna.com","password":"Pastor@123"}'

# Create devotional
POST /api/v1/devotionals
Authorization: Bearer {access_token}
```

### Reader Testing
```bash
# Login as reader
curl -X POST http://localhost:30042/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@ailabsafrica.com","password":"User@123"}'

# Read devotionals
GET /api/v1/devotionals
Authorization: Bearer {access_token}
```

---

## Database Storage

Users are stored in MongoDB:
- Database: `devotionalflow`
- Collection: `users`
- Password: Hashed with bcrypt
- JWT tokens: HS256 algorithm

---

## Consistency Across KasaAI Platforms

These default users (`admin@ailabsafrica.com` and `user@ailabsafrica.com`) are consistent across all KasaAI applications:
- ChurchFlow
- StudyFlow
- EventFlow
- InkWave
- EstateFlow
- DevotionalFlow (FreshManna)
- Core Backend
- Developer Platform

This allows for unified testing and administration across the entire KasaAI ecosystem.
