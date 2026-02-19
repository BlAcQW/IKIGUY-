# Database Backup System

**Version:** 1.0
**Date:** 2025-10-26
**Status:** Implemented

---

## Overview

Centralized database backup system for all KasaAI applications. Provides automated and manual backup capabilities for MongoDB and PostgreSQL databases with secure storage in Hetzner Storage Box.

### Key Features

✅ **MongoDB & PostgreSQL Support** - Backup both database types
✅ **Automated Backups** - Daily, weekly, and monthly schedules via cron
✅ **Manual Backups** - On-demand backups through admin UI
✅ **Secure Storage** - Encrypted backups in Hetzner Storage Box
✅ **Retention Policy** - Automatic cleanup of old backups
✅ **Restore Functionality** - Full database restore from any backup
✅ **Organization Scoping** - Backups organized by organization
✅ **Universal Admin Only** - Restricted to universal administrators

---

## Architecture

### Components

```
┌─────────────────────────────────────────────────────────────┐
│                    KasaAI Backup System                      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────┐    ┌────────────────────────────┐      │
│  │  Cron Jobs      │    │  Admin UI (b2c-portal)     │      │
│  │  ───────────    │    │  ──────────────────        │      │
│  │  • Daily (2AM)  │    │  • Create backup           │      │
│  │  • Weekly (3AM) │    │  • View backups            │      │
│  │  • Monthly (4AM)│    │  • Restore backup          │      │
│  │  • Cleanup (5AM)│    │  • Cleanup old backups     │      │
│  └────────┬────────┘    └──────────┬─────────────────┘      │
│           │                         │                         │
│           └──────────┬──────────────┘                        │
│                      │                                        │
│           ┌──────────▼────────────┐                          │
│           │  Core Backend API      │                          │
│           │  /backups/*            │                          │
│           └──────────┬─────────────┘                         │
│                      │                                        │
│           ┌──────────▼─────────────┐                         │
│           │  Backup Service         │                         │
│           │  (@apps/shared/backup/) │                         │
│           │  ────────────────────── │                         │
│           │  • backup_database()    │                         │
│           │  • restore_database()   │                         │
│           │  • list_backups()       │                         │
│           │  • cleanup_old_backups()│                         │
│           └──────────┬─────────────┘                         │
│                      │                                        │
│        ┌─────────────┼─────────────┐                         │
│        │             │              │                         │
│   ┌────▼─────┐  ┌───▼────┐  ┌─────▼────────┐                │
│   │ mongodump│  │pg_dump │  │Hetzner Storage│                │
│   │          │  │        │  │     Box       │                │
│   └──────────┘  └────────┘  └───────────────┘                │
└─────────────────────────────────────────────────────────────┘
```

---

## Storage Structure

Backups are organized in Hetzner Storage Box with the following structure:

```
/backups/
├── {organization_id}/
│   ├── mongodb/
│   │   ├── {database_name}/
│   │   │   ├── daily/
│   │   │   │   ├── backup_2025-10-26_02-00-00.tar.gz
│   │   │   │   ├── backup_2025-10-26_02-00-00.metadata.json
│   │   │   │   └── ...
│   │   │   ├── weekly/
│   │   │   │   └── ...
│   │   │   ├── monthly/
│   │   │   │   └── ...
│   │   │   └── manual/
│   │   │       └── ...
│   │   └── ...
│   └── postgresql/
│       ├── {database_name}/
│       │   ├── daily/
│       │   ├── weekly/
│       │   ├── monthly/
│       │   └── manual/
│       └── ...
└── ...
```

---

## Retention Policy

Automated backup cleanup runs daily at 5 AM.

| Backup Type | Retention Period | Cleanup Rule |
|-------------|------------------|--------------|
| **Daily**   | 7 days          | Delete backups older than 7 days |
| **Weekly**  | 4 weeks         | Delete backups older than 4 weeks |
| **Monthly** | 12 months       | Delete backups older than 365 days |
| **Manual**  | Forever         | Never deleted automatically |

### Implementation

Located in: `/opt/kasaai/apps/shared/backup/database_backup_service.py`

```python
async def cleanup_old_backups(self):
    """
    Clean up old backups based on retention policy.
    """
    now = datetime.utcnow()
    all_backups = await self.list_backups()

    for backup in all_backups:
        should_delete = False
        age = now - backup.timestamp

        if backup.backup_type == BackupType.DAILY:
            if age > timedelta(days=7):
                should_delete = True

        elif backup.backup_type == BackupType.WEEKLY:
            if age > timedelta(weeks=4):
                should_delete = True

        elif backup.backup_type == BackupType.MONTHLY:
            if age > timedelta(days=365):
                should_delete = True

        if should_delete:
            await self.storage.delete_file(backup.backup_path)
            await self.storage.delete_file(metadata_path)
```

---

## Backup Process

### MongoDB Backup

1. **Run mongodump**: `mongodump --uri {uri} --db {db_name} --out {output_dir} --gzip`
2. **Compress**: Create tar.gz archive of dump directory
3. **Upload**: Upload to Hetzner Storage Box at organized path
4. **Metadata**: Store backup metadata (timestamp, size, status)

### PostgreSQL Backup

1. **Run pg_dump**: `pg_dump -h {host} -U {user} -d {db_name} -F c -f {output_file}`
2. **Compress**: Create tar.gz archive (pg_dump custom format is already compressed)
3. **Upload**: Upload to Hetzner Storage Box at organized path
4. **Metadata**: Store backup metadata (timestamp, size, status)

---

## Restore Process

### Safety Checks

⚠️ **WARNING**: Restore operations are DESTRUCTIVE and will:
- Drop ALL existing data in the target database
- Replace it with backup data
- Cannot be undone

### Steps

1. **Download Backup**: Download backup file from Hetzner Storage Box
2. **Download Metadata**: Verify backup integrity and details
3. **Extract**: Uncompress tar.gz archive
4. **Restore Database**:
   - **MongoDB**: `mongorestore --uri {uri} --db {db_name} --drop {dump_dir}`
   - **PostgreSQL**: `pg_restore -h {host} -U {user} -d {db_name} --clean -F c {dump_file}`
5. **Cleanup**: Remove temporary files

---

## Automated Backup Schedule

### Cron Configuration

Located in: `/opt/kasaai/apps/shared/backup/setup_cron.sh`

```bash
# Daily backups at 2 AM
0 2 * * * cd /opt/kasaai && /opt/kasaai/apps/venv/bin/python /opt/kasaai/apps/shared/backup/backup_cron.py --backup-type daily

# Weekly backups on Sunday at 3 AM
0 3 * * 0 cd /opt/kasaai && /opt/kasaai/apps/venv/bin/python /opt/kasaai/apps/shared/backup/backup_cron.py --backup-type weekly

# Monthly backups on 1st of month at 4 AM
0 4 1 * * cd /opt/kasaai && /opt/kasaai/apps/venv/bin/python /opt/kasaai/apps/shared/backup/backup_cron.py --backup-type monthly

# Cleanup old backups daily at 5 AM
0 5 * * * cd /opt/kasaai && /opt/kasaai/apps/venv/bin/python /opt/kasaai/apps/shared/backup/backup_cron.py --cleanup-only
```

### Setup Instructions

1. **Run setup script**:
   ```bash
   cd /opt/kasaai/apps/shared/backup
   sudo bash setup_cron.sh
   ```

2. **Verify cron entries**:
   ```bash
   crontab -l | grep "KasaAI Database Backups"
   ```

3. **View logs**:
   ```bash
   tail -f /var/log/kasaai_backups.log
   ```

### Manual Backup Execution

```bash
# Daily backup
/opt/kasaai/apps/venv/bin/python /opt/kasaai/apps/shared/backup/backup_cron.py --backup-type daily

# Weekly backup
/opt/kasaai/apps/venv/bin/python /opt/kasaai/apps/shared/backup/backup_cron.py --backup-type weekly

# Monthly backup
/opt/kasaai/apps/venv/bin/python /opt/kasaai/apps/shared/backup/backup_cron.py --backup-type monthly

# Cleanup only
/opt/kasaai/apps/venv/bin/python /opt/kasaai/apps/shared/backup/backup_cron.py --cleanup-only
```

---

## API Endpoints

All endpoints require **Universal Admin** authentication.

### POST /backups/

Create a database backup.

**Request:**
```json
{
  "database_name": "kasaai_core",
  "database_type": "mongodb",
  "organization_id": "org_123",
  "backup_type": "manual"
}
```

**Response:**
```json
{
  "database_name": "kasaai_core",
  "database_type": "mongodb",
  "backup_type": "manual",
  "organization_id": "org_123",
  "timestamp": "2025-10-26T12:00:00",
  "file_size": 5500000,
  "compressed_size": 2400000,
  "backup_path": "org_123/mongodb/kasaai_core/manual/backup_2025-10-26_12-00-00.tar.gz",
  "status": "completed"
}
```

### GET /backups/

List all backups with optional filters.

**Query Parameters:**
- `organization_id` - Filter by organization
- `database_name` - Filter by database name
- `database_type` - Filter by type (mongodb/postgresql)
- `backup_type` - Filter by backup type (daily/weekly/monthly/manual)

**Response:**
```json
[
  {
    "database_name": "kasaai_core",
    "database_type": "mongodb",
    "backup_type": "daily",
    "timestamp": "2025-10-26T02:00:00",
    "compressed_size": 2400000,
    "status": "completed"
  }
]
```

### POST /backups/restore

Restore database from backup.

⚠️ **DESTRUCTIVE OPERATION** - Drops all existing data!

**Request:**
```json
{
  "backup_path": "org_123/mongodb/kasaai_core/daily/backup_2025-10-26_02-00-00.tar.gz",
  "target_database_name": null
}
```

**Response:**
```json
{
  "success": true,
  "message": "Database restored successfully",
  "backup_path": "...",
  "target_database": "kasaai_core"
}
```

### DELETE /backups/cleanup

Clean up old backups based on retention policy.

**Response:**
```json
{
  "success": true,
  "message": "Backup cleanup completed successfully"
}
```

### GET /backups/stats

Get backup statistics.

**Response:**
```json
{
  "total_backups": 42,
  "total_size_bytes": 128000000,
  "total_size_mb": 122.07,
  "by_type": {
    "daily": 7,
    "weekly": 4,
    "monthly": 12,
    "manual": 19
  },
  "by_database": {
    "mongodb:kasaai_core": 15,
    "mongodb:churchflow": 8,
    "postgresql:kasaai_core": 10
  },
  "latest_backup": {
    "database_name": "kasaai_core",
    "timestamp": "2025-10-26T02:00:00"
  }
}
```

### GET /backups/databases

List available databases for backup.

**Response:**
```json
{
  "mongodb": [
    "kasaai_core",
    "churchflow",
    "eventflow",
    "inkwave",
    "studyflow"
  ],
  "postgresql": [
    "kasaai_core",
    "n8n",
    "community"
  ]
}
```

---

## Admin UI

Located at: **Admin → Database** (`/admin/database`)

### Features

1. **Backup Statistics Dashboard**
   - Total backups count
   - Total storage used
   - Daily backups count
   - Latest backup timestamp

2. **Create Backup**
   - Select database type (MongoDB/PostgreSQL)
   - Select database name from dropdown
   - Choose backup type (Manual/Daily/Weekly/Monthly)
   - Create backup button

3. **Retention Policy Display**
   - Daily: 7 days (with count)
   - Weekly: 4 weeks (with count)
   - Monthly: 12 months (with count)
   - Manual: Forever (with count)

4. **Backup List**
   - Searchable/filterable table
   - Filter by database type
   - Filter by backup type
   - Columns: Database, Type, Backup Type, Timestamp, Size, Status
   - Restore button for each backup

5. **Restore Dialog**
   - Confirmation dialog with backup details
   - ⚠️ Warning about data loss
   - Restore or cancel

6. **Cleanup Button**
   - Manual trigger for retention policy cleanup
   - Removes old backups based on retention rules

---

## Files and Locations

### Backend

```
/opt/kasaai/apps/shared/backup/
├── __init__.py                      # Module exports
├── database_backup_service.py       # Main backup service (900+ lines)
├── backup_cron.py                   # Automated backup script
└── setup_cron.sh                    # Cron setup helper

/opt/kasaai/apps/core_backend/backend/routes/
└── backups.py                       # API endpoints (500+ lines)

/opt/kasaai/apps/core_backend/backend/
└── main.py                          # Router registration
```

### Frontend

```
/opt/kasaai/apps/b2c-portal/src/pages/admin/
└── Database.tsx                     # Admin UI (800+ lines)
```

### Logs

```
/var/log/kasaai_backups.log          # Backup cron job logs
```

---

## Security

### Authentication

- All backup endpoints require **universal admin** role
- Checked via: `OrganizationService.is_universal_admin(user_id, email)`
- Returns 403 Forbidden for non-universal admins

### Authorization Check

```python
def check_universal_admin(user: dict = Depends(get_current_user_mongo)):
    """Check if user is universal admin."""
    user_id = user.get("tenant_id") or user.get("account_id") or user.get("sub")
    user_email = user.get("email", "")

    org_service = OrganizationService()
    if not org_service.is_universal_admin(user_id, user_email):
        raise HTTPException(
            status_code=403,
            detail="Only universal administrators can manage backups"
        )

    return user
```

### Data Protection

1. **Encryption**: All backups stored in Hetzner Storage Box (encrypted at rest)
2. **Transport**: HTTPS/SFTP for upload/download
3. **Compression**: gzip compression reduces storage costs
4. **Isolation**: Organization-scoped backup paths prevent cross-contamination

---

## Best Practices

### 3-2-1 Backup Rule

✅ **3 copies** - Original + Daily + Weekly/Monthly backups
✅ **2 media types** - Local database + Remote storage (Hetzner)
✅ **1 offsite** - Hetzner Storage Box is offsite from servers

### Recommendations

1. **Test Restores Regularly**: Verify backups work by testing restore to test database
2. **Monitor Backup Logs**: Check `/var/log/kasaai_backups.log` for failures
3. **Check Storage Space**: Monitor Hetzner Storage Box usage
4. **Backup Before Major Changes**: Create manual backup before migrations or updates
5. **Document Restore Procedures**: Ensure team knows how to restore in emergency
6. **Set Up Alerts**: Configure monitoring for backup failures

---

## Troubleshooting

### Backup Fails

**Symptom**: Backup completes with error status

**Solutions**:
1. Check database credentials in `.env`
2. Verify mongodump/pg_dump are installed:
   ```bash
   which mongodump
   which pg_dump
   ```
3. Check Hetzner Storage Box credentials:
   ```bash
   echo $HETZNER_STORAGE_PASSWORD
   ```
4. Review logs:
   ```bash
   tail -100 /var/log/kasaai_backups.log
   ```

### Restore Fails

**Symptom**: Restore operation throws error

**Solutions**:
1. Verify target database exists
2. Check database permissions
3. Ensure enough disk space for extraction
4. Review error in logs

### Cron Not Running

**Symptom**: No backups created automatically

**Solutions**:
1. Verify cron entries:
   ```bash
   crontab -l | grep "KasaAI"
   ```
2. Check cron service:
   ```bash
   systemctl status cron
   ```
3. Verify Python path and script path in crontab
4. Check log file permissions

### Storage Space Issues

**Symptom**: Backup upload fails due to space

**Solutions**:
1. Check Hetzner Storage Box usage
2. Run manual cleanup:
   ```bash
   /opt/kasaai/apps/venv/bin/python /opt/kasaai/apps/shared/backup/backup_cron.py --cleanup-only
   ```
3. Adjust retention policy if needed
4. Upgrade storage plan

---

## Testing

### Manual Test Workflow

1. **Create Test Backup**:
   ```bash
   # Via API
   curl -X POST https://api.ailabsafrica.com/backups/ \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "database_name": "kasaai_core",
       "database_type": "mongodb",
       "organization_id": "test",
       "backup_type": "manual"
     }'
   ```

2. **List Backups**:
   ```bash
   curl https://api.ailabsafrica.com/backups/ \
     -H "Authorization: Bearer $TOKEN"
   ```

3. **Create Test Database**:
   ```bash
   # MongoDB
   mongosh $MONGODB_URL --eval "use kasaai_core_test"

   # PostgreSQL
   PGPASSWORD=$POSTGRES_PASSWORD psql -h localhost -U postgres -c "CREATE DATABASE kasaai_core_test"
   ```

4. **Restore to Test Database**:
   ```bash
   curl -X POST https://api.ailabsafrica.com/backups/restore \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "backup_path": "test/mongodb/kasaai_core/manual/backup_2025-10-26_12-00-00.tar.gz",
       "target_database_name": "kasaai_core_test"
     }'
   ```

5. **Verify Data**:
   ```bash
   # MongoDB
   mongosh $MONGODB_URL/kasaai_core_test --eval "db.users.countDocuments()"

   # PostgreSQL
   PGPASSWORD=$POSTGRES_PASSWORD psql -h localhost -U postgres kasaai_core_test -c "SELECT COUNT(*) FROM users"
   ```

6. **Cleanup Test**:
   ```bash
   # MongoDB
   mongosh $MONGODB_URL --eval "use kasaai_core_test; db.dropDatabase()"

   # PostgreSQL
   PGPASSWORD=$POSTGRES_PASSWORD psql -h localhost -U postgres -c "DROP DATABASE kasaai_core_test"
   ```

---

## Environment Variables

Required environment variables in `/opt/kasaai/.env`:

```bash
# MongoDB
MONGODB_URL=mongodb://admin:password@127.0.0.1:27017/kasaai_core?authSource=admin

# PostgreSQL
POSTGRES_SERVER=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password
POSTGRES_DB_CORE=kasaai_core

# Hetzner Storage Box
HETZNER_STORAGE_USERNAME=u497034-sub1
HETZNER_STORAGE_HOST=u497034-sub1.your-storagebox.de
HETZNER_STORAGE_PASSWORD=your_password

# Optional
DEFAULT_ORGANIZATION_ID=default  # Default org ID for automated backups
```

---

## Future Enhancements

### Potential Improvements

1. **Incremental Backups**
   - Only backup changes since last backup
   - Reduce backup time and storage

2. **Backup Verification**
   - Automatic verify after backup
   - Checksum validation

3. **Compression Options**
   - Support different compression levels
   - zstd, bzip2 alternatives

4. **Backup Encryption**
   - Client-side encryption before upload
   - Password-protected backups

5. **Multi-Destination Support**
   - Backup to multiple storage providers
   - S3, Google Cloud Storage, etc.

6. **Notification System**
   - Email/Slack alerts for backup failures
   - Daily backup summary reports

7. **Point-in-Time Recovery**
   - Binary log/WAL archiving
   - Restore to specific timestamp

8. **Backup Size Optimization**
   - Exclude temporary collections
   - Configurable exclusion lists

9. **Parallel Backups**
   - Backup multiple databases concurrently
   - Faster total backup time

10. **Restore Preview**
    - Preview backup contents before restore
    - Selective restore (specific collections/tables)

---

## Related Documentation

- [Hetzner Storage Box Integration](/opt/kasaai/apps/shared/storage/HETZNER_STORAGE_BOX.md)
- [Organization System](/opt/kasaai/apps/shared/ORGANIZATION_SYSTEM.md)
- [Authentication Setup](/opt/kasaai/apps/architecture/AUTHENTICATION_SETUP.md)

---

## Version History

| Version | Date       | Changes                                      |
|---------|------------|----------------------------------------------|
| 1.0     | 2025-10-26 | Initial implementation - MongoDB, PostgreSQL, automated backups, retention policy, admin UI |

---

**Maintained by:** AI Labs Africa
**Contact:** alfred.anyan@gmail.com
