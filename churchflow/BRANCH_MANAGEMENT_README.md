# Branch Management with Geolocation Support

## Overview

Complete CRUD system for managing church branches with GPS coordinates for proximity-based auto check-in. This system replaces the previous hardcoded branch constants with a flexible MongoDB-backed solution.

---

## 🎯 What's Been Built

### 1. Backend API (`/backend/app/api/routes/branches_crud.py`)

**Complete REST API with:**

#### Read Operations
- `GET /branches/` - List all branches with filtering
  - Filter by: active status, GPS availability, region, auto check-in status
  - Pagination support
  - Sorted by name

- `GET /branches/{id}` - Get single branch details

- `GET /branches/search/nearby` - Find branches near GPS coordinate
  - Uses Haversine distance calculation
  - Returns sorted by distance (nearest first)
  - Supports max distance filtering

- `GET /branches/stats/summary` - Branch statistics
  - Total, active, inactive counts
  - GPS coordinate coverage
  - Auto check-in enabled count
  - Breakdown by region

#### Create Operation
- `POST /branches/` - Create new branch
  - Admin-only
  - Duplicate name validation
  - Full geolocation support

#### Update Operation
- `PATCH /branches/{id}` - Update existing branch
  - Admin-only
  - Partial updates (only specified fields)
  - Duplicate name validation

#### Delete Operation
- `DELETE /branches/{id}` - Delete branch
  - Admin-only
  - Soft delete by default (sets `is_active=False`)
  - Hard delete protection (checks for references)

---

### 2. Migration Script (`/backend/scripts/migrate_branches_to_db.py`)

**Migrates hardcoded branches to MongoDB**

#### Features:
- Migrates 150+ branches from `constants/branches.py` to MongoDB
- Preserves all existing branch data
- Handles updates (won't duplicate existing branches)
- Dry-run mode for testing
- Verification command
- Lists branches needing geocoding

#### Usage:

```bash
# Dry run (preview changes)
python scripts/migrate_branches_to_db.py \
  --organization-id 674e9a2b3f1234567890abcd \
  --dry-run

# Actual migration
python scripts/migrate_branches_to_db.py \
  --organization-id 674e9a2b3f1234567890abcd

# Verify migration
python scripts/migrate_branches_to_db.py \
  --organization-id 674e9a2b3f1234567890abcd \
  --verify

# List branches without GPS coordinates
python scripts/migrate_branches_to_db.py \
  --organization-id 674e9a2b3f1234567890abcd \
  --list-missing-coords
```

---

### 3. Admin UI (`/frontend/src/components/admin/BranchManagement.tsx`)

**Complete admin interface for branch management**

#### Features:

##### Dashboard View
- **Statistics Cards**: Total, active, with GPS, auto check-in enabled, etc.
- **Filtering**: By region, active status
- **Branch Table**:
  - Name, location, region
  - GPS status indicator
  - Auto check-in status
  - Check-in radius
  - Active/inactive status
  - Edit/delete actions

##### Create/Edit Modal
- **Basic Info**:
  - Branch name
  - Location description
  - Region

- **GPS Coordinates**:
  - Interactive map picker (uses existing `MapPicker` component)
  - Click to set coordinates
  - Search location by name
  - Display selected coordinates

- **Check-In Settings**:
  - Check-in radius slider (50-5000m)
  - Enable/disable auto check-in toggle
  - Active/inactive toggle

- **Info Box**: Guidance on auto check-in settings

##### Branch Statistics
- Real-time counts and percentages
- Region breakdown
- GPS coverage metrics

---

## 📊 Branch Data Model

```typescript
interface Branch {
  _id: string;
  organization_id: string;

  // Basic info
  name: string;                    // "Adenta"
  location: string;                 // "Adenta, Greater Accra, Ghana"
  region: string;                   // "Greater Accra"

  // Geolocation
  latitude: number | null;          // 5.7108
  longitude: number | null;         // -0.1673
  checkin_radius: number;           // 500 (meters)
  auto_checkin_enabled: boolean;    // true/false
  geocoding_accuracy: string | null; // "exact", "street", "city", etc.

  // Service schedule
  service_times: ServiceSchedule[]; // [{day, time, duration}]

  // Status
  is_active: boolean;
  created_at: string;
  updated_at: string;

  // Computed fields
  has_coordinates: boolean;
  can_auto_checkin: boolean;
}
```

---

## 🚀 Setup Instructions

### Step 1: Run Migration

First, migrate existing branches to MongoDB:

```bash
cd /opt/kasaai/apps/churchflow/backend

# Get your organization ID (from database or API)
# Then run migration:
python scripts/migrate_branches_to_db.py \
  --organization-id YOUR_ORG_ID_HERE
```

### Step 2: Add GPS Coordinates

For branches without GPS coordinates, you have 3 options:

**Option A: Batch Geocoding Script**
```bash
python scripts/geocode_branches.py
# This will geocode all branches using OpenStreetMap
# Takes ~3 minutes for 150 branches
```

**Option B: Manual Entry via Admin UI**
- Open Branch Management in admin panel
- Click edit on a branch
- Use the map picker to set coordinates
- Save

**Option C: Bulk Update via API**
- Use the `PATCH /branches/{id}` endpoint
- Send latitude/longitude in request body

### Step 3: Configure Service Times

For each branch, add service schedules:

```bash
# Via API:
PATCH /branches/{branch_id}
{
  "service_times": [
    {
      "day_of_week": "sunday",
      "service_type": "sunday_morning",
      "start_time": "08:00",
      "duration_minutes": 120,
      "is_active": true
    },
    {
      "day_of_week": "sunday",
      "service_type": "sunday_evening",
      "start_time": "18:00",
      "duration_minutes": 90,
      "is_active": true
    }
  ]
}
```

### Step 4: Enable Auto Check-In

For branches ready for auto check-in:

```bash
PATCH /branches/{branch_id}
{
  "auto_checkin_enabled": true,
  "checkin_radius": 500  # meters
}
```

---

## 🔧 Database Indexes

The migration script automatically creates these indexes for optimal performance:

```javascript
// Unique constraint on organization + name
{ organization_id: 1, name: 1 } (unique)

// Query indexes
{ organization_id: 1, is_active: 1 }
{ organization_id: 1, region: 1 }
{ organization_id: 1, auto_checkin_enabled: 1 }
{ organization_id: 1, latitude: 1, longitude: 1 }
```

---

## 📡 API Examples

### List All Active Branches

```bash
GET /api/v1/branches?organization_id=674e9a2b3f1234567890abcd&is_active=true
```

### Search Nearby Branches

```bash
GET /api/v1/branches/search/nearby?
  latitude=5.6037&
  longitude=-0.1870&
  max_distance=5000&
  organization_id=674e9a2b3f1234567890abcd&
  auto_checkin_only=true
```

Response:
```json
[
  {
    "_id": "...",
    "name": "Adenta",
    "latitude": 5.7108,
    "longitude": -0.1673,
    "distance": 342.5,  // meters from search point
    "can_auto_checkin": true,
    ...
  }
]
```

### Create New Branch

```bash
POST /api/v1/branches
{
  "organization_id": "674e9a2b3f1234567890abcd",
  "name": "New Branch",
  "location": "New Location, Accra, Ghana",
  "region": "Greater Accra",
  "latitude": 5.6037,
  "longitude": -0.1870,
  "checkin_radius": 500,
  "auto_checkin_enabled": true
}
```

### Update Branch GPS Settings

```bash
PATCH /api/v1/branches/674e9a2b3f1234567890abcd
{
  "latitude": 5.7108,
  "longitude": -0.1673,
  "checkin_radius": 750,
  "auto_checkin_enabled": true
}
```

---

## 🎨 UI Integration

### Adding to Admin Navigation

In your admin layout, add:

```tsx
import BranchManagement from './components/admin/BranchManagement';

// In your router:
<Route path="/admin/branches" element={<BranchManagement />} />
```

### Branch Management Features

The admin UI provides:
- ✅ Complete CRUD operations
- ✅ Interactive map for GPS selection
- ✅ Real-time statistics
- ✅ Filtering and search
- ✅ Region-based organization
- ✅ Auto check-in configuration
- ✅ Soft delete protection

---

## 🔐 Security & Permissions

### Admin-Only Operations
- Create branch: Requires `admin` or `universal_admin` role
- Update branch: Requires `admin` or `universal_admin` role
- Delete branch: Requires `admin` or `universal_admin` role

### Read Operations
- All authenticated users can read branches
- Organization-scoped access control

### Soft Delete Protection
- Default delete is soft (sets `is_active=False`)
- Hard delete checks for references in:
  - `registrations` collection
  - `auto_checkin_logs` collection
- Prevents accidental data loss

---

## 📈 Statistics Dashboard

The admin UI displays:

1. **Total Branches**: All branches in organization
2. **Active Branches**: Currently operational
3. **With GPS**: Branches with coordinates
4. **Auto Check-In**: Branches with auto check-in enabled
5. **Need GPS**: Branches missing coordinates
6. **Inactive**: Deactivated branches

Plus:
- **Region Breakdown**: Branches per region
- **Coverage Percentage**: % with GPS coordinates

---

## 🧪 Testing the System

### 1. Verify Migration

```bash
python scripts/migrate_branches_to_db.py \
  --organization-id YOUR_ORG_ID \
  --verify
```

Expected output:
- Total branches count
- Active/inactive breakdown
- GPS coordinate coverage
- Top regions list

### 2. Test API Endpoints

```bash
# List branches
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:30030/api/v1/branches?organization_id=YOUR_ORG_ID"

# Get statistics
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:30030/api/v1/branches/stats/summary?organization_id=YOUR_ORG_ID"
```

### 3. Test Admin UI

1. Navigate to `/admin/branches`
2. Verify statistics display correctly
3. Test filtering by region
4. Create a test branch
5. Edit and update GPS coordinates
6. Test soft delete
7. Verify branch appears as inactive

---

## 🐛 Troubleshooting

### Migration Issues

**Problem**: "Invalid organization ID format"
```bash
# Solution: Ensure organization ID is a valid MongoDB ObjectId (24-char hex)
mongo churchflow --eval "db.organizations.find().pretty()"
```

**Problem**: Duplicate branch names
```bash
# Solution: Migration handles this automatically
# Existing branches are updated, not duplicated
```

### API Issues

**Problem**: 403 Forbidden on create/update
```bash
# Solution: Ensure user has admin role
# Check: current_user.roles includes "admin" or "universal_admin"
```

**Problem**: Branch search returns empty
```bash
# Solution: Check GPS coordinates are set and within search radius
# Verify: latitude/longitude are not null
```

### UI Issues

**Problem**: Map picker not displaying
```bash
# Solution: Ensure MapPicker component exists
# Check: /frontend/src/components/MapPicker.tsx
```

**Problem**: Cannot save branch
```bash
# Solution: Check browser console for validation errors
# Verify: name, location, region are all filled
```

---

## 📚 Next Steps

After setting up branch management:

1. **Phase 2**: Implement proximity check-in service
   - Use branch GPS coordinates
   - Calculate distances
   - Trigger check-ins when within radius

2. **Phase 3**: Build member-facing auto check-in UI
   - Location permission requests
   - Nearby branch detection
   - One-tap check-in widget

3. **Phase 4**: Gamification integration
   - Award points for check-ins
   - Track attendance streaks
   - Unlock badges

---

## 📝 Summary

You now have a complete branch management system with:

- ✅ **Full CRUD API** (Create, Read, Update, Delete)
- ✅ **Migration script** (Constants → MongoDB)
- ✅ **Admin UI** (Interactive management interface)
- ✅ **GPS support** (Map picker integration)
- ✅ **Auto check-in settings** (Radius, enable/disable)
- ✅ **Statistics dashboard** (Real-time metrics)
- ✅ **Filtering & search** (Region, status, GPS)
- ✅ **Soft delete protection** (Prevents data loss)
- ✅ **Organization scoping** (Multi-tenant support)

**Files Created:**
- `backend/app/api/routes/branches_crud.py` (554 lines)
- `backend/scripts/migrate_branches_to_db.py` (395 lines)
- `frontend/src/components/admin/BranchManagement.tsx` (625 lines)

**Total**: ~1,574 lines of production-ready code

---

Ready to proceed with proximity check-in and gamification! 🚀
