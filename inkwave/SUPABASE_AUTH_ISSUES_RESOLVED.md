# Supabase Authentication Issues - Complete Resolution Log

**Date**: November 24, 2025
**Server**: Dev Server (85.214.12.174)
**Application**: InkWave
**Issue**: Users immediately logged out after login attempts

---

## Root Causes Identified

### 1. **File Permission Errors**
**Symptom**: Backend service failing to start/reload with permission denied errors

**Files Affected**:
- `/opt/kasaai/apps/inkwave/backend/app/api/routes/payments.py` (root-only: 600)
- `/opt/kasaai/apps/inkwave/backend/app/services/payment_service.py` (root-only: 600)
- `/opt/kasaai/apps/shared/services/expresspay_service.py` (root-only: 600)

**Root Cause**: Files created by root with restrictive permissions, but service runs as user `dev`

**Error Messages**:
```
PermissionError: [Errno 13] Permission denied: '/opt/kasaai/apps/inkwave/backend/app/api/routes/payments.py'
```

**Solution Applied**:
```bash
sudo chown -R dev:www-data /opt/kasaai/apps/inkwave/backend/
sudo chown -R dev:www-data /opt/kasaai/apps/shared/
sudo chmod -R 755 /opt/kasaai/apps/inkwave/backend/
sudo chmod -R 755 /opt/kasaai/apps/shared/
find /opt/kasaai/apps/inkwave/backend -type d -name "__pycache__" -exec sudo rm -rf {} +
find /opt/kasaai/apps/shared -type d -name "__pycache__" -exec sudo rm -rf {} +
```

---

### 2. **Nginx Proxy Misconfiguration**
**Symptom**: 502 Bad Gateway when accessing Supabase endpoints

**Root Cause**: Nginx pointing to wrong port
- **Expected**: Port 54321 (where simple_api.py runs)
- **Configured**: Port 8090 (non-existent service)

**Configuration File**: `/etc/nginx/sites-available/supabase.ailabsafrica.com.conf`

**Error Behavior**: All `/auth/v1/*` requests returned 502 Bad Gateway

**Solution Applied**:
```bash
sudo sed -i 's/localhost:8090/localhost:54321/g' /etc/nginx/sites-available/supabase.ailabsafrica.com.conf
sudo nginx -t
sudo systemctl reload nginx
```

**Fixed Section**:
```nginx
location / {
    proxy_pass http://localhost:54321;  # Changed from 8090
    proxy_http_version 1.1;
    # ... rest of config
}
```

---

### 3. **Missing Supabase Auth Endpoints**
**Symptom**: Login works but users immediately logged out; token verification fails

**Root Cause**: The simple_api.py only implemented REST endpoints, not GoTrue auth endpoints

**Missing Endpoints**:
- `POST /auth/v1/signup` - User registration
- `POST /auth/v1/token` - User login
- `GET /auth/v1/user` - Token verification (critical for session persistence)
- `POST /auth/v1/admin/users` - Admin user creation

**Backend Expected Flow**:
```python
# InkWave backend at app/core/auth.py:62
response = supabase.auth.get_user(token)  # This was failing!
if not response.user:
    raise HTTPException(401, "Invalid or expired token")
```

**Why Users Were Logged Out**:
1. User logs in → receives JWT token
2. Frontend stores token
3. Frontend makes authenticated request with token
4. Backend calls `supabase.auth.get_user(token)` to verify
5. **Supabase returns 404** (endpoint doesn't exist)
6. Backend returns 401 Unauthorized
7. Frontend detects 401 → logs user out automatically

---

### 4. **PostgreSQL Authentication Issues**
**Symptom**: Auth endpoints returning database connection errors

**Root Cause**: Incorrect/missing PostgreSQL password in simple_api.py

**Error Messages**:
```
connection to server at "localhost" (127.0.0.1), port 5432 failed:
fe_sendauth: no password supplied
password authentication failed for user "postgres"
```

**Attempted Values**:
- Empty string: `''` ❌
- Wrong password: `'aawwER44444'` (5 fours) ❌
- **Correct**: `'aawwER444444'` (6 fours) ✅

**Solution**:
```python
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'postgres',
    'user': 'postgres',
    'password': 'aawwER444444'  # 6 fours, from /opt/kasaai/.env
}
```

---

### 5. **Missing Database Schema and Tables**
**Symptom**: Auth endpoints failing with "relation does not exist"

**Error Message**:
```
relation "auth.users" does not exist
LINE 1: SELECT id FROM auth.users WHERE email = ...
```

**Root Cause**: The auth schema and users table were never created in PostgreSQL

**Solution Applied**:
```bash
sudo -u postgres psql <<'EOF'
CREATE SCHEMA IF NOT EXISTS auth;
CREATE TABLE IF NOT EXISTS auth.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    encrypted_password VARCHAR(255) NOT NULL,
    email_confirmed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    raw_user_meta_data JSONB DEFAULT '{}'::jsonb,
    raw_app_meta_data JSONB DEFAULT '{}'::jsonb
);
EOF
```

---

## Complete Solution

### Created: `/opt/supabase/simple_api_with_auth.py`

A comprehensive Supabase-compatible API with:

1. **Full Auth Endpoints**:
   - `POST /auth/v1/signup` - User registration with auto-confirmed email
   - `POST /auth/v1/token` - Login returning JWT tokens
   - `GET /auth/v1/user` - Token verification (Bearer token in header)
   - `POST /auth/v1/admin/users` - Admin user creation (requires service key)

2. **JWT Token Generation**:
   ```python
   payload = {
       'sub': user_id,
       'email': email,
       'role': 'authenticated',
       'iat': datetime.utcnow(),
       'exp': datetime.utcnow() + timedelta(days=7)
   }
   token = jwt.encode(payload, JWT_SECRET, algorithm='HS256')
   ```

3. **Security**:
   - API key verification for REST endpoints
   - Service key verification for admin endpoints
   - Password hashing with werkzeug
   - JWT token validation with expiration

4. **API Key Handling**:
   - Regular API Key: `A9FUKeENqS1Z6rmENfX8wHkihmd5yHirKFkRIhMgusg=`
   - Service Key: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` (from SUPABASE_SERVICE_KEY)
   - Auth endpoints skip API key check

### Updated: `/opt/supabase/start_api.sh`

```bash
#!/bin/bash
cd /opt/supabase
source venv/bin/activate
python3 simple_api_with_auth.py  # Changed from simple_api.py
```

---

## Verification Tests

### 1. Test Signup
```bash
curl -X POST http://localhost:54321/auth/v1/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"TestPass123!"}'
```

**Expected Response**:
```json
{
  "access_token": "eyJhbGci...",
  "token_type": "bearer",
  "expires_in": 604800,
  "user": {
    "id": "uuid-here",
    "email": "test@example.com",
    "created_at": "2025-11-24T..."
  }
}
```

### 2. Test Login
```bash
curl -X POST http://localhost:54321/auth/v1/token \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"TestPass123!"}'
```

### 3. Test Token Verification (Most Critical!)
```bash
TOKEN="eyJhbGci..."  # From login response
curl http://localhost:54321/auth/v1/user \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response**:
```json
{
  "id": "uuid-here",
  "email": "test@example.com",
  "email_confirmed_at": "2025-11-24T...",
  "created_at": "2025-11-24T...",
  "user_metadata": {}
}
```

If this returns 401 or 404, users will be immediately logged out!

---

## Prevention Checklist

### For Future Deployments:

- [ ] **File Permissions**: Always check ownership and permissions after creating files
  ```bash
  ls -la /opt/kasaai/apps/*/backend/app/**/*.py
  # Should be: -rwxr-xr-x dev www-data
  ```

- [ ] **Service Logs**: Check for permission errors before declaring service "running"
  ```bash
  sudo journalctl -u inkwave-backend.service -n 50 --no-pager | grep -i "error\|permission"
  ```

- [ ] **Nginx Port Mapping**: Verify proxy_pass points to correct port
  ```bash
  grep "proxy_pass" /etc/nginx/sites-available/supabase.ailabsafrica.com.conf
  # Should show: http://localhost:54321
  ```

- [ ] **Database Connectivity**: Test DB connection before starting auth service
  ```bash
  sudo -u postgres psql -c "SELECT 1"
  PGPASSWORD='aawwER444444' psql -h localhost -U postgres -d postgres -c "SELECT 1"
  ```

- [ ] **Auth Tables Exist**: Verify schema and tables
  ```bash
  sudo -u postgres psql -c "\dt auth.*"
  ```

- [ ] **Test Critical Auth Flow**:
  1. Signup creates user ✅
  2. Login returns valid token ✅
  3. Token verification succeeds ✅ **MOST IMPORTANT**
  4. Backend accepts token ✅

- [ ] **Clean Cache After Permission Fixes**:
  ```bash
  find /opt/kasaai/apps -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
  ```

---

## Common Error Patterns & Solutions

### Pattern 1: "502 Bad Gateway" on auth endpoints
**Check**:
1. Is Supabase API running? `sudo systemctl status supabase-api`
2. Is it on the right port? `sudo lsof -i :54321`
3. Does nginx proxy to right port? `grep proxy_pass /etc/nginx/sites-available/supabase*`

### Pattern 2: Users logged out immediately after login
**Check**:
1. Does `/auth/v1/user` endpoint exist and work?
   ```bash
   curl http://localhost:54321/auth/v1/user -H "Authorization: Bearer <token>"
   ```
2. Backend auth validation at `app/core/auth.py:62` - does `get_user()` succeed?

### Pattern 3: Permission denied errors
**Check**:
1. File ownership: `ls -la <file>` should show `dev www-data`, not `root root`
2. Service user: `grep "User=" /etc/systemd/system/inkwave-backend.service`
3. Clean pycache and restart

### Pattern 4: Database connection errors
**Check**:
1. Password matches `.env` file
2. Database exists: `sudo -u postgres psql -l | grep postgres`
3. Auth schema exists: `sudo -u postgres psql -c "\dn auth"`

---

## Service Dependencies

InkWave login requires ALL of these to work:

1. ✅ **PostgreSQL** (port 5432)
   - auth.users table must exist
   - Password must be correct

2. ✅ **Supabase API** (port 54321)
   - simple_api_with_auth.py must be running
   - Auth endpoints must respond

3. ✅ **Nginx**
   - Must proxy supabase.ailabsafrica.com → localhost:54321
   - SSL certificates valid

4. ✅ **InkWave Backend** (port 8001)
   - No permission errors
   - Can connect to MongoDB
   - Can verify tokens with Supabase

5. ✅ **File Permissions**
   - All Python files readable by `dev` user
   - No root-only files in service paths

---

## Key Files Modified

| File | Purpose | Change |
|------|---------|--------|
| `/opt/supabase/simple_api_with_auth.py` | New auth API | Added full GoTrue-compatible endpoints |
| `/opt/supabase/start_api.sh` | Service startup | Changed to use new API file |
| `/etc/nginx/sites-available/supabase.ailabsafrica.com.conf` | Nginx proxy | Port 8090 → 54321 |
| `/opt/kasaai/apps/inkwave/backend/app/**/*.py` | Backend files | Fixed ownership to dev:www-data |
| `/opt/kasaai/apps/shared/**/*.py` | Shared services | Fixed ownership to dev:www-data |
| PostgreSQL `auth` schema | Database | Created schema and users table |

---

## Restart Sequence (If Needed)

**Correct order to restart services**:

```bash
# 1. PostgreSQL (if auth tables were modified)
sudo systemctl restart postgresql
sleep 2

# 2. Supabase API (simple_api_with_auth.py)
sudo systemctl restart supabase-api.service
sleep 3

# 3. Nginx (if config changed)
sudo nginx -t && sudo systemctl reload nginx
sleep 2

# 4. InkWave Backend (if files changed)
sudo systemctl restart inkwave-backend.service
sleep 5

# 5. Verify all services
sudo systemctl status supabase-api --no-pager | head -20
sudo systemctl status inkwave-backend --no-pager | head -20
curl -s http://localhost:54321/health
curl -s http://localhost:8001/health
```

**NEVER restart the full server** - only restart individual services as needed.

---

## Monitoring Commands

**Check if login is working**:
```bash
# 1. Check Supabase API health
curl -s http://localhost:54321/health | jq .

# 2. Check InkWave backend health
curl -s http://localhost:8001/health | jq .

# 3. Test complete auth flow
TOKEN=$(curl -s -X POST http://localhost:54321/auth/v1/token \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"TestPass123!"}' | jq -r .access_token)

curl -s http://localhost:54321/auth/v1/user \
  -H "Authorization: Bearer $TOKEN" | jq .

# If this returns user data, auth is working ✅
# If this returns 401/404, users will be logged out ❌
```

**Check service logs**:
```bash
# InkWave backend errors
sudo journalctl -u inkwave-backend.service -n 50 --no-pager | grep -E "error|Error|ERROR|401|permission"

# Supabase API errors
sudo journalctl -u supabase-api.service -n 50 --no-pager | grep -E "error|Error|ERROR"
```

---

## Summary

**Total Issues Found**: 5
**Total Files Modified**: 8
**Services Restarted**: 2 (supabase-api, inkwave-backend)
**System Reboots Required**: 0

**Key Lesson**: The "immediate logout" issue was caused by missing token verification endpoint (`/auth/v1/user`). Even if login succeeds, without proper token verification, the backend will reject all authenticated requests, causing the frontend to log users out.

**Status**: ✅ **RESOLVED** - All auth endpoints working, token verification operational, users can login and stay logged in.
