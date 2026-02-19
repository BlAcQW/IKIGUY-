# Email Server Quick Start Guide

## TL;DR - What You Need to Do

Your email server is **90% configured**. You just need to:

1. Get a Gmail app password (2 minutes)
2. Run one command to configure it (10 seconds)
3. Test it (5 seconds)

## Step 1: Get Gmail App Password

### Enable 2FA (if not already enabled)
1. Go to: https://myaccount.google.com/security
2. Sign in with `ailabsafrica@gmail.com`
3. Enable **"2-Step Verification"**

### Generate App Password
1. Go to: https://myaccount.google.com/apppasswords
2. Select: **Mail** → **Other (Custom name)** → **"KasaAI Email Server"**
3. Click **Generate**
4. Copy the 16-character password (it looks like: `xxxx xxxx xxxx xxxx`)
5. Remove spaces → `xxxxxxxxxxxxxxxx`

## Step 2: Configure Email Server

Run this command with your app password:

```bash
cd /opt/kasaai/apps/core_backend
/opt/kasaai/apps/venv/bin/python scripts/setup_email_server.py --gmail-password "YOUR_APP_PASSWORD"
```

**Example** (replace with your actual password):
```bash
/opt/kasaai/apps/venv/bin/python scripts/setup_email_server.py --gmail-password "abcdabcdabcdabcd"
```

## Step 3: Test Email Delivery

```bash
/opt/kasaai/apps/venv/bin/python scripts/setup_email_server.py --test-email ailabsafrica@gmail.com
```

Check your inbox at `ailabsafrica@gmail.com` - you should receive a test email!

## Step 4: Verify Everything Works

```bash
# Check mail queue (should be empty after successful delivery)
mailq

# View recent deliveries
sudo grep "status=sent" /var/log/mail.log | tail -5
```

## That's It! 🎉

Your call management system will now automatically send email notifications when VAPI calls complete.

## Quick Commands Reference

```bash
# Configure email server
cd /opt/kasaai/apps/core_backend
/opt/kasaai/apps/venv/bin/python scripts/setup_email_server.py \
  --gmail-password "YOUR_APP_PASSWORD"

# Send test email
/opt/kasaai/apps/venv/bin/python scripts/setup_email_server.py \
  --test-email ailabsafrica@gmail.com

# Check email queue
mailq

# View logs
sudo tail -f /var/log/mail.log

# Restart Postfix
sudo systemctl restart postfix

# Check Postfix status
sudo systemctl status postfix
```

## What Happens After Configuration?

When a VAPI call completes:
1. Call summary is generated using AI
2. Email notification is created with call details
3. Email is sent via Postfix → Gmail → `ailabsafrica@gmail.com`
4. You receive a beautiful HTML email with:
   - Call summary
   - Customer information
   - Call duration and cost
   - Transcript preview

## Troubleshooting

### No email received?
```bash
# Check queue
mailq

# Check logs
sudo tail -30 /var/log/mail.log

# Retry delivery
sudo postqueue -f
```

### Authentication failed?
- Verify app password is correct (16 characters, no spaces)
- Ensure 2FA is enabled on Gmail
- Try regenerating the app password

### Need more help?
- Read: `EMAIL_SERVER_SETUP.md` (full technical guide)
- Read: `GMAIL_APP_PASSWORD_SETUP.md` (credential setup)
- Read: `EMAIL_SETUP_COMPLETE.md` (what was configured)

---

**Need Help?** Run the setup script with `--help`:
```bash
/opt/kasaai/apps/venv/bin/python scripts/setup_email_server.py --help
```
