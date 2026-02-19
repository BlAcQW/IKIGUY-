# ChurchFlow MongoDB Index Fix

**Date:** 2025-11-03
**Issue:** Registration endpoint returning 500 Internal Server Error
**Status:** ✅ FIXED

---

## Problem

The ChurchFlow registration endpoint (`POST /api/v1/registrations/`) was failing with a 500 error:

```
pymongo.errors.DuplicateKeyError: E11000 duplicate key error collection:
churchflow.conference_registrations index: user_id_1_conference_id_1
dup key: { user_id: null, conference_id: ObjectId('68fbc116ca541168d5ea195e') }
```

### Root Cause

The `user_id + conference_id` composite index in the `conference_registrations` collection had a **unique sparse index**. However, **MongoDB sparse indexes still include documents with explicit `null` values** - they only exclude documents where the field is completely missing.

This caused issues for anonymous registrations:
- ✅ First registration with `user_id: null` → Success
- ❌ Second registration with `user_id: null` for same conference → Duplicate key error

**Key MongoDB Behavior:**
- **Sparse index**: Excludes documents where the field is missing, BUT includes documents with `null` values
- **PartialFilterExpression**: Can exclude documents based on type checks, properly excluding both missing AND null values

---

## Solution

Changed from **sparse indexes** to **partialFilterExpression** indexes using `$type: "string"`:

```javascript
// Drop old sparse indexes
db.conference_registrations.dropIndex('user_id_1_conference_id_1');
db.conference_registrations.dropIndex('user_phone_1_conference_id_1');
db.conference_registrations.dropIndex('qr_code_1');

// Create new partial filter indexes
db.conference_registrations.createIndex(
  { user_id: 1, conference_id: 1 },
  {
    unique: true,
    partialFilterExpression: { user_id: { $type: "string" } }
  }
);

db.conference_registrations.createIndex(
  { user_phone: 1, conference_id: 1 },
  {
    unique: true,
    partialFilterExpression: { user_phone: { $type: "string" } }
  }
);

db.conference_registrations.createIndex(
  { qr_code: 1 },
  {
    unique: true,
    partialFilterExpression: { qr_code: { $type: "string" } }
  }
);
```

### What This Means

With partialFilterExpression using `$type: "string"`:
- ✅ Multiple registrations can have `user_id` missing
- ✅ Multiple registrations can have `user_id: null`
- ✅ Non-null user_id values must still be unique per conference
- ✅ No duplicate key errors for null or missing values

---

## Commands Used

```bash
# Drop old sparse indexes
mongosh "mongodb://admin:PASSWORD@127.0.0.1:27017/" --eval "
  db.getSiblingDB('churchflow').conference_registrations.dropIndex('user_id_1_conference_id_1');
  db.getSiblingDB('churchflow').conference_registrations.dropIndex('user_phone_1_conference_id_1');
  db.getSiblingDB('churchflow').conference_registrations.dropIndex('qr_code_1');
"

# Restart backend to recreate indexes with partialFilterExpression
sudo systemctl restart kasaai-churchflow-backend
```

The indexes are automatically recreated by the backend application using partialFilterExpression as defined in `/opt/kasaai/apps/churchflow/backend/app/core/database.py:134-148`.

---

## Verification

### Before Fix
```
POST /api/v1/registrations/
Status: 500 Internal Server Error
Error: DuplicateKeyError on user_id: null, conference_id: ObjectId('...')
```

### After Fix
```
POST /api/v1/registrations/ (1st anonymous registration)
Status: 201 Created
Response: {
  "registration_code": "REG-UL93ZQFLZQQ",
  "user_name": "Test User 1762200350399",
  "user_phone": "+2331762200350399",
  "status": "confirmed"
}

POST /api/v1/registrations/ (2nd anonymous registration for same conference)
Status: 201 Created
Response: {
  "registration_code": "REG-YU6L6GIQFDC",
  "user_name": "Test User 1762200356639",
  "user_phone": "+2331762200356639",
  "status": "confirmed"
}
```

✅ **Registration endpoint working correctly**
✅ **Multiple anonymous registrations for same conference now working**

---

## Current Indexes

```javascript
[
  { v: 2, key: { _id: 1 }, name: '_id_' },
  { v: 2, key: { user_id: 1 }, name: 'user_id_1' },
  { v: 2, key: { conference_id: 1 }, name: 'conference_id_1' },
  {
    v: 2,
    key: { user_id: 1, conference_id: 1 },
    name: 'user_id_1_conference_id_1',
    unique: true,
    partialFilterExpression: { user_id: { '$type': 'string' } }  // ✅ Now using partialFilterExpression
  },
  {
    v: 2,
    key: { user_phone: 1, conference_id: 1 },
    name: 'user_phone_1_conference_id_1',
    unique: true,
    partialFilterExpression: { user_phone: { '$type': 'string' } }  // ✅ Now using partialFilterExpression
  },
  {
    v: 2,
    key: { qr_code: 1 },
    name: 'qr_code_1',
    unique: true,
    partialFilterExpression: { qr_code: { '$type': 'string' } }  // ✅ Now using partialFilterExpression
  }
]
```

---

## Best Practices

### Sparse Indexes vs PartialFilterExpression

**Sparse Indexes:**
- Exclude documents where the field is **missing**
- ⚠️ **Still include documents where the field is explicitly `null`**
- Good for: Optional fields that rarely contain values

**PartialFilterExpression with `$type: "string"`:**
- Exclude documents where the field is **missing OR null OR not a string**
- ✅ **Only include documents where the field has an actual string value**
- Better for: Unique constraints on optional fields (e.g., user_id, email, phone)

### When to Use Each Approach

Use **partialFilterExpression** when:
- ✅ You want uniqueness only for documents with actual values (not null)
- ✅ Field may be null, missing, or have a value
- ✅ Anonymous/guest records should be allowed without conflicts

Use **sparse indexes** when:
- ✅ Field may be missing but if present should always have a value (never null)
- ✅ You want to include null values in the unique constraint

Use **regular indexes** when:
- ✅ Field must always have a value
- ✅ Field is required in your schema
- ✅ You want to enforce "only one null" constraint

---

## Related Collections

This same pattern may apply to other collections with unique indexes on optional fields. Review:

- `members` collection - email, phone fields
- `events` collection - registration_link field  
- `donations` collection - receipt_url field

---

**Fixed By:** AI Labs Africa Platform Team
**Production Server:** 148.251.0.46 (Live)
**Database:** MongoDB churchflow
