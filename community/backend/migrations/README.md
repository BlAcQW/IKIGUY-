# Database Migrations

This directory contains database migration scripts for the African Language Community Platform.

## Overview

Migrations are used to evolve the database schema over time in a controlled, versioned manner. Each migration:
- Has a unique sequential ID (001, 002, etc.)
- Includes forward migration (changes to apply)
- Includes rollback script (how to undo changes)
- Is tracked in the `migrations` collection

## Running Migrations

### Run All Pending Migrations
```bash
cd /opt/kasaai/apps/community/backend/migrations
python run_migrations.py
```

### Run Specific Migration
```bash
python run_migrations.py --migration 001_add_mlops_collections
```

### Check Migration Status
```bash
python run_migrations.py --status
```

### Rollback Migration
```bash
python run_migrations.py --rollback 001_add_mlops_collections
```

## Migration List

### 001_add_mlops_collections
**Status:** Pending
**Description:** Add MLOps collections and enhance existing models

**Changes:**
- Creates new collections:
  - `ml_models` - ML model registry with versioning
  - `ml_training_pipelines` - Training pipeline tracking
  - `dataset_versions` - Dataset version control
  - `file_uploads` - User upload tracking
  - `resource_links` - External resource management
  - `model_language_associations` - Multi-language model linking
  - `storage_manifests` - File system indexing

- Enhances existing collections:
  - `external_datasets` - Adds versioning, storage paths, MLOps tracking
  - `languages` - Adds dataset/model/pipeline tracking, performance metrics

**Indexes Created:**
- Unique indexes on UUIDs and version combinations
- Compound indexes for common query patterns
- Performance indexes on status fields and timestamps

**Validation Rules:**
- Schema validation for required fields
- Pattern validation for semantic versions
- Enum validation for status fields

## Creating New Migrations

1. Create migration file: `00X_description.py`
2. Create rollback file: `00X_rollback_description.py`
3. Add migration ID to `MIGRATIONS` list in `run_migrations.py`
4. Update this README with migration details

### Migration Template

```python
"""
Migration 00X: Description

What this migration does and why.
"""

import os
import sys
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()


async def run_migration():
    """Execute the migration."""

    mongodb_url = os.getenv("MONGODB_URL")
    db_name = os.getenv("MONGODB_DATABASE", "african_language_community")

    client = AsyncIOMotorClient(mongodb_url)
    db = client[db_name]

    try:
        await db.command("ping")

        # Your migration code here

        # Record migration
        await db.migrations.insert_one({
            "migration_id": "00X_description",
            "description": "What this does",
            "executed_at": datetime.utcnow(),
            "status": "completed"
        })

        print("✅ Migration 00X completed")

    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(run_migration())
```

## Best Practices

1. **Always test migrations** on development data before production
2. **Backup database** before running migrations in production
3. **Never modify** executed migrations - create new ones instead
4. **Test rollbacks** to ensure they work correctly
5. **Use transactions** where possible for atomic operations
6. **Document breaking changes** in migration description
7. **Update Pydantic models** to match schema changes

## Migration Tracking

Migrations are tracked in the `migrations` collection:

```javascript
{
  "_id": ObjectId("..."),
  "migration_id": "001_add_mlops_collections",
  "description": "Add MLOps collections and enhance existing models",
  "executed_at": ISODate("2025-01-15T10:30:00Z"),
  "status": "completed",  // or "rolled_back"
  "rolled_back_at": null
}
```

## Environment Variables

Required environment variables:
- `MONGODB_URL` - MongoDB connection string
- `MONGODB_DATABASE` - Database name (default: african_language_community)

These should be defined in `/opt/kasaai/apps/community/backend/.env`

## Troubleshooting

### Migration fails with "already executed"
Check migration status: `python run_migrations.py --status`

### Connection errors
Verify MongoDB URL in `.env` file and ensure MongoDB is running

### Permission errors
Ensure the MongoDB user has necessary permissions for schema modifications

### Rollback fails
Check that rollback script exists and migration was actually executed
