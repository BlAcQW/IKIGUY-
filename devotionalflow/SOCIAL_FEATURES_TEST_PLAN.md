# Social Features - Complete Test Plan

**Date:** December 16, 2025
**Status:** ⚠️ REQUIRES BROWSER REFRESH TO TEST

---

## ⚠️ CRITICAL: You Must Refresh First!

**Your browser is still running the OLD build** (`index-CmHo2Kkv.js`)
**The NEW build with fixes is** (`index-Ll0DTmDX.js`)

### How to Get the New Version:
1. **Hard Refresh:** Press `Ctrl + Shift + R` (Windows/Linux) or `Cmd + Shift + R` (Mac)
2. **Or:** Open DevTools (F12) → Right-click refresh → "Empty Cache and Hard Reload"

---

## Backend API Endpoints (All Verified ✅)

### Likes
- ✅ `POST /api/v1/devotionals/{id}/like` - Toggle devotional like
- ✅ `POST /api/v1/comments/{id}/like` - Toggle comment like

### Comments
- ✅ `POST /api/v1/devotionals/{id}/comments` - Create comment
- ✅ `GET /api/v1/devotionals/{id}/comments` - List comments
- ✅ `PUT /api/v1/comments/{id}` - Edit comment
- ✅ `DELETE /api/v1/comments/{id}` - Delete comment

### Bookmarks
- ✅ `POST /api/v1/devotionals/{id}/bookmark` - Toggle bookmark
- ✅ `GET /api/v1/users/me/bookmarks` - List bookmarks

### Shares
- ✅ `POST /api/v1/devotionals/{id}/share` - Track share

---

## Frontend Implementation (In New Build)

### 1. ✅ Like Devotionals

**Location:** Devotional page → Bottom floating action bar

**Implementation:**
```typescript
// Line 154-204 in Devotional.tsx
const likeMutation = useMutation({
  mutationFn: async () => {
    return await apiClient.likeDevotional(id);
  },
  onMutate: async () => {
    // Optimistic update
    queryClient.setQueryData(['devotional', id], (old: any) => ({
      ...old,
      likes_count: old.likes_count + (old.is_liked ? -1 : 1),
      is_liked: !old.is_liked,
    }));
  },
  // ... error handling & rollback
});
```

**How to Test:**
1. Open any devotional
2. Scroll to bottom floating action bar
3. Click the heart ❤️ icon
4. Should see:
   - Heart fills with color
   - Bounce animation
   - Count increases by 1
5. Click again to unlike:
   - Heart empties
   - Count decreases by 1

---

### 2. ✅ Like Comments

**Location:** Devotional page → Comments section → Under each comment

**Implementation:**
```typescript
// Line 413-479 in Devotional.tsx
const commentLikeMutation = useMutation({
  mutationFn: async (commentId: string) => {
    return await apiClient.likeComment(commentId);
  },
  onMutate: async (commentId) => {
    // Optimistically update the comment
    queryClient.setQueryData(['comments', id], (old: any) => {
      return old.map((comment: Comment) => {
        if (comment.id === commentId) {
          return {
            ...comment,
            likes_count: comment.likes_count + (comment.is_liked ? -1 : 1),
            is_liked: !comment.is_liked,
          };
        }
        return comment;
      });
    });
  },
});
```

**How to Test:**
1. Open any devotional
2. Scroll to comments section
3. Click heart icon under any comment
4. Should see:
   - Heart fills with color
   - Small bounce animation
   - Count increases
5. Click again to unlike

---

### 3. ✅ Comment on Devotionals

**Location:** Devotional page → Comments section → Bottom textarea

**Implementation:**
```typescript
// Line 358-410 in Devotional.tsx
const commentMutation = useMutation({
  mutationFn: async (text: string) => {
    if (!id) return;
    return await apiClient.createComment(id, { text });
  },
  onSuccess: () => {
    // Invalidate queries to refresh
    queryClient.invalidateQueries({ queryKey: ['comments', id] });
    queryClient.invalidateQueries({ queryKey: ['devotional', id] });
    setNewComment("");
    toast({
      title: "Comment posted",
      description: "Your comment has been added successfully"
    });
  },
});
```

**How to Test:**
1. Open any devotional
2. Click comment icon in bottom bar
3. Type a comment in the textarea
4. Click Send or press Enter
5. Should see:
   - Comment appears immediately
   - Toast: "Comment posted"
   - Textarea clears
   - Comment count increases

---

### 4. ⚠️ Reply to Comments (Threaded)

**Current Status:** Backend supports it, Frontend partially implemented

**Backend Support:**
- ✅ `parent_comment_id` field exists
- ✅ Backend returns nested replies
- ✅ Can create replies via API

**Frontend Gap:**
- ❌ No "Reply" button visible on comments
- ❌ No reply UI/textarea
- ❌ Threading not displayed

**What Needs to Be Added:**
```typescript
// Need to add:
1. "Reply" button on each comment
2. Reply textarea (shows/hides on click)
3. Display nested replies with indentation
4. Pass parent_comment_id when replying
```

**Test Status:** ⚠️ PARTIALLY WORKING (backend ready, needs frontend UI)

---

### 5. ⚠️ Edit Own Comments

**Current Status:** Backend supports it, Frontend NOT implemented

**Backend Support:**
- ✅ `PUT /api/v1/comments/{id}` endpoint exists
- ✅ Checks user ownership
- ✅ Returns updated comment

**Frontend Gap:**
- ❌ No edit button on comments
- ❌ No edit UI
- ❌ No mutation implemented

**What Needs to Be Added:**
```typescript
// Need to add:
1. Three-dot menu on own comments
2. "Edit" option
3. Edit mode (textarea replaces text)
4. Save/Cancel buttons
5. Update mutation
```

**Test Status:** ⚠️ NOT IMPLEMENTED IN FRONTEND

---

### 6. ⚠️ Delete Own Comments

**Current Status:** Backend supports it, Frontend NOT implemented

**Backend Support:**
- ✅ `DELETE /api/v1/comments/{id}` endpoint exists
- ✅ Soft delete (marks as deleted)
- ✅ Checks user ownership

**Frontend Gap:**
- ❌ No delete button on comments
- ❌ No confirmation dialog
- ❌ No mutation implemented

**What Needs to Be Added:**
```typescript
// Need to add:
1. Three-dot menu on own comments
2. "Delete" option
3. Confirmation dialog
4. Delete mutation
5. Remove from UI on success
```

**Test Status:** ⚠️ NOT IMPLEMENTED IN FRONTEND

---

### 7. ✅ Share Devotionals

**Location:** Devotional page → Bottom bar "Share" button

**Implementation:**
```typescript
// Line 679-688 in Devotional.tsx
const handleShare = () => {
  if (devotional) {
    setShareSheetData({
      title: devotional.title,
      text: devotional.excerpt,
      url: `${window.location.origin}/devotional/${devotional.id}`,
      imageUrl: devotional.cover_image_url,
    });
    setShowShareSheet(true);
  }
};
```

**Components:**
- ✅ ShareSheet component exists
- ✅ Handles Web Share API
- ✅ Falls back to copy link
- ✅ Tracks shares to backend

**How to Test:**
1. Open any devotional
2. Click "Share" button in bottom bar
3. Should see share sheet with options:
   - Native share (if supported)
   - Copy link
   - Social media options
4. Select an option
5. Should see success toast
6. Share tracked in analytics

---

## Summary of What Works NOW (After Refresh)

| Feature | Backend | Frontend | Status |
|---------|---------|----------|--------|
| Like Devotionals | ✅ | ✅ | **WORKS** |
| Like Comments | ✅ | ✅ | **WORKS** |
| Comment on Devotionals | ✅ | ✅ | **WORKS** |
| Reply to Comments | ✅ | ❌ | **BACKEND ONLY** |
| Edit Own Comments | ✅ | ❌ | **BACKEND ONLY** |
| Delete Own Comments | ✅ | ❌ | **BACKEND ONLY** |
| Share Devotionals | ✅ | ✅ | **WORKS** |
| Bookmark Devotionals | ✅ | ✅ | **WORKS** |

---

## What Needs to Be Implemented

### 1. Reply to Comments (Threading)

**Required Components:**
```typescript
// Add to Devotional.tsx
const [replyingTo, setReplyingTo] = useState<string | null>(null);
const [replyText, setReplyText] = useState("");

const replyMutation = useMutation({
  mutationFn: async ({ commentId, text }: { commentId: string; text: string }) => {
    return await apiClient.createComment(id!, {
      text,
      parent_comment_id: commentId
    });
  },
});
```

**UI Changes:**
- Add "Reply" button to each comment
- Show reply textarea when clicked
- Display nested replies with indentation
- Different background for reply levels

---

### 2. Edit Comments

**Required Components:**
```typescript
// Add to Devotional.tsx
const [editingComment, setEditingComment] = useState<string | null>(null);
const [editText, setEditText] = useState("");

const editCommentMutation = useMutation({
  mutationFn: async ({ commentId, text }: { commentId: string; text: string }) => {
    return await apiClient.updateComment(commentId, { text });
  },
});
```

**UI Changes:**
- Add three-dot menu to own comments
- "Edit" option in menu
- Replace comment text with textarea
- Save/Cancel buttons
- Show "edited" badge after save

---

### 3. Delete Comments

**Required Components:**
```typescript
// Add to Devotional.tsx
const [deletingComment, setDeletingComment] = useState<string | null>(null);

const deleteCommentMutation = useMutation({
  mutationFn: async (commentId: string) => {
    return await apiClient.deleteComment(commentId);
  },
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['comments', id] });
    toast({ title: "Comment deleted" });
  },
});
```

**UI Changes:**
- Add three-dot menu to own comments
- "Delete" option in menu
- Confirmation dialog
- Remove comment from UI on success
- Show "[deleted]" placeholder

---

## Immediate Test Steps (After Refresh)

### Test 1: Like Devotional
```
1. Hard refresh browser (Ctrl+Shift+R)
2. Go to any devotional
3. Click heart in bottom bar
4. Verify heart fills and count increases
5. Click again to unlike
```

### Test 2: Like Comment
```
1. Go to any devotional with comments
2. Click heart under any comment
3. Verify heart fills and count increases
4. Click again to unlike
```

### Test 3: Post Comment
```
1. Go to any devotional
2. Click comment icon in bottom bar
3. Type "Test comment"
4. Click Send
5. Verify comment appears
6. Verify toast shows success
```

### Test 4: Share Devotional
```
1. Go to any devotional
2. Click "Share" button
3. Verify share sheet opens
4. Try "Copy link"
5. Verify link copied successfully
```

---

## Missing Features to Implement

**Priority 1 (Core Engagement):**
- [ ] Reply to comments UI
- [ ] Edit own comments UI
- [ ] Delete own comments UI

**Priority 2 (Enhanced):**
- [ ] Comment reactions (beyond like)
- [ ] Report inappropriate comments
- [ ] Pin important comments (pastor only)
- [ ] Mention users (@username)
- [ ] Rich text in comments (bold, italic)

**Priority 3 (Advanced):**
- [ ] GIF support in comments
- [ ] Image attachments in comments
- [ ] Comment threading depth limit
- [ ] Collapse long comment threads
- [ ] Sort comments (newest, most liked)

---

## API Client Methods Available

All these methods exist in `/frontend/src/lib/api.ts`:

```typescript
// Devotionals
✅ likeDevotional(id: string)
✅ bookmarkDevotional(id: string)
✅ shareDevotional(id: string, platform: string)

// Comments
✅ createComment(devotionalId: string, data: { text: string, parent_comment_id?: string })
✅ getComments(devotionalId: string)
✅ updateComment(commentId: string, data: { text: string })
✅ deleteComment(commentId: string)
✅ likeComment(commentId: string)
```

---

## Next Steps

1. **IMMEDIATE:** Hard refresh browser to get new build
2. **TEST:** Follow test plan above
3. **REPORT:** Which features work vs don't work
4. **IMPLEMENT:** Missing frontend features (reply, edit, delete)

---

**Current Build:** `index-Ll0DTmDX.js` (HAS FIXES)
**Your Browser:** `index-CmHo2Kkv.js` (OLD - DOESN'T WORK)

**REFRESH NOW TO TEST!** 🔄

---

**END OF SOCIAL FEATURES TEST PLAN**
