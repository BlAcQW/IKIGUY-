# Using a Remote Mail Server

## Overview

Yes! You can absolutely use a mail server running on another server. This is actually a very common production setup.

## Benefits of Using Remote Mail Server

- ✅ Centralized email management
- ✅ Better deliverability (dedicated mail server)
- ✅ SPF/DKIM/DMARC properly configured
- ✅ No need to configure Postfix locally
- ✅ Easier to manage multiple applications
- ✅ Professional email infrastructure

---

## Option 1: Direct SMTP Connection (Recommended)

### Step 1: Test Your Remote SMTP Server

Run the interactive test script:

```bash
cd /opt/kasaai/apps/core_backend
/opt/kasaai/apps/venv/bin/python scripts/test_remote_smtp.py
```

It will ask you:
- SMTP server hostname/IP
- SMTP port (25, 587, or 465)
- Username/password (if required)
- Whether to use TLS

### Step 2: Update .env Configuration

Once the test passes, update `/opt/kasaai/.env`:

```ini
# Remote SMTP Server Configuration
SMTP_SERVER=mail.yourdomain.com  # Your mail server IP or hostname
SMTP_PORT=587  # Common ports: 25 (plain), 587 (STARTTLS), 465 (SSL)
SMTP_USERNAME=noreply@yourdomain.com  # Email account username
SMTP_PASSWORD=your_password_here  # Password for the account
SENDER_EMAIL=noreply@yourdomain.com  # From address
```

### Step 3: Update call_management.py (if needed)

The current code already supports remote SMTP! It reads from .env:

```python
smtp_server = os.getenv("SMTP_SERVER", "localhost")
smtp_port = int(os.getenv("SMTP_PORT", "25"))
smtp_username = os.getenv("SMTP_USERNAME")
smtp_password = os.getenv("SMTP_PASSWORD")
```

If you need STARTTLS support, update the `send_email_async()` function:

```python
server = smtplib.SMTP(smtp_server, smtp_port, timeout=30)

# Add STARTTLS if using port 587
if smtp_port == 587:
    server.starttls()

# Authenticate if credentials provided
if smtp_username and smtp_password:
    server.login(smtp_username, smtp_password)
```

### Step 4: Restart Backend Service

```bash
sudo systemctl restart kasaai-core-backend
```

### Step 5: Test Email Sending

```bash
cd /opt/kasaai/apps/core_backend
/opt/kasaai/apps/venv/bin/python scripts/setup_email_server.py \
  --test-email ailabsafrica@gmail.com
```

---

## Option 2: Use Local Postfix as Relay

Keep local Postfix but relay through your remote mail server.

### Configure Postfix

```bash
# Set relay host
sudo postconf -e "relayhost = [mail.yourdomain.com]:587"

# Enable SASL authentication
sudo postconf -e "smtp_sasl_auth_enable = yes"
sudo postconf -e "smtp_sasl_security_options = noanonymous"
sudo postconf -e "smtp_sasl_password_maps = hash:/etc/postfix/sasl_passwd"

# Enable TLS
sudo postconf -e "smtp_tls_security_level = encrypt"
sudo postconf -e "smtp_tls_CAfile = /etc/ssl/certs/ca-certificates.crt"
```

### Create SASL Password File

```bash
# Create password file
echo "[mail.yourdomain.com]:587 username:password" | sudo tee /etc/postfix/sasl_passwd

# Generate database
sudo postmap /etc/postfix/sasl_passwd

# Secure files
sudo chmod 600 /etc/postfix/sasl_passwd*

# Restart Postfix
sudo systemctl restart postfix
```

### Test

```bash
echo "Test email" | mail -s "Test" ailabsafrica@gmail.com
```

---

## Common Remote Server Types

### 1. **iRedMail Server**

```ini
SMTP_SERVER=mail.yourdomain.com
SMTP_PORT=587
SMTP_USERNAME=noreply@yourdomain.com
SMTP_PASSWORD=your_password
SENDER_EMAIL=noreply@yourdomain.com
```

### 2. **Mailcow**

```ini
SMTP_SERVER=mailcow.yourdomain.com
SMTP_PORT=587
SMTP_USERNAME=noreply@yourdomain.com
SMTP_PASSWORD=your_password
SENDER_EMAIL=noreply@yourdomain.com
```

### 3. **cPanel/WHM Server**

```ini
SMTP_SERVER=mail.yourhost.com
SMTP_PORT=587
SMTP_USERNAME=noreply@yourdomain.com
SMTP_PASSWORD=your_cpanel_email_password
SENDER_EMAIL=noreply@yourdomain.com
```

### 4. **Plesk Server**

```ini
SMTP_SERVER=mail.yourhost.com
SMTP_PORT=587
SMTP_USERNAME=noreply@yourdomain.com
SMTP_PASSWORD=your_plesk_email_password
SENDER_EMAIL=noreply@yourdomain.com
```

### 5. **Office 365**

```ini
SMTP_SERVER=smtp.office365.com
SMTP_PORT=587
SMTP_USERNAME=noreply@yourdomain.com
SMTP_PASSWORD=your_office365_password
SENDER_EMAIL=noreply@yourdomain.com
```

### 6. **Google Workspace**

```ini
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=noreply@yourdomain.com
SMTP_PASSWORD=your_app_password  # Requires app password
SENDER_EMAIL=noreply@yourdomain.com
```

### 7. **Custom Postfix/Exim Server**

```ini
SMTP_SERVER=123.45.67.89  # Or hostname
SMTP_PORT=25  # Or 587 if TLS required
SMTP_USERNAME=  # Leave empty if no auth required
SMTP_PASSWORD=  # Leave empty if no auth required
SENDER_EMAIL=noreply@yourdomain.com
```

---

## Port Numbers Guide

| Port | Description | Security | When to Use |
|------|-------------|----------|-------------|
| **25** | SMTP | Plain text | Internal servers, no auth |
| **587** | Submission | STARTTLS | Most common, requires auth |
| **465** | SMTPS | SSL/TLS | Older, less common |
| **2525** | Alternative | STARTTLS | When 25/587 blocked |

---

## Testing Checklist

Before going live, test these:

1. **Connection Test**
   ```bash
   telnet mail.yourdomain.com 587
   # Should see: 220 mail.yourdomain.com ESMTP
   ```

2. **Authentication Test**
   ```bash
   /opt/kasaai/apps/venv/bin/python scripts/test_remote_smtp.py
   ```

3. **Email Delivery Test**
   ```bash
   /opt/kasaai/apps/venv/bin/python scripts/setup_email_server.py \
     --test-email ailabsafrica@gmail.com
   ```

4. **Check Logs**
   ```bash
   sudo tail -f /var/log/mail.log  # If using Postfix relay
   # Or check your remote server's logs
   ```

---

## Firewall Configuration

Make sure your firewall allows outbound SMTP:

```bash
# Allow outbound SMTP (if using UFW)
sudo ufw allow out 25/tcp
sudo ufw allow out 587/tcp
sudo ufw allow out 465/tcp
```

---

## Security Best Practices

1. **Use TLS/STARTTLS**
   - Always encrypt SMTP connections
   - Use port 587 with STARTTLS

2. **Strong Passwords**
   - Use strong passwords for SMTP accounts
   - Consider app-specific passwords

3. **Limit Permissions**
   - SMTP account should only have send permission
   - No need for IMAP/POP3 access

4. **Monitor Usage**
   - Watch for unauthorized email sending
   - Set up alerts for high volume

5. **SPF/DKIM Records**
   - Ensure remote server has proper DNS records
   - Verify SPF includes your application server's IP

---

## Troubleshooting

### Issue: Connection Timeout

```bash
# Test connectivity
telnet mail.yourdomain.com 587

# Check firewall
sudo ufw status

# Verify DNS
nslookup mail.yourdomain.com
```

### Issue: Authentication Failed

- Verify username/password
- Check if account requires app password
- Ensure account has SMTP permission
- Try port 25 if 587 fails

### Issue: Relay Access Denied

- Verify SMTP server allows relay from your IP
- Check if authentication is required
- Ensure sender domain is allowed

### Issue: TLS Errors

```bash
# Test TLS connection
openssl s_client -connect mail.yourdomain.com:587 -starttls smtp
```

---

## Example: Complete Setup with Remote iRedMail

If you have an iRedMail server at `mail.example.com`:

### 1. Create Email Account on iRedMail
- Login to iRedMail admin panel
- Create account: `noreply@example.com`
- Set password

### 2. Update .env
```ini
SMTP_SERVER=mail.example.com
SMTP_PORT=587
SMTP_USERNAME=noreply@example.com
SMTP_PASSWORD=your_password_here
SENDER_EMAIL=noreply@example.com
```

### 3. Test Connection
```bash
cd /opt/kasaai/apps/core_backend
/opt/kasaai/apps/venv/bin/python scripts/test_remote_smtp.py
# Enter: mail.example.com, 587, noreply@example.com, password
```

### 4. Restart Service
```bash
sudo systemctl restart kasaai-core-backend
```

### 5. Done!
Emails will now be sent through your iRedMail server.

---

## Performance Considerations

### Local Postfix Relay (Faster)
- Queues emails locally
- Relays in background
- Application doesn't wait for delivery

### Direct SMTP (Simpler)
- Connects directly to remote server
- May add latency to webhook processing
- Use async sending (already implemented)

---

## Recommendation

**Best Setup:**
1. Use **Direct SMTP connection** (Option 1)
2. Configure proper credentials in .env
3. Use port **587** with **STARTTLS**
4. Enable **async email sending** (already done in call_management.py)

This gives you:
- ✅ Simple configuration
- ✅ No local Postfix needed
- ✅ Works with any SMTP server
- ✅ Easy to troubleshoot

---

## Quick Start Commands

```bash
# 1. Test your remote SMTP server
cd /opt/kasaai/apps/core_backend
/opt/kasaai/apps/venv/bin/python scripts/test_remote_smtp.py

# 2. Update .env with the settings from test

# 3. Restart backend
sudo systemctl restart kasaai-core-backend

# 4. Test email delivery
/opt/kasaai/apps/venv/bin/python scripts/setup_email_server.py \
  --test-email ailabsafrica@gmail.com

# 5. Check inbox - Done! 🎉
```

---

## Need Help?

Run the interactive setup:
```bash
/opt/kasaai/apps/venv/bin/python scripts/test_remote_smtp.py
```

It will guide you through testing and provide the exact .env configuration you need!
