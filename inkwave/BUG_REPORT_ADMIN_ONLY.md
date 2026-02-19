# InkWave - Bug Report Admin-Only Access

**Date:** 2025-12-05
**Status:** ✅ COMPLETE

## Summary

Restricted the bug report floating button to admin users only. Regular users and authors will no longer see the bug report widget.

---

## Changes Made

### Frontend: ReportBug Component Restriction

**File:** `/opt/kasaai/apps/inkwave/frontend/src/components/ReportBug.tsx`

**Before:**
```tsx
const ReportBug: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  // ... component renders for everyone
}
```

**After:**
```tsx
const ReportBug: React.FC = () => {
  const { data: profileData } = useProfile();
  const [isOpen, setIsOpen] = useState(false);

  // Only show for admin users
  const isAdmin = profileData?.is_admin === true ||
                  profileData?.role === 'admin' ||
                  profileData?.role === 'superadmin' ||
                  profileData?.role === 'universal_admin';

  // Don't render anything if not admin
  if (!isAdmin) {
    return null;
  }

  // ... rest of component
}
```

**Behavior:**
- Component checks user's profile data via `useProfile()` hook
- Verifies user has admin role (`admin`, `superadmin`, `universal_admin`) OR `is_admin` flag
- Returns `null` (renders nothing) if user is not admin
- Only admin users see the floating bug report button

---

## User Experience

### For Regular Users (USER role)
- ✅ Bug report button is completely hidden
- ✅ No UI clutter from admin-only features
- ✅ Cleaner interface

### For Authors (AUTHOR role)
- ✅ Bug report button is completely hidden
- ✅ Can upload books but cannot report bugs via widget
- ℹ️ Can still report bugs via support channels

### For Admins (ADMIN/SUPERADMIN)
- ✅ Bug report button visible in bottom-left corner
- ✅ Can report bugs directly to Linear/Slack
- ✅ Full access to bug reporting functionality

---

## Implementation Details

### Role Check Logic

The component checks multiple conditions for admin access:

```tsx
const isAdmin = profileData?.is_admin === true ||      // is_admin flag
                profileData?.role === 'admin' ||       // ADMIN role
                profileData?.role === 'superadmin' ||  // SUPERADMIN role
                profileData?.role === 'universal_admin'; // UNIVERSAL_ADMIN role
```

This ensures:
- Users with `is_admin: true` can report bugs
- Users with ADMIN role can report bugs
- Users with SUPERADMIN role can report bugs
- Users with UNIVERSAL_ADMIN role can report bugs

### Component Location

The `ReportBug` component is used in:
- `/src/pages/AdminDashboardPage.tsx` - Admin dashboard page

Even though it's on the admin dashboard (which is already protected), the component itself now also checks roles for defense in depth.

---

## Security Considerations

### Defense in Depth
1. **AdminDashboardPage** already requires authentication via `ProtectedRoute`
2. **ReportBug component** now also checks for admin role
3. **Backend API** (`/api/v1/feedback/bug-report`) should also verify permissions (TODO)

### Why Component-Level Check?

Even though the component is on an admin-only page, adding the role check to the component itself:
- Prevents accidental exposure if component is reused elsewhere
- Makes the component self-contained and secure by default
- Provides clear documentation of intended usage
- Follows security best practices (don't rely on parent context)

---

## Testing

### Manual Testing Steps

1. **As Regular User:**
   ```
   1. Log in with USER role account
   2. Navigate to any page
   3. ✓ Verify bug report button is NOT visible
   ```

2. **As Author:**
   ```
   1. Log in with AUTHOR role account
   2. Navigate to any page
   3. ✓ Verify bug report button is NOT visible
   ```

3. **As Admin:**
   ```
   1. Log in with ADMIN role account
   2. Navigate to admin dashboard (/admin)
   3. ✓ Verify bug report button IS visible (bottom-left)
   4. ✓ Click and verify modal opens
   5. ✓ Submit a test report
   ```

### Expected Behavior

| Role | Bug Report Button Visible |
|------|---------------------------|
| USER | ❌ No |
| AUTHOR | ❌ No |
| ADMIN | ✅ Yes |
| SUPERADMIN | ✅ Yes |
| UNIVERSAL_ADMIN | ✅ Yes |

---

## Future Enhancements

### Recommended

1. **Backend API Protection**
   ```python
   # TODO: Add admin check to bug report endpoint
   @router.post("/feedback/bug-report")
   async def submit_bug_report(
       bug_report: BugReport,
       user = Depends(get_current_admin_user)  # Require admin
   ):
   ```

2. **Alternative Feedback Channel**
   - Add "Contact Support" link for regular users
   - Provide email/form for non-admins to report issues
   - Create public feedback board for feature requests

3. **Admin Bug Report Analytics**
   - Track bug reports by admin user
   - Show bug report history in admin dashboard
   - Link to Linear issues directly

---

## Files Modified

### Frontend
- `src/components/ReportBug.tsx` - Added admin role check
- Built and deployed new frontend bundle

### Documentation
- `BUG_REPORT_ADMIN_ONLY.md` - This file

---

## Rollback Instructions

If issues arise:

```bash
cd /opt/kasaai/apps/inkwave/frontend

# Revert changes
git checkout HEAD -- src/components/ReportBug.tsx

# Rebuild
npm run build
```

---

## Related Changes

This change is part of a broader effort to implement role-based access control:
- ✅ Book upload restricted to AUTHOR/ADMIN (previous)
- ✅ My Books page restricted to ADMIN (previous)
- ✅ Bug report widget restricted to ADMIN (this change)

See also:
- `ADMIN_ACCESS_CONTROL_CHANGES.md` - Book upload and My Books restrictions

---

## Support

For questions or issues:
1. Verify user role: `db.users.findOne({email: "user@example.com"}, {role: 1, is_admin: 1})`
2. Check browser console for profile data loading
3. Verify `useProfile()` hook returns correct data

---

**Status:** ✅ **PRODUCTION READY**

Bug report widget is now properly restricted to admin users only.
