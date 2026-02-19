# Affiliate Platform - Implementation Tasks

**Project:** Multi-Level Marketing (MLM) / Affiliate System
**Target:** B2C Portal Integration
**Start Date:** 2025-11-18
**Estimated Duration:** 2 weeks

---

## Phase 1: Database & Core Services (Week 1, Days 1-3)

### Database Setup
- [x] Create `affiliate_profiles` collection with indexes
- [x] Create `referral_links` collection with indexes
- [x] Create `referral_attributions` collection with indexes
- [x] Create `commission_records` collection with indexes
- [x] Create `payout_requests` collection with indexes
- [x] Add `is_affiliate` field to existing `users` collection
- [x] Create database initialization script
- [x] Test MongoDB indexes performance (32 indexes created across 5 collections + 1 on users)

### Backend Models (core_backend)
- [x] Create `/opt/kasaai/apps/core_backend/backend/models/affiliate.py`
  - [x] `AffiliateProfile` Pydantic model
  - [x] `ReferralLink` Pydantic model
  - [x] `ReferralAttribution` Pydantic model
  - [x] `CommissionRecord` Pydantic model
  - [x] `PayoutRequest` Pydantic model
- [x] Create `/opt/kasaai/apps/core_backend/backend/schemas/affiliate.py`
  - [x] Request schemas (JoinProgramRequest, UpdateProfileRequest, etc.)
  - [x] Response schemas (AffiliateStatsResponse, etc.)

### Backend Services (core_backend)
- [x] Create `/opt/kasaai/apps/core_backend/backend/services/affiliate_service.py`
  - [x] `join_program(user_id, upline_code)` - Enroll user
  - [x] `generate_referral_code(user_id)` - Generate unique code
  - [x] `get_profile(user_id)` - Get affiliate profile
  - [x] `update_profile(user_id, updates)` - Update settings
  - [x] `get_stats(user_id)` - Calculate statistics
  - [x] `track_click(referral_code, request)` - Track referral clicks
  - [x] `attribute_signup(user_id, referral_code)` - Attribute new user
  - [x] `calculate_commission(transaction_id)` - Calculate multi-tier commissions
  - [x] `get_affiliate_chain(affiliate_id, max_tiers)` - Get upline chain
  - [x] `get_referrals(user_id, tier)` - List referrals by tier
  - [x] `get_network_tree(user_id)` - Build network tree
  - [x] `get_commissions(user_id, filters)` - List commissions
  - [x] `request_payout(user_id, amount, method)` - Create payout request
  - [x] `process_payout(payout_id, admin_user_id)` - Process payout (pending - admin feature)
  - [x] `update_affiliate_stats(user_id)` - Update stats after actions

---

## Phase 2: API Endpoints (Week 1, Days 4-5)

### API Router (core_backend)
- [x] Create `/opt/kasaai/apps/core_backend/backend/routes/affiliates.py`
- [x] Register router in `main.py`

### Affiliate Management Endpoints
- [x] `POST /api/affiliates/join` - Join affiliate program
- [x] `GET /api/affiliates/profile` - Get affiliate profile
- [x] `PATCH /api/affiliates/profile` - Update profile settings
- [x] `GET /api/affiliates/stats` - Get dashboard statistics

### Referral Link Endpoints
- [x] `GET /api/affiliates/referral-links` - List all referral links
- [x] `POST /api/affiliates/referral-links` - Create custom link
- [x] `GET /api/affiliates/referral-code` - Get primary referral code

### Network & Referrals Endpoints
- [x] `GET /api/affiliates/referrals` - List referrals (with tier filter)
- [ ] `GET /api/affiliates/network` - Get network tree structure (future enhancement)
- [x] `GET /api/affiliates/network/stats` - Get network statistics

### Commission Endpoints
- [x] `GET /api/affiliates/commissions` - List commissions (with filters)
- [ ] `GET /api/affiliates/commissions/summary` - Get summary by period (future enhancement)
- [x] `GET /api/affiliates/commissions/pending` - Get pending commissions

### Payout Endpoints
- [x] `GET /api/affiliates/payouts` - List payout history
- [x] `POST /api/affiliates/payouts/request` - Request payout
- [ ] `GET /api/affiliates/payouts/{id}` - Get payout details (future enhancement)

### Public/Internal Endpoints
- [x] `GET /api/public/track-referral?ref={code}` - Track referral click
- [x] `POST /api/internal/process-commission` - Process commission (internal)

### API Testing
- [ ] Write Pytest tests for all endpoints
- [ ] Test with real database
- [ ] Test authentication and authorization
- [ ] Test error handling

---

## Phase 3: Frontend Foundation (Week 2, Days 1-2)

### Frontend API Client (b2c-portal)
- [x] Extend `/opt/kasaai/apps/b2c-portal/src/lib/core-api.ts`
  - [x] `affiliateApi.joinProgram(uplineCode?)`
  - [x] `affiliateApi.getProfile()`
  - [x] `affiliateApi.updateProfile(updates)`
  - [x] `affiliateApi.getStats()`
  - [x] `affiliateApi.getReferralLinks()`
  - [x] `affiliateApi.createReferralLink(utmData)`
  - [x] `affiliateApi.getReferralCode()`
  - [x] `affiliateApi.getReferrals(tier?, limit?, offset?)`
  - [ ] `affiliateApi.getNetworkTree()` - Future enhancement
  - [x] `affiliateApi.getNetworkStats()`
  - [x] `affiliateApi.getCommissions(filters?)`
  - [ ] `affiliateApi.getCommissionsSummary(startDate?, endDate?)` - Future enhancement
  - [x] `affiliateApi.getPendingCommissions()`
  - [x] `affiliateApi.getPayouts(limit?, offset?)`
  - [x] `affiliateApi.requestPayout(amount, method, paymentMethodId?)`
  - [x] `affiliateApi.trackReferral(code)` - Public tracking
  - [x] Added all TypeScript interfaces for type safety
  - [x] Registered in coreApi export

### Shared Components (b2c-portal)
- [ ] Create `/opt/kasaai/apps/b2c-portal/src/components/affiliates/` directory
- [ ] Create `AffiliateStats.tsx` - Stats cards component
  - [ ] Total earnings card
  - [ ] This month earnings card
  - [ ] Total referrals card
  - [ ] Pending commissions card
- [ ] Create `ReferralLinkGenerator.tsx` - Generate and copy links
  - [ ] Display primary referral code
  - [ ] Generate custom links with UTM parameters
  - [ ] Copy to clipboard functionality
  - [ ] Share buttons (social media)
- [ ] Create `CommissionTable.tsx` - Commission records table
  - [ ] Sortable columns (date, amount, tier, status)
  - [ ] Filter by status, tier, date range
  - [ ] Pagination
  - [ ] Export to CSV
- [ ] Create `ReferralTable.tsx` - List of referrals
  - [ ] Show name, email, joined date, tier
  - [ ] Show total purchases and commissions earned
  - [ ] Filter by tier
  - [ ] Pagination
- [ ] Create `PayoutRequestForm.tsx` - Request payout form
  - [ ] Amount input with validation
  - [ ] Payout method selection
  - [ ] Payment method selection (if applicable)
  - [ ] Show processing fees
  - [ ] Confirm dialog
- [ ] Create `NetworkTreeView.tsx` - Visualize network (basic version)
  - [ ] List view by tier (Phase 1)
  - [ ] Tree graph visualization (Phase 2 - optional)
- [ ] Create `AffiliateOnboarding.tsx` - Onboarding wizard
  - [ ] Welcome step
  - [ ] How it works explanation
  - [ ] Commission structure display
  - [ ] Enter upline code (optional)
  - [ ] Complete enrollment

---

## Phase 4: Frontend Pages (Week 2, Days 3-4)

### Affiliate Pages (b2c-portal)
- [ ] Create `/opt/kasaai/apps/b2c-portal/src/pages/affiliates/` directory
- [ ] Create `AffiliatesDashboard.tsx`
  - [ ] Use `AffiliateStats` component
  - [ ] Use `ReferralLinkGenerator` component
  - [ ] Show recent referrals table
  - [ ] Show recent commissions table
  - [ ] Quick payout request button
- [ ] Create `AffiliatesJoin.tsx`
  - [ ] Use `AffiliateOnboarding` component
  - [ ] Check if already enrolled (redirect if yes)
  - [ ] Handle enrollment API call
  - [ ] Redirect to dashboard on success
- [ ] Create `AffiliatesReferrals.tsx`
  - [ ] Use `ReferralTable` component
  - [ ] Tier filter tabs (All, Tier 1, Tier 2, Tier 3)
  - [ ] Use `NetworkTreeView` component
  - [ ] Show network stats summary
- [ ] Create `AffiliatesCommissions.tsx`
  - [ ] Use `CommissionTable` component
  - [ ] Summary cards (total earned, this month, pending)
  - [ ] Filter controls (status, tier, date range)
  - [ ] Export functionality
- [ ] Create `AffiliatesPayouts.tsx`
  - [ ] Use `PayoutRequestForm` component
  - [ ] Show payout history table
  - [ ] Show pending payouts
  - [ ] Payout status tracking

### Routing (b2c-portal)
- [ ] Update `/opt/kasaai/apps/b2c-portal/src/App.tsx`
  - [ ] Add route: `/affiliates` → `AffiliatesDashboard`
  - [ ] Add route: `/affiliates/join` → `AffiliatesJoin`
  - [ ] Add route: `/affiliates/referrals` → `AffiliatesReferrals`
  - [ ] Add route: `/affiliates/commissions` → `AffiliatesCommissions`
  - [ ] Add route: `/affiliates/payouts` → `AffiliatesPayouts`
  - [ ] Add protected route wrapper (requires authentication)

---

## Phase 5: Integration (Week 2, Day 5)

### Signup Flow Integration
- [ ] Update `/opt/kasaai/apps/b2c-portal/src/components/auth/MongoSignupForm.tsx`
  - [ ] Add referral code input field (optional)
  - [ ] Pre-fill from cookie `kasaai_ref` on mount
  - [ ] Pre-fill from URL param `?ref=CODE` on mount
  - [ ] Pass referral_code to signup API
- [ ] Update `/opt/kasaai/apps/core_backend/backend/services/auth_service.py`
  - [ ] Accept `referral_code` parameter in signup
  - [ ] Call `affiliate_service.attribute_signup()` after user creation
  - [ ] Handle invalid referral codes gracefully

### Purchase Flow Integration
- [ ] Update `/opt/kasaai/apps/core_backend/backend/services/wallet_service.py`
  - [ ] After deposit completion (status = "completed")
  - [ ] Call `affiliate_service.calculate_commission(transaction_id)`
  - [ ] Log commission calculation results
  - [ ] Handle commission calculation errors gracefully

### Navigation Integration
- [ ] Update `/opt/kasaai/apps/b2c-portal/src/components/dashboard/DashboardSidebar.tsx`
  - [ ] Add "Affiliate" navigation section
  - [ ] Show only if user is enrolled (`user.is_affiliate`)
  - [ ] Add menu items:
    - [ ] Dashboard (`/affiliates`)
    - [ ] My Referrals (`/affiliates/referrals`)
    - [ ] Commissions (`/affiliates/commissions`)
    - [ ] Payouts (`/affiliates/payouts`)
  - [ ] Add earnings badge (show pending commissions)
  - [ ] Add "Become an Affiliate" CTA button if not enrolled
  - [ ] Link CTA to `/affiliates/join`

### Referral Tracking Middleware
- [ ] Update `/opt/kasaai/apps/b2c-portal/src/App.tsx`
  - [ ] Add useEffect hook to check URL param `?ref=CODE`
  - [ ] Set cookie `kasaai_ref` if referral code found
  - [ ] Cookie settings: max-age=2592000 (30 days), secure, samesite=lax
  - [ ] Call `/api/public/track-referral?ref=CODE` to log click
  - [ ] Handle tracking errors silently (don't block user)

### User Context Enhancement
- [ ] Update user context to include `is_affiliate` field
- [ ] Fetch affiliate profile on login (if enrolled)
- [ ] Cache affiliate stats in context

---

## Phase 6: Testing (Week 2, Day 5)

### Backend Unit Tests
- [ ] Create `/opt/kasaai/apps/core_backend/tests/test_affiliate_service.py`
  - [ ] Test `join_program()` - creates profile and referral code
  - [ ] Test `generate_referral_code()` - uniqueness
  - [ ] Test `get_affiliate_chain()` - correct tier levels
  - [ ] Test `calculate_commission()` - correct amounts per tier
  - [ ] Test `attribute_signup()` - creates attribution record
  - [ ] Test fraud detection logic

### Backend Integration Tests
- [ ] Create `/opt/kasaai/apps/core_backend/tests/test_affiliate_api.py`
  - [ ] Test join program endpoint (with/without upline)
  - [ ] Test get profile (enrolled vs non-enrolled)
  - [ ] Test referral tracking flow
  - [ ] Test commission calculation on purchase
  - [ ] Test payout request creation
  - [ ] Test authentication and authorization

### Frontend Component Tests
- [ ] Test `AffiliateStats` renders correctly
- [ ] Test `ReferralLinkGenerator` copy functionality
- [ ] Test `CommissionTable` filtering and sorting
- [ ] Test `PayoutRequestForm` validation
- [ ] Test `AffiliateOnboarding` wizard flow

### E2E Tests
- [ ] Create `/opt/kasaai/apps/b2c-portal/tests/e2e/affiliate-flow.spec.ts`
  - [ ] Test complete flow: join → refer → earn → payout
  - [ ] User A joins affiliate program
  - [ ] User A generates referral link
  - [ ] User B signs up with referral code
  - [ ] User B makes purchase
  - [ ] Verify User A earns tier 1 commission
  - [ ] User A requests payout
  - [ ] Verify payout record created

---

## Phase 7: Documentation & Deployment

### Documentation
- [ ] Update `/opt/kasaai/apps/b2c-portal/README.md`
  - [ ] Add affiliate platform section
  - [ ] Document new routes and components
- [ ] Create affiliate help documentation
  - [ ] How to join the program
  - [ ] How to generate referral links
  - [ ] Commission structure explained
  - [ ] How to request payouts
  - [ ] FAQs
- [ ] Update API documentation (Swagger/ReDoc)
  - [ ] Document all affiliate endpoints
  - [ ] Add example requests/responses

### Deployment Preparation
- [ ] Review all environment variables
- [ ] Create database migration script
- [ ] Prepare staging deployment
  - [ ] Deploy to dev server (85.214.12.174)
  - [ ] Test on dev environment
  - [ ] Fix any issues
- [ ] Prepare production deployment
  - [ ] Create deployment checklist
  - [ ] Schedule deployment window
  - [ ] Prepare rollback plan

### Deployment to Dev Server
- [ ] Run database migration script
- [ ] Deploy core_backend changes
  - [ ] Update code
  - [ ] Restart service: `sudo systemctl restart kasaai-core-backend`
  - [ ] Check logs: `sudo journalctl -u kasaai-core-backend -f`
- [ ] Deploy b2c-portal changes
  - [ ] Build frontend: `npm run build`
  - [ ] Deploy to nginx
  - [ ] Clear cache
- [ ] Verify deployment
  - [ ] Test affiliate enrollment
  - [ ] Test referral tracking
  - [ ] Test commission calculation
  - [ ] Test payout request

### Deployment to Production
- [ ] Same as dev deployment steps
- [ ] Deploy to production server (148.251.0.46)
- [ ] Monitor for errors
- [ ] Announce launch

---

## Phase 8: Beta Testing & Launch

### Beta Testing
- [ ] Recruit 10-20 beta testers
- [ ] Provide beta testers with instructions
- [ ] Monitor beta tester activity
- [ ] Collect feedback
- [ ] Fix bugs and issues
- [ ] Iterate based on feedback

### Marketing Preparation
- [ ] Create affiliate program landing page
- [ ] Design marketing materials
  - [ ] Email templates
  - [ ] Social media posts
  - [ ] Banners and graphics
- [ ] Prepare affiliate onboarding email sequence
- [ ] Create affiliate success stories

### Launch
- [ ] Public announcement
- [ ] Email existing users about affiliate program
- [ ] Social media campaign
- [ ] Monitor signups and performance
- [ ] Provide support for early affiliates

---

## Phase 9: Monitoring & Optimization

### Monitoring Setup
- [ ] Set up alerts for:
  - [ ] Failed commission calculations
  - [ ] Failed payout processing
  - [ ] Suspicious referral patterns
  - [ ] High payout request volume
- [ ] Create admin dashboard for:
  - [ ] Total affiliates count
  - [ ] Total commissions paid
  - [ ] Revenue from referred users
  - [ ] Top affiliates leaderboard
  - [ ] Pending payout approvals

### Performance Optimization
- [ ] Monitor database query performance
- [ ] Optimize slow queries
- [ ] Add caching where appropriate
- [ ] Monitor API response times
- [ ] Optimize frontend bundle size

### Analytics
- [ ] Track affiliate program KPIs
  - [ ] Active affiliates
  - [ ] Conversion rates
  - [ ] Average earnings per affiliate
  - [ ] ROI of affiliate program
- [ ] Create weekly/monthly reports
- [ ] Analyze top performer patterns

---

## Future Enhancements (Phase 10 - Optional)

### Advanced Features
- [ ] Network tree graph visualization (D3.js or similar)
- [ ] Leaderboards with monthly winners
- [ ] Achievement badges system
- [ ] Performance analytics dashboard
- [ ] Affiliate marketing materials library
- [ ] Email drip campaigns for affiliates
- [ ] SMS notifications for new referrals
- [ ] Recurring commissions (lifetime value)
- [ ] Tiered affiliate levels (Bronze, Silver, Gold)
- [ ] Custom commission rates per affiliate
- [ ] Bulk payout processing for admins
- [ ] Fraud detection ML model
- [ ] Short URL service (kasa.ai/r/CODE)

---

## Notes & Discoveries

### [Add discoveries during implementation]

---

## Completion Checklist

### Phase 1: Database & Core Services
- [ ] All collections created
- [ ] All indexes applied
- [ ] All models defined
- [ ] All service methods implemented
- [ ] Unit tests passing

### Phase 2: API Endpoints
- [ ] All endpoints implemented
- [ ] All endpoints tested
- [ ] API documentation updated
- [ ] Integration tests passing

### Phase 3: Frontend Foundation
- [ ] API client extended
- [ ] All shared components created
- [ ] Component tests passing

### Phase 4: Frontend Pages
- [ ] All pages created
- [ ] Routing configured
- [ ] Page tests passing

### Phase 5: Integration
- [ ] Signup flow integrated
- [ ] Purchase flow integrated
- [ ] Navigation integrated
- [ ] Referral tracking working

### Phase 6: Testing
- [ ] All backend tests passing
- [ ] All frontend tests passing
- [ ] E2E tests passing

### Phase 7: Documentation & Deployment
- [ ] Documentation complete
- [ ] Deployed to dev server
- [ ] Deployed to production

### Phase 8: Beta Testing & Launch
- [ ] Beta testing complete
- [ ] Issues resolved
- [ ] Public launch successful

### Phase 9: Monitoring & Optimization
- [ ] Monitoring in place
- [ ] Performance optimized
- [ ] Analytics tracking

---

**Status:** Ready to Start
**Last Updated:** 2025-11-18
