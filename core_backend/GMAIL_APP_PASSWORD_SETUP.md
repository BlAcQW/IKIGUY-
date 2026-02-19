# Gmail App Password Setup Guide

## What Password Do You Need?

You need a **Gmail App Password** (NOT your regular Gmail password). This is a 16-character password that Gmail generates specifically for third-party applications.

## Why App Password?

- Google requires app-specific passwords for "less secure" applications
- Your regular Gmail password won't work for SMTP authentication
- App passwords provide better security and can be revoked individually
- Required when 2-Factor Authentication is enabled

## Step-by-Step Setup Instructions

### 1. Enable 2-Factor Authentication (2FA)

**IMPORTANT**: You must enable 2FA before you can create app passwords.

1. Go to: https://myaccount.google.com/security
2. Sign in with `ailabsafrica@gmail.com`
3. Find **"2-Step Verification"** section
4. Click **"Get Started"** if not already enabled
5. Follow the prompts to set up 2FA (via phone or authenticator app)

### 2. Generate App Password

Once 2FA is enabled:

1. Go to: https://myaccount.google.com/apppasswords
   - Or navigate: Google Account → Security → 2-Step Verification → App passwords

2. You may need to sign in again

3. Under "Select app":
   - Choose **"Mail"**

4. Under "Select device":
   - Choose **"Other (Custom name)"**
   - Enter: **"KasaAI Email Server"**

5. Click **"Generate"**

6. Google will show a 16-character password like:
   ```
   xxxx xxxx xxxx xxxx
   ```

7. **IMPORTANT**:
   - Copy this password immediately (you won't see it again)
   - Remove the spaces: `xxxxxxxxxxxxxxxx`
   - Save it securely

### 3. Configure KasaAI with App Password

Once you have the app password, run this command:

```bash
cd /opt/kasaai/apps/core_backend
/opt/kasaai/apps/venv/bin/python scripts/setup_email_server.py --gmail-password "YOUR_16_CHAR_PASSWORD"
```

**Example** (replace with your actual password):
```bash
/opt/kasaai/apps/venv/bin/python scripts/setup_email_server.py --gmail-password "abcdabcdabcdabcd"
```

### 4. Test Email Delivery

After configuring, test the setup:

```bash
/opt/kasaai/apps/venv/bin/python scripts/setup_email_server.py --test-email ailabsafrica@gmail.com
```

## Quick Command Reference

```bash
# 1. Configure with app password
cd /opt/kasaai/apps/core_backend
/opt/kasaai/apps/venv/bin/python scripts/setup_email_server.py \
  --gmail-password "YOUR_APP_PASSWORD_HERE"

# 2. Test email sending
/opt/kasaai/apps/venv/bin/python scripts/setup_email_server.py \
  --test-email ailabsafrica@gmail.com

# 3. Check mail queue
mailq

# 4. View delivery logs
sudo tail -f /var/log/mail.log
```

## Troubleshooting

### Problem: "App passwords" option not showing

**Solution**: Ensure 2-Factor Authentication is fully enabled first.

### Problem: App password not working

**Solutions**:
1. Verify you copied the entire 16-character password
2. Remove all spaces from the password
3. Try regenerating a new app password
4. Ensure using `ailabsafrica@gmail.com` account

### Problem: Emails still not sending

**Check**:
```bash
# 1. Check mail queue
mailq

# 2. View errors
sudo tail -30 /var/log/mail.log

# 3. Verify Postfix configuration
sudo postconf | grep relayhost

# 4. Test SASL file
sudo cat /etc/postfix/sasl_passwd
```

## Security Best Practices

1. **Never share app passwords** - they provide full access to send emails
2. **Revoke unused passwords** - If you regenerate, delete the old one
3. **Use unique passwords** - Generate separate app passwords for different services
4. **Monitor usage** - Check Gmail sent folder for unauthorized emails
5. **Rotate regularly** - Change app passwords every 90 days

## Revoking App Passwords

If you need to revoke an app password:

1. Go to: https://myaccount.google.com/apppasswords
2. Find "KasaAI Email Server"
3. Click **"Remove"**
4. Generate a new one and reconfigure

## Alternative: Using Different Gmail Account

If you want to use a different Gmail account:

1. Generate app password for that account
2. Update `/etc/postfix/sasl_passwd`:
   ```
   [smtp.gmail.com]:587 your-email@gmail.com:APP_PASSWORD
   ```
3. Run: `sudo postmap /etc/postfix/sasl_passwd`
4. Restart Postfix: `sudo systemctl restart postfix`

## What Happens After Setup?

Once configured:

1. **Call Management System** sends email notification
2. **Python application** connects to `localhost:25` (Postfix)
3. **Postfix** receives email and queues it
4. **Postfix** connects to `smtp.gmail.com:587` using app password
5. **Gmail** authenticates and accepts the email
6. **Gmail** delivers to `ailabsafrica@gmail.com`

## Email Flow Diagram

```
┌─────────────────────┐
│  VAPI Call Webhook  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Generate Summary   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Create HTML Email  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Postfix (Port 25)  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Gmail SMTP (587)   │  ← Uses App Password
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Inbox: ailabsafrica│
│      @gmail.com     │
└─────────────────────┘
```

## Additional Resources

- [Google App Passwords Help](https://support.google.com/accounts/answer/185833)
- [Postfix SASL Authentication](http://www.postfix.org/SASL_README.html)
- [Email Server Setup Guide](./EMAIL_SERVER_SETUP.md)

## Need Help?

If you're still having issues:

1. Check the detailed logs: `sudo tail -f /var/log/mail.log`
2. Verify app password: `sudo cat /etc/postfix/sasl_passwd`
3. Test Gmail SMTP directly: `telnet smtp.gmail.com 587`
4. Contact system administrator

---

**Remember**: The app password is a **16-character code** generated by Gmail, NOT your regular Gmail password!
