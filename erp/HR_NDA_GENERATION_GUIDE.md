# HR NDA Generation Guide

Complete guide for HR to generate and send NDAs to new employees with organization letterhead.

---

## 🎯 Overview

HR can now generate personalized NDAs with company logo and letterhead directly from the employee onboarding interface. The system automatically creates signing links that employees can use to review and sign documents electronically.

---

## 📍 Where to Generate NDAs

### Access the Interface

1. Navigate to **Onboarding** page in the ERP system
2. Click on any employee record to view their details
3. In the **Employee Information** section header, you'll see a **"Generate NDA"** button
4. Click this button to open the NDA generation modal

---

## 📝 Step-by-Step Process

### Step 1: Open Employee Details

- From the Onboarding page, click on an employee row
- The detail view modal opens showing:
  - Employee information
  - Progress percentage
  - Task checklist
  - Status indicators

### Step 2: Generate NDA

1. Click **"Generate NDA"** button (blue button with file icon)
2. Modal opens showing:
   - Employee name, email, position, start date
   - Generate button with organization letterhead mention
3. Click **"Generate NDA with Organization Letterhead"**
4. System creates the NDA (takes 2-3 seconds)

### Step 3: Get Signing Link

Once generated, you'll see:
- ✅ Success message with document ID
- 📅 Expiration date (30 days from now)
- 🔗 **Signing Link** - Unique URL for this employee
- 📧 **Email Template** - Pre-filled message ready to send

### Step 4: Send to Employee

**Option A: Copy Link**
- Click **"Copy Link"** button
- Paste into your own email client
- Send to employee

**Option B: Copy Email Template**
- Expand the **Email Template** section
- Click **"Copy Email Template"**
- Paste entire email into your email client
- Send to employee

**Email Template Includes:**
- Subject line
- Greeting with employee's first name
- Start date mention
- Signing link
- Expiration notice
- HR contact information

### Step 5: Automatic Updates

When employee signs the NDA:
- ✅ Legal document status → "signed"
- ✅ Audit trail created (IP, timestamp, user agent)
- ✅ Employee onboarding record → `nda_signed: true`
- ✅ Onboarding task "Sign NDA electronically" → completed
- ✅ Progress percentage recalculated
- ✅ Onboarding status → "in_progress"

---

## 🏢 Organization Letterhead

### What's Included

Every generated NDA automatically includes:
- **Company Logo** (if configured)
- **Company Name**: AI Labs Africa
- **Address**:
  ```
  HNO DA701, Cloverleaf St.
  Accra, Ghana
  ```
- **Phone**: (if configured)
- **Email**: (if configured)

### Configuring Organization Details

To update company letterhead information:

```bash
cd /opt/kasaai/apps/erp/backend
python -m scripts.update_ai_labs_org
```

This script sets:
- Display name
- Address (structured format)
- Logo URL
- Brand colors
- Invoice settings

---

## 🔒 Security Features

### Signing Links
- ✅ Cryptographically secure tokens (32 bytes)
- ✅ 30-day automatic expiration
- ✅ One-time use (cannot sign twice)
- ✅ No authentication required (public endpoint)
- ✅ Organization data hidden from public view

### Audit Trail
Every signature captures:
- Signer name and email
- Signature image (base64)
- IP address
- Browser/device info (user agent)
- Timestamp (UTC)
- Consent checkboxes
- Verification status

---

## 📊 Monitoring & Status

### Check NDA Status

**In Onboarding Details:**
- Task checklist shows "Sign NDA electronically"
- Status: ✅ Completed or ⏳ Pending
- Completion date (if signed)
- Completed by email (if signed)

**View All Documents:**
```bash
GET /api/v1/legal/documents?employee_id=EMP001
```

**Check Specific Document:**
```bash
GET /api/v1/legal/documents/{document_id}/status
```

### Resend Signing Link

If employee doesn't sign or link expires:
```bash
POST /api/v1/legal/documents/{document_id}/resend
```

This:
- Generates new secure token
- Extends expiry by 30 days
- Increments reminder count
- Returns new signing link

---

## ❓ Common Questions

### Q: Can I customize the NDA template?
**A:** Yes! Edit the template at:
```
/opt/kasaai/apps/shared/legal/NDA_Employee_AILabs_Africa.md
```

The system automatically replaces:
- `[EMPLOYEE NAME]` → Employee's full name (uppercase)
- `[JOB TITLE]` → Position
- `[COMPANY NAME]` → Organization name
- `_________________` → Start date

### Q: What if the employee loses the link?
**A:** Use the resend function:
1. Find document in system
2. Call resend endpoint
3. Send new link to employee

### Q: Can I generate multiple NDAs for the same employee?
**A:** Yes! Each generation creates a unique document. However, typically one NDA per employee is sufficient.

### Q: How do I know when employee signs?
**A:**
1. Check onboarding progress (auto-updated)
2. Task "Sign NDA" will show completed
3. Progress percentage increases
4. (Future) Email notification to HR

### Q: What if link expires?
**A:** Resend the document - generates new 30-day link.

### Q: Is this legally binding?
**A:** Yes! Electronic signatures are legally binding under:
- ✅ ESIGN Act (United States)
- ✅ eIDAS (European Union)
- ✅ UETA (Uniform Electronic Transactions Act)

Complete audit trail provides legal evidence.

---

## 🚀 Quick Reference

| Action | Location |
|--------|----------|
| Generate NDA | Onboarding Page → Employee Details → "Generate NDA" button |
| Copy Link | NDA Modal → "Copy Link" button |
| Copy Email | NDA Modal → Email Template → "Copy Email Template" |
| Check Status | Onboarding Page → Employee Details → Tasks section |
| Resend Link | API: `POST /api/v1/legal/documents/{id}/resend` |
| View Documents | API: `GET /api/v1/legal/documents/employee/{id}` |

---

## 📱 API Endpoints

For automation or integration:

```bash
# Generate NDA
POST /api/v1/legal/generate-nda?employee_name=John+Doe&employee_email=john@example.com&employee_id=EMP001&position=Developer&start_date=2025-11-15

# View document (employee uses this - no auth required)
GET /api/v1/legal/sign/{token}

# Sign document (employee submits signature - no auth required)
POST /api/v1/legal/sign/{token}

# Check status (HR)
GET /api/v1/legal/documents/{document_id}/status

# List employee documents (HR)
GET /api/v1/legal/documents/employee/{employee_id}

# Resend link (HR)
POST /api/v1/legal/documents/{document_id}/resend
```

---

## 🎨 UI Screenshots

### Generate NDA Button
Located in employee detail view header, next to "Employee Information" title.

### NDA Generation Modal
- Employee info display
- Generate button
- Success state with signing link
- Copy buttons
- Email template
- Next steps guide

### Email Template
Pre-filled with:
- Personalized greeting
- Start date mention
- Signing link
- Expiration notice
- HR contact info

---

## 📞 Support

For issues or questions:
- **Technical Issues**: Contact IT Support
- **Process Questions**: Contact HR Manager
- **System Updates**: Check `NDA_SIGNING_WORKFLOW_GUIDE.md`

---

**Last Updated**: 2025-11-07
**Version**: 1.0.0
**System**: KasaAI ERP - HR Module
