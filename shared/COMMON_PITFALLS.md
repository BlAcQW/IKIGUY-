# Common Development Pitfalls - Lessons Learned

This document catalogs recurring mistakes and their solutions to prevent future issues.

## Table of Contents
1. [React Hooks Pitfalls](#react-hooks-pitfalls)
2. [WebSocket Connection Issues](#websocket-connection-issues)
3. [Authentication Errors](#authentication-errors)
4. [Build and Deployment](#build-and-deployment)

---

## React Hooks Pitfalls

### 🔴 CRITICAL: useEffect Dependency Hell

**Date:** 2025-11-11
**Severity:** Critical - Causes resource exhaustion

#### The Problem:
```typescript
// ❌ WRONG - Infinite reconnection loop
const connect = useCallback(async () => {
  const ws = new WebSocket(url);
  // ... connection logic
}, [assistantId, onStatusChange, onError, handleWebSocketMessage]);

useEffect(() => {
  connect();
  return cleanup;
}, [connect]); // ← connect function changes on EVERY render
```

**Symptoms:**
- 5-10+ WebSocket connections created per second
- Browser error: "Insufficient resources"
- Backend spawns multiple VAD model instances (10+ GB RAM each)
- Page becomes unresponsive

**Root Cause:**
- `connect` function has callbacks in dependencies
- Callbacks change on every render (new function references)
- `useEffect` sees `connect` changed → runs again
- Creates new connection → causes re-render → repeat

#### The Fix:
```typescript
// ✅ CORRECT - Connect once on mount
useEffect(() => {
  connect();
  return cleanup;
  // eslint-disable-next-line react-hooks/exhaustive-deps
}, []); // Empty array = run once on mount only
```

**Alternative Fix (if you need dependencies):**
```typescript
// Use useRef for callbacks to maintain stable references
const onErrorRef = useRef(onError);
const onStatusChangeRef = useRef(onStatusChange);

useEffect(() => {
  onErrorRef.current = onError;
  onStatusChangeRef.current = onStatusChange;
}, [onError, onStatusChange]);

const connect = useCallback(async () => {
  // Use onErrorRef.current instead of onError
}, []); // Empty array - no dependencies

useEffect(() => {
  connect();
  return cleanup;
}, [connect]); // Now safe - connect never changes
```

**Lesson Learned:**
- **NEVER** put functions with changing dependencies in useEffect deps
- Use empty `[]` for "run once on mount" effects
- Use refs for callbacks that might change
- Always check Chrome DevTools Network tab for multiple connections

---

## WebSocket Connection Issues

### 🟡 Multiple Simultaneous Connections

**Problem:** Creating multiple WebSocket connections to same endpoint

**Common Causes:**
1. Strict Mode in React (mounts/unmounts twice in dev)
2. Component re-renders before cleanup
3. useEffect dependency issues (see above)

**Solution:**
```typescript
// Add connection state check
const connect = useCallback(async () => {
  // Prevent multiple connections
  if (wsRef.current?.readyState === WebSocket.OPEN) {
    console.log('[WS] Already connected');
    return;
  }

  // Clean up any existing connection
  if (wsRef.current) {
    wsRef.current.close();
    wsRef.current = null;
  }

  // Now create new connection
  const ws = new WebSocket(url);
  wsRef.current = ws;
}, []);
```

### 🟡 Forgotten Cleanup

**Problem:** WebSocket connections not closed on unmount

**Solution:**
```typescript
useEffect(() => {
  connect();

  // CRITICAL: Always cleanup
  return () => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    if (wsRef.current) {
      wsRef.current.close(1000, 'Component unmounted');
      wsRef.current = null;
    }
  };
}, []);
```

### 🟡 nginx WebSocket Configuration

**Problem:** WebSocket upgrade failing at reverse proxy

**Required nginx config:**
```nginx
location / {
    proxy_pass http://localhost:30027;

    # WebSocket support
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";

    # Standard headers
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

**Verification:**
```bash
# Check nginx config
cat /etc/nginx/sites-enabled/api.ailabsafrica.com.conf | grep -i "upgrade"

# Test nginx config
sudo nginx -t

# Reload if valid
sudo nginx -s reload
```

---

## Authentication Errors

### 🔴 "Invalid email or password" - No Debugging Info

**Date:** 2025-11-11
**Problem:** Backend returns 401 but doesn't log WHY login failed

**Original Code (NO LOGGING):**
```python
user_doc = await self.users_collection.find_one({"email": email.lower()})
if not user_doc:
    raise HTTPException(status_code=401, detail="Invalid email or password")

if not verify_password(password, user.password_hash):
    raise HTTPException(status_code=401, detail="Invalid email or password")
```

**Issue:** Impossible to debug why login fails:
- User typo in email?
- Wrong password?
- Account doesn't exist?
- Database connection issue?

**Fixed Code (WITH LOGGING):**
```python
import logging
logger = logging.getLogger(__name__)

user_doc = await self.users_collection.find_one({"email": email.lower()})
if not user_doc:
    # Log for debugging (don't reveal to user - prevents enumeration)
    logger.warning(f"Login attempt with non-existent email: {email}")
    raise HTTPException(status_code=401, detail="Invalid email or password")

if not verify_password(password, user.password_hash):
    # Log for debugging
    logger.warning(f"Failed password attempt for user: {email}")
    raise HTTPException(status_code=401, detail="Invalid email or password")
```

**Debugging Commands:**
```bash
# Check recent failed logins
journalctl -u kasaai-core-backend | grep "Login attempt\|Failed password"

# Count failed attempts per email
journalctl -u kasaai-core-backend | grep "Failed password" | \
  awk '{print $NF}' | sort | uniq -c | sort -rn
```

**Security Note:**
- ✅ DO log to backend for admin debugging
- ❌ DON'T reveal to user whether email exists (prevents enumeration attacks)
- ❌ DON'T log actual passwords (even in debug mode)

### 🟡 Email Case Sensitivity

**Problem:** User signs up with `User@Example.com`, tries to log in with `user@example.com`, gets 401

**Root Cause:** Inconsistent email normalization

**Solution:**
```python
# Backend - ALWAYS lowercase emails
email = signin_data.email.lower()
user_doc = await self.users_collection.find_one({"email": email})
```

```typescript
// Frontend - ALSO lowercase before sending
const email = formData.email.toLowerCase();
await mongoAuth.signin({ email, password });
```

### 🟡 Test Accounts Not Working

**Problem:** Can't log in with test accounts after backend restart

**Common Causes:**
1. Database not running: `sudo systemctl status mongod`
2. Wrong MongoDB auth: Check connection string in backend logs
3. Test account never created: Check `db.users.find({email: 'test@example.com'})`

**Quick Fix:**
```bash
# Create test account
curl -X POST https://api.ailabsafrica.com/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test123@kasaai.com",
    "password": "TestPass123",
    "first_name": "Test",
    "last_name": "User"
  }'
```

---

## Build and Deployment

### 🟡 Frontend Not Updating After Changes

**Problem:** Made code changes but browser still shows old behavior

**Common Causes:**
1. Build not run: Need `npm run build` after changes
2. Browser cache: Old JS bundle cached
3. Service worker: Old version cached

**Solution:**
```bash
# 1. Build new version
cd /opt/kasaai/apps/b2c-portal
npm run build

# 2. Hard refresh in browser
# Chrome: Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)
# Firefox: Ctrl+F5 (Windows) or Cmd+Shift+R (Mac)

# 3. Or clear all cache
# Chrome DevTools → Network → Disable cache (checkbox)
# Or: Settings → Clear browsing data → Cached images and files
```

### 🟡 Backend Changes Not Applied

**Problem:** Updated Python code but backend still uses old version

**Solution:**
```bash
# Restart backend service
sudo systemctl restart kasaai-core-backend

# Verify it's running
sudo systemctl status kasaai-core-backend

# Check logs for errors
journalctl -u kasaai-core-backend -f
```

---

## Checklist: Before Reporting "It Doesn't Work"

Before escalating an issue, verify:

### Frontend Issues:
- [ ] Hard refresh browser (Ctrl+Shift+R)
- [ ] Clear browser cache completely
- [ ] Check browser console for errors (F12 → Console)
- [ ] Check Network tab for failed requests
- [ ] Verify API URL in `.env` is correct
- [ ] Run `npm run build` after code changes
- [ ] Check localStorage has valid tokens

### Backend Issues:
- [ ] Backend service is running: `systemctl status kasaai-core-backend`
- [ ] Check backend logs: `journalctl -u kasaai-core-backend -f`
- [ ] MongoDB is running: `systemctl status mongod`
- [ ] Test endpoint with curl directly
- [ ] Restart backend after code changes
- [ ] Check nginx config: `sudo nginx -t`

### Database Issues:
- [ ] Can connect to MongoDB: `mongosh 'mongodb://...'`
- [ ] User exists: `db.users.find({email: 'user@example.com'})`
- [ ] User is active: Check `is_active: true`
- [ ] Organization exists: `db.organizations.find({})`

### Network Issues:
- [ ] Can reach backend: `curl https://api.ailabsafrica.com/auth/health`
- [ ] CORS headers present: Check response headers
- [ ] WebSocket upgrade supported: Check nginx config
- [ ] No firewall blocking: Check ports 443, 80, 30027

---

## Prevention Strategies

### Code Review Checklist:

**React Hooks:**
- [ ] useEffect dependencies are stable or empty
- [ ] useCallback used for functions in dependencies
- [ ] Cleanup functions always provided
- [ ] No infinite loops possible

**WebSocket:**
- [ ] Connection check before creating new WS
- [ ] Cleanup on unmount
- [ ] No multiple simultaneous connections
- [ ] Proper error handling and reconnection logic

**Authentication:**
- [ ] Detailed logging for debugging
- [ ] Generic error messages to users
- [ ] Email normalization (lowercase)
- [ ] Password strength validation
- [ ] No sensitive data in logs

**Testing:**
- [ ] Test in clean browser session
- [ ] Test with multiple accounts
- [ ] Test rapid reconnections
- [ ] Test error scenarios
- [ ] Check logs for errors

---

## Quick Reference

### Restart Everything:
```bash
# Backend
sudo systemctl restart kasaai-core-backend

# nginx
sudo systemctl reload nginx

# MongoDB (if needed)
sudo systemctl restart mongod
```

### Check Everything:
```bash
# Services status
systemctl status kasaai-core-backend mongod nginx

# Recent errors
journalctl -u kasaai-core-backend --since "10 minutes ago" | grep -i error

# Active connections
ss -tlnp | grep 30027

# MongoDB health
mongosh --eval "db.adminCommand('ping')"
```

### Test Everything:
```bash
# Auth health
curl https://api.ailabsafrica.com/auth/health

# Create test user
curl -X POST https://api.ailabsafrica.com/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"TestPass123","first_name":"Test","last_name":"User"}'

# Test login
curl -X POST https://api.ailabsafrica.com/auth/signin \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"TestPass123"}'
```

---

## Resources

- **Full Auth Troubleshooting:** `/opt/kasaai/apps/shared/AUTH_TROUBLESHOOTING.md`
- **Backend Logs:** `journalctl -u kasaai-core-backend -f`
- **nginx Config:** `/etc/nginx/sites-enabled/api.ailabsafrica.com.conf`
- **MongoDB:** `mongosh 'mongodb://admin:aawwER4444%25@127.0.0.1:27017/kasaai_core?authSource=admin'`

---

**Last Updated:** 2025-11-11
**Maintainer:** Development Team
**Version:** 1.0

**Remember:** Every bug is a lesson. Document it here so we never make the same mistake twice!
