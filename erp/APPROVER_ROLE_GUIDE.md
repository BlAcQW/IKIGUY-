# Expense Approver Role System

**Date**: 2025-11-11
**Status**: ✅ Implemented and Active

## Overview

The ERP system now includes a dedicated **APPROVER** role for managing financial expense approvals. This role enables organizations to implement proper approval workflows, ensuring that all expenses are reviewed before being processed.

## Features

### 1. Role-Based Access Control

The system now supports three role types in addition to ADMIN and USER:

- **UNIVERSAL_ADMIN**: Can access and manage all organizations
- **ADMIN**: Can manage organization and all its data, including approving expenses
- **APPROVER**: **NEW** - Can approve financial expenses and budgets
- **USER**: Can access organization data based on permissions

### 2. Approval Workflow

#### For Regular Users:
1. Create an expense with receipt and details
2. Click "Send for Approval" button
3. Expense status changes to PENDING
4. Wait for approver to review

#### For Approvers:
1. View list of pending expenses
2. Review expense details and receipts
3. Either:
   - **Approve**: Sets status to APPROVED with timestamp
   - **Reject**: Sets status to REJECTED with reason

### 3. Security Rules

- ✅ Users **cannot** approve their own expenses
- ✅ Only APPROVER or ADMIN roles can approve/reject expenses
- ✅ Ownership is tracked via `created_by` field
- ✅ All approval actions are logged with user ID and timestamp

---

## API Endpoints

### Get User Permissions
```http
GET /api/finance/user/permissions
```

**Response:**
```json
{
  "user_id": "...",
  "email": "user@example.com",
  "organization_id": "...",
  "is_admin": false,
  "is_approver": true,
  "can_approve": true
}
```

### Send Expense for Approval
```http
POST /api/finance/expenses/{expense_id}/send-for-approval
```

**Response:** Updated expense object with `status: "pending"`

### Approve Expense
```http
POST /api/finance/expenses/{expense_id}/approve
```

**Requirements:**
- User must have APPROVER or ADMIN role
- User cannot be the creator of the expense

**Response:** Updated expense with:
- `status: "approved"`
- `approved_by: "user_id"`
- `approved_date: "2025-11-11"`

### Reject Expense
```http
POST /api/finance/expenses/{expense_id}/reject?rejection_reason=...
```

**Requirements:**
- User must have APPROVER or ADMIN role
- User cannot be the creator of the expense
- Rejection reason is required

**Response:** Updated expense with:
- `status: "rejected"`
- `rejection_reason: "User provided reason"`
- `approved_by: "user_id"` (tracks who rejected)

---

## Frontend Implementation

### UI Components

The Finance page now shows context-aware buttons based on:
1. **User's role** (can_approve permission)
2. **Expense ownership** (created_by field)
3. **Expense status** (pending, approved, rejected)

### Button Logic

| User Type | Expense Owner | Status | Buttons Shown |
|-----------|---------------|--------|---------------|
| Regular User | Yes | New | "Send for Approval" |
| Regular User | Yes | Pending | None (waiting) |
| Regular User | No | Any | None |
| Approver | No | Pending | "Approve", "Reject" |
| Approver | Yes | Pending | None (own expense) |
| Admin | No | Pending | "Approve", "Reject" |

### User Experience

**Creating an Expense:**
```
1. User fills out expense form
2. Uploads receipt (optional)
3. Submits expense
4. Clicks "Send for Approval"
5. Status changes to PENDING
6. User sees "Pending" badge (yellow)
```

**Approving an Expense:**
```
1. Approver logs in
2. Views Finance > Expenses tab
3. Sees pending expenses with action buttons
4. Reviews expense details
5. Clicks "Approve" or "Reject"
6. Confirmation dialog appears
7. Status updates immediately
8. Badge color changes (green/red)
```

---

## Database Schema

### Updated Expense Model

```python
class Expense(BaseModel):
    # ... existing fields ...

    # Approval fields
    status: ExpenseStatus  # pending, approved, rejected, reimbursed
    approved_by: Optional[str]  # User ID who approved/rejected
    approved_date: Optional[date]  # When it was approved
    rejection_reason: Optional[str]  # Reason if rejected

    # Tracking fields (from BaseModel)
    created_by: Optional[str]  # User ID who created
    created_at: datetime
    updated_by: Optional[str]
    updated_at: datetime
```

---

## Setup Instructions

### 1. Add Approver to Organization

Run the setup script to add alfred.anyan@gmail.com as approver:

```bash
cd /opt/kasaai/apps/erp
MONGODB_URL="mongodb://admin:password@127.0.0.1:27017/erp?authSource=admin" \
/opt/kasaai/apps/venv/bin/python setup_approver.py
```

### 2. Assign Approver Role to Users

Via API or database:

```python
# Add user to organization with APPROVER role
await org_service.add_user_to_organization(
    organization_id=org_id,
    user_id=user_id,
    email="approver@company.com",
    role=OrganizationRole.APPROVER
)
```

Or update existing user:

```python
# Update user role to APPROVER
await db.organization_users.update_one(
    {"organization_id": org_id, "user_id": user_id},
    {"$set": {"role": "approver"}}
)
```

---

## Testing

### Manual Testing Checklist

- [ ] Create expense as regular user
- [ ] Verify "Send for Approval" button appears
- [ ] Click "Send for Approval" and verify status changes
- [ ] Log in as approver
- [ ] Verify approve/reject buttons appear for other users' expenses
- [ ] Verify buttons do NOT appear for own expenses
- [ ] Approve an expense and verify status changes
- [ ] Reject an expense with reason
- [ ] Verify regular user cannot see approve/reject buttons
- [ ] Test user permissions endpoint

### Automated Tests

Run the test suite:

```bash
cd /opt/kasaai/apps/erp/backend
MONGODB_URL="..." /opt/kasaai/apps/venv/bin/python -m pytest tests/test_expense_approval.py -v
```

---

## Current Approver

**Default Approver**: alfred.anyan@gmail.com
**Role**: APPROVER
**Organizations**: All organizations in ERP system

This user has been automatically added to all organizations with the APPROVER role.

---

## Future Enhancements

### Planned Features:
- [ ] Email notifications to approvers when expense is submitted
- [ ] Email notifications to users when expense is approved/rejected
- [ ] Approval hierarchy (multiple approval levels)
- [ ] Approval limits (e.g., amounts over $500 need manager approval)
- [ ] Approval delegation (approver can delegate to another user)
- [ ] Bulk approve/reject functionality
- [ ] Approval dashboard with pending count
- [ ] Approval history and audit trail UI

### Potential Integrations:
- [ ] Slack notifications for pending approvals
- [ ] SMS notifications for urgent approvals
- [ ] Mobile app push notifications
- [ ] Integration with accounting software (QuickBooks, Xero)

---

## Troubleshooting

### Issue: Approve button not showing

**Check:**
1. User has APPROVER or ADMIN role
2. Expense status is PENDING
3. User is not the creator of the expense
4. Frontend has fetched user permissions correctly

**Solution:**
```bash
# Check user role in database
mongosh "mongodb://admin:password@127.0.0.1:27017/erp?authSource=admin"
> db.organization_users.findOne({email: "user@example.com"})
```

### Issue: "You cannot approve your own expense" error

**Reason:** This is by design. Users cannot approve expenses they created.

**Solution:** Have another user with APPROVER role approve the expense.

### Issue: Approver not receiving notifications

**Status:** Notifications are not yet implemented. This is a future enhancement.

**Workaround:** Approvers should check the Finance > Expenses page regularly for pending expenses.

---

## Code References

### Backend Files:
- `/opt/kasaai/apps/shared/models/organization.py:31` - APPROVER role definition
- `/opt/kasaai/apps/shared/dependencies/auth.py:255-317` - Approval permission checks
- `/opt/kasaai/apps/erp/backend/app/api/routes/finance.py:603-829` - Approval endpoints
- `/opt/kasaai/apps/erp/setup_approver.py` - Setup script

### Frontend Files:
- `/opt/kasaai/apps/erp/frontend/src/pages/FinancePage.tsx:151-158` - Permissions fetching
- `/opt/kasaai/apps/erp/frontend/src/pages/FinancePage.tsx:199-245` - Approval handlers
- `/opt/kasaai/apps/erp/frontend/src/pages/FinancePage.tsx:582-634` - Approval buttons UI

---

## Support

For issues or questions:
1. Check this documentation first
2. Review the troubleshooting section
3. Check the TASKS.md file for known issues
4. Contact the development team

**Last Updated**: 2025-11-11
**Version**: 1.0
