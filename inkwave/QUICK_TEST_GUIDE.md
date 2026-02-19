# Quick Test Guide - Organization Creation

**Status:** ✅ Fixed and Ready to Test
**Last Updated:** 2025-11-03

---

## 🚀 Quick Start (3 Steps)

### 1. Start Backend
```bash
cd /opt/kasaai/apps/inkwave/backend
source /opt/kasaai/apps/venv/bin/activate
uvicorn app.main:app --reload --port 30033
```

### 2. Open Browser
```
http://localhost:5173/admin/organizations
or
https://inkwave.ailabsafrica.com/admin/organizations
```

### 3. Create Organization
- Click "Create Organization"
- Fill form:
  - **Name:** `my-test-org` (lowercase, no spaces)
  - **Display Name:** `My Test Organization`
  - **Description:** `Testing org creation`
  - **Industry:** `Technology`
  - **Website:** `https://test.com`
- Click "Create"
- ✅ Should see success message

---

## ✅ What Should Happen

1. ✅ Success toast: "Organization 'My Test Organization' created successfully!"
2. ✅ Modal closes automatically
3. ✅ Organization appears in sidebar list
4. ✅ Can click to view details

---

## ❌ If Something Goes Wrong

### Error: "Authorization header missing"
**Fix:** Log in first at `/login`

### Error: "Name must be lowercase..."
**Fix:** Change name to lowercase (e.g., `my-org` not `My Org`)

### Error: Nothing happens
**Check:**
1. Is backend running? `curl http://localhost:30033/health`
2. Is MongoDB running? `sudo systemctl status mongod`
3. Open browser console (F12) for errors

---

## 🔍 Quick Debug

### Backend Running?
```bash
curl http://localhost:30033/health
# Should return: {"status":"healthy"...}
```

### Logged In?
```javascript
// In browser console (F12)
localStorage.getItem('access_token')
// Should return a long JWT string
```

### Organization Created?
```bash
mongosh mongodb://admin:aawwER4444%@127.0.0.1:27017/inkwave
db.organizations.find()
```

---

## 📚 Full Documentation

- **Debugging Guide:** [DEBUGGING_ORGANIZATION_CREATION.md](DEBUGGING_ORGANIZATION_CREATION.md)
- **Fix Summary:** [ORGANIZATION_CREATION_FIX_SUMMARY.md](ORGANIZATION_CREATION_FIX_SUMMARY.md)
- **User Tasks:** [USER_TASK_LISTS.md](USER_TASK_LISTS.md)

---

## 🎯 Test Checklist

- [ ] Backend running
- [ ] Logged in as user
- [ ] Can access /admin/organizations
- [ ] "Create Organization" button works
- [ ] Can fill and submit form
- [ ] Success message appears
- [ ] Organization appears in list
- [ ] Can view organization details

---

**That's it! You're ready to test.** 🎉
