# Email Account Management Service Architecture

**Version:** 1.0.0
**Last Updated:** November 3, 2025
**Status:** Production
**Author:** KasaAI Development Team

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Components](#components)
- [Data Flow](#data-flow)
- [Security](#security)
- [API Endpoints](#api-endpoints)
- [Integration Points](#integration-points)
- [Deployment](#deployment)
- [Monitoring & Maintenance](#monitoring--maintenance)
- [Future Enhancements](#future-enhancements)

---

## Overview

The Email Account Management Service provides automated email account provisioning, management, and lifecycle control on the organization's iRedMail server. This service enables applications to programmatically create, suspend, restore, and manage email accounts without manual intervention.

### Purpose

- **Automated Onboarding:** Create email accounts automatically when employees join
- **Lifecycle Management:** Disable/enable accounts during employment lifecycle events
- **System Integration:** Connect HR systems, ERPs, and custom applications
- **Self-Service:** Enable users to request and manage email accounts
- **Compliance:** Maintain audit trails of all email account operations

### Key Features

✅ **Automatic Email Generation** - Creates firstname.lastname@ailabsafrica.com format
✅ **Duplicate Handling** - Intelligent suffix addition for duplicate names
✅ **Secure Password Generation** - Cryptographically secure temporary passwords
✅ **Account Suspension** - Disable accounts without data loss
✅ **Account Restoration** - Re-enable suspended accounts
✅ **Quota Management** - Customizable mailbox sizes (1 MB - 10 GB)
✅ **Audit Logging** - Complete operation history
✅ **Multi-Application** - Shared service across all applications

---

## Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Email Account Management Service                 │
└─────────────────────────────────────────────────────────────────────┘

┌──────────────┐        ┌──────────────┐        ┌──────────────┐
│  ERP Backend │        │  Developer   │        │   Custom     │
│  (HR Module) │        │   Platform   │        │  Applications│
└───────┬──────┘        └───────┬──────┘        └───────┬──────┘
        │                       │                        │
        │     HTTPS (API Calls) │                        │
        └───────────┬───────────┴────────────────────────┘
                    │
                    ▼
        ┌───────────────────────────┐
        │  Email Account Service    │
        │  (@shared/services/)      │
        │  - create_account()       │
        │  - disable_account()      │
        │  - enable_account()       │
        │  - check_exists()         │
        │  - generate_email()       │
        └────────────┬──────────────┘
                     │
                     │ HTTPS REST API
                     ▼
        ┌───────────────────────────┐
        │  iRedMail REST API        │
        │  (85.214.12.174:8100)     │
        │  iredmail-api.ailabsafrica│
        │  - FastAPI Application    │
        │  - API Key Auth           │
        │  - IP Whitelisting        │
        └────────────┬──────────────┘
                     │
                     │ CLI Wrapper
                     ▼
        ┌───────────────────────────┐
        │  iRedMail CLI Tools       │
        │  (Bash Scripts)           │
        │  - create_user.sh         │
        │  - delete_user.sh         │
        │  - ldapsearch             │
        └────────────┬──────────────┘
                     │
                     │ LDAP/System
                     ▼
        ┌───────────────────────────┐
        │  Mail Server              │
        │  mail.ailabsafrica.com    │
        │  (85.214.12.174)          │
        │  - iRedMail               │
        │  - OpenLDAP               │
        │  - Postfix                │
        │  - Dovecot                │
        └───────────────────────────┘
```

### Component Layers

| Layer | Component | Technology | Location | Purpose |
|-------|-----------|------------|----------|---------|
| **Application** | ERP HR Module | FastAPI | apps/erp/backend | Employee email automation |
| **Application** | Developer Platform | FastAPI | apps/developer_platform | External API access |
| **Service** | EmailAccountService | Python/Async | apps/shared/services | Shared email operations |
| **API Gateway** | iRedMail REST API | FastAPI | mail server | REST wrapper for CLI |
| **CLI Layer** | iRedMail Tools | Bash | mail server | User management scripts |
| **Infrastructure** | iRedMail Server | Linux/LDAP | mail server | Email server infrastructure |

---

## Components

### 1. Email Account Service (`email_account_service.py`)

**Location:** `/opt/kasaai/apps/shared/services/email_account_service.py`

**Purpose:** Shared Python service that provides async methods for email account management across all applications.

**Key Methods:**

```python
class EmailAccountService:
    async def create_account(first_name, last_name, email=None, quota_mb=512) -> Dict
    async def disable_account(email) -> Dict
    async def enable_account(email) -> Dict
    async def check_exists(email) -> bool
    async def generate_email(first_name, last_name) -> str
```

**Features:**
- Async/await for non-blocking operations
- Automatic retry with exponential backoff (max 3 attempts)
- Comprehensive error handling
- Timeout protection (30 seconds)
- Singleton pattern for service instance
- Environment-based configuration

**Configuration (from .env):**

```ini
IREDMAIL_API_URL=https://iredmail-api.ailabsafrica.com
IREDMAIL_API_KEY=wMwdpcPTKjX4V0iw915PiXOeKmIF_loND3jkL6PVERk
IREDMAIL_DEFAULT_QUOTA_MB=512
```

### 2. iRedMail REST API

**Location:** `85.214.12.174:/opt/iredmail-api/`

**Purpose:** FastAPI application that exposes REST endpoints for email account management, wrapping iRedMail CLI tools.

**Components:**

```
/opt/iredmail-api/
├── main.py              # FastAPI application & endpoints
├── config.py            # Configuration management
├── auth.py              # API key authentication & IP whitelisting
├── iredmail_cli.py      # CLI wrapper for iRedMail commands
├── .env                 # Environment variables
├── requirements.txt     # Python dependencies
└── venv/                # Python virtual environment
```

**Endpoints:**

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/accounts` | Create email account |
| PATCH | `/api/accounts/{email}/disable` | Disable account |
| PATCH | `/api/accounts/{email}/enable` | Enable account |
| GET | `/api/accounts/{email}` | Check if account exists |
| POST | `/api/accounts/generate-email` | Preview email generation |
| GET | `/health` | Health check |

**Security:**
- API Key authentication via X-API-Key header
- IP whitelisting (148.251.0.46, 127.0.0.1)
- HTTPS only (SSL via Let's Encrypt)
- Input validation via Pydantic models

**Systemd Service:**

```ini
# /etc/systemd/system/iredmail-api.service
[Unit]
Description=iRedMail REST API Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/iredmail-api
Environment="PATH=/opt/iredmail-api/venv/bin"
ExecStart=/opt/iredmail-api/venv/bin/python /opt/iredmail-api/main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

### 3. iRedMail CLI Wrapper

**Location:** `85.214.12.174:/opt/iredmail-api/iredmail_cli.py`

**Purpose:** Python wrapper around iRedMail bash CLI tools for programmatic access.

**Key Methods:**

```python
class IRedMailCLI:
    def generate_email(first_name, last_name) -> str
    def account_exists(email) -> bool
    def create_account(email, password, quota_mb) -> Dict
    def disable_account(email) -> Dict
```

**Email Generation Logic:**

```python
# Format: firstname.lastname@ailabsafrica.com
# If exists: firstname.lastname2@ailabsafrica.com
# If exists: firstname.lastname3@ailabsafrica.com
# ... up to firstname.lastname100@ailabsafrica.com
```

### 4. Nginx Reverse Proxy

**Location:** `85.214.12.174:/etc/nginx/sites-available/iredmail-api.ailabsafrica.com.conf`

**Purpose:** Reverse proxy with SSL termination for iRedMail API.

**Configuration:**

```nginx
# HTTP -> HTTPS redirect
server {
    listen 80;
    server_name iredmail-api.ailabsafrica.com;
    return 301 https://$host$request_uri;
}

# HTTPS endpoint
server {
    listen 443 ssl http2;
    server_name iredmail-api.ailabsafrica.com;

    ssl_certificate /etc/letsencrypt/live/iredmail-api.ailabsafrica.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/iredmail-api.ailabsafrica.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8100;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**SSL Certificate:**
- Provider: Let's Encrypt
- Auto-renewal: certbot
- Expires: February 1, 2026

---

## Data Flow

### Create Email Account Flow

```
┌──────────────────────────────────────────────────────────────────┐
│                     Create Email Account Flow                     │
└──────────────────────────────────────────────────────────────────┘

1. Application Request
   ├─ ERP HR Module (Employee Creation)
   ├─ Developer Platform (API Call)
   └─ Custom Application
            │
            ▼
2. Email Account Service
   ├─ Validate input (first_name, last_name, quota)
   ├─ Generate email if not provided
   ├─ Make HTTPS request to iRedMail API
   ├─ Retry logic (3 attempts, exponential backoff)
   └─ Handle errors (timeout, network, server)
            │
            ▼
3. iRedMail REST API
   ├─ Verify API key
   ├─ Check IP whitelist
   ├─ Validate request body
   ├─ Call IRedMailCLI wrapper
   └─ Return JSON response
            │
            ▼
4. iRedMail CLI Wrapper
   ├─ Check if email exists (ldapsearch)
   ├─ Generate unique email if duplicate
   ├─ Generate secure password
   ├─ Execute create_user.sh script
   └─ Return result
            │
            ▼
5. iRedMail Server
   ├─ Create LDAP user entry
   ├─ Set up mailbox (Postfix/Dovecot)
   ├─ Apply quota limits
   └─ Enable email delivery
            │
            ▼
6. Response to Application
   ├─ Success: {email, password, status, created_at}
   ├─ Error: {error_code, message, details}
   └─ Audit: Log to email_account_operations collection
```

### Disable Account Flow

```
1. Application Request (Employee Termination)
            │
            ▼
2. Email Account Service
   └─ POST /api/accounts/{email}/disable
            │
            ▼
3. iRedMail REST API
   └─ Execute disable CLI command
            │
            ▼
4. iRedMail Server
   ├─ Disable LDAP user (accountStatus=disabled)
   ├─ Block IMAP/SMTP access
   └─ Preserve all emails and folders
            │
            ▼
5. Application
   ├─ Update employee record (email_account_status=disabled)
   └─ Log operation (email_account_operations collection)
```

---

## Security

### Authentication & Authorization

**API Key Authentication:**
```python
# All requests require API key in header
X-API-Key: wMwdpcPTKjX4V0iw915PiXOeKmIF_loND3jkL6PVERk
```

**IP Whitelisting:**
```python
ALLOWED_IPS = ["148.251.0.46", "127.0.0.1"]
# 148.251.0.46 = Production ERP/Apps server
# 127.0.0.1 = Local testing
```

### Password Security

**Generation:**
```python
import secrets
import string

def generate_secure_password(length=16):
    """Generate cryptographically secure random password."""
    chars = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(chars) for _ in range(length))
```

**Best Practices:**
- ✅ Generate 16-character passwords
- ✅ Use secrets module (not random)
- ✅ Include letters, digits, special characters
- ✅ Deliver once via secure channel
- ✅ Clear from database after first delivery
- ❌ Never log passwords
- ❌ Never store in plain text long-term

### SSL/TLS

**Configuration:**
```nginx
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers HIGH:!aNULL:!MD5;
ssl_prefer_server_ciphers on;
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
```

### Network Security

**Firewall Rules:**
```bash
# Only allow HTTPS traffic from specific IPs
iptables -A INPUT -p tcp --dport 8100 -s 148.251.0.46 -j ACCEPT
iptables -A INPUT -p tcp --dport 8100 -s 127.0.0.1 -j ACCEPT
iptables -A INPUT -p tcp --dport 8100 -j DROP
```

### Audit Logging

**MongoDB Collection: `email_account_operations`**

```javascript
{
  _id: ObjectId,
  organization_id: "org_123",
  employee_id: "emp_456",
  employee_number: "EMP001",
  email: "john.doe@ailabsafrica.com",
  operation: "create",  // create|disable|enable|delete
  status: "success",    // success|failed
  error_message: null,  // if failed
  reason: "employee_hired",
  created_at: ISODate("2025-11-03T21:15:00Z"),
  created_by: "user_789"
}
```

---

## API Endpoints

### Developer Platform Integration

**Base URL:** `https://developer.ailabsafrica.com/api/v1/email`

**Endpoints:**

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/accounts` | Required | Create email account |
| POST | `/accounts/disable` | Required | Disable account |
| POST | `/accounts/enable` | Required | Enable account |
| POST | `/accounts/check` | Required | Check if exists |
| POST | `/accounts/generate-email` | Required | Preview email |
| GET | `/config` | Required | Get configuration |

**Rate Limits:**

| Endpoint | Limit | Quota Cost |
|----------|-------|-----------|
| Create Account | 10/minute | 1 credit |
| Disable/Enable | 10/minute | Free |
| Check/Generate | 20/minute | Free |
| Get Config | 100/minute | Free |

---

## Integration Points

### 1. ERP HR Module

**File:** `/opt/kasaai/apps/erp/backend/app/api/routes/hr.py`

**Automatic Email Creation:**

```python
@router.post("/employees")
async def create_employee(employee_create: EmployeeCreate):
    # 1. Create employee record (ALWAYS succeeds)
    employee_id = await db.employees.insert_one(employee_data)

    # 2. Attempt email creation (non-blocking)
    try:
        email_result = await email_service.create_account(
            first_name=employee_data.first_name,
            last_name=employee_data.last_name
        )

        # Update employee with email details
        await db.employees.update_one(
            {"id": employee_id},
            {"$set": {
                "email_account_created": True,
                "email_account_status": "active",
                "email_temporary_password": email_result["password"]
            }}
        )

        # Log operation
        await db.email_account_operations.insert_one({...})

    except Exception as e:
        # Mark as failed but don't block employee creation
        await db.employees.update_one(
            {"id": employee_id},
            {"$set": {"email_account_status": "failed"}}
        )

    return {"employee": employee_data, "email_account": email_result}
```

**Automatic Email Deactivation:**

```python
@router.patch("/employees/{employee_id}")
async def update_employee(employee_id: str, update_data: dict):
    # Detect termination
    if update_data.get("employment_status") == "terminated":
        # Disable email account
        await email_service.disable_account(employee.email)

        # Update status
        await db.employees.update_one(
            {"id": employee_id},
            {"$set": {"email_account_status": "disabled"}}
        )

        # Log operation
        await db.email_account_operations.insert_one({...})
```

### 2. Developer Platform

**File:** `/opt/kasaai/apps/developer_platform/backend/routes/email_routes.py`

**Public API Endpoints:**

Exposes email management functionality to external developers via authenticated API keys.

**Example Integration:**

```python
import requests

# External developer using KasaAI API
url = "https://developer.ailabsafrica.com/api/v1/email/accounts"
headers = {"X-API-Key": "kasa_live_your_api_key"}
data = {"first_name": "John", "last_name": "Doe"}

response = requests.post(url, headers=headers, json=data)
result = response.json()

print(f"Email: {result['data']['email']}")
print(f"Password: {result['data']['password']}")
```

### 3. Custom Applications

Any application can integrate by:

1. Installing shared service: `from shared.services.email_account_service import get_email_account_service`
2. Setting environment variables: `IREDMAIL_API_URL`, `IREDMAIL_API_KEY`
3. Calling service methods: `await email_service.create_account(...)`

---

## Deployment

### Production Server (148.251.0.46)

**Applications Using Email Service:**
- ERP Backend (Port 30034)
- Developer Platform (Port 30028)

**Environment Variables:**

```bash
# /opt/kasaai/.env (Shared)
IREDMAIL_API_URL=https://iredmail-api.ailabsafrica.com
IREDMAIL_API_KEY=wMwdpcPTKjX4V0iw915PiXOeKmIF_loND3jkL6PVERk
IREDMAIL_DEFAULT_QUOTA_MB=512
```

### Mail Server (85.214.12.174)

**iRedMail API Service:**

```bash
# Check status
systemctl status iredmail-api

# View logs
journalctl -u iredmail-api -f

# Restart service
systemctl restart iredmail-api
```

**Nginx Configuration:**

```bash
# Test configuration
nginx -t

# Reload nginx
systemctl reload nginx
```

**SSL Certificate Renewal:**

```bash
# Automatic renewal via certbot
# Cron job: /etc/cron.d/certbot

# Manual renewal
certbot renew
```

### DNS Configuration

```bash
# DNS Record
iredmail-api.ailabsafrica.com A 85.214.12.174

# Verify
nslookup iredmail-api.ailabsafrica.com
dig iredmail-api.ailabsafrica.com +short
```

---

## Monitoring & Maintenance

### Health Checks

**API Health Endpoint:**

```bash
curl https://iredmail-api.ailabsafrica.com/health

# Response
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-11-03T21:15:00.123456"
}
```

**Monitoring Script:**

```bash
#!/bin/bash
# /opt/monitoring/check_iredmail_api.sh

HEALTH_URL="https://iredmail-api.ailabsafrica.com/health"
ALERT_EMAIL="admin@ailabsafrica.com"

response=$(curl -s -o /dev/null -w "%{http_code}" "$HEALTH_URL")

if [ "$response" != "200" ]; then
    echo "iRedMail API health check failed: HTTP $response" | \
        mail -s "Alert: iRedMail API Down" "$ALERT_EMAIL"
fi
```

### Log Management

**Application Logs:**

```bash
# iRedMail API logs
journalctl -u iredmail-api -f

# Nginx access logs
tail -f /var/log/nginx/access.log | grep iredmail-api

# Nginx error logs
tail -f /var/log/nginx/error.log
```

**Log Rotation:**

```bash
# /etc/logrotate.d/iredmail-api
/var/log/iredmail-api/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    missingok
    create 0640 root root
}
```

### Database Maintenance

**Email Operations Collection:**

```javascript
// Check operation statistics
db.email_account_operations.aggregate([
  {
    $group: {
      _id: "$operation",
      count: { $sum: 1 },
      success: {
        $sum: { $cond: [{ $eq: ["$status", "success"] }, 1, 0] }
      },
      failed: {
        $sum: { $cond: [{ $eq: ["$status", "failed"] }, 1, 0] }
      }
    }
  }
])

// Clean old temporary passwords (run monthly)
db.employees.updateMany(
  {
    email_temporary_password: { $ne: null },
    email_account_created_at: { $lt: new Date(Date.now() - 30*24*60*60*1000) }
  },
  { $set: { email_temporary_password: null } }
)
```

### Backup

**MongoDB Backup:**

```bash
# Backup email operations
mongodump --db erp --collection email_account_operations --out /backup/

# Backup entire ERP database
mongodump --db erp --out /backup/erp_$(date +%Y%m%d)/
```

**Configuration Backup:**

```bash
# Backup iRedMail API config
tar -czf /backup/iredmail-api-config.tar.gz /opt/iredmail-api/
```

---

## Future Enhancements

### Phase 2: Frontend Integration

- [ ] Password display modal on employee creation
- [ ] Email status indicators (🟢 Active, 🔴 Disabled, ⚠️ Failed)
- [ ] Manual retry button for failed email creations
- [ ] Email account management panel in employee details

### Phase 3: Advanced Features

- [ ] Email forwarding setup (forward to manager on termination)
- [ ] Email alias management (multiple aliases per account)
- [ ] Custom email quota per employee/department
- [ ] Bulk email account creation for existing employees
- [ ] Email usage statistics and reporting
- [ ] Auto-archive emails before account deletion
- [ ] Email templates for welcome messages
- [ ] Integration with Active Directory / LDAP sync

### Phase 4: Integration Improvements

- [ ] Webhook notifications for email events
- [ ] Real-time sync with iRedMail
- [ ] Two-way sync (detect manual changes in iRedMail)
- [ ] Integration with onboarding/offboarding workflows
- [ ] Microsoft 365 / Google Workspace sync
- [ ] Email signature management
- [ ] Distribution list management
- [ ] Shared mailbox creation

### Phase 5: Compliance & Security

- [ ] Email retention policies
- [ ] GDPR compliance features (data export, deletion)
- [ ] Email encryption at rest
- [ ] Two-factor authentication for email access
- [ ] Email archival service integration
- [ ] Legal hold capabilities
- [ ] Audit report generation
- [ ] Compliance dashboard

---

## References

### Documentation

- [ERP Employee Email Automation](/opt/kasaai/apps/erp/EMPLOYEE_EMAIL_AUTOMATION.md)
- [Shared Services README](/opt/kasaai/apps/shared/services/README.md)
- [Developer Platform API Documentation](/opt/kasaai/apps/developer_platform/API_DOCUMENTATION.md)
- [iRedMail Setup Guide](/opt/kasaai/apps/erp/IREDMAIL_SETUP.md)

### API Endpoints

- **Production API:** https://iredmail-api.ailabsafrica.com
- **Developer API:** https://developer.ailabsafrica.com/api/v1/email
- **Webmail:** https://mail.ailabsafrica.com
- **iRedAdmin:** https://mail.ailabsafrica.com/iredadmin

### Support

- **Technical Issues:** Create issue in project repository
- **Security Concerns:** Email admin@ailabsafrica.com
- **Feature Requests:** Add to project roadmap

---

**Last Updated:** November 3, 2025
**Version:** 1.0.0
**Status:** Production Ready ✅
