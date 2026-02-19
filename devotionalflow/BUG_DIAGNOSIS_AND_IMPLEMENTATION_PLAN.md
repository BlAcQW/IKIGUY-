# DevotionalFlow - Bug Diagnosis & Implementation Plan

**Date:** December 15, 2025
**Tech Stack:** FastAPI + Motor (async) + MongoDB | React + TypeScript + Vite PWA + TanStack Query

---

## STEP 0: CODE MAPPING ✅ COMPLETE

### Backend Routes Mapped
- ✅ **18 route files** fully documented
- ✅ All endpoints cataloged with auth requirements
- ✅ Query parameters documented
- ✅ Base URL: `https://freshmanna-api.ailabsafrica.com/api/v1`

### Frontend Routes Mapped
- ✅ **25+ page routes** identified
- ✅ API client methods cataloged (107 methods)
- ✅ Feature implementations verified
- ✅ Component locations documented

**Key Findings:**
- ✅ Bookmarks API exists and is fully implemented
- ✅ Reading preferences partially implemented
- ❌ Recent devotionals filtering by date range NOT implemented
- ❌ Block users feature NOT implemented
- ❌ Delete account feature NOT implemented

---

## BUG #1: Recent Devotionals (Last 30 Days) Browse

### 🔍 Diagnosis

**Root Cause:** The Browse page sorts devotionals but **does NOT filter by date range**.

**File:** `/opt/kasaai/apps/devotionalflow/frontend/src/pages/Browse.tsx`

**Current Implementation (Lines 51-57):**
```typescript
const response = await apiClient.getDevotionals({
  status: 'published',
  category: selectedCategory === 'all' ? undefined : selectedCategory,
  sort_by: sortBy as any,
  sort_order: 'desc',
  limit: 50,
});
```

**Missing:**
- ❌ No `startDate` or `endDate` filter parameter
- ❌ Backend `/api/v1/devotionals/` endpoint doesn't support date range filtering
- ❌ No "Recent" button or date range UI in Browse page

**Database Field:**
- Field used for publish date: `published_at` (confirmed in backend model)

### 🎯 Impact: **HIGH** - Core feature not working

### ⚠️ Risk: **LOW** - Additive change, no breaking changes

---

## BUG #2: Bookmark/Favorite Devotionals

### 🔍 Diagnosis

**Status:** API endpoints exist, need to verify frontend toggle behavior

**Backend Endpoints (CONFIRMED):**
```
POST /api/v1/devotionals/{devotional_id}/bookmark (toggle)
GET /api/v1/users/me/bookmarks (list)
```

**Frontend Implementation:**
- **File:** `/opt/kasaai/apps/devotionalflow/frontend/src/lib/api.ts`
  - Line 267: `bookmarkDevotional(id)` ✅
  - Line 275: `getBookmarks()` ✅

- **File:** `/opt/kasaai/apps/devotionalflow/frontend/src/pages/Bookmarks.tsx`
  - Lines 183-293: Full bookmark UI ✅

**Potential Issues:**
1. Bookmark toggle not showing optimistic UI updates
2. TanStack Query cache not invalidating after bookmark
3. Bookmark icon state not syncing with server

**Need to Verify:**
- Check if toggle in Devotional.tsx properly calls API
- Verify TanStack Query cache invalidation
- Test actual toggle behavior with real API

### 🎯 Impact: **HIGH** - Core engagement feature

### ⚠️ Risk: **LOW** - Likely just missing cache invalidation

---

## BUG #3: Reading Settings (Theme & Line Height)

### 🔍 Diagnosis

**Found:**
- ✅ Notification settings fully working (Profile.tsx lines 750-987)
- ✅ Privacy settings fully working (PrivacySettingsDialog.tsx)

**Missing:**
- ❌ Theme switcher for reader view
- ❌ Line height control for reader typography
- ❌ Font size control in reader (mentioned as "only thing that works")

**Current State:**
- `next-themes` is installed (package.json line 56) but need to verify:
  1. ThemeProvider wraps app in main.tsx
  2. Reader page uses theme tokens (not hardcoded colors)

**Backend Support:**
```typescript
// User model has reading_preferences:
{
  font_size: "small" | "medium" | "large",
  theme: "light" | "dark",
  notification_time: string
}
```

**What Needs Implementation:**
1. Theme toggle in settings (light/dark mode)
2. Line height slider/selector (1.0x, 1.5x, 2.0x)
3. Apply settings in reader typography CSS
4. Persist in user preferences via API

### 🎯 Impact: **MEDIUM** - UX improvement, accessibility

### ⚠️ Risk: **LOW** - Additive UI changes

---

## BUG #4: Block Users Feature

### 🔍 Diagnosis

**Status:** ❌ **NOT IMPLEMENTED**

**Backend:** No routes found for blocking
**Frontend:** No UI components found

**Required Implementation:**

**Backend Routes (NEW):**
```
POST /api/v1/users/{user_id}/block
DELETE /api/v1/users/{user_id}/unblock
GET /api/v1/users/me/blocked
```

**Database Schema:**
```javascript
blocks collection {
  _id: ObjectId,
  blocker_user_id: ObjectId,  // User who is blocking
  blocked_user_id: ObjectId,   // User being blocked
  created_at: DateTime
}

// Index: { blocker_user_id: 1, blocked_user_id: 1 } unique
```

**Comment Filtering:**
- Modify `/api/v1/devotionals/{id}/comments` to filter blocked users
- Hide comments from users you blocked
- Hide your comments from users who blocked you

**Frontend UI:**
- Add "Block User" to comment context menu
- Add "Block User" to profile page
- Create BlockedUsers settings page with unblock option

### 🎯 Impact: **MEDIUM** - Safety & moderation feature

### ⚠️ Risk: **MEDIUM** - Affects comment queries, requires careful testing

---

## BUG #5: Delete Account Feature

### 🔍 Diagnosis

**Status:** ❌ **NOT IMPLEMENTED**

**Current:** Only "Sign Out" button exists (Profile.tsx lines 1016-1023)

**Required Implementation:**

**Backend Route (NEW):**
```
POST /api/v1/users/me/delete
Request Body: { confirmation: "DELETE" }
```

**Security Requirements:**
1. Require re-authentication (recent login < 5 minutes ago)
2. User must type "DELETE" to confirm
3. Optional: Send email confirmation link

**Data Handling:**
```javascript
// Keep for data integrity:
- Devotionals (mark as "Deleted User" author)
- Comments (anonymize: authorName = "Deleted User", authorId = null)

// Delete:
- User document
- Reading history
- Bookmarks
- Likes
- Gamification profile
- Streak data
- Push subscriptions
```

**Frontend Flow:**
1. Settings → Delete Account button (red, destructive)
2. Warning dialog: "This action cannot be undone"
3. Type "DELETE" confirmation
4. Re-auth prompt (if needed)
5. Call API → logout → redirect to homepage

### 🎯 Impact: **LOW** - Legal requirement (GDPR), infrequent use

### ⚠️ Risk: **HIGH** - Irreversible, must handle data carefully

---

## IMPLEMENTATION PRIORITY ORDER

### Phase 1: Critical Fixes (Ship First) 🚀
**Priority:** Highest | **Risk:** Lowest | **Impact:** Highest

1. **Recent Devotionals Date Filtering** (2-3 hours)
   - Backend: Add date range query params to `/devotionals/`
   - Frontend: Add date filter UI to Browse page
   - Add Mongo indexes for `published_at`
   - Write pytest for date filtering

2. **Fix Bookmark Toggle Behavior** (1-2 hours)
   - Verify toggle works, add optimistic updates
   - Fix TanStack Query cache invalidation
   - Test with real API calls

### Phase 2: UX Improvements (Ship Second) ✨
**Priority:** Medium | **Risk:** Low | **Impact:** Medium

3. **Reading Settings (Theme + Line Height)** (2-3 hours)
   - Verify next-themes setup
   - Add line height control to settings
   - Apply settings in reader CSS
   - Persist preferences

### Phase 3: Safety Features (Ship Third) 🛡️
**Priority:** Medium | **Risk:** Medium | **Impact:** Medium

4. **Block Users Feature** (4-6 hours)
   - Backend routes + Mongo schema
   - Comment filtering logic
   - Frontend UI (block/unblock)
   - pytest tests for comment filtering

### Phase 4: Legal Compliance (Ship Last) ⚖️
**Priority:** Low | **Risk:** High | **Impact:** Low (frequency)

5. **Delete Account Feature** (3-4 hours)
   - Backend deletion route with safeguards
   - Data anonymization logic
   - Frontend confirmation flow
   - pytest tests for data cleanup

---

## DETAILED IMPLEMENTATION PLANS

### A) Recent Devotionals - Backend

**File:** `/opt/kasaai/apps/devotionalflow/backend/app/routes/devotionals.py`

**Changes Needed:**

1. Add query parameters to existing `GET /` endpoint:
```python
@router.get("/")
async def list_devotionals(
    # ... existing params ...
    start_date: Optional[str] = Query(None, description="Start date YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="End date YYYY-MM-DD"),
    days: Optional[int] = Query(None, description="Last N days from today"),
):
    query = {"status": "published"}

    # Date filtering
    if days:
        start_date = (datetime.utcnow() - timedelta(days=days)).isoformat()

    if start_date or end_date:
        query["published_at"] = {}
        if start_date:
            query["published_at"]["$gte"] = datetime.fromisoformat(start_date)
        if end_date:
            query["published_at"]["$lte"] = datetime.fromisoformat(end_date)
```

2. Add Mongo indexes:
```python
# In MongoDB setup
await db.devotionals.create_index([("published_at", -1)])
await db.devotionals.create_index([("published_at", -1), ("category", 1)])
await db.devotionals.create_index([("likes_count", -1), ("published_at", -1)])
```

3. Write pytest test:
```python
async def test_recent_devotionals_date_filter():
    # Create devotionals with different dates
    # Query with days=30
    # Assert only recent ones returned
```

### A) Recent Devotionals - Frontend

**File:** `/opt/kasaai/apps/devotionalflow/frontend/src/pages/Browse.tsx`

**Changes:**

1. Add date range state:
```typescript
const [dateRange, setDateRange] = useState<'all' | 'week' | 'month' | 'year'>('month');
```

2. Update API call:
```typescript
const response = await apiClient.getDevotionals({
  status: 'published',
  days: dateRange === 'week' ? 7 : dateRange === 'month' ? 30 : dateRange === 'year' ? 365 : undefined,
  category: selectedCategory === 'all' ? undefined : selectedCategory,
  sort_by: sortBy as any,
  sort_order: 'desc',
  limit: 50,
});
```

3. Add UI filter buttons:
```tsx
<div className="flex gap-2">
  <Button onClick={() => setDateRange('week')}>Last 7 Days</Button>
  <Button onClick={() => setDateRange('month')}>Last 30 Days</Button>
  <Button onClick={() => setDateRange('year')}>This Year</Button>
  <Button onClick={() => setDateRange('all')}>All Time</Button>
</div>
```

4. Update apiClient method:
```typescript
// frontend/src/lib/api.ts
async getDevotionals(params?: {
  // ... existing params
  days?: number;
  start_date?: string;
  end_date?: string;
})
```

---

### B) Bookmarks - Diagnostic Steps

1. **Check Devotional.tsx bookmark toggle:**
   - Search for `bookmarkDevotional` call
   - Verify optimistic update
   - Check TanStack Query invalidation

2. **Test API directly:**
```bash
# Bookmark a devotional
curl -X POST https://freshmanna-api.ailabsafrica.com/api/v1/devotionals/{id}/bookmark \
  -H "Authorization: Bearer $TOKEN"

# Get bookmarks
curl https://freshmanna-api.ailabsafrica.com/api/v1/users/me/bookmarks \
  -H "Authorization: Bearer $TOKEN"
```

3. **Fix if needed:**
   - Add `queryClient.invalidateQueries(['bookmarks'])` after toggle
   - Add optimistic update in mutation
   - Show loading/error states

---

### C) Reading Settings - Implementation

**Backend:** Already supports `reading_preferences` in user model ✅

**Frontend Changes:**

**File:** `/opt/kasaai/apps/devotionalflow/frontend/src/pages/Profile.tsx`

Add Reading Settings section:
```tsx
{/* Reading Settings */}
<div className="space-y-4">
  <h3 className="font-semibold">Reading Preferences</h3>

  {/* Theme */}
  <div>
    <Label>Theme</Label>
    <Select value={theme} onValueChange={setTheme}>
      <SelectItem value="light">Light</SelectItem>
      <SelectItem value="dark">Dark</SelectItem>
      <SelectItem value="system">System</SelectItem>
    </Select>
  </div>

  {/* Line Height */}
  <div>
    <Label>Line Height</Label>
    <Select value={lineHeight} onValueChange={setLineHeight}>
      <SelectItem value="normal">Normal (1.5)</SelectItem>
      <SelectItem value="relaxed">Relaxed (1.75)</SelectItem>
      <SelectItem value="loose">Loose (2.0)</SelectItem>
    </Select>
  </div>

  {/* Font Size */}
  <div>
    <Label>Font Size</Label>
    <Select value={fontSize} onValueChange={setFontSize}>
      <SelectItem value="small">Small</SelectItem>
      <SelectItem value="medium">Medium</SelectItem>
      <SelectItem value="large">Large</SelectItem>
    </Select>
  </div>
</div>
```

**Apply in Reader:**
```tsx
// Devotional.tsx - reader section
<div
  className="prose"
  style={{
    fontSize: fontSize === 'small' ? '14px' : fontSize === 'large' ? '18px' : '16px',
    lineHeight: lineHeight === 'normal' ? 1.5 : lineHeight === 'relaxed' ? 1.75 : 2.0
  }}
>
  {content}
</div>
```

---

### D) Block Users - Full Implementation

**Backend File:** `/opt/kasaai/apps/devotionalflow/backend/app/routes/blocks.py` (NEW)

```python
from fastapi import APIRouter, Depends, HTTPException
from app.utils.auth import get_current_user
from app.db.mongodb import get_database
from datetime import datetime
from bson import ObjectId

router = APIRouter()

@router.post("/users/{user_id}/block")
async def block_user(
    user_id: str,
    current_user = Depends(get_current_user)
):
    """Block a user."""
    db = get_database()

    # Prevent self-blocking
    if user_id == current_user.user_id:
        raise HTTPException(400, "Cannot block yourself")

    # Check if already blocked
    existing = await db.blocks.find_one({
        "blocker_user_id": ObjectId(current_user.user_id),
        "blocked_user_id": ObjectId(user_id)
    })

    if existing:
        return {"message": "User already blocked"}

    # Create block
    await db.blocks.insert_one({
        "blocker_user_id": ObjectId(current_user.user_id),
        "blocked_user_id": ObjectId(user_id),
        "created_at": datetime.utcnow()
    })

    return {"message": "User blocked successfully"}

@router.delete("/users/{user_id}/unblock")
async def unblock_user(
    user_id: str,
    current_user = Depends(get_current_user)
):
    """Unblock a user."""
    db = get_database()

    result = await db.blocks.delete_one({
        "blocker_user_id": ObjectId(current_user.user_id),
        "blocked_user_id": ObjectId(user_id)
    })

    if result.deleted_count == 0:
        raise HTTPException(404, "Block not found")

    return {"message": "User unblocked successfully"}

@router.get("/users/me/blocked")
async def get_blocked_users(
    current_user = Depends(get_current_user)
):
    """Get list of blocked users."""
    db = get_database()

    blocks = await db.blocks.find({
        "blocker_user_id": ObjectId(current_user.user_id)
    }).to_list(length=1000)

    # Get user details for blocked users
    blocked_user_ids = [block["blocked_user_id"] for block in blocks]
    users = await db.users.find({
        "_id": {"$in": blocked_user_ids}
    }).to_list(length=1000)

    return {
        "blocks": [
            {
                "user_id": str(user["_id"]),
                "name": user.get("name"),
                "email": user.get("email"),
                "blocked_at": block["created_at"]
            }
            for block, user in zip(blocks, users)
        ]
    }
```

**Update comments.py to filter blocked users:**
```python
# In get_comments endpoint
blocked_user_ids = await db.blocks.find({
    "blocker_user_id": ObjectId(current_user.user_id)
}).distinct("blocked_user_id")

query["author_id"] = {"$nin": blocked_user_ids}
```

**Frontend UI:**
```tsx
// BlockUserButton.tsx (NEW)
const BlockUserButton = ({ userId, userName }) => {
  const mutation = useMutation({
    mutationFn: () => apiClient.blockUser(userId),
    onSuccess: () => {
      toast({ title: `${userName} has been blocked` });
      queryClient.invalidateQueries(['comments']);
    }
  });

  return (
    <DropdownMenuItem onClick={() => mutation.mutate()}>
      <Ban className="w-4 h-4 mr-2" />
      Block User
    </DropdownMenuItem>
  );
};
```

---

### E) Delete Account - Full Implementation

**Backend:** `/opt/kasaai/apps/devotionalflow/backend/app/routes/auth.py`

```python
@router.post("/me/delete")
async def delete_account(
    confirmation: str = Body(..., embed=True),
    current_user = Depends(get_current_user)
):
    """
    Delete user account permanently.
    Requires typing "DELETE" for confirmation.
    """
    db = get_database()

    # Verify confirmation
    if confirmation != "DELETE":
        raise HTTPException(400, "Must type DELETE to confirm")

    user_id = ObjectId(current_user.user_id)

    # Anonymize comments
    await db.comments.update_many(
        {"author_id": user_id},
        {"$set": {
            "author_id": None,
            "author_name": "Deleted User",
            "author_email": None
        }}
    )

    # Delete user data
    await db.bookmarks.delete_many({"user_id": user_id})
    await db.likes.delete_many({"user_id": user_id})
    await db.reading_history.delete_many({"user_id": user_id})
    await db.gamification_profiles.delete_many({"user_id": user_id})
    await db.streaks.delete_many({"user_id": user_id})
    await db.push_subscriptions.delete_many({"user_id": user_id})

    # Delete user
    await db.users.delete_one({"_id": user_id})

    logger.info(f"User account deleted: {current_user.email}")

    return {"message": "Account deleted successfully"}
```

**Frontend:** `/opt/kasaai/apps/devotionalflow/frontend/src/components/profile/DeleteAccountDialog.tsx` (NEW)

```tsx
export const DeleteAccountDialog = ({ open, onOpenChange }) => {
  const [confirmation, setConfirmation] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { logout } = useAuth();
  const navigate = useNavigate();
  const { toast } = useToast();

  const handleDelete = async () => {
    if (confirmation !== 'DELETE') {
      toast({
        title: "Invalid confirmation",
        description: "Please type DELETE to confirm",
        variant: "destructive"
      });
      return;
    }

    setIsLoading(true);

    try {
      await apiClient.deleteAccount(confirmation);

      toast({
        title: "Account deleted",
        description: "Your account has been permanently deleted"
      });

      // Logout and redirect
      await logout();
      navigate('/');
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to delete account",
        variant: "destructive"
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle className="text-destructive">Delete Account</DialogTitle>
          <DialogDescription>
            This action cannot be undone. All your data will be permanently deleted.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Warning</AlertTitle>
            <AlertDescription>
              This will permanently delete your account and all associated data.
            </AlertDescription>
          </Alert>

          <div>
            <Label htmlFor="confirmation">Type DELETE to confirm</Label>
            <Input
              id="confirmation"
              value={confirmation}
              onChange={(e) => setConfirmation(e.target.value)}
              placeholder="DELETE"
            />
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button
            variant="destructive"
            onClick={handleDelete}
            disabled={isLoading || confirmation !== 'DELETE'}
          >
            {isLoading && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
            Delete My Account
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
```

---

## TESTING REQUIREMENTS

### Backend Tests

**File:** `/opt/kasaai/apps/devotionalflow/backend/tests/test_features.py` (NEW)

```python
# A) Test recent devotionals date filter
async def test_recent_devotionals_filters_by_date():
    # Create devotionals with dates: 10 days ago, 20 days ago, 40 days ago
    # Query with days=30
    # Assert only 10d and 20d returned, not 40d

# B) Test bookmarks unique behavior
async def test_bookmark_prevents_duplicates():
    # Bookmark same devotional twice
    # Assert only one bookmark exists

# C) Test block filtering on comments
async def test_blocked_users_filtered_from_comments():
    # User A blocks User B
    # User B comments on devotional
    # User A gets comments
    # Assert User B's comment not in results

# D) Test delete account anonymization
async def test_delete_account_anonymizes_comments():
    # User creates comments
    # User deletes account
    # Assert comments still exist with author_name="Deleted User"
```

### Frontend Manual QA Checklist

#### Recent Devotionals
- [ ] Navigate to /browse
- [ ] Click "Last 30 Days" filter
- [ ] Verify only devotionals from last 30 days shown
- [ ] Try "Last 7 Days" - verify only week shown
- [ ] Combine with category filter - verify both work

#### Bookmarks
- [ ] View a devotional
- [ ] Click bookmark icon
- [ ] Verify icon changes to filled state
- [ ] Navigate to /bookmarks
- [ ] Verify devotional appears in list
- [ ] Click bookmark again to remove
- [ ] Verify removed from list

#### Reading Settings
- [ ] Go to Profile → Settings
- [ ] Change theme to Dark
- [ ] Verify reader page uses dark theme
- [ ] Change line height to Loose
- [ ] Open devotional, verify text has 2.0 line height
- [ ] Change font size to Large
- [ ] Verify text is larger

#### Block Users
- [ ] View comment on devotional
- [ ] Click "..." menu → Block User
- [ ] Verify comment disappears
- [ ] Go to Settings → Blocked Users
- [ ] Verify user in list
- [ ] Click Unblock
- [ ] Refresh devotional, verify comment reappears

#### Delete Account
- [ ] Go to Profile → Settings
- [ ] Scroll to bottom → Delete Account
- [ ] Click button
- [ ] Warning dialog appears
- [ ] Type "DELETE" in confirmation
- [ ] Click Delete My Account
- [ ] Verify redirected to homepage
- [ ] Verify cannot log in with old credentials

---

## HOW TO TEST SAFELY

### Local Testing
1. Use dev database, not production
2. Create test user accounts
3. Test each feature in isolation
4. Run pytest suite before deploying

### Production Testing
1. Deploy to staging first
2. Test with real admin account
3. Monitor error logs
4. Use feature flags if possible

### Rollback Plan
- Keep previous version running
- If critical bug found, rollback immediately
- Fix in dev, re-deploy when stable

---

## DELIVERABLES SUMMARY

✅ **1. Diagnosis Summary**
- All 5 bugs diagnosed with exact file paths
- Root causes identified
- Current vs expected behavior documented

✅ **2. Implementation Plan**
- Ordered by impact and risk
- Detailed code changes for each bug
- Backend + Frontend for each feature

✅ **3. Code Changes**
- File lists provided
- Key functions identified
- Code examples provided

✅ **4. Testing Plan**
- pytest tests for backend
- Manual QA checklist for frontend
- Safe deployment strategy

---

## ESTIMATED EFFORT

| Feature | Backend | Frontend | Testing | Total |
|---------|---------|----------|---------|-------|
| Recent Devotionals | 1.5h | 1h | 0.5h | **3h** |
| Bookmarks Fix | 0h | 1h | 1h | **2h** |
| Reading Settings | 0h | 2h | 1h | **3h** |
| Block Users | 3h | 2h | 1h | **6h** |
| Delete Account | 2h | 1.5h | 0.5h | **4h** |
| **TOTAL** | **6.5h** | **7.5h** | **4h** | **18h** |

**Recommended:** Ship in 3 PRs over 1 week
- PR #1: Recent Devotionals + Bookmarks (Day 1-2)
- PR #2: Reading Settings + Block Users (Day 3-4)
- PR #3: Delete Account (Day 5-6)

---

**END OF DIAGNOSIS & IMPLEMENTATION PLAN**
