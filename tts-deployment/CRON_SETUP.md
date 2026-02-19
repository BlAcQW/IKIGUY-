# TTS Health Monitoring Cron Job Setup

**Created:** 2025-10-20
**Purpose:** Automated health monitoring for all TTS services

---

## Overview

This document describes how to set up automated health monitoring for the TTS deployment using the Kasaai Cron Management system.

---

## Setup Instructions

### Option 1: Via Admin Panel (Recommended)

1. **Navigate to Cron Management**
   - Go to https://kasaai.ailabsafrica.com/admin/cron-management
   - Log in with admin credentials

2. **Create New Cron Job**
   - Click "Create Cron Job" button
   - Fill in the following details:

   ```
   Name: TTS Health Check Monitor
   Description: Monitors all TTS services every 5 minutes and logs health status
   Cron Expression: */5 * * * *  (every 5 minutes)
   Job Type: monitoring
   Script Path: /opt/kasaai/apps/tts-deployment/scripts/comprehensive_health_check.sh

   Metadata (optional):
   {
     "service": "tts-deployment",
     "output_format": "colored",
     "monitored_services": ["Coqui XTTS v2", "MeloTTS", "OpenVoice", "Kokoro TTS", "Crawl4AI"]
   }
   ```

3. **Verify Job Creation**
   - Job should appear in the cron jobs list
   - Status should be "Active"
   - Next run time should be displayed

4. **Monitor Execution**
   - Check execution logs in the admin panel
   - View job history and success/failure rates

---

### Option 2: Via API (Requires Authentication)

```bash
curl -X POST "https://api.ailabsafrica.com/cron-management/jobs/create" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_AUTH_TOKEN" \
  -d '{
    "name": "TTS Health Check Monitor",
    "description": "Monitors all TTS services every 5 minutes and logs health status",
    "cron_expression": "*/5 * * * *",
    "job_type": "monitoring",
    "script_path": "/opt/kasaai/apps/tts-deployment/scripts/comprehensive_health_check.sh",
    "metadata": {
      "service": "tts-deployment",
      "output_format": "colored"
    }
  }'
```

**Response (Success):**
```json
{
  "success": true,
  "job_id": "custom_abc123def456",
  "message": "Custom cron job 'TTS Health Check Monitor' created successfully"
}
```

---

## Cron Schedule Options

The cron expression follows standard cron format: `minute hour day month day_of_week`

### Common Schedules

| Expression | Description |
|------------|-------------|
| `*/5 * * * *` | Every 5 minutes |
| `*/10 * * * *` | Every 10 minutes |
| `*/15 * * * *` | Every 15 minutes |
| `0 */1 * * *` | Every hour |
| `0 */6 * * *` | Every 6 hours |
| `0 0 * * *` | Daily at midnight |

---

## Health Check Script Details

### Script Location
```
/opt/kasaai/apps/tts-deployment/scripts/comprehensive_health_check.sh
```

### What It Checks
- ✅ Docker container status (running/stopped)
- ✅ Local HTTP health endpoints (port connectivity)
- ✅ HTTPS/SSL certificate validation
- ✅ Service response times
- ✅ Overall uptime percentage

### Output Format
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TTS Services Health Check
Time: 2025-10-20 13:34:36
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ MeloTTS              HEALTHY | HTTPS: SSL OK
✓ Kokoro TTS           HEALTHY | HTTPS: SSL OK
✓ Crawl4AI             HEALTHY | HTTPS: SSL OK
✓ OpenVoice            HEALTHY | HTTPS: SSL OK
✓ Coqui XTTS v2        HEALTHY | HTTPS: SSL OK

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Summary:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total Services:     5
Healthy:            5
Degraded:           0
Offline:            0

Uptime:             100%
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Exit Codes
- `0` - All services healthy
- `1` - One or more services degraded/offline

---

## Monitoring the Cron Job

### Via Admin Panel
1. Go to https://kasaai.ailabsafrica.com/admin/cron-management
2. Find "TTS Health Check Monitor" in the list
3. Click to view details and execution history
4. Check recent logs for success/failure status

### Via API
```bash
# List all cron jobs
curl "https://api.ailabsafrica.com/cron-management/jobs" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get specific job details
curl "https://api.ailabsafrica.com/cron-management/jobs/JOB_ID" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get execution logs
curl "https://api.ailabsafrica.com/cron-management/logs?job_id=JOB_ID&limit=50" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Troubleshooting

### Job Not Running
1. Check job status in admin panel - is it paused?
2. Verify script path is correct and executable:
   ```bash
   ls -l /opt/kasaai/apps/tts-deployment/scripts/comprehensive_health_check.sh
   chmod +x /opt/kasaai/apps/tts-deployment/scripts/comprehensive_health_check.sh
   ```
3. Check execution logs for error messages

### Script Fails to Execute
1. Ensure script has execute permissions:
   ```bash
   chmod +x /opt/kasaai/apps/tts-deployment/scripts/comprehensive_health_check.sh
   ```
2. Test script manually:
   ```bash
   /opt/kasaai/apps/tts-deployment/scripts/comprehensive_health_check.sh
   ```
3. Check script dependencies (curl, sudo access, etc.)

### No Execution Logs
1. Verify cron job is active (not paused)
2. Check if APScheduler is running in backend
3. Review backend logs for scheduler errors:
   ```bash
   sudo journalctl -u kasaai-core-backend -f | grep -i cron
   ```

---

## Pausing/Resuming the Job

### Via Admin Panel
1. Navigate to the job in Cron Management
2. Click "Pause" button to temporarily stop execution
3. Click "Resume" button to restart execution

### Via API
```bash
# Pause job
curl -X POST "https://api.ailabsafrica.com/cron-management/jobs/JOB_ID/pause" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Resume job
curl -X POST "https://api.ailabsafrica.com/cron-management/jobs/JOB_ID/resume" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Deleting the Job

### Via Admin Panel
1. Navigate to the job in Cron Management
2. Click "Delete" button
3. Confirm deletion

### Via API
```bash
curl -X DELETE "https://api.ailabsafrica.com/cron-management/jobs/JOB_ID" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Alternative: Manual Crontab (Not Recommended)

If the Kasaai Cron Management system is unavailable, you can use system crontab:

```bash
# Edit crontab
crontab -e

# Add this line
*/5 * * * * /opt/kasaai/apps/tts-deployment/scripts/comprehensive_health_check.sh >> /var/log/tts/health_check.log 2>&1

# Save and exit
```

**Note:** This approach doesn't provide:
- Web-based monitoring
- Execution logs in admin panel
- Easy pause/resume functionality
- Centralized job management

---

## Next Steps

1. ✅ Create the cron job via admin panel
2. ✅ Verify first execution (wait 5 minutes)
3. ✅ Check execution logs for success
4. ✅ Monitor for 24 hours to ensure stability
5. ✅ Set up alerting if health check fails (optional)

---

**Created by:** Claude Code
**Last Updated:** 2025-10-20
**Status:** Ready for deployment
