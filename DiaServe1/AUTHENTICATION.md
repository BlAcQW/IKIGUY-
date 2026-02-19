# EstateFlow Authentication System

## Overview

EstateFlow uses **real Supabase authentication** with JWT token validation for secure user authentication. The system provides seamless authentication across frontend and backend with protected routes and organization-based multi-tenancy.

## Authentication Flow

```
1. User visits EstateFlow → Redirected to /login (if not authenticated)
2. User enters credentials → Frontend calls Supabase auth API
3. Supabase validates credentials → Returns JWT access token
4. Token stored in localStorage → Automatically included in API requests
5. Backend validates JWT with Supabase → Extracts user info
6. User gains access → Can access protected routes and API endpoints
```

## Frontend Implementation

### 1. Supabase Client Configuration

**File**: `frontend/src/lib/supabase.ts`

```typescript
import { createClient } from '@supabase/supabase-js';

export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    autoRefreshToken: true,
    persistSession: true,
    detectSessionInUrl: true
  }
});
```

### 2. Authentication Context

**File**: `frontend/src/contexts/AuthContext.tsx`

Provides global authentication state management with:
- User and session state
- signIn, signUp, signOut methods
- Auto session refresh
- Auth state change listeners

### 3. Protected Routes

**File**: `frontend/src/components/ProtectedRoute.tsx`

Wraps all dashboard routes and redirects unauthenticated users to /login:

```typescript
export function ProtectedRoute() {
  const { user, loading } = useAuth();

  if (loading) return <Loader2 />;
  if (!user) return <Navigate to="/login" replace />;

  return <Outlet />;
}
```

### 4. API Integration

**Files**: `frontend/src/lib/api/*.ts`

All API clients use `getAuthTokenSync()` to retrieve JWT tokens from Supabase localStorage:

```typescript
import { getAuthTokenSync } from "../auth";

export async function listProperties() {
  const token = getAuthTokenSync();

  const response = await fetch(url, {
    headers: getDefaultHeaders(token || undefined)
  });

  return response.json();
}
```

### 5. Login Page

**File**: `frontend/src/pages/Login.tsx`

Provides email/password authentication with:
- Loading states
- Error handling
- Toast notifications
- Auto-redirect if already logged in

## Backend Implementation

### 1. Authentication Utilities

**File**: `backend/app/core/auth.py`

Provides JWT validation with Supabase:

```python
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """Validate JWT token and extract user information."""
    supabase = get_supabase()
    token = credentials.credentials

    # Verify JWT with Supabase
    response = supabase.auth.get_user(token)

    if not response or not response.user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return {
        "id": response.user.id,
        "email": response.user.email,
        "role": response.user.user_metadata.get("role", "user"),
        "organization_id": response.user.user_metadata.get("organization_id")
    }
```

### 2. Protected Endpoints

All API endpoints use `get_current_user` dependency:

```python
@router.get("/properties")
async def list_properties(
    user: Dict[str, Any] = Depends(get_current_user)
):
    # User is authenticated
    return {"properties": [...]}
```

### 3. Organization Context

Multi-tenancy support via organization context:

```python
async def get_organization_context(
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, str]:
    """Extract organization context from authenticated user."""
    organization_id = user.get("organization_id")

    if not organization_id:
        raise HTTPException(status_code=403, detail="User has no organization")

    return {
        "organization_id": organization_id,
        "user_id": user.get("id")
    }
```

## Configuration

### Frontend Environment Variables

**File**: `frontend/.env`

```env
VITE_API_URL=http://localhost:30039
VITE_APP_NAME=EstateFlow
VITE_SUPABASE_URL=https://supabase.ailabsafrica.com
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Backend Environment Variables

**File**: `/opt/kasaai/.env` (shared)

```env
SUPABASE_URL=https://supabase.ailabsafrica.com
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## Default Test Users

For development and testing purposes:

### Admin User
- **Email**: `admin@ailabsafrica.com`
- **Password**: `Admin@2024!`
- **Role**: Universal Admin
- **Supabase UUID**: `4a6252e7-3dc7-483a-92c3-59a0a814a169`

### Regular User
- **Email**: `user@ailabsafrica.com`
- **Password**: `User@2024!`
- **Role**: Standard User
- **Supabase UUID**: `a1d7c822-847f-40ec-9fed-cc3cd9155c06`

See `/opt/kasaai/apps/shared/auth/DEFAULT_USERS.md` for complete list.

## Testing Authentication

### 1. Get JWT Token

```bash
curl -X POST 'http://localhost:8000/auth/v1/token?grant_type=password' \
  -H 'apikey: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...' \
  -H 'Content-Type: application/json' \
  -d @- << 'EOF'
{
  "email": "admin@ailabsafrica.com",
  "password": "Admin@2024!"
}
EOF
```

### 2. Test API with JWT

```bash
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

curl "http://localhost:30039/api/v1/properties" \
  -H "Authorization: Bearer $TOKEN"
```

## Security Features

### Frontend
- ✅ JWT tokens stored securely in localStorage by Supabase
- ✅ Auto token refresh before expiration
- ✅ Protected routes redirect to login
- ✅ Automatic session cleanup on logout

### Backend
- ✅ Real JWT validation with Supabase
- ✅ User information extracted from verified tokens
- ✅ Organization-based access control
- ✅ No mock authentication in production

## User Metadata Structure

Supabase stores user metadata in JWT:

```json
{
  "user_metadata": {
    "organization_id": "52c6ce95-7093-4071-84bd-6774149597bf",
    "role": "admin"
  }
}
```

This metadata is used for:
- Multi-tenancy (organization isolation)
- Role-based access control
- User permissions

## Implementation Status

- ✅ Supabase client configuration
- ✅ AuthContext with React hooks
- ✅ Login/Logout UI components
- ✅ Protected routes
- ✅ Backend JWT validation
- ✅ API integration
- ✅ Frontend build complete
- ✅ End-to-end testing successful

## Future Enhancements

- [ ] Password reset flow
- [ ] Email verification
- [ ] Two-factor authentication (2FA)
- [ ] Social login (Google, GitHub)
- [ ] Session management dashboard
- [ ] Audit logging for authentication events

## Troubleshooting

### User Can't Log In

1. Verify user exists in Supabase
2. Check email is confirmed (or confirmation disabled)
3. Verify password is correct
4. Check Supabase service is running: `sudo docker ps | grep supabase`
5. Check backend logs: `sudo journalctl -u kasaai-estateflow-backend -f`

### API Returns 401 Unauthorized

1. Verify JWT token is not expired
2. Check `Authorization: Bearer <token>` header is present
3. Verify backend Supabase configuration is correct
4. Restart backend service: `sudo systemctl restart kasaai-estateflow-backend`

### Protected Routes Not Working

1. Verify AuthProvider wraps the app in App.tsx
2. Check ProtectedRoute component is wrapping dashboard routes
3. Verify user session exists in localStorage
4. Clear browser cache and try again

## References

- Supabase Documentation: https://supabase.com/docs
- Supabase Auth API: https://supabase.com/docs/reference/javascript/auth-api
- FastAPI Security: https://fastapi.tiangolo.com/tutorial/security/
- React Router Protected Routes: https://reactrouter.com/en/main/start/tutorial#protected-routes

---

**Last Updated**: December 7, 2025
**Status**: Production Ready ✅
