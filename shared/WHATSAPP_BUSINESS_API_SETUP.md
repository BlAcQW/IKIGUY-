# WhatsApp Business API Setup Guide

**Complete step-by-step guide to get your WhatsApp Business API credentials**

## Overview

To use WhatsApp campaigns, you need:
1. **WhatsApp Business Account** - Free to create
2. **Phone Number** - A verified business phone number
3. **Access Token** - Permanent access token for API calls
4. **Phone Number ID** - Unique identifier for your WhatsApp number
5. **Business Account ID** - Your WhatsApp Business Account ID

## Step 1: Create Meta (Facebook) Developer Account

### 1.1 Sign Up
1. Go to https://developers.facebook.com/
2. Click **"Get Started"** (top right)
3. Log in with your Facebook account (or create one)
4. Complete the registration process
5. Verify your email address

### 1.2 Create an App
1. Go to https://developers.facebook.com/apps
2. Click **"Create App"**
3. Select **"Business"** as the app type
4. Click **"Next"**
5. Fill in app details:
   - **App Name**: e.g., "KasaAI Campaigns"
   - **App Contact Email**: Your business email
   - **Business Account**: Create new or select existing
6. Click **"Create App"**

## Step 2: Add WhatsApp Product

### 2.1 Add WhatsApp to Your App
1. In your app dashboard, scroll to **"Add Products to Your App"**
2. Find **"WhatsApp"** and click **"Set Up"**
3. This will take you to the WhatsApp setup page

### 2.2 Quick Start
1. You'll see the **WhatsApp Quick Start** guide
2. You'll be given a **test phone number** (5 phone numbers, 250 messages free)
3. Note down the provided credentials:
   - **Phone Number ID**
   - **WhatsApp Business Account ID**

## Step 3: Get Access Token (Temporary)

### 3.1 Get Temporary Token
1. In the WhatsApp setup page, you'll see a **temporary access token**
2. This token expires in 24 hours (good for testing only)
3. Copy this token for initial testing

**Example Temporary Token:**
```
EAAJcB3ZCxyz...ABC123 (expires in 24 hours)
```

## Step 4: Get Permanent Access Token

### 4.1 Create System User (Recommended)
1. Go to https://business.facebook.com/settings
2. Click **"Business Settings"** (left sidebar)
3. Under **"Users"**, click **"System Users"**
4. Click **"Add"** to create a system user
5. Fill in details:
   - **Name**: e.g., "KasaAI WhatsApp Bot"
   - **Role**: Admin
6. Click **"Create System User"**

### 4.2 Generate Permanent Token
1. Click on the system user you just created
2. Click **"Generate New Token"**
3. Select your WhatsApp app from the dropdown
4. Select permissions (check ALL WhatsApp permissions):
   - `whatsapp_business_management`
   - `whatsapp_business_messaging`
5. Click **"Generate Token"**
6. **IMPORTANT**: Copy and save this token securely - you won't see it again!

**Example Permanent Token:**
```
EAAJcB3ZCxyz...PERMANENT_TOKEN_HERE
```

### 4.3 Alternative: Use App Settings Token (Simpler but less secure)
1. Go to your app dashboard
2. Click **"WhatsApp"** → **"API Setup"**
3. Under **"Temporary access token"**, click **"Generate permanent token"**
4. Follow the prompts to create a permanent token

## Step 5: Add a Phone Number (Production)

### 5.1 Verify Your Business
1. Go to https://business.facebook.com/
2. Complete business verification:
   - Business name
   - Business address
   - Business documents (registration, tax ID, etc.)
3. Wait for verification (can take 1-3 business days)

### 5.2 Add Your Phone Number
1. In WhatsApp API Setup, click **"Add Phone Number"**
2. Choose one of these options:
   - **Use your own number**: Port existing number
   - **Get a new number**: Buy from a provider (e.g., Twilio, Vonage)
3. Follow the verification process:
   - Enter phone number
   - Receive verification code (SMS or call)
   - Enter code to verify
4. Set up two-factor authentication (2FA) for security

**Important Phone Number Requirements:**
- Must be a business phone number (not personal)
- Cannot be registered with regular WhatsApp app
- Must have SMS/voice capability for verification
- Recommended: Use a cloud phone number provider

## Step 6: Create Message Templates

WhatsApp requires pre-approved templates for business-initiated messages.

### 6.1 Access Template Manager
1. Go to WhatsApp Manager: https://business.facebook.com/wa/manage/message-templates/
2. Or: App Dashboard → WhatsApp → Message Templates

### 6.2 Create a Template
1. Click **"Create Template"**
2. Fill in template details:
   - **Template Name**: e.g., `event_reminder` (lowercase, underscores only)
   - **Category**: Select appropriate category
     - `MARKETING` - Promotions, offers
     - `UTILITY` - Account updates, reminders
     - `AUTHENTICATION` - OTP, verification codes
   - **Language**: Select language (e.g., English)

### 6.3 Design Template Content
1. **Header** (Optional):
   - Text, Image, Video, or Document
   - Example: "Upcoming Event"

2. **Body** (Required):
   - Your message text
   - Use variables: {{1}}, {{2}}, {{3}}
   - Example: "Hi {{1}}, your appointment is on {{2}} at {{3}}."

3. **Footer** (Optional):
   - Small text at bottom
   - Example: "Reply STOP to unsubscribe"

4. **Buttons** (Optional):
   - Quick Reply buttons
   - Call to Action (URL, Phone)
   - Example: "Confirm" | "Cancel"

### 6.4 Submit for Approval
1. Review your template
2. Click **"Submit"**
3. Wait for approval (usually 10 minutes - 24 hours)
4. Check status: PENDING → APPROVED/REJECTED

**Template Example:**
```
Template Name: event_reminder
Category: UTILITY
Language: English

Body:
Hi {{1}}, reminder that {{2}} is happening on {{3}} at {{4}}.
See you there!

Footer:
Powered by KasaAI

Buttons:
- [Quick Reply] Confirm
- [Quick Reply] Cancel
```

## Step 7: Configure Webhooks

Webhooks receive delivery status updates and incoming messages.

### 7.1 Set Webhook URL
1. In App Dashboard → WhatsApp → Configuration
2. Under **"Webhooks"**, click **"Configure Webhooks"**
3. Enter your webhook URLs:
   - **Callback URL**: `https://api.ailabsafrica.com/api/whatsapp-campaigns/webhooks/status`
   - **Verify Token**: Create a secure random string (e.g., `whatsapp_webhook_verify_12345`)
4. Click **"Verify and Save"**

### 7.2 Subscribe to Events
1. Under **"Webhook Fields"**, select:
   - ✅ `messages` - Incoming messages
   - ✅ `message_status` - Delivery status updates
2. Click **"Subscribe"**

### 7.3 Test Webhook
1. Send a test message using the API
2. Check your backend logs for webhook events
3. Verify you receive status updates (sent, delivered, read, failed)

## Step 8: Configure Environment Variables

### 8.1 Backend Environment Variables
Add these to your `.env` file or environment:

```bash
# WhatsApp Business API Credentials
WHATSAPP_ACCESS_TOKEN=EAAJcB3ZCxyz...YOUR_PERMANENT_TOKEN
WHATSAPP_PHONE_NUMBER_ID=102290129340398
WHATSAPP_BUSINESS_ACCOUNT_ID=109123...789
WHATSAPP_VERIFY_TOKEN=whatsapp_webhook_verify_12345
WHATSAPP_WEBHOOK_SECRET=your_webhook_secret_key_here

# Optional: Cost Configuration
WHATSAPP_COST_PER_MESSAGE=0.0055  # $0.0055 USD per message
WHATSAPP_COST_PER_MEDIA=0.0100     # $0.01 USD for media messages
```

### 8.2 How to Find Your IDs

**Phone Number ID:**
1. WhatsApp API Setup → From Phone Number
2. Click on your phone number
3. Copy **"Phone number ID"**

**Business Account ID:**
1. WhatsApp API Setup → top of page
2. Look for **"WhatsApp Business Account ID"**

**Access Token:**
- Copy from System User token generation
- Or from API Setup page (temporary)

## Step 9: Test Your Setup

### 9.1 Send Test Message via API
```bash
curl -X POST "https://graph.facebook.com/v17.0/YOUR_PHONE_NUMBER_ID/messages" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "messaging_product": "whatsapp",
    "to": "+1234567890",
    "type": "template",
    "template": {
      "name": "hello_world",
      "language": {
        "code": "en_US"
      }
    }
  }'
```

### 9.2 Expected Response
```json
{
  "messaging_product": "whatsapp",
  "contacts": [
    {
      "input": "+1234567890",
      "wa_id": "1234567890"
    }
  ],
  "messages": [
    {
      "id": "wamid.HBgNMTIzNDU2Nzg5MAA..."
    }
  ]
}
```

### 9.3 Verify in KasaAI
1. Log into KasaAI B2C Portal
2. Go to **"WhatsApp Campaigns"**
3. Click **"Sync Templates"** - should see your approved templates
4. Create a test campaign
5. Verify you can select your templates
6. Send to 1-2 test numbers

## Step 10: Production Checklist

Before going to production, ensure:

### API Configuration
- [ ] Permanent access token configured
- [ ] Phone number verified and active
- [ ] All required templates approved
- [ ] Webhooks configured and tested
- [ ] Environment variables set in production

### Business Verification
- [ ] Business verified by Meta
- [ ] Display name approved
- [ ] Business profile complete (logo, description, address)
- [ ] Terms of service and privacy policy URLs set

### Compliance
- [ ] Opt-in mechanism for users (required by WhatsApp)
- [ ] Opt-out instructions in messages (e.g., "Reply STOP")
- [ ] Message frequency disclosed to users
- [ ] Customer data handling compliant with policies

### Technical Setup
- [ ] Rate limiting configured (default: 1 msg/sec, can request increase)
- [ ] Error handling and retry logic tested
- [ ] Monitoring and alerting set up
- [ ] Cost tracking configured
- [ ] Webhook delivery verified

### Message Quality
- [ ] Templates follow WhatsApp policies
- [ ] No prohibited content (spam, misleading, etc.)
- [ ] Messages provide value to recipients
- [ ] Timing appropriate (no night messages)

## Common Issues & Solutions

### Issue 1: "Invalid Access Token"
**Solution**:
- Verify token hasn't expired
- Check token has correct permissions
- Regenerate permanent token if needed

### Issue 2: "Phone Number Not Registered"
**Solution**:
- Complete phone number verification
- Check 2FA is enabled
- Verify phone number ID is correct

### Issue 3: "Template Not Found"
**Solution**:
- Sync templates from API
- Verify template is APPROVED status
- Check template name matches exactly (case-sensitive)

### Issue 4: "Webhook Not Receiving Events"
**Solution**:
- Verify webhook URL is publicly accessible (HTTPS)
- Check verify token matches
- Ensure webhook endpoint returns 200 OK
- Check firewall settings

### Issue 5: "Message Rejected - Policy Violation"
**Solution**:
- Review WhatsApp Commerce Policy
- Ensure opt-in from recipients
- Check message content for prohibited terms
- Don't send promotional content to users who haven't opted in

## Rate Limits

WhatsApp enforces tier-based rate limits:

| Tier | Limit | How to Reach |
|------|-------|--------------|
| Tier 1 | 1,000 unique users/24hr | Default |
| Tier 2 | 10,000 unique users/24hr | Maintain quality, low block rate |
| Tier 3 | 100,000 unique users/24hr | Consistent high quality |
| Unlimited | No limit | Enterprise agreement |

**Tips to Increase Tier:**
- Maintain <50% message quality score
- Keep block rate low (<0.5%)
- Ensure high delivery rates
- Respond to user messages

## Pricing (as of 2024)

**Conversation-Based Pricing:**
- **Marketing**: ~$0.0055 - $0.095 per conversation (varies by country)
- **Utility**: ~$0.0025 - $0.04 per conversation
- **Authentication**: ~$0.005 - $0.04 per conversation
- **Service**: Free (user-initiated within 24hr)

**Free Tier:**
- 1,000 free conversations per month (per phone number)
- Applies to all business-initiated conversations

**Media Costs:**
- Media messages: +$0.01 per message

**Note**: Prices vary by country. Check latest pricing:
https://developers.facebook.com/docs/whatsapp/pricing

## Resources

### Official Documentation
- WhatsApp Business Platform: https://developers.facebook.com/docs/whatsapp
- Cloud API Guide: https://developers.facebook.com/docs/whatsapp/cloud-api
- Message Templates: https://developers.facebook.com/docs/whatsapp/message-templates
- Business Policies: https://www.whatsapp.com/legal/commerce-policy

### Useful Links
- Developer Dashboard: https://developers.facebook.com/apps
- Business Manager: https://business.facebook.com/
- Template Manager: https://business.facebook.com/wa/manage/message-templates/
- API Explorer: https://developers.facebook.com/tools/explorer

### Support
- Developer Community: https://developers.facebook.com/community/
- WhatsApp Business API Support: https://business.whatsapp.com/support

## Quick Reference Card

Save these credentials securely:

```
┌─────────────────────────────────────────────────────┐
│ WhatsApp Business API Credentials                   │
├─────────────────────────────────────────────────────┤
│ Access Token: EAAJcB3ZCxyz...                       │
│ Phone Number ID: 102290129340398                    │
│ Business Account ID: 109123...789                   │
│ Verify Token: whatsapp_webhook_verify_12345         │
│ Webhook URL: https://api.ailabsafrica.com/api/...   │
└─────────────────────────────────────────────────────┘
```

---

**Next Steps After Setup:**
1. Add credentials to `.env` file
2. Restart backend services
3. Test template sync in KasaAI
4. Create your first campaign
5. Monitor delivery and costs

**Need Help?**
- Check troubleshooting section above
- Review WhatsApp documentation
- Test with sandbox/test numbers first
- Contact Meta support for account issues
