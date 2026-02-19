# Authentication Troubleshooting Guide

## Common Auth Errors and Solutions

### ❌ Error: "Invalid email or password" (401 Unauthorized)

This error occurs when:

1. **User doesn't exist in database**
   - Check: `mongosh 'mongodb://admin:aawwER4444%25@127.0.0.1:27017/kasaai_core?authSource=admin' --eval "db.users.find({email: 'user@example.com'}).toArray()"`
   - Solution: Create account via `/auth/signup` endpoint first

2. **Wrong password**
   - Check backend logs: `journalctl -u kasaai-core-backend | grep "Failed password attempt"`
   - Solution: Use correct password or reset (not yet implemented)

3. **Email case mismatch**
   - Backend stores emails in lowercase: `signin_data.email.lower()`
   - Frontend should also lowercase emails before sending
   - Check: Make sure frontend lowercases email in login form

4. **Account is inactive**
   - Check: `db.users.find({email: 'user@example.com'}, {is_active: 1})`
   - Solution: Set `is_active: true` in database

### ❌ Error: "WebSocket connection failed: Insufficient resources"

**Root Cause:** Multiple WebSocket connections created rapidly due to React hook dependency issues

**Symptoms:**
- 5-10+ WebSocket connections within seconds
- Browser console shows "Insufficient resources"
- Backend logs show multiple "connection open" for same assistant
- Each connection loads VAD model (resource intensive)

**Fix:**
```typescript
// ❌ WRONG - causes infinite reconnections
useEffect(() => {
  connect();
  return cleanup;
}, [connect]); // connect function changes frequently

// ✅ CORRECT - connects once on mount
useEffect(() => {
  connect();
  return cleanup;
  // eslint-disable-next-line react-hooks/exhaustive-deps
}, []); // Empty dependency array
```

**Prevention:**
- Always use empty dependency array `[]` for connection effects
- Use `useCallback` with stable dependencies for connection functions
- Add connection state checks before creating new connections

### ❌ Error: "Network request failed" / CORS errors

**Symptoms:**
- Request blocked by CORS policy
- `Access-Control-Allow-Origin` errors in console

**Check nginx configuration:**
```bash
cat /etc/nginx/sites-enabled/api.ailabsafrica.com.conf | grep -A 10 "CORS"
```

**Required CORS headers:**
```nginx
add_header 'Access-Control-Allow-Origin' '$cors_origin' always;
add_header 'Access-Control-Allow-Credentials' 'true' always;
add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, OPTIONS, PATCH' always;
add_header 'Access-Control-Allow-Headers' 'Content-Type, Authorization, Accept, Origin, X-Requested-With, X-Service-Token, X-Organization-ID' always;
```

**WebSocket CORS:**
```nginx
proxy_set_header Upgrade $http_upgrade;
proxy_set_header Connection "upgrade";
```

## Backend Auth Debugging

### Enable Detailed Logging

Auth service now logs failed login attempts:

```python
# Location: /opt/kasaai/apps/core_backend/backend/services/auth_service.py

# Non-existent email
logger.warning(f"Login attempt with non-existent email: {email}")

# Wrong password
logger.warning(f"Failed password attempt for user: {email}")
```

### Check Logs:
```bash
# Real-time auth logs
journalctl -u kasaai-core-backend -f | grep -i "auth\|login\|password"

# Recent auth failures
journalctl -u kasaai-core-backend --since "10 minutes ago" | grep -i "401\|failed password\|non-existent email"
```

### Test Endpoints Directly:

```bash
# Test signup
curl -X POST https://api.ailabsafrica.com/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPass123",
    "first_name": "Test",
    "last_name": "User",
    "organization_name": "Test Org"
  }'

# Test signin
curl -X POST https://api.ailabsafrica.com/auth/signin \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPass123",
    "remember_me": false
  }'

# Test health
curl https://api.ailabsafrica.com/auth/health
```

## Frontend Auth Debugging

### Check Browser Storage:
```javascript
// Check localStorage for tokens
localStorage.getItem('mongo_access_token')
localStorage.getItem('mongo_refresh_token')
localStorage.getItem('mongo_user')
localStorage.getItem('mongo_organization')

// Clear auth state
localStorage.removeItem('mongo_access_token')
localStorage.removeItem('mongo_refresh_token')
localStorage.removeItem('mongo_user')
localStorage.removeItem('mongo_organization')
```

### Check Network Requests:
1. Open DevTools → Network tab
2. Filter by "signin" or "auth"
3. Check request payload:
   - Is email correct?
   - Is password sent?
   - Is `remember_me` field present?
4. Check response:
   - Status code (200 = success, 401 = failed auth)
   - Response body (contains error message)

### Common Frontend Issues:

1. **Old build cached**
   - Solution: Hard refresh (Ctrl+Shift+R or Cmd+Shift+R)
   - Or: Clear browser cache completely

2. **Wrong API URL**
   - Check: `.env` file has `VITE_CORE_API_URL=https://api.ailabsafrica.com`
   - Check: `src/config/api-config.ts` uses correct URL

3. **Token expired**
   - Access tokens expire after 24 hours
   - Refresh tokens expire after 30 days
   - Solution: Re-login to get new tokens

## Database Checks

### Find user by email:
```javascript
use kasaai_core
db.users.find({email: "user@example.com"}).pretty()
```

### Check user's organization:
```javascript
db.organization_users.find({
  user_id: "user-id-here"
}).pretty()
```

### Check active sessions:
```javascript
db.user_sessions.find({
  user_id: "user-id-here",
  is_active: true
}).pretty()
```

### Reset user password (manual):
```javascript
// Generate hash with bcrypt (do this in Python/Node)
// Then update database
db.users.updateOne(
  {email: "user@example.com"},
  {$set: {password_hash: "new-bcrypt-hash-here"}}
)
```

## Password Requirements

Current requirements (enforced by backend):
- Minimum 8 characters
- At least 1 uppercase letter
- At least 1 lowercase letter
- At least 1 number

**Location:** `/opt/kasaai/apps/core_backend/backend/utils/auth.py:validate_password_strength()`

## Test Accounts

**Working test accounts:**

```
Email: test123@kasaai.com
Password: TestPass123
Organization: Test Org 123
```

```
Email: testuser1762861301@example.com
Password: TestPassword123!
```

## Quick Fixes

### Create new test user:
```bash
TIMESTAMP=$(date +%s)
curl -X POST https://api.ailabsafrica.com/auth/signup \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"test${TIMESTAMP}@example.com\",
    \"password\": \"TestPass123\",
    \"first_name\": \"Test\",
    \"last_name\": \"User\",
    \"organization_name\": \"Test Org ${TIMESTAMP}\"
  }"
```

### Check backend is running:
```bash
sudo systemctl status kasaai-core-backend
```

### Restart backend:
```bash
sudo systemctl restart kasaai-core-backend
```

### Check MongoDB is running:
```bash
sudo systemctl status mongod
```

## Common Mistakes to Avoid

### ❌ DON'T:
1. Use `[connect]` in useEffect dependency array for WebSocket hooks
2. Create new WebSocket on every render
3. Forget to clean up WebSocket on unmount
4. Store passwords in plain text
5. Log actual passwords (even in development)
6. Return different error messages for "user not found" vs "wrong password" (security risk)
7. Skip email validation on frontend
8. Allow weak passwords

### ✅ DO:
1. Use empty dependency array `[]` for WebSocket connection effects
2. Clean up connections in useEffect cleanup
3. Always hash passwords with bcrypt
4. Log failed login attempts with email only (for security auditing)
5. Return generic "Invalid email or password" for all auth failures
6. Validate email format on both frontend and backend
7. Enforce strong password requirements
8. Use HTTPS for all auth requests
9. Store JWT tokens securely (HttpOnly cookies preferred over localStorage)
10. Implement rate limiting on auth endpoints

## Security Best Practices

1. **Never log passwords** - even in debug mode
2. **Always use HTTPS** - no exceptions
3. **Use bcrypt for password hashing** - with proper salt rounds (12+)
4. **Implement rate limiting** - prevent brute force attacks
5. **Add email verification** - confirm user owns email (TODO)
6. **Implement 2FA** - add extra security layer (TODO)
7. **Use short-lived access tokens** - currently 24 hours
8. **Rotate refresh tokens** - currently 30 days
9. **Log all auth attempts** - for security auditing
10. **Implement account lockout** - after N failed attempts (TODO)

## Monitoring

### Watch for suspicious activity:
```bash
# Failed login attempts
journalctl -u kasaai-core-backend | grep "Failed password" | tail -20

# Multiple attempts from same email
journalctl -u kasaai-core-backend | grep "Login attempt" | sort | uniq -c | sort -rn

# Check for brute force attacks
journalctl -u kasaai-core-backend --since "1 hour ago" | grep "401 Unauthorized" | wc -l
```

## Contact

For authentication issues that can't be resolved:
1. Check this document first
2. Review backend logs
3. Test endpoints directly with curl
4. Check MongoDB user data
5. Create issue with full error context

Last updated: 2025-11-11
Version: 1.0
