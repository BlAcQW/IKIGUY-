# Like and Comment Interactions - Fix Summary & QA Checklist

## Date: 2025-12-16

## Overview
Fixed non-functional like (heart) and comment buttons across the FreshManna application. Issues included inactive buttons, missing API wiring, inconsistent state management, and lack of authentication handling.

---

## Root Causes Identified

### Backend Issues
1. **Collection Name Mismatch** ⚠️ CRITICAL
   - `engagement_service.py` was writing to `devotional_likes` collection
   - `devotional_service.py` was reading from `likes` collection
   - Result: Likes were never reflected when fetching devotionals

### Frontend Issues
1. **TrendingDevotionals (Landing Page)**
   - Like/comment icons were decorative only, not interactive
   - No mutations wired up
   - Entire card navigated to auth page on click

2. **Feed Page**
   - Missing authentication checks before API calls
   - Silent 401 errors with no user feedback

3. **Devotional Detail Page**
   - Comments API response format mismatch (expected `.items`, got array)
   - No URL hash support for opening comments directly

4. **State Consistency**
   - Query caches not invalidated across pages
   - Liking on detail page didn't update feed counts

---

## Changes Made

### Backend Fixes

#### File: `backend/app/services/engagement_service.py`
**Lines 45-55, 71-78**
- ✅ Changed `db.devotional_likes` to `db.likes`
- ✅ Updated schema to use `target_id` and `target_type` fields
- ✅ Now consistent with `devotional_service.py` and database indexes

**Before:**
```python
existing_like = await db.devotional_likes.find_one(
    {"devotional_id": ObjectId(devotional_id), "user_id": ObjectId(user_id)}
)
```

**After:**
```python
existing_like = await db.likes.find_one(
    {
        "target_id": ObjectId(devotional_id),
        "user_id": ObjectId(user_id),
        "target_type": "devotional"
    }
)
```

### Frontend Fixes

#### File: `frontend/src/components/landing/TrendingDevotionals.tsx`
**Lines 7-15, 60-120, 223-248**
- ✅ Added `useAuth`, `useToast`, `useMutation`, `queryClient` hooks
- ✅ Added `likeMutation` with authentication check
- ✅ Added optimistic updates with rollback on error
- ✅ Made like button interactive with `stopPropagation`
- ✅ Made comment button navigate to devotional with `#comments` hash
- ✅ Query invalidation for state consistency

**Key Addition:**
```tsx
<button
  onClick={(e) => {
    e.stopPropagation();
    likeMutation.mutate(devotional.id);
  }}
  className={cn(
    "flex items-center gap-1.5 transition-colors",
    devotional.is_liked ? "text-secondary" : "hover:text-secondary"
  )}
>
  <Heart className={cn("w-4 h-4", devotional.is_liked && "fill-secondary")} />
  <span>{devotional.stats.likes}</span>
</button>
```

#### File: `frontend/src/pages/Feed.tsx`
**Lines 85-108, 110, 129-130, 140-151, 152-200**
- ✅ Added authentication check before like mutation
- ✅ Added sign-in prompt toast for unauthenticated users
- ✅ Skip optimistic updates if not authenticated
- ✅ Added same for bookmark mutation
- ✅ Query invalidation for cross-page consistency

**Key Addition:**
```tsx
if (!user) {
  toast({
    title: "Sign in required",
    description: "Please sign in to like devotionals",
    action: (
      <Button variant="outline" size="sm" onClick={() => navigate('/auth?redirect=...')}>
        Sign In
      </Button>
    ),
  });
  throw new Error('Authentication required');
}
```

#### File: `frontend/src/pages/Devotional.tsx`
**Lines 77, 83-87, 134-135, 195-200, 353-405**
- ✅ Fixed comments API response handling (removed `.items` accessor)
- ✅ Added URL hash support to open comments directly
- ✅ Added authentication check to comment mutation
- ✅ Added success/error toasts for better UX
- ✅ Query invalidation across all pages

**Key Fixes:**
```tsx
// Open comments via URL hash
const [showComments, setShowComments] = useState(window.location.hash === '#comments');

useEffect(() => {
  if (window.location.hash === '#comments') {
    setShowComments(true);
  }
}, [id]);

// Fixed comments response
const response = await apiClient.getComments(id);
return Array.isArray(response) ? response : [];
```

---

## QA Testing Checklist

### Prerequisites
- [ ] Backend service running on port 30042
- [ ] Frontend dev server running
- [ ] Two test accounts (authenticated & unauthenticated)
- [ ] Published devotional with 0 likes/comments

### Test Scenarios

#### 1. Unauthenticated User - Landing Page
- [ ] Navigate to landing page
- [ ] Verify like counts are visible on trending cards
- [ ] Click heart icon → Should show "Sign in required" toast
- [ ] Toast should have "Sign In" button
- [ ] Click "Sign In" button → Should navigate to auth page
- [ ] Click comment icon → Should navigate to devotional detail with comments open

#### 2. Unauthenticated User - Feed Page
- [ ] Navigate to `/feed`
- [ ] Verify like counts are visible
- [ ] Click heart icon → Should show "Sign in required" toast
- [ ] Verify no API call is made (check network tab)

#### 3. Unauthenticated User - Devotional Detail
- [ ] Navigate to devotional detail page
- [ ] Click heart icon → Should show "Sign in required" toast
- [ ] Click comment button → Comment sheet opens
- [ ] Verify comment input is disabled or prompts sign-in
- [ ] Try to submit comment → Should prompt to sign in

#### 4. Authenticated User - Landing Page
- [ ] Sign in with test account
- [ ] Navigate to landing page
- [ ] Click heart icon on a trending card
- [ ] Verify heart fills with color immediately (optimistic update)
- [ ] Verify count increments immediately
- [ ] Click heart again → Should unlike (heart unfills, count decrements)
- [ ] Refresh page → Verify like state persists correctly

#### 5. Authenticated User - Feed Page
- [ ] Navigate to `/feed`
- [ ] Click heart on first devotional
- [ ] Verify optimistic update works
- [ ] Click heart again to unlike
- [ ] Verify state persists after refresh

#### 6. Authenticated User - Devotional Detail
- [ ] Navigate to devotional detail
- [ ] Click heart → Verify like works
- [ ] Click comment button → Comment sheet opens
- [ ] Type a comment (e.g., "Test comment")
- [ ] Submit comment
- [ ] Verify "Comment posted" toast appears
- [ ] Verify comment appears in list immediately
- [ ] Verify comment count increments on devotional

#### 7. Cross-Page State Consistency
- [ ] Like a devotional on the detail page
- [ ] Navigate back to feed page
- [ ] Verify the devotional shows as liked in the feed
- [ ] Navigate to landing page
- [ ] Verify the devotional shows as liked in trending cards
- [ ] Unlike from landing page
- [ ] Verify all pages reflect the unliked state

#### 8. Comment Functionality
- [ ] Navigate to devotional detail
- [ ] Click comment button
- [ ] Post comment #1
- [ ] Post comment #2
- [ ] Verify both comments appear
- [ ] Verify comment count shows "2"
- [ ] Navigate away and back
- [ ] Verify comments persist
- [ ] Go to feed → Verify comment count shows "2"
- [ ] Go to landing page → Verify comment count shows "2"

#### 9. Navigation with Hash
- [ ] Share devotional URL with `#comments` hash
- [ ] Open in new tab
- [ ] Verify comments section opens automatically

#### 10. Error Handling
- [ ] Disconnect internet (if testing offline support)
- [ ] Try to like → Should queue for later or show error
- [ ] Reconnect internet
- [ ] Verify queued action syncs (if offline support exists)

#### 11. Comment Validation
- [ ] Try to post empty comment → Should fail
- [ ] Try to post 501 character comment → Should fail with validation error
- [ ] Post valid comment → Should succeed

#### 12. Database Verification
- [ ] After liking: Check MongoDB `likes` collection
- [ ] Verify document has `target_id`, `target_type: "devotional"`, `user_id`
- [ ] After commenting: Check MongoDB `comments` collection
- [ ] Verify document has `devotional_id`, `user_id`, `text`, `likes_count: 0`
- [ ] Verify `devotionals` collection has updated `likes_count` and `comments_count`

---

## API Endpoints Reference

| Method | Endpoint | Auth Required | Description |
|--------|----------|---------------|-------------|
| POST | `/api/v1/devotionals/{id}/like` | Yes | Toggle like on devotional |
| POST | `/api/v1/devotionals/{id}/bookmark` | Yes | Toggle bookmark on devotional |
| GET | `/api/v1/devotionals/{id}/comments` | No | Get all comments for devotional |
| POST | `/api/v1/devotionals/{id}/comments` | Yes | Create comment on devotional |
| DELETE | `/api/v1/comments/{id}` | Yes | Soft delete comment |

---

## Known Limitations

1. **Tests Not Running**: Integration tests created but can't run due to import path issues with shared modules. Manual QA required.

2. **Offline Support**: While mutations check `isOnline` flag, full offline sync functionality depends on service worker implementation.

3. **Comment Likes**: Comment liking UI exists but mutation not fully tested in this fix cycle.

4. **Comment Editing**: Comment editing exists but not covered in this fix.

---

## Rollback Plan

If issues occur in production:

1. **Backend Rollback**:
   ```bash
   git revert <commit-hash>
   sudo systemctl restart kasaai-devotionalflow-backend
   ```

2. **Frontend Rollback**:
   ```bash
   git revert <commit-hash>
   npm run build
   ```

3. **Database Migration** (if needed):
   ```javascript
   // Rename collection back
   db.likes.renameCollection("devotional_likes")
   ```

---

## Post-Deployment Monitoring

Watch for:
- 401 errors on `/devotionals/{id}/like` endpoint
- Missing `is_liked` field in devotional responses
- Comment count not incrementing
- Frontend console errors related to mutations

**Logs to check:**
```bash
# Backend logs
sudo journalctl -u kasaai-devotionalflow-backend -f | grep -i "like\|comment"

# Check for 401s
sudo journalctl -u kasaai-devotionalflow-backend -f | grep "401"
```

---

## Success Criteria

- [X] Backend uses consistent collection name (`likes`)
- [X] All frontend components wire up mutations correctly
- [X] Authentication checks present before all mutations
- [X] Optimistic updates work with rollback on error
- [X] Query invalidation ensures state consistency
- [X] User-friendly error messages for unauthenticated users
- [X] URL hash navigation opens comments automatically
- [ ] All QA test scenarios pass (requires manual testing)

---

## Files Modified

**Backend:**
- `app/services/engagement_service.py` (lines 45-55, 71-78)

**Frontend:**
- `src/components/landing/TrendingDevotionals.tsx` (major refactor)
- `src/pages/Feed.tsx` (authentication checks added)
- `src/pages/Devotional.tsx` (comments fix, hash navigation, auth checks)

**Tests:**
- `backend/tests/test_likes_comments.py` (created, needs env fixes to run)

**Documentation:**
- `LIKES_COMMENTS_FIX_QA.md` (this file)

---

## Next Steps

1. ✅ Complete all fixes
2. ⏳ Run manual QA using checklist above
3. ⏳ Fix any issues found during QA
4. ⏳ Deploy to dev environment
5. ⏳ Re-run QA on dev
6. ⏳ Deploy to production with monitoring
7. ⏳ Address user's additional feature requests (reading settings, etc.)
