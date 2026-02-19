# Conference Materials Management Feature

## Overview
Implemented a complete conference materials management system that allows uploading, downloading, and managing files (brochures, schedules, maps, etc.) for conferences. The ACI Impact 2025 brochure is now available for download on the landing page.

## What Has Been Implemented

### 1. Backend Components

#### Database Model (`app/models/conference_material.py`)
- `ConferenceMaterial` model with fields:
  - Conference association
  - File metadata (name, size, type)
  - Display settings (public/private, landing page visibility)
  - Material categorization (brochure, schedule, map, form, etc.)

#### Service Layer (`app/services/conference_material_service.py`)
- File upload with validation (max 50MB, allowed types)
- File storage management
- CRUD operations for material metadata
- Public/private access control
- Landing page material filtering

#### API Routes (`app/api/routes/conference_materials.py`)
- `POST /api/v1/conferences/{conference_id}/materials` - Upload material
- `GET /api/v1/conferences/{conference_id}/materials` - List materials
- `GET /api/v1/conference-materials/{material_id}` - Get material details
- `GET /api/v1/conference-materials/{material_id}/download` - Download file
- `PUT /api/v1/conference-materials/{material_id}` - Update metadata
- `DELETE /api/v1/conference-materials/{material_id}` - Delete material

### 2. Storage
- Created `/opt/kasaai/apps/churchflow/backend/storage/conference_materials/` directory
- ACI Impact 2025 brochure copied and uploaded (7.7MB PDF)
- Database record created with `display_on_landing: true`

### 3. Frontend Integration
- Updated landing page (`src/pages/Landing.tsx`) to:
  - Fetch materials for Impact 2025 conference
  - Display materials in attractive purple card section
  - Show file type, size, and description
  - Provide direct download links

### 4. Database Record
- Brochure uploaded with ID: `693008d33dd320d29135b861`
- Download URL: `/api/v1/conference-materials/693008d33dd320d29135b861/download`
- Marked as public and visible on landing page

## Features

### File Upload
- Supports: PDF, DOC/DOCX, XLS/XLSX, images (JPG, PNG, GIF), TXT
- Max file size: 50MB
- Automatic file naming with timestamp
- Metadata tracking (title, description, type, visibility)

### Access Control
- Public/private materials
- Landing page visibility toggle
- Display order for sorting
- Authentication required for private materials

### Material Types
- Brochure
- Schedule
- Map
- Form
- Flyer
- Guide
- Other

## API Usage Examples

### Upload a Material (Admin/Coordinator)
```bash
curl -X POST \
  https://churchflow-api.ailabsafrica.com/api/v1/conferences/68fbc116ca541168d5ea195e/materials \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@path/to/file.pdf" \
  -F "title=Event Schedule" \
  -F "description=Detailed schedule for all conference days" \
  -F "material_type=schedule" \
  -F "is_public=true" \
  -F "display_on_landing=true" \
  -F "display_order=2"
```

### List Conference Materials (Public)
```bash
curl https://churchflow-api.ailabsafrica.com/api/v1/conferences/68fbc116ca541168d5ea195e/materials?public_only=true&landing_page_only=true
```

### Download Material
```bash
curl -O https://churchflow-api.ailabsafrica.com/api/v1/conference-materials/693008d33dd320d29135b861/download
```

### Update Material Metadata (Admin)
```bash
curl -X PUT \
  https://churchflow-api.ailabsafrica.com/api/v1/conference-materials/693008d33dd320d29135b861 \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Updated Title",
    "display_on_landing": false,
    "display_order": 5
  }'
```

### Delete Material (Admin)
```bash
curl -X DELETE \
  https://churchflow-api.ailabsafrica.com/api/v1/conference-materials/693008d33dd320d29135b861 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Landing Page Display

The materials now appear on the landing page (https://churchflow.ailabsafrica.com) in a purple card section below the bus booking CTA. Features:
- Eye-catching design with icons
- File type and size display
- Click to download
- Responsive grid layout (mobile-optimized)

## Testing & Quality Assurance

### Comprehensive CRUD Tests ✅
**Test Suite**: `/opt/kasaai/apps/churchflow/backend/scripts/test_materials_crud.py`
**Results**: All 23 tests passed - See [TEST_RESULTS.md](backend/TEST_RESULTS.md)

**Test Coverage**:
1. ✅ PDF upload with metadata
2. ✅ Image upload with privacy settings
3. ✅ List and filter operations
4. ✅ Material detail retrieval
5. ✅ Metadata updates
6. ✅ File download verification
7. ✅ Material deletion with cleanup
8. ✅ File validation (type & size)

**Mobile Responsiveness** ✅
- Responsive padding and spacing
- Adaptive icon and text sizes
- Touch-friendly active states
- Optimized for screens from 320px to 2560px
- Grid adapts: 1 column (mobile) → 2 columns (tablet+)

## Admin Materials Management Tab ✅

### Location
Conference Detail page → Materials tab (5th tab after Check-in)
**Path**: `/conferences/{conferenceId}` → Materials tab

### Features
The Materials tab provides complete CRUD functionality for managing conference documents:

**Upload Materials**:
- Drag-and-drop or file picker
- Supported formats: PDF, DOC, DOCX, XLS, XLSX, JPG, JPEG, PNG, GIF, TXT
- Maximum file size: 50MB
- Required fields: File, Title
- Optional fields: Description, Type (brochure/schedule/map/form/flyer/guide/other)
- Visibility controls:
  - Public checkbox (no login required to download)
  - Display on landing page checkbox
  - Display order (numeric sorting)

**List Materials**:
- Card-based layout with file metadata
- Visual indicators:
  - Eye icon = Public material
  - Eye-off icon = Private material
  - "Landing" badge = Displayed on landing page
- File information: Type, filename, size, display order

**Material Actions**:
1. **Download** (blue icon) - Direct download of the file
2. **Copy URL** (gray → green icon) - Copy download URL to clipboard
   - Shows checkmark and turns green for 2 seconds after copying
   - Full URL: `https://churchflow-api.ailabsafrica.com/api/v1/conference-materials/{id}/download`
3. **Edit** (gray icon) - Edit metadata inline
4. **Delete** (red icon) - Remove material with confirmation

**Edit Mode**:
- Click edit icon to enter inline edit mode
- Editable fields:
  - Title
  - Description
  - Material type
  - Public/private toggle
  - Landing page visibility
  - Display order
- Save or Cancel buttons
- File itself cannot be replaced (must delete and re-upload)

**Empty State**:
- Friendly message with icon when no materials exist
- Prominent "Upload Material" call-to-action

### Component Details
**File**: `src/components/ConferenceMaterials.tsx`
**Props**: `{ conferenceId: string }`
**Features**:
- Real-time material list updates after actions
- Form validation
- Error handling with user feedback
- Responsive design (mobile-friendly)
- Loading states
- Success/error alerts

## Future Enhancements

### Additional Features to Consider

1. **Enhanced Upload**
   - Drag & drop file upload
   - Upload progress indicator with percentage
   - Bulk upload support (multiple files at once)
   - Replace file functionality (keep metadata, update file)

2. **File Management**
   - Material preview modal (PDF viewer, image lightbox)
   - Download analytics (track download counts)
   - File versioning (keep history of uploads)
   - Duplicate material detection

3. **Security & Performance**
   - Virus scanning integration for uploaded files
   - CDN integration for faster downloads
   - Thumbnail generation for images and PDF first pages
   - Automatic image compression/optimization

4. **User Experience**
   - QR code generation for materials (scan to download)
   - Short URL generation service integration
   - Material search and filtering
   - Batch operations (delete multiple, update visibility)
   - Material categories and tags

5. **Integration**
   - Email materials to registered attendees
   - WhatsApp sharing integration
   - SMS with material links
   - Automatic materials in registration confirmation

## Testing

### Verify Brochure Upload
```bash
# Check if brochure is in database
cd /opt/kasaai/apps/churchflow/backend
/opt/kasaai/apps/venv/bin/python scripts/upload_initial_brochure.py

# Test download
curl -I https://churchflow-api.ailabsafrica.com/api/v1/conference-materials/693008d33dd320d29135b861/download
```

### Test Frontend Display
1. Visit https://churchflow.ailabsafrica.com
2. Scroll to "Conference Materials" section
3. Click on brochure to download
4. Verify file downloads correctly

## Files Created/Modified

### New Files
- `backend/app/models/conference_material.py`
- `backend/app/services/conference_material_service.py`
- `backend/app/api/routes/conference_materials.py`
- `backend/scripts/upload_initial_brochure.py`
- `backend/storage/conference_materials/aci-impact-2025-brochure.pdf`

### Modified Files
- `backend/app/main.py` - Added conference_materials router
- `frontend/src/pages/Landing.tsx` - Added materials display section

## Database Collections

### conference_materials
```javascript
{
  _id: ObjectId,
  conference_id: ObjectId,
  organization_id: ObjectId,
  title: String,
  description: String,
  file_name: String,
  file_path: String,
  file_size: Number,
  file_type: String,
  material_type: String,
  is_public: Boolean,
  display_on_landing: Boolean,
  display_order: Number,
  uploaded_by: ObjectId,
  created_at: Date,
  updated_at: Date
}
```

## Security Considerations

- File type validation prevents malicious uploads
- File size limit prevents DoS attacks
- Authentication required for uploads and private materials
- Files stored outside web root with unique names
- Role-based access (admin/coordinator only for management)

## Maintenance

### Adding New File Types
Edit `conference_material_service.py`:
```python
ALLOWED_FILE_TYPES = {
    "application/pdf",
    # ... add new MIME types
}
```

### Changing File Size Limit
Edit `conference_material_service.py`:
```python
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
```

### Cleanup Old Files
```bash
# Find materials not in database
cd /opt/kasaai/apps/churchflow/backend/storage/conference_materials
# Create cleanup script to remove orphaned files
```

## Support

For issues or questions:
- Check API docs: https://churchflow-api.ailabsafrica.com/api/v1/docs
- View logs: `sudo journalctl -u kasaai-churchflow-backend -f`
- Database queries: `mongosh` then use `churchflow` database

## Status

✅ Backend API fully implemented and tested
✅ File storage configured
✅ Initial brochure uploaded
✅ Landing page integration complete
✅ Backend service restarted
✅ Frontend built and deployed

⚠️ Materials management admin tab not yet implemented (API ready for integration)
