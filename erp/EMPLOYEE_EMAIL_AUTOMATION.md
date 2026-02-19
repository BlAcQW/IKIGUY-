# Employee Email Account Automation

## Overview
Automatically creates and manages email accounts on iRedMail when employees are created or terminated in the ERP system.

**Last Updated**: November 3, 2025
**Status**: Backend Complete, Frontend Pending

---

## Architecture

```
ERP Backend (148.251.0.46:30034)
    ↓ HTTP
Email Account Service (/apps/shared/services/)
    ↓ HTTPS/HTTP
iRedMail REST API (85.214.12.174:8100)
    ↓ CLI
iRedMail Server (mail.ailabsafrica.com)
```

---

## Features

### ✅ Implemented
1. **Automatic Email Creation**: When an employee is created, their email account is automatically created on iRedMail
2. **Email Format**: Auto-generates `firstname.lastname@ailabsafrica.com` with duplicate handling
3. **Temporary Password**: Generates secure random password (16 characters)
4. **Email Deactivation**: Automatically disables email when employee is:
   - Terminated (employment_status changed to "terminated")
   - Soft-deleted (is_active set to False)
5. **Error Handling**: Employee creation succeeds even if email creation fails
6. **Operation Logging**: All email operations logged to `email_account_operations` collection
7. **Status Tracking**: Employee records track email account status

### 🔄 Pending
1. Frontend UI updates (password display modal, status indicators)
2. DNS record creation for iredmail-api.ailabsafrica.com
3. Integration tests
4. Manual email account retry button

---

## Component Details

### 1. iRedMail REST API Service

**Location**: `85.214.12.174:/opt/iredmail-api/`
**Service**: `iredmail-api.service`
**Port**: 8100 (internal)
**Status**: ✅ Running

#### Files
- `main.py` - FastAPI application
- `config.py` - Configuration management
- `auth.py` - API key authentication
- `iredmail_cli.py` - CLI wrapper for iRedMail commands
- `.env` - Environment configuration
- `requirements.txt` - Python dependencies

#### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/accounts` | Create email account |
| PATCH | `/api/accounts/{email}/disable` | Disable account |
| PATCH | `/api/accounts/{email}/enable` | Enable account |
| GET | `/api/accounts/{email}` | Check if account exists |
| DELETE | `/api/accounts/{email}` | Delete account (permanent) |
| POST | `/api/accounts/generate-email` | Preview email generation |

#### Authentication
- Header: `X-API-Key: wMwdpcPTKjX4V0iw915PiXOeKmIF_loND3jkL6PVERk`
- IP Whitelist: 148.251.0.46, 127.0.0.1

#### Example Request
```bash
curl -X POST http://85.214.12.174:8100/api/accounts \
  -H "X-API-Key: wMwdpcPTKjX4V0iw915PiXOeKmIF_loND3jkL6PVERk" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "John",
    "last_name": "Doe",
    "quota_mb": 512
  }'
```

#### Example Response
```json
{
  "success": true,
  "email": "john.doe@ailabsafrica.com",
  "status": "created",
  "password": "rA9#mK2$pQ8@vL4!",
  "message": "Email account created successfully",
  "timestamp": "2025-11-03T20:58:00.123456"
}
```

### 2. Email Account Service

**Location**: `/opt/kasaai/apps/shared/services/email_account_service.py`

Shared service that communicates with iRedMail API.

#### Key Methods
```python
async def create_account(first_name, last_name, email=None, password=None) -> Dict
async def disable_account(email) -> Dict
async def enable_account(email) -> Dict
async def check_exists(email) -> bool
async def generate_email(first_name, last_name) -> str
```

#### Features
- Auto-retry with exponential backoff (max 3 attempts)
- Comprehensive error handling
- Timeout protection (30 seconds)
- Singleton pattern

#### Configuration (from .env)
```ini
IREDMAIL_API_URL=http://85.214.12.174:8100
IREDMAIL_API_KEY=wMwdpcPTKjX4V0iw915PiXOeKmIF_loND3jkL6PVERk
IREDMAIL_DEFAULT_QUOTA_MB=512
```

### 3. Employee Model Updates

**Location**: `/opt/kasaai/apps/erp/backend/app/models/hr.py`

#### New Fields
```python
email_account_created: bool = False
email_account_created_at: Optional[datetime] = None
email_account_status: str = "pending"  # pending|active|disabled|failed
email_temporary_password: Optional[str] = None  # Cleared after first use
```

### 4. Employee API Routes

**Location**: `/opt/kasaai/apps/erp/backend/app/api/routes/hr.py`

#### POST /employees
Creates employee and email account.

**Request** (unchanged):
```json
{
  "first_name": "John",
  "last_name": "Doe",
  "email": "john.doe@ailabsafrica.com",
  "department": "Engineering",
  "position": "Software Engineer",
  "hire_date": "2025-11-03",
  "salary": 75000
}
```

**Response** (enhanced):
```json
{
  "employee": {
    "id": "uuid",
    "employee_id": "EMP001",
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@ailabsafrica.com",
    "email_account_created": true,
    "email_account_status": "active",
    "email_account_created_at": "2025-11-03T20:58:00.123456",
    ...
  },
  "email_account": {
    "email_created": true,
    "temporary_password": "rA9#mK2$pQ8@vL4!",
    "email_error": null
  }
}
```

**Error Handling**:
- Employee record is ALWAYS created (primary data preserved)
- If email creation fails, `email_account_status` = "failed"
- Error details returned in `email_account.email_error`
- User can retry via manual button (future feature)

#### PATCH /employees/{id}
Updates employee. Detects termination and disables email.

**Request**:
```json
{
  "employment_status": "terminated",
  "termination_date": "2025-11-03"
}
```

**Response**:
```json
{
  "employee": {...},
  "email_action": {
    "email_disabled": true,
    "email_error": null
  }
}
```

#### DELETE /employees/{id}
Soft deletes employee and disables email account.

---

## Database Schema

### employees Collection

Updated fields:
```javascript
{
  // ... existing fields ...
  email_account_created: false,
  email_account_created_at: ISODate("2025-11-03T20:58:00.000Z"),
  email_account_status: "active", // or "pending", "disabled", "failed"
  email_temporary_password: "rA9#mK2$pQ8@vL4!"
}
```

### email_account_operations Collection (NEW)

Tracks all email account operations:
```javascript
{
  _id: ObjectId,
  organization_id: String,
  employee_id: String,
  employee_number: String, // e.g., "EMP001"
  email: String,
  operation: String, // "create", "disable", "enable", "delete"
  status: String, // "success", "failed"
  error_message: String, // if failed
  reason: String, // "employee_terminated", "employee_deleted", etc.
  created_at: ISODate,
  created_by: String // user ID
}
```

---

## Workflow Examples

### Employee Onboarding
1. HR creates employee record via POST /employees
2. Backend:
   - Saves employee to MongoDB
   - Calls EmailAccountService.create_account()
   - Service calls iRedMail API
   - API executes CLI command to create account
   - Password is generated and returned
3. Frontend (future):
   - Shows success modal with email and temporary password
   - User copies password for employee
   - Password is cleared from database after first use

### Employee Termination
1. HR updates employee status to "terminated"
2. Backend detects status change
3. Calls EmailAccountService.disable_account()
4. Email account is disabled (emails preserved)
5. Employee cannot access email
6. Frontend shows "Email Disabled" status

### Email Duplicate Handling
If "John Doe" already exists:
1. First: `john.doe@ailabsafrica.com`
2. Second: `john.doe2@ailabsafrica.com`
3. Third: `john.doe3@ailabsafrica.com`
...and so on.

---

## Security

### API Key Protection
- Stored in `.env` files (not in git)
- Different keys for prod/dev recommended
- 32-byte URL-safe tokens

### IP Whitelisting
- iRedMail API only accepts requests from:
  - ERP server (148.251.0.46)
  - Localhost (127.0.0.1)

### Password Security
- Generated using `secrets` module (cryptographically secure)
- 16 characters: letters, digits, special chars
- Stored temporarily in employee record
- Should be cleared after first delivery to employee

### Audit Trail
- All operations logged with:
  - Who performed the action
  - What action was taken
  - When it occurred
  - Success/failure status
  - Error details if failed

---

## Troubleshooting

### Email Creation Fails

**Check iRedMail API service**:
```bash
ssh root@85.214.12.174
systemctl status iredmail-api
journalctl -u iredmail-api -f
```

**Check logs**:
```bash
tail -f /var/log/iredmail-api/api.log
tail -f /var/log/iredmail-api/error.log
```

**Test API directly**:
```bash
curl http://localhost:8100/health
```

### Email Already Exists Error

Employee creation succeeds but email fails with "already exists":
1. Check if email account was created manually
2. Use different email or delete existing account
3. Retry via UI button (future feature)

### Connection Timeout

ERP cannot reach iRedMail API:
1. Check API is running: `systemctl status iredmail-api`
2. Check network connectivity: `ping 85.214.12.174`
3. Check firewall rules
4. Verify API_URL in .env is correct

### Deactivation Doesn't Work

Email not disabled when employee terminated:
1. Check employee had `email_account_created=true`
2. Check email_account_operations collection for errors
3. Manually disable via iRedAdmin if needed

---

## Future Enhancements

### Phase 2: Frontend Integration
1. Password display modal on employee creation
2. Email status indicators (🟢 Active, 🔴 Disabled, ⚠️ Failed)
3. Manual retry button for failed email creations
4. Email account management panel in employee details

### Phase 3: Advanced Features
1. Email forwarding setup (forward to manager on termination)
2. Email alias management
3. Custom email quota per employee
4. Bulk email account creation for existing employees
5. Email usage statistics
6. Auto-archive emails before account deletion

### Phase 4: Integration Improvements
1. Webhook notifications for email events
2. Real-time sync with iRedMail
3. Two-way sync (detect manual changes in iRedMail)
4. Integration with onboarding/offboarding workflows

---

## Testing

### Manual Test: Create Employee
```bash
curl -X POST https://dev-erp-api.ailabsafrica.com/api/v1/hr/employees \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "X-Organization-ID: YOUR_ORG_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Test",
    "last_name": "Employee",
    "email": "test.employee@ailabsafrica.com",
    "department": "IT",
    "position": "Developer",
    "hire_date": "2025-11-03",
    "salary": 50000
  }'
```

Expected response should include `email_account.temporary_password`.

### Manual Test: Terminate Employee
```bash
curl -X PATCH https://dev-erp-api.ailabsafrica.com/api/v1/hr/employees/{ID} \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "X-Organization-ID: YOUR_ORG_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "employment_status": "terminated"
  }'
```

Check `email_account_operations` collection for disable operation.

### Verify Email Account
Login to webmail: https://mail.ailabsafrica.com
Use generated credentials to verify account works.

---

## Maintenance

### Backup Email Operations Log
```bash
mongodump --db erp --collection email_account_operations --out /backup/
```

### Clear Old Temporary Passwords
Run periodically to clear passwords from employee records:
```javascript
db.employees.updateMany(
  { email_temporary_password: { $ne: null } },
  { $set: { email_temporary_password: null } }
)
```

### Monitor API Health
Add to monitoring system:
```bash
curl http://85.214.12.174:8100/health
```

---

## Support & Documentation

- **iRedMail Setup**: `/opt/kasaai/apps/erp/IREDMAIL_SETUP.md`
- **ERP HR Module**: `/opt/kasaai/apps/erp/backend/app/api/routes/hr.py`
- **Email Service**: `/opt/kasaai/apps/shared/services/email_account_service.py`
- **iRedMail API**: `http://85.214.12.174:8100/docs`

---

## Notes

- Email accounts use default quota: 512 MB
- Email domain: ailabsafrica.com
- Disabled accounts preserve all emails (not deleted)
- Manual intervention via iRedAdmin always possible
- System designed to be resilient (employee data never lost)
