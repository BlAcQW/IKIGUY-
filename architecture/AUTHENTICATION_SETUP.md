# KasaAI Authentication & Authorization Setup

**Version**: 1.0
**Last Updated**: 2025-10-24
**Status**: Production

---

## Table of Contents

1. [Overview](#overview)
2. [Supabase Configuration](#supabase-configuration)
3. [Environment Setup](#environment-setup)
4. [Backend Integration](#backend-integration)
5. [Frontend Integration](#frontend-integration)
6. [Database Schema](#database-schema)
7. [Security Best Practices](#security-best-practices)
8. [Troubleshooting](#troubleshooting)

---

## Overview

KasaAI uses **self-hosted Supabase** for authentication and authorization across all internal applications. This provides:

- **JWT-based authentication** with secure token management
- **Row Level Security (RLS)** for database access control
- **OAuth integrations** for social login
- **User management** with roles and permissions
- **Real-time subscriptions** for live data updates

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Internal Apps                          │
│  @apps/b2c-portal | @apps/core_backend |               │
│  @apps/developer_platform | @apps/ailabsafrica          │
└──────────────────┬──────────────────────────────────────┘
                   │
                   │ JWT Auth
                   ▼
┌─────────────────────────────────────────────────────────┐
│           Self-hosted Supabase Instance                  │
│                                                          │
│  API Gateway: https://supabase-api.ailabsafrica.com    │
│  Dashboard:   https://supabase.ailabsafrica.com        │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │   Auth API   │  │  PostgreSQL  │  │  Realtime    │ │
│  │   + JWT      │  │  + RLS       │  │  WebSocket   │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────┘
```

---

## Supabase Configuration

### Access Credentials

**Production Configuration (Internal Apps)**:

```bash
# API Gateway
SUPABASE_URL=https://supabase-api.ailabsafrica.com

# Authentication Keys
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxvY2FsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjEzMjIwNzUsImV4cCI6MjA3NjY4MjA3NX0.bwOq689zcxepQnidP5k4pU7e_MOr_SP-00UVEQFz0eQ

SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxvY2FsIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MTMyMjA3NSwiZXhwIjoyMDc2NjgyMDc1fQ.ncbP9EEe5v-3E7U9mhLNTfdq_VR-iUTxuNsaXn3HK2E

# JWT Secret (for token verification)
SUPABASE_JWT_SECRET=/HWoqwJ4l1nakz9BP52KFXccpzy61dh5qvkjLtxHno4=
```

**Database Direct Access**:

```bash
# For migrations and admin operations
DB_HOST=localhost
DB_PORT=5433
DB_USER=postgres
DB_PASSWORD=ciWfkEMFYnrYA6Ip665VbEps58SV5DY/
DB_NAME=postgres
```

### Dashboard Access

- **Supabase Studio**: https://supabase.ailabsafrica.com
- **API Gateway**: https://supabase-api.ailabsafrica.com

---

## Environment Setup

### Backend (.env)

Create a `.env` file in your backend directory:

```bash
# Copy from @apps/shared/.env.example
cp /opt/kasaai/apps/shared/.env.example .env
```

Required environment variables:

```bash
# Supabase Configuration
SUPABASE_URL=https://supabase-api.ailabsafrica.com
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxvY2FsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjEzMjIwNzUsImV4cCI6MjA3NjY4MjA3NX0.bwOq689zcxepQnidP5k4pU7e_MOr_SP-00UVEQFz0eQ
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxvY2FsIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MTMyMjA3NSwiZXhwIjoyMDc2NjgyMDc1fQ.ncbP9EEe5v-3E7U9mhLNTfdq_VR-iUTxuNsaXn3HK2E
SUPABASE_JWT_SECRET=/HWoqwJ4l1nakz9BP52KFXccpzy61dh5qvkjLtxHno4=

# MongoDB for application data
MONGODB_URL=mongodb://admin:password@127.0.0.1:27017/kasaai_core?authSource=admin

# Application settings
ENVIRONMENT=production
LOG_LEVEL=INFO
```

### Frontend (.env)

Create a `.env` file in your frontend directory:

```bash
# Supabase Configuration
VITE_SUPABASE_URL=https://supabase-api.ailabsafrica.com
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxvY2FsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjEzMjIwNzUsImV4cCI6MjA3NjY4MjA3NX0.bwOq689zcxepQnidP5k4pU7e_MOr_SP-00UVEQFz0eQ

# API Backend
VITE_API_URL=https://api.ailabsafrica.com
```

---

## Backend Integration

### Using Shared Supabase Service

```python
# Import from @apps/shared
from apps.shared.integration.supabase import SupabaseIntegration, SupabaseConfig
import os

# Initialize Supabase
supabase_config = SupabaseConfig(
    url=os.getenv("SUPABASE_URL"),
    anon_key=os.getenv("SUPABASE_ANON_KEY"),
    service_role_key=os.getenv("SUPABASE_SERVICE_ROLE_KEY"),
    timeout=30,
    verify_ssl=True
)

supabase = SupabaseIntegration(config=supabase_config)
```

### JWT Verification Middleware (FastAPI)

```python
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthCredentials
from jose import jwt, JWTError
import os

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthCredentials = Depends(security)
) -> dict:
    """
    Verify JWT token and extract user information.

    Returns:
        dict: User data from JWT payload

    Raises:
        HTTPException: If token is invalid or expired
    """
    token = credentials.credentials

    try:
        # Decode JWT using Supabase JWT secret
        payload = jwt.decode(
            token,
            os.getenv("SUPABASE_JWT_SECRET"),
            algorithms=["HS256"],
            audience="authenticated"
        )

        return {
            "user_id": payload.get("sub"),
            "email": payload.get("email"),
            "role": payload.get("role"),
            "metadata": payload.get("user_metadata", {})
        }

    except JWTError as e:
        raise HTTPException(
            status_code=401,
            detail=f"Invalid or expired token: {str(e)}"
        )

# Usage in routes
from fastapi import APIRouter

router = APIRouter()

@router.get("/profile")
async def get_profile(user: dict = Depends(get_current_user)):
    """Get authenticated user profile."""
    return {
        "success": True,
        "user": user
    }
```

### Admin Operations (Service Role)

```python
from apps.shared.integration.supabase_admin import SupabaseAdmin, SupabaseAdminConfig

# Initialize admin client
admin_config = SupabaseAdminConfig(
    url=os.getenv("SUPABASE_URL"),
    service_role_key=os.getenv("SUPABASE_SERVICE_ROLE_KEY")
)

admin = SupabaseAdmin(config=admin_config)

# Create user programmatically
async def create_system_user(email: str, password: str):
    """Create a user with service role."""
    result = await admin.insert_data(
        table="auth.users",
        data={
            "email": email,
            "encrypted_password": "hashed_password_here",
            "role": "authenticated"
        }
    )
    return result
```

---

## Frontend Integration

### React Setup with Supabase Client

```typescript
// src/lib/supabase.ts
import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    autoRefreshToken: true,
    persistSession: true,
    detectSessionInUrl: true
  }
});
```

### Authentication Hook

```typescript
// src/hooks/useAuth.ts
import { useState, useEffect } from 'react';
import { supabase } from '../lib/supabase';
import { User } from '@supabase/supabase-js';

export function useAuth() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Get initial session
    supabase.auth.getSession().then(({ data: { session } }) => {
      setUser(session?.user ?? null);
      setLoading(false);
    });

    // Listen for auth changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      (_event, session) => {
        setUser(session?.user ?? null);
      }
    );

    return () => subscription.unsubscribe();
  }, []);

  const signIn = async (email: string, password: string) => {
    const { data, error } = await supabase.auth.signInWithPassword({
      email,
      password
    });

    if (error) throw error;
    return data;
  };

  const signOut = async () => {
    const { error } = await supabase.auth.signOut();
    if (error) throw error;
  };

  const signUp = async (email: string, password: string) => {
    const { data, error } = await supabase.auth.signUp({
      email,
      password
    });

    if (error) throw error;
    return data;
  };

  return {
    user,
    loading,
    signIn,
    signOut,
    signUp
  };
}
```

### Protected Route Component

```typescript
// src/components/ProtectedRoute.tsx
import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

interface Props {
  children: React.ReactNode;
}

export function ProtectedRoute({ children }: Props) {
  const { user, loading } = useAuth();

  if (loading) {
    return <div>Loading...</div>;
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}
```

---

## Database Schema

### User Profiles Table

```sql
-- Create profiles table for additional user data
CREATE TABLE IF NOT EXISTS public.profiles (
  id UUID REFERENCES auth.users ON DELETE CASCADE PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  full_name TEXT,
  avatar_url TEXT,
  organization_id UUID,
  role TEXT DEFAULT 'user',
  metadata JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable Row Level Security
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

-- Users can view their own profile
CREATE POLICY "Users can view own profile"
  ON public.profiles
  FOR SELECT
  USING (auth.uid() = id);

-- Users can update their own profile
CREATE POLICY "Users can update own profile"
  ON public.profiles
  FOR UPDATE
  USING (auth.uid() = id);

-- Service role can manage all profiles
CREATE POLICY "Service role can manage profiles"
  ON public.profiles
  FOR ALL
  USING (auth.jwt() ->> 'role' = 'service_role');

-- Create function to handle new user creation
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.profiles (id, email, full_name)
  VALUES (NEW.id, NEW.email, NEW.raw_user_meta_data->>'full_name');
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to create profile on user signup
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();
```

---

## Security Best Practices

### 1. Token Management

```typescript
// Always store tokens securely
// ✅ Good: Supabase handles this automatically with localStorage encryption
const { data } = await supabase.auth.signInWithPassword({ email, password });

// ❌ Bad: Don't store tokens in plain text
localStorage.setItem('token', plainToken);
```

### 2. API Key Usage

```python
# ✅ Good: Use service role key only in backend
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# ❌ Bad: Never expose service role key in frontend
# VITE_SUPABASE_SERVICE_ROLE_KEY = "..." # DON'T DO THIS!
```

### 3. Row Level Security

```sql
-- ✅ Good: Always enable RLS on tables with sensitive data
ALTER TABLE sensitive_data ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users see only their data"
  ON sensitive_data
  FOR SELECT
  USING (auth.uid() = user_id);

-- ❌ Bad: Never disable RLS on production tables
ALTER TABLE sensitive_data DISABLE ROW LEVEL SECURITY; -- DON'T DO THIS!
```

### 4. Password Requirements

```python
# Enforce strong passwords
PASSWORD_MIN_LENGTH = 8
PASSWORD_REQUIREMENTS = {
    "lowercase": True,
    "uppercase": True,
    "numbers": True,
    "special_chars": True
}
```

---

## Troubleshooting

### Issue 1: "Invalid JWT"

**Symptoms**: 401 errors, "Invalid or expired token"

**Solutions**:
```bash
# 1. Verify JWT secret matches
echo $SUPABASE_JWT_SECRET

# 2. Check token expiration
# Tokens expire after 1 hour by default

# 3. Ensure token is properly formatted
# Format: Bearer <token>
```

### Issue 2: Connection Refused

**Symptoms**: Cannot connect to Supabase API

**Solutions**:
```bash
# 1. Verify API URL is correct
curl https://supabase-api.ailabsafrica.com/health

# 2. Check network connectivity
ping supabase-api.ailabsafrica.com

# 3. Verify firewall rules allow port 443
```

### Issue 3: RLS Policy Blocks Access

**Symptoms**: "permission denied for table"

**Solutions**:
```sql
-- 1. Check if RLS is enabled
SELECT tablename, rowsecurity
FROM pg_tables
WHERE schemaname = 'public';

-- 2. Review existing policies
SELECT * FROM pg_policies WHERE tablename = 'your_table';

-- 3. Test policy with specific user
SET ROLE authenticated;
SET request.jwt.claim.sub = 'user-uuid';
SELECT * FROM your_table;
```

### Issue 4: Token Refresh Loop

**Symptoms**: Continuous token refresh requests

**Solutions**:
```typescript
// Ensure autoRefreshToken is configured correctly
const supabase = createClient(url, key, {
  auth: {
    autoRefreshToken: true,
    persistSession: true,
    // Add token refresh threshold
    storage: window.localStorage,
    storageKey: 'supabase.auth.token',
    detectSessionInUrl: true
  }
});
```

---

## Next Steps

1. **Setup Email Templates**: Configure Supabase Studio email templates
2. **Enable OAuth**: Add Google/GitHub OAuth providers
3. **Configure MFA**: Enable multi-factor authentication for admin users
4. **Setup Webhooks**: Create auth event webhooks for user lifecycle events
5. **Monitor Usage**: Set up logging and monitoring for auth events

---

## References

- [Supabase Documentation](https://supabase.com/docs)
- [Supabase Auth Docs](https://supabase.com/docs/guides/auth)
- [JWT Best Practices](https://auth0.com/docs/secure/tokens/json-web-tokens/json-web-token-best-practices)
- [Internal Apps Architecture](./ARCHITECTURE.md)
- [Integration Guide](./INTEGRATION_GUIDE.md)

---

**Last Updated**: 2025-10-24
**Maintained By**: KasaAI Engineering Team
