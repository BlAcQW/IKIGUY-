# Email Service Alternatives

## Current Setup Status

You have **TWO email services already configured**:

1. **Postfix + Gmail SMTP** (Primary - needs app password)
2. **Resend API** (Fallback - already has API key)

## Option 1: Use Resend API (Recommended - Already Configured!)

### Why Resend?

- ✅ **Already configured** - API key in .env
- ✅ **Free tier**: 3,000 emails/month
- ✅ **Better deliverability** than Gmail
- ✅ **No 2FA required**
- ✅ **Professional service**
- ✅ **Email analytics**

### Quick Switch to Resend

Simply disable Postfix and use Resend as primary:

```bash
cd /opt/kasaai/apps/core_backend
/opt/kasaai/apps/venv/bin/python scripts/switch_to_resend.py
```

Or manually by setting in .env:
```ini
# Disable Postfix by commenting out
# SMTP_SERVER=localhost
# SMTP_PORT=25

# Resend API (already configured)
RESEND_API=re_3CKHxpwj_Jk9DmyqvF8nBDQbNWa2Lz6oB
PRIMARY_EMAIL_SERVICE=resend
```

### Test Resend

```bash
cd /opt/kasaai/apps/core_backend
/opt/kasaai/apps/venv/bin/python scripts/test_resend_email.py
```

---

## Option 2: SendGrid (Free Tier Alternative)

### Setup SendGrid

1. **Create Account**: https://signup.sendgrid.com/
2. **Generate API Key**:
   - Go to Settings → API Keys
   - Create API Key with "Mail Send" permission
   - Copy the key

3. **Configure in .env**:
   ```ini
   SENDGRID_API_KEY=SG.your-api-key-here
   SENDER_EMAIL=noreply@ailabsafrica.com
   ```

4. **Install SDK**:
   ```bash
   /opt/kasaai/apps/venv/bin/pip install sendgrid
   ```

5. **Test**:
   ```bash
   /opt/kasaai/apps/venv/bin/python scripts/test_sendgrid_email.py
   ```

---

## Option 3: Amazon SES

### Setup Amazon SES

1. **Create AWS Account**: https://aws.amazon.com/
2. **Verify Email Address**:
   - Go to SES Console → Verified Identities
   - Add `noreply@ailabsafrica.com`
   - Verify via email

3. **Get SMTP Credentials**:
   - Go to SMTP Settings
   - Create SMTP credentials
   - Note: Server, Port, Username, Password

4. **Configure in .env**:
   ```ini
   AWS_SES_SMTP_SERVER=email-smtp.us-east-1.amazonaws.com
   AWS_SES_SMTP_PORT=587
   AWS_SES_USERNAME=your-smtp-username
   AWS_SES_PASSWORD=your-smtp-password
   SENDER_EMAIL=noreply@ailabsafrica.com
   ```

5. **Update Postfix** (or use direct SMTP):
   ```bash
   sudo postconf -e "relayhost = [email-smtp.us-east-1.amazonaws.com]:587"
   # Update SASL password file with AWS credentials
   ```

---

## Option 4: Mailgun

### Setup Mailgun

1. **Create Account**: https://signup.mailgun.com/
2. **Verify Domain** (optional for testing, use sandbox)
3. **Get API Key**: Settings → API Keys
4. **Configure**:
   ```ini
   MAILGUN_API_KEY=your-api-key
   MAILGUN_DOMAIN=sandbox123.mailgun.org
   SENDER_EMAIL=noreply@sandbox123.mailgun.org
   ```

---

## Comparison Table

| Service | Free Tier | Setup Time | Deliverability | Status |
|---------|-----------|------------|----------------|---------|
| **Resend** | 3,000/month | ✅ Done | ⭐⭐⭐⭐⭐ | **Already configured!** |
| Gmail SMTP | ~500/day | 5 min | ⭐⭐⭐⭐ | Needs app password |
| SendGrid | 100/day | 10 min | ⭐⭐⭐⭐⭐ | Not configured |
| Amazon SES | 62,000/month* | 15 min | ⭐⭐⭐⭐⭐ | Not configured |
| Mailgun | 5,000/month | 10 min | ⭐⭐⭐⭐⭐ | Not configured |

*First 12 months on AWS Free Tier, then $0.10/1,000 emails

---

## My Recommendation

### 🥇 **Best Choice: Resend API**

Why? Because it's **already configured** and requires zero additional setup!

**Action Plan**:
1. Verify Resend API key is active
2. Test Resend email sending
3. Disable Postfix/Gmail requirement
4. Update call_management.py to use Resend as primary

### 🥈 **Alternative: Gmail SMTP**

If you prefer free and don't mind the app password:
1. Get Gmail app password (2 minutes)
2. Configure Postfix (10 seconds)
3. Test delivery

### 🥉 **Long-term: Amazon SES**

If you expect high volume (>3,000 emails/month):
1. Set up AWS account
2. Verify email/domain
3. Configure SES SMTP

---

## How to Switch to Resend Right Now

Since Resend is already configured, you can test it immediately:

```python
# Test Resend API
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

async def test_resend():
    resend_api_key = os.getenv("RESEND_API")

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {resend_api_key}",
                "Content-Type": "application/json"
            },
            json={
                "from": "KasaAI <noreply@ailabsafrica.com>",
                "to": ["ailabsafrica@gmail.com"],
                "subject": "Test Email via Resend",
                "html": "<h1>It works!</h1><p>Email sent via Resend API</p>"
            }
        )

    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")

# Run test
import asyncio
asyncio.run(test_resend())
```

---

## Need Help Choosing?

Answer these questions:

1. **How many emails per month?**
   - <100: Gmail or Resend free tier
   - 100-3,000: Resend free tier
   - >3,000: SendGrid, SES, or Resend paid

2. **How quickly do you need it working?**
   - Right now: **Use Resend** (already configured)
   - 5 minutes: Gmail SMTP
   - 10-15 minutes: SendGrid, SES

3. **What's your budget?**
   - $0: Gmail, Resend free tier, SendGrid free tier
   - <$10/month: Resend, SendGrid
   - >$10/month: SES (very high volume)

4. **Do you need analytics?**
   - Yes: Resend, SendGrid, SES
   - No: Gmail SMTP

**My vote: Resend API** - it's already configured and just needs testing! 🚀
