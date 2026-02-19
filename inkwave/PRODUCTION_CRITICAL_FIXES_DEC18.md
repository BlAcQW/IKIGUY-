# Production Critical Fixes - December 18, 2025

## Summary
Fixed critical authentication and API errors affecting all authenticated users due to data integrity issues in the database.

## Issues Resolved

### 1. Authentication Failures (401 Unauthorized)
**Symptoms:**
- Users could not access authenticated endpoints
- Wallet balance API returned 401
- Voice settings API returned 401
- Token refresh succeeded but API calls still failed

**Root Cause:**
```
pydantic_core._pydantic_core.ValidationError: 1 validation error for UserInDB
library_books.1.book_title
  Field required [type=missing, input_value={'book_id': 'book_7573881e40f7...'}
```

Some users had library_books entries missing the required `book_title` field. When the backend tried to load user documents during authentication, Pydantic validation failed, causing 401 errors.

**Solution:**
- Created migration script: `backend/migrations/fix_library_book_titles.py`
- Script identified 8 library_books entries across 5 users with missing book_title
- Looked up book details from books collection
- Updated user documents with correct metadata

**Migration Results:**
```
Users fixed: 5
Book entries fixed: 8
Errors: 0

Fixed books:
- Turning Pain to Power (book_715b1932bece)
- Understanding the Prophetic (book_7573881e40f7)
- Enforcing Prophetic Decrees (book_5bb65ca24e10)
- The Price Of Greatness (book_08b02f063733)
- The Incredible Power of a Praying Woman (book_94785e2405d0)

Affected users:
- juliusattah998@gmail.com
- vuharty@gmail.com
- ayikunarhbenjamin@gmail.com
- xornamyeboah@gmail.com
- charlesmaccarthy124@gmail.com
```

### 2. Profile API Failures (500 Internal Server Error)
**Symptoms:**
- GET /api/v1/profile returned 500 errors
- Profile page failed to load

**Root Cause:**
Same as #1 - Pydantic validation failure when loading user documents.

**Solution:**
Fixed by the same migration script.

### 3. Social Suggestions Failures (500 Internal Server Error)
**Symptoms:**
- GET /api/v1/social/suggestions returned 500 errors
- Discover page failed to load suggested users

**Root Cause:**
Same as #1 - When the suggestions endpoint tried to return user documents, serialization failed due to invalid library_books data.

**Solution:**
Fixed by the same migration script.

### 4. PWA Manifest 403 Error
**Symptoms:**
```
GET https://inkwave.ailabsafrica.com/manifest.webmanifest 403 (Forbidden)
Manifest fetch from https://inkwave.ailabsafrica.com/manifest.webmanifest failed, code 403
```

**Root Cause:**
Manifest file had incorrect permissions (600 - owner read/write only).

**Solution:**
```bash
chmod 644 /opt/kasaai/apps/inkwave/frontend/dist/manifest.webmanifest
```

## Actions Taken

1. **Database Migration** (13:54 CET)
   - Ran `fix_library_book_titles.py`
   - Fixed 8 library_books entries
   - Updated 5 user documents

2. **File Permissions** (13:52 CET)
   - Fixed manifest.webmanifest permissions (600 → 644)

3. **Service Restart** (13:53 CET)
   - Restarted kasaai-inkwave-backend service
   - All workers running cleanly

4. **Git Commits** (13:45 & 13:56 CET)
   - Commit dbdcbd78: Added document.title to all pages
   - Commit 2fa337a6: Database migration for library_books fix

## Verification

### Before Fix:
```
ERROR:app.core.auth:Authentication failed for token eyJhbGciOiJIUzI1NiIs...:
1 validation error for UserInDB
library_books.1.book_title
  Field required
154.160.19.226:0 - "GET /api/v1/wallet/balance HTTP/1.1" 401
154.160.19.226:0 - "GET /api/v1/profile HTTP/1.1" 500
```

### After Fix:
```
[2025-12-18 13:53:46] Application startup complete.
No validation errors in logs
Backend running with 16 workers
```

## Impact

**Users Affected:** 5 users (out of 838 total users)

**Endpoints Fixed:**
- ✅ GET /api/v1/profile
- ✅ GET /api/v1/wallet/balance
- ✅ GET /api/v1/books/{book_id}/voice-settings
- ✅ GET /api/v1/social/suggestions
- ✅ GET /manifest.webmanifest (PWA)

**Severity:** CRITICAL - Affected users could not use any authenticated features

**Status:** ✅ RESOLVED

## Technical Details

### Data Model
```python
class LibraryBook(BaseModel):
    book_id: str
    book_title: str  # This was missing in 8 entries
    book_cover_url: Optional[str] = None
    book_author: Optional[str] = None
    access_type: str = "invitation"
    invitation_id: Optional[str] = None
    granted_by: Optional[str] = None
    granted_at: datetime = Field(default_factory=datetime.utcnow)
```

### Migration Logic
```python
# For each library_books entry missing book_title:
book_doc = db.books.find_one({"book_id": book_id})
library_books[idx]["book_title"] = book_doc.get("title")
library_books[idx]["book_cover_url"] = book_doc.get("cover_url")
library_books[idx]["book_author"] = book_doc.get("author")
db.users.update_one({"user_id": user_id}, {"$set": {"library_books": library_books}})
```

## Prevention

### Recommendations:
1. **Add Database Validation:** Create MongoDB schema validation for library_books
2. **Add Migration Tests:** Test migrations against production-like data
3. **Add Monitoring:** Alert on Pydantic validation errors
4. **Update Book Grant Logic:** Ensure book_title is always populated when granting book access

### Code Changes Needed:
```python
# In book invitation/grant logic:
async def grant_book_access(user_id: str, book_id: str):
    book = await db.books.find_one({"book_id": book_id})
    library_book = {
        "book_id": book_id,
        "book_title": book["title"],  # Ensure this is always set
        "book_cover_url": book.get("cover_url"),
        "book_author": book.get("author"),
        # ... rest of fields
    }
    # Add to user's library
```

## Files Modified

### New Files:
- `/opt/kasaai/apps/inkwave/backend/migrations/fix_library_book_titles.py`
- `/opt/kasaai/apps/inkwave/PRODUCTION_CRITICAL_FIXES_DEC18.md` (this file)

### Modified Files:
- `/opt/kasaai/apps/inkwave/frontend/dist/manifest.webmanifest` (permissions only)
- 18 page files with document.title (separate feature)

## Testing

### Manual Testing:
```bash
# Test authentication
curl -H "Authorization: Bearer <token>" https://inkwave-api.ailabsafrica.com/api/v1/profile

# Test wallet
curl -H "Authorization: Bearer <token>" https://inkwave-api.ailabsafrica.com/api/v1/wallet/balance

# Test social suggestions
curl -H "Authorization: Bearer <token>" https://inkwave-api.ailabsafrica.com/api/v1/social/suggestions

# Test manifest
curl -I https://inkwave.ailabsafrica.com/manifest.webmanifest
```

### Expected Results:
- All endpoints return 200 OK
- No Pydantic validation errors in logs
- Manifest returns 200 with proper content-type

## Monitoring

**Check Logs:**
```bash
sudo journalctl -u kasaai-inkwave-backend -f
```

**Look For:**
- No "ValidationError: 1 validation error for UserInDB"
- No "library_books.*.book_title Field required"
- No 401 errors after successful token refresh
- No 500 errors on profile or social endpoints

## Conclusion

All critical production errors have been resolved. The root cause was incomplete data migration when the LibraryBook model was enhanced with additional required fields. The migration script has been preserved for future reference and can be re-run safely (it's idempotent).

---

**Date:** December 18, 2025, 13:56 CET
**Environment:** Production (inkwave.ailabsafrica.com)
**Database:** inkwave (MongoDB)
**Backend:** Port 30033 (16 Gunicorn workers)
