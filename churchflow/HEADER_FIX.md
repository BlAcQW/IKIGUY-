# Header Encoding Error Fix

## Problem

Users were experiencing "Failed to encode header value" errors in the browser console:

```
Failed to encode header value: DOMException: String contains an invalid character
```

This error occurred when making API requests, specifically when the `Authorization` header was being set with an access token.

## Root Cause

HTTP headers must only contain **ISO-8859-1 (Latin-1)** characters. The error occurred because authentication tokens stored in localStorage contained invalid characters:
- Newlines (`\n`)
- Carriage returns (`\r`)
- Tabs (`\t`)
- Extra whitespace

These characters can be introduced when:
1. Tokens are copied/pasted with trailing newlines
2. API responses include whitespace
3. Code inadvertently adds whitespace when storing tokens

## Solution

Created a `sanitizeToken()` utility function that removes all invalid characters from tokens before use.

### Implementation

**File**: `src/lib/header-utils.ts`

```typescript
export function sanitizeToken(token: string | null | undefined): string | null {
  // Handle null/undefined/empty
  if (!token || token.trim() === '') {
    return null;
  }

  // Remove all whitespace (including newlines, carriage returns, tabs)
  const sanitized = token.replace(/[\r\n\t\s]+/g, '').trim();

  // Return null if sanitized token is empty
  return sanitized === '' ? null : sanitized;
}
```

### Applied In 3 Critical Locations

#### 1. Request Interceptor (axios-config.ts)
**When**: Every API request
```typescript
const rawToken = localStorage.getItem('access_token')
const token = sanitizeToken(rawToken)
if (token && config.headers) {
  config.headers.Authorization = `Bearer ${token}`
}
```

#### 2. Token Refresh Flow (axios-config.ts)
**When**: After 401 errors and token exchange
```typescript
const rawNewToken = await exchangeToken()
const newToken = sanitizeToken(rawNewToken)
if (newToken) {
  localStorage.setItem('access_token', newToken)
}
```

#### 3. Token Storage (Login.tsx, OrganizationContext.tsx)
**When**: Storing tokens to localStorage
```typescript
const backendToken = sanitizeToken(rawBackendToken)
if (backendToken) {
  localStorage.setItem('access_token', backendToken)
}
```

## Files Modified

1. **lib/header-utils.ts**
   - Added `sanitizeToken()` function

2. **lib/axios-config.ts**
   - Import `sanitizeToken`
   - Sanitize tokens in request interceptor
   - Sanitize tokens in retry logic
   - Sanitize tokens after refresh

3. **pages/Login.tsx**
   - Import `sanitizeToken`
   - Sanitize Supabase token before storage
   - Sanitize backend token before storage

4. **contexts/OrganizationContext.tsx**
   - Import `sanitizeToken`
   - Sanitize token during organization switch

## Testing

### Unit Tests
All sanitization tests pass:
- ✅ Clean token (no changes)
- ✅ Token with newline (`\n`)
- ✅ Token with carriage return (`\r`)
- ✅ Token with tabs (`\t`)
- ✅ Token with spaces
- ✅ Empty string → `null`
- ✅ Whitespace only → `null`

### Production Verification
After deployment:
1. Clear localStorage
2. Login fresh
3. Verify no "Failed to encode header value" errors
4. Check browser console for clean API requests

## Impact

### Before Fix
❌ HTTP header errors on every request
❌ Console filled with DOMException errors
❌ Potential API failures
❌ Poor user experience

### After Fix
✅ All tokens sanitized before use
✅ Clean HTTP headers
✅ No console errors
✅ Reliable API communication

## Prevention

The fix is **defensive** and handles tokens from any source:
- API responses
- User input
- Copy/paste operations
- Environment variables

By sanitizing at both **storage** and **retrieval** points, we ensure tokens are always safe for HTTP header use.

## Related Issues

This fix also improves:
- Token refresh reliability
- Organization switching
- Cross-origin requests
- Mobile browser compatibility

## Additional Fix Required

After initial deployment, the error persisted because **many files were bypassing the axios interceptor** and setting the `X-Organization-ID` header directly using `fetch()` calls.

### Phase 2: Fix Direct Header Assignments

Created a batch script to update 12 files that were setting `X-Organization-ID` without encoding:

1. **hooks/useGiving.ts** - 8 locations
2. **hooks/useAnalytics.ts** - 4 locations
3. **hooks/useMemberAnalytics.ts** - 1 location
4. **hooks/useAutomation.ts** - 7 locations
5. **hooks/useIntegrations.ts** - 11 locations
6. **pages/RegisteredMembers.tsx** - 1 location
7. **pages/RegistrationDetail.tsx** - 3 locations
8. **pages/QRScanner.tsx** - 8 locations
9. **pages/admin/AutomationPage.tsx** - 1 location
10. **components/admin/OrganizationBilling.tsx** - 4 locations
11. **components/admin/SubscriptionBilling.tsx** - 3 locations
12. **components/admin/UserManagement.tsx** - 3 locations

**Total**: 54 locations fixed

### Changes Made

Before:
```typescript
headers['X-Organization-ID'] = organizationId;
// or
'X-Organization-ID': organizationId
```

After:
```typescript
const encoded = encodeHeaderValue(organizationId);
if (encoded) {
  headers['X-Organization-ID'] = encoded;
}
// or
'X-Organization-ID': encodeHeaderValue(organizationId) || ''
```

## Deployment

**Date**: December 20, 2025
**Initial Commit**: `20dda4f6` - Added sanitizeToken()
**Complete Fix Commit**: `6c8ebc84` - Fixed all direct X-Organization-ID assignments
**New Bundle**: `index-B10zWhYn.js`
**Status**: ✅ Deployed to Production

---

**Last Updated**: December 20, 2025
**Severity**: Critical (User-facing errors)
**Resolution**: Complete
