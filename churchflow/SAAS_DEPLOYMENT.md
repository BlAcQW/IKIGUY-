# ChurchFlow SaaS Multi-Church Deployment Guide

## Overview

This guide covers deploying the Phase 5 SaaS Multi-Church infrastructure for ChurchFlow, including billing, onboarding, and platform administration.

## Prerequisites

- Stripe account (test and production)
- Access to production/dev servers
- Supabase authentication configured
- MongoDB database running

## 1. Stripe Setup

### Create Stripe Products

1. **Go to Stripe Dashboard**: https://dashboard.stripe.com/test/products
2. **Create Standard Plan**:
   - Name: "ChurchFlow Standard"
   - Price: $49/month
   - Recurring billing
   - Copy the Price ID (e.g., `price_1234567890`)
3. **Create Premium Plan**:
   - Name: "ChurchFlow Premium"
   - Price: $99/month
   - Recurring billing
   - Copy the Price ID (e.g., `price_9876543210`)

### Configure Webhook Endpoint

1. **Go to Webhooks**: https://dashboard.stripe.com/test/webhooks
2. **Add endpoint**:
   - URL: `https://churchflow-api.ailabsafrica.com/api/v1/billing/webhooks/stripe`
   - Events to send:
     - `invoice.payment_succeeded`
     - `invoice.payment_failed`
     - `customer.subscription.updated`
     - `customer.subscription.deleted`
     - `customer.subscription.trial_will_end`
3. **Copy webhook signing secret** (e.g., `whsec_...`)

## 2. Backend Configuration

### Update Environment Variables

Add to `/opt/kasaai/.env`:

```bash
# Stripe Configuration
STRIPE_SECRET_KEY="sk_test_your_actual_key_here"
STRIPE_PUBLISHABLE_KEY="pk_test_your_actual_key_here"
STRIPE_WEBHOOK_SECRET="whsec_your_actual_secret_here"
STRIPE_ENVIRONMENT="sandbox"  # Change to "live" for production

# Stripe Price IDs (from step 1)
STRIPE_PRICE_STANDARD="price_1234567890"  # Replace with actual ID
STRIPE_PRICE_PREMIUM="price_9876543210"   # Replace with actual ID
```

### Update Subscription Model

Edit `backend/app/models/subscription.py` line 179-182:

```python
STRIPE_PRICE_IDS = {
    SubscriptionPlan.STANDARD: "price_1234567890",  # Your actual Standard price ID
    SubscriptionPlan.PREMIUM: "price_9876543210",    # Your actual Premium price ID
}
```

### Restart Backend Service

```bash
sudo systemctl restart kasaai-churchflow-backend
sudo journalctl -u kasaai-churchflow-backend -f  # Check logs
```

## 3. Frontend Configuration

### Update Environment Variables

Edit `/opt/kasaai/apps/churchflow/frontend/.env`:

```bash
VITE_API_URL=https://churchflow-api.ailabsafrica.com
VITE_SUPABASE_URL=https://supabase.ailabsafrica.com
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key_here
VITE_STRIPE_PUBLISHABLE_KEY=pk_test_your_actual_key_here  # Same as backend
```

### Build and Deploy Frontend

```bash
cd /opt/kasaai/apps/churchflow/frontend
npm install
npm run build

# Deploy dist/ folder to nginx serving directory
# Already configured at churchflow.ailabsafrica.com
```

## 4. Database Initialization

The subscription data will be stored in MongoDB:

- Database: `churchflow`
- Collections:
  - `subscriptions` - Subscription records
  - `usage_metrics` - Usage tracking per organization
  - `billing_events` - Audit log for billing events

No manual initialization needed - collections will be created automatically.

## 5. Testing the Implementation

### Test Signup Flow

1. **Navigate to**: https://churchflow.ailabsafrica.com/signup
2. **Complete all 5 steps**:
   - Step 1: Church information
   - Step 2: Admin account
   - Step 3: Phone verification (use test number)
   - Step 4: Plan selection
   - Step 5: Payment (use Stripe test card: `4242 4242 4242 4242`)
3. **Verify**:
   - Organization created in MongoDB
   - Subscription created with trial status
   - Stripe customer and subscription created

### Test Billing Dashboard

1. **Login to ChurchFlow**
2. **Navigate to**: /admin/billing
3. **Verify displays**:
   - Current plan
   - Usage metrics
   - Upgrade/downgrade options

### Test Platform Admin Dashboard

1. **Login as universal admin** (`admin@ailabsafrica.com`)
2. **Navigate to**: /admin/platform
3. **Verify displays**:
   - Total churches
   - MRR/ARR metrics
   - Church list with filters
   - Revenue analytics

### Test Stripe Webhooks

1. **Trigger test webhook** in Stripe Dashboard
2. **Check backend logs**:
   ```bash
   sudo journalctl -u kasaai-churchflow-backend -n 100 | grep webhook
   ```
3. **Verify**: Subscription status updated in database

## 6. Universal Admin Configuration

To grant platform admin access:

1. **Edit**: `apps/shared/services/organization_service.py`
2. **Add email to universal admins list** (line ~50):
   ```python
   UNIVERSAL_ADMINS = [
       "admin@ailabsafrica.com",
       "youremail@domain.com",  # Add your email
   ]
   ```
3. **Restart backend**

## 7. Production Checklist

Before going live:

- [ ] Switch Stripe to live keys (`sk_live_...`, `pk_live_...`)
- [ ] Update `STRIPE_ENVIRONMENT="live"` in backend .env
- [ ] Create live Stripe products and update price IDs
- [ ] Configure live Stripe webhook endpoint
- [ ] Update frontend .env with live Stripe publishable key
- [ ] Test complete signup flow with real card
- [ ] Monitor logs for errors
- [ ] Set up Stripe email notifications for failed payments
- [ ] Configure customer portal in Stripe for self-service
- [ ] Enable Stripe tax collection if applicable
- [ ] Set up billing alerts in Stripe

## 8. Monitoring & Maintenance

### Key Metrics to Monitor

- **MRR/ARR**: Track in platform admin dashboard
- **Churn rate**: Monitor canceled subscriptions
- **Failed payments**: Check Stripe dashboard daily
- **Webhook delivery**: Ensure webhooks are processing

### Backend Logs

```bash
# View recent logs
sudo journalctl -u kasaai-churchflow-backend -n 500

# Follow logs in real-time
sudo journalctl -u kasaai-churchflow-backend -f

# Filter for billing-related logs
sudo journalctl -u kasaai-churchflow-backend | grep -i "subscription\|billing\|stripe"
```

### Database Queries

```bash
# Connect to MongoDB
mongosh -u admin -p 'aawwER4444%' --authenticationDatabase admin

# Switch to ChurchFlow database
use churchflow

# Check subscription counts
db.subscriptions.countDocuments({ status: "active" })
db.subscriptions.countDocuments({ plan: "standard" })
db.subscriptions.countDocuments({ plan: "premium" })

# View recent subscriptions
db.subscriptions.find().sort({ created_at: -1 }).limit(10).pretty()

# Check usage metrics
db.usage_metrics.find().sort({ updated_at: -1 }).limit(5).pretty()
```

## 9. Troubleshooting

### Issue: Webhook not receiving events

**Solution**:
1. Check webhook endpoint URL is correct in Stripe
2. Verify webhook secret matches in backend .env
3. Check backend logs for webhook errors
4. Test webhook in Stripe dashboard

### Issue: Payment setup fails

**Solution**:
1. Verify Stripe publishable key in frontend .env
2. Check browser console for errors
3. Verify backend /billing/setup-intent endpoint works
4. Check CORS configuration allows Stripe

### Issue: Platform admin dashboard shows 403 Forbidden

**Solution**:
1. Verify user email is in UNIVERSAL_ADMINS list
2. Check backend logs for authorization errors
3. Verify JWT token is valid and not expired

## 10. Support & Resources

- **Stripe Documentation**: https://stripe.com/docs
- **Stripe Test Cards**: https://stripe.com/docs/testing
- **Backend Logs**: `sudo journalctl -u kasaai-churchflow-backend -f`
- **Frontend Build**: `cd frontend && npm run build`

## API Endpoints Summary

### Public Endpoints
- `POST /api/v1/onboarding/signup` - Church registration
- `POST /api/v1/onboarding/verify-phone` - Phone verification
- `POST /api/v1/billing/webhooks/stripe` - Stripe webhook handler

### Protected Endpoints (Organization Admin)
- `POST /api/v1/billing/subscriptions` - Create subscription
- `GET /api/v1/billing/subscriptions/{org_id}` - Get subscription
- `PATCH /api/v1/billing/subscriptions/{org_id}/plan` - Update plan
- `POST /api/v1/billing/subscriptions/{org_id}/cancel` - Cancel subscription
- `GET /api/v1/billing/usage/{org_id}` - Get usage metrics
- `POST /api/v1/billing/setup-intent/{org_id}` - Create payment setup

### Protected Endpoints (Platform Admin)
- `GET /api/v1/platform-admin/dashboard` - Platform overview
- `GET /api/v1/platform-admin/churches` - List all churches
- `GET /api/v1/platform-admin/revenue` - Revenue metrics
- `GET /api/v1/platform-admin/usage` - Usage metrics

## Frontend Routes

### Public Routes
- `/signup` - Church registration wizard
- `/login` - Login page

### Protected Routes (Organization Admin)
- `/admin/billing` - Subscription & billing management

### Protected Routes (Platform Admin)
- `/admin/platform` - Platform admin dashboard

---

**Deployment Date**: March 2025
**Phase**: Phase 5 - SaaS Multi-Church
**Version**: 1.0.0
