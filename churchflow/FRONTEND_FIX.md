# ChurchFlow Frontend - Configuration Fix

**Date:** 2025-10-24
**Issue:** Frontend serving old build after hard refresh
**Status:** ✅ **FIXED**

---

## Issues Found

### 1. **No API Proxy in Nginx** ❌
- Frontend had hardcoded API URLs to `http://churchflow-api.ailabsafrica.com`
- This domain doesn't exist/resolve
- API calls were failing

### 2. **Aggressive Browser Caching** ❌
- Static assets cached for 365 days
- Hard refresh wasn't clearing cache effectively
- Users stuck on old version

### 3. **Missing axios Dependency** ❌
- `ConferenceRegistration.tsx` imports axios
- Package not in package.json
- Build was failing

### 4. **Mixed API URLs** ❌
- Some files: `http://churchflow-api.ailabsafrica.com`
- Some files: `http://localhost:30030`
- No centralized configuration

---

## Fixes Applied

### 1. **Added Nginx API Proxy** ✅

Added to `/etc/nginx/sites-enabled/churchflow.ailabsafrica.com.conf`:

```nginx
location /api/v1/ {
    proxy_pass http://127.0.0.1:30030/api/v1/;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;

    # Disable caching for API responses
    add_header Cache-Control "no-store, no-cache, must-revalidate";
    expires off;
}
```

**Result:** API now accessible at `https://churchflow.ailabsafrica.com/api/v1/*`

### 2. **Reduced Cache Duration** ✅

Changed static asset caching:

**Before:**
```nginx
expires 365d;
add_header Cache-Control "public, immutable";
```

**After:**
```nginx
expires 7d;
add_header Cache-Control "public, max-age=604800";
```

**Result:** Easier to deploy updates, still good caching

### 3. **Installed axios** ✅

```bash
npm install axios
```

### 4. **Fixed All API URLs** ✅

Replaced hardcoded URLs with relative paths:

**Before:**
```typescript
fetch('http://churchflow-api.ailabsafrica.com/api/v1/auth/login')
fetch('http://localhost:30030/api/users/me')
```

**After:**
```typescript
fetch('/api/v1/auth/login')
fetch('/api/v1/users/me')
```

Files updated:
- `src/pages/QRScanner.tsx`
- `src/pages/ConferenceRegistration.tsx`
- `src/pages/Login.tsx`
- `src/pages/BusManagement.tsx`
- `src/pages/Dashboard.tsx`
- `src/pages/ConferenceManagement.tsx`

### 5. **Rebuilt Frontend** ✅

```bash
npm run build
```

**New Build:**
- `index-DzaVqoAd.js` (245KB)
- `index-CD0qDKQL.css` (19KB)
- Built: Oct 24, 2025 17:25

---

## Verification

### ✅ Nginx Serving Correct Directory
```
root /opt/kasaai/apps/churchflow/frontend/dist;
```

### ✅ Latest Build is Live
```bash
$ curl -s https://churchflow.ailabsafrica.com/ | grep -o 'index-.*\.js'
index-DzaVqoAd.js  # ✅ New version
```

### ✅ API Proxy Working
```bash
$ curl -s https://churchflow.ailabsafrica.com/api/v1/users/me
{"detail":"Not authenticated"}  # ✅ Proper API response
```

### ✅ New Assets Accessible
```bash
$ curl -I https://churchflow.ailabsafrica.com/assets/index-DzaVqoAd.js
HTTP/2 200  # ✅ New JS file loads
```

---

## For Users: How to See New Version

### Option 1: Hard Refresh (Recommended)
- **Chrome/Firefox (Windows/Linux):** Ctrl + Shift + R
- **Chrome/Firefox (Mac):** Cmd + Shift + R
- **Safari:** Cmd + Option + R

### Option 2: Clear Browser Cache
1. Open browser settings
2. Clear browsing data
3. Select "Cached images and files"
4. Refresh page

### Option 3: Incognito/Private Window
- Open in private/incognito mode
- New version will load automatically

---

## Architecture

### Before (Broken)
```
Browser → churchflow-api.ailabsafrica.com ❌
          (DNS doesn't resolve)
```

### After (Working)
```
Browser → churchflow.ailabsafrica.com/api/v1/*
       → Nginx Proxy
       → localhost:30030 (Backend)
       → ✅ Working
```

---

## File Structure

```
/opt/kasaai/apps/churchflow/
├── frontend/
│   ├── dist/                    # ← Nginx serves from here
│   │   ├── index.html          # Updated with new asset hashes
│   │   └── assets/
│   │       ├── index-DzaVqoAd.js   # New build
│   │       └── index-CD0qDKQL.css  # New build
│   ├── src/
│   │   ├── config.ts           # API configuration (created)
│   │   └── pages/              # All API URLs fixed
│   └── .env.production         # Created
└── backend/                     # Runs on port 30030
```

---

## Testing Checklist

- ✅ Nginx config valid (`nginx -t`)
- ✅ Nginx reloaded
- ✅ Frontend builds without errors
- ✅ New asset hashes generated
- ✅ Live site serves new version
- ✅ API proxy returns proper responses
- ✅ All API URLs use relative paths
- ✅ Cache headers updated

---

## What Changed for Developers

### API Calls (All Pages)

**Old Way (Don't Use):**
```typescript
const response = await fetch('http://churchflow-api.ailabsafrica.com/api/v1/users');
```

**New Way (Use This):**
```typescript
const response = await fetch('/api/v1/users');
```

**Why:**
- Works in both development and production
- No CORS issues
- Uses nginx proxy automatically

---

## Cache Strategy

| Resource | Cache Duration | Reason |
|----------|----------------|---------|
| HTML | No cache | Always fresh |
| API responses | No cache | Always fresh |
| JS/CSS | 7 days | Balance between performance and updates |
| Images | 7 days | Infrequently change |

**Note:** Vite automatically adds content hashes to filenames (e.g., `index-DzaVqoAd.js`), so new builds force browser to fetch new files even with caching.

---

## Troubleshooting

### "Still seeing old version"
1. Check browser console for errors
2. Hard refresh (Ctrl+Shift+R)
3. Check Network tab shows new asset hash
4. Try incognito mode
5. Clear browser cache completely

### "API calls failing"
1. Check nginx is running: `sudo systemctl status nginx`
2. Check backend is running: `sudo systemctl status kasaai-churchflow`
3. Test API directly: `curl https://churchflow.ailabsafrica.com/api/v1/health`
4. Check nginx error logs: `sudo tail -f /var/log/nginx/churchflow.ailabsafrica.error.log`

### "Build fails"
1. Check all dependencies installed: `npm install`
2. Check node_modules exists
3. Try clean install: `rm -rf node_modules && npm install`
4. Check for TypeScript errors: `npm run build`

---

## Production URLs

- **Frontend:** https://churchflow.ailabsafrica.com
- **API (via proxy):** https://churchflow.ailabsafrica.com/api/v1/*
- **Backend (direct):** http://localhost:30030/api/v1/*

---

## Summary

All issues have been resolved:

1. ✅ API proxy configured in nginx
2. ✅ All API URLs fixed to use relative paths
3. ✅ axios dependency installed
4. ✅ Cache duration reduced for easier updates
5. ✅ Frontend rebuilt with new asset hashes
6. ✅ New version deployed and accessible

**Status:** Production ready. Users may need to hard refresh to see changes due to previous 365-day cache.

---

**Fixed by:** Claude (AI Assistant)
**Date:** 2025-10-24
**Time:** ~30 minutes

🤖 Generated with [Claude Code](https://claude.com/claude-code)
