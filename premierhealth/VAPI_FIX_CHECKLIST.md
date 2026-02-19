# VAPI Webhook URL Fix - Quick Checklist

## The Fix (One-Line Summary)
Change webhook URL from `/vapi/webhooks/premier-health` to `/premier-health/vapi-webhook` in all 7 VAPI assistants.

## Quick Steps

### 1. Login to VAPI Dashboard
- [ ] Go to https://vapi.ai and login

### 2. Update Each Assistant
For **each** of the 7 assistants below, update the webhook URL:

- [ ] **Greater Accra Assistant**
  - Current: `https://api.ailabsafrica.com/vapi/webhooks/premier-health`
  - Change to: `https://api.ailabsafrica.com/premier-health/vapi-webhook`
  - Save ✓

- [ ] **Ashanti Assistant**
  - Current: `https://api.ailabsafrica.com/vapi/webhooks/premier-health`
  - Change to: `https://api.ailabsafrica.com/premier-health/vapi-webhook`
  - Save ✓

- [ ] **Western & Central Assistant**
  - Current: `https://api.ailabsafrica.com/vapi/webhooks/premier-health`
  - Change to: `https://api.ailabsafrica.com/premier-health/vapi-webhook`
  - Save ✓

- [ ] **Eastern & Volta Assistant**
  - Current: `https://api.ailabsafrica.com/vapi/webhooks/premier-health`
  - Change to: `https://api.ailabsafrica.com/premier-health/vapi-webhook`
  - Save ✓

- [ ] **Northern Regions Assistant**
  - Current: `https://api.ailabsafrica.com/vapi/webhooks/premier-health`
  - Change to: `https://api.ailabsafrica.com/premier-health/vapi-webhook`
  - Save ✓

- [ ] **Bono Regions Assistant**
  - Current: `https://api.ailabsafrica.com/vapi/webhooks/premier-health`
  - Change to: `https://api.ailabsafrica.com/premier-health/vapi-webhook`
  - Save ✓

- [ ] **Bono/Bono East/Ahafo Assistant**
  - Current: `https://api.ailabsafrica.com/vapi/webhooks/premier-health`
  - Change to: `https://api.ailabsafrica.com/premier-health/vapi-webhook`
  - Save ✓

### 3. Test
- [ ] Call any assistant and ask: "I need a doctor in Madina"
- [ ] Verify you get provider names (not "cannot find providers")

### 4. Verify Backend Logs (Optional)
```bash
sudo journalctl -u kasaai-core-backend -f | grep "KNOWLEDGE BASE QUERY"
```
- [ ] See RAG query logs appearing when you make a call

## Copy-Paste URL
```
https://api.ailabsafrica.com/premier-health/vapi-webhook
```

## Done! ✅
Once all checkboxes are complete, the issue is resolved.
