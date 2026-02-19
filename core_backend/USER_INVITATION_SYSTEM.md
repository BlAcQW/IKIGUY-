# User Invitation System Documentation

## Overview

The User Invitation System allows administrators to invite new users via email. When invited users accept, they are automatically:
1. Created in the system with their own organization
2. Registered as affiliates with the inviter's referral code (if inviter is an affiliate)
3. Able to build their own affiliate downline

This implements **Option 1: Each Affiliate Gets Their Own Organization** for the MLM structure.

---

## Features

### For Admins
- **Send Invitations**: Invite users by email with customizable role and message
- **Track Invitations**: View all pending, accepted, expired, and cancelled invitations
- **Manage Invitations**: Cancel pending invitations or resend invitation emails
- **Copy Invitation Links**: Share invitation URLs directly

### For Invited Users
- **Secure Signup**: Accept invitation with a unique token
- **Set Own Password**: Users choose their own password (no admin-set passwords)
- **Auto-Affiliate Registration**: Automatically enrolled as affiliate with inviter's referral code
- **Own Organization**: Each user gets their own organization for full autonomy

---

## Architecture

### Backend Components

#### 1. Models (`backend/models/invitation.py`)
- **UserInvitation**: Core invitation model with token, email, role, status, expiry
- **InviteUserRequest**: Request model for creating invitations
- **AcceptInvitationRequest**: Request model for accepting invitations
- **InvitationListResponse**: Response model with invitation statistics

#### 2. Service (`backend/services/invitation_service.py`)
- **InvitationService**: Business logic for invitation management
  - `create_invitation()`: Creates invitation and fetches inviter's referral code
  - `accept_invitation()`: Creates user account and auto-registers as affiliate
  - `cancel_invitation()`: Cancels pending invitations
  - `resend_invitation()`: Resends invitation email
  - `get_invitations()`: Lists invitations with filtering
  - `mark_expired_invitations()`: Periodic cleanup of expired invitations

#### 3. Routes

**Admin Routes (`backend/routes/admin.py`)**
- `POST /api/admin/invitations` - Create invitation
- `GET /api/admin/invitations` - List all invitations
- `DELETE /api/admin/invitations/{id}` - Cancel invitation
- `POST /api/admin/invitations/{id}/resend` - Resend invitation

**Public Routes (`backend/routes/invitations_public.py`)**
- `GET /api/invitations/{token}/details` - Get invitation details (public)
- `POST /api/invitations/{token}/accept` - Accept invitation (public)

### Frontend Components

#### 1. Admin Users Page (`src/pages/admin/Users.tsx`)
- **Two Tabs**: Users & Invitations
- **Invite User Button**: Opens dialog to send invitation
- **Invitations Table**: Shows all invitations with status badges
- **Actions**: Copy link, resend email, cancel invitation

#### 2. Accept Invitation Page (`src/pages/AcceptInvitation.tsx`)
- **Public Page**: Accessible without authentication
- **Invitation Details**: Shows inviter name, role, message
- **Signup Form**: First name, last name, password, confirm password
- **Auto-Login**: Users are automatically logged in after accepting

---

## User Flow

### 1. Admin Invites User

```
Admin → User Management → Invite User Button
│
├─ Enter email address
├─ Select role (user, admin, moderator, universal_admin)
├─ Optional: Add personal message
└─ Click "Send Invitation"
```

**Backend Process:**
1. Check if user already exists
2. Check for pending invitations
3. Fetch inviter's affiliate referral code (if exists)
4. Generate unique invitation token
5. Save invitation to database
6. Send invitation email (TODO: implement actual email service)

### 2. User Receives Email

```
Email contains:
- Personal message from inviter
- Invitation link: https://kasaai.ailabsafrica.com/accept-invitation?token=...
- Expiry date (7 days default)
```

### 3. User Accepts Invitation

```
User → Clicks invitation link → AcceptInvitation page
│
├─ View invitation details
├─ Enter first name, last name
├─ Set password
└─ Click "Accept & Create Account"
```

**Backend Process:**
1. Validate invitation token
2. Check expiry status
3. Create user account in MongoDB
4. Create organization for the user
5. **Auto-register as affiliate** with inviter's referral code
6. Mark invitation as accepted
7. Return authentication tokens
8. Redirect to dashboard

---

## Affiliate Integration

### Automatic Affiliate Registration

When a user accepts an invitation:

```python
# In invitation_service.py accept_invitation()

# 1. Create user account
auth_response = await auth_service.signup(signup_data)
user_id = auth_response.user.id
organization_id = auth_response.user.primary_organization_id

# 2. Auto-register as affiliate with inviter's referral code
if invitation.inviter_referral_code:
    affiliate_profile = await self.affiliate_service.join_program(
        user_id=user_id,
        organization_id=organization_id,
        upline_referral_code=invitation.inviter_referral_code,  # Key: Inviter's code
    )
```

### Result
- **Inviter**: Gets new affiliate in their downline
- **Invited User**:
  - Own organization
  - Own affiliate profile with unique referral code
  - Can invite others and build their own downline
  - Earns commissions (15% tier 1, 8% tier 2, 3% tier 3)

### Example MLM Structure

```
Alfred (Org: "Alfred's AI Services", Ref: ALFRED001)
  └─ Invites → User A
      ├─ Org: "User A's AI Services"
      ├─ Ref: USERA001
      ├─ Upline: ALFRED001 (Alfred gets 15% commission on User A's sales)
      │
      └─ Invites → User B
          ├─ Org: "User B's AI Services"
          ├─ Ref: USERB001
          ├─ Upline: USERA001 (User A gets 15%, Alfred gets 8% on User B's sales)
          │
          └─ Invites → User C
              ├─ Org: "User C's AI Services"
              ├─ Ref: USERC001
              └─ Upline: USERB001 (User B gets 15%, User A gets 8%, Alfred gets 3%)
```

---

## API Endpoints

### Admin Endpoints (Require Admin Auth)

#### Create Invitation
```http
POST /api/admin/invitations
Authorization: Bearer {admin_token}
Content-Type: application/json

{
  "email": "newuser@example.com",
  "role": "user",
  "message": "Welcome to our platform!",
  "send_email": true
}
```

**Response:**
```json
{
  "success": true,
  "message": "Invitation sent to newuser@example.com",
  "invitation": {
    "id": "inv_123",
    "email": "newuser@example.com",
    "token": "abc123def456...",
    "role": "user",
    "status": "pending",
    "expires_at": "2025-11-30T12:00:00Z",
    "invited_by": "Alfred Anyan",
    "referral_code": "ALFRED001"
  }
}
```

#### List Invitations
```http
GET /api/admin/invitations?status=pending&limit=100&skip=0
Authorization: Bearer {admin_token}
```

**Response:**
```json
{
  "success": true,
  "invitations": [
    {
      "id": "inv_123",
      "email": "user@example.com",
      "token": "abc123...",
      "role": "user",
      "status": "pending",
      "invited_by": "Alfred Anyan",
      "referral_code": "ALFRED001",
      "created_at": "2025-11-23T10:00:00Z",
      "expires_at": "2025-11-30T10:00:00Z"
    }
  ],
  "stats": {
    "total": 10,
    "pending": 5,
    "accepted": 3,
    "expired": 1,
    "cancelled": 1
  }
}
```

#### Cancel Invitation
```http
DELETE /api/admin/invitations/{invitation_id}
Authorization: Bearer {admin_token}
```

#### Resend Invitation
```http
POST /api/admin/invitations/{invitation_id}/resend
Authorization: Bearer {admin_token}
```

### Public Endpoints (No Auth Required)

#### Get Invitation Details
```http
GET /api/invitations/{token}/details
```

**Response:**
```json
{
  "success": true,
  "invitation": {
    "email": "newuser@example.com",
    "invited_by": "Alfred Anyan",
    "role": "user",
    "message": "Welcome to our platform!",
    "created_at": "2025-11-23T10:00:00Z",
    "expires_at": "2025-11-30T10:00:00Z",
    "status": "pending",
    "is_expired": false,
    "is_valid": true
  }
}
```

#### Accept Invitation
```http
POST /api/invitations/{token}/accept
Content-Type: application/json

{
  "token": "abc123def456...",
  "first_name": "John",
  "last_name": "Doe",
  "password": "SecureP@ssw0rd123"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Account created successfully",
  "user": {
    "id": "user_789",
    "email": "newuser@example.com",
    "name": "John Doe",
    "role": "user"
  },
  "tokens": {
    "access_token": "eyJhbGc...",
    "refresh_token": "eyJhbGc..."
  }
}
```

---

## Database Schema

### user_invitations Collection

```javascript
{
  "id": "uuid",
  "email": "newuser@example.com",
  "token": "secure_random_token_32_bytes",

  // Inviter info
  "invited_by_user_id": "user_123",
  "invited_by_email": "admin@example.com",
  "invited_by_name": "Alfred Anyan",
  "inviter_referral_code": "ALFRED001",  // For auto-affiliate registration

  // Role and org
  "role": "user",
  "organization_id": null,  // Optional

  // Invitation details
  "message": "Welcome to our platform!",
  "status": "pending",  // pending, accepted, expired, cancelled

  // Timestamps
  "created_at": "2025-11-23T10:00:00Z",
  "expires_at": "2025-11-30T10:00:00Z",  // 7 days default
  "accepted_at": null,
  "cancelled_at": null,

  // Acceptance details
  "accepted_user_id": null,
  "accepted_ip_address": null,
  "accepted_user_agent": null,

  // Metadata
  "metadata": {}
}
```

---

## Configuration

### Invitation Expiry
Default: 7 days

```python
# In models/invitation.py
expires_at: datetime = Field(
    default_factory=lambda: datetime.utcnow() + timedelta(days=7),
    description="Invitation expiry (7 days default)"
)
```

### Invitation Token Security
- 32-byte URL-safe random token
- Generated using `secrets.token_urlsafe(32)`
- Approximately 256 bits of entropy

### Email Service
**Current Status**: Placeholder (logs to console)

**TODO**: Implement actual email service
```python
# In invitation_service.py _send_invitation_email()
# TODO: Replace with actual email service
# await email_service.send(...)
```

---

## Security Considerations

### 1. Token Security
- ✅ Cryptographically secure random tokens
- ✅ 256-bit entropy (32 bytes URL-safe)
- ✅ Single-use tokens (marked as used on acceptance)

### 2. Expiry Management
- ✅ 7-day expiry by default
- ✅ Automatic expiry checking on acceptance
- ⚠️ **TODO**: Add periodic cleanup task to mark expired invitations

### 3. Authorization
- ✅ Admin-only invitation creation
- ✅ Public invitation acceptance (requires valid token)
- ✅ No authentication required for /accept-invitation page

### 4. Password Security
- ✅ Minimum 8 characters enforced
- ✅ Password confirmation required
- ✅ Passwords hashed using bcrypt in auth service

### 5. Email Verification
- ⚠️ **TODO**: Add email verification step
- **Current**: Users can log in immediately after accepting

---

## Testing

### Manual Testing Flow

1. **As Admin - Create Invitation**
   ```
   1. Log in as admin
   2. Go to Admin → Users
   3. Click "Invite User"
   4. Enter email, select role, add message
   5. Click "Send Invitation"
   6. Verify invitation appears in "Invitations" tab
   7. Copy invitation link
   ```

2. **As New User - Accept Invitation**
   ```
   1. Open invitation link in incognito window
   2. Verify invitation details are displayed
   3. Enter first name, last name, password
   4. Click "Accept & Create Account"
   5. Verify automatic login to dashboard
   ```

3. **Verify Affiliate Registration**
   ```
   1. As new user, check if you have a referral code
   2. As admin, check affiliate_profiles collection
   3. Verify upline_id matches inviter's user_id
   4. Verify referral_code is set
   ```

### API Testing with cURL

```bash
# 1. Create invitation (requires admin token)
curl -X POST https://api.ailabsafrica.com/api/admin/invitations \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "role": "user",
    "message": "Join us!",
    "send_email": true
  }'

# 2. Get invitation details (public)
curl https://api.ailabsafrica.com/api/invitations/TOKEN_FROM_STEP_1/details

# 3. Accept invitation (public)
curl -X POST https://api.ailabsafrica.com/api/invitations/TOKEN_FROM_STEP_1/accept \
  -H "Content-Type: application/json" \
  -d '{
    "token": "TOKEN_FROM_STEP_1",
    "first_name": "John",
    "last_name": "Doe",
    "password": "SecurePassword123"
  }'
```

---

## Future Enhancements

### High Priority
1. **Email Service Integration**
   - Replace console logging with actual email delivery
   - Use SendGrid, AWS SES, or similar
   - Email template with branding

2. **Email Verification**
   - Require email verification before full access
   - Send verification code/link after signup

3. **Invitation Analytics**
   - Track invitation conversion rates
   - Monitor acceptance times
   - Identify most successful inviters

### Medium Priority
4. **Customizable Expiry**
   - Allow admins to set custom expiry per invitation
   - Default: 7 days, Range: 1-30 days

5. **Invitation Limits**
   - Rate limiting per user
   - Daily/monthly invitation quotas

6. **Batch Invitations**
   - CSV upload for bulk invitations
   - Progress tracking
   - Error handling for duplicate emails

### Low Priority
7. **Invitation Templates**
   - Pre-defined message templates
   - Dynamic variables (inviter name, company, etc.)

8. **Reminder Emails**
   - Automated reminders for pending invitations
   - Send reminder 3 days before expiry

---

## Troubleshooting

### Issue: Invitation link shows "Invalid Invitation"
- **Cause**: Token expired or invalid
- **Solution**: Resend invitation from admin panel

### Issue: User already exists error
- **Cause**: Email already registered in system
- **Solution**: User should use "Forgot Password" or contact admin

### Issue: Pending invitation already exists
- **Cause**: Previous invitation not accepted or expired
- **Solution**: Cancel old invitation and create new one

### Issue: Affiliate not registered after acceptance
- **Cause**: Inviter doesn't have affiliate profile
- **Solution**: Verify inviter is enrolled in affiliate program

---

## Monitoring

### Key Metrics to Track
1. **Invitation Conversion Rate**: accepted / sent
2. **Average Time to Accept**: accepted_at - created_at
3. **Expiry Rate**: expired / sent
4. **Cancel Rate**: cancelled / sent
5. **Affiliate Enrollment Success**: affiliates created / invitations accepted

### Database Queries

```javascript
// Count pending invitations
db.user_invitations.countDocuments({ status: "pending" })

// Find expired pending invitations
db.user_invitations.find({
  status: "pending",
  expires_at: { $lt: new Date() }
})

// Conversion rate
db.user_invitations.aggregate([
  {
    $group: {
      _id: null,
      total: { $sum: 1 },
      accepted: {
        $sum: { $cond: [{ $eq: ["$status", "accepted"] }, 1, 0] }
      }
    }
  },
  {
    $project: {
      conversion_rate: {
        $multiply: [{ $divide: ["$accepted", "$total"] }, 100]
      }
    }
  }
])
```

---

## Changelog

### Version 1.0.0 (2025-11-23)
- ✅ Initial implementation
- ✅ Admin invitation creation and management
- ✅ Public invitation acceptance page
- ✅ Automatic affiliate registration
- ✅ Each user gets own organization (Option 1)
- ✅ Frontend UI with tabs for users and invitations
- ⚠️ Email service placeholder (console logging)
- ⚠️ No periodic expiry cleanup task yet

---

## Related Documentation
- [Affiliate System](AFFILIATE_IMPLEMENTATION_SUMMARY.md)
- [Organization Management](docs/ORGANIZATION_MANAGEMENT.md)
- [Authentication System](docs/AUTHENTICATION.md)
