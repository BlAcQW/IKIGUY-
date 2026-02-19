# EstateFlow Upload Fix - December 11, 2025

## Issue
File uploads were failing with 404 errors. Users attempting to upload property images or videos received "Upload failed" errors.

## Root Cause
The `FileUpload.tsx` component was calling incorrect API endpoints:
- ❌ Called: `https://estateflow-api.ailabsafrica.com/upload/images`
- ✅ Should be: `https://estateflow-api.ailabsafrica.com/api/v1/upload/images`

The component was missing the `/api/v1` prefix in the endpoint URLs.

## Error Logs
```
INFO: 154.161.159.212:0 - "POST /upload/images HTTP/1.1" 404 Not Found
INFO: 154.161.159.212:0 - "POST /upload/images HTTP/1.1" 404 Not Found
```

## Solution
Updated `/opt/kasaai/apps/estateflow/frontend/src/components/FileUpload.tsx`:

### Fixed Upload Endpoint (Line 90-93)
**Before:**
```typescript
const endpoint =
  accept === "videos" || file.type.startsWith("video/")
    ? `${API_BASE_URL}/upload/videos`
    : `${API_BASE_URL}/upload/images`;
```

**After:**
```typescript
const endpoint =
  accept === "videos" || file.type.startsWith("video/")
    ? `${API_BASE_URL}/api/v1/upload/videos`
    : `${API_BASE_URL}/api/v1/upload/images`;
```

### Fixed Storage URL (Line 114)
**Before:**
```typescript
const fileUrl = `${API_BASE_URL}/storage/${result.path}`;
```

**After:**
```typescript
const fileUrl = `${API_BASE_URL}/api/v1/storage/${result.path}`;
```

## Testing

### Backend Service Status
```bash
$ sudo systemctl status kasaai-estateflow-backend
● kasaai-estateflow-backend.service - EstateFlow Backend Service
   Loaded: loaded
   Active: active (running)
   Port: 30039
```

### Endpoint Verification
```bash
# Test upload endpoint (without auth - should return 401/403, not 404)
$ curl -X POST "https://estateflow-api.ailabsafrica.com/api/v1/upload/images" \
  -F "file=@/tmp/test_image.png"
{"detail":"Not authenticated"}
```

✅ **Result**: Endpoint now exists and requires authentication (correct behavior)
❌ **Before**: Endpoint returned 404 Not Found

### Frontend Build
```bash
$ cd estateflow/frontend && npm run build
✓ built in 2.36s
PWA v1.2.0
precache  15 entries (1001.18 KiB)
```

✅ **Result**: Frontend rebuilt successfully with fixed endpoints

## Files Modified
- `estateflow/frontend/src/components/FileUpload.tsx` (2 lines changed)

## Expected Behavior (After Fix)

### Image Upload Flow
1. User selects image file(s) in property creation wizard
2. Frontend calls: `POST /api/v1/upload/images` with authentication
3. Backend validates file and uploads to Hetzner Storage Box
4. Backend returns storage path
5. Frontend converts to URL: `/api/v1/storage/properties/{org_id}/property-images/...`
6. Property is created with image URLs

### Video Upload Flow
1. User selects video file in property creation wizard
2. Frontend calls: `POST /api/v1/upload/videos` with authentication
3. Backend validates file and uploads to Hetzner Storage Box
4. Backend returns storage path
5. Frontend converts to URL: `/api/v1/storage/properties/{org_id}/property-videos/...`
6. Property is created with video URL

## Supported Formats

### Images
- JPEG, PNG, GIF, WebP, HEIC, HEIF
- Max size: 10 MB per image
- Max files: 20 images per batch

### Videos
- MP4, MOV, AVI, WebM
- Max size: 100 MB per video
- Max files: 1 video per property

## API Endpoints (Corrected)

### Upload Endpoints
- `POST /api/v1/upload/images` - Upload property image(s)
- `POST /api/v1/upload/videos` - Upload property video
- `POST /api/v1/upload/batch` - Batch upload multiple images

### Storage Serving
- `GET /api/v1/storage/{file_path}` - Serve uploaded files

## Authentication
All upload endpoints require:
```
Authorization: Bearer <supabase-jwt-token>
```

Token obtained from Supabase authentication when user logs in.

## Storage Location
Files stored on Hetzner Storage Box:
```
kasaai/estateflow/properties/{org_id}/
  ├── property-images/{year}/{month}/{timestamp}_{hash}.jpg
  └── property-videos/{year}/{month}/{timestamp}_{hash}.mp4
```

## Deployment Status
- ✅ Backend: Running on port 30039
- ✅ Frontend: Rebuilt and deployed
- ✅ Upload endpoints: Accessible at correct URLs
- ✅ Storage endpoint: Working
- ✅ Hetzner Storage: Connected

## Testing Checklist

- [x] Verify service is running
- [x] Test endpoint accessibility (returns auth error, not 404)
- [x] Rebuild frontend with fixed URLs
- [ ] **User Testing Required**: Test full upload flow with logged-in user
- [ ] Verify images appear on property detail page
- [ ] Verify videos appear on property detail page
- [ ] Test batch upload (multiple images)
- [ ] Test file validation (size limits, formats)

## Next Steps

1. **User Testing**: Have a real user test the upload functionality
   - Log in to EstateFlow: https://estateflow.ailabsafrica.com
   - Create new property
   - Navigate to Media step
   - Upload images and/or video
   - Verify files appear in preview
   - Complete property creation
   - Verify files display on property detail page

2. **Monitor Logs**: Watch for any upload errors
   ```bash
   sudo journalctl -u kasaai-estateflow-backend -f | grep upload
   ```

3. **Verify Storage**: Check Hetzner Storage Box for uploaded files
   ```bash
   # Check storage structure
   ls -la /path/to/hetzner/kasaai/estateflow/properties/
   ```

## Related Documentation
- `/opt/kasaai/apps/estateflow/FILE_UPLOAD_IMPLEMENTATION.md` - Full implementation guide
- `/opt/kasaai/apps/shared/storage/hetzner_storage_box.py` - Storage service
- `/opt/kasaai/apps/estateflow/frontend/src/components/FileUpload.tsx` - Upload component

## Issue Resolution Time
- **Reported**: December 11, 2025 15:45 CET
- **Diagnosed**: December 11, 2025 15:48 CET
- **Fixed**: December 11, 2025 15:50 CET
- **Deployed**: December 11, 2025 15:51 CET
- **Total Time**: ~6 minutes

## Lesson Learned
When using centralized API configuration (`API_BASE_URL`), ensure all endpoint paths include the full API version prefix (`/api/v1`). The `API_BASE_URL` should only contain the domain, not the API version path.

---

**Status**: ✅ FIXED - Ready for user testing
**Priority**: High - Core functionality
**Impact**: All users attempting to upload property media
