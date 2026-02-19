# Nginx CORS Configuration Guide for KasaAI Applications

**Last Updated**: 2025-11-02
**Author**: KasaAI Development Team

---

## Overview

This document provides standard patterns and best practices for configuring CORS (Cross-Origin Resource Sharing) in nginx for KasaAI applications, with special attention to Supabase authentication integration.

---

## Table of Contents

1. [CORS Basics](#cors-basics)
2. [Standard CORS Headers](#standard-cors-headers)
3. [Supabase-Specific Requirements](#supabase-specific-requirements)
4. [Configuration Patterns](#configuration-patterns)
5. [Common Issues & Solutions](#common-issues--solutions)
6. [Testing CORS Configuration](#testing-cors-configuration)

---

## CORS Basics

CORS is a browser security mechanism that controls which cross-origin requests are allowed. For KasaAI applications where:
- Frontend is at `https://app.ailabsafrica.com`
- Backend is at `https://app-api.ailabsafrica.com`
- Supabase is at `https://supabase-api.ailabsafrica.com`

The browser requires proper CORS headers to allow these cross-origin requests.

### How CORS Works

1. **Preflight Request**: Browser sends OPTIONS request with:
   - `Origin`: The requesting domain
   - `Access-Control-Request-Method`: The actual HTTP method to be used
   - `Access-Control-Request-Headers`: Headers that will be sent

2. **Preflight Response**: Server must respond with:
   - `Access-Control-Allow-Origin`: Allowed origins
   - `Access-Control-Allow-Methods`: Allowed HTTP methods
   - `Access-Control-Allow-Headers`: Allowed request headers
   - HTTP status: 204 (No Content)

3. **Actual Request**: If preflight succeeds, browser sends the actual request

---

## Standard CORS Headers

### Minimum Required Headers

```nginx
add_header Access-Control-Allow-Origin "*" always;
add_header Access-Control-Allow-Methods "GET, POST, PUT, PATCH, DELETE, OPTIONS" always;
add_header Access-Control-Allow-Headers "Authorization, Content-Type, Accept, apikey" always;
```

### Production-Ready Headers

```nginx
# CORS Configuration
add_header Access-Control-Allow-Origin "*" always;
add_header Access-Control-Allow-Methods "GET, POST, PUT, PATCH, DELETE, OPTIONS" always;
add_header Access-Control-Allow-Headers "Authorization, Content-Type, Accept, apikey, X-Client-Info" always;
add_header Access-Control-Expose-Headers "Content-Length, Content-Range" always;

# Handle preflight OPTIONS requests
if ($request_method = 'OPTIONS') {
    return 204;
}
```

**Important**: Use `always` modifier to ensure headers are sent even on error responses (4xx, 5xx).

---

## Supabase-Specific Requirements

### Required Header: x-supabase-api-version

**Supabase JavaScript SDK v2+** sends an `x-supabase-api-version` header with every request. Nginx must allow this header in CORS configuration:

```nginx
add_header Access-Control-Allow-Headers "Authorization, Content-Type, Accept, apikey, X-Client-Info, x-supabase-api-version" always;
```

### Example Error Without This Header

```
Access to fetch at 'https://supabase-api.ailabsafrica.com/auth/v1/token?grant_type=password'
from origin 'https://app.ailabsafrica.com' has been blocked by CORS policy:
Request header field x-supabase-api-version is not allowed by Access-Control-Allow-Headers
in preflight response.
```

### Full Supabase CORS Configuration

```nginx
# Supabase-compatible CORS headers
add_header Access-Control-Allow-Origin "*" always;
add_header Access-Control-Allow-Methods "GET, POST, PUT, PATCH, DELETE, OPTIONS" always;
add_header Access-Control-Allow-Headers "Authorization, Content-Type, Accept, apikey, X-Client-Info, x-supabase-api-version" always;
add_header Access-Control-Expose-Headers "Content-Length, Content-Range" always;

# Handle preflight OPTIONS requests
if ($request_method = 'OPTIONS') {
    return 204;
}
```

---

## Configuration Patterns

### Pattern 1: Direct Application Backend (No Supabase Proxy)

**Use Case**: Applications that connect directly to Supabase from frontend/backend
**Examples**: ERP, StudyFlow, InkWave, EventFlow, ChurchFlow

```nginx
server {
    listen 443 ssl http2;
    server_name app-api.ailabsafrica.com;

    # SSL configuration
    ssl_certificate /etc/letsencrypt/live/app-api.ailabsafrica.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/app-api.ailabsafrica.com/privkey.pem;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "SAMEORIGIN" always;

    # Proxy to application backend
    location / {
        proxy_pass http://127.0.0.1:30030;
        proxy_http_version 1.1;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**Note**: CORS is handled by the application backend (FastAPI, Express, etc.), not nginx.

---

### Pattern 2: Supabase Proxy (Centralized)

**Use Case**: Central nginx proxy for Supabase services (Auth, REST, Realtime, Storage)
**Example**: `supabase-api.ailabsafrica.com` proxying to Kong Gateway

```nginx
server {
    listen 443 ssl http2;
    server_name supabase-api.ailabsafrica.com;

    # SSL configuration
    ssl_certificate /etc/letsencrypt/live/supabase.ailabsafrica.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/supabase.ailabsafrica.com/privkey.pem;

    # CORS headers at server level
    add_header Access-Control-Allow-Origin "*" always;
    add_header Access-Control-Allow-Methods "GET, POST, PUT, PATCH, DELETE, OPTIONS" always;
    add_header Access-Control-Allow-Headers "Authorization, Content-Type, Accept, apikey, X-Client-Info, x-supabase-api-version" always;
    add_header Access-Control-Expose-Headers "Content-Length, Content-Range" always;

    # Handle preflight OPTIONS requests
    if ($request_method = 'OPTIONS') {
        return 204;
    }

    # Generic location block
    location / {
        proxy_pass http://localhost:8000;

        # Hide CORS headers from upstream (Kong) to prevent duplicates
        proxy_hide_header Access-Control-Allow-Origin;
        proxy_hide_header Access-Control-Allow-Methods;
        proxy_hide_header Access-Control-Allow-Headers;
        proxy_hide_header Access-Control-Expose-Headers;
        proxy_hide_header Access-Control-Allow-Credentials;

        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Specific location blocks also need proxy_hide_header
    location /auth/v1/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;

        # Hide CORS headers from Kong to prevent duplicates
        proxy_hide_header Access-Control-Allow-Origin;
        proxy_hide_header Access-Control-Allow-Methods;
        proxy_hide_header Access-Control-Allow-Headers;
        proxy_hide_header Access-Control-Expose-Headers;
        proxy_hide_header Access-Control-Allow-Credentials;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Authorization $http_authorization;
    }

    location /rest/v1/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;

        # Hide CORS headers from Kong to prevent duplicates
        proxy_hide_header Access-Control-Allow-Origin;
        proxy_hide_header Access-Control-Allow-Methods;
        proxy_hide_header Access-Control-Allow-Headers;
        proxy_hide_header Access-Control-Expose-Headers;
        proxy_hide_header Access-Control-Allow-Credentials;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /storage/v1/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;

        # Hide CORS headers from Kong to prevent duplicates
        proxy_hide_header Access-Control-Allow-Origin;
        proxy_hide_header Access-Control-Allow-Methods;
        proxy_hide_header Access-Control-Allow-Headers;
        proxy_hide_header Access-Control-Expose-Headers;
        proxy_hide_header Access-Control-Allow-Credentials;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**Critical**: Specific location blocks (`/auth/v1/`, `/rest/v1/`, `/storage/v1/`) **MUST** have `proxy_hide_header` directives. Nginx does NOT inherit these from the generic `/` location block!

---

## Common Issues & Solutions

### Issue 1: Duplicate CORS Headers

**Symptom**:
```
The 'Access-Control-Allow-Origin' header contains multiple values '*, *',
but only one is allowed.
```

**Root Cause**: Both nginx and upstream service (Kong, backend) adding CORS headers

**Solution**: Use `proxy_hide_header` to hide upstream CORS headers:

```nginx
location / {
    proxy_pass http://upstream;

    # Hide CORS headers from upstream
    proxy_hide_header Access-Control-Allow-Origin;
    proxy_hide_header Access-Control-Allow-Methods;
    proxy_hide_header Access-Control-Allow-Headers;
    proxy_hide_header Access-Control-Expose-Headers;
    proxy_hide_header Access-Control-Allow-Credentials;
}
```

**Important**: Add `proxy_hide_header` to **ALL specific location blocks** (e.g., `/auth/v1/`, `/rest/v1/`), not just the generic `/` block!

---

### Issue 2: Missing x-supabase-api-version Header

**Symptom**:
```
Request header field x-supabase-api-version is not allowed by
Access-Control-Allow-Headers in preflight response.
```

**Solution**: Add `x-supabase-api-version` to allowed headers:

```nginx
add_header Access-Control-Allow-Headers "Authorization, Content-Type, Accept, apikey, X-Client-Info, x-supabase-api-version" always;
```

---

### Issue 3: Nginx Location Block Inheritance

**Symptom**: CORS works for `/` but not for specific paths like `/auth/v1/token`

**Root Cause**: Nginx specific location blocks don't inherit directives from less-specific blocks

**Solution**: Duplicate `proxy_hide_header` in EACH location block:

```nginx
# Generic location
location / {
    proxy_hide_header Access-Control-Allow-Origin;  # ← Add here
    proxy_pass http://upstream;
}

# Specific location
location /auth/v1/ {
    proxy_hide_header Access-Control-Allow-Origin;  # ← ALSO add here!
    proxy_pass http://upstream;
}
```

---

### Issue 4: CORS Headers Not Sent on Errors

**Symptom**: CORS works for 200 responses but fails on 401/404/500

**Solution**: Use `always` modifier:

```nginx
add_header Access-Control-Allow-Origin "*" always;  # ← ALWAYS modifier
```

---

## Testing CORS Configuration

### Test 1: Check Allowed Headers

```bash
curl -s -I -X OPTIONS https://supabase-api.ailabsafrica.com/auth/v1/token \
  -H "Origin: https://app.ailabsafrica.com" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: x-supabase-api-version,content-type,authorization" | \
  grep -i "access-control"
```

**Expected Output**:
```
access-control-allow-origin: *
access-control-allow-methods: GET, POST, PUT, PATCH, DELETE, OPTIONS
access-control-allow-headers: Authorization, Content-Type, Accept, apikey, X-Client-Info, x-supabase-api-version
access-control-expose-headers: Content-Length, Content-Range
```

---

### Test 2: Check for Duplicate Headers

```bash
curl -s -I https://supabase-api.ailabsafrica.com/auth/v1/token \
  -H "Origin: https://app.ailabsafrica.com" | \
  grep -c "access-control-allow-origin"
```

**Expected Output**: `1` (no duplicates)

**If Output is `2` or more**: You have duplicate CORS headers! Add `proxy_hide_header` directives.

---

### Test 3: Test Actual Authentication Request

```bash
curl -s -X POST 'https://supabase-api.ailabsafrica.com/auth/v1/token?grant_type=password' \
  -H 'Content-Type: application/json' \
  -H 'Origin: https://app.ailabsafrica.com' \
  -H 'apikey: <YOUR_SUPABASE_ANON_KEY>' \
  -d '{"email":"admin@ailabsafrica.com","password":"Admin@2024!"}' | \
  python3 -m json.tool | head -10
```

**Expected**: Should return user data and access token (not CORS error)

---

## Best Practices

1. **Single CORS Layer**: Only ONE layer should add CORS headers (nginx OR upstream, not both)

2. **Use `always` Modifier**: Ensure CORS headers are sent even on errors:
   ```nginx
   add_header Access-Control-Allow-Origin "*" always;
   ```

3. **Specific Location Blocks**: Always add `proxy_hide_header` to specific location blocks:
   ```nginx
   location /auth/v1/ {
       proxy_hide_header Access-Control-Allow-Origin;
       # ... other hide directives
   }
   ```

4. **Supabase SDK Compatibility**: Always include `x-supabase-api-version` in allowed headers

5. **Test After Changes**: Always test CORS after nginx config changes:
   ```bash
   sudo nginx -t && sudo systemctl reload nginx
   curl -s -I https://api.example.com/endpoint | grep -i access-control
   ```

6. **Restrict Origins in Production**: Replace `"*"` with specific origins in production:
   ```nginx
   add_header Access-Control-Allow-Origin "https://app.ailabsafrica.com" always;
   ```

---

## Troubleshooting Checklist

When experiencing CORS issues:

- [ ] Does `Access-Control-Allow-Headers` include `x-supabase-api-version`?
- [ ] Are there duplicate CORS headers? (Check with `curl | grep -c`)
- [ ] Do ALL specific location blocks have `proxy_hide_header` directives?
- [ ] Is the `always` modifier present on all `add_header` directives?
- [ ] Does preflight OPTIONS request return 204?
- [ ] Are CORS headers present on error responses (401, 404, 500)?

---

## Related Documentation

- [Supabase Authentication Setup](./SUPABASE_AUTH_SETUP.md)
- [Default Users](../shared/auth/DEFAULT_USERS.md)
- [Shared Auth README](../shared/auth/README.md)
- [ERP Supabase Status](../erp/SUPABASE_STATUS.md) - Complete troubleshooting guide

---

## Changelog

### 2025-11-02
- Initial documentation
- Added Supabase-specific requirements
- Documented duplicate header issue and solution
- Added nginx location block inheritance caveat
- Added comprehensive testing section

---

**Maintained by**: KasaAI Development Team
**Questions**: See [ERP Supabase Status](../erp/SUPABASE_STATUS.md) for detailed troubleshooting examples
