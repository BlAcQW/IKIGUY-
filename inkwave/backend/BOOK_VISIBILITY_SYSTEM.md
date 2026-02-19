# Book Visibility & Access Control System

## Overview

InkWave now includes a comprehensive book visibility and access control system that allows authors to control who can see their books, and gives admins powerful moderation tools.

## Features

### For Authors
- **4 Visibility States**: draft, unlisted, private, public
- **Default Privacy**: All uploaded books start as "private"
- **Easy Publishing**: Authors can change visibility to make books discoverable
- **Upload Feedback**: Authors see their hidden books with an admin badge

### For Users
- **Browse Public Books**: Discover books in the "All Books" section
- **Add to Library**: Explicitly add public books to your library
- **Private Invitations**: Continue to receive private book invitations

### For Admins
- **Hide Books**: Soft-delete inappropriate content (visible to uploader with badge)
- **Restore Books**: Unhide previously hidden books
- **Soft Delete**: Mark books as deleted (can be restored)
- **Permanent Delete**: Complete removal (cannot be undone)
- **Full Audit Trail**: All actions logged with reason and timestamp

## Visibility States

### Draft
- **Who sees it**: Only the uploader
- **Use case**: Book is incomplete or still processing
- **Discovery**: Not in "All Books" listing

### Unlisted
- **Who sees it**: Anyone with the direct link
- **Use case**: Share privately without discovery
- **Discovery**: Not in "All Books" listing

### Private (Default)
- **Who sees it**: Only users who have it in their library (via invitation)
- **Use case**: Personal books, church-specific content
- **Discovery**: Not in "All Books" listing

### Public
- **Who sees it**: Everyone
- **Use case**: Books meant for wide distribution
- **Discovery**: Appears in "All Books" listing
- **Library**: Users can add to their library with one click

## API Endpoints

### Author/User Endpoints

#### Change Book Visibility
```http
PATCH /api/v1/books/{book_id}/visibility?visibility=public
Authorization: Bearer <token>
```

**Visibility Values**: `draft`, `unlisted`, `private`, `public`

**Response**:
```json
{
  "success": true,
  "message": "Book visibility updated to 'public'",
  "book_id": "book_abc123",
  "visibility": "public"
}
```

**Permissions**: Only the book uploader or admin can change visibility

**Audit Log**: Creates an audit log entry for the visibility change

#### Add Public Book to Library
```http
POST /api/v1/books/{book_id}/add-to-library
Authorization: Bearer <token>
```

**Response**:
```json
{
  "success": true,
  "message": "'Book Title' added to your library",
  "book_id": "book_abc123"
}
```

**Requirements**:
- Book must be public
- User must be authenticated
- Book not already in library

### Admin Moderation Endpoints

#### Hide a Book
```http
POST /admin/books/{book_id}/hide?reason=Inappropriate+content
Authorization: Bearer <admin_token>
```

**Parameters**:
- `reason` (required, min 10 characters): Reason for hiding

**Response**:
```json
{
  "success": true,
  "message": "Book hidden successfully",
  "book_id": "book_abc123",
  "reason": "Inappropriate content"
}
```

**Effect**:
- Book hidden from public listings
- Uploader sees book with "Hidden by Admin: [reason]" badge
- Creates audit log entry

#### Unhide a Book
```http
POST /admin/books/{book_id}/unhide?reason=Issue+resolved
Authorization: Bearer <admin_token>
```

**Parameters**:
- `reason` (optional): Reason for unhiding

**Response**:
```json
{
  "success": true,
  "message": "Book unhidden successfully",
  "book_id": "book_abc123"
}
```

#### Permanently Delete a Book
```http
DELETE /admin/books/{book_id}/permanent?reason=Spam+content&confirm=true
Authorization: Bearer <admin_token>
```

**Parameters**:
- `reason` (required, min 10 characters): Reason for deletion
- `confirm` (required): Must be `true`

**WARNING**: This action is permanent and cannot be undone!

**Response**:
```json
{
  "success": true,
  "message": "Book permanently deleted",
  "book_id": "book_abc123",
  "warning": "This action cannot be undone"
}
```

#### List Hidden Books
```http
GET /admin/books/hidden?page=1&per_page=20
Authorization: Bearer <admin_token>
```

**Response**:
```json
{
  "books": [
    {
      "id": "book_abc123",
      "title": "Book Title",
      "author": "Author Name",
      "uploaded_by": "user_123",
      "visibility": "public",
      "hidden_by": "admin_456",
      "hidden_by_email": "admin@example.com",
      "hidden_at": "2025-12-05T10:30:00Z",
      "hidden_reason": "Inappropriate content"
    }
  ],
  "total": 5,
  "page": 1,
  "per_page": 20
}
```

#### Get Audit Log
```http
GET /admin/audit-log?book_id=book_abc123&limit=50
Authorization: Bearer <admin_token>
```

**Query Parameters**:
- `book_id` (optional): Filter by book ID
- `admin_id` (optional): Filter by admin user ID
- `action` (optional): Filter by action type
- `limit` (default: 50, max: 500): Number of records

**Response**:
```json
{
  "logs": [
    {
      "audit_id": "audit_xyz789",
      "action": "visibility_changed",
      "entity_id": "book_abc123",
      "actor_id": "user_123",
      "actor_email": "user@example.com",
      "actor_role": "user",
      "reason": null,
      "changes": {
        "visibility": {
          "before": "private",
          "after": "public"
        }
      },
      "metadata": {
        "book_title": "Book Title",
        "book_author": "Author Name"
      },
      "created_at": "2025-12-05T10:15:00Z"
    }
  ],
  "total": 3,
  "filters": {
    "book_id": "book_abc123",
    "admin_id": null,
    "action": null
  }
}
```

## Database Schema

### Books Collection

New fields added to existing `books` collection:

```javascript
{
  // Visibility Control (Author-controlled)
  visibility: "private",  // "draft" | "unlisted" | "private" | "public"
  visibility_changed_at: ISODate("2025-12-05T10:15:00Z"),
  visibility_changed_by: "user_123",

  // Admin Moderation (soft hide)
  is_hidden: false,
  hidden_by: null,
  hidden_by_email: null,
  hidden_at: null,
  hidden_reason: null,

  // Soft Delete
  is_deleted: false,
  deleted_by: null,
  deleted_by_email: null,
  deleted_at: null,
  deletion_reason: null
}
```

### Audit Logs Collection

New collection `audit_logs`:

```javascript
{
  audit_id: "audit_xyz789",
  action: "visibility_changed",  // Enum: see below
  entity_type: "book",
  entity_id: "book_abc123",
  actor_id: "user_123",
  actor_email: "user@example.com",
  actor_role: "user",
  reason: null,  // Optional
  changes: {
    visibility: {
      before: "private",
      after: "public"
    }
  },
  metadata: {
    book_title: "Book Title",
    book_author: "Author Name",
    uploader_id: "user_456"
  },
  created_at: ISODate("2025-12-05T10:15:00Z")
}
```

**Audit Actions**:
- `visibility_changed` - Author/admin changed visibility
- `book_hidden` - Admin hid the book
- `book_unhidden` - Admin unhid the book
- `book_deleted` - Admin soft-deleted the book
- `book_restored` - Admin restored a deleted book
- `book_permanently_deleted` - Admin permanently deleted the book

### Indexes

```javascript
// Books collection
db.books.createIndex({ visibility: 1 })
db.books.createIndex({ is_hidden: 1 })
db.books.createIndex({ is_deleted: 1 })
db.books.createIndex({ uploaded_by: 1, visibility: 1 })
db.books.createIndex({ visibility: 1, is_hidden: 1, is_deleted: 1 })
db.books.createIndex({ is_hidden: 1, hidden_at: -1 })

// Audit logs collection
db.audit_logs.createIndex({ entity_id: 1, created_at: -1 })
db.audit_logs.createIndex({ action: 1, created_at: -1 })
db.audit_logs.createIndex({ actor_id: 1, created_at: -1 })
```

## Migration

### Running the Migration

```bash
cd /opt/kasaai/apps/inkwave/backend
/opt/kasaai/apps/venv/bin/python scripts/migrate_book_visibility.py migrate
```

**What it does**:
1. Adds visibility, is_hidden, is_deleted fields to all existing books
2. Sets all existing books to `visibility="private"` (safe default)
3. Creates database indexes
4. Creates audit_logs collection with indexes
5. Verifies migration success

**Verification**:
```bash
/opt/kasaai/apps/venv/bin/python scripts/migrate_book_visibility.py verify
```

**Rollback** (if needed):
```bash
/opt/kasaai/apps/venv/bin/python scripts/migrate_book_visibility.py rollback
```

### Post-Migration

After migration:
1. **Restart the backend service**:
   ```bash
   sudo systemctl restart kasaai-inkwave-backend
   ```

2. **Authors can now change visibility**:
   - Authors should log in and change their books to "public" if they want them discoverable

3. **Test the system**:
   ```bash
   # Anonymous users see only public books
   curl http://localhost:30033/api/v1/books

   # Change a book to public (requires auth token)
   curl -X PATCH 'http://localhost:30033/api/v1/books/BOOK_ID/visibility?visibility=public' \
     -H "Authorization: Bearer TOKEN"
   ```

## Testing

### Unit Tests

```bash
cd /opt/kasaai/apps/inkwave/backend
/opt/kasaai/apps/venv/bin/python -m pytest tests/test_book_visibility_filtering.py -v
```

Tests the core visibility filtering logic without database.

### Integration Tests

```bash
/opt/kasaai/apps/venv/bin/python -m pytest tests/test_book_visibility_api.py -v -s
```

Tests with real database:
- Visibility changes
- Book listing with filtering
- Admin moderation actions
- Audit log creation

### Audit Log CRUD Tests

```bash
/opt/kasaai/apps/venv/bin/python -m pytest tests/test_audit_log_crud.py -v -s
```

Tests audit log service CRUD operations with real data.

## Permission Matrix

| Visibility | Anonymous | User | Owner | Admin |
|------------|-----------|------|-------|-------|
| **Draft** | ❌ | ❌ | ✅ | ✅ |
| **Unlisted** | ✅ (with link) | ✅ (with link) | ✅ | ✅ |
| **Private** | ❌ | ✅ (if in library) | ✅ | ✅ |
| **Public** | ✅ | ✅ | ✅ | ✅ |
| **Hidden** | ❌ | ❌ | ✅ (with badge) | ✅ |
| **Deleted** | ❌ | ❌ | ❌ | ✅ |

## Backward Compatibility

- **Existing invitation system**: Unchanged - continues to work
- **User library_books array**: Unchanged - continues to work
- **Existing books**: Migrated to `visibility="private"` (safe default)
- **Hard delete endpoint**: Still available for authors (DELETE /books/{id})
- **New permanent delete**: Admin-only endpoint

## Best Practices

### For Authors

1. **Start Private**: All uploads start as private by default
2. **Review Before Publishing**: Check your book before making it public
3. **Use Unlisted**: Share with specific users via link without public discovery
4. **Respect Hidden Status**: If admin hides your book, review the reason

### For Admins

1. **Always Provide Reason**: Required for hide/delete actions
2. **Use Soft Delete First**: Can be undone if mistake
3. **Permanent Delete Rarely**: Only for serious violations
4. **Monitor Audit Log**: Regular reviews of moderation actions
5. **Communicate**: Inform uploaders about moderation actions

## Troubleshooting

### Book Not Appearing

1. **Check visibility**: Book must be `public` to appear in "All Books"
2. **Check hidden status**: `is_hidden=true` hides from non-admin users
3. **Check deleted status**: `is_deleted=true` hides from non-admin users
4. **Check user role**: Only public books appear for anonymous users

### Cannot Change Visibility

1. **Permission check**: Only uploader or admin can change visibility
2. **Authentication**: Ensure valid token is provided
3. **Book exists**: Verify book_id is correct

### Audit Logs Not Created

1. **Check database connection**: Ensure MongoDB is connected
2. **Check collection exists**: Migration should create `audit_logs` collection
3. **Check indexes**: Run migration verify command

## Future Enhancements

Possible future additions:
- Scheduled publishing (set visibility to change at specific time)
- Visibility history (track all visibility changes)
- Bulk moderation actions
- Email notifications for moderation actions
- Custom visibility rules (by organization, by role, etc.)
- Visibility analytics (views by visibility state)

## Support

For issues or questions:
1. Check this documentation
2. Review audit logs for admin actions
3. Check backend logs: `sudo journalctl -u kasaai-inkwave-backend -f`
4. Test with MongoDB queries to verify data state

## Implementation Files

**Core Implementation**:
- `app/models/book.py` - Book model with visibility fields
- `app/models/audit_log.py` - Audit log model
- `app/services/book_service.py` - Visibility filtering and moderation
- `app/services/audit_log_service.py` - Audit logging service
- `app/api/routes/books.py` - Book endpoints with visibility
- `app/api/routes/admin.py` - Admin moderation endpoints

**Migration**:
- `scripts/migrate_book_visibility.py` - Database migration script

**Tests**:
- `tests/test_book_visibility_filtering.py` - Unit tests
- `tests/test_book_visibility_api.py` - Integration tests
- `tests/test_audit_log_crud.py` - Audit log CRUD tests

---

**Version**: 1.0.0
**Date**: 2025-12-05
**Status**: ✅ Implemented and Tested
