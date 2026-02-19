# Affiliate Platform Implementation Plan

## Overview

Multi-level marketing (MLM) / affiliate platform integrated into the KasaAI B2C Portal. Enables users to earn commissions by referring new customers through a 3-tier referral system.

---

## Business Model

### Commission Structure
- **Tier 1 (Direct Referrals):** 15%
- **Tier 2 (Sub-Affiliates):** 8%
- **Tier 3 (Sub-Sub-Affiliates):** 3%
- **Total Max Commission:** 26% per sale

### Example Flow
```
User A (Tier 1) → refers User B
User B (Tier 2) → refers User C
User C (Tier 3) → refers User D

User D purchases $100 credits:
- User C earns $15 (tier 1 from D)
- User B earns $8 (tier 2 from D)
- User A earns $3 (tier 3 from D)
```

---

## Technical Architecture

### Database Schema (MongoDB - kasaai_core)

#### New Collections

**1. affiliate_profiles**
```python
{
    "_id": ObjectId,
    "user_id": str,              # Links to users collection
    "organization_id": str,       # Multi-tenant isolation
    "referral_code": str,         # Unique code (e.g., "ALFRED001")
    "upline_id": Optional[str],   # Parent affiliate user_id
    "tier_level": int,            # How deep in tree (1, 2, or 3)

    # Commission rates (customizable per affiliate)
    "tier1_commission_rate": Decimal(0.15),  # 15%
    "tier2_commission_rate": Decimal(0.08),  # 8%
    "tier3_commission_rate": Decimal(0.03),  # 3%

    # Statistics
    "total_referrals": int,
    "direct_referrals": int,
    "total_sales": Decimal,
    "total_commissions_earned": Decimal,
    "total_commissions_paid": Decimal,
    "pending_commissions": Decimal,

    # Status
    "is_active": bool,
    "is_verified": bool,
    "joined_program_at": datetime,
    "last_referral_at": Optional[datetime],

    # Payout settings
    "payout_method": str,  # "wallet_credit", "momo", "bank_transfer", "paypal"
    "payout_threshold": Decimal(20.00),  # Minimum $20
    "payment_method_id": Optional[str],

    # Metadata
    "created_at": datetime,
    "updated_at": datetime
}
```

**2. referral_links**
```python
{
    "_id": ObjectId,
    "affiliate_id": str,
    "organization_id": str,
    "referral_code": str,
    "utm_source": Optional[str],
    "utm_campaign": Optional[str],
    "click_count": int,
    "conversion_count": int,
    "last_clicked_at": Optional[datetime],
    "created_at": datetime
}
```

**3. referral_attributions**
```python
{
    "_id": ObjectId,
    "referred_user_id": str,      # New user who signed up
    "affiliate_id": str,           # Who gets credit
    "organization_id": str,
    "referral_code": str,
    "attribution_method": str,     # "cookie", "url_param", "manual"
    "cookie_id": Optional[str],
    "ip_address": Optional[str],
    "user_agent": Optional[str],
    "clicked_at": datetime,
    "signed_up_at": Optional[datetime],
    "first_purchase_at": Optional[datetime],
    "created_at": datetime
}
```

**4. commission_records**
```python
{
    "_id": ObjectId,
    "affiliate_id": str,           # Who earns commission
    "organization_id": str,
    "referred_user_id": str,       # Who made purchase
    "transaction_id": str,         # Links to transactions collection

    # Commission details
    "sale_amount": Decimal,
    "commission_rate": Decimal,
    "commission_amount": Decimal,
    "tier_level": int,             # 1, 2, or 3

    # Status
    "status": str,  # "pending", "approved", "paid", "cancelled"
    "approved_at": Optional[datetime],
    "paid_at": Optional[datetime],
    "payout_transaction_id": Optional[str],

    # Metadata
    "created_at": datetime,
    "updated_at": datetime,
    "notes": Optional[str]
}
```

**5. payout_requests**
```python
{
    "_id": ObjectId,
    "affiliate_id": str,
    "organization_id": str,
    "amount": Decimal,
    "payout_method": str,
    "payment_method_id": Optional[str],

    # Status
    "status": str,  # "pending", "processing", "completed", "failed", "cancelled"
    "processed_by": Optional[str],
    "processed_at": Optional[datetime],

    # Transaction reference
    "transaction_id": Optional[str],
    "provider_reference": Optional[str],

    # Metadata
    "created_at": datetime,
    "updated_at": datetime,
    "notes": Optional[str],
    "failure_reason": Optional[str]
}
```

#### Indexes
```python
affiliate_profiles:
  - {"user_id": 1} - unique
  - {"referral_code": 1} - unique
  - {"upline_id": 1}
  - {"organization_id": 1}

referral_links:
  - {"affiliate_id": 1}
  - {"referral_code": 1}
  - {"organization_id": 1}

referral_attributions:
  - {"referred_user_id": 1} - unique
  - {"affiliate_id": 1}
  - {"referral_code": 1}
  - {"organization_id": 1}

commission_records:
  - {"affiliate_id": 1}
  - {"referred_user_id": 1}
  - {"transaction_id": 1}
  - {"status": 1}
  - {"organization_id": 1}

payout_requests:
  - {"affiliate_id": 1}
  - {"status": 1}
  - {"organization_id": 1}
```

---

## API Endpoints

### Router: `/api/affiliates/`

#### Affiliate Profile Management
```
POST   /api/affiliates/join
  Request: { upline_referral_code?: string }
  Response: { affiliate_profile, referral_code }

GET    /api/affiliates/profile
  Response: { affiliate_profile }

PATCH  /api/affiliates/profile
  Request: { payout_method?, payout_threshold?, payment_method_id? }
  Response: { affiliate_profile }

GET    /api/affiliates/stats
  Response: {
    total_referrals, direct_referrals, total_sales,
    total_earned, total_paid, pending_commissions,
    this_month_earnings, conversion_rate
  }
```

#### Referral Links
```
GET    /api/affiliates/referral-links
  Response: [{ referral_code, url, clicks, conversions }]

POST   /api/affiliates/referral-links
  Request: { utm_source?, utm_campaign? }
  Response: { referral_link }

GET    /api/affiliates/referral-code
  Response: { referral_code, base_url }
```

#### Referrals & Network
```
GET    /api/affiliates/referrals?tier={1|2|3}&limit=50&offset=0
  Response: [{
    user_id, name, email, joined_at, tier_level,
    total_purchases, commissions_earned
  }]

GET    /api/affiliates/network
  Response: { tree structure with stats per level }

GET    /api/affiliates/network/stats
  Response: {
    tier1_count, tier2_count, tier3_count,
    total_network_size, total_network_sales
  }
```

#### Commissions
```
GET    /api/affiliates/commissions?status=&limit=50&offset=0
  Response: [{
    id, referred_user, sale_amount, commission_amount,
    tier_level, status, created_at
  }]

GET    /api/affiliates/commissions/summary?start_date=&end_date=
  Response: {
    total_earned, by_tier, by_month
  }

GET    /api/affiliates/commissions/pending
  Response: { pending_amount, pending_count, records }
```

#### Payouts
```
GET    /api/affiliates/payouts?limit=50&offset=0
  Response: [{
    id, amount, payout_method, status, created_at, processed_at
  }]

POST   /api/affiliates/payouts/request
  Request: { amount, payout_method, payment_method_id? }
  Response: { payout_request }

GET    /api/affiliates/payouts/{id}
  Response: { payout_request_details }
```

#### Public/Internal Endpoints
```
GET    /api/public/track-referral?ref={code}
  Sets cookie: kasaai_ref={code}; max-age=2592000
  Response: { success: true }

POST   /api/internal/process-commission
  Request: { transaction_id }
  Response: { commissions_created: [...] }
  (Called internally after successful deposit)
```

---

## Frontend Structure

### New Pages
```
/opt/kasaai/apps/b2c-portal/src/pages/
├── affiliates/
│   ├── AffiliatesDashboard.tsx       # Main dashboard
│   ├── AffiliatesJoin.tsx             # Join program
│   ├── AffiliatesReferrals.tsx        # View referrals
│   ├── AffiliatesCommissions.tsx      # Commission history
│   └── AffiliatesPayouts.tsx          # Payout management
```

### New Components
```
/opt/kasaai/apps/b2c-portal/src/components/affiliates/
├── AffiliateStats.tsx                 # Stats cards
├── ReferralLinkGenerator.tsx          # Generate/copy links
├── NetworkTreeView.tsx                # Visualize network
├── CommissionTable.tsx                # Commission records
├── PayoutRequestForm.tsx              # Request payout
├── ReferralTable.tsx                  # List referrals
└── AffiliateOnboarding.tsx            # Onboarding wizard
```

### Routes
```typescript
// Add to App.tsx
<Route path="/affiliates" element={<AffiliatesDashboard />} />
<Route path="/affiliates/join" element={<AffiliatesJoin />} />
<Route path="/affiliates/referrals" element={<AffiliatesReferrals />} />
<Route path="/affiliates/commissions" element={<AffiliatesCommissions />} />
<Route path="/affiliates/payouts" element={<AffiliatesPayouts />} />
```

---

## Backend Services

### File Structure
```
/opt/kasaai/apps/core_backend/backend/
├── routes/
│   └── affiliates.py                  # API router
├── services/
│   └── affiliate_service.py           # Business logic
├── models/
│   └── affiliate.py                   # Pydantic models
└── schemas/
    └── affiliate.py                   # Request/response schemas
```

### Service Methods
```python
class AffiliateService:
    async def join_program(user_id, upline_code=None)
    async def get_profile(user_id)
    async def update_profile(user_id, updates)
    async def get_stats(user_id)
    async def generate_referral_code(user_id)
    async def track_click(referral_code, request)
    async def attribute_signup(user_id, referral_code)
    async def calculate_commission(transaction_id)
    async def get_referrals(user_id, tier=None)
    async def get_network_tree(user_id)
    async def get_commissions(user_id, filters)
    async def request_payout(user_id, amount, method)
    async def process_payout(payout_id, admin_user_id)
```

---

## Integration Points

### 1. Signup Flow Enhancement
**File:** `b2c-portal/src/components/auth/MongoSignupForm.tsx`
- Add optional "Referral Code" input field
- Check cookie `kasaai_ref` on page load
- Pre-fill if cookie exists
- Pass to signup API

**File:** `core_backend/backend/services/auth_service.py`
- Accept `referral_code` parameter
- Call `affiliate_service.attribute_signup()` after user creation

### 2. Purchase Flow Enhancement
**File:** `core_backend/backend/services/wallet_service.py`
- After successful deposit completion
- Call `affiliate_service.calculate_commission(transaction_id)`
- Creates commission records for tiers 1-3 if user was referred

### 3. Navigation Enhancement
**File:** `b2c-portal/src/components/dashboard/DashboardSidebar.tsx`
- Add "Affiliate" section for enrolled users
- Add "Become an Affiliate" CTA for non-affiliates
- Show earnings badge on affiliate menu item

### 4. Referral Tracking Middleware
**File:** `b2c-portal/src/App.tsx`
- Add useEffect to check URL param `?ref=CODE`
- Set cookie `kasaai_ref` if found
- Call tracking endpoint `/api/public/track-referral`

---

## Cookie Attribution Logic

### Setting Cookie (on link click)
```javascript
// When user lands on site with ?ref=CODE
const urlParams = new URLSearchParams(window.location.search);
const refCode = urlParams.get('ref');

if (refCode) {
  // Set 30-day cookie
  document.cookie = `kasaai_ref=${refCode}; max-age=2592000; path=/; secure; samesite=lax`;

  // Track click
  await fetch(`/api/public/track-referral?ref=${refCode}`);
}
```

### Reading Cookie (on signup)
```javascript
// In MongoSignupForm.tsx
const getReferralCode = () => {
  // Priority 1: URL parameter
  const urlParams = new URLSearchParams(window.location.search);
  const urlRef = urlParams.get('ref');
  if (urlRef) return urlRef;

  // Priority 2: Cookie
  const cookies = document.cookie.split(';');
  const refCookie = cookies.find(c => c.trim().startsWith('kasaai_ref='));
  if (refCookie) {
    return refCookie.split('=')[1];
  }

  return null;
};

// Pre-fill form
useEffect(() => {
  const ref = getReferralCode();
  if (ref) setReferralCode(ref);
}, []);
```

---

## Referral URL Structure

### Standard URLs
```
https://kasaai.ailabsafrica.com?ref=ALFRED001
https://kasaai.ailabsafrica.com/signup?ref=ALFRED001
https://kasaai.ailabsafrica.com/pricing?ref=ALFRED001
```

### With UTM Tracking
```
https://kasaai.ailabsafrica.com?ref=ALFRED001&utm_source=instagram&utm_campaign=q1_2025
```

### Generated Format
```javascript
const generateReferralURL = (code, utmSource?, utmCampaign?) => {
  const base = 'https://kasaai.ailabsafrica.com';
  const params = new URLSearchParams({ ref: code });
  if (utmSource) params.append('utm_source', utmSource);
  if (utmCampaign) params.append('utm_campaign', utmCampaign);
  return `${base}?${params.toString()}`;
};
```

---

## Commission Calculation Algorithm

### Pseudo-code
```python
async def calculate_commission(transaction_id: str):
    """
    Calculate multi-tier commissions for a purchase.
    """
    # 1. Get transaction details
    transaction = await get_transaction(transaction_id)

    # 2. Check if buyer was referred
    attribution = await get_attribution(transaction.user_id)
    if not attribution:
        return []  # No commissions

    # 3. Get affiliate chain (tiers 1-3)
    affiliate_chain = await get_affiliate_chain(attribution.affiliate_id, max_tiers=3)

    # 4. Calculate commissions for each tier
    commissions = []
    for tier, affiliate in enumerate(affiliate_chain, start=1):
        rate = affiliate.get_commission_rate(tier)
        amount = transaction.amount * rate

        commission = await create_commission_record(
            affiliate_id=affiliate.user_id,
            referred_user_id=transaction.user_id,
            transaction_id=transaction_id,
            sale_amount=transaction.amount,
            commission_rate=rate,
            commission_amount=amount,
            tier_level=tier,
            status="approved"  # Auto-approve for now
        )

        # Update affiliate stats
        await update_affiliate_stats(affiliate.user_id, commission_amount=amount)

        commissions.append(commission)

    return commissions
```

### Example Calculation
```
User D purchases $100 credits
User D was referred by User C
User C was referred by User B
User B was referred by User A

Tier 1: User C earns $100 × 0.15 = $15.00
Tier 2: User B earns $100 × 0.08 = $8.00
Tier 3: User A earns $100 × 0.03 = $3.00

Total commissions: $26.00 (26% of sale)
Net revenue: $74.00
```

---

## Payout Processing

### Payout Methods

**1. Wallet Credit (Instant)**
```python
async def payout_to_wallet(payout_request):
    # Add commission to affiliate's wallet
    await wallet_service.create_adjustment(
        user_id=payout_request.affiliate_id,
        amount=payout_request.amount,
        description=f"Affiliate payout - Request #{payout_request.id}",
        transaction_type="adjustment"
    )
```

**2. Mobile Money (MoMo)**
```python
async def payout_to_momo(payout_request):
    # Use existing payment provider integrations
    await momo_provider.send_money(
        phone=affiliate.phone,
        amount=payout_request.amount,
        currency="GHS",
        reference=f"AFFILIATE_{payout_request.id}"
    )
```

**3. Bank Transfer**
```python
async def payout_to_bank(payout_request):
    # Manual processing or bank API integration
    # Create pending transaction, admin approves
    pass
```

**4. PayPal**
```python
async def payout_to_paypal(payout_request):
    # PayPal Payouts API
    await paypal_provider.payout(
        email=affiliate.email,
        amount=payout_request.amount,
        reference=f"AFFILIATE_{payout_request.id}"
    )
```

### Payout Thresholds
- Wallet Credit: No minimum
- Mobile Money: $10 minimum
- Bank Transfer: $50 minimum
- PayPal: $20 minimum

### Processing Fees
- Wallet Credit: $0 (free)
- Mobile Money: 2.5% ($0.25 minimum)
- Bank Transfer: $5 fixed
- PayPal: 2.9% + $0.30

---

## Security & Fraud Prevention

### Anti-Fraud Measures

1. **Email Verification Required**
   - Commissions only eligible after email verification
   - Prevents fake account creation

2. **Purchase-Based Commissions**
   - Commission only on actual purchases
   - Not on signups alone

3. **Device Fingerprinting**
   - Track IP address, user agent
   - Flag suspicious patterns (same IP, multiple accounts)

4. **Manual Review for Large Payouts**
   - Payouts > $500 require admin approval
   - Review network structure for anomalies

5. **Minimum Account Age**
   - Account must be 7+ days old for payout eligibility
   - Prevents quick hit-and-run schemes

6. **Self-Referral Prevention**
   - Cannot refer yourself
   - Cannot refer from same IP/device within 24 hours

7. **Rate Limiting**
   - Max 5 referral link clicks per IP per hour
   - Max 10 signups per referral code per day

---

## Analytics & Reporting

### Affiliate Dashboard Metrics
- Total earnings (all-time, this month, last month)
- Pending commissions
- Total referrals (tier 1, 2, 3)
- Conversion rate (clicks → signups → purchases)
- Top performing referrals
- Earnings trend chart

### Admin Analytics
- Total affiliates count
- Active affiliates (referred someone in last 30 days)
- Total commissions paid
- Revenue from referred users
- ROI of affiliate program
- Top affiliates leaderboard
- Fraud detection alerts

---

## Notifications

### Email Notifications
- Welcome email on joining program
- New referral signup
- Commission earned
- Payout processed
- Payout failed

### In-App Notifications
- Real-time notification on new referral
- Commission approval
- Payout status updates

---

## Testing Strategy

### Unit Tests
- Commission calculation logic
- Referral code generation (uniqueness)
- Affiliate chain retrieval
- Payout processing

### Integration Tests
- Signup with referral code
- Purchase triggers commission
- Payout request flow
- Cookie attribution

### E2E Tests
- Complete affiliate journey (join → refer → earn → payout)
- Multi-tier commission calculation
- Payout request and processing

---

## Deployment Checklist

- [ ] Create MongoDB indexes
- [ ] Deploy backend changes (core_backend)
- [ ] Deploy frontend changes (b2c-portal)
- [ ] Update API documentation
- [ ] Configure email templates
- [ ] Set up monitoring alerts
- [ ] Create admin dashboard for payouts
- [ ] Train support team
- [ ] Prepare marketing materials
- [ ] Beta test with 10-20 affiliates
- [ ] Launch publicly

---

## Success Metrics (KPIs)

### Acquisition
- Active affiliates count
- New affiliates per month
- Affiliate activation rate

### Performance
- Total referred users
- Conversion rate (referred signup → purchase)
- Average order value (referred vs non-referred)

### Financial
- Total commissions paid
- Revenue from referred users
- Cost per acquisition via affiliates
- Affiliate program ROI

### Engagement
- Referral link clicks
- Average referrals per affiliate
- Top 10% performance benchmark

---

## Future Enhancements (Phase 2)

- [ ] Network tree visualization (interactive graph)
- [ ] Leaderboards with rewards
- [ ] Achievement badges and gamification
- [ ] Custom commission rates per affiliate
- [ ] Tiered affiliate levels (Bronze, Silver, Gold, Platinum)
- [ ] Affiliate marketing materials library (banners, templates)
- [ ] Performance analytics (best traffic sources, conversion funnel)
- [ ] Recurring commissions (lifetime value tracking)
- [ ] Sub-affiliate recruitment bonuses
- [ ] White-label affiliate portal option

---

## Support & Documentation

### Affiliate Help Center
- How to join the program
- How to generate referral links
- Commission structure explained
- How to request payouts
- FAQs

### Admin Documentation
- How to approve payouts
- Fraud detection guidelines
- Commission dispute resolution
- Analytics interpretation

---

**Plan Version:** 1.0
**Created:** 2025-11-18
**Status:** Ready for Implementation
