# Multi-Level Marketing (MLM) / Affiliate Platform - Architecture Recommendation

## Executive Summary

After thorough analysis of your existing infrastructure, I recommend **integrating the affiliate/MLM system into the b2c-portal** rather than creating a standalone platform or adding it to the ERP. This recommendation is based on:

1. **B2C Portal** already has complete wallet, payment, and organization infrastructure
2. **ERP** is designed for internal operations, not customer-facing services
3. A **standalone platform** would create unnecessary duplication and complexity
4. The affiliate system is fundamentally a **customer acquisition feature** that belongs in the customer portal

---

## Detailed Analysis

### Option A: Standalone Platform (affiliates.ailabsafrica.com)

#### Pros
- Clean separation of concerns
- Independent scaling
- Dedicated UI/UX for affiliates
- Can have different auth/permission model

#### Cons
- **Duplication of infrastructure** (wallet, payments, user management, organization context)
- **Data synchronization complexity** - must sync with b2c-portal for commissions, users, sales
- **Increased maintenance burden** - separate deployment, monitoring, updates
- **User friction** - affiliates must maintain separate accounts from their customer accounts
- **Development time** - 3-4 weeks to build from scratch
- **No code reuse** - can't leverage existing wallet service, payment integrations, organization context

**Verdict:** ❌ Not recommended - too much duplication

---

### Option B: Integration into ERP (@apps/erp/)

#### Pros
- Already has partnership tracking module (similar domain)
- Has organization management
- Has role-based access control
- MongoDB-based like core_backend

#### Cons
- **Wrong audience** - ERP is for internal business operations, not customer-facing
- **Access control mismatch** - ERP requires organization membership, affiliates are external
- **No wallet infrastructure** - would need to build from scratch
- **No payment integrations** - Stripe, Flutterwave, MoMo not configured
- **Different purpose** - Partnership module is for B2B vendor/technology partners, not customer affiliates
- **Security concerns** - mixing internal business data with external affiliate access
- **User experience confusion** - affiliates shouldn't see HR, Finance, Projects, etc.

**Verdict:** ❌ Not recommended - wrong use case

---

### Option C: Integration into B2C Portal (@apps/b2c-portal/) ✅ RECOMMENDED

#### Pros
1. **Existing Infrastructure Ready**
   - ✅ Wallet system already implemented (`/api/wallet/*`)
   - ✅ Payment methods (Stripe, Flutterwave, MoMo, PayPal, etc.)
   - ✅ Transaction tracking and history
   - ✅ Organization context with multi-tenant isolation
   - ✅ User authentication (MongoDB-based JWT)
   - ✅ Role-based access control
   - ✅ Receipt generation and downloads
   - ✅ Auto-reload and balance alerts

2. **Natural User Flow**
   - Affiliates are also potential customers
   - Single account for both purchasing and earning
   - Seamless transition from customer → affiliate
   - Unified dashboard experience

3. **Data Architecture Perfect Fit**
   - Organization_id already scopes all data
   - User roles can add "AFFILIATE" role
   - Wallet can track both spending and earnings
   - Transaction types already support "transfer" and "adjustment"

4. **Technical Advantages**
   - Reuse existing API endpoints
   - Leverage shared wallet service (`@apps/shared/integration/wallet.py`)
   - Use existing payment provider integrations
   - Minimal new infrastructure needed
   - Can deploy with same backend (core_backend)

5. **Business Logic Alignment**
   - Credit purchases trigger commission calculations
   - Referral tracking naturally integrates with signup flow
   - Cookie-based attribution already possible (add to existing auth flow)
   - Payout processing uses existing transaction system

#### Implementation Complexity
- **Estimated Timeline**: 1-2 weeks (vs 3-4 weeks for standalone)
- **New Components**:
  - Affiliate dashboard page
  - Referral link generator
  - Commission calculation service
  - Sub-affiliate tree view
  - Payout request module
- **Database Changes**:
  - Add affiliate fields to user model
  - Create affiliate_links collection
  - Create commission_records collection
  - Extend transactions to support commission payouts

#### Cons (Minimal)
- Slightly increased complexity in b2c-portal codebase
- Need to add affiliate-specific UI sections (but using existing design system)
- May need to add role-based navigation hiding (non-affiliates shouldn't see affiliate sections)

**Verdict:** ✅ **STRONGLY RECOMMENDED** - Best ROI, fastest to market, lowest risk

---

## Recommended Architecture (B2C Portal Integration)

### 1. Database Schema Extensions

#### New Collections (MongoDB - `kasaai_core` database)

```python
# Collection: affiliate_profiles
{
    "_id": ObjectId,
    "user_id": str,  # Links to existing users collection
    "organization_id": str,  # Multi-tenant isolation
    "referral_code": str,  # Unique code (e.g., "ALFRED001")
    "upline_id": Optional[str],  # Parent affiliate user_id
    "tier_level": int,  # 1, 2, or 3 (how deep in the tree)

    # Commission rates
    "tier1_commission_rate": Decimal,  # e.g., 0.15 (15%)
    "tier2_commission_rate": Decimal,  # e.g., 0.08 (8%)
    "tier3_commission_rate": Decimal,  # e.g., 0.03 (3%)

    # Statistics
    "total_referrals": int,
    "direct_referrals": int,  # Tier 1 only
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
    "payout_threshold": Decimal,  # Min amount before payout
    "payment_method_id": Optional[str],  # For automated payouts

    # Metadata
    "created_at": datetime,
    "updated_at": datetime,
    "custom_fields": dict
}

# Collection: referral_links
{
    "_id": ObjectId,
    "affiliate_id": str,  # User ID of affiliate
    "organization_id": str,
    "referral_code": str,  # The unique code
    "utm_source": str,  # For analytics
    "utm_campaign": Optional[str],
    "click_count": int,
    "conversion_count": int,
    "last_clicked_at": Optional[datetime],
    "created_at": datetime
}

# Collection: referral_attributions
{
    "_id": ObjectId,
    "referred_user_id": str,  # New user who signed up
    "affiliate_id": str,  # Who gets credit
    "organization_id": str,
    "referral_code": str,
    "attribution_method": str,  # "cookie", "url_param", "manual"
    "cookie_id": Optional[str],
    "ip_address": Optional[str],
    "user_agent": Optional[str],
    "clicked_at": datetime,
    "signed_up_at": Optional[datetime],
    "first_purchase_at": Optional[datetime],
    "created_at": datetime
}

# Collection: commission_records
{
    "_id": ObjectId,
    "affiliate_id": str,  # Who earns the commission
    "organization_id": str,
    "referred_user_id": str,  # Who made the purchase
    "transaction_id": str,  # Links to existing transactions collection

    # Commission details
    "sale_amount": Decimal,  # Original purchase amount
    "commission_rate": Decimal,
    "commission_amount": Decimal,
    "tier_level": int,  # 1, 2, or 3

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

# Collection: payout_requests
{
    "_id": ObjectId,
    "affiliate_id": str,
    "organization_id": str,
    "amount": Decimal,
    "payout_method": str,  # "wallet_credit", "momo", "bank_transfer", "paypal"
    "payment_method_id": Optional[str],

    # Status tracking
    "status": str,  # "pending", "processing", "completed", "failed", "cancelled"
    "processed_by": Optional[str],  # Admin user_id who processed
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

---

### 2. API Endpoints (Add to core_backend)

```python
# New router: /opt/kasaai/apps/core_backend/backend/routes/affiliates.py

# Affiliate Profile Management
POST   /api/affiliates/join                    # Join affiliate program
GET    /api/affiliates/profile                 # Get affiliate profile
PATCH  /api/affiliates/profile                 # Update profile settings
GET    /api/affiliates/stats                   # Get statistics dashboard

# Referral Links
GET    /api/affiliates/referral-links          # List referral links
POST   /api/affiliates/referral-links          # Create custom link
GET    /api/affiliates/referral-code           # Get primary referral code

# Referrals & Network
GET    /api/affiliates/referrals               # List direct referrals (tier 1)
GET    /api/affiliates/network                 # Get full network tree (tiers 1-3)
GET    /api/affiliates/network/stats           # Network statistics

# Commissions
GET    /api/affiliates/commissions             # List commission records
GET    /api/affiliates/commissions/summary     # Summary by period
GET    /api/affiliates/commissions/pending     # Pending commissions

# Payouts
GET    /api/affiliates/payouts                 # List payout history
POST   /api/affiliates/payouts/request         # Request payout
GET    /api/affiliates/payouts/{id}            # Get payout details

# Public/Attribution endpoints
GET    /api/public/track-referral              # Track referral click (sets cookie)
POST   /api/internal/process-commission        # Internal: process after purchase
```

---

### 3. Frontend Components (Add to b2c-portal)

#### New Pages

```
/opt/kasaai/apps/b2c-portal/src/pages/
├── AffiliatesDashboard.tsx          # Main affiliate dashboard
├── AffiliatesJoin.tsx                # Join affiliate program
├── AffiliatesReferrals.tsx           # View referrals & network
├── AffiliatesCommissions.tsx         # Commission history
└── AffiliatesPayouts.tsx             # Payout requests & history
```

#### New Components

```
/opt/kasaai/apps/b2c-portal/src/components/affiliates/
├── AffiliateStats.tsx                # Stats cards (earnings, referrals, etc.)
├── ReferralLinkGenerator.tsx         # Generate & copy referral links
├── NetworkTreeView.tsx               # Visualize affiliate network
├── CommissionTable.tsx               # Commission records table
├── PayoutRequestForm.tsx             # Request payout form
├── ReferralLeaderboard.tsx           # Top affiliates (gamification)
└── AffiliateOnboarding.tsx           # Onboarding wizard
```

---

### 4. Service Layer (Add to core_backend)

```python
# /opt/kasaai/apps/core_backend/backend/services/affiliate_service.py

class AffiliateService:
    """
    Handles all affiliate program logic.
    """

    async def join_program(user_id: str, upline_referral_code: Optional[str] = None):
        """
        Enroll user in affiliate program.
        - Generate unique referral code
        - Link to upline if provided
        - Create affiliate profile
        """
        pass

    async def track_referral_click(referral_code: str, request: Request):
        """
        Track referral link click.
        - Set 30-day attribution cookie
        - Log click in referral_links
        - Return tracking pixel or redirect
        """
        pass

    async def attribute_signup(user_id: str, request: Request):
        """
        Called during signup to attribute to affiliate.
        - Check for referral cookie or URL param
        - Create attribution record
        """
        pass

    async def calculate_commission(transaction_id: str):
        """
        Calculate and record commissions after purchase.
        - Get transaction details
        - Find attributed affiliate
        - Calculate tier 1, 2, 3 commissions
        - Create commission records
        - Update affiliate stats
        """
        pass

    async def process_payout(payout_request_id: str):
        """
        Process affiliate payout.
        - Validate balance
        - Create wallet transaction or external payment
        - Update payout status
        - Send notification
        """
        pass

    async def get_network_tree(affiliate_id: str, max_depth: int = 3):
        """
        Get affiliate's referral tree.
        - Build hierarchical structure
        - Include stats per level
        """
        pass
```

---

### 5. Integration Points

#### A. Signup Flow Enhancement

**File:** `/opt/kasaai/apps/b2c-portal/src/components/auth/MongoSignupForm.tsx`

```typescript
// Add referral code input field
<Input
  placeholder="Referral Code (Optional)"
  value={referralCode}
  onChange={(e) => setReferralCode(e.target.value)}
/>

// Pass to signup API
const signupData = {
  ...existingFields,
  referral_code: referralCode
};
```

**Backend:** `/opt/kasaai/apps/core_backend/backend/services/auth_service.py`

```python
async def signup(email, password, referral_code=None):
    # Existing user creation logic
    user = await create_user(...)

    # NEW: Attribute to affiliate if referral code provided
    if referral_code:
        await affiliate_service.attribute_signup(user.id, referral_code)

    return user
```

#### B. Purchase Flow Enhancement

**File:** `/opt/kasaai/apps/core_backend/backend/services/wallet_service.py`

```python
async def create_deposit(user_id, amount, payment_method_id):
    # Existing deposit logic
    transaction = await wallet.create_deposit(...)

    # NEW: Calculate commissions if user was referred
    await affiliate_service.calculate_commission(transaction.id)

    return transaction
```

#### C. Navigation Enhancement

**File:** `/opt/kasaai/apps/b2c-portal/src/components/dashboard/DashboardSidebar.tsx`

```typescript
// Add affiliate section for enrolled users
{user.is_affiliate && (
  <NavSection title="Affiliate">
    <NavItem icon={Users} to="/affiliates" label="Dashboard" />
    <NavItem icon={Link2} to="/affiliates/referrals" label="My Referrals" />
    <NavItem icon={DollarSign} to="/affiliates/commissions" label="Commissions" />
    <NavItem icon={Wallet} to="/affiliates/payouts" label="Payouts" />
  </NavSection>
)}

// Add "Join Affiliate Program" CTA for non-affiliates
{!user.is_affiliate && (
  <Button onClick={() => navigate('/affiliates/join')}>
    Become an Affiliate
  </Button>
)}
```

---

### 6. Commission Structure Recommendation

Based on your initial request and industry standards:

```
Tier 1 (Direct Referrals): 15% commission
- User A refers User B
- User B purchases $100 credits
- User A earns $15

Tier 2 (Sub-Affiliates): 8% commission
- User A refers User B
- User B refers User C
- User C purchases $100 credits
- User A earns $8, User B earns $15

Tier 3 (Sub-Sub-Affiliates): 3% commission
- User A → User B → User C → User D
- User D purchases $100 credits
- User A earns $3, User B earns $8, User C earns $15
```

**Total Max Commission per Sale:** 26% (15% + 8% + 3%)

**Alternative Conservative Model:**
```
Tier 1: 10%
Tier 2: 5%
Tier 3: 2%
Total: 17%
```

---

### 7. Referral URL Structure

```
https://kasaai.ailabsafrica.com?ref=ALFRED001
https://kasaai.ailabsafrica.com/signup?ref=ALFRED001
https://kasaai.ailabsafrica.com/pricing?ref=ALFRED001

# With UTM tracking
https://kasaai.ailabsafrica.com?ref=ALFRED001&utm_source=instagram&utm_campaign=q1_2025

# Short URL service (optional future enhancement)
https://kasa.ai/r/ALFRED001
```

---

### 8. Cookie Attribution Logic

```javascript
// On referral link click
document.cookie = `kasaai_ref=${referralCode}; max-age=2592000; path=/; secure; samesite=lax`;

// On signup
const referralCode = getCookie('kasaai_ref') || getURLParam('ref');
if (referralCode) {
  signupData.referral_code = referralCode;
}
```

**Attribution Priority:**
1. URL parameter `?ref=CODE` (highest priority - overrides cookie)
2. Cookie `kasaai_ref` (30-day window)
3. Manual entry in signup form

---

### 9. Payout Methods

```
Option 1: Wallet Credit (Instant)
- Commission added directly to user's wallet
- Can use for purchasing more credits
- No fees
- Instant processing

Option 2: Mobile Money (MoMo, M-Pesa, etc.)
- Payout to mobile money account
- Processing fee: 2-3%
- Processing time: 1-2 business days
- Minimum: $10

Option 3: Bank Transfer
- Direct bank deposit
- Processing fee: $2-5 fixed
- Processing time: 2-5 business days
- Minimum: $50

Option 4: PayPal
- PayPal withdrawal
- Processing fee: 2.9% + $0.30
- Processing time: 1-2 business days
- Minimum: $20
```

**Recommended Default:** Wallet Credit (keeps money in ecosystem, reduces friction)

---

### 10. Gamification & Incentives (Optional Phase 2)

```
- Leaderboards (top affiliates by month/quarter)
- Achievement badges (First Sale, 10 Referrals, $1000 Earned, etc.)
- Bonus tiers (earn 20% commission after 50 referrals)
- Contests (top affiliate wins bonus credit)
- Performance analytics (conversion rates, best traffic sources)
```

---

## Implementation Phases

### Phase 1: Core Affiliate System (Week 1)
- [ ] Database schema setup (collections)
- [ ] Affiliate service layer
- [ ] Join program endpoint
- [ ] Referral code generation
- [ ] Basic affiliate dashboard page
- [ ] Referral link generator component

### Phase 2: Attribution & Tracking (Week 1)
- [ ] Cookie tracking implementation
- [ ] Signup flow integration
- [ ] Attribution service
- [ ] Track referral clicks endpoint
- [ ] Analytics integration

### Phase 3: Commission Calculation (Week 2)
- [ ] Commission calculation service
- [ ] Purchase flow integration
- [ ] Multi-tier commission logic
- [ ] Commission records API
- [ ] Commission history UI

### Phase 4: Payouts (Week 2)
- [ ] Payout request functionality
- [ ] Wallet credit payout (auto)
- [ ] External payout integrations (MoMo, Bank, PayPal)
- [ ] Payout approval workflow (admin)
- [ ] Payout history UI

### Phase 5: Advanced Features (Week 3 - Optional)
- [ ] Network tree visualization
- [ ] Leaderboards
- [ ] Performance analytics
- [ ] Email notifications
- [ ] Affiliate marketing materials (banners, templates)

---

## Cost Analysis

### Development Costs
- **Standalone Platform:** 3-4 weeks dev time = ~120-160 hours
- **ERP Integration:** 2-3 weeks dev time + refactoring = ~100-120 hours
- **B2C Portal Integration:** 1-2 weeks dev time = ~40-80 hours ✅

### Operational Costs
- **Standalone Platform:**
  - Additional server/hosting
  - Separate SSL cert
  - Duplicate payment integrations
  - Higher maintenance overhead

- **B2C Portal Integration:**
  - No additional infrastructure
  - Reuses existing services
  - Minimal maintenance overhead ✅

### Commission Costs (Ongoing)
Assuming $10,000/month in referred sales with 3-tier MLM:
- Tier 1 (15%): $1,500
- Tier 2 (8%): $800
- Tier 3 (3%): $300
- **Total Commission Expense:** $2,600/month (26% of sales)

---

## Comparison Matrix

| Factor | Standalone | ERP Integration | B2C Portal Integration |
|--------|-----------|----------------|----------------------|
| Development Time | 3-4 weeks | 2-3 weeks | 1-2 weeks ✅ |
| Infrastructure Reuse | ❌ None | ⚠️ Partial | ✅ Full |
| User Experience | ⚠️ Separate accounts | ❌ Confusing | ✅ Unified |
| Wallet Integration | ❌ Build from scratch | ❌ Build from scratch | ✅ Already exists |
| Payment Methods | ❌ Duplicate setup | ❌ New setup | ✅ Already configured |
| Maintenance Burden | ❌ High | ⚠️ Medium | ✅ Low |
| Security | ⚠️ Additional surface | ❌ Mixing concerns | ✅ Existing model |
| Scalability | ✅ Independent | ⚠️ Limited | ✅ Scales with platform |
| Cost | ❌ High | ⚠️ Medium | ✅ Low |
| **Recommendation** | ❌ | ❌ | ✅ **BEST CHOICE** |

---

## Risks & Mitigation

### Risk 1: Commission Fraud
**Risk:** Fake signups, self-referrals, click fraud
**Mitigation:**
- Require email verification before commission eligibility
- Commission only paid after actual purchase (not just signup)
- Monitor for suspicious patterns (same IP, device fingerprinting)
- Manual review for large payouts
- Minimum account age before payout eligibility

### Risk 2: Revenue Impact
**Risk:** 26% commission rate reduces profit margins
**Mitigation:**
- Start with lower rates (10%/5%/2% = 17% total)
- Implement commission caps per affiliate
- Only pay commission on net revenue (after refunds)
- Time-bound commissions (e.g., only first 6 months of referred user purchases)

### Risk 3: Payout Processing Costs
**Risk:** High fees for external payouts (MoMo, PayPal, bank transfers)
**Mitigation:**
- Incentivize wallet credit payouts (no fees)
- Batch external payouts (monthly instead of on-demand)
- Set minimum payout thresholds
- Pass processing fees to affiliates (transparent)

### Risk 4: User Confusion
**Risk:** Customers confused by affiliate features
**Mitigation:**
- Role-based navigation (hide affiliate sections for non-affiliates)
- Clear onboarding wizard
- Opt-in affiliate program (not automatic)
- Separate affiliate documentation

---

## Success Metrics

### Key Performance Indicators (KPIs)

```
Acquisition Metrics:
- Active affiliates count
- New affiliates per month
- Affiliate activation rate (joined → first referral)

Performance Metrics:
- Total referred users
- Referred user conversion rate (signup → purchase)
- Average order value (referred vs non-referred)
- Affiliate retention rate

Financial Metrics:
- Total commissions paid
- Revenue from referred users
- Cost of acquisition via affiliates vs other channels
- Lifetime value of referred customers

Engagement Metrics:
- Referral link clicks
- Average referrals per affiliate
- Top 10% affiliate performance
- Payout request frequency
```

---

## Conclusion

**Strong recommendation: Integrate into b2c-portal (@apps/b2c-portal/)**

### Why This is the Best Choice:

1. ✅ **Fastest Time to Market:** 1-2 weeks vs 3-4 weeks
2. ✅ **Lowest Development Cost:** Reuse 80% of existing infrastructure
3. ✅ **Best User Experience:** Unified account for customer + affiliate activities
4. ✅ **Proven Infrastructure:** Wallet, payments, and transactions already production-ready
5. ✅ **Scalability:** Leverages existing multi-tenant architecture
6. ✅ **Maintenance:** Single codebase, single deployment, single monitoring stack
7. ✅ **Natural Fit:** Affiliates are customers who recruit other customers

### Next Steps:

1. Review and approve this architecture
2. Set commission rate structure (recommend starting conservative: 10%/5%/2%)
3. Create TASKS.md entry with Phase 1 implementation plan
4. Begin Phase 1 development (database schema + core services)
5. Beta test with 10-20 trusted affiliates
6. Launch publicly with marketing campaign

---

## Appendix A: Example Affiliate Dashboard Wireframe

```
┌─────────────────────────────────────────────────────────────┐
│ KasaAI - Affiliate Dashboard                    [Profile ▼] │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  📊 Your Performance                                         │
│  ┌──────────────┬──────────────┬──────────────┬───────────┐ │
│  │ Total Earned │ This Month   │ Total Refs   │ Pending   │ │
│  │   $1,247.50  │   $342.80    │      47      │  $128.40  │ │
│  └──────────────┴──────────────┴──────────────┴───────────┘ │
│                                                               │
│  🔗 Your Referral Link                                       │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ https://kasaai.ailabsafrica.com?ref=ALFRED001  [Copy]  │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                               │
│  👥 Recent Referrals                                         │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ Name         │ Joined    │ Purchases │ Your Earnings   │ │
│  ├─────────────────────────────────────────────────────────┤ │
│  │ John Doe     │ 2 days    │   $50     │    $7.50       │ │
│  │ Jane Smith   │ 1 week    │  $200     │   $30.00       │ │
│  │ Bob Johnson  │ 2 weeks   │  $100     │   $15.00       │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                               │
│  💰 Request Payout                   [View Full Dashboard]   │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Appendix B: Technology Stack Summary

**Frontend (b2c-portal):**
- React 18 + TypeScript
- Tailwind CSS + shadcn/ui
- React Router (add `/affiliates/*` routes)
- TanStack Query (API state management)
- Existing auth context (MongoAuthContext)

**Backend (core_backend):**
- FastAPI (Python)
- MongoDB (add new collections)
- Existing wallet service (shared library)
- Existing payment providers (Stripe, Flutterwave, MoMo, etc.)
- JWT authentication (existing)

**Database:**
- MongoDB `kasaai_core` database
- New collections: `affiliate_profiles`, `referral_links`, `referral_attributions`, `commission_records`, `payout_requests`
- Indexes: `referral_code`, `user_id`, `affiliate_id`, `organization_id`

**Infrastructure:**
- Same deployment as b2c-portal/core_backend
- No additional services required
- Reuse existing Nginx configuration
- Same SSL certificates

---

**Document Version:** 1.0
**Date:** 2025-11-18
**Author:** AI Labs Africa - Claude Code
**Status:** Proposal - Pending Approval
