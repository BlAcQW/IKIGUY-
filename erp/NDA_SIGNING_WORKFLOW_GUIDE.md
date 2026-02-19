# NDA E-Signature Workflow - Complete Guide

## Overview

This guide shows you how to send NDAs to new hires, get automatic confirmation when signed, and have their profile updated automatically.

---

## 📋 Quick Start

### For HR: Send NDA to New Hire

#### Method 1: Using the ERP Web Interface (Recommended)

**Step 1: Navigate to Onboarding Page**
1. Log in to the ERP system at https://erp.ailabsafrica.com
2. Go to **HR** → **Onboarding**
3. Find the employee you want to send an NDA to

**Step 2: Generate NDA**
1. Click on the employee row to open the details view
2. In the "Employee Information" section, click the **"Generate NDA"** button
3. Review the employee details in the modal
4. Click **"Generate NDA"** to create the signing link

**Step 3: Send Link to Employee**
1. After generation, you'll see the signing link
2. Click **"Copy Link"** to copy the signing URL
3. Send the link to the employee via email or messaging

**Features:**
- ✅ Automatically includes company letterhead (logo and address)
- ✅ Pre-fills employee information from onboarding record
- ✅ Generates secure signing token (expires in 30 days)
- ✅ One-click copy to clipboard
- ✅ Visual confirmation of success

---

#### Method 2: Using the API (Advanced)

**Step 1: Generate NDA with Signing Link**

```bash
curl -X POST "https://erp-api.ailabsafrica.com/api/v1/legal/generate-nda" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "employee_name": "John Doe",
    "employee_email": "john.doe@example.com",
    "employee_id": "EMP001",
    "position": "Software Developer",
    "start_date": "2025-11-15"
  }'
```

**Note:** The NDA now includes organization letterhead with:
- Company logo (AI Labs Africa)
- Address: HNO DA701, Cloverleaf St., Accra, Ghana
- Contact information (phone, email)

**Response:**
```json
{
  "document_id": "doc_abc123",
  "signing_token": "xJ3kL9mN2pQ4rT6vW8yZ",
  "signing_link": "/api/v1/legal/sign/xJ3kL9mN2pQ4rT6vW8yZ",
  "full_signing_url": "https://erp-api.ailabsafrica.com/api/v1/legal/sign/xJ3kL9mN2pQ4rT6vW8yZ",
  "expires_at": "2025-12-15T10:00:00Z",
  "message": "NDA generated successfully. Send signing link to john.doe@example.com"
}
```

**Step 2: Send Link to New Hire**

Email template:
```
Subject: AI Labs Africa - NDA Signature Required

Hi John,

Welcome to AI Labs Africa!

Before your start date on November 15, 2025, please review and electronically sign your Non-Disclosure Agreement (NDA).

Click here to review and sign:
https://erp-api.ailabsafrica.com/api/v1/legal/sign/xJ3kL9mN2pQ4rT6vW8yZ

This link will expire in 30 days.

If you have any questions, please contact HR at hr@ailabsafrica.com

Best regards,
AI Labs Africa HR Team
```

---

## 🔐 For New Hire: Signing the NDA

### Step 1: Click the Link

New hire clicks the signing link and sees the full NDA document.

### Step 2: View Document (Public Endpoint - No Login Required)

```bash
# New hire can view document without authentication
curl -X GET "https://erp-api.ailabsafrica.com/api/v1/legal/sign/xJ3kL9mN2pQ4rT6vW8yZ"
```

**Response:**
```json
{
  "id": "doc_abc123",
  "document_type": "nda",
  "title": "Employee NDA - John Doe",
  "content": "# EMPLOYEE NON-DISCLOSURE AND CONFIDENTIALITY AGREEMENT\n\n**AI Labs Africa**...",
  "employee_name": "John Doe",
  "employee_email": "john.doe@example.com",
  "company_representative": "HR Director",
  "effective_date": "2025-11-15",
  "status": "pending_signature"
}
```

### Step 3: Sign Document

```bash
# New hire submits electronic signature
curl -X POST "https://erp-api.ailabsafrica.com/api/v1/legal/sign/xJ3kL9mN2pQ4rT6vW8yZ" \
  -H "Content-Type: application/json" \
  -d '{
    "signature_data": "data:image/png;base64,iVBORw0KGgoAAAANS...",
    "consent_acknowledged": true,
    "consents": {
      "terms_agreed": true,
      "electronic_signature_consent": true
    }
  }'
```

**What Gets Captured:**
- ✅ Signature image (base64 encoded)
- ✅ IP address (automatic)
- ✅ Browser details (automatic)
- ✅ Timestamp (automatic)
- ✅ Consent acknowledgments

**Response:**
```json
{
  "message": "Document signed successfully",
  "document_id": "doc_abc123",
  "signed_at": "2025-11-07T14:30:00Z",
  "status": "signed"
}
```

---

## ✅ Automatic Profile Update

When the NDA is signed, the system **automatically**:

1. **Updates Legal Document Status:**
   - Changes status from `pending_signature` → `signed`
   - Records signature timestamp
   - Stores IP address and browser info

2. **Creates Audit Trail:**
   - Creates `DocumentSignature` record
   - Stores full signing details
   - Permanent record for compliance

3. **Updates Employee Onboarding Record:**
   ```json
   {
     "nda_document_id": "doc_abc123",
     "nda_signed": true,
     "nda_signed_date": "2025-11-07T14:30:00Z"
   }
   ```

4. **Updates Onboarding Task Checklist:**
   - Finds task with task_id "all_1" (Sign NDA electronically)
   - Marks task status as `completed`
   - Records completion timestamp and signer email
   - Recalculates completed_tasks count and progress_percentage
   - Updates onboarding_status to "in_progress" or "completed"

---

## 📧 Confirmation & Notifications

### HR Receives Automatic Notification

When document is signed, HR automatically sees:

**Check Document Status:**
```bash
curl -X GET "https://erp-api.ailabsafrica.com/api/v1/legal/documents/doc_abc123/status" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "document_id": "doc_abc123",
  "employee_name": "John Doe",
  "employee_email": "john.doe@example.com",
  "document_type": "nda",
  "status": "signed",
  "signed": true,
  "signed_date": "2025-11-07T14:30:00Z",
  "created_at": "2025-11-01T10:00:00Z",
  "expires_at": "2025-12-01T10:00:00Z"
}
```

---

## 🔄 Complete Workflow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     HR Creates Onboarding                       │
│                  POST /api/v1/onboarding                        │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│              HR Generates NDA with Signing Link                 │
│           POST /api/v1/legal/generate-nda                       │
│                                                                  │
│   • Fetches organization details (logo, address, contact)     │
│   • Builds professional letterhead                             │
│   • Reads NDA template from @shared/legal/                     │
│   • Replaces [EMPLOYEE NAME], [JOB TITLE], etc.               │
│   • Generates unique secure token                              │
│   • Creates signing link (30 day expiry)                       │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│               HR Sends Email with Signing Link                  │
│     https://erp-api.ailabsafrica.com/api/v1/legal/sign/TOKEN  │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│         New Hire Clicks Link (No Login Required)               │
│              GET /api/v1/legal/sign/TOKEN                       │
│                                                                  │
│   • Views full NDA document                                     │
│   • Reads all terms and conditions                             │
│   • Sees company and employee details                          │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│         New Hire Signs Document Electronically                  │
│             POST /api/v1/legal/sign/TOKEN                       │
│                                                                  │
│   Captures:                                                     │
│   • Typed or drawn signature                                    │
│   • IP address: 192.168.1.100                                  │
│   • Browser: Mozilla/5.0...                                     │
│   • Timestamp: 2025-11-07T14:30:00Z                           │
│   • Consent checkboxes                                          │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                 Automatic System Actions                         │
│                                                                  │
│   1. Update Legal Document:                                     │
│      status: pending_signature → signed                         │
│      signature_data: [base64]                                   │
│      signature_timestamp: [now]                                 │
│                                                                  │
│   2. Create Audit Trail Record:                                 │
│      DocumentSignature with all details                         │
│                                                                  │
│   3. Update Employee Onboarding:                                │
│      nda_signed: true                                           │
│      nda_signed_date: [now]                                     │
│      nda_document_id: [doc_id]                                  │
│                                                                  │
│   4. Update Onboarding Task:                                    │
│      "Sign NDA" → completed                                     │
│      Progress: 1/16 (6.25%)                                     │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│            HR Gets Automatic Confirmation                        │
│                                                                  │
│   • Dashboard shows "NDA: Signed ✅"                           │
│   • Email notification (optional)                               │
│   • View full audit trail                                       │
│   • Download signed PDF (future)                                │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📊 Viewing Signed Documents

### Get All Documents for Employee

```bash
curl -X GET "https://erp-api.ailabsafrica.com/api/v1/legal/documents/employee/EMP001" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
[
  {
    "id": "doc_abc123",
    "document_type": "nda",
    "title": "Employee NDA - John Doe",
    "employee_id": "EMP001",
    "employee_name": "John Doe",
    "status": "signed",
    "signed_date": "2025-11-07T14:30:00Z",
    "signature_ip_address": "192.168.1.100",
    "signature_timestamp": "2025-11-07T14:30:00Z",
    "created_at": "2025-11-01T10:00:00Z"
  },
  {
    "id": "doc_xyz789",
    "document_type": "employment_contract",
    "status": "pending_signature",
    ...
  }
]
```

### List All Pending Documents

```bash
curl -X GET "https://erp-api.ailabsafrica.com/api/v1/legal/documents?status=pending_signature" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 🔁 Resending Signing Links

If employee doesn't sign, HR can resend:

```bash
curl -X POST "https://erp-api.ailabsafrica.com/api/v1/legal/documents/doc_abc123/resend" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "message": "Signing link resent successfully",
  "signing_link": "/api/v1/legal/sign/NEW_TOKEN_HERE",
  "full_signing_url": "https://erp-api.ailabsafrica.com/api/v1/legal/sign/NEW_TOKEN_HERE",
  "expires_at": "2025-12-07T14:30:00Z"
}
```

**What Happens:**
- Generates new secure token
- Extends expiry by 30 days
- Increments reminder count
- Ready to send new email

---

## 🔒 Security Features

### Electronic Signature Audit Trail

Every signature captures:
```json
{
  "signer_name": "John Doe",
  "signer_email": "john.doe@example.com",
  "signature_data": "data:image/png;base64...",
  "signed_at": "2025-11-07T14:30:00Z",
  "ip_address": "192.168.1.100",
  "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)...",
  "consent_text": "I have read and agree to the terms",
  "consent_checkboxes": {
    "terms_agreed": true,
    "electronic_signature_consent": true
  },
  "verified": true
}
```

### Link Security
- ✅ Cryptographically secure tokens (32 bytes)
- ✅ 30-day expiration
- ✅ One-time use (signed = link invalid)
- ✅ No authentication required (public endpoint)
- ✅ Organization data hidden from public view

### Compliance
- ✅ ESIGN Act compliant (US)
- ✅ eIDAS compliant (EU)
- ✅ Complete audit trail
- ✅ IP address logging
- ✅ Timestamp verification
- ✅ Consent tracking

---

## 🎯 Integration with Onboarding

### Automatic Task Completion

When NDA is signed, onboarding task automatically updates:

**Before:**
```json
{
  "task_id": "all_1",
  "title": "Sign NDA electronically",
  "status": "pending",
  "order": 1
}
```

**After:**
```json
{
  "task_id": "all_1",
  "title": "Sign NDA electronically",
  "status": "completed",
  "completed_date": "2025-11-07T14:30:00Z",
  "completed_by": "john.doe@example.com",
  "order": 1
}
```

### Progress Tracking

```json
{
  "total_tasks": 16,
  "completed_tasks": 1,
  "progress_percentage": 6.25,
  "onboarding_status": "in_progress",
  "nda_signed": true,
  "nda_document_id": "doc_abc123"
}
```

---

## 📱 Frontend Integration (Coming Soon)

### HR Interface
- Button: "Generate & Send NDA"
- Document status badges
- Signature timestamp display
- Resend link button
- View audit trail modal

### Employee Self-Service
- Canvas signature pad
- Typed signature option
- Document review checklist
- Consent checkboxes
- Confirmation page

---

## 🚀 API Endpoints Reference

| Method | Endpoint | Auth Required | Description |
|--------|----------|---------------|-------------|
| POST | `/api/v1/legal/generate-nda` | ✅ Yes (HR) | Generate NDA with signing link |
| GET | `/api/v1/legal/sign/{token}` | ❌ No (Public) | View document to sign |
| POST | `/api/v1/legal/sign/{token}` | ❌ No (Public) | Submit signature |
| GET | `/api/v1/legal/documents` | ✅ Yes (HR) | List all documents |
| GET | `/api/v1/legal/documents/{id}` | ✅ Yes (HR) | Get document details |
| GET | `/api/v1/legal/documents/{id}/status` | ✅ Yes (HR) | Check signing status |
| POST | `/api/v1/legal/documents/{id}/resend` | ✅ Yes (HR) | Resend signing link |
| GET | `/api/v1/legal/documents/employee/{id}` | ✅ Yes (HR) | Get employee's documents |

---

## 📝 Example: Complete Onboarding Flow

```bash
# 1. HR creates onboarding record
curl -X POST ".../onboarding" -d '{
  "employee_id": "EMP001",
  "first_name": "John",
  "last_name": "Doe",
  "email": "john@example.com",
  "department": "Development",
  "position": "Software Developer",
  "start_date": "2025-11-15"
}'

# 2. HR generates NDA
curl -X POST ".../legal/generate-nda" -d '{
  "employee_name": "John Doe",
  "employee_email": "john@example.com",
  "employee_id": "EMP001",
  "position": "Software Developer",
  "start_date": "2025-11-15"
}'

# 3. HR sends email with signing link to john@example.com

# 4. John clicks link and views NDA (no login)
# Opens: https://erp-api.ailabsafrica.com/api/v1/legal/sign/TOKEN

# 5. John signs NDA electronically

# 6. System automatically:
#    - Updates document status → signed
#    - Creates audit trail
#    - Updates onboarding record
#    - Marks task as completed

# 7. HR checks status
curl -X GET ".../legal/documents/doc_abc123/status"
# Response: "signed": true ✅
```

---

## ⚙️ Configuration & Setup

### Organization Letterhead

All generated NDAs automatically include your organization's letterhead with:
- Company logo
- Company name
- Full address
- Phone and email contact information

**Current Configuration (AI Labs Africa):**
```
AI Labs Africa

[Company Logo]

HNO DA701, Cloverleaf St.
Accra, Greater Accra Region
Ghana
Phone: +233 (0) XXX XXX XXX
Email: info@ailabsafrica.com
```

### Updating Organization Settings

To update the organization letterhead information, use the provided script:

```bash
cd /opt/kasaai/apps/erp/backend
source /opt/kasaai/apps/venv/bin/activate
python -m scripts.update_ai_labs_org
```

The script updates:
- Display name and organization name
- Logo URL (points to /shared/branding/ailabsafrica_logo.png)
- Address (both legacy and structured billing address)
- Contact information (phone, email)
- Invoice settings (prefix, payment terms, etc.)

**Editing the Script:**

Open `/opt/kasaai/apps/erp/backend/scripts/update_ai_labs_org.py` and modify:

```python
org_update = {
    "display_name": "Your Company Name",
    "address": "Your Address Here",
    "billing_address": {
        "street": "Street Address",
        "city": "City",
        "state": "State/Region",
        "country": "Country"
    },
    "phone": "+XXX XXX XXX",
    "email": "info@yourcompany.com",
    "logo_url": "/shared/branding/your_logo.png"
}
```

**Uploading a New Logo:**

1. Copy your logo to the shared branding directory:
   ```bash
   cp your_logo.png /opt/kasaai/apps/shared/branding/
   ```

2. Update the `logo_url` in the script to match your filename

3. Run the update script

4. Restart the ERP backend:
   ```bash
   sudo systemctl restart kasaai-erp-backend
   ```

The logo will be accessible at: `https://erp-api.ailabsafrica.com/shared/branding/your_logo.png`

---

## ✨ Benefits

1. **Legally Binding**: ESIGN/eIDAS compliant electronic signatures
2. **Audit Trail**: Complete forensic record of who, when, where, how
3. **No Manual Work**: Automatic profile updates
4. **Secure**: Cryptographic tokens, IP logging, consent tracking
5. **Simple**: One link, no login required for signing
6. **Tracked**: HR always knows signing status
7. **Reminder System**: Easy to resend if not signed

---

**Ready to use!** 🎉

All API endpoints are live and ready. The NDA template is read from `/opt/kasaai/apps/shared/legal/NDA_Employee_AILabs_Africa.md` and automatically personalized for each employee.

---

**Last Updated**: 2025-11-07
**Version**: 1.0.0
