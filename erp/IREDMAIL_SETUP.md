# iRedMail Email Account Setup for ERP System

**Mail Server**: mail.ailabsafrica.com
**Last Updated**: 2025-02-11

---

## Overview

The ERP system users need corresponding email accounts in iRedMail for:
- Password reset emails from Supabase
- System notifications
- User communication
- Admin notifications

## Required Email Accounts

### 1. Admin User
- **Email**: admin@ailabsafrica.com
- **Password**: Admin@2024!
- **Purpose**: Universal admin account
- **Quota**: 1024 MB

### 2. Regular User
- **Email**: user@ailabsafrica.com
- **Password**: User@2024!
- **Purpose**: Standard user account for testing
- **Quota**: 512 MB

### 3. System Email (Optional)
- **Email**: noreply@ailabsafrica.com
- **Purpose**: Automated emails (Supabase notifications)
- **Quota**: 256 MB

---

## Setup Methods

### Method 1: Web Interface (Recommended)

1. **Access iRedMail Admin Panel**
   ```
   URL: https://mail.ailabsafrica.com/iredadmin
   Username: postmaster@ailabsafrica.com
   Password: <postmaster-password>
   ```

2. **Create Admin User**
   - Navigate to: **Domains** → **ailabsafrica.com** → **Users**
   - Click **Add User**
   - Fill in:
     - Email: `admin@ailabsafrica.com`
     - Password: `Admin@2024!`
     - Display Name: `KasaAI Admin`
     - Quota: `1024` MB
     - Language: English
   - Click **Add**

3. **Create Regular User**
   - Same steps as above with:
     - Email: `user@ailabsafrica.com`
     - Password: `User@2024!`
     - Display Name: `KasaAI User`
     - Quota: `512` MB

4. **Create System Email (Optional)**
   - Same steps with:
     - Email: `noreply@ailabsafrica.com`
     - Password: `NoReply@2024!`
     - Display Name: `KasaAI System`
     - Quota: `256` MB

### Method 2: Command Line

1. **SSH to Mail Server**
   ```bash
   ssh root@mail.ailabsafrica.com
   ```

2. **Navigate to Tools Directory**
   ```bash
   cd /var/www/iredadmin/tools
   ```

3. **Create Admin User**
   ```bash
   sudo bash create_user.sh admin@ailabsafrica.com 'Admin@2024!'
   ```

4. **Create Regular User**
   ```bash
   sudo bash create_user.sh user@ailabsafrica.com 'User@2024!'
   ```

5. **Create System Email (Optional)**
   ```bash
   sudo bash create_user.sh noreply@ailabsafrica.com 'NoReply@2024!'
   ```

6. **Verify Users Created**
   ```bash
   sudo bash list_users.sh ailabsafrica.com
   ```

### Method 3: Direct Database (Advanced)

1. **Access MySQL/MariaDB**
   ```bash
   mysql -u root -p vmail
   ```

2. **Check Existing Users**
   ```sql
   SELECT username, name, quota, storagebasedirectory
   FROM mailbox
   WHERE domain = 'ailabsafrica.com';
   ```

3. **Insert User (Not Recommended - Use tools instead)**
   ```sql
   -- This is complex, use the web interface or CLI tools instead
   ```

---

## Verification

### 1. Check User Exists

**Via Web Interface:**
- Login to https://mail.ailabsafrica.com/iredadmin
- Navigate to: Domains → ailabsafrica.com → Users
- Verify users are listed

**Via Command Line:**
```bash
ssh root@mail.ailabsafrica.com
cd /var/www/iredadmin/tools
sudo bash list_users.sh ailabsafrica.com | grep -E "(admin|user)@ailabsafrica.com"
```

### 2. Test Email Login

**Via Webmail:**
1. Navigate to: https://mail.ailabsafrica.com
2. Login with:
   - Username: `admin@ailabsafrica.com`
   - Password: `Admin@2024!`
3. Verify inbox loads

**Via IMAP (with mail client):**
- Server: mail.ailabsafrica.com
- Port: 993 (SSL/TLS)
- Username: admin@ailabsafrica.com
- Password: Admin@2024!

### 3. Send Test Email

```bash
# From mail server
echo "Test email from admin" | mail -s "Test" admin@ailabsafrica.com
echo "Test email from user" | mail -s "Test" user@ailabsafrica.com
```

---

## Configure Supabase SMTP

Once email accounts are created, configure Supabase to send emails:

1. **Access Supabase Dashboard**
   - Navigate to: https://supabase.ailabsafrica.com/project/_/auth/email-templates

2. **Configure SMTP Settings**
   - SMTP Host: `mail.ailabsafrica.com`
   - SMTP Port: `587` (STARTTLS) or `465` (SSL)
   - SMTP User: `noreply@ailabsafrica.com`
   - SMTP Password: `NoReply@2024!`
   - Sender Email: `noreply@ailabsafrica.com`
   - Sender Name: `KasaAI`

3. **Test Email Sending**
   - Send test email from Supabase dashboard
   - Verify email received at admin@ailabsafrica.com

---

## Email Aliases (Optional)

Create aliases for better organization:

**Via Web Interface:**
1. Navigate to: Domains → ailabsafrica.com → Aliases
2. Create:
   - `support@ailabsafrica.com` → `admin@ailabsafrica.com`
   - `erp@ailabsafrica.com` → `admin@ailabsafrica.com`
   - `no-reply@ailabsafrica.com` → `noreply@ailabsafrica.com`

**Via Command Line:**
```bash
cd /var/www/iredadmin/tools
sudo bash create_alias.sh support@ailabsafrica.com admin@ailabsafrica.com
sudo bash create_alias.sh erp@ailabsafrica.com admin@ailabsafrica.com
```

---

## Troubleshooting

### User Creation Failed

**Error: User already exists**
- Solution: Delete existing user or use different email
- Check: `sudo bash list_users.sh ailabsafrica.com`

**Error: Permission denied**
- Solution: Use sudo with commands
- Check: Logged in as root or have sudo access

**Error: Domain not found**
- Solution: Verify domain exists in iRedMail
- Check: Domains list in admin panel

### Email Not Received

1. **Check mail queue**
   ```bash
   sudo mailq
   ```

2. **Check mail logs**
   ```bash
   sudo tail -f /var/log/mail.log | grep -E "(admin|user)@ailabsafrica.com"
   ```

3. **Verify user quota**
   ```bash
   # Login to webmail
   # Check if quota is full
   ```

4. **Check spam folder**
   - Emails might be marked as spam

### SMTP Connection Failed

1. **Test SMTP connection**
   ```bash
   telnet mail.ailabsafrica.com 587
   # or
   openssl s_client -connect mail.ailabsafrica.com:465 -crlf
   ```

2. **Check firewall**
   ```bash
   sudo ufw status | grep -E "(587|465|993|143)"
   ```

3. **Check iRedMail service**
   ```bash
   sudo systemctl status postfix
   sudo systemctl status dovecot
   ```

---

## Security Best Practices

### Development
- ✅ Use test passwords
- ✅ Limited quotas for test accounts
- ✅ Monitor for abuse

### Production
- ⚠️ Change all default passwords
- ⚠️ Use strong passwords (16+ characters)
- ⚠️ Enable 2FA if available
- ⚠️ Set appropriate quotas
- ⚠️ Monitor login attempts
- ⚠️ Regular password rotation
- ⚠️ Disable unused accounts

---

## Maintenance

### Password Reset

**Via Web Interface:**
1. Login to iRedMail admin
2. Navigate to user
3. Click "Edit"
4. Set new password

**Via Command Line:**
```bash
cd /var/www/iredadmin/tools
sudo bash reset_password.sh admin@ailabsafrica.com 'NewPassword123!'
```

### Delete User

```bash
cd /var/www/iredadmin/tools
sudo bash delete_user.sh user@ailabsafrica.com
```

### Change Quota

**Via Web Interface:**
1. Edit user
2. Change quota value
3. Save

---

## Integration Checklist

- [ ] Create admin@ailabsafrica.com
- [ ] Create user@ailabsafrica.com
- [ ] Create noreply@ailabsafrica.com (optional)
- [ ] Test login to webmail for each account
- [ ] Send test emails between accounts
- [ ] Configure Supabase SMTP settings
- [ ] Test Supabase email sending
- [ ] Set up email aliases (optional)
- [ ] Document passwords securely
- [ ] Configure email forwarding (optional)

---

## Quick Reference

### Mail Server Details
- **Server**: mail.ailabsafrica.com
- **Admin Panel**: https://mail.ailabsafrica.com/iredadmin
- **Webmail**: https://mail.ailabsafrica.com
- **IMAP**: 993 (SSL/TLS)
- **SMTP**: 587 (STARTTLS), 465 (SSL)
- **POP3**: 995 (SSL/TLS)

### Default Accounts
| Email | Password | Purpose | Quota |
|-------|----------|---------|-------|
| admin@ailabsafrica.com | Admin@2024! | Universal Admin | 1024 MB |
| user@ailabsafrica.com | User@2024! | Regular User | 512 MB |
| noreply@ailabsafrica.com | NoReply@2024! | System Emails | 256 MB |

---

**Setup Complete! 📧**

Next steps:
1. Test all email accounts
2. Configure Supabase SMTP
3. Test password reset flow
4. Monitor email delivery
