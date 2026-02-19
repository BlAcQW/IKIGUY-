# StudyFlow - Supabase Authentication Setup

**Date:** 2025-10-24
**Status:** Configuration Documented

---

## Current Supabase Infrastructure

### Local Supabase Instance (`/opt/supabase`)

**Status:** ❌ **Not Recommended for MVP** (Auth service has connectivity issues)

**Configuration:**
- Docker Compose setup with all Supabase services
- PostgreSQL: `localhost:54322` (database: `community`)
- Kong API Gateway: `localhost:8090`
- Studio UI: `localhost:3003`
- Nginx Proxy: `https://supabase.ailabsafrica.com`

**Issues Found:**
- Auth service can't connect to database (connection timeouts)
- Requires Docker restart and configuration fixes
- pgvector extension has permission issues

**Log Error:**
```
{"level":"fatal","msg":"running db migrations: Migrator: problem creating schema migrations:
couldn't start a new transaction: could not create new transaction:
failed to connect to `host=db user=supabase_auth_admin database=community`:
dial error (timeout: dial tcp 172.20.0.4:5432: connect: connection timed out)"}
```

---

### External Supabase Instance (Cloud)

**Status:** ✅ **Recommended for MVP** (Already in use by other apps)

**Configuration:**
- **Project ID:** `ljzbzjgvwzivpmlmuxhx`
- **URL:** `https://ljzbzjgvwzivpmlmuxhx.supabase.co`
- **Anon Key:** (stored in `.env`)
- **Service Role Key:** (stored in `.env`)

**Apps Currently Using This:**
- `@apps/core_backend` - Main API
- `@apps/b2c-portal` - Frontend portal
- Other KasaAI apps

**Advantages:**
- ✅ Already working and tested
- ✅ Includes pgvector by default
- ✅ Managed by Supabase (no maintenance needed)
- ✅ Auto-backups and high availability
- ✅ Free tier: 500MB database, 1GB file storage, 50MB bandwidth

---

## Recommendation for StudyFlow MVP

### Use External Supabase Instance

**Rationale:**
1. **Working Now:** No time wasted debugging local setup
2. **Proven:** Already used by core_backend and b2c-portal
3. **pgvector Ready:** Includes vector extension out of the box
4. **Production-Ready:** Managed, backed up, monitored
5. **Free Tier:** Sufficient for pilot (500-1000 students)

**Later Migration Path:**
- After MVP success, migrate to local Supabase
- Or use external Supabase long-term (cost scales with usage)

---

## StudyFlow Configuration

### Environment Variables (.env)

Create `/opt/kasaai/apps/studyflow/backend/.env`:

```bash
# ============================================
# Supabase Configuration (External Instance)
# ============================================
SUPABASE_URL=https://ljzbzjgvwzivpmlmuxhx.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxqemJ6amd2d3ppdnBtbG11eGh4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTQwMzQ4OTgsImV4cCI6MjA2OTYxMDg5OH0.Y8IhixS7geKsWVnJwf0qC2vHYBwHA3dRQAzy8nc9QCw
SUPABASE_SERVICE_ROLE_KEY=<get-from-core_backend/.env>

# PostgreSQL (pgvector) - Supabase connection
POSTGRES_HOST=db.ljzbzjgvwzivpmlmuxhx.supabase.co
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=<get-from-supabase-dashboard>
POSTGRES_DB=postgres

# MongoDB (main database)
MONGODB_URL=mongodb://localhost:27017/studyflow
MONGODB_DB_NAME=studyflow

# JWT Secret (from Supabase)
SUPABASE_JWT_SECRET=<get-from-supabase-dashboard>

# AI APIs (from existing KasaAI setup)
GOOGLE_API_KEY=<get-from-core_backend/.env>
OPENAI_API_KEY=<get-from-core_backend/.env>
ANTHROPIC_API_KEY=<get-from-core_backend/.env>

# Payment Gateways
PAYSTACK_SECRET_KEY=<get-from-core_backend/.env>
PAYSTACK_PUBLIC_KEY=<get-from-core_backend/.env>

# n8n Automation
N8N_URL=<get-from-core_backend/.env>
N8N_API_KEY=<get-from-core_backend/.env>

# Application
APP_NAME=StudyFlow
APP_ENV=development
API_URL=http://localhost:8000
```

---

## Backend Integration Code

### 1. Setup Supabase Client

Create `/opt/kasaai/apps/studyflow/backend/app/core/supabase.py`:

```python
"""
Supabase client configuration for StudyFlow.
"""
from supabase import create_client, Client
from app.core.config import settings

# Initialize Supabase client
supabase: Client = create_client(
    settings.SUPABASE_URL,
    settings.SUPABASE_ANON_KEY
)

# For admin operations (server-side only)
supabase_admin: Client = create_client(
    settings.SUPABASE_URL,
    settings.SUPABASE_SERVICE_ROLE_KEY
)
```

---

### 2. Authentication Middleware

Create `/opt/kasaai/apps/studyflow/backend/app/core/auth.py`:

```python
"""
Authentication middleware using Supabase JWT.
"""
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthCredentials
from supabase import Client
from app.core.supabase import supabase
from typing import Optional
import jwt

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthCredentials = Depends(security)
) -> dict:
    """
    Verify JWT token and return current user.

    Args:
        credentials: HTTP Bearer credentials (JWT token)

    Returns:
        dict: User data from Supabase

    Raises:
        HTTPException: If token is invalid or user not found
    """
    token = credentials.credentials

    try:
        # Verify JWT with Supabase
        user = supabase.auth.get_user(token)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )

        return user.user

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication: {str(e)}"
        )


async def get_optional_user(
    credentials: Optional[HTTPAuthCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[dict]:
    """
    Get current user if authenticated, otherwise return None.

    Args:
        credentials: HTTP Bearer credentials (JWT token), optional

    Returns:
        dict or None: User data if authenticated, None otherwise
    """
    if not credentials:
        return None

    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None


async def require_role(user: dict = Depends(get_current_user), required_role: str = "student"):
    """
    Verify user has required role.

    Args:
        user: Current authenticated user
        required_role: Role required to access endpoint

    Raises:
        HTTPException: If user doesn't have required role
    """
    user_role = user.get("user_metadata", {}).get("role", "student")

    if user_role != required_role and user_role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied. Required role: {required_role}"
        )

    return user
```

---

### 3. Example Auth Endpoints

Create `/opt/kasaai/apps/studyflow/backend/app/api/routes/auth.py`:

```python
"""
Authentication routes for StudyFlow.
"""
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, EmailStr
from app.core.supabase import supabase, supabase_admin
from app.core.auth import get_current_user
from typing import Optional

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


class RegisterRequest(BaseModel):
    """User registration request."""
    email: EmailStr
    password: str
    name: str
    role: str = "student"  # student, parent, teacher, admin
    phone: Optional[str] = None


class LoginRequest(BaseModel):
    """User login request."""
    email: EmailStr
    password: str


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest):
    """
    Register new user.

    Creates user in Supabase Auth and stores profile in MongoDB.
    """
    try:
        # Create user in Supabase Auth
        auth_response = supabase_admin.auth.admin.create_user({
            "email": request.email,
            "password": request.password,
            "email_confirm": True,  # Auto-confirm for MVP
            "user_metadata": {
                "name": request.name,
                "role": request.role,
                "phone": request.phone
            }
        })

        user = auth_response.user

        # TODO: Create user profile in MongoDB
        # await create_user_profile(user.id, request)

        return {
            "success": True,
            "message": "User registered successfully",
            "user_id": user.id,
            "email": user.email
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Registration failed: {str(e)}"
        )


@router.post("/login")
async def login(request: LoginRequest):
    """
    Login user with email and password.

    Returns JWT token for subsequent requests.
    """
    try:
        # Sign in with Supabase
        auth_response = supabase.auth.sign_in_with_password({
            "email": request.email,
            "password": request.password
        })

        return {
            "success": True,
            "access_token": auth_response.session.access_token,
            "refresh_token": auth_response.session.refresh_token,
            "user": {
                "id": auth_response.user.id,
                "email": auth_response.user.email,
                "role": auth_response.user.user_metadata.get("role", "student")
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )


@router.post("/logout")
async def logout(user: dict = Depends(get_current_user)):
    """
    Logout current user.
    """
    try:
        # Sign out from Supabase
        supabase.auth.sign_out()

        return {
            "success": True,
            "message": "Logged out successfully"
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Logout failed: {str(e)}"
        )


@router.get("/me")
async def get_me(user: dict = Depends(get_current_user)):
    """
    Get current user profile.
    """
    return {
        "id": user.id,
        "email": user.email,
        "role": user.user_metadata.get("role", "student"),
        "name": user.user_metadata.get("name"),
        "phone": user.user_metadata.get("phone")
    }
```

---

## Database Setup for StudyFlow

### Supabase PostgreSQL (pgvector)

**Purpose:** Store RAG embeddings and vector search

**Setup:**

1. Access Supabase Studio: https://ljzbzjgvwzivpmlmuxhx.supabase.co
2. Enable pgvector extension (should be enabled by default)
3. Create tables for RAG:

```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create collection for study materials
CREATE TABLE IF NOT EXISTS studyflow_knowledge_base (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    collection_name TEXT NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    embedding vector(1536),  -- OpenAI embedding dimension
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for vector search
CREATE INDEX IF NOT EXISTS studyflow_knowledge_base_embedding_idx
ON studyflow_knowledge_base
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Create index for collection filtering
CREATE INDEX IF NOT EXISTS studyflow_knowledge_base_collection_idx
ON studyflow_knowledge_base(collection_name);

-- Create index for metadata filtering
CREATE INDEX IF NOT EXISTS studyflow_knowledge_base_metadata_idx
ON studyflow_knowledge_base USING gin(metadata);
```

---

### MongoDB (Primary Database)

**Purpose:** Store users, sessions, exercises, progress, wallet transactions

**Database:** `studyflow`

**Collections:**
- `users` - All user accounts (students, parents, teachers, admins)
- `students` - Student-specific data
- `parents` - Parent-specific data (linked to students)
- `teachers` - Teacher-specific data
- `schools` - School/organization data
- `classes` - Class/grade information
- `study_materials` - Uploaded materials metadata
- `tutoring_sessions` - Q&A sessions and conversation history
- `exercises` - Practice exercises
- `student_progress` - Learning analytics
- `progress_reports` - Weekly reports
- `wallet_transactions` - Payment history
- `notifications` - In-app notifications

**Setup:**

```bash
# Connect to MongoDB
mongo

# Create database and collections
use studyflow

# Create users collection with indexes
db.users.createIndex({ "email": 1 }, { unique: true })
db.users.createIndex({ "supabase_id": 1 }, { unique: true })
db.users.createIndex({ "role": 1 })

# Create students collection
db.students.createIndex({ "user_id": 1 }, { unique: true })
db.students.createIndex({ "parent_id": 1 })
db.students.createIndex({ "school_id": 1 })

# Create materials collection
db.study_materials.createIndex({ "school_id": 1, "subject": 1 })
db.study_materials.createIndex({ "grade": 1, "subject": 1 })

# Create sessions collection
db.tutoring_sessions.createIndex({ "student_id": 1, "created_at": -1 })
db.tutoring_sessions.createIndex({ "subject": 1 })

# Create exercises collection
db.exercises.createIndex({ "student_id": 1, "created_at": -1 })
db.exercises.createIndex({ "subject": 1, "topic": 1 })

# Create wallet transactions
db.wallet_transactions.createIndex({ "wallet_id": 1, "created_at": -1 })
db.wallet_transactions.createIndex({ "status": 1 })
```

---

## Testing Authentication

### 1. Register Test User

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "student@test.com",
    "password": "testpass123",
    "name": "Test Student",
    "role": "student",
    "phone": "+233244000000"
  }'
```

### 2. Login

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "student@test.com",
    "password": "testpass123"
  }'
```

**Response:**
```json
{
  "success": true,
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "...",
  "user": {
    "id": "uuid",
    "email": "student@test.com",
    "role": "student"
  }
}
```

### 3. Access Protected Endpoint

```bash
curl -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer <access_token>"
```

---

## Frontend Integration (React Native)

### 1. Install Supabase Client

```bash
cd /opt/kasaai/apps/studyflow/mobile
npm install @supabase/supabase-js
```

### 2. Create Supabase Client

Create `mobile/src/lib/supabase.ts`:

```typescript
import { createClient } from '@supabase/supabase-js'
import AsyncStorage from '@react-native-async-storage/async-storage'

const supabaseUrl = process.env.EXPO_PUBLIC_SUPABASE_URL!
const supabaseAnonKey = process.env.EXPO_PUBLIC_SUPABASE_ANON_KEY!

export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    storage: AsyncStorage,
    autoRefreshToken: true,
    persistSession: true,
    detectSessionInUrl: false,
  },
})
```

### 3. Auth Context

Create `mobile/src/context/AuthContext.tsx`:

```typescript
import React, { createContext, useState, useEffect, useContext } from 'react'
import { supabase } from '@/lib/supabase'
import { User } from '@supabase/supabase-js'

interface AuthContextType {
  user: User | null
  loading: boolean
  signIn: (email: string, password: string) => Promise<void>
  signUp: (email: string, password: string, name: string, role: string) => Promise<void>
  signOut: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Check active session
    supabase.auth.getSession().then(({ data: { session } }) => {
      setUser(session?.user ?? null)
      setLoading(false)
    })

    // Listen for auth changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user ?? null)
    })

    return () => subscription.unsubscribe()
  }, [])

  const signIn = async (email: string, password: string) => {
    const { error } = await supabase.auth.signInWithPassword({ email, password })
    if (error) throw error
  }

  const signUp = async (email: string, password: string, name: string, role: string) => {
    const { error } = await supabase.auth.signUp({
      email,
      password,
      options: {
        data: {
          name,
          role,
        },
      },
    })
    if (error) throw error
  }

  const signOut = async () => {
    const { error } = await supabase.auth.signOut()
    if (error) throw error
  }

  return (
    <AuthContext.Provider value={{ user, loading, signIn, signUp, signOut }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
```

---

## Migration Path (Local Supabase - Future)

### If We Want to Use Local Supabase Later:

1. **Fix Docker Network Issues:**
   ```bash
   cd /opt/supabase
   docker-compose down
   docker-compose up -d
   ```

2. **Setup Auth Schema:**
   ```sql
   -- Create auth user
   CREATE USER supabase_auth_admin WITH PASSWORD 'aawwER44444';
   GRANT ALL PRIVILEGES ON DATABASE community TO supabase_auth_admin;
   ```

3. **Install pgvector as Superuser:**
   ```bash
   docker exec -it supabase-db-1 psql -U postgres -d community -c "CREATE EXTENSION vector;"
   ```

4. **Update Environment Variables:**
   ```bash
   SUPABASE_URL=http://localhost:8090
   SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0
   ```

---

## Summary

### ✅ For MVP: Use External Supabase

**Configuration:**
- URL: `https://ljzbzjgvwzivpmlmuxhx.supabase.co`
- Already working with other KasaAI apps
- Includes pgvector by default
- Free tier sufficient for pilot

**Next Steps:**
1. ✅ Copy Supabase keys from `core_backend/.env`
2. Create `studyflow/backend/.env` with configuration
3. Implement auth endpoints (register, login, logout)
4. Test authentication flow
5. Setup MongoDB collections
6. Create pgvector tables for RAG

### 🔄 Later: Migrate to Local Supabase (Optional)

- After MVP success and validation
- Or continue using external instance (scales with usage)
- Local instance requires Docker fixes first

---

**Status:** ✅ Configuration documented, ready to proceed with implementation

**Next:** Create backend project structure and implement authentication
