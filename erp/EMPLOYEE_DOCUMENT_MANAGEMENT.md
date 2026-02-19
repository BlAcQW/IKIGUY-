# Employee Document Management Feature

**Date**: 2025-11-06
**Status**: ✅ Implemented

## Overview

This document describes the employee document management feature implemented in the ERP system, which allows attaching CVs and certificates to employee records with automatic email creation notifications.

## Features

### 1. CV Upload
- Upload employee CV in PDF, DOC, or DOCX format
- Single CV per employee (replaces previous CV if uploaded again)
- Secure storage with organization/employee isolation
- Maximum file size: 10MB (configurable)

### 2. Certificate Upload
- Upload multiple certificates per employee
- Supported formats: PDF, JPG, JPEG, PNG
- Each certificate has a name/label (e.g., "Bachelor's Degree", "AWS Certification")
- Upload timestamp tracked for each certificate
- Individual certificate deletion

### 3. Email Creation Notifications
- Toast notification when employee email account is created successfully
- Shows temporary password in toast message
- Error notification if email creation fails
- Non-blocking: Employee is created even if email creation fails

## Technical Implementation

### Backend

#### Database Schema Changes
Added to `Employee` model in `/opt/kasaai/apps/erp/backend/app/models/hr.py`:
```python
cv_url: Optional[str]  # Path to CV file
certificates: List[Dict[str, str]]  # List of certificates with name, url, uploaded_at
```

#### File Upload Service
New service: `/opt/kasaai/apps/erp/backend/app/services/file_upload_service.py`
- Validates file type and size
- Stores files in organized directory structure: `uploads/{org_id}/employees/{employee_id}/{type}/`
- Generates unique filenames using UUID
- Provides secure file deletion

#### API Endpoints
Added to `/opt/kasaai/apps/erp/backend/app/api/routes/hr.py`:

1. **POST** `/hr/employees/{employee_id}/upload-cv`
   - Upload CV for an employee
   - Replaces existing CV if present
   - Returns: `{ success, message, cv_url }`

2. **POST** `/hr/employees/{employee_id}/upload-certificate?certificate_name=<name>`
   - Upload certificate with a name
   - Adds to employee's certificates list
   - Returns: `{ success, message, certificate }`

3. **DELETE** `/hr/employees/{employee_id}/certificates/{certificate_index}`
   - Delete specific certificate by index
   - Removes file from disk and database

4. **GET** `/hr/files/{file_path:path}`
   - Serve uploaded files
   - Validates organization access
   - Security: Path traversal protection

#### Configuration
Added to `/opt/kasaai/apps/erp/backend/app/config.py`:
```python
UPLOAD_DIR: str = "/opt/kasaai/apps/erp/uploads"
MAX_UPLOAD_SIZE_MB: int = 10
ALLOWED_EXTENSIONS: str = ".pdf,.doc,.docx,.jpg,.jpeg,.png"
```

### Frontend

#### Component Updates
Updated `/opt/kasaai/apps/erp/frontend/src/pages/HRPage.tsx`:

**State Management:**
- `cvFile`: Stores selected CV file
- `certificateFiles`: Array of certificate files with names
- `certificateName`: Current certificate name input
- `showToast`: Toast visibility
- `toastMessage`: Toast message content
- `toastType`: 'success' or 'error'

**UI Components:**
1. CV Upload Section:
   - File input for CV (PDF, DOC, DOCX)
   - Selected file preview
   - Remove file button

2. Certificate Upload Section:
   - Certificate name input
   - File selection button
   - List of selected certificates with names
   - Remove certificate button for each

3. Toast Notifications:
   - Success: Employee created + email account details
   - Error: Email creation failure reasons
   - File upload confirmations

#### User Flow
1. User fills employee form
2. (Optional) Selects CV file
3. (Optional) Adds certificates with names
4. Submits form
5. Employee is created
6. Toast shows email creation status with temporary password
7. Files are uploaded in background
8. Toast confirms file uploads

## File Storage Structure

```
/opt/kasaai/apps/erp/uploads/
├── {organization_id_1}/
│   └── employees/
│       ├── {employee_id_1}/
│       │   ├── cv/
│       │   │   └── {uuid}.pdf
│       │   └── certificates/
│       │       ├── {uuid}.pdf
│       │       └── {uuid}.jpg
│       └── {employee_id_2}/
│           └── cv/
│               └── {uuid}.docx
└── {organization_id_2}/
    └── employees/
        └── ...
```

## Security Features

1. **Organization Isolation**: Files stored in organization-specific directories
2. **Employee Isolation**: Each employee has their own directory
3. **Path Traversal Protection**: File serving validates paths
4. **Access Control**: Only users with organization access can view files
5. **File Type Validation**: Only allowed extensions accepted
6. **File Size Limits**: Configurable maximum upload size
7. **Unique Filenames**: UUID-based naming prevents conflicts

## Configuration

### Environment Variables
Add to `.env` file:
```bash
# File Upload Configuration
UPLOAD_DIR=/opt/kasaai/apps/erp/uploads
MAX_UPLOAD_SIZE_MB=10
ALLOWED_EXTENSIONS=.pdf,.doc,.docx,.jpg,.jpeg,.png
```

### Directory Setup
```bash
# Create uploads directory with proper permissions
mkdir -p /opt/kasaai/apps/erp/uploads
chmod 755 /opt/kasaai/apps/erp/uploads
```

## Usage Examples

### Creating Employee with Documents

1. **Via Web UI:**
   - Navigate to HR > Employees
   - Click "Add Employee"
   - Fill required fields (name, email, position, department, etc.)
   - Under "Documents" section:
     - Click "Choose File" to select CV
     - Enter certificate name (e.g., "Bachelor's Degree")
     - Click "Add" to attach certificate file
     - Repeat for multiple certificates
   - Click "Create"
   - Toast notification shows email creation status
   - Toast notifications show file upload confirmations

2. **Via API:**
   ```bash
   # Create employee
   curl -X POST https://dev-erp-api.ailabsafrica.com/api/v1/hr/employees \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "first_name": "John",
       "last_name": "Doe",
       "email": "john.doe@example.com",
       "position": "Software Engineer",
       "department": "Engineering",
       "hire_date": "2025-11-06",
       "salary": 75000
     }'

   # Upload CV
   curl -X POST https://dev-erp-api.ailabsafrica.com/api/v1/hr/employees/{id}/upload-cv \
     -H "Authorization: Bearer $TOKEN" \
     -F "file=@/path/to/cv.pdf"

   # Upload Certificate
   curl -X POST "https://dev-erp-api.ailabsafrica.com/api/v1/hr/employees/{id}/upload-certificate?certificate_name=Bachelor's%20Degree" \
     -H "Authorization: Bearer $TOKEN" \
     -F "file=@/path/to/degree.pdf"
   ```

### Viewing Employee Documents

Files are accessible via:
```
GET /api/v1/hr/files/{org_id}/employees/{employee_id}/cv/{filename}
GET /api/v1/hr/files/{org_id}/employees/{employee_id}/certificates/{filename}
```

## Testing

### Manual Testing Checklist

- [ ] Create employee with CV
- [ ] Create employee with certificates
- [ ] Create employee with both CV and certificates
- [ ] Verify toast shows email creation success
- [ ] Verify toast shows email creation errors
- [ ] Upload CV for existing employee
- [ ] Upload certificate for existing employee
- [ ] Delete certificate from employee
- [ ] Replace existing CV
- [ ] Verify file type validation (reject .exe, .js, etc.)
- [ ] Verify file size limits
- [ ] Verify cross-organization access is blocked
- [ ] Download employee CV
- [ ] Download employee certificate

### Test Script
See: `/opt/kasaai/apps/erp/backend/tests/test_employee_documents.py` (to be created)

## Future Enhancements

1. **Thumbnail Generation**: Generate thumbnails for image certificates
2. **Document Versioning**: Keep history of CVs
3. **Bulk Upload**: Upload multiple certificates at once
4. **Document Templates**: Pre-defined certificate types
5. **Document Expiry**: Track certificate expiration dates
6. **Document Verification**: Mark documents as verified by HR
7. **OCR Integration**: Extract text from uploaded documents
8. **Cloud Storage**: Store files in S3/Azure instead of local disk
9. **Document Preview**: In-browser PDF/image preview
10. **Audit Trail**: Track who viewed/downloaded documents

## Related Files

### Backend
- `/opt/kasaai/apps/erp/backend/app/models/hr.py` - Employee model
- `/opt/kasaai/apps/erp/backend/app/api/routes/hr.py` - HR API routes
- `/opt/kasaai/apps/erp/backend/app/services/file_upload_service.py` - File upload service
- `/opt/kasaai/apps/erp/backend/app/config.py` - Configuration

### Frontend
- `/opt/kasaai/apps/erp/frontend/src/pages/HRPage.tsx` - HR management page
- `/opt/kasaai/apps/erp/frontend/src/components/Toast.tsx` - Toast notification component

### Documentation
- `/opt/kasaai/apps/erp/TASKS.md` - Project tasks and progress
- `/opt/kasaai/apps/erp/README.md` - Project README

## Support

For issues or questions:
1. Check the logs: `sudo journalctl -u kasaai-erp-backend -f`
2. Verify uploads directory exists and is writable
3. Check file permissions
4. Verify environment variables are set correctly
5. Contact development team

## License

Copyright © 2025 AI Labs Africa. All rights reserved.
