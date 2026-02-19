# ChurchFlow Automation Setup & Monitoring Guide

**Last Updated**: December 5, 2025
**Status**: Production Ready ✅

---

## 📋 Overview

The ChurchFlow automation system automatically sends conference reminders to registered attendees. This guide covers setup, monitoring, and troubleshooting.

---

## 🚀 Initial Setup

### 1. Backend Service

The backend service is already running:
- **Service**: `kasaai-churchflow-backend.service`
- **Status**: Active and running
- **Port**: 30030
- **URL**: https://churchflow-api.ailabsafrica.com

### 2. Systemd Timer (Automated Execution)

The automation executor runs every 15 minutes to process pending reminders.

**Files Location**:
- Service: `/etc/systemd/system/churchflow-automation-executor.service`
- Timer: `/etc/systemd/system/churchflow-automation-executor.timer`

**Status Commands**:
```bash
# Check timer status
sudo systemctl status churchflow-automation-executor.timer

# Check last execution
sudo systemctl status churchflow-automation-executor.service

# View execution logs
sudo journalctl -u churchflow-automation-executor.service -n 50

# View recent executions with timestamps
sudo journalctl -u churchflow-automation-executor.service --since "1 hour ago"
```

**Management Commands**:
```bash
# Start timer
sudo systemctl start churchflow-automation-executor.timer

# Stop timer
sudo systemctl stop churchflow-automation-executor.timer

# Restart timer
sudo systemctl restart churchflow-automation-executor.timer

# Disable timer (prevent auto-start on boot)
sudo systemctl disable churchflow-automation-executor.timer

# Enable timer (auto-start on boot)
sudo systemctl enable churchflow-automation-executor.timer
```

**Manual Execution** (for testing):
```bash
# Trigger execution manually
sudo systemctl start churchflow-automation-executor.service

# Or use curl directly
curl -X POST https://churchflow-api.ailabsafrica.com/api/v1/automation/execute-pending
```

### 3. Frontend Access

The automation dashboard is accessible at:
- **URL**: https://churchflow.ailabsafrica.com/admin/automation
- **Authentication**: Required (admin or coordinator role)
- **Organization**: Must select organization from dropdown

---

## 📝 Creating Your First Workflow

### Step 1: Create a Conference

1. Navigate to: https://churchflow.ailabsafrica.com/admin/conferences
2. Click "Create Conference"
3. Fill in details:
   - Name: e.g., "Youth Summit 2025"
   - Start Date: Set to future date (at least 7+ days from now)
   - End Date: Set end date
   - Venue: Conference location
4. Click "Create"

### Step 2: Add Registrations

You need registered attendees for reminders to be sent:

1. Navigate to: https://churchflow.ailabsafrica.com/register
2. Select your conference
3. Fill in registration form (including phone number)
4. Submit registration
5. Repeat for test attendees (or use real registrations)

**Minimum**: At least 1 registration required

### Step 3: Create Automation Workflow

1. Navigate to: https://churchflow.ailabsafrica.com/admin/automation
2. Click "Create Workflow" button
3. Select your conference from dropdown
4. Review default reminders:
   - 📅 7 days before: "Coming up next week!"
   - 📅 3 days before: "This weekend!"
   - 📅 1 day before: "Tomorrow! Save your QR code"
5. Click "Create Workflow"

### Step 4: Verify Scheduling

After creating the workflow:

1. Check the workflows list - you should see:
   - Status: "active" (green)
   - Next Execution: Date/time of first reminder
2. Dashboard statistics will update:
   - Total Workflows: +1
   - Active Workflows: +1
   - Pending Reminders: +3 (7d, 3d, 1d)

---

## 📊 Monitoring & Analytics

### Dashboard Statistics

The automation dashboard shows:

**Workflow Metrics**:
- Total Workflows: All workflows created
- Active Workflows: Currently running
- Paused Workflows: Temporarily disabled

**Reminder Metrics**:
- Pending Reminders: Not yet sent
- Upcoming Reminders (24h): Due within next 24 hours

**Performance Metrics** (30-day window):
- Success Rate: Percentage of successful executions
- Total Executions: Total reminder deliveries attempted
- Failed Executions: Number of failures

### Workflow Details

Each workflow shows:
- **Name**: Workflow identifier
- **Status**: active/paused/completed/cancelled/failed
- **Type**: event_reminder, member_onboarding, etc.
- **Executions**: Total count (successful count)
- **Last Execution**: Timestamp of last reminder sent
- **Next Execution**: Timestamp of next scheduled reminder

### MongoDB Collections

**automation_workflows**:
```javascript
db.automation_workflows.find().pretty()
```

**scheduled_reminders**:
```javascript
// Find pending reminders
db.scheduled_reminders.find({ status: "pending" }).pretty()

// Find upcoming reminders (next 24h)
db.scheduled_reminders.find({
  status: "pending",
  scheduled_at: {
    $gte: new Date(),
    $lte: new Date(Date.now() + 24*60*60*1000)
  }
}).pretty()

// Find completed reminders
db.scheduled_reminders.find({ status: "completed" }).pretty()
```

**automation_logs** (audit trail):
```javascript
// Recent automation events
db.automation_logs.find().sort({ created_at: -1 }).limit(20).pretty()

// Find errors
db.automation_logs.find({ event_type: "error" }).pretty()
```

### API Endpoints for Monitoring

**Dashboard Statistics**:
```bash
TOKEN="your_jwt_token"
ORG_ID="your_organization_id"

curl -X GET "https://churchflow-api.ailabsafrica.com/api/v1/automation/dashboard" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Organization-ID: $ORG_ID"
```

**List All Workflows**:
```bash
curl -X GET "https://churchflow-api.ailabsafrica.com/api/v1/automation/workflows" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Organization-ID: $ORG_ID"
```

**List Active Workflows**:
```bash
curl -X GET "https://churchflow-api.ailabsafrica.com/api/v1/automation/workflows?status=active" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Organization-ID: $ORG_ID"
```

---

## 🔍 Troubleshooting

### No Reminders Being Sent

**Check 1: Timer Status**
```bash
sudo systemctl status churchflow-automation-executor.timer
```
Expected: `Active: active (waiting)`

**Check 2: Pending Reminders**
```javascript
db.scheduled_reminders.find({ status: "pending" }).count()
```
Expected: > 0 if you have upcoming conferences

**Check 3: Workflow Status**
```javascript
db.automation_workflows.find({ status: "active" }).count()
```
Expected: > 0 if you created workflows

**Check 4: Conference Date**
```javascript
db.scheduled_reminders.find({
  status: "pending",
  scheduled_at: { $lte: new Date() }
})
```
If this returns results, reminders are overdue and should execute on next timer run.

**Check 5: Execution Logs**
```bash
sudo journalctl -u churchflow-automation-executor.service --since "1 hour ago"
```
Look for successful HTTP 200 responses.

### Reminders Scheduled But Not Executing

**Check 1: Backend Service**
```bash
sudo systemctl status kasaai-churchflow-backend
```
Expected: `Active: active (running)`

**Check 2: Manual Execution**
```bash
curl -X POST https://churchflow-api.ailabsafrica.com/api/v1/automation/execute-pending
```
Expected response:
```json
{
  "success": true,
  "executed": 1,
  "successful": 1,
  "failed": 0,
  "timestamp": "2025-12-05T21:30:00.000000"
}
```

**Check 3: Backend Logs**
```bash
sudo journalctl -u kasaai-churchflow-backend --since "15 minutes ago" | grep automation
```
Look for automation-related errors.

### SMS Messages Not Delivering

**Check 1: SMS Campaign Status**
```javascript
// Find SMS campaigns created by automation
db.sms_campaigns.find({ created_by: "automation_system" }).sort({ created_at: -1 })
```

**Check 2: SMS Campaign Logs**
```bash
sudo journalctl -u kasaai-churchflow-backend | grep -i "sms\|arkesel\|twilio"
```

**Check 3: Arkesel/Twilio Credentials**
```bash
# Check environment variables
sudo systemctl show kasaai-churchflow-backend | grep -i arkesel
```

### Workflow Stuck in "Failed" Status

**Investigate Failure**:
```javascript
// Find failed workflow
db.automation_workflows.findOne({ _id: ObjectId("workflow_id") })

// Find related failed reminders
db.scheduled_reminders.find({
  workflow_id: "workflow_id",
  status: "failed"
})

// Check error logs
db.automation_logs.find({
  workflow_id: "workflow_id",
  event_type: "error"
}).sort({ created_at: -1 })
```

**Resolution**:
1. Fix underlying issue (SMS credentials, network, etc.)
2. Reactivate workflow:
   ```bash
   # Via API
   curl -X PUT "https://churchflow-api.ailabsafrica.com/api/v1/automation/workflows/{workflow_id}/status?status=active" \
     -H "Authorization: Bearer $TOKEN" \
     -H "X-Organization-ID: $ORG_ID"
   ```
3. Or via UI: Click "Activate" button on workflow

---

## ⚙️ Configuration

### Adjusting Timer Frequency

Edit `/etc/systemd/system/churchflow-automation-executor.timer`:

```ini
[Timer]
# Run every 5 minutes (more frequent)
OnUnitActiveSec=5min

# Or every 30 minutes (less frequent)
OnUnitActiveSec=30min

# Or every hour
OnUnitActiveSec=1h
```

Apply changes:
```bash
sudo systemctl daemon-reload
sudo systemctl restart churchflow-automation-executor.timer
```

### Customizing Reminder Messages

Currently, reminder messages are set when creating the workflow. To customize:

**Option 1**: Edit via MongoDB (temporary solution)
```javascript
db.automation_workflows.updateOne(
  { _id: ObjectId("workflow_id") },
  {
    $set: {
      "event_reminder_config.reminder_steps.0.message_template": "Your custom message here"
    }
  }
)
```

**Option 2**: Delete and recreate workflow with new messages (future UI feature)

### Changing Reminder Timing

To change from 7/3/1 days to different timing:

**Option 1**: Via MongoDB
```javascript
db.automation_workflows.updateOne(
  { _id: ObjectId("workflow_id") },
  {
    $set: {
      "event_reminder_config.reminder_steps.0.days_before": 14  // 14 days instead of 7
    }
  }
)
```

**Option 2**: Create custom workflow via API (advanced)

---

## 📈 Best Practices

### 1. Monitor Daily

Check dashboard daily for:
- Pending reminders count
- Success rate (should be >95%)
- Failed executions (should be 0)

### 2. Test Before Production

Before announcing automation:
1. Create test conference 7+ days away
2. Add test registration (your phone number)
3. Create workflow
4. Wait for first reminder (or adjust date for immediate test)
5. Verify SMS delivery

### 3. Keep Workflows Clean

- Delete completed workflows after conference ends
- Pause workflows if conference is cancelled
- Don't create duplicate workflows for same conference

### 4. Backup Strategy

MongoDB includes automation collections in regular backups:
- `automation_workflows`
- `scheduled_reminders`
- `automation_logs`

Restore if needed:
```bash
mongorestore --db churchflow /path/to/backup/churchflow
```

---

## 🚨 Emergency Procedures

### Stop All Reminders Immediately

```bash
# Stop the timer
sudo systemctl stop churchflow-automation-executor.timer

# Pause all active workflows via MongoDB
mongo churchflow --eval '
  db.automation_workflows.updateMany(
    { status: "active" },
    { $set: { status: "paused" } }
  )
'
```

### Delete All Pending Reminders

```bash
mongo churchflow --eval '
  db.scheduled_reminders.deleteMany({ status: "pending" })
'
```

### Resume Normal Operations

```bash
# Restart timer
sudo systemctl start churchflow-automation-executor.timer

# Reactivate workflows via UI or API
```

---

## 📞 Support

### Log Locations

- **Timer Logs**: `sudo journalctl -u churchflow-automation-executor.service`
- **Backend Logs**: `sudo journalctl -u kasaai-churchflow-backend`
- **MongoDB Logs**: `/var/log/mongodb/mongod.log`

### Health Checks

**Backend**:
```bash
curl https://churchflow-api.ailabsafrica.com/health
```

**Automation Endpoint**:
```bash
curl -X POST https://churchflow-api.ailabsafrica.com/api/v1/automation/execute-pending
```

**Database**:
```bash
mongo churchflow --eval 'db.automation_workflows.count()'
```

---

## 📚 Related Documentation

- [PHASE_7_WEEK_5-6_COMPLETE.md](./PHASE_7_WEEK_5-6_COMPLETE.md) - Full implementation details
- [PHASE_7_WEEK_5-6_BACKEND_COMPLETE.md](./PHASE_7_WEEK_5-6_BACKEND_COMPLETE.md) - Backend architecture
- [README.md](./README.md) - General ChurchFlow documentation

---

**Document Version**: 1.0
**Last Updated**: December 5, 2025
**Status**: Production Ready ✅
