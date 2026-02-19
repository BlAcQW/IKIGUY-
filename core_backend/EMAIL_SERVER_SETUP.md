# Email Server Setup Guide

## Overview

The KasaAI system uses **Postfix** as a local mail transfer agent (MTA) that relays emails through **Gmail SMTP**. This provides reliable email delivery for call notifications and summaries.

## Architecture

```
┌──────────────────┐      ┌──────────────┐      ┌─────────────┐
│  Call Management │ -->  │   Postfix    │ -->  │   Gmail     │ --> Recipient
│      Service     │      │  (localhost) │      │  SMTP Relay │
└──────────────────┘      └──────────────┘      └─────────────┘
   Port 8000                Port 25              Port 587
```

## Gmail App Password Setup

### Step 1: Enable 2-Factor Authentication
1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Sign in with `ailabsafrica@gmail.com`
3. Navigate to **"2-Step Verification"**
4. Enable 2-FA if not already enabled

### Step 2: Generate App Password
1. Once 2-FA is enabled, go to [App Passwords](https://myaccount.google.com/apppasswords)
2. Click **"Select app"** → Choose **"Mail"**
3. Click **"Select device"** → Choose **"Other (Custom name)"**
4. Enter name: **"KasaAI Email Server"**
5. Click **"Generate"**
6. Copy the 16-character password (format: `xxxx xxxx xxxx xxxx`)
7. Remove spaces (final format: `xxxxxxxxxxxxxxxx`)

### Step 3: Configure Postfix with App Password

Run the setup script with your Gmail app password:

```bash
cd /opt/kasaai/apps/core_backend
/opt/kasaai/apps/venv/bin/python scripts/setup_email_server.py --gmail-password "YOUR_APP_PASSWORD_HERE"
```

**Important**: Replace `YOUR_APP_PASSWORD_HERE` with the actual 16-character app password (no spaces)

## Manual Configuration (Alternative)

If you prefer to configure manually:

### 1. Edit SASL Password File

```bash
sudo nano /etc/postfix/sasl_passwd
```

Add this line (replace with your actual app password):
```
[smtp.gmail.com]:587 ailabsafrica@gmail.com:YOUR_APP_PASSWORD
```

### 2. Update Postfix Database

```bash
sudo postmap /etc/postfix/sasl_passwd
sudo chmod 600 /etc/postfix/sasl_passwd
sudo chmod 600 /etc/postfix/sasl_passwd.db
```

### 3. Restart Postfix

```bash
sudo systemctl restart postfix
```

## Postfix Configuration

The following Postfix settings are already configured:

```ini
relayhost = [smtp.gmail.com]:587
smtp_sasl_auth_enable = yes
smtp_sasl_security_options = noanonymous
smtp_sasl_password_maps = hash:/etc/postfix/sasl_passwd
smtp_tls_security_level = encrypt
smtp_tls_CAfile = /etc/ssl/certs/ca-certificates.crt
```

## Testing Email Delivery

### Test 1: Using Setup Script

```bash
cd /opt/kasaai/apps/core_backend
/opt/kasaai/apps/venv/bin/python scripts/setup_email_server.py --test-email ailabsafrica@gmail.com
```

### Test 2: Using Command Line

```bash
echo "This is a test email from KasaAI" | mail -s "Test Email" ailabsafrica@gmail.com
```

### Test 3: Check Mail Queue

```bash
# View mail queue
mailq

# View detailed queue
postqueue -p

# Flush queue (force delivery)
sudo postqueue -f
```

## Monitoring and Troubleshooting

### Check Postfix Status

```bash
sudo systemctl status postfix
```

### View Mail Logs

```bash
# Real-time log monitoring
sudo tail -f /var/log/mail.log

# Recent errors
sudo grep -i error /var/log/mail.log | tail -20

# Recent deliveries
sudo grep -i "status=sent" /var/log/mail.log | tail -10
```

### Common Issues and Solutions

#### Issue 1: Authentication Failed

**Error**: `SASL authentication failed`

**Solution**:
- Verify Gmail app password is correct (16 characters, no spaces)
- Ensure 2-FA is enabled on the Gmail account
- Regenerate app password if needed
- Update SASL password file and restart Postfix

#### Issue 2: Connection Timeout

**Error**: `Connection timed out`

**Solution**:
- Check firewall allows outbound port 587
- Verify DNS resolution: `nslookup smtp.gmail.com`
- Test connectivity: `telnet smtp.gmail.com 587`

```bash
# Allow outbound SMTP if using firewall
sudo ufw allow out 587/tcp
```

#### Issue 3: Messages Stuck in Queue

**Error**: Mail in `mailq` not delivering

**Solution**:
```bash
# View detailed error
sudo postcat -vq QUEUE_ID

# Flush queue
sudo postqueue -f

# Delete specific message
sudo postsuper -d QUEUE_ID

# Delete all queued messages
sudo postsuper -d ALL
```

#### Issue 4: Emails Rejected by Gmail

**Error**: `Relay access denied` or `Sender address rejected`

**Solution**:
- Ensure sender email is `noreply@ailabsafrica.com` or another verified sender
- Check Gmail account hasn't hit sending limits
- Verify SASL credentials are for the correct account

## Environment Variables

The following environment variables are configured in `/opt/kasaai/.env`:

```ini
# Local Postfix Mail Server Configuration
SMTP_SERVER=localhost
SMTP_PORT=25
SMTP_USERNAME=noreply@ailabsafrica.com
SMTP_PASSWORD=noreply_secure_2025
SENDER_EMAIL=noreply@ailabsafrica.com

# Resend API as fallback
RESEND_API=re_3CKHxpwj_Jk9DmyqvF8nBDQbNWa2Lz6oB
```

## Email Flow in Call Management

When a VAPI call completes:

1. **Webhook Received**: `/call-management/vapi/webhook`
2. **Background Processing**:
   - Generate AI summary
   - Track costs
   - Save to database
3. **Email Notification**:
   - Create HTML email with call summary
   - Send via Postfix (localhost:25)
   - Postfix relays to Gmail SMTP (smtp.gmail.com:587)
   - Gmail delivers to `ailabsafrica@gmail.com`

## Service Management

### Start Postfix

```bash
sudo systemctl start postfix
```

### Stop Postfix

```bash
sudo systemctl stop postfix
```

### Restart Postfix

```bash
sudo systemctl restart postfix
```

### Enable on Boot

```bash
sudo systemctl enable postfix
```

### Check if Running

```bash
sudo netstat -tlnp | grep :25
```

## Security Best Practices

1. **Protect SASL Password File**
   ```bash
   # Should be 600 (readable only by root)
   ls -la /etc/postfix/sasl_passwd*
   ```

2. **Use App-Specific Passwords**
   - Never use main Gmail password
   - Generate separate app passwords for different services
   - Revoke unused app passwords

3. **Monitor Failed Attempts**
   ```bash
   sudo grep -i "authentication failed" /var/log/mail.log
   ```

4. **Rotate Credentials Regularly**
   - Generate new Gmail app password every 90 days
   - Update SASL password file
   - Restart Postfix

## Testing Checklist

- [ ] Postfix service is running
- [ ] Port 25 is listening
- [ ] SASL password file configured
- [ ] Gmail app password is valid
- [ ] Test email sent successfully
- [ ] Email received in Gmail inbox
- [ ] No errors in `/var/log/mail.log`
- [ ] Call management webhook sends notifications

## Quick Reference Commands

```bash
# Setup email server
cd /opt/kasaai/apps/core_backend
/opt/kasaai/apps/venv/bin/python scripts/setup_email_server.py --gmail-password "APP_PASSWORD"

# Send test email
/opt/kasaai/apps/venv/bin/python scripts/setup_email_server.py --test-email ailabsafrica@gmail.com

# Check Postfix status
sudo systemctl status postfix

# View mail logs
sudo tail -f /var/log/mail.log

# Check mail queue
mailq

# Flush mail queue
sudo postqueue -f

# Restart Postfix
sudo systemctl restart postfix
```

## Support

For issues or questions:
1. Check `/var/log/mail.log` for detailed error messages
2. Verify Gmail app password hasn't been revoked
3. Ensure firewall allows outbound port 587
4. Test direct Gmail SMTP connection
5. Contact system administrator

## Related Files

- **Setup Script**: `/opt/kasaai/apps/core_backend/scripts/setup_email_server.py`
- **Call Management Routes**: `/opt/kasaai/apps/core_backend/backend/routes/call_management.py`
- **Environment Config**: `/opt/kasaai/.env`
- **Postfix Main Config**: `/etc/postfix/main.cf`
- **Postfix Master Config**: `/etc/postfix/master.cf`
- **SASL Password**: `/etc/postfix/sasl_passwd`
- **Mail Logs**: `/var/log/mail.log`
