# Admin User Setup for Organization Switcher

## Current Issue

The organization switcher is not showing because the admin user needs to have the `admin` role set in Supabase.

## Solution: Set Admin Role in Supabase

### Step 1: Access Supabase Dashboard

1. Go to: https://supabase.ailabsafrica.com
2. Log in with admin credentials

### Step 2: Find Admin User

1. Click **Authentication** in left sidebar
2. Click **Users**
3. Find user: `admin@ailabsafrica.com`
4. Click on the user to open details

### Step 3: Set Admin Role

1. Scroll to **Raw User Meta Data** section
2. Click **Edit** or directly edit the JSON
3. Add the following:
```json
{
  "role": "admin"
}
```
4. Click **Save** or **Update user**

### Step 4: Verify in Frontend

1. Log out of EstateFlow
2. Log back in as `admin@ailabsafrica.com`
3. Open browser DevTools (F12)
4. Go to **Console** tab
5. Look for logs like:
```
OrganizationContext - User: {
  email: "admin@ailabsafrica.com",
  role: "admin",
  isAdmin: true,
  organizationsCount: 5
}
```

6. You should see the organization switcher in the header next to the page title

## Alternative: Check in Browser Console

After logging in, run this in the browser console to check your user metadata:

```javascript
// Get current user
const { data: { user } } = await supabase.auth.getUser()
console.log('User email:', user.email)
console.log('User metadata:', user.user_metadata)
console.log('Is admin:', user.user_metadata?.role === 'admin' || user.email === 'admin@ailabsafrica.com')
```

## What the Organization Switcher Does

Once admin role is set:

1. **Shows in Header**: A dropdown appears next to the page title
2. **Lists All Organizations**: Shows all 5 organizations in the database:
   - Your Organization (5 properties)
   - Ghana Premium Properties (10 properties)
   - Test Org 1, 2, etc.
3. **Switches Context**: Clicking an organization switches all data views
4. **Persists Selection**: Remembers your choice in localStorage

## Debug Logging

The frontend now has debug logging enabled. After logging in, check the browser console for:

- `OrganizationContext - User:` - Shows user info and isAdmin status
- `OrganizationSwitcher:` - Shows if switcher is rendering and why/why not

## Expected Behavior

### For Admin Users (admin@ailabsafrica.com with role=admin):
- ✅ Organization switcher shows in header
- ✅ Can see and select all organizations
- ✅ Properties change when switching organizations

### For Regular Users:
- ❌ Organization switcher does NOT show
- ✅ Only see their assigned organization's data
- ✅ Cannot access other organizations

## Troubleshooting

### Issue: Still don't see switcher after setting role

1. **Hard refresh browser**: Ctrl+Shift+R (Windows/Linux) or Cmd+Shift+R (Mac)
2. **Clear browser cache**: Settings → Clear browsing data → Cached images and files
3. **Log out and log back in**: Fresh authentication token
4. **Check browser console**: Look for errors or debug logs

### Issue: "isAdmin: false" in console

Check:
1. User metadata has `"role": "admin"`
2. User email is exactly `admin@ailabsafrica.com`
3. Token is fresh (try logging out and back in)

### Issue: "organizationsCount: 0"

Check:
1. Backend is running: `sudo systemctl status kasaai-estateflow-backend`
2. Organizations API works: See test command below
3. Network tab in DevTools shows successful API call to `/api/v1/organizations`

## Test Organizations API

Test the organizations endpoint directly:

```bash
# Get your access token from browser (in DevTools → Application → Local Storage)
# Look for: sb-[project]-auth-token

curl -X GET "https://estateflow-api.ailabsafrica.com/api/v1/organizations" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" | jq
```

Expected response:
```json
{
  "organizations": [
    {
      "id": "68cc21d968f3a4c4d6847bc0",
      "name": "...",
      ...
    },
    ...
  ],
  "total": 5,
  "limit": 100,
  "offset": 0
}
```

## Files Updated

### Frontend (with debug logging):
- `src/contexts/OrganizationContext.tsx` - Added console logs
- `src/components/OrganizationSwitcher.tsx` - Added console logs and loading state
- Rebuilt: `/opt/kasaai/apps/estateflow/frontend/dist/`

### Backend:
- Organizations API: `/api/v1/organizations`
- Running on: https://estateflow-api.ailabsafrica.com

## Next Steps

1. Set admin role in Supabase user metadata
2. Log out and log back in
3. Open browser console
4. Look for organization switcher in header
5. If still not showing, share the console logs

---

**Need Help?**

Share the following from browser console:
1. `OrganizationContext - User:` log output
2. `OrganizationSwitcher:` log output
3. Any red errors in console
4. Network tab showing `/api/v1/organizations` request and response
