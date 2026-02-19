# ChurchFlow Automation - Quick Reference Card

---

## 🚀 Quick Start (3 Steps)

1. **Create Conference** (7+ days in future)
   - Go to: `/admin/conferences` → Create Conference

2. **Get Registrations** (at least 1)
   - Share registration link: `/register/{conference_id}`
   - Or register manually

3. **Create Workflow**
   - Go to: `/admin/automation` → Create Workflow
   - Select conference → Done!

**Reminders auto-send at 7d, 3d, 1d before conference** ✅

---

## 📊 Dashboard Quick View

**URL**: https://churchflow.ailabsafrica.com/admin/automation

**Key Metrics**:
- 🔢 Total Workflows - How many automation workflows exist
- ✅ Active Workflows - Currently running
- ⏰ Pending Reminders - Scheduled but not yet sent
- 📈 Success Rate - % of successful deliveries (30d)

**Colors**:
- 🟢 Green = Active
- 🟡 Yellow = Paused
- 🔴 Red = Failed
- 🔵 Blue = Completed

---

## ⚙️ Common Commands

### Check Timer Status
```bash
sudo systemctl status churchflow-automation-executor.timer
```

### View Recent Executions
```bash
sudo journalctl -u churchflow-automation-executor.service -n 20
```

### Manual Trigger (Testing)
```bash
curl -X POST https://churchflow-api.ailabsafrica.com/api/v1/automation/execute-pending
```

### Check Pending Reminders (MongoDB)
```bash
mongo churchflow --eval 'db.scheduled_reminders.find({status:"pending"}).count()'
```

---

## 🎛️ Workflow Actions

| Action | When to Use | How |
|--------|-------------|-----|
| **Create** | New conference needs reminders | Click "Create Workflow" |
| **Pause** | Temporarily stop (e.g., postponed event) | Click pause icon ⏸️ |
| **Activate** | Resume paused workflow | Click play icon ▶️ |
| **Delete** | Conference cancelled permanently | Click trash icon 🗑️ |

---

## 🔍 Quick Troubleshooting

| Problem | Quick Check | Solution |
|---------|-------------|----------|
| No reminders sent | Timer active? | `sudo systemctl start churchflow-automation-executor.timer` |
| Workflow shows "failed" | Check logs | `sudo journalctl -u kasaai-churchflow-backend \| tail -50` |
| SMS not delivering | Arkesel credits? | Check SMS campaign logs |
| Can't create workflow | Conference in past? | Create new conference with future date |

---

## 📅 Default Reminder Schedule

| Timing | Message Template |
|--------|------------------|
| **7 days before** | "📅 [Conference] is coming up next week! Get ready for an amazing time." |
| **3 days before** | "🎉 [Conference] is this weekend! Don't forget to prepare." |
| **1 day before** | "⏰ [Conference] is TOMORROW! Save your QR code for quick check-in." |

---

## 🚨 Emergency Stop

```bash
# Stop all automation
sudo systemctl stop churchflow-automation-executor.timer

# Pause all workflows
mongo churchflow --eval 'db.automation_workflows.updateMany({status:"active"},{$set:{status:"paused"}})'
```

---

## 📞 Quick Health Check

```bash
# All-in-one health check
curl https://churchflow-api.ailabsafrica.com/health && \
sudo systemctl is-active churchflow-automation-executor.timer && \
mongo churchflow --eval 'db.automation_workflows.find({status:"active"}).count()'
```

Expected output:
- `{"status":"healthy"}` (backend)
- `active` (timer)
- `N` (number of active workflows)

---

## 📊 Monitoring Dashboard URLs

| Dashboard | URL |
|-----------|-----|
| Automation | https://churchflow.ailabsafrica.com/admin/automation |
| Conferences | https://churchflow.ailabsafrica.com/admin/conferences |
| SMS Campaigns | https://churchflow.ailabsafrica.com/admin/sms-campaigns |
| Analytics | https://churchflow.ailabsafrica.com/admin/analytics |

---

## 💡 Pro Tips

✅ **Create workflows immediately after creating conferences** - Don't wait!

✅ **Monitor success rate** - Should stay above 95%. If it drops, investigate.

✅ **Test first** - Use test conference with your phone number before production.

✅ **Check daily** - Quick 30-second dashboard check prevents issues.

✅ **Delete completed** - Remove old workflows to keep dashboard clean.

❌ **Don't create duplicates** - One workflow per conference is enough.

❌ **Don't pause too early** - Reminders only send once; can't resend.

---

**Last Updated**: December 5, 2025
**Full Docs**: [AUTOMATION_SETUP_GUIDE.md](./AUTOMATION_SETUP_GUIDE.md)
