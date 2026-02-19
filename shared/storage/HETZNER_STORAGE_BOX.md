# Hetzner Storage Box Integration

Centralized storage service for all KasaAI applications using Hetzner Storage Box.

## Overview

The Hetzner Storage Box provides reliable, scalable cloud storage accessible via multiple protocols:
- **WebDAV (HTTPS)** - Primary protocol, best for programmatic access
- **SFTP (SSH)** - Alternative protocol, good for large files
- **Samba/CIFS** - For Windows integration (experimental)

## Credentials

```
Username: u497034-sub1
Host: u497034-sub1.your-storagebox.de
Samba Share: \\u497034-sub1.your-storagebox.de\u497034-sub1
Password: Set in environment variable HETZNER_STORAGE_PASSWORD
```

## Installation

### Required Dependencies

```bash
# WebDAV client (recommended)
pip install webdavclient3

# SFTP client (alternative)
pip install paramiko

# Optional: Samba/CIFS client
pip install pysmb
```

### Environment Variables

Add to `/opt/kasaai/.env`:

```bash
# Hetzner Storage Box Configuration
HETZNER_STORAGE_USERNAME=u497034-sub1
HETZNER_STORAGE_PASSWORD=AILabsAdm1n123%
HETZNER_STORAGE_HOST=u497034-sub1.your-storagebox.de
HETZNER_STORAGE_PROTOCOL=webdav  # or sftp
HETZNER_STORAGE_BASE_PATH=kasaai  # Base directory for all apps
```

## Usage Examples

### Basic File Upload/Download

```python
from apps.shared.storage.hetzner_storage_box import HetznerStorageBox, StorageProtocol

# Initialize storage
storage = HetznerStorageBox(
    protocol=StorageProtocol.WEBDAV,
    base_path="kasaai/studyflow"  # App-specific directory
)

# Connect
await storage.connect()

# Upload file
await storage.upload_file(
    local_path="/tmp/document.pdf",
    remote_path="materials/chapter1.pdf"
)
# Actual path: /kasaai/studyflow/materials/chapter1.pdf

# Download file
await storage.download_file(
    remote_path="materials/chapter1.pdf",
    local_path="/tmp/downloaded.pdf"
)

# Disconnect when done
await storage.disconnect()
```

### Using Context Manager

```python
from apps.shared.storage.hetzner_storage_box import HetznerStorageBox

# Automatic connection/disconnection
with HetznerStorageBox(base_path="kasaai/inkwave") as storage:
    # Upload audiobook
    await storage.upload_file(
        local_path="/tmp/audiobook.mp3",
        remote_path="books/book_123/audio.mp3"
    )

    # List files
    files = await storage.list_files("books/book_123/")
    for file in files:
        print(f"{file['name']}: {file['size']} bytes")
```

### Using Global Singleton

```python
from apps.shared.storage.hetzner_storage_box import get_storage

# Get global storage instance (auto-connects)
storage = await get_storage(base_path="kasaai/churchflow")

# Upload conference materials
await storage.upload_file(
    local_path="/tmp/conference_program.pdf",
    remote_path="conferences/2025/program.pdf"
)

# Check if file exists
exists = await storage.file_exists("conferences/2025/program.pdf")
```

### Directory Management

```python
storage = await get_storage(base_path="kasaai/eventflow")

# Create directory structure
await storage.create_directory("events/2025/annual_gala")

# List all files recursively
files = await storage.list_files("events/", recursive=True)

# Get file metadata
info = await storage.get_file_info("events/2025/annual_gala/poster.jpg")
print(f"Size: {info['size']} bytes")
print(f"Modified: {info['modified']}")
```

### Progress Tracking

```python
def upload_progress(bytes_transferred, total_bytes):
    """Progress callback for large file uploads."""
    percent = (bytes_transferred / total_bytes) * 100
    print(f"Upload progress: {percent:.1f}%")

storage = await get_storage()

# Upload with progress tracking (SFTP only)
storage_sftp = HetznerStorageBox(protocol=StorageProtocol.SFTP)
await storage_sftp.connect()

await storage_sftp.upload_file(
    local_path="/tmp/large_video.mp4",
    remote_path="videos/training.mp4",
    progress_callback=upload_progress
)
```

### Error Handling

```python
from apps.shared.storage.hetzner_storage_box import (
    HetznerStorageBox,
    HetznerStorageBoxError
)

storage = await get_storage()

try:
    await storage.upload_file(
        local_path="/tmp/document.pdf",
        remote_path="documents/report.pdf",
        overwrite=False  # Don't overwrite existing
    )
except HetznerStorageBoxError as e:
    print(f"Upload failed: {e}")
    # Handle error (retry, notify user, etc.)
```

## App-Specific Usage Patterns

### StudyFlow - Study Materials

```python
from apps.shared.storage.hetzner_storage_box import get_storage

async def upload_study_material(user_id: str, class_id: str, file_path: str, filename: str):
    """Upload study material for a class."""
    storage = await get_storage(base_path="kasaai/studyflow")

    remote_path = f"users/{user_id}/classes/{class_id}/materials/{filename}"

    await storage.upload_file(
        local_path=file_path,
        remote_path=remote_path
    )

    return {
        "remote_path": remote_path,
        "url": f"https://{storage.host}/{storage.base_path}/{remote_path}"
    }
```

### InkWave - Audiobooks

```python
async def store_audiobook(book_id: str, audio_file: str, cover_image: str):
    """Store audiobook files."""
    storage = await get_storage(base_path="kasaai/inkwave")

    # Upload audio
    await storage.upload_file(
        local_path=audio_file,
        remote_path=f"books/{book_id}/audio.mp3"
    )

    # Upload cover
    await storage.upload_file(
        local_path=cover_image,
        remote_path=f"books/{book_id}/cover.jpg"
    )

    # List all book files
    files = await storage.list_files(f"books/{book_id}/")
    return files
```

### ChurchFlow - Conference Materials

```python
async def store_conference_documents(conference_id: str, documents: list):
    """Store conference documents and photos."""
    storage = await get_storage(base_path="kasaai/churchflow")

    uploaded = []

    for doc in documents:
        remote_path = f"conferences/{conference_id}/{doc['type']}/{doc['filename']}"

        await storage.upload_file(
            local_path=doc['path'],
            remote_path=remote_path
        )

        uploaded.append({
            "filename": doc['filename'],
            "remote_path": remote_path,
            "type": doc['type']
        })

    return uploaded
```

### EventFlow - Event Resources

```python
async def manage_event_files(event_id: str):
    """Manage event planning files."""
    storage = await get_storage(base_path="kasaai/eventflow")

    event_dir = f"events/{event_id}/"

    # Create event directory structure
    await storage.create_directory(f"{event_dir}documents")
    await storage.create_directory(f"{event_dir}media")
    await storage.create_directory(f"{event_dir}contracts")

    # List all event files
    files = await storage.list_files(event_dir, recursive=True)

    # Organize by type
    organized = {
        "documents": [],
        "media": [],
        "contracts": []
    }

    for file in files:
        if not file['is_directory']:
            if 'documents' in file['path']:
                organized['documents'].append(file)
            elif 'media' in file['path']:
                organized['media'].append(file)
            elif 'contracts' in file['path']:
                organized['contracts'].append(file)

    return organized
```

### ERP - Partnership Documents

```python
async def upload_partnership_proposal(
    partnership_id: str,
    org_id: str,
    file: UploadFile
) -> dict:
    """Upload partnership proposal documents to cloud storage."""
    from apps.shared.storage.hetzner_storage_box import get_storage, StorageProtocol
    import tempfile
    import os
    from datetime import datetime

    # Get storage instance
    storage = await get_storage(
        protocol=StorageProtocol.WEBDAV,
        base_path="erp/partnerships"
    )

    # Generate unique filename
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    file_ext = file.filename.rsplit(".", 1)[-1] if "." in file.filename else ""
    safe_filename = f"proposal_{timestamp}.{file_ext}" if file_ext else f"proposal_{timestamp}"

    # Create remote path
    remote_path = f"{org_id}/{partnership_id}/proposals/{safe_filename}"

    # Save uploaded file to temporary location
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_ext}") as temp_file:
        content = await file.read()
        temp_file.write(content)
        temp_path = temp_file.name

    try:
        # Upload to Hetzner Storage Box
        await storage.upload_file(temp_path, remote_path)

        return {
            "filename": safe_filename,
            "remote_path": remote_path,
            "size": len(content),
            "uploaded_at": datetime.utcnow().isoformat()
        }
    finally:
        # Clean up temporary file
        if os.path.exists(temp_path):
            os.unlink(temp_path)

async def download_partnership_file(
    partnership_id: str,
    org_id: str,
    file_type: str,
    filename: str
) -> bytes:
    """Download partnership file from cloud storage."""
    from apps.shared.storage.hetzner_storage_box import get_storage, StorageProtocol
    import tempfile
    import os

    # Get storage instance
    storage = await get_storage(
        protocol=StorageProtocol.WEBDAV,
        base_path="erp/partnerships"
    )

    # Construct remote file path
    remote_path = f"{org_id}/{partnership_id}/{file_type}/{filename}"

    # Download to temporary file
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_path = temp_file.name

    try:
        # Download from Hetzner Storage Box
        await storage.download_file(remote_path, temp_path)

        # Read file content
        with open(temp_path, "rb") as f:
            content = f.read()

        return content
    finally:
        # Clean up temporary file
        if os.path.exists(temp_path):
            os.unlink(temp_path)
```

**ERP File Structure:**
```
erp/partnerships/
├── {org_id}/
│   ├── {partnership_id}/
│   │   ├── proposals/
│   │   │   ├── proposal_20251108_094533.pdf
│   │   │   └── proposal_20251109_102145.docx
│   │   ├── contracts/
│   │   │   └── contract_20251110_151230.pdf
│   │   └── documents/
│   │       ├── document_20251108_083045.pdf
│   │       └── document_20251112_141522.xlsx
```

## Best Practices

### 1. Directory Structure

Organize files by app and purpose:

```
/kasaai/
├── studyflow/
│   ├── users/
│   │   └── {user_id}/
│   │       └── classes/
│   │           └── {class_id}/
│   │               └── materials/
│   ├── schools/
│   └── shared/
├── inkwave/
│   ├── books/
│   │   └── {book_id}/
│   │       ├── audio.mp3
│   │       └── cover.jpg
│   └── user_progress/
├── churchflow/
│   ├── conferences/
│   │   └── {conference_id}/
│   │       ├── documents/
│   │       ├── photos/
│   │       └── recordings/
│   └── branches/
├── eventflow/
│   ├── events/
│   │   └── {event_id}/
│   │       ├── documents/
│   │       ├── media/
│   │       └── contracts/
│   └── templates/
└── voice-lab/
    ├── voice_clones/
    └── tts_cache/
```

### 2. File Naming Conventions

Use consistent, safe filenames:

```python
import re
from pathlib import Path

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for storage."""
    # Remove special characters
    filename = re.sub(r'[^\w\s\-\.]', '', filename)

    # Replace spaces with underscores
    filename = filename.replace(' ', '_')

    # Lowercase
    filename = filename.lower()

    return filename

# Usage
safe_name = sanitize_filename("My Document (2025).pdf")
# Result: "my_document_2025.pdf"
```

### 3. Large File Handling

For files > 100MB, use SFTP with progress tracking:

```python
async def upload_large_file(local_path: str, remote_path: str):
    """Upload large file with SFTP and progress tracking."""
    storage = HetznerStorageBox(protocol=StorageProtocol.SFTP)
    await storage.connect()

    def progress(transferred, total):
        percent = (transferred / total) * 100
        print(f"\rProgress: {percent:.1f}%", end='', flush=True)

    try:
        await storage.upload_file(
            local_path=local_path,
            remote_path=remote_path,
            progress_callback=progress
        )
        print("\nUpload complete!")
    finally:
        await storage.disconnect()
```

### 4. Error Handling and Retries

Implement retry logic for network failures:

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
async def upload_with_retry(storage, local_path, remote_path):
    """Upload with automatic retries."""
    return await storage.upload_file(local_path, remote_path)
```

### 5. Temporary Files Cleanup

Clean up temporary files after upload:

```python
import os
import tempfile

async def process_and_upload(data: bytes, filename: str):
    """Process data and upload, cleaning up temp files."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".tmp") as tmp:
        tmp.write(data)
        tmp_path = tmp.name

    try:
        storage = await get_storage()
        await storage.upload_file(tmp_path, filename)
    finally:
        os.unlink(tmp_path)  # Always clean up
```

## Performance Considerations

### WebDAV vs SFTP

| Feature | WebDAV | SFTP |
|---------|--------|------|
| **Speed** | Fast for small files | Better for large files |
| **Reliability** | High (HTTPS) | High (SSH) |
| **Progress Tracking** | No | Yes |
| **Ease of Use** | Simpler API | More features |
| **Recommended For** | Documents, images | Videos, large datasets |

### Caching

Implement local caching for frequently accessed files:

```python
import hashlib
from pathlib import Path

class CachedStorage:
    """Storage with local file caching."""

    def __init__(self, cache_dir: str = "/tmp/storage_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.storage = None

    async def get_file(self, remote_path: str) -> str:
        """Get file (from cache if available)."""
        # Generate cache key
        cache_key = hashlib.md5(remote_path.encode()).hexdigest()
        cache_path = self.cache_dir / cache_key

        # Check cache
        if cache_path.exists():
            return str(cache_path)

        # Download to cache
        if not self.storage:
            self.storage = await get_storage()

        await self.storage.download_file(remote_path, str(cache_path))
        return str(cache_path)
```

## Security Notes

1. **Password Protection**: Store password in environment variable, never in code
2. **SSL/TLS**: WebDAV uses HTTPS, SFTP uses SSH encryption
3. **Access Control**: Use app-specific base paths to isolate data
4. **File Validation**: Validate file types and sizes before upload
5. **Audit Logging**: Log all file operations for security auditing

## Troubleshooting

### Connection Issues

```python
# Test connection
storage = HetznerStorageBox()
try:
    await storage.connect()
    print("✅ Connected successfully")
except HetznerStorageBoxError as e:
    print(f"❌ Connection failed: {e}")
    # Check: password, hostname, firewall, network
```

### Permission Issues

```bash
# Check WebDAV access
curl -u u497034-sub1:PASSWORD https://u497034-sub1.your-storagebox.de/

# Check SFTP access
sftp -P 23 u497034-sub1@u497034-sub1.your-storagebox.de
```

### Large File Timeouts

```python
# Increase timeout for large files
storage = HetznerStorageBox()
if storage.protocol == StorageProtocol.WEBDAV:
    storage.webdav_client.timeout = 300  # 5 minutes
```

## API Reference

See inline documentation in `hetzner_storage_box.py` for full API details.

---

**Support**: For issues or questions, refer to [Hetzner Storage Box Documentation](https://docs.hetzner.com/storage/storage-box/)
