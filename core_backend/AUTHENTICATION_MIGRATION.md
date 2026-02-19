# Backend Authentication Migration from Supabase to MongoDB

## Overview
The backend authentication system has been migrated from Supabase to MongoDB. This migration provides better integration with the core backend, eliminates external dependencies, and provides more control over user management.

## Migration Status ✅ COMPLETED

### New MongoDB Authentication System - ✅ IMPLEMENTED
- [x] **auth_service.py** - New MongoDB authentication service
- [x] **auth.py** - Added `get_current_user_mongo()` function for MongoDB JWT validation
- [x] **routes/auth.py** - New authentication endpoints (`/auth/signup`, `/auth/signin`, `/auth/signout`, `/auth/me`)
- [x] **utils/auth.py** - JWT generation and validation utilities for MongoDB auth
- [x] **models/user.py** - MongoDB user models
- [x] **models/organization.py** - MongoDB organization models

### Deprecated Supabase Authentication - ⚠️ DEPRECATED
- [x] **routes/supabase_consolidated.deprecated.py** - Supabase consolidated routes (deprecated)
- [x] **services/supabase_consolidated_service.deprecated.py** - Supabase service (deprecated)
- [x] **auth.py:get_current_user_bearer()** - Supabase JWT validation (deprecated with warning)

### Partially Migrated Files - ⚠️ MIXED SYSTEM
- [x] **routes/admin.py** - Contains both MongoDB and deprecated Supabase functions

## Authentication Endpoints

### New MongoDB Authentication Endpoints ✅ ACTIVE
```
POST   /auth/signup        - Create new user with organization
POST   /auth/signin        - Authenticate user and get JWT tokens
POST   /auth/signout       - Sign out user and invalidate tokens
GET    /auth/me           - Get current user profile
POST   /auth/refresh      - Refresh access token
GET    /auth/health       - Check authentication service health
```

### Deprecated Supabase Endpoints ❌ DEPRECATED
```
POST   /supabase-consolidated/auth/authenticate  - Use /auth/signin instead
GET    /supabase-consolidated/auth/current       - Use /auth/me instead
POST   /supabase-consolidated/users/create       - Use /auth/signup instead
```

## JWT Token Structure

### New MongoDB JWT Claims ✅ CURRENT
```json
{
  "sub": "user_id",
  "email": "user@example.com",
  "name": "User Name",
  "user_metadata": {
    "first_name": "User",
    "last_name": "Name",
    "avatar_url": ""
  },
  "app_metadata": {},
  "role": "authenticated",
  "aud": "kasaai-core",
  "iss": "kasaai-auth",
  "iat": 1234567890,
  "exp": 1234567890,
  "organization_id": "org_id"
}
```

### Deprecated Supabase JWT Claims ❌ DEPRECATED
```json
{
  "sub": "supabase_user_id",
  "email": "user@example.com",
  "aud": "authenticated",
  "iss": "https://supabase-project.supabase.co/auth/v1",
  // ... other Supabase-specific claims
}
```

## Backend Functions Migration Guide

### Authentication Dependencies
```python
# OLD (deprecated)
from ..auth import get_current_user_bearer

@router.get("/protected")
async def protected_route(user: dict = Depends(get_current_user_bearer)):
    pass

# NEW (MongoDB)
from ..auth import get_current_user_mongo

@router.get("/protected")
async def protected_route(user: dict = Depends(get_current_user_mongo)):
    pass
```

### User Management
```python
# OLD (deprecated Supabase)
from supabase import create_client
supabase = create_client(url, key)
response = supabase.auth.admin.create_user({
    "email": email,
    "password": password
})

# NEW (MongoDB)
from ..services.auth_service import auth_service
user = await auth_service.create_user({
    "email": email,
    "password": password,
    "first_name": first_name,
    "last_name": last_name
})
```

## Database Changes

### User Storage Migration
- **Old**: Users stored in Supabase auth tables
- **New**: Users stored in MongoDB `users` collection
- **Organizations**: Automatically created in MongoDB `organizations` collection

### Data Structure
```python
# Old Supabase User (external service)
{
  "id": "supabase_uuid",
  "email": "user@example.com",
  "user_metadata": {...},
  "app_metadata": {...}
}

# New MongoDB User (internal control)
{
  "_id": ObjectId(),
  "id": "user_uuid",
  "email": "user@example.com",
  "first_name": "User",
  "last_name": "Name",
  "display_name": "User Name",
  "password_hash": "hashed_password",
  "is_active": True,
  "is_verified": False,
  "primary_organization_id": "org_uuid",
  "created_at": datetime,
  "updated_at": datetime
}
```

## Security Improvements

### JWT Token Security
- **Issuer Control**: Tokens issued by core backend (not external service)
- **Custom Claims**: Include organization_id for multi-tenancy
- **Token Refresh**: Proper refresh token implementation
- **Expiration**: Configurable token expiration times

### Password Security
- **Hashing**: Uses bcrypt for password hashing
- **Validation**: Configurable password requirements
- **Rate Limiting**: Can implement custom rate limiting

## Cleanup Tasks ⚠️ FUTURE WORK

### High Priority
1. **Update admin functions** in `routes/admin.py` to use MongoDB instead of Supabase
2. **Replace Supabase user management** calls with MongoDB equivalents
3. **Update remaining endpoints** to use `get_current_user_mongo` instead of `get_current_user_bearer`

### Medium Priority
1. **Remove deprecated routes** after confirming they're not in use
2. **Clean up Supabase imports** from files that no longer need them
3. **Update documentation** to reflect MongoDB authentication

### Low Priority
1. **Remove Supabase dependencies** from requirements.txt if completely unused
2. **Delete deprecated files** after thorough testing
3. **Update environment variables** documentation

## File Status Summary

### ✅ Fully Migrated to MongoDB
- `backend/services/auth_service.py`
- `backend/routes/auth.py`
- `backend/utils/auth.py`
- `backend/models/user.py`
- `backend/models/organization.py`

### ❌ Deprecated (Supabase)
- `backend/routes/supabase_consolidated.deprecated.py`
- `backend/services/supabase_consolidated_service.deprecated.py`
- Functions using `supabase.auth.admin.*`

### ⚠️ Partially Migrated (Mixed)
- `backend/routes/admin.py` - Contains both systems
- `backend/auth.py` - Has both `get_current_user_bearer` (deprecated) and `get_current_user_mongo` (new)

### 🔍 Needs Review
- Any files importing from deprecated services
- Scripts using Supabase authentication
- Tests using Supabase authentication

## Environment Variables

### New MongoDB Auth Variables
```bash
# MongoDB Authentication Configuration
JWT_SECRET_KEY=your-jwt-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
MONGODB_URL=mongodb://...
```

### Deprecated Supabase Variables (can be removed after full migration)
```bash
# Deprecated - can be removed
SUPABASE_URL=https://...
SUPABASE_ANON_KEY=...
SUPABASE_SERVICE_ROLE_KEY=...
```

## Testing Status

### ✅ Tested and Working
- User signup with organization creation
- User signin with JWT token generation
- JWT token validation
- Password hashing and verification
- Token refresh functionality
- Authentication middleware

### ⚠️ Needs Testing
- Admin user management with MongoDB
- Migration of existing Supabase users to MongoDB
- Integration with existing services using the new auth

## Notes
- The MongoDB authentication system is fully functional and ready for production
- Deprecated Supabase functions are marked but still available for backward compatibility
- New development should use MongoDB authentication exclusively
- The migration provides better security, control, and integration with the core backend