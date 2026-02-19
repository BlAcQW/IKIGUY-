# Shared Authentication System

Centralized Supabase authentication for all KasaAI applications.

## Overview

All KasaAI applications use Supabase authentication hosted at `https://supabase.ailabsafrica.com`. This provides:

- JWT-based authentication
- Secure password hashing
- Session management
- User metadata storage
- Email verification (optional)
- Password recovery

## Quick Start

### 1. Import Authentication Dependencies

```python
from apps.shared.auth.supabase_auth import (
    get_current_user,
    get_current_user_optional,
    verify_token,
)
```

### 2. Protect Routes

```python
from fastapi import APIRouter, Depends
from apps.shared.auth.supabase_auth import get_current_user

router = APIRouter()

@router.get("/protected")
async def protected_route(user: dict = Depends(get_current_user)):
    """Protected endpoint requiring authentication."""
    return {"user": user["email"], "id": user["id"]}
```

### 3. Configure Environment

```bash
SUPABASE_URL=https://supabase.ailabsafrica.com
SUPABASE_ANON_KEY=<your-anon-key>
SUPABASE_SERVICE_ROLE_KEY=<your-service-role-key>
```

## Default Users

See [DEFAULT_USERS.md](./DEFAULT_USERS.md) for default test users and setup instructions.

- **Admin**: admin@ailabsafrica.com
- **User**: user@ailabsafrica.com

## Authentication Flow

```
1. User submits credentials to frontend
2. Frontend calls Supabase auth API
3. Supabase returns JWT token
4. Frontend stores token
5. Frontend includes token in all API requests (Authorization header)
6. Backend validates token with Supabase
7. Backend extracts user info from token
8. Backend checks organization membership
9. Backend processes request with user context
```

## Available Functions

### `get_current_user()`
Requires valid JWT token. Returns user dict or raises 401.

```python
@router.get("/me")
async def get_me(user: dict = Depends(get_current_user)):
    return user
```

### `get_current_user_optional()`
Optional authentication. Returns user dict or None.

```python
@router.get("/public-or-private")
async def flexible_route(user: dict | None = Depends(get_current_user_optional)):
    if user:
        return {"message": f"Hello {user['email']}"}
    return {"message": "Hello guest"}
```

### `verify_token()`
Manually verify a JWT token.

```python
from apps.shared.auth.supabase_auth import verify_token

user = await verify_token(token)
```

## User Object Structure

```python
{
    "id": "uuid",              # Supabase user UUID
    "sub": "uuid",             # Same as id
    "email": "user@example.com",
    "email_verified": true,
    "phone": null,
    "role": "authenticated",
    "aud": "authenticated",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
}
```

## Integration with Organization System

Authentication is integrated with the organization system:

```python
from apps.shared.dependencies import require_organization_access

@router.get("/data")
async def get_data(
    user: dict = Depends(get_current_user),
    org_id: str = Depends(require_organization_access)
):
    """
    Requires:
    1. Valid authentication
    2. Organization membership
    """
    # User has access to org_id
    return {"organization": org_id, "user": user["email"]}
```

## Frontend Integration

### React Setup

```typescript
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  import.meta.env.VITE_SUPABASE_URL,
  import.meta.env.VITE_SUPABASE_ANON_KEY
)

// Login
const { data, error } = await supabase.auth.signInWithPassword({
  email: 'user@example.com',
  password: 'password'
})

// Get session
const { data: { session } } = await supabase.auth.getSession()

// Logout
await supabase.auth.signOut()
```

### API Client with Auth

```typescript
import axios from 'axios'
import { supabase } from './supabase'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
})

api.interceptors.request.use(async (config) => {
  const { data: { session } } = await supabase.auth.getSession()

  if (session?.access_token) {
    config.headers.Authorization = `Bearer ${session.access_token}`
  }

  return config
})
```

## Security Best Practices

1. **Always use HTTPS** in production
2. **Never expose service role key** to frontend
3. **Validate tokens server-side** - never trust client claims
4. **Set appropriate token expiry** (default: 1 hour)
5. **Use refresh tokens** for long sessions
6. **Implement rate limiting** on auth endpoints
7. **Log authentication attempts** for security monitoring

## Testing

### Unit Tests

```python
import pytest
from apps.shared.auth.supabase_auth import verify_token

@pytest.mark.asyncio
async def test_verify_token():
    """Test token verification."""
    # Mock token
    token = "valid.jwt.token"
    user = await verify_token(token)
    assert user["email"] == "test@example.com"
```

### Integration Tests

```python
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_protected_route():
    """Test protected route with auth."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Without auth - should fail
        response = await client.get("/api/v1/protected")
        assert response.status_code == 401

        # With auth - should succeed
        headers = {"Authorization": "Bearer valid_token"}
        response = await client.get("/api/v1/protected", headers=headers)
        assert response.status_code == 200
```

## Troubleshooting

### "Invalid token" error
- Check token format: `Bearer <token>`
- Verify token hasn't expired
- Ensure Supabase URL is correct

### "User not found" error
- User may not exist in Supabase
- Check email confirmation status
- Verify Supabase service is running

### CORS errors

**Common Symptoms:**
- Browser blocks authentication requests with CORS policy error
- "Request header field x-supabase-api-version is not allowed" error
- "The 'Access-Control-Allow-Origin' header contains multiple values" error

**Quick Fixes:**

1. **Missing x-supabase-api-version header** (Supabase JS SDK v2+ requirement):
   ```nginx
   # In nginx config, add x-supabase-api-version to allowed headers:
   add_header Access-Control-Allow-Headers "Authorization, Content-Type, Accept, apikey, X-Client-Info, x-supabase-api-version" always;
   ```

2. **Duplicate CORS headers** (nginx + upstream both adding headers):
   ```nginx
   # In nginx location blocks, hide upstream CORS headers:
   location /auth/v1/ {
       proxy_hide_header Access-Control-Allow-Origin;
       proxy_hide_header Access-Control-Allow-Methods;
       proxy_hide_header Access-Control-Allow-Headers;
       proxy_hide_header Access-Control-Expose-Headers;
       proxy_hide_header Access-Control-Allow-Credentials;

       proxy_pass http://upstream;
   }
   ```

3. **Missing CORS on specific routes**:
   - Nginx specific location blocks don't inherit from generic `/` blocks
   - Add `proxy_hide_header` to EACH specific location block

**Detailed Guide**: See [NGINX CORS Setup Guide](../../architecture/NGINX_CORS_SETUP.md) for comprehensive CORS configuration patterns and troubleshooting.

**Testing CORS**:
```bash
# Test for duplicate headers (should return "1")
curl -s -I https://supabase-api.ailabsafrica.com/auth/v1/token \
  -H "Origin: https://app.ailabsafrica.com" | \
  grep -c "access-control-allow-origin"

# Test preflight request
curl -s -I -X OPTIONS https://supabase-api.ailabsafrica.com/auth/v1/token \
  -H "Origin: https://app.ailabsafrica.com" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: x-supabase-api-version,content-type,authorization" | \
  grep -i "access-control"
```

## Migration from Other Auth Systems

If migrating from another auth system:

1. Export user emails and hashed passwords
2. Use Supabase Admin API to bulk import
3. Send password reset emails to all users
4. Update application code to use new auth
5. Test thoroughly before switching over

## References

- [Supabase Auth Documentation](https://supabase.com/docs/guides/auth)
- [JWT.io](https://jwt.io) - Token debugger
- [DEFAULT_USERS.md](./DEFAULT_USERS.md) - Default test users
