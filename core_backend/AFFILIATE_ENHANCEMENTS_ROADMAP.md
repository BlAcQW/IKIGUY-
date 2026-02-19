# Affiliate System Enhancements Roadmap

## Overview
This document outlines the implementation plan for advanced affiliate system features.

---

## ✅ Completed Features (Status: DONE)

### 1. Affiliate Leaderboard System
**Status**: ✅ Implemented
**Commit**: `5a13a396`

**Backend**:
- `GET /api/affiliates/leaderboard` - Get ranked affiliates
- `GET /api/affiliates/my-rank` - Get user's ranking
- Support for multiple metrics (earnings, referrals, sales)
- Period filtering (all_time, month, week)

**Frontend**:
- LeaderboardTable component with real-time rankings
- Special highlighting for top 3 (gold/silver/bronze)
- Personal rank tracking card
- Metric switching (earnings/referrals/sales)

---

## 🚧 Remaining Enhancements

### 2. Conversion Tracking & Attribution Analytics

**Priority**: HIGH
**Estimated Effort**: 4-6 hours
**Dependencies**: None

#### Backend Tasks:
1. **Add Click Tracking Analytics**
   ```python
   # New models in affiliate.py
   class ClickAnalytics(BaseModel):
       link_id: str
       clicked_at: datetime
       ip_address: str
       user_agent: str
       referrer: Optional[str]
       utm_params: Dict[str, str]
       converted: bool  # Did they sign up?
       converted_at: Optional[datetime]
   ```

2. **Enhance track-referral endpoint**
   - Store IP, user agent, referrer
   - Track UTM parameters
   - Store in `referral_clicks` collection

3. **Add Analytics Endpoints**
   ```python
   GET /api/affiliates/analytics/conversion-rates
   GET /api/affiliates/analytics/traffic-sources
   GET /api/affiliates/analytics/link-performance
   ```

4. **Conversion Funnel Tracking**
   - Click → View signup page → Complete signup → First purchase
   - Store funnel stage transitions

#### Frontend Tasks:
1. **Create AnalyticsDashboard component**
   - Conversion rate charts (Chart.js or Recharts)
   - Traffic source breakdown (pie chart)
   - Link performance table
   - Funnel visualization

2. **Add Analytics tab to Dashboard**
   - Replace or add alongside existing tabs
   - Time range selector (7d, 30d, 90d, all)

#### Database Collections:
```javascript
referral_clicks: {
  _id: ObjectId,
  link_id: string,
  referral_code: string,
  affiliate_id: string,
  clicked_at: datetime,
  ip_address: string,
  user_agent: string,
  referrer: string,
  utm_source: string,
  utm_campaign: string,
  utm_medium: string,
  converted: boolean,
  converted_user_id: string | null,
  converted_at: datetime | null
}
```

---

### 3. Referral Campaigns System

**Priority**: MEDIUM
**Estimated Effort**: 6-8 hours
**Dependencies**: None

#### Concept:
Allow affiliates to create time-limited campaigns with custom:
- Landing pages
- Promotional materials
- Special bonus commission rates
- Contest mechanics

#### Backend Tasks:
1. **Add Campaign Model**
   ```python
   class ReferralCampaign(BaseModel):
       id: str
       affiliate_id: str
       organization_id: str
       name: str
       description: str
       start_date: datetime
       end_date: datetime
       bonus_rate: Decimal  # Extra commission %
       target_referrals: int
       target_sales: Decimal
       prize: Optional[str]
       is_active: bool
       referral_codes: List[str]  # Campaign-specific codes
   ```

2. **Campaign Endpoints**
   ```python
   POST /api/affiliates/campaigns - Create campaign
   GET /api/affiliates/campaigns - List campaigns
   GET /api/affiliates/campaigns/{id} - Get campaign details
   PATCH /api/affiliates/campaigns/{id} - Update campaign
   GET /api/affiliates/campaigns/{id}/stats - Campaign performance
   ```

3. **Bonus Commission Logic**
   - Check if transaction belongs to active campaign
   - Apply bonus rate on top of regular commission
   - Track campaign-specific metrics

#### Frontend Tasks:
1. **Campaign Management Page**
   - Create new campaign form
   - Campaign list with status
   - Performance tracking per campaign

2. **Campaign-specific Links**
   - Generate links tagged with campaign ID
   - QR code generation for offline marketing

---

### 4. Automated Payout Scheduling

**Priority**: HIGH (Operations)
**Estimated Effort**: 3-4 hours
**Dependencies**: None

#### Backend Tasks:
1. **Create Payout Scheduler Service**
   ```python
   # backend/services/payout_scheduler.py
   class PayoutScheduler:
       async def process_scheduled_payouts(self):
           # Find affiliates with balance > threshold
           # Auto-create payout requests
           # Integrate with payment provider APIs
   ```

2. **Add Scheduler Configuration**
   ```python
   # In affiliate profile
   auto_payout_enabled: bool = False
   auto_payout_schedule: str = "monthly"  # weekly, monthly
   auto_payout_day: int = 15  # Day of month
   ```

3. **Background Task (Celery/APScheduler)**
   ```python
   # Run daily
   @scheduler.scheduled_job('cron', hour=2)
   async def auto_payout_task():
       scheduler = PayoutScheduler(db)
       await scheduler.process_scheduled_payouts()
   ```

4. **Payout API Integration**
   - PayPal Mass Payments API
   - Stripe Payouts API
   - Mobile Money APIs (M-Pesa, etc.)
   - Bank transfer APIs

5. **Payout Status Tracking**
   ```python
   class PayoutStatus(Enum):
       PENDING = "pending"
       PROCESSING = "processing"
       COMPLETED = "completed"
       FAILED = "failed"
       CANCELLED = "cancelled"
   ```

#### Frontend Tasks:
1. **Auto-Payout Settings**
   - Toggle auto-payout on/off
   - Set schedule (weekly/monthly)
   - Set payout day
   - Minimum threshold

2. **Payout History with Status**
   - Show processing status
   - Transaction IDs
   - Failure reasons
   - Retry options

---

### 5. Real-time WebSocket Notifications

**Priority**: LOW (Nice to have)
**Estimated Effort**: 8-10 hours
**Dependencies**: WebSocket infrastructure

#### Backend Tasks:
1. **WebSocket Setup (Socket.IO or FastAPI WebSockets)**
   ```python
   # backend/websockets/affiliate_notifications.py
   @app.websocket("/ws/affiliates/{user_id}")
   async def affiliate_websocket(websocket, user_id):
       # Send real-time notifications
       pass
   ```

2. **Event Types to Broadcast**
   - New referral signup
   - Commission earned
   - Payout processed
   - Rank change on leaderboard
   - Campaign milestone reached

3. **Notification Service**
   ```python
   class AffiliateNotificationService:
       async def broadcast_new_commission(affiliate_id, commission):
           # Send to connected WebSocket clients

       async def broadcast_rank_change(affiliate_id, old_rank, new_rank):
           # Send rank update
   ```

#### Frontend Tasks:
1. **WebSocket Hook**
   ```typescript
   // hooks/useAffiliateNotifications.ts
   export const useAffiliateNotifications = () => {
       const [socket, setSocket] = useState<Socket | null>(null);
       // Connect, listen, disconnect
   }
   ```

2. **Notification Toast System**
   - Real-time commission alerts
   - Referral signup notifications
   - Rank update celebrations

3. **Live Dashboard Updates**
   - Auto-refresh stats without reload
   - Real-time leaderboard updates

---

## Implementation Priority

### Phase 1 (High Value, Low Effort)
1. ✅ **Leaderboard** - COMPLETED
2. **Automated Payouts** - Critical for operations
3. **Conversion Analytics** - Key for affiliate optimization

### Phase 2 (Medium Priority)
4. **Referral Campaigns** - Marketing feature
5. **Real-time Notifications** - User engagement

---

## Database Indexes Needed

```javascript
// For analytics performance
db.referral_clicks.createIndex({ "referral_code": 1, "clicked_at": -1 })
db.referral_clicks.createIndex({ "affiliate_id": 1, "converted": 1 })
db.referral_clicks.createIndex({ "utm_campaign": 1, "clicked_at": -1 })

// For campaigns
db.referral_campaigns.createIndex({ "affiliate_id": 1, "is_active": 1 })
db.referral_campaigns.createIndex({ "end_date": 1, "is_active": 1 })

// For payouts
db.payout_requests.createIndex({ "status": 1, "created_at": -1 })
db.payout_requests.createIndex({ "affiliate_id": 1, "status": 1 })
```

---

## Testing Requirements

### For Each Feature:
1. **Unit Tests** - Service methods
2. **Integration Tests** - API endpoints
3. **Load Tests** - Performance under scale
4. **Security Tests** - Authorization, data validation

### Example Test Coverage:
```python
# tests/test_analytics.py
async def test_conversion_rate_calculation()
async def test_traffic_source_breakdown()
async def test_link_performance_metrics()

# tests/test_campaigns.py
async def test_create_campaign()
async def test_bonus_commission_calculation()
async def test_campaign_expiration()

# tests/test_payouts.py
async def test_auto_payout_eligibility()
async def test_payout_processing()
async def test_payout_retry_logic()
```

---

## Metrics to Track

### Business Metrics:
- Total affiliate signups
- Active affiliates (made commission in last 30d)
- Average commission per affiliate
- Top referral sources
- Conversion rate by traffic source
- Payout processing time
- Failed payout rate

### Technical Metrics:
- API response times
- WebSocket connection stability
- Database query performance
- Background task success rate

---

## Next Steps

To continue implementation:
1. Choose which enhancement to implement next
2. Review database schema changes
3. Implement backend service methods
4. Add API endpoints
5. Create frontend components
6. Write tests
7. Deploy and monitor

Would you like to proceed with any specific enhancement?
