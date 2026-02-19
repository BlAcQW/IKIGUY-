# KasaAI Documentation

**Official documentation for the KasaAI platform with user management and role-based access control.**

🌐 **Live Site**: https://docs.ailabsafrica.com

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Getting Started](#getting-started)
- [Authentication System](#authentication-system)
- [User Roles](#user-roles)
- [API Reference](#api-reference)
- [Admin Guide](#admin-guide)
- [Development](#development)
- [Deployment](#deployment)
- [Documentation Structure](#documentation-structure)

---

## Overview

This is the official KasaAI documentation site built with **Docusaurus** and **FastAPI**. It provides:

- **Public Documentation**: API reference, guides, tutorials, and use cases
- **Internal Documentation**: Protected documentation for AI Labs employees
- **User Management**: Signup, authentication, and role-based access control
- **Admin Dashboard API**: Manage users and document visibility

---

## Features

### 🔐 Authentication & Authorization
- **Supabase Authentication**: Secure JWT-based authentication
- **Role-Based Access Control**: 3 user roles (admin, internal, public)
- **User Signup**: Anyone can create an account
- **Universal Admin Support**: Pre-configured admin accounts
- **Welcome Emails**: Automated email notifications on signup

### 📚 Documentation
- **Public Docs**: Getting Started, Guides, API Reference, Use Cases
- **Internal Docs**: Developer onboarding, architecture, deployment, maintenance
- **Document Visibility Control**: Set any document as public or internal
- **Search & Navigation**: Full Docusaurus features

### 👥 User Management
- **User CRUD Operations**: Create, read, update, delete users
- **Role Assignment**: Promote users to internal or admin roles
- **User Activation**: Enable/disable user accounts
- **MongoDB Integration**: Custom user metadata and roles
- **Email Notifications**: Welcome emails and account updates

### 📄 Document Management
- **Visibility Control**: Public or internal per document
- **Metadata Management**: Title, description, access level
- **Path-Based Protection**: Automatic protection for `/internal/*` routes

---

## Architecture

### Tech Stack

**Frontend**:
- Docusaurus 3.x (Static Site Generator)
- React 18
- TypeScript
- MDX for documentation

**Backend**:
- FastAPI (Python)
- Uvicorn (ASGI Server)
- Motor (Async MongoDB driver)
- Supabase Python Client
- Unified Email Service (SMTP/Postfix)

**Authentication**:
- Supabase (JWT tokens, user accounts)
- MongoDB (Custom roles, metadata)

**Database**:
- MongoDB: User roles, document metadata
- Supabase PostgreSQL: User authentication

**Infrastructure**:
- Nginx: Reverse proxy, SSL termination
- systemd: Service management
- Let's Encrypt: SSL certificates

### Components

```
docs/
├── backend/                    # FastAPI server
│   ├── main.py                # Main application & routes
│   ├── docs_models.py         # Pydantic models
│   ├── docs_database.py       # MongoDB operations
│   └── requirements.txt       # Python dependencies
├── build/                     # Docusaurus static output
├── docs/                      # Documentation content
│   ├── getting-started/       # Public docs
│   ├── guides/                # Public docs
│   ├── api-reference/         # Public docs
│   ├── use-cases/             # Public docs
│   └── internal/              # Protected docs (auth required)
│       ├── introduction.md
│       ├── onboarding.md      # Full developer onboarding
│       ├── architecture.md
│       ├── deployment.md
│       └── maintenance.md
├── src/                       # Docusaurus theme customization
├── static/                    # Static assets
├── docusaurus.config.ts       # Docusaurus configuration
├── sidebars.ts               # Sidebar structure
└── package.json              # Node dependencies
```

---

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Python 3.10+
- MongoDB
- Supabase account

### Installation

1. **Install Node Dependencies**:
   ```bash
   cd /opt/kasaai/apps/docs
   npm install
   ```

2. **Install Python Dependencies**:
   ```bash
   source /opt/kasaai/apps/venv/bin/activate
   cd backend
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables**:

   Required in `/opt/kasaai/.env`:
   ```bash
   # Supabase Authentication
   SUPABASE_URL=https://supabase.ailabsafrica.com
   SUPABASE_ANON_KEY=<your-anon-key>
   SUPABASE_SERVICE_ROLE_KEY=<your-service-key>

   # MongoDB
   MONGO_USER=admin
   MONGO_PASSWORD=<your-password>
   MONGO_HOST=127.0.0.1
   MONGO_PORT=27017

   # Universal Admins
   UNIVERSAL_ADMIN_EMAILS=admin@ailabsafrica.com,alfred.anyan@gmail.com
   UNIVERSAL_ADMIN_USER_IDS=4a6252e7-3dc7-483a-92c3-59a0a814a169,65715ad2-bcfa-42aa-ab21-e0b06f19b3e4
   ```

4. **Build Documentation**:
   ```bash
   npm run build
   ```

5. **Run Development Server**:
   ```bash
   # Frontend only (Docusaurus)
   npm start

   # Backend (FastAPI)
   cd backend
   python main.py
   ```

---

## Authentication System

### How It Works

We use a **hybrid authentication system**:

1. **Supabase**: Handles user accounts, passwords, JWT tokens
2. **MongoDB**: Stores custom roles and user metadata
3. **JWT Tokens**: Bearer tokens for API authentication

### Authentication Flow

```
User Signup/Login
    ↓
Supabase creates account & issues JWT
    ↓
User record created in MongoDB (role: "public")
    ↓
User makes request with token
    ↓
Backend verifies token with Supabase
    ↓
Backend checks MongoDB for user role
    ↓
Access granted based on role
```

### Default Admin Accounts

These users automatically get `admin` role:

| Email | Password | Purpose |
|-------|----------|---------|
| admin@ailabsafrica.com | Admin@2024! | Primary admin |
| alfred.anyan@gmail.com | AlfredSecure2024! | Universal admin |
| user@ailabsafrica.com | User@2024! | Test admin |

**Note**: These same accounts work across all KasaAI applications (Core Backend, Developer Platform, etc.)

---

## User Roles

| Role | Access Level | Can Access |
|------|-------------|------------|
| **admin** | Full access | • All public docs<br>• All internal docs<br>• User management<br>• Document visibility control |
| **internal** | Internal employee | • All public docs<br>• All internal docs |
| **public** | Default for new users | • Public docs only |

---

## API Reference

### Base URL

```
https://docs.ailabsafrica.com/api
```

### Authentication Endpoints

#### Signup
```bash
POST /api/auth/signup
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "full_name": "John Doe"
}
```

**Response**:
```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "full_name": "John Doe",
    "role": "public"
  }
}
```

**Email Notification**:
- A welcome email is automatically sent to the user's email address
- Email contains account details and access information
- Signup succeeds even if email delivery fails (non-blocking)

#### Login
```bash
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

#### Verify Authentication
```bash
GET /api/auth/verify
Authorization: Bearer <token>
```

**Response**:
```json
{
  "authenticated": true,
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "role": "internal"
  },
  "is_admin": false,
  "has_internal_access": true
}
```

### User Management Endpoints (Admin Only)

#### List All Users
```bash
GET /api/admin/users?skip=0&limit=100
Authorization: Bearer <admin-token>
```

#### Get User by ID
```bash
GET /api/admin/users/{user_id}
Authorization: Bearer <admin-token>
```

#### Update User
```bash
PUT /api/admin/users/{user_id}
Authorization: Bearer <admin-token>
Content-Type: application/json

{
  "role": "internal",           // "admin" | "internal" | "public"
  "full_name": "John Doe",
  "is_active": true
}
```

#### Delete User
```bash
DELETE /api/admin/users/{user_id}
Authorization: Bearer <admin-token>
```

### Document Management Endpoints (Admin Only)

#### List All Documents
```bash
GET /api/admin/documents?skip=0&limit=100
Authorization: Bearer <admin-token>
```

#### Create Document Metadata
```bash
POST /api/admin/documents
Authorization: Bearer <admin-token>
Content-Type: application/json

{
  "path": "guides/internal-guide",
  "visibility": "internal",      // "public" | "internal"
  "title": "Internal Guide",
  "description": "For employees only"
}
```

#### Update Document Visibility
```bash
PUT /api/admin/documents/{path}
Authorization: Bearer <admin-token>
Content-Type: application/json

{
  "visibility": "internal",
  "title": "Updated Title",
  "description": "Updated description"
}
```

#### Delete Document Metadata
```bash
DELETE /api/admin/documents/{path}
Authorization: Bearer <admin-token>
```

### Health Check
```bash
GET /api/health
```

**Response**:
```json
{
  "status": "healthy",
  "service": "KasaAI Documentation",
  "version": "2.0.0",
  "features": [
    "user_management",
    "role_based_access",
    "document_visibility"
  ]
}
```

---

## Admin Guide

### Common Tasks

#### 1. Give User Access to Internal Docs

```bash
# Login as admin
TOKEN=$(curl -s -X POST https://docs.ailabsafrica.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@ailabsafrica.com","password":"Admin@2024!"}' \
  | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

# List users to find user ID
curl -H "Authorization: Bearer $TOKEN" \
  https://docs.ailabsafrica.com/api/admin/users

# Update user role to "internal"
curl -X PUT https://docs.ailabsafrica.com/api/admin/users/USER_ID \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"role":"internal"}'
```

#### 2. Make User an Admin

```bash
curl -X PUT https://docs.ailabsafrica.com/api/admin/users/USER_ID \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"role":"admin"}'
```

#### 3. Deactivate User Account

```bash
curl -X PUT https://docs.ailabsafrica.com/api/admin/users/USER_ID \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"is_active":false}'
```

#### 4. Set Document to Internal Only

```bash
curl -X POST https://docs.ailabsafrica.com/api/admin/documents \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "path": "guides/sensitive-guide",
    "visibility": "internal",
    "title": "Sensitive Guide",
    "description": "For internal use only"
  }'
```

#### 5. Direct MongoDB Access

```bash
# Connect to MongoDB
mongosh "mongodb://admin:PASSWORD@127.0.0.1:27017/"

# Switch to docs database
use kasaai_docs

# List all users
db.users.find().pretty()

# Update user role
db.users.updateOne(
  { email: "user@example.com" },
  { $set: { role: "internal" } }
)

# List document metadata
db.document_metadata.find().pretty()

# Update document visibility
db.document_metadata.updateOne(
  { path: "guides/advanced" },
  { $set: { visibility: "internal" } }
)
```

---

## Development

### Local Development

1. **Start Docusaurus Dev Server**:
   ```bash
   npm start
   ```
   Opens browser at http://localhost:3000

2. **Start Backend Server**:
   ```bash
   cd backend
   python main.py
   ```
   Backend runs at http://localhost:30035

3. **Make Changes**:
   - Edit markdown files in `docs/`
   - Changes auto-reload in browser
   - Edit backend in `backend/main.py`

### Adding New Documentation

1. **Create Markdown File**:
   ```bash
   # For public docs
   touch docs/guides/new-guide.md

   # For internal docs
   touch docs/internal/new-internal-guide.md
   ```

2. **Add to Sidebar**:
   Edit `sidebars.ts`:
   ```typescript
   guidesSidebar: [
     // ...
     'guides/new-guide',
   ]
   ```

3. **Set Visibility** (if needed):
   ```bash
   curl -X POST https://docs.ailabsafrica.com/api/admin/documents \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "path": "guides/new-guide",
       "visibility": "internal"
     }'
   ```

### Testing

```bash
# Build documentation
npm run build

# Test build locally
npm run serve

# Test backend endpoints
curl http://localhost:30035/api/health
```

---

## Email Configuration

The documentation system uses the shared email service for sending automated notifications.

### SMTP Configuration

Email settings are configured in `/opt/kasaai/.env`:

```bash
# SMTP Configuration
SMTP_SERVER=localhost
SMTP_PORT=25
SMTP_USERNAME=
SMTP_PASSWORD=
SMTP_USE_TLS=false
SENDER_EMAIL=noreply@ailabsafrica.com
SENDER_NAME=KasaAI Platform
SMTP_FROM_EMAIL=noreply@ailabsafrica.com
```

### Email Features

**Welcome Emails**:
- Sent automatically on user signup
- Contains account information and access level
- Beautifully formatted HTML emails with fallback text
- Non-blocking (signup succeeds even if email fails)

**Email Service**:
- Uses `@shared/services/unified_email_service.py`
- Supports SMTP, Resend, and SendGrid
- Automatic fallback mechanisms
- Comprehensive logging

### Testing Emails

```bash
cd /opt/kasaai/apps/docs/backend
/opt/kasaai/apps/venv/bin/python test_email.py
```

---

## Deployment

### Production Deployment

The documentation is deployed at **https://docs.ailabsafrica.com**

#### Service Configuration

**systemd Service**: `/etc/systemd/system/kasaai-docs-backend.service`

```ini
[Unit]
Description=KasaAI Documentation Backend
After=network.target

[Service]
Type=simple
User=dev
Group=dev
WorkingDirectory=/opt/kasaai/apps/docs/backend
Environment="PATH=/opt/kasaai/apps/venv/bin"
EnvironmentFile=/opt/kasaai/.env
ExecStart=/opt/kasaai/apps/venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 30035
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Nginx Configuration**: `/etc/nginx/sites-available/docs.ailabsafrica.com.conf`

```nginx
server {
    listen 443 ssl;
    server_name docs.ailabsafrica.com;

    ssl_certificate /etc/letsencrypt/live/docs.ailabsafrica.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/docs.ailabsafrica.com/privkey.pem;

    # API routes
    location /api/ {
        proxy_pass http://localhost:30035;
        # ... proxy headers
    }

    # Internal docs (requires auth)
    location /internal/ {
        proxy_pass http://localhost:30035;
    }

    # All other routes (static files)
    location / {
        proxy_pass http://localhost:30035;
    }
}
```

#### Deployment Steps

1. **Pull Latest Changes**:
   ```bash
   cd /opt/kasaai/apps/docs
   git pull origin main
   ```

2. **Install Dependencies** (if package.json changed):
   ```bash
   npm install
   ```

3. **Rebuild Documentation**:
   ```bash
   npm run build
   ```

4. **Restart Backend Service**:
   ```bash
   sudo systemctl restart kasaai-docs-backend
   ```

5. **Check Status**:
   ```bash
   sudo systemctl status kasaai-docs-backend
   ```

6. **View Logs**:
   ```bash
   sudo journalctl -u kasaai-docs-backend -f
   ```

#### SSL Certificate Renewal

Certificates auto-renew via certbot. To manually renew:

```bash
sudo certbot renew
sudo systemctl reload nginx
```

#### Service Management Commands

```bash
# Start service
sudo systemctl start kasaai-docs-backend

# Stop service
sudo systemctl stop kasaai-docs-backend

# Restart service
sudo systemctl restart kasaai-docs-backend

# Check status
sudo systemctl status kasaai-docs-backend

# View logs
sudo journalctl -u kasaai-docs-backend -f

# Enable auto-start on boot
sudo systemctl enable kasaai-docs-backend
```

---

## Documentation Structure

### Public Documentation

Located in `docs/`:

```
docs/
├── getting-started/
│   ├── introduction.md
│   ├── quickstart.md
│   ├── authentication.md
│   ├── first-api-call.md
│   └── core-concepts.md
├── guides/
│   ├── voice-assistants/
│   ├── phone-calls/
│   ├── workflows/
│   └── best-practices/
├── api-reference/
│   ├── overview.md
│   ├── assistants/
│   ├── calls/
│   ├── workflows/
│   ├── executions/
│   └── usage/
└── use-cases/
    ├── customer-support-bot.md
    ├── appointment-reminders.md
    ├── lead-qualification.md
    └── ...
```

### Internal Documentation

Located in `docs/internal/` (requires authentication):

```
docs/internal/
├── introduction.md          # Internal docs overview
├── onboarding.md           # Full developer onboarding guide
├── architecture.md         # System architecture details
├── deployment.md           # Deployment procedures
└── maintenance.md          # Operational procedures
```

**Access Control**:
- All files under `docs/internal/` require `internal` or `admin` role
- Other docs can be set to internal via document metadata API

---

## Database Schema

### Users Collection (`kasaai_docs.users`)

```javascript
{
  _id: ObjectId,
  supabase_id: "uuid-from-supabase",  // Primary key (indexed)
  email: "user@example.com",          // Unique (indexed)
  full_name: "John Doe",
  role: "public",                     // "admin" | "internal" | "public"
  is_active: true,
  created_at: ISODate,
  updated_at: ISODate
}
```

### Document Metadata Collection (`kasaai_docs.document_metadata`)

```javascript
{
  _id: ObjectId,
  path: "guides/advanced",            // Document path (unique, indexed)
  visibility: "internal",             // "public" | "internal"
  title: "Advanced Guide",
  description: "Advanced features guide",
  created_at: ISODate,
  updated_at: ISODate
}
```

---

## Troubleshooting

### Common Issues

#### 1. Backend Won't Start

```bash
# Check logs
sudo journalctl -u kasaai-docs-backend -n 50

# Common causes:
# - MongoDB not running
# - Port 30035 already in use
# - Missing environment variables
```

#### 2. 401 Unauthorized

**Cause**: Invalid or expired token

**Solution**: Login again to get fresh token

#### 3. 403 Forbidden (Internal Docs)

**Cause**: User doesn't have `internal` or `admin` role

**Solution**: Admin must update user role:
```bash
curl -X PUT https://docs.ailabsafrica.com/api/admin/users/USER_ID \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{"role":"internal"}'
```

#### 4. Documentation Not Building

```bash
# Clear cache and rebuild
npm run clear
npm run build
```

#### 5. MongoDB Connection Error

**Check credentials in `.env`**:
```bash
MONGO_USER=admin
MONGO_PASSWORD=<correct-password>
```

---

## Resources

### Documentation
- **Live Site**: https://docs.ailabsafrica.com
- **API Base**: https://docs.ailabsafrica.com/api
- **Internal Docs**: https://docs.ailabsafrica.com/internal/introduction

### Related Services
- **Core API**: https://api.ailabsafrica.com
- **Developer Console**: https://developer.ailabsafrica.com
- **Supabase**: https://supabase.ailabsafrica.com

### Tools
- **Docusaurus**: https://docusaurus.io/
- **FastAPI**: https://fastapi.tiangolo.com/
- **Supabase**: https://supabase.com/docs
- **MongoDB**: https://www.mongodb.com/docs/

---

## Support

### For Developers

- **Email**: alfred.anyan@gmail.com
- **GitHub Issues**: https://github.com/alfredanyan/kasaai-v2/issues

### For Users

- Check the documentation first
- Contact your administrator for access issues
- Use signup if you need a new account

---

## License

Copyright © 2025 AI Labs Africa. All rights reserved.

---

**Version**: 2.0.0
**Last Updated**: November 7, 2025
**Service Status**: ✅ Active
