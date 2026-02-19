# KasaAI Drive

Google Drive-like file management system for organizations built with FastAPI, Next.js, and Hetzner Storage.

## Features

### Core Functionality
- **File Operations**: Upload, download, delete, rename, move files
- **Folder Management**: Create, rename, delete, move folders with nested hierarchy
- **Search & Filters**: Full-text search, filter by type/date/size/owner, sort options
- **Sharing & Permissions**: Share with users, role-based permissions (view/comment/edit/manage), public share links
- **Organization-Based Access**: Users access files based on organization membership
- **Trash & Restore**: Soft delete with 30-day retention
- **Starred Items**: Mark important files/folders for quick access
- **Recent Files**: Quick access to recently modified files

### Technical Features
- **Storage**: Hetzner Storage Box via WebDAV/SFTP
- **Database**: MongoDB for metadata and search
- **Authentication**: Supabase for user authentication
- **Real-time Updates**: WebSocket support for file upload progress
- **File Validation**: Type and size validation with magic byte checking
- **Permission System**: Hierarchical permissions with inheritance
- **Activity Logging**: Complete audit trail of file operations

## Architecture

### Backend (Port 30037)
- **Framework**: FastAPI with async/await
- **Database**: MongoDB (kasaai_drive)
- **Storage**: Hetzner Storage Box (`kasaai/drive/{org_id}/`)
- **Auth**: Shared Supabase auth (`@shared/auth/supabase_auth`)
- **Default Org**: AI Labs Ltd. (`ai_labs_ltd`)

### Frontend
- **Framework**: Next.js 14 with App Router
- **UI**: React + TypeScript + Tailwind CSS + Shadcn/ui
- **State**: Zustand for state management
- **API Client**: React Query for data fetching

### Shared Services
- **Location**: `apps/shared/services/drive_service.py`
- **Reusability**: Can be imported by any application
- **Features**: Complete drive functionality as a library

## API Endpoints

### Files
- `POST /api/files/upload` - Upload file
- `GET /api/files/{file_id}` - Get file metadata
- `GET /api/files/{file_id}/download` - Download file
- `PUT /api/files/{file_id}/rename` - Rename file
- `PUT /api/files/{file_id}/move` - Move file
- `DELETE /api/files/{file_id}` - Delete file (trash or permanent)
- `POST /api/files/{file_id}/star` - Toggle star status

### Folders
- `POST /api/folders` - Create folder
- `GET /api/folders/{folder_id}/contents` - List folder contents
- `GET /api/folders/{folder_id}/breadcrumbs` - Get breadcrumb trail
- `PUT /api/folders/{folder_id}/rename` - Rename folder
- `PUT /api/folders/{folder_id}/move` - Move folder
- `DELETE /api/folders/{folder_id}` - Delete folder

### Search
- `GET /api/search?q={query}` - Search files and folders
- `GET /api/search/recent` - Get recent files
- `GET /api/search/starred` - Get starred items

### Sharing
- `POST /api/share/{item_id}/user` - Share with user
- `POST /api/share/{item_id}/link` - Create public share link
- `DELETE /api/share/{item_id}/link` - Revoke share link

## Database Schema

### Collection: drive_items

```javascript
{
  _id: "uuid",
  name: "filename.pdf",
  type: "file" | "folder",
  path: "org_123/folder/file_id_filename.pdf",
  parent_id: "folder_uuid" | null,
  organization_id: "org_123",
  owner_id: "user_uuid",
  size: 1024000,
  mime_type: "application/pdf",
  file_hash: "sha256_hash",
  created_at: ISODate("2025-11-10T..."),
  modified_at: ISODate("2025-11-10T..."),
  is_deleted: false,
  deleted_at: null,
  is_starred: false,
  permissions: [
    {
      user_id: "user_uuid",
      role: "view" | "comment" | "edit" | "manage",
      granted_at: ISODate("..."),
      granted_by: "user_uuid"
    }
  ],
  share_link: {
    token: "uuid",
    created_at: ISODate("..."),
    created_by: "user_uuid",
    expires_at: ISODate("...") | null,
    is_public: true
  },
  metadata: {}
}
```

## Installation

### Backend

```bash
cd /opt/kasaai/apps/drive/backend

# Install dependencies (uses shared venv)
/opt/kasaai/apps/venv/bin/pip install -r requirements.txt

# Run development server
/opt/kasaai/apps/venv/bin/python main.py
```

### Frontend

```bash
cd /opt/kasaai/apps/drive/frontend

# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build
```

## Environment Variables

Required in `/opt/kasaai/.env`:

```bash
# MongoDB
MONGODB_URL=mongodb://admin:password@localhost:27017/?authSource=admin
MONGODB_DB_NAME=kasaai_drive

# Supabase Authentication (uses shared @shared/auth)
SUPABASE_URL=https://supabase.ailabsafrica.com
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key

# Organization System (uses shared @shared/services/organization_service)
DEFAULT_ORGANIZATION_ID=ai_labs_ltd
DEFAULT_ORGANIZATION_NAME=AI Labs Ltd.
UNIVERSAL_ADMIN_EMAILS=admin@ailabsafrica.com,alfred.anyan@gmail.com,user@ailabsafrica.com
UNIVERSAL_ADMIN_USER_IDS=4a6252e7-3dc7-483a-92c3-59a0a814a169,65715ad2-bcfa-42aa-ab21-e0b06f19b3e4,a1d7c822-847f-40ec-9fed-cc3cd9155c06

# Hetzner Storage
HETZNER_STORAGE_USERNAME=u497034-sub1
HETZNER_STORAGE_PASSWORD=password
HETZNER_STORAGE_HOST=u497034-sub1.your-storagebox.de
HETZNER_STORAGE_PROTOCOL=webdav

# Storage Limits
MAX_FILE_SIZE_MB=100
MAX_UPLOAD_SIZE_MB=500

# Security
SECRET_KEY=your_secret_key
```

## Deployment

### Backend Service

```bash
# Create systemd service
sudo nano /etc/systemd/system/kasaai-drive-backend.service
```

```ini
[Unit]
Description=KasaAI Drive Backend API
After=network.target mongodb.service

[Service]
Type=simple
User=dev
WorkingDirectory=/opt/kasaai/apps/drive/backend
Environment="PATH=/opt/kasaai/apps/venv/bin"
Environment="PYTHONPATH=/opt/kasaai:/opt/kasaai/apps"
ExecStart=/opt/kasaai/apps/venv/bin/uvicorn main:app --host 0.0.0.0 --port 30037
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Nginx Configuration

```nginx
# API
server {
    listen 443 ssl http2;
    server_name drive-api.ailabsafrica.com;

    location / {
        proxy_pass http://127.0.0.1:30037;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        client_max_body_size 500M;
    }
}

# Frontend
server {
    listen 443 ssl http2;
    server_name drive.ailabsafrica.com;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

## Usage Examples

### Upload File (Python)

```python
from apps.shared.services.drive_service import get_drive_service
from motor.motor_asyncio import AsyncIOMotorClient

# Initialize
client = AsyncIOMotorClient("mongodb://...")
db = client.kasaai_drive
drive = await get_drive_service(db, organization_id="org_123")

# Upload file
with open("document.pdf", "rb") as f:
    result = await drive.upload_file(
        file_content=f.read(),
        filename="document.pdf",
        parent_id=None,
        owner_id="user_123",
        organization_id="org_123"
    )

print(f"Uploaded: {result['id']}")
```

### Upload File (cURL)

```bash
curl -X POST https://drive-api.ailabsafrica.com/api/files/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@document.pdf" \
  -F "parent_id=folder_123" \
  -F "organization_id=org_123"
```

### Search Files (cURL)

```bash
curl -X GET "https://drive-api.ailabsafrica.com/api/search?q=contract&file_type=document" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Testing

```bash
# Run unit tests
cd /opt/kasaai/apps/drive/backend
/opt/kasaai/apps/venv/bin/pytest tests/

# Run with coverage
/opt/kasaai/apps/venv/bin/pytest --cov=app tests/
```

## Security

- **Authentication**: All endpoints require valid Supabase JWT token
- **Authorization**: Organization-based access control
- **File Validation**: MIME type and magic byte checking
- **Rate Limiting**: Implemented on upload endpoints
- **Audit Logging**: All file operations logged
- **Encryption**: Files encrypted in transit (HTTPS/WebDAV)

## Monitoring

```bash
# Check service status
sudo systemctl status kasaai-drive-backend

# View logs
sudo journalctl -u kasaai-drive-backend -f

# Monitor storage usage
mongosh --eval "db.drive_items.aggregate([
  {$match: {organization_id: 'org_123', is_deleted: false}},
  {$group: {_id: null, total: {$sum: '$size'}}}
])"
```

## Roadmap

- [ ] File versioning and history
- [ ] Advanced sharing (teams, groups)
- [ ] File previews (thumbnails, PDF viewer)
- [ ] Collaborative editing
- [ ] File comments and annotations
- [ ] Automatic file organization (AI-powered)
- [ ] Advanced search (OCR, content indexing)
- [ ] Mobile apps (iOS, Android)
- [ ] Desktop sync client
- [ ] Trash auto-cleanup (30 days)

## License

Copyright © 2025 AI Labs Africa. All rights reserved.

## Support

For support, contact: support@ailabsafrica.com
