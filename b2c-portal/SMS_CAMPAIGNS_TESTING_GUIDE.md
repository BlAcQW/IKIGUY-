# SMS Campaign Testing Guide with Arkesel
**Created:** 2025-12-03
**Purpose:** Step-by-step guide to test b2c-portal SMS campaigns with Arkesel provider

---

## Prerequisites

### 1. Arkesel Account Setup
1. Sign up at https://developers.arkesel.com/
2. Obtain API Key from dashboard
3. Register sender ID(s) with Arkesel
4. Verify account has SMS credits

### 2. Environment Configuration
Add to `/opt/kasaai/.env`:
```bash
# Arkesel SMS Provider
ARKESEL_API_KEY=your_api_key_here
ARKESEL_SENDER_ID=YOUR_SENDER  # Optional default sender ID
```

### 3. Backend Configuration
Verify Arkesel is configured in `core_backend/backend/routes/sms_campaigns.py`:
```python
sms_config = {
    "providers": {
        "arkesel": {
            "api_key": os.getenv("ARKESEL_API_KEY", ""),
            "sender_id": os.getenv("ARKESEL_SENDER_ID", "")
        }
    },
    "default_provider": "arkesel"
}
```

### 4. Restart Services
```bash
sudo systemctl restart kasaai-core-backend
```

---

## Test Plan

### Phase 1: Basic Campaign Creation (15 minutes)

#### Test 1.1: Create Campaign with Auto-Preparation
**Objective:** Verify campaign creation and automatic message preparation

**Steps:**
1. Navigate to `https://kasaai.ailabsafrica.com/sms-campaigns`
2. Click "Create Campaign"
3. Fill in form:
   - **Name:** "Test Campaign - Arkesel"
   - **Template:** "Hello {{name}}, this is a test message from Arkesel. Phone: {{phone}}"
   - **SMS Provider:** Select "Arkesel (Ghana)"
   - **Sender ID:** Your registered Arkesel sender ID
   - **Send Rate:** 1/sec (Normal)
4. Click "Create Campaign"

**Expected Results:**
- ✅ Toast message: "Campaign created and messages are prepared"
- ✅ Campaign appears in list with status "Draft"
- ✅ Progress shows 0/N where N = audience size
- ✅ No manual "Prepare" button needed

**Verification:**
```bash
# Check backend logs for auto-preparation
sudo journalctl -u kasaai-core-backend -f | grep -i "prepare"
```

---

#### Test 1.2: Template Preview
**Objective:** Verify template rendering with placeholders

**Steps:**
1. In Create Campaign dialog, enter template with placeholders
2. Click "Preview" button

**Expected Results:**
- ✅ Preview card shows rendered content
- ✅ Character count displayed
- ✅ SMS segment count calculated (160 chars/segment)
- ✅ Placeholders listed: name, phone

---

### Phase 2: Real-Time Status Updates (20 minutes)

#### Test 2.1: Start Campaign & Monitor SSE
**Objective:** Verify Server-Sent Events work for live updates

**Preparation:**
- Create a test audience with 5-10 real phone numbers (use team members)
- Ensure you have SMS credits in Arkesel account

**Steps:**
1. Click "Play" button on draft campaign
2. Keep browser tab open
3. Watch progress bar and counters

**Expected Results:**
- ✅ Campaign status changes to "Running" immediately
- ✅ Progress bar updates in real-time (no manual refresh)
- ✅ "Sent" counter increments live
- ✅ "Total Cost" updates as messages send
- ✅ No page refresh needed

**Technical Verification:**
```javascript
// Open browser console and check:
// You should see EventSource connection
performance.getEntriesByType('resource').filter(r => r.name.includes('status-stream'))
```

**Network Tab Check:**
- Open DevTools → Network → EventStream
- Look for `/sms-campaigns/{id}/status-stream`
- Should show continuous connection with periodic updates

---

#### Test 2.2: SSE Disconnect Handling
**Objective:** Verify SSE connections close properly

**Steps:**
1. Start a campaign
2. Wait for it to complete
3. Close the tab or navigate away

**Expected Results:**
- ✅ EventSource connection closes automatically
- ✅ No memory leaks in browser
- ✅ No error messages in console

**Verification:**
```bash
# Check backend logs - no hanging connections
sudo netstat -an | grep :30027 | grep ESTABLISHED | wc -l
```

---

### Phase 3: Edit Campaign (10 minutes)

#### Test 3.1: Edit Draft Campaign
**Objective:** Verify edit functionality with auto-re-preparation

**Steps:**
1. Create a draft campaign
2. Click blue "Edit" button (pencil icon)
3. Modify campaign:
   - Change name to "Test Campaign - Edited"
   - Update template: "Updated message: Hello {{name}}!"
   - Change send rate to 2/sec (Fast)
4. Click "Update Campaign"

**Expected Results:**
- ✅ Toast: "Campaign updated and messages are re-prepared"
- ✅ Campaign list shows updated name
- ✅ Edit dialog closes
- ✅ Old form data cleared

**Backend Verification:**
```bash
# Check logs for re-preparation
sudo journalctl -u kasaai-core-backend -n 50 | grep -i "prepare"
```

---

#### Test 3.2: Edit Paused Campaign
**Objective:** Verify edit works after pausing

**Steps:**
1. Start a campaign
2. Click "Pause" button
3. Click "Edit" button
4. Make changes and update

**Expected Results:**
- ✅ Can edit paused campaign
- ✅ Messages re-prepared after edit
- ✅ Campaign remains paused (doesn't auto-resume)

---

#### Test 3.3: Prevent Editing Running Campaign
**Objective:** Verify edit button is hidden for running campaigns

**Steps:**
1. Start a campaign
2. Look for edit button while campaign is running

**Expected Results:**
- ✅ Edit button not visible for "Running" campaigns
- ✅ Only Pause button available

---

### Phase 4: Message-Level Analytics (15 minutes)

#### Test 4.1: View Campaign Details
**Objective:** Verify tabbed analytics interface

**Steps:**
1. Click "Eye" icon on any campaign
2. Verify "Overview" tab content

**Expected Results:**
- ✅ Two tabs visible: "Overview" and "Messages"
- ✅ Overview shows:
  - Status badge
  - Provider name (Arkesel)
  - Progress bar with percentages
  - Total/Sent/Failed/Pending counts
  - Message template
  - Total cost
  - Created/Started timestamps
- ✅ Action buttons visible based on status

---

#### Test 4.2: View Message-Level Details
**Objective:** Verify detailed message analytics with error tracking

**Steps:**
1. In Campaign Details, click "Messages" tab
2. Wait for messages to load
3. Review message list

**Expected Results:**
- ✅ Loading spinner appears briefly
- ✅ Table shows for each message:
  - Recipient name
  - Phone number (monospace font)
  - Status badge (color-coded)
  - Sent timestamp
  - Cost (4 decimal places)
  - **Error message** (if failed)
- ✅ Empty state if no messages

**Critical Test - Failed Message Debugging:**
1. Intentionally send to invalid number (e.g., +233000000000)
2. Wait for failure
3. Open Messages tab
4. Find the failed message

**Expected:**
- ✅ Status badge shows "failed" (red)
- ✅ Error column shows Arkesel error message
- ✅ Error is not truncated in table cell

---

### Phase 5: Campaign Duplication (10 minutes)

#### Test 5.1: Duplicate Completed Campaign
**Objective:** Verify copy functionality for recurring campaigns

**Steps:**
1. Wait for a campaign to complete (or manually complete one)
2. Click purple "Copy" button (clipboard icon)
3. Verify Create Campaign dialog opens

**Expected Results:**
- ✅ Copy button only visible for "Completed" campaigns
- ✅ Create Campaign dialog opens automatically
- ✅ All fields pre-filled:
  - Name: "{Original Name} (Copy)"
  - Template content: identical
  - Audience: same
  - Sender ID: same
  - Send rate: same
  - SMS Provider: Arkesel
- ✅ Toast: "Campaign duplicated - Pre-filled with original campaign data"

---

#### Test 5.2: Create from Duplicate
**Objective:** Verify duplicated campaign can be created

**Steps:**
1. After clicking Copy, modify name if desired
2. Click "Create Campaign"

**Expected Results:**
- ✅ New campaign created (separate from original)
- ✅ Messages auto-prepared
- ✅ Both campaigns visible in list
- ✅ Original campaign unchanged

---

### Phase 6: Arkesel-Specific Tests (20 minutes)

#### Test 6.1: Sender ID Configuration
**Objective:** Verify Arkesel sender ID works

**Steps:**
1. Create campaign with custom sender ID
2. Use alphanumeric sender (max 11 chars): "TESTAPP" or "MyBrand"
3. Send to real phone number

**Expected Results:**
- ✅ SMS received with correct sender ID
- ✅ No "Invalid Sender ID" errors
- ✅ Arkesel accepts alphanumeric sender

**Arkesel Requirements:**
- Alphanumeric: A-Z, a-z, 0-9 (max 11 chars)
- Must be registered with Arkesel first
- Some sender IDs require pre-approval

---

#### Test 6.2: Cost Tracking
**Objective:** Verify accurate cost calculation for Arkesel

**Steps:**
1. Send campaign with 10 messages
2. Check Arkesel dashboard for actual cost
3. Compare with b2c-portal total cost

**Expected Results:**
- ✅ Costs match (or very close)
- ✅ Cost per message displayed correctly
- ✅ Total cost updated in real-time

**Arkesel Pricing (Ghana):**
- Local SMS: ~GHS 0.025 per message
- International: varies by country
- Long SMS (>160 chars): multiple segments billed

---

#### Test 6.3: Error Handling
**Objective:** Verify proper error messages from Arkesel

**Test Cases:**
| Scenario | Expected Error | Status |
|----------|---------------|--------|
| Invalid phone format | "Invalid phone number" | ✅ |
| Insufficient credits | "Insufficient balance" | ✅ |
| Invalid sender ID | "Sender ID not registered" | ✅ |
| Network timeout | Connection error caught | ✅ |
| Rate limit exceeded | Backoff and retry | ✅ |

**Steps:**
1. Test each scenario by intentionally triggering error
2. Check Messages tab for error details
3. Verify error is user-friendly

---

### Phase 7: Performance & Stress Tests (30 minutes)

#### Test 7.1: Large Campaign (1000+ messages)
**Objective:** Verify system handles large campaigns

**Steps:**
1. Create audience with 1000+ contacts
2. Create campaign with this audience
3. Start campaign
4. Monitor:
   - SSE updates frequency
   - UI responsiveness
   - Backend load
   - Message send rate

**Expected Results:**
- ✅ UI remains responsive
- ✅ SSE updates every 2-3 seconds
- ✅ Progress bar smooth
- ✅ No browser freezing
- ✅ Backend CPU < 50%

---

#### Test 7.2: Multiple Concurrent Campaigns
**Objective:** Verify SSE handles multiple campaigns

**Steps:**
1. Start 3-5 campaigns simultaneously
2. Keep all campaigns visible in list
3. Monitor updates

**Expected Results:**
- ✅ All campaigns update independently
- ✅ No interference between SSE streams
- ✅ Network tab shows separate EventSource connections
- ✅ No memory leaks

---

#### Test 7.3: Message List Pagination
**Objective:** Test message list with 100+ messages

**Steps:**
1. Run campaign with 200+ messages
2. Open Messages tab
3. Scroll through list

**Expected Results:**
- ✅ First 100 messages load quickly
- ✅ Pagination controls appear (if implemented)
- ✅ Scroll performance acceptable
- ✅ No duplicate messages

---

## Known Issues & Workarounds

### Issue 1: SSE Connection Drops
**Symptom:** Real-time updates stop after 30 seconds
**Cause:** Nginx timeout or proxy configuration
**Workaround:**
```nginx
# In nginx.conf
location /sms-campaigns/ {
    proxy_read_timeout 300s;
    proxy_buffering off;
}
```

### Issue 2: Messages Tab Slow for Large Campaigns
**Symptom:** Loading 5000+ messages takes >5 seconds
**Solution:** Implement pagination (already prepared in code)
**Workaround:** Limit displayed messages to 100 with "Load More" button

---

## Success Criteria

### All tests must pass:
- ✅ Auto-preparation works (no manual step)
- ✅ Real-time updates via SSE functional
- ✅ Edit campaign works for draft/paused
- ✅ Message-level analytics with errors displayed
- ✅ Duplicate campaign creates new copy
- ✅ Arkesel provider sends successfully
- ✅ Costs calculated accurately
- ✅ No console errors
- ✅ No memory leaks
- ✅ UI responsive under load

### Performance Benchmarks:
- Campaign creation: < 2 seconds
- Message preparation: < 5 seconds for 1000 messages
- SSE update latency: < 3 seconds
- Messages tab load: < 2 seconds for 100 messages

---

## Troubleshooting

### Problem: Campaign stuck in "Draft"
**Check:**
1. Backend logs: `sudo journalctl -u kasaai-core-backend -n 100`
2. Message preparation errors
3. Audience has valid contacts

### Problem: SSE not updating
**Check:**
1. Browser console for EventSource errors
2. Network tab - is connection established?
3. Backend logs for SSE stream errors
4. Nginx proxy configuration

### Problem: Messages not sending via Arkesel
**Check:**
1. ARKESEL_API_KEY is correct
2. Arkesel account has credits
3. Sender ID is registered
4. Phone numbers are valid format (+233...)
5. Backend logs for Arkesel API errors

---

## Post-Testing Checklist

After completing all tests:
- [ ] Document any bugs found
- [ ] Update SMS_CAMPAIGNS_IMPROVEMENTS.md with test results
- [ ] Verify all features work in production
- [ ] Monitor Arkesel usage and costs
- [ ] Train users on new features
- [ ] Set up alerting for campaign failures
- [ ] Create user documentation/video

---

## Contact & Support

**Arkesel Support:**
- Website: https://developers.arkesel.com
- Email: support@arkesel.com
- Docs: https://developers.arkesel.com/sms-api

**Internal Support:**
- Backend logs: `sudo journalctl -u kasaai-core-backend -f`
- Frontend logs: Browser console
- System health: Check system monitoring dashboard
