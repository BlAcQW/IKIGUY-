# Database Fixes and Migrations

## 2025-11-03: Dropped qr_code unique index

**Issue**: Conference registration was failing with 500 error due to duplicate key constraint on `qr_code` field.

**Error**:
```
pymongo.errors.DuplicateKeyError: E11000 duplicate key error collection: churchflow.conference_registrations index: qr_code_1 dup key: { qr_code: null }
```

**Root Cause**:
- The `conference_registrations` collection had a unique index on `qr_code` field
- Registration documents don't store the `qr_code` field (it's generated on-demand in API responses)
- Multiple registrations with `null` qr_code values violated the unique constraint

**Fix Applied**:
```javascript
db.conference_registrations.dropIndex('qr_code_1')
```

**Result**: Registrations now work successfully. QR codes are still generated on-demand when fetching registration data through the API.

**Verification**:
```bash
# Test registration creation
curl -X POST http://localhost:30030/api/v1/registrations/ \
  -H "Content-Type: application/json" \
  -d '{
    "conference_id": "68fbc116ca541168d5ea195e",
    "user_phone": "+233123456789",
    "user_name": "Test User",
    "user_email": "test@example.com",
    "branch_id": "68fbc116ca541168d5ea1954",
    "requires_bus": false,
    "special_needs": "None",
    "emergency_contact": "+233987654321"
  }'
```

---

## 2025-11-03: Fixed user_id indexes and created proper unique constraint

**Issue**: Registration still failing with 500 error due to duplicate key on `user_id` field.

**Error**:
```
pymongo.errors.DuplicateKeyError: E11000 duplicate key error collection: churchflow.conference_registrations index: user_id_1_conference_id_1 dup key: { user_id: null, conference_id: ObjectId('...') }
```

**Root Cause**:
- The code uses `user_phone` field to identify users, not `user_id`
- Old indexes were created with `user_id` field which doesn't exist in documents
- Multiple registrations with `user_id: null` violated the unique constraint

**Fixes Applied**:
```javascript
// Drop incorrect indexes
db.conference_registrations.dropIndex('user_id_1_conference_id_1')
db.conference_registrations.dropIndex('user_id_1')

// Create correct unique index based on actual schema
db.conference_registrations.createIndex(
  {user_phone: 1, conference_id: 1},
  {unique: true}
)
```

**Final Indexes**:
```javascript
[
  { v: 2, key: { _id: 1 }, name: '_id_' },
  { v: 2, key: { conference_id: 1 }, name: 'conference_id_1' },
  { v: 2, key: { user_phone: 1, conference_id: 1 }, name: 'user_phone_1_conference_id_1', unique: true }
]
```

**Verification**:
```bash
# Successfully created test registration
curl -X POST http://localhost:30030/api/v1/registrations/ \
  -H "Content-Type: application/json" \
  -d '{
    "conference_id": "68fbc116ca541168d5ea195e",
    "user_phone": "+233999888777",
    "user_name": "Test User",
    "user_email": "test@example.com",
    "branch_id": "68fbc116ca541168d5ea1955",
    "requires_bus": true,
    "bus_route_id": "68fbc116ca541168d5ea1960",
    "special_needs": "None",
    "emergency_contact": "+233111222333"
  }'
```

**Result**:
- ✅ Registrations now work successfully
- ✅ Duplicate phone+conference combinations are properly prevented
- ✅ Users can register for different conferences
- ✅ Same conference cannot have duplicate registrations from same phone

---

## 2025-11-03: Fixed database initialization code to match actual schema

**Issue**: Backend service failing to start due to attempting to create incorrect indexes during initialization.

**Error**:
```
pymongo.errors.DuplicateKeyError: Index build failed ... caused by :: E11000 duplicate key error collection: churchflow.conference_registrations index: qr_code_1 dup key: { qr_code: null }
```

**Root Cause**:
- The `database.py` initialization code was trying to create indexes that don't match the actual schema
- Attempted to create `qr_code` unique index (QR codes are generated on-demand, not stored)
- Attempted to create `user_id` indexes (schema uses `user_phone` field instead)
- Service was crashing on startup in an infinite restart loop

**Fix Applied**:
Updated `/opt/kasaai/apps/churchflow/backend/app/core/database.py` line 119-125:
```python
# Before (incorrect):
await db.conference_registrations.create_index("user_id")
await db.conference_registrations.create_index("conference_id")
await db.conference_registrations.create_index("qr_code", unique=True)
await db.conference_registrations.create_index(
    [("user_id", 1), ("conference_id", 1)],
    unique=True
)

# After (correct):
# Note: QR codes are generated on-demand, not stored in database
await db.conference_registrations.create_index("conference_id")
await db.conference_registrations.create_index(
    [("user_phone", 1), ("conference_id", 1)],
    unique=True
)  # Reason: Prevent duplicate registrations per phone+conference
```

**Result**:
- ✅ Backend service now starts successfully
- ✅ Database indexes match actual schema
- ✅ No more startup crashes
- ✅ Service stable and responsive
