# Email Server Setup - Complete Summary

## ✅ What Was Configured

The KasaAI email server has been successfully configured to send email notifications from the Call Management system to `ailabsafrica@gmail.com`.

### Architecture Overview

```
┌──────────────────────┐
│  Call Management     │  Python app sends to localhost:25
│  (call_management.py)│
└──────────┬───────────┘
           │ SMTP (no auth)
           ▼
┌──────────────────────┐
│  Postfix MTA         │  Local mail server
│  (localhost:25)      │
└──────────┬───────────┘
           │ SMTP + SASL auth
           │ (requires Gmail app password)
           ▼
┌──────────────────────┐
│  Gmail SMTP Relay    │  smtp.gmail.com:587
│  (smtp.gmail.com)    │
└──────────┬───────────┘
           │ Delivers
           ▼
┌──────────────────────┐
│  ailabsafrica        │  Recipient inbox
│  @gmail.com          │
└──────────────────────┘
```

## 📋 Configuration Details

### 1. Postfix Configuration (`/etc/postfix/main.cf`)

```ini
relayhost = [smtp.gmail.com]:587
smtp_sasl_auth_enable = yes
smtp_sasl_security_options = noanonymous
smtp_sasl_password_maps = hash:/etc/postfix/sasl_passwd
smtp_tls_security_level = encrypt
smtp_tls_CAfile = /etc/ssl/certs/ca-certificates.crt
```

### 2. SASL Password File (`/etc/postfix/sasl_passwd`)

```
[smtp.gmail.com]:587 ailabsafrica@gmail.com:APP_PASSWORD_PLACEHOLDER
```

**⚠️ IMPORTANT**: You must replace `APP_PASSWORD_PLACEHOLDER` with an actual Gmail app password.

### 3. Environment Variables (`/opt/kasaai/.env`)

```ini
SMTP_SERVER=localhost
SMTP_PORT=25
SMTP_USERNAME=noreply@ailabsafrica.com
SMTP_PASSWORD=noreply_secure_2025
SENDER_EMAIL=noreply@ailabsafrica.com
RESEND_API=re_3CKHxpwj_Jk9DmyqvF8nBDQbNWa2Lz6oB
```

### 4. Call Management Integration

Updated `/opt/kasaai/apps/core_backend/backend/routes/call_management.py` to:
- Use `localhost:25` for SMTP connection
- No authentication needed for local Postfix relay
- Postfix handles Gmail SASL authentication
- Fallback to Resend API if Postfix unavailable

## 🚀 Next Steps Required

### CRITICAL: Configure Gmail App Password

**The email server will NOT work until you complete this step:**

1. **Enable 2-Factor Authentication** on `ailabsafrica@gmail.com`
   - Go to: https://myaccount.google.com/security
   - Enable "2-Step Verification"

2. **Generate App Password**
   - Go to: https://myaccount.google.com/apppasswords
   - Create app password for "Mail" / "KasaAI Email Server"
   - Copy the 16-character password (remove spaces)

3. **Configure Postfix with App Password**
   ```bash
   cd /opt/kasaai/apps/core_backend
   /opt/kasaai/apps/venv/bin/python scripts/setup_email_server.py \
     --gmail-password "YOUR_16_CHAR_APP_PASSWORD"
   ```

4. **Test Email Delivery**
   ```bash
   /opt/kasaai/apps/venv/bin/python scripts/setup_email_server.py \
     --test-email ailabsafrica@gmail.com
   ```

## 📁 Files Created/Modified

### New Files

1. **`/opt/kasaai/apps/core_backend/scripts/setup_email_server.py`**
   - Email server setup and testing script
   - Configures SASL password file
   - Sends test emails
   - Monitors mail logs

2. **`/opt/kasaai/apps/core_backend/EMAIL_SERVER_SETUP.md`**
   - Comprehensive email server documentation
   - Configuration details
   - Troubleshooting guide
   - Monitoring commands

3. **`/opt/kasaai/apps/core_backend/GMAIL_APP_PASSWORD_SETUP.md`**
   - Step-by-step Gmail app password setup
   - Quick command reference
   - Security best practices

4. **`/opt/kasaai/apps/core_backend/tests/test_email_service.py`**
   - Unit tests for email functionality
   - 14 test cases covering:
     - SMTP connections
     - Email message creation
     - Sending emails
     - HTML content
     - Fallback mechanisms
     - Validation

### Modified Files

1. **`/opt/kasaai/.env`**
   - Updated `SMTP_PORT` from `587` to `25`
   - Added Resend API key for fallback
   - Added comments about Postfix relay

2. **`/opt/kasaai/apps/core_backend/backend/routes/call_management.py`**
   - Updated to use `localhost:25` for SMTP
   - Removed local SMTP authentication (Postfix handles it)
   - Simplified email sending logic
   - Maintained Resend fallback

3. **`/etc/postfix/main.cf`** (System file)
   - Configured Gmail relay
   - Enabled SASL authentication
   - Enabled TLS encryption

4. **`/etc/postfix/sasl_passwd`** (System file)
   - Created SASL password file (needs real app password)

## ✅ What's Working Now

1. ✅ **Postfix Service**
   - Running and listening on port 25
   - Configured to relay through Gmail SMTP
   - TLS encryption enabled

2. ✅ **Email Queue System**
   - Emails are successfully queued
   - Postfix attempts delivery to Gmail
   - Logs are properly recorded

3. ✅ **Call Management Integration**
   - Routes updated to use localhost SMTP
   - HTML email templates working
   - Error handling and fallback in place

4. ✅ **Unit Tests**
   - 14 tests created and passing
   - Coverage for all email scenarios
   - Mocked SMTP connections for testing

## ⚠️ What's NOT Working Yet

1. ❌ **Actual Email Delivery**
   - **Reason**: Gmail app password not configured
   - **Status**: Emails queued but deferred
   - **Error**: `SASL authentication failed`
   - **Solution**: Complete "Next Steps Required" above

## 🧪 Testing Status

### Current Test Result
```bash
$ /opt/kasaai/apps/venv/bin/python scripts/setup_email_server.py --test-email ailabsafrica@gmail.com

✅ Postfix service is running
✅ Test email sent successfully to ailabsafrica@gmail.com
📬 Email queued for delivery via Postfix relay
```

### Mail Queue Status
```bash
$ mailq

-Queue ID-  --Size-- ----Arrival Time---- -Sender/Recipient-------
0E8453188BC6    4161 Mon Oct 20 10:56:28  noreply@ailabsafrica.com
(SASL authentication failed; server smtp.gmail.com said:
 535-5.7.8 Username and Password not accepted)
                                         ailabsafrica@gmail.com

-- 4 Kbytes in 1 Request.
```

**Analysis**: Email is queued and Postfix is attempting delivery, but Gmail is rejecting due to missing/invalid app password.

### Unit Tests
```bash
$ /opt/kasaai/apps/venv/bin/python -m pytest tests/test_email_service.py -v

14 passed, 2 warnings in 0.04s
```

## 📚 Documentation

Three comprehensive guides have been created:

1. **`EMAIL_SERVER_SETUP.md`**
   - Full technical documentation
   - Configuration reference
   - Troubleshooting guide
   - Monitoring commands

2. **`GMAIL_APP_PASSWORD_SETUP.md`**
   - Step-by-step setup instructions
   - Quick command reference
   - Security best practices
   - Troubleshooting

3. **`EMAIL_SETUP_COMPLETE.md`** (this file)
   - Summary of what was done
   - Current status
   - Next steps required

## 🔍 Monitoring & Troubleshooting

### Check Email Queue
```bash
mailq
```

### View Mail Logs
```bash
sudo tail -f /var/log/mail.log
```

### Check Postfix Status
```bash
sudo systemctl status postfix
```

### Test Email Sending
```bash
cd /opt/kasaai/apps/core_backend
/opt/kasaai/apps/venv/bin/python scripts/setup_email_server.py \
  --test-email ailabsafrica@gmail.com
```

### Flush Mail Queue (Force Retry)
```bash
sudo postqueue -f
```

### View Postfix Configuration
```bash
sudo postconf | grep -E "(relayhost|smtp_sasl)"
```

## 🎯 How Email Notifications Work

When a VAPI call completes:

1. **Webhook Received**
   - Endpoint: `/call-management/vapi/webhook`
   - Receives VAPI end-of-call-report

2. **Background Processing**
   - Generate AI summary of transcript
   - Track Vonage call costs
   - Link to automation config
   - Save to MongoDB

3. **Email Notification**
   - Create HTML email with:
     - Call summary
     - Customer information
     - Call metrics (duration, cost)
     - Transcript preview
   - Send via `send_email_async()` function
   - Connect to `localhost:25` (Postfix)
   - Postfix queues and relays to Gmail
   - Delivered to `ailabsafrica@gmail.com`

4. **Error Handling**
   - If Postfix fails: fallback to Resend API
   - All errors logged to `/var/log/mail.log`
   - Non-critical: webhook processing continues

## 🔐 Security Considerations

1. **SASL Password File**
   - Protected with `600` permissions (root only)
   - Contains sensitive Gmail app password
   - Hashed in `.db` file

2. **Gmail App Password**
   - Dedicated password for this application
   - Can be revoked independently
   - No access to main Gmail password

3. **TLS Encryption**
   - All SMTP traffic to Gmail is encrypted
   - Uses system CA certificates

4. **Environment Variables**
   - SMTP credentials in `.env` (gitignored)
   - Resend API key as backup

## 📊 Email Statistics (Future)

Once operational, you can track:
- Total emails sent
- Delivery success rate
- Queue delays
- Failures and bounces

Monitor with:
```bash
# Sent emails count
sudo grep -c "status=sent" /var/log/mail.log

# Failed deliveries
sudo grep -c "status=bounced\|status=deferred" /var/log/mail.log

# Today's email activity
sudo grep "$(date +%b\ %d)" /var/log/mail.log | grep "status=sent"
```

## 🛠️ Maintenance

### Regular Tasks

1. **Monitor Queue** (daily)
   ```bash
   mailq
   ```

2. **Check Logs** (weekly)
   ```bash
   sudo grep -i error /var/log/mail.log | tail -50
   ```

3. **Rotate App Password** (every 90 days)
   - Generate new Gmail app password
   - Update SASL file
   - Restart Postfix

4. **Clear Old Logs** (monthly)
   ```bash
   sudo logrotate -f /etc/logrotate.d/rsyslog
   ```

## 🎉 Success Criteria

Email server will be fully operational when:

- ✅ Postfix is running (DONE)
- ✅ SASL configuration is set (DONE)
- ✅ TLS encryption enabled (DONE)
- ✅ Call management integration updated (DONE)
- ✅ Unit tests passing (DONE)
- ⏳ Gmail app password configured (PENDING - USER ACTION)
- ⏳ Test email successfully delivered (PENDING - USER ACTION)
- ⏳ No errors in mail.log (PENDING - USER ACTION)
- ⏳ Mail queue is empty (PENDING - USER ACTION)

## 📞 Support

If you encounter issues:

1. Read the documentation:
   - `EMAIL_SERVER_SETUP.md` for technical details
   - `GMAIL_APP_PASSWORD_SETUP.md` for credentials setup

2. Check the logs:
   ```bash
   sudo tail -100 /var/log/mail.log
   ```

3. Verify configuration:
   ```bash
   sudo postconf | grep smtp
   ```

4. Test manually:
   ```bash
   /opt/kasaai/apps/venv/bin/python scripts/setup_email_server.py --test-email YOUR_EMAIL
   ```

## 🚀 Ready to Go Live!

**Final Step**: Configure Gmail app password and test:

```bash
# 1. Configure (after getting app password from Gmail)
cd /opt/kasaai/apps/core_backend
/opt/kasaai/apps/venv/bin/python scripts/setup_email_server.py \
  --gmail-password "YOUR_APP_PASSWORD"

# 2. Test
/opt/kasaai/apps/venv/bin/python scripts/setup_email_server.py \
  --test-email ailabsafrica@gmail.com

# 3. Check inbox
# You should receive a beautifully formatted test email!

# 4. Monitor logs
sudo tail -f /var/log/mail.log
```

---

**Setup Date**: October 20, 2025
**Status**: ✅ Configured, ⏳ Awaiting Gmail App Password
**Services**: Postfix, Call Management, Email Notifications
**Next Action**: Generate and configure Gmail app password
