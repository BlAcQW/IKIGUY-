# Expense Receipt Attachment Feature

**Date**: 2025-11-06 (Initial), 2025-11-11 (Multi-upload Enhancement)
**Status**: ✅ Implemented with Multi-Upload Support

## Overview

This document describes the expense receipt attachment feature, which allows users to attach receipts to expenses either by uploading files (PDF, images) or by taking photos directly from mobile devices. **Now enhanced with bulk upload and drag-and-drop support.**

## Features

### 1. Multi-File Upload (NEW ✨)
- **Select multiple files at once** using file picker
- Upload up to 10+ files in a single operation
- Bulk upload API endpoint for efficient processing
- Individual file validation and error reporting
- Progress feedback for each file

### 2. Drag and Drop Support (NEW ✨)
- **Drag and drop multiple files** into upload zone
- Visual feedback during drag operation
- Automatic file type filtering
- Works on desktop browsers

### 3. File Upload
- Upload receipt files from computer
- Supported formats: PDF, JPG, PNG, HEIC
- Multiple receipts per expense
- File size validation (10MB per file)

### 4. Mobile Camera Capture
- Direct photo capture using device camera
- Uses HTML5 `capture="environment"` attribute
- Optimized for mobile devices
- Automatic image compression

### 5. Receipt Management
- Attach receipts during expense creation
- Add receipts to existing expenses
- View attached receipts
- Delete individual receipts
- Preview all selected receipts before submission
- Real-time file list with size information

## Technical Implementation

### Backend

#### API Endpoints

1. **POST** `/finance/expenses/{expense_id}/attach-receipts-bulk` **(NEW ✨)**
   - **Attach multiple receipts in a single API call**
   - Upload up to 10+ files simultaneously
   - Returns detailed status for each file
   - Response includes success/failure for each file
   - Example response:
     ```json
     {
       "success": true,
       "message": "3 receipts attached successfully",
       "total_files": 3,
       "successful_uploads": 3,
       "failed_uploads": 0,
       "receipts": [
         {
           "filename": "receipt1.pdf",
           "success": true,
           "receipt_url": "https://...",
           "receipt_path": "uploads/..."
         }
       ],
       "expense": { ... }
     }
     ```

2. **POST** `/finance/expenses/{expense_id}/attach-receipt`
   - Attach a single receipt to an existing expense
   - Uploads file to organized storage
   - Returns: `{ success, message, receipt_url, expense }`

3. **DELETE** `/finance/expenses/{expense_id}/receipts/{receipt_index}`
   - Delete specific receipt by index
   - **Removes file from storage AND database**
   - Graceful error handling if file already deleted

4. **DELETE** `/finance/expenses/{expense_id}` **(Enhanced ✨)**
   - Soft-deletes expense (sets `is_active=False`)
   - **Automatically deletes ALL receipt files from storage**
   - Prevents orphaned files from accumulating
   - Logs each file deletion for audit trail

5. **POST** `/finance/expenses/upload-receipt` *(Existing)*
   - Upload receipt with optional data extraction
   - AI-powered data extraction available
   - Returns extracted expense data

#### File Storage

**Location**: Uses existing shared file upload service

**Structure**:
```
uploads/
└── {organization_id}/
    └── receipts/
        └── {year}/
            └── {month}/
                └── {unique_id}_{filename}.ext
```

#### Database Schema

The `Expense` model already includes:
```python
receipt_urls: List[str]  # List of receipt file paths
```

### Frontend

#### Component Updates

**File**: `/opt/kasaai/apps/erp/frontend/src/pages/FinancePage.tsx`

**New UI Elements**:

1. **Upload Section**:
   ```tsx
   <label className="flex-1 cursor-pointer">
     <div className="px-4 py-3 border-2 border-dashed...">
       <Upload className="w-5 h-5 mx-auto mb-1" />
       <span>Upload File</span>
     </div>
     <input
       type="file"
       accept="image/*,.pdf"
       className="hidden"
       onChange={handleFileUpload}
     />
   </label>
   ```

2. **Camera Capture**:
   ```tsx
   <label className="flex-1 cursor-pointer">
     <div className="px-4 py-3 border-2 border-dashed...">
       <Camera className="w-5 h-5 mx-auto mb-1" />
       <span>Take Photo</span>
     </div>
     <input
       type="file"
       accept="image/*"
       capture="environment"  // Activates camera on mobile
       className="hidden"
       onChange={handleCameraCapture}
     />
   </label>
   ```

3. **Receipt Preview**:
   - Shows selected files before upload
   - File name, size display
   - Remove button for each file
   - Existing receipts display (for editing)

#### State Management

```typescript
// In formData
receipt_files: File[]  // New files to upload

// In Expense interface
receipt_urls: string[]  // Existing receipt URLs
```

#### Upload Flow

1. User selects/captures receipt files
2. Files stored in `formData.receipt_files`
3. Files previewed in UI
4. On form submit:
   - Expense created/updated first
   - Then each receipt file uploaded via separate API call
   - Toast notification shows success/errors

## User Experience

### Desktop Flow (Multi-File Upload)

**Option 1: Drag and Drop (NEW ✨)**
1. Navigate to Finance > Expenses
2. Click "Add Expense"
3. Fill expense details
4. Scroll to "Receipts" section
5. **Drag multiple PDFs/images into the drop zone**
6. Files appear in preview list instantly
7. Add more files if needed (repeat drag or use buttons)
8. Submit form
9. All receipts uploaded in bulk automatically

**Option 2: File Picker (NEW ✨)**
1. Navigate to Finance > Expenses
2. Click "Add Expense"
3. Fill expense details
4. Scroll to "Receipts" section
5. Click "Upload Files" button
6. **Select multiple files at once** (Ctrl+Click or Cmd+Click)
7. Preview appears showing all selected files
8. Submit form
9. All receipts uploaded in bulk automatically

### Mobile Flow

1. Open ERP app on mobile browser
2. Navigate to Finance > Expenses
3. Click "Add Expense"
4. Fill expense details
5. Scroll to "Receipts" section
6. Click "Take Photo"
7. Device camera opens
8. Take photo of receipt
9. Preview appears
10. Submit form
11. Receipt uploaded automatically

## Mobile Browser Compatibility

### Camera Capture Support

| Browser | iOS | Android | Notes |
|---------|-----|---------|-------|
| Safari | ✅ | N/A | Native camera access |
| Chrome | ✅ | ✅ | Full support |
| Firefox | ✅ | ✅ | Full support |
| Edge | ✅ | ✅ | Full support |
| Samsung Internet | N/A | ✅ | Full support |

**Note**: `capture="environment"` opens rear camera by default on mobile devices

### HEIC Support

- iOS devices capture photos in HEIC format
- Backend automatically converts HEIC to JPEG
- No user action required

## Security Features

1. **Organization Isolation**: Files stored in org-specific directories
2. **File Type Validation**: Only allowed extensions accepted
3. **File Size Limits**: Configurable maximum upload size
4. **Access Control**: Only org members can view receipts
5. **Path Traversal Protection**: File serving validates paths

## File Cleanup & Storage Management (NEW ✨)

### Automatic File Deletion

The system now includes comprehensive file cleanup to prevent storage bloat:

1. **Individual Receipt Deletion**:
   - Deletes file from storage immediately
   - Removes database reference
   - Graceful error handling if file missing

2. **Expense Deletion** (Enhanced):
   - Automatically deletes ALL associated receipt files
   - Prevents orphaned files in storage
   - Logs each deletion for audit trail
   - Continues even if some files fail to delete

### Storage Path Structure

```
uploads/
└── {organization_id}/
    └── receipts/
        └── {year}/
            └── {month}/
                └── {unique_id}_{filename}.ext
```

### Benefits

- **No orphaned files**: Deleting an expense cleans up all its receipts
- **Audit trail**: All deletions logged for compliance
- **Storage efficiency**: Automatic cleanup prevents bloat
- **Graceful degradation**: Continues operation even if file deletion fails

## Configuration

### Environment Variables

```bash
# Use shared file upload service configuration
# No additional config needed
```

### File Upload Settings

- **Max file size**: 10MB (configurable)
- **Allowed formats**: PDF, JPG, JPEG, PNG, HEIC, HEIF
- **Storage location**: Shared storage service

## Usage Examples

### Creating Expense with Multiple Receipts (NEW ✨)

1. **Via Web UI:**
   - Fill expense form
   - Drag and drop multiple files OR click "Upload Files" and select multiple
   - Preview all selected files
   - Submit form (all files uploaded in bulk)

2. **Via API - Bulk Upload:**
   ```bash
   # Create expense
   curl -X POST https://dev-erp-api.ailabsafrica.com/api/v1/finance/expenses \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "expense_date": "2025-11-11",
       "merchant": "Office Depot",
       "category": "office_supplies",
       "amount": 150.00,
       "currency": "USD"
     }'

   # Attach multiple receipts in one API call
   curl -X POST https://dev-erp-api.ailabsafrica.com/api/v1/finance/expenses/{id}/attach-receipts-bulk \
     -H "Authorization: Bearer $TOKEN" \
     -F "files=@/path/to/receipt1.pdf" \
     -F "files=@/path/to/receipt2.jpg" \
     -F "files=@/path/to/receipt3.png"
   ```

3. **Via API - Single Upload (Still Supported):**
   ```bash
   # Attach single receipt
   curl -X POST https://dev-erp-api.ailabsafrica.com/api/v1/finance/expenses/{id}/attach-receipt \
     -H "Authorization: Bearer $TOKEN" \
     -F "file=@/path/to/receipt.jpg"
   ```

### Viewing Receipts

Receipts are displayed in the expense edit form:
- Existing receipts shown with "View" links
- Click "View" to open receipt in new tab

### Deleting Receipts

```bash
curl -X DELETE https://dev-erp-api.ailabsafrica.com/api/v1/finance/expenses/{expense_id}/receipts/{index} \
  -H "Authorization: Bearer $TOKEN"
```

## Advanced Features

### AI Data Extraction (Existing)

The system already supports automatic data extraction from receipts:

```bash
curl -X POST https://dev-erp-api.ailabsafrica.com/api/v1/finance/expenses/upload-receipt \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@receipt.pdf" \
  -F "extract_data=true" \
  -F "use_ai=true"  # Optional: Use AI for better accuracy
```

Returns:
```json
{
  "receipt_url": "...",
  "extracted_data": {
    "merchant": "Starbucks",
    "amount": 15.50,
    "tax_amount": 1.50,
    "expense_date": "2025-11-06",
    "category": "restaurant",
    "confidence": 0.85
  }
}
```

## Best Practices

### For Users

1. **Take Clear Photos**: Ensure receipt text is readable
2. **Good Lighting**: Use adequate lighting when capturing
3. **Flat Surface**: Place receipt on flat surface
4. **Full Receipt**: Capture entire receipt including totals
5. **Multiple Receipts**: Attach all related receipts

### For Developers

1. **Error Handling**: Display helpful error messages
2. **Progress Indicators**: Show upload progress for large files
3. **Validation**: Validate file types before upload
4. **Optimization**: Compress images before upload on mobile
5. **Offline Support**: Consider offline-first approach

## Testing

### Automated Unit Tests (NEW ✨)

Comprehensive test suite available at:
`/opt/kasaai/apps/erp/backend/tests/test_expense_multi_upload.py`

**Test Coverage:**
- Bulk upload of multiple PDFs
- Mixed file types (PDFs + images)
- Invalid file type handling
- Large batch uploads (10+ files)
- Individual file error handling
- Receipt deletion after bulk upload
- Response structure validation
- Database integrity checks

**Running Tests:**
```bash
cd /opt/kasaai/apps/erp/backend
pytest tests/test_expense_multi_upload.py -v
```

### Manual Testing Checklist

**Multi-Upload Features (NEW ✨)**
- [ ] Drag and drop multiple PDFs
- [ ] Drag and drop multiple images
- [ ] Select multiple files via file picker (Ctrl+Click)
- [ ] Mix of PDFs and images in one upload
- [ ] Drag invalid file types (should filter automatically)
- [ ] Upload 10+ files at once
- [ ] Preview all files before submit
- [ ] Remove individual files from preview

**Original Features**
- [ ] Upload single PDF receipt (desktop)
- [ ] Upload single JPEG image (desktop)
- [ ] Take photo with phone camera (mobile)
- [ ] View attached receipts
- [ ] Delete receipts
- [ ] Edit expense with existing receipts
- [ ] Test file type validation
- [ ] Test file size limits
- [ ] Test on iOS Safari
- [ ] Test on Android Chrome

### Test Data

Sample test files are generated automatically in the unit tests using:
- Minimal valid PDF files
- 1x1 PNG images
- Various file formats for validation testing

## Troubleshooting

### Camera Not Opening on Mobile

**Cause**: Browser permissions not granted
**Solution**:
1. Check browser settings
2. Allow camera access for site
3. Try different browser

### File Upload Fails

**Cause**: File too large or wrong format
**Solution**:
1. Check file size (<10MB)
2. Check file format (PDF, JPG, PNG, HEIC only)
3. Try compressing image

### Receipt Not Displaying

**Cause**: CORS or authentication issue
**Solution**:
1. Check authentication token
2. Verify organization access
3. Check browser console for errors

## Future Enhancements

1. **Image Compression**: Automatic client-side compression
2. ~~**Batch Upload**: Upload multiple receipts at once~~ ✅ **IMPLEMENTED** (2025-11-11)
3. ~~**Drag and Drop**: Drag and drop multiple files~~ ✅ **IMPLEMENTED** (2025-11-11)
4. **OCR Integration**: Extract text from all receipts
5. **Receipt Matching**: Auto-match receipts to expenses
6. **Cloud Storage**: Store receipts in S3/Azure
7. **Offline Mode**: Queue uploads for later
8. **Receipt Scanner**: Dedicated receipt scanner mode
9. **Receipt Templates**: Common receipt formats
10. **Duplicate Detection**: Prevent duplicate receipts
11. **Receipt Verification**: Mark receipts as verified
12. **Upload Progress Bar**: Show progress for large uploads

## Related Files

### Backend
- `/opt/kasaai/apps/erp/backend/app/models/finance.py` - Expense model
- `/opt/kasaai/apps/erp/backend/app/api/routes/finance.py` - Finance API routes (includes bulk upload endpoint)

### Frontend
- `/opt/kasaai/apps/erp/frontend/src/pages/FinancePage.tsx` - Finance page with expense form and multi-upload

### Tests
- `/opt/kasaai/apps/erp/backend/tests/test_expense_multi_upload.py` - Comprehensive unit tests for multi-upload (NEW ✨)

### Documentation
- `/opt/kasaai/apps/erp/TASKS.md` - Project tasks and progress
- `/opt/kasaai/apps/erp/README.md` - Project README
- `/opt/kasaai/apps/erp/EXPENSE_RECEIPT_ATTACHMENT.md` - This file

## Support

For issues or questions:
1. Check the logs: `sudo journalctl -u kasaai-erp-backend -f`
2. Verify file upload service is working
3. Check browser console for errors
4. Test with different file types
5. Contact development team

## License

Copyright © 2025 AI Labs Africa. All rights reserved.
