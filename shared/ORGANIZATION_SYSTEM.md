# Centralized Organization System

**Version:** 1.0.0
**Last Updated:** 2025-10-26
**Status:** Production Ready

---

## Overview

The centralized organization system provides multi-tenant functionality for all KasaAI applications. Every user belongs to at least one organization, and all data is scoped to organizations.

### Key Features

✅ **Multi-Tenant Architecture** - Complete data isolation between organizations
✅ **Role-Based Access Control** - Admin and User roles per organization
✅ **Universal Admin** - Special role for platform administrators
✅ **Easy Integration** - Drop-in middleware and dependencies
✅ **Type-Safe** - Full Pydantic model support
✅ **Async-Ready** - Built on Motor (async MongoDB driver)

---

## Architecture

### Three-Tier Role System

1. **Universal Admin (`universal_admin`)**
   - Access to ALL organizations
   - Can perform any operation across the platform
   - Defined in environment variables
   - Used for platform administration and support

2. **Organization Admin (`admin`)**
   - Full access within their organization
   - Can manage organization settings
   - Can invite/remove users
   - Can perform all CRUD operations on organization data

3. **Organization User (`user`)**
   - Standard access within their organization
   - Can read and create data
   - Limited administrative capabilities
   - Permissions can be customized per user

### Data Model

```
Organization
├── id: str (UUID)
├── name: str (unique)
├── display_name: str
├── description: str
├── industry: str
├── settings: dict
└── is_active: bool

OrganizationUser
├── id: str (UUID)
├── organization_id: str
├── user_id: str (from auth system)
├── email: str
├── role: OrganizationRole (admin | user)
├── permissions: dict
└── is_active: bool
```

---

## Quick Start

### 1. Setup in Your FastAPI App

```python
# app/main.py
from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient
from apps.shared.middleware import OrganizationContextMiddleware
from apps.shared.services.organization_service import get_organization_service

app = FastAPI()

# Add organization context middleware
app.add_middleware(OrganizationContextMiddleware)

# Initialize organization service on startup
@app.on_event("startup")
async def startup():
    # Connect to MongoDB
    mongodb_url = os.getenv("MONGODB_URL")
    db_name = os.getenv("MONGODB_DATABASE", "your_app_db")

    client = AsyncIOMotorClient(mongodb_url)
    db = client[db_name]

    # Initialize organization service
    org_service = get_organization_service(db)
    await org_service.initialize_indexes()

    # Store in app state for access in routes
    app.state.org_service = org_service
```

### 2. Configure Environment Variables

```bash
# .env
MONGODB_URL=mongodb://admin:password@localhost:27017/
MONGODB_DATABASE=churchflow  # or eventflow, inkwave, studyflow

# Universal admins (comma-separated)
UNIVERSAL_ADMIN_EMAILS=admin@ailabsafrica.com,support@ailabsafrica.com
UNIVERSAL_ADMIN_USER_IDS=user_123abc,user_456def
```

### 3. Use in Your Routes

```python
# app/api/routes/events.py
from fastapi import APIRouter, Depends
from apps.shared.dependencies import require_organization_access, OrganizationScoped

router = APIRouter()

@router.get("/events")
async def get_events(
    org_id: str = Depends(require_organization_access)
):
    """Get all events for the organization."""
    # org_id is validated - user has access
    events = await db.events.find({"organization_id": org_id}).to_list(100)
    return {"events": events}


@router.post("/events")
async def create_event(
    event_data: EventCreate,
    scope: OrganizationScoped = Depends()
):
    """Create a new event."""
    # Add organization_id to the event
    event = Event(
        **event_data.dict(),
        organization_id=scope.org_id,
        created_by=scope.user["id"]
    )

    await db.events.insert_one(event.dict())
    return event


@router.delete("/events/{event_id}")
async def delete_event(
    event_id: str,
    scope: OrganizationScoped = Depends()
):
    """Delete an event (admin only)."""
    # Require admin role
    await scope.require_admin()

    result = await db.events.delete_one({
        "id": event_id,
        "organization_id": scope.org_id
    })

    return {"deleted": result.deleted_count > 0}
```

---

## API Endpoints

### Organization Management

Create dedicated organization management routes:

```python
# app/api/routes/organizations.py
from fastapi import APIRouter, Depends, HTTPException
from apps.shared.models import OrganizationCreate, OrganizationUpdate
from apps.shared.services.organization_service import get_organization_service
from apps.shared.dependencies import get_current_user

router = APIRouter(prefix="/api/v1/organizations", tags=["Organizations"])

@router.post("")
async def create_organization(
    org_data: OrganizationCreate,
    user: dict = Depends(get_current_user)
):
    """Create a new organization."""
    org_service = get_organization_service()
    organization = await org_service.create_organization(
        org_data,
        user["id"],
        user["email"]
    )
    return organization


@router.get("")
async def list_organizations(
    user: dict = Depends(get_current_user)
):
    """List all organizations for current user."""
    org_service = get_organization_service()
    user_orgs = await org_service.get_organizations_for_user(user["id"])

    # Fetch full organization details
    organizations = []
    for user_org in user_orgs:
        org = await org_service.get_organization(user_org.organization_id)
        if org:
            organizations.append({
                "organization": org,
                "role": user_org.role,
                "joined_at": user_org.joined_at
            })

    return {"organizations": organizations}


@router.get("/{organization_id}")
async def get_organization(
    organization_id: str,
    org_id: str = Depends(require_organization_access)
):
    """Get organization details."""
    org_service = get_organization_service()
    org = await org_service.get_organization(organization_id)

    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    return org


@router.patch("/{organization_id}")
async def update_organization(
    organization_id: str,
    update_data: OrganizationUpdate,
    scope: OrganizationScoped = Depends()
):
    """Update organization (admin only)."""
    await scope.require_admin()

    org_service = get_organization_service()
    org = await org_service.update_organization(organization_id, update_data)

    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    return org


@router.get("/{organization_id}/users")
async def list_organization_users(
    organization_id: str,
    org_id: str = Depends(require_organization_access)
):
    """List all users in organization."""
    org_service = get_organization_service()
    users = await org_service.get_users_in_organization(organization_id)
    return {"users": users}


@router.post("/{organization_id}/users")
async def invite_user(
    organization_id: str,
    invite_data: OrganizationInviteRequest,
    scope: OrganizationScoped = Depends()
):
    """Invite user to organization (admin only)."""
    await scope.require_admin()

    # TODO: Implement invitation system
    # - Generate invitation token
    # - Send invitation email
    # - Create invitation record

    return {"message": "Invitation sent", "email": invite_data.email}
```

---

## Frontend Integration

### Sending Organization Context

All API requests must include the `X-Organization-ID` header:

```typescript
// src/lib/api.ts
import axios from 'axios';

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add interceptor to include organization ID
apiClient.interceptors.request.use((config) => {
  const orgId = localStorage.getItem('current_organization_id');
  if (orgId) {
    config.headers['X-Organization-ID'] = orgId;
  }
  return config;
});

export default apiClient;
```

### Organization Selector Component

```typescript
// src/components/OrganizationSelector.tsx
import { useState, useEffect } from 'react';
import api from '../lib/api';

export function OrganizationSelector() {
  const [organizations, setOrganizations] = useState([]);
  const [currentOrgId, setCurrentOrgId] = useState(
    localStorage.getItem('current_organization_id')
  );

  useEffect(() => {
    // Fetch user's organizations
    api.get('/api/v1/organizations')
      .then(res => setOrganizations(res.data.organizations))
      .catch(err => console.error('Failed to fetch organizations:', err));
  }, []);

  const handleOrgChange = (orgId: string) => {
    localStorage.setItem('current_organization_id', orgId);
    setCurrentOrgId(orgId);
    window.location.reload(); // Reload to fetch new org data
  };

  return (
    <select
      value={currentOrgId || ''}
      onChange={(e) => handleOrgChange(e.target.value)}
    >
      {organizations.map((org) => (
        <option key={org.organization.id} value={org.organization.id}>
          {org.organization.display_name} ({org.role})
        </option>
      ))}
    </select>
  );
}
```

---

## Data Migration

### Migrating Existing Data

If you have existing data without organization IDs, use this migration script:

```python
# scripts/migrate_to_organizations.py
"""
Migrate existing data to organization system.

Usage:
    python scripts/migrate_to_organizations.py --app churchflow --org-name "Default Church"
"""

import asyncio
import argparse
from motor.motor_asyncio import AsyncIOMotorClient
from apps.shared.services.organization_service import get_organization_service
from apps.shared.models import OrganizationCreate

async def migrate_app_data(app_name: str, org_name: str):
    """Migrate app data to organization system."""

    # Connect to database
    mongodb_url = "mongodb://admin:password@localhost:27017/"
    client = AsyncIOMotorClient(mongodb_url)
    db = client[app_name]

    # Initialize organization service
    org_service = get_organization_service(db)
    await org_service.initialize_indexes()

    # Create default organization
    print(f"Creating default organization: {org_name}")
    org = await org_service.create_organization(
        OrganizationCreate(
            name=org_name.lower().replace(" ", "-"),
            display_name=org_name,
            description=f"Default organization for {app_name}"
        ),
        creator_user_id="system",
        creator_email="admin@ailabsafrica.com"
    )

    print(f"Created organization: {org.id}")

    # Update all collections to include organization_id
    collections_to_migrate = [
        "events", "tasks", "conferences", "speakers",  # ChurchFlow
        "books", "reading_sessions", "interactions",  # InkWave
        "study_sessions", "tutoring_sessions",        # StudyFlow
        # Add your app's collections here
    ]

    for collection_name in collections_to_migrate:
        try:
            collection = db[collection_name]

            # Count documents without organization_id
            count = await collection.count_documents({"organization_id": {"$exists": False}})

            if count > 0:
                print(f"Migrating {count} documents in {collection_name}...")

                # Update all documents to include organization_id
                result = await collection.update_many(
                    {"organization_id": {"$exists": False}},
                    {"$set": {"organization_id": org.id}}
                )

                print(f"✓ Updated {result.modified_count} documents in {collection_name}")
            else:
                print(f"✓ {collection_name} - no migration needed")

        except Exception as e:
            print(f"✗ Error migrating {collection_name}: {e}")

    print("\nMigration complete!")
    print(f"Organization ID: {org.id}")
    print(f"Organization Name: {org.display_name}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Migrate app data to organizations")
    parser.add_argument("--app", required=True, help="App name (churchflow, eventflow, etc.)")
    parser.add_argument("--org-name", required=True, help="Organization display name")

    args = parser.parse_args()

    asyncio.run(migrate_app_data(args.app, args.org_name))
```

---

## Testing

### Unit Tests

```python
# apps/shared/tests/test_organization_service.py
import pytest
from motor.motor_asyncio import AsyncIOMotorClient
from apps.shared.services.organization_service import get_organization_service
from apps.shared.models import OrganizationCreate, OrganizationRole

@pytest.fixture
async def org_service():
    """Create organization service for testing."""
    client = AsyncIOMotorClient("mongodb://localhost:27017/")
    db = client["test_organizations"]

    service = get_organization_service(db)
    await service.initialize_indexes()

    yield service

    # Cleanup
    await db.organizations.delete_many({})
    await db.organization_users.delete_many({})

@pytest.mark.asyncio
async def test_create_organization(org_service):
    """Test organization creation."""
    org_data = OrganizationCreate(
        name="test-org",
        display_name="Test Organization"
    )

    org = await org_service.create_organization(
        org_data,
        "user_123",
        "test@example.com"
    )

    assert org.id is not None
    assert org.name == "test-org"
    assert org.display_name == "Test Organization"

    # Verify creator is admin
    org_user = await org_service.get_organization_user(org.id, "user_123")
    assert org_user is not None
    assert org_user.role == OrganizationRole.ADMIN

@pytest.mark.asyncio
async def test_organization_access(org_service):
    """Test organization access validation."""
    org_data = OrganizationCreate(name="test-org", display_name="Test Org")
    org = await org_service.create_organization(org_data, "user_123", "test@example.com")

    # Creator should have access
    has_access = await org_service.has_access_to_organization(
        org.id, "user_123", "test@example.com"
    )
    assert has_access is True

    # Other user should not have access
    has_access = await org_service.has_access_to_organization(
        org.id, "user_456", "other@example.com"
    )
    assert has_access is False
```

---

## Best Practices

### 1. Always Scope Data to Organizations

```python
# ✅ Good
@router.get("/events")
async def get_events(org_id: str = Depends(require_organization_access)):
    events = await db.events.find({"organization_id": org_id}).to_list(100)
    return {"events": events}

# ❌ Bad - returns data from all organizations
@router.get("/events")
async def get_events():
    events = await db.events.find({}).to_list(100)
    return {"events": events}
```

### 2. Validate Organization Access in Mutations

```python
# ✅ Good
@router.patch("/events/{event_id}")
async def update_event(
    event_id: str,
    update_data: EventUpdate,
    org_id: str = Depends(require_organization_access)
):
    # Verify event belongs to organization
    event = await db.events.find_one({
        "id": event_id,
        "organization_id": org_id
    })
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    # Update event
    ...

# ❌ Bad - could update events from other organizations
@router.patch("/events/{event_id}")
async def update_event(event_id: str, update_data: EventUpdate):
    await db.events.update_one({"id": event_id}, {"$set": update_data.dict()})
```

### 3. Use OrganizationScoped for Complex Operations

```python
@router.post("/events/{event_id}/publish")
async def publish_event(
    event_id: str,
    scope: OrganizationScoped = Depends()
):
    # Require admin
    await scope.require_admin()

    # Verify event belongs to organization
    event = await db.events.find_one({
        "id": event_id,
        "organization_id": scope.org_id
    })

    # Publish event
    ...
```

### 4. Index Organization Fields

```python
# Create index on organization_id for all collections
await db.events.create_index("organization_id")
await db.tasks.create_index("organization_id")
await db.users.create_index("organization_id")
```

---

## Troubleshooting

### Common Issues

**Issue:** "Organization service not initialized"
**Solution:** Call `get_organization_service(database)` in your app startup

**Issue:** "Access denied to organization"
**Solution:** Verify user is a member of the organization and X-Organization-ID header is set

**Issue:** "Duplicate key error on name"
**Solution:** Organization names must be unique. Use slugified names.

**Issue:** Frontend not including X-Organization-ID
**Solution:** Add axios interceptor or check localStorage has current_organization_id

---

## Summary

The centralized organization system provides:

✅ Complete multi-tenancy for all KasaAI apps
✅ Role-based access control (admin/user/universal_admin)
✅ Easy integration with FastAPI middleware and dependencies
✅ Type-safe models and async support
✅ Data isolation between organizations

**Next Steps:**
1. Integrate into your app following Quick Start
2. Migrate existing data using migration script
3. Add organization management routes
4. Update frontend to include X-Organization-ID header
5. Write tests for organization-scoped operations
